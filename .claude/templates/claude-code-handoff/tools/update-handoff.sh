#!/usr/bin/env bash
# update-handoff.sh - Auto-aggiornamento dell'handoff Claude Code (variante Linux/macOS).
#
# Confronta la versione della guida upstream (Cranot/claude-code-guide, auto-aggiornata
# ~ogni 2 giorni) con quella tracciata in .claude/handoff-state.json. Se e' cambiata:
#   1. scarica la guida grezza in _notes/upstream/claude-code-guide.md (ignorato da git);
#   2. aggiorna il file di stato (tracciato);
#   3. se la CLI `claude` e' installata, ri-distilla .claude/context/claude-code-handoff.md;
#      altrimenti segnala di eseguire /refresh-handoff dentro la sessione.
#
# Uso:
#   ./tools/update-handoff.sh              # check + aggiorna se serve
#   ./tools/update-handoff.sh --check      # solo verifica: exit 10 se c'e' un aggiornamento
#   ./tools/update-handoff.sh --force      # riscarica e rigenera comunque
#   ./tools/update-handoff.sh --no-distill # scarica e aggiorna lo stato, senza corsa LLM
#
# Cron consigliato (ogni 2 giorni alle 4:00):
#   0 4 */2 * * cd /path/al/progetto && ./tools/update-handoff.sh >> _notes/handoff-update.log 2>&1
#
# Exit code: 0 = allineato o aggiornato; 10 = aggiornamento disponibile (--check); 1 = errore.
# Il commit dei file rigenerati resta manuale dell'utente.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
STATE="$PROJECT_ROOT/.claude/handoff-state.json"
HANDOFF="$PROJECT_ROOT/.claude/context/claude-code-handoff.md"
RAW_DIR="$PROJECT_ROOT/_notes/upstream"
RAW_COPY="$RAW_DIR/claude-code-guide.md"

REPO="Cranot/claude-code-guide"
RAW_BASE="https://raw.githubusercontent.com/$REPO/main"

FORCE=0; CHECK_ONLY=0; NO_DISTILL=0
for arg in "$@"; do
  case "$arg" in
    --force) FORCE=1 ;;
    --check) CHECK_ONLY=1 ;;
    --no-distill) NO_DISTILL=1 ;;
    *) echo "Argomento sconosciuto: $arg" >&2; exit 2 ;;
  esac
done

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"; }

# --- Versione locale tracciata ---
local_version=""
if [ -f "$STATE" ]; then
  local_version="$(grep -oE '"upstream_release"[^,}]*' "$STATE" | sed -E 's/^"[^"]+"[[:space:]]*:[[:space:]]*"?([^"]*)"?.*/\1/' || true)"
fi

# --- Versione upstream ---
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
upstream_version=""
upstream_last_check=""
if curl -fsSL --max-time 30 "$RAW_BASE/.update-state.json" -o "$tmp/state.json" 2>/dev/null; then
  upstream_version="$(grep -oE '"last_release"[^,}]*' "$tmp/state.json" | sed -E 's/^"[^"]+"[[:space:]]*:[[:space:]]*"?([^"]*)"?.*/\1/' || true)"
  upstream_last_check="$(grep -oE '"last_check"[^,}]*' "$tmp/state.json" | sed -E 's/^"[^"]+"[[:space:]]*:[[:space:]]*"?([^"]*)"?.*/\1/' || true)"
else
  log "Avviso: stato upstream non leggibile. Procedo solo con --force."
fi

# --- Rilevamento stallo della fonte: se l'updater upstream non gira da >14 giorni, la guida
# --- stessa e' vecchia e "versione allineata" NON significa "informazione aggiornata".
STALE_DAYS=14
if [ -n "$upstream_last_check" ]; then
  check_epoch="$(date -d "$upstream_last_check" +%s 2>/dev/null || true)"
  if [ -n "$check_epoch" ]; then
    age_days=$(( ( $(date +%s) - check_epoch ) / 86400 ))
    if [ "$age_days" -gt "$STALE_DAYS" ]; then
      log "ATTENZIONE: la fonte upstream risulta ferma da $age_days giorni (ultimo check upstream: $upstream_last_check)."
      log "La guida potrebbe non riflettere le release recenti di Claude Code: integrare con 'claude --help' e le docs ufficiali."
    fi
  fi
