#!/usr/bin/env bash
# ============================================================================
# session-end-wipe.sh  (TEMPLATE, variante POSIX di session-end-wipe.ps1)
# Eseguito da un hook SessionEnd di Claude Code a OGNI chiusura di sessione.
# Pulisce il magazzino nascosto dell'account preservando:
#   - i progetti il cui slug inizia con uno dei prefissi in $KEEP_PREFIXES (specifici
#     della macchina, uno per ogni disco dove stanno i progetti di sviluppo)
#   - configurazione, login, skill, plugin, hooks, daemon  -> mai toccati
#   - di .claude.json solo le voci 'projects' non preservate (vedi blocco 4)
#   - i file dei progetti su disco                  -> mai toccati
#
# Installazione per-account (vedi PROJECT-SYSTEM.md sezione 15):
#   1. copia questo file in <CLAUDE_CONFIG_DIR>/hooks/session-end-wipe.sh
#      e, accanto, scrub-claude-json.js preso dalla stessa cartella del template
#   2. imposta BASE col path assoluto della home dell'account
#   3. registra l'hook in <CLAUDE_CONFIG_DIR>/settings.json:
#        "hooks": { "SessionEnd": [ { "hooks": [ {
#          "type": "command",
#          "command": "bash \"<CLAUDE_CONFIG_DIR>/hooks/session-end-wipe.sh\""
#        } ] } ] }
# ============================================================================
set -u
BASE="<CLAUDE_CONFIG_DIR>"          # path assoluto della home dell'account
KEEP_PREFIXES="D--"                 # prefissi degli slug da preservare, separati da spazio; dipende dalla macchina (es. "D-- E--" su piu dischi)
# Percorso di .claude.json: con CLAUDE_CONFIG_DIR impostato sta DENTRO la home
# dell'account; nella home di default sta invece accanto ad essa, in $HOME/.claude.json.
CFG_FILE="$BASE/.claude.json"
# Prefissi di PERCORSO da preservare dentro 'projects' di .claude.json (blocco 4).
# Sono percorsi, non slug: su Windows la radice del disco dei progetti ("D:"), su POSIX
# la radice della cartella di sviluppo ("/home/utente/dev"). Un elemento per prefisso.
KEEP_PATH_PREFIXES=("D:")

# --- 1) progetti: rimuovi transcript + memoria nascosta di tutto tranne i prefissi preservati ---
if [ -d "$BASE/projects" ]; then
  for p in "$BASE/projects"/*/; do
    [ -d "$p" ] || continue
    b="$(basename "$p")"
    keep=0
    for prefix in $KEEP_PREFIXES; do
      case "$b" in "$prefix"*) keep=1; break ;; esac
    done
    [ "$keep" -eq 1 ] && continue
    rm -rf "$p"
  done
fi

# --- 2) store per-account effimeri ---
# Per conservare resume/undo dei progetti preservati tra una sessione e l'altra,
# togli 'sessions' e 'file-history' dalla lista. 'daemon', 'skills', 'plugins' e
# 'hooks' restano fuori: sono stato vivo o configurazione, non residui di sessione.
for e in sessions session-env shell-snapshots file-history plans tasks paste-cache \
         backups memory cache jobs ide todos statsig telemetry; do
  rm -rf "${BASE:?}/$e"
done
rm -f "$BASE/history.jsonl" "$BASE/mcp-needs-auth-cache.json"

# --- 3) scratchpad temporanei: $TMPDIR/claude/<slug-progetto> ---
# Claude Code tiene qui scratchpad e output dei task, uno slug per progetto e una
# sottocartella per sessione. La radice e' condivisa fra tutti gli account della stessa
# utenza, quindi il passaggio e' idempotente. Si rimuovono solo le cartelle che sembrano
# slug di progetto, cosi da non toccare 'bundled-skills' e simili.
TMP_ROOT="${TMPDIR:-/tmp}/claude"
if [ -d "$TMP_ROOT" ]; then
  for p in "$TMP_ROOT"/*/; do
    [ -d "$p" ] || continue
    b="$(basename "$p")"
    # slug di progetto: 'X--...' con la convenzione Windows, oppure '-...' su POSIX
    # (dove derivano da un percorso assoluto). Tutto il resto non si tocca.
    case "$b" in [A-Za-z]--*|-*) ;; *) continue ;; esac
    keep=0
    for prefix in $KEEP_PREFIXES; do
      case "$b" in "$prefix"*) keep=1; break ;; esac
    done
    [ "$keep" -eq 1 ] && continue
    rm -rf "$p"
  done
fi

# --- 4) .claude.json: rimuovi le voci 'projects' dei percorsi non preservati ---
# Senza questo passaggio l'elenco dei percorsi aperti sopravvive al wipe. Il file
# custodisce login e configurazione, quindi la modifica e' delegata a
# scrub-claude-json.js, che valida il risultato prima di sostituire l'originale. Se Node
# non c'e', il passaggio si salta senza toccare il file. Si ripulisce anche l'eventuale
# .backup, che altrimenti conserverebbe le stesse voci.
SCRUB_JS="$BASE/hooks/scrub-claude-json.js"
if [ -f "$SCRUB_JS" ] && command -v node >/dev/null 2>&1; then
  for target in "$CFG_FILE" "$CFG_FILE.backup"; do
    [ -f "$target" ] || continue
    node "$SCRUB_JS" "$target" "${KEEP_PATH_PREFIXES[@]}" >/dev/null 2>&1
    rm -f "$target.tmp"
  done
fi
