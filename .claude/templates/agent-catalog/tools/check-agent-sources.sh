#!/usr/bin/env bash
# check-agent-sources.sh - Controlla se le fonti del catalogo hanno nuovi commit upstream (variante Linux/macOS).
#
# Stessa strategia a costo zero di tools/update-handoff.sh: confronta l'ultimo commit del branch
# di ciascuna fonte (una richiesta HTTP) con lo sha registrato in .claude/agent-catalog/state.json
# l'ultima volta che si e' controllato. A differenza dell'handoff, qui non c'e' una fonte che si
# auto-aggiorna a cadenza nota: "controllato di recente" non implica "nessuna novita'", significa
# solo che non si e' ancora guardato. Per questo lo stallo qui e' della verifica locale, non della
# fonte: se non si controlla da piu' di 30 giorni lo script lo segnala, cosa diversa dal caso
# dell'handoff dove e' l'updater upstream stesso a poter fermarsi.
#
# Uso:
#   ./tools/check-agent-sources.sh            # controlla tutte le fonti e aggiorna lo stato
#   ./tools/check-agent-sources.sh --check    # solo verifica, non scrive stato; exit 10 se c'e' novita'
#
# Exit code: 0 = nessuna fonte con novita' (o stato aggiornato); 10 = novita' disponibili (--check); 1 = errore.
# Richiede jq.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SOURCES="$PROJECT_ROOT/.claude/agent-catalog/sources.json"
STATE="$PROJECT_ROOT/.claude/agent-catalog/state.json"
STALE_DAYS=30

CHECK_ONLY=0
[ "${1:-}" = "--check" ] && CHECK_ONLY=1

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"; }

if ! command -v jq >/dev/null 2>&1; then
  echo "ERRORE: serve jq (apt install jq / brew install jq)." >&2
  exit 1
fi
if [ ! -f "$SOURCES" ]; then
  log "ERRORE: non trovo $SOURCES. Il pacchetto agent-catalog e' instanziato correttamente?"
  exit 1
fi
if [ ! -f "$STATE" ]; then echo '{"sources": {}, "fetch_log": []}' > "$STATE"; fi

any_update=0
count=$(jq '.sources | length' "$SOURCES")
new_state="$STATE"
for i in $(seq 0 $((count - 1))); do
  key="$(jq -r ".sources[$i].key" "$SOURCES")"
  repo="$(jq -r ".sources[$i].repo" "$SOURCES")"
  branch="$(jq -r ".sources[$i].branch" "$SOURCES")"

  last_sha="$(jq -r --arg k "$key" '.sources[$k].last_known_sha // empty' "$STATE")"
  last_checked="$(jq -r --arg k "$key" '.sources[$k].last_checked_at // empty' "$STATE")"

  current_sha="$(curl -fsSL --max-time 20 -H "User-Agent: agent-catalog-script" "https://api.github.com/repos/$repo/commits/$branch" 2>/dev/null | jq -r '.sha // empty')"
  if [ -z "$current_sha" ]; then
    log "[$key] ERRORE: impossibile leggere l'ultimo commit."
    continue
  fi

  if [ -n "$last_checked" ]; then
    check_epoch="$(date -d "$last_checked" +%s 2>/dev/null || true)"
    if [ -n "$check_epoch" ]; then
      age_days=$(( ( $(date +%s) - check_epoch ) / 86400 ))
      if [ "$age_days" -gt "$STALE_DAYS" ]; then
        log "[$key] ATTENZIONE: non controllato da $age_days giorni (ultimo controllo: $last_checked)."
      fi
    fi
  fi

  if [ -z "$last_sha" ]; then
    log "[$key] Nessuno stato precedente: prima registrazione, sha ${current_sha:0:7}."
  elif [ "$last_sha" != "$current_sha" ]; then
    log "[$key] AGGIORNAMENTO DISPONIBILE: ${last_sha:0:7} -> ${current_sha:0:7}. Rivedere con list-community-agents.sh $key."
    any_update=1
  else
    log "[$key] Nessuna novita' (sha ${current_sha:0:7})."
  fi

  if [ "$CHECK_ONLY" -eq 0 ]; then
    tmp_state="$(mktemp)"
    jq --arg k "$key" --arg sha "$current_sha" --arg date "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" \
      '.sources[$k] = {last_known_sha: $sha, last_checked_at: $date}' \
      "$new_state" > "$tmp_state" && mv "$tmp_state" "$new_state"
  fi
done

if [ "$CHECK_ONLY" -eq 0 ]; then
  log "Stato aggiornato in .claude/agent-catalog/state.json"
fi

if [ "$CHECK_ONLY" -eq 1 ] && [ "$any_update" -eq 1 ]; then
  exit 10
fi
exit 0