fi

log "Versione locale: '${local_version:-nessuna}' | upstream: '${upstream_version:-sconosciuta}'"

# --- Decisione ---
if [ "$FORCE" -eq 0 ] && [ -n "$upstream_version" ] && [ "$upstream_version" = "$local_version" ]; then
  log "Nessun aggiornamento: versione $upstream_version gia' distillata."
  exit 0
fi
if [ "$CHECK_ONLY" -eq 1 ]; then
  if [ -z "$upstream_version" ] && [ "$FORCE" -eq 0 ]; then
    log "Stato upstream non disponibile: impossibile verificare."
    exit 1
  fi
  log "Aggiornamento disponibile: $upstream_version (locale: '${local_version:-nessuna}')."
  exit 10
fi

# --- Scarica la guida grezza ---
log "Scarico la guida upstream..."
if ! curl -fsSL --max-time 60 "$RAW_BASE/README.md" -o "$tmp/README.md" || [ ! -s "$tmp/README.md" ]; then
  log "ERRORE: download della guida fallito. Riprovare piu' tardi."
  exit 1
fi

mkdir -p "$RAW_DIR"
{
  echo "<!-- Fonte grezza scaricata automaticamente da github.com/$REPO -->"
  echo "<!-- Versione upstream: ${upstream_version:-sconosciuta} - $(date '+%Y-%m-%d %H:%M:%S') -->"
  echo "<!-- NON modificare a mano: rigenerato da tools/update-handoff.sh. Ignorato da git (_notes/). -->"
  echo ""
  cat "$tmp/README.md"
} > "$RAW_COPY"
log "Guida grezza salvata in _notes/upstream/claude-code-guide.md"

# --- Aggiorna lo stato tracciato ---
mkdir -p "$(dirname "$STATE")"
cat > "$STATE" << EOF
{
  "upstream_release": "${upstream_version:-unknown}",
  "last_update": "$(date -u '+%Y-%m-%dT%H:%M:%SZ')",
  "source": "github.com/$REPO"
}
EOF
log "Stato aggiornato in .claude/handoff-state.json"

# --- Ri-distillazione (corsa LLM, consuma token) ---
if [ "$NO_DISTILL" -eq 1 ]; then
  log "Ri-distillazione saltata (--no-distill): eseguire /refresh-handoff dentro Claude Code."
  exit 0
fi
if ! command -v claude >/dev/null 2>&1; then
  log "CLI claude non trovata: aprire il progetto con 'claude' ed eseguire /refresh-handoff."
  exit 0
fi

log "CLI claude trovata: ri-distillo l'handoff (consuma token)..."
prompt="Leggi _notes/upstream/claude-code-guide.md (guida Claude Code upstream, versione ${upstream_version:-?}) e rigenera .claude/context/claude-code-handoff.md seguendo la procedura del comando .claude/commands/refresh-handoff.md: stessa struttura in sezioni 0-13, sezioni 0 e 13 invariate, marcatori OFFICIAL/COMMUNITY/NEW, frontmatter aggiornato (upstream-release: ${upstream_version:-?}, distilled-date: oggi). Aggiorna solo i contenuti cambiati upstream. Scrivi il file, poi elenca in 3-5 punti cosa e' cambiato."
if claude -p "$prompt" --max-turns 12 --permission-mode acceptEdits; then
  log "Handoff ri-distillato. Rivedere il diff prima del commit (manuale)."
else
  log "Ri-distillazione fallita: usare /refresh-handoff dentro Claude Code."
fi

log "Fatto. Versione upstream tracciata: ${upstream_version:-unknown}"
exit 0
