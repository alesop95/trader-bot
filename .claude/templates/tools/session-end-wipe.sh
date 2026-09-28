#!/usr/bin/env bash
# ============================================================================
# session-end-wipe.sh  (TEMPLATE, variante POSIX di session-end-wipe.ps1)
# Eseguito da un hook SessionEnd di Claude Code a OGNI chiusura di sessione.
# Pulisce il magazzino nascosto dell'account preservando:
#   - i progetti il cui slug inizia con uno dei prefissi in $KEEP_PREFIXES (specifici
#     della macchina, uno per ogni radice dove stanno i progetti di sviluppo)
#   - configurazione, login, skill, plugin, hooks, daemon  -> mai toccati
#   - di .claude.json solo le voci 'projects' non preservate (vedi blocco 4)
#   - i file dei progetti su disco                  -> mai toccati
#
# QUESTO TEMPLATE NON PARTE FINCHE' NON E' STATO COMPILATO. I segnaposto
# <CLAUDE_CONFIG_DIR>, <KEEP_PREFIXES> e <KEEP_PATH_PREFIXES> sono deliberatamente non
# funzionanti: uno script che cancella non deve avere un default che funziona, perche'
# un default giusto su una macchina e' un default sbagliato su tutte le altre e il modo
# in cui sbaglia e' silenzioso. Vedi il blocco 0 di guardie qui sotto.
#
# Installazione per-account (vedi PROJECT-SYSTEM.md sezione 15):
#   1. copia questo file in <CLAUDE_CONFIG_DIR>/hooks/session-end-wipe.sh
#      e, accanto, scrub-claude-json.js preso dalla stessa cartella del template
#   2. scopri quali slug esistono davvero in questo account, senza inventarli:
#        bash session-end-wipe.sh --list
#      il comando non cancella nulla e stampa gli slug presenti marcati KEEP o WIPE
#   3. compila BASE, KEEP_PREFIXES e KEEP_PATH_PREFIXES qui sotto
#   4. prova a vuoto, che non rimuove niente e stampa cosa farebbe:
#        bash session-end-wipe.sh --dry-run
#   5. registra l'hook in <CLAUDE_CONFIG_DIR>/settings.json:
#        "hooks": { "SessionEnd": [ { "hooks": [ {
#          "type": "command",
#          "command": "bash \"<CLAUDE_CONFIG_DIR>/hooks/session-end-wipe.sh\""
#        } ] } ] }
# ============================================================================
set -u

# --- configurazione, da compilare all'installazione -------------------------
# BASE: path assoluto della home dell'account. Lasciando il segnaposto, lo script lo
# risolve da $CLAUDE_CONFIG_DIR e in sua mancanza da $HOME/.claude, e comunque lo valida.
BASE="<CLAUDE_CONFIG_DIR>"
# KEEP_PREFIXES: prefissi degli slug da preservare, separati da spazio. SPECIFICI DELLA
# MACCHINA. Su Windows uno per disco di sviluppo (es. "D-- E--"); su POSIX gli slug
# derivano dal percorso assoluto, quindi il prefisso ha la forma della radice di sviluppo
# resa come slug (es. "-home-utente-dev-"). Non si indovina: si legge da --list.
KEEP_PREFIXES="<KEEP_PREFIXES>"
# KEEP_PATH_PREFIXES: prefissi di PERCORSO da preservare dentro 'projects' di
# .claude.json (blocco 4). Sono percorsi, non slug: su Windows la radice del disco dei
# progetti ("D:"), su POSIX la radice della cartella di sviluppo ("/home/utente/dev").
# Un elemento per prefisso.
KEEP_PATH_PREFIXES=("<KEEP_PATH_PREFIXES>")
# Deroga esplicita alla guardia dell'insieme vuoto (blocco 0.3): si passa nell'ambiente
# solo se si vuole davvero un account in cui NESSUN progetto e' preservato.
ALLOW_EMPTY_KEEP="${ALLOW_EMPTY_KEEP:-0}"

# --- modo di esecuzione -----------------------------------------------------
MODE="wipe"
case "${1:-}" in
  "")        ;;
  --dry-run) MODE="dry"  ;;
  --list)    MODE="list" ;;
  *) echo "uso: $(basename "$0") [--dry-run|--list]" >&2; exit 2 ;;
esac

# --- diario -----------------------------------------------------------------
# L'hook SessionEnd gira senza che nessuno ne veda l'output, quindi un rifiuto a partire
# sarebbe invisibile: l'esito dell'ultima corsa si scrive nella home dell'account.
LOG=""
log() {
  printf '%s\n' "$*"
  if [ -n "$LOG" ]; then printf '%s\n' "$*" >>"$LOG"; fi
  return 0
}
abort() {
  log "ABORT: $*"
  log "Nessuna rimozione eseguita."
  exit 1
}

# --- blocco 0: guardie, prima di qualunque rimozione ------------------------

# 0.1 dove sta davvero il magazzino. Un BASE non risolto o non valido farebbe 'rm -rf'
# su percorsi che non sono la home di un account, quindi si verifica che il posto esista
# e assomigli a un magazzino di Claude Code prima di toccarlo.
case "$BASE" in
  ""|*"<"*">"*) BASE="${CLAUDE_CONFIG_DIR:-$HOME/.claude}" ;;
esac
BASE="${BASE%/}"
[ -n "$BASE" ] || abort "BASE vuoto dopo la risoluzione."
case "$BASE" in
  "/"|"$HOME") abort "BASE risolto a '$BASE', che non e' la home di un account Claude Code." ;;
esac
[ -d "$BASE" ] || abort "BASE '$BASE' non esiste: controlla CLAUDE_CONFIG_DIR o compila il segnaposto."
if [ ! -d "$BASE/projects" ] && [ ! -f "$BASE/settings.json" ] && [ ! -f "$BASE/settings.local.json" ] && [ ! -f "$BASE/.credentials.json" ]; then
  abort "BASE '$BASE' non contiene ne' projects/ ne' un settings.json: non sembra il magazzino di un account Claude Code."
fi
LOG="$BASE/session-end-wipe.log"
: >"$LOG" 2>/dev/null || LOG=""
log "session-end-wipe: $(date '+%Y-%m-%d %H:%M:%S')  modo=$MODE  base=$BASE"

# 0.2 la configurazione e' stata compilata. Il segnaposto non si sostituisce da solo, e
# un KEEP_PREFIXES vuoto significherebbe "non preservare niente". La guardia non vale in
# modo '--list', che e' proprio il comando con cui si scopre che cosa configurare: li'
# la mancanza si segnala e si prosegue in sola lettura.
KEEP_CONFIGURED=1
case "$KEEP_PREFIXES" in
  ""|*"<"*">"*) KEEP_CONFIGURED=0; KEEP_PREFIXES="" ;;
esac
if [ "$KEEP_CONFIGURED" -eq 0 ] && [ "$MODE" != "list" ]; then
  abort "KEEP_PREFIXES non compilato. Esegui '--list' per vedere gli slug presenti in questo account, poi scegli cosa preservare."
fi

# 0.3 i prefissi parlano di QUESTA macchina. E' la guardia che conta davvero: un insieme
# di prefissi corretto altrove non corrisponde a nessuno slug qui, l'insieme preservato
# risulta vuoto e il wipe cancellerebbe l'intero magazzino senza segnalare niente. Il
# caso tipico e' un 'D--' portato su Linux, dove gli slug derivano da /home.
matches_keep() {
  local b="$1" prefix
  for prefix in $KEEP_PREFIXES; do
    case "$b" in "$prefix"*) return 0 ;; esac
  done
  return 1
}
PROJ="$BASE/projects"
total=0; kept=0
if [ -d "$PROJ" ]; then
  for p in "$PROJ"/*/; do
    [ -d "$p" ] || continue
    total=$((total+1))
    if matches_keep "$(basename "$p")"; then kept=$((kept+1)); fi
  done
fi
if [ "$MODE" = "list" ]; then
  log "Slug presenti in $PROJ (sola lettura, nessuna rimozione):"
  if [ "$total" -eq 0 ]; then
    log "  (nessuno)"
  else
    for p in "$PROJ"/*/; do
      [ -d "$p" ] || continue
      b="$(basename "$p")"
      if matches_keep "$b"; then log "  [KEEP] $b"; else log "  [WIPE] $b"; fi
    done
  fi
  log "Totale $total, preservati $kept, da rimuovere $((total - kept))."
  if [ "$KEEP_CONFIGURED" -eq 0 ]; then
    log "KEEP_PREFIXES non e' ancora compilato: finche' resta cosi' lo script rifiuta di rimuovere."
    log "Scegli i prefissi dagli slug qui sopra, uno per ogni radice di sviluppo da preservare."
  else
    log "KEEP_PREFIXES attuali: $KEEP_PREFIXES"
  fi
  exit 0
fi
if [ "$total" -gt 0 ] && [ "$kept" -eq 0 ] && [ "$ALLOW_EMPTY_KEEP" != "1" ]; then
  abort "nessuno dei $total slug in $PROJ corrisponde a KEEP_PREFIXES ('$KEEP_PREFIXES'): la configurazione e' di un'altra macchina. Esegui '--list' e correggi i prefissi; se l'insieme vuoto e' voluto, imposta ALLOW_EMPTY_KEEP=1."
fi
log "Progetti: $total totali, $kept preservati, $((total - kept)) da rimuovere."

rm_path() {
  if [ "$MODE" = "dry" ]; then
    if [ -e "$1" ]; then log "  [dry-run] rm -rf $1"; fi
  else
    rm -rf "$1"
  fi
  return 0
}
rm_file() {
  if [ "$MODE" = "dry" ]; then
    if [ -e "$1" ]; then log "  [dry-run] rm -f $1"; fi
  else
    rm -f "$1"
  fi
  return 0
}

# --- 1) progetti: rimuovi transcript + memoria nascosta di tutto tranne i prefissi preservati ---
if [ -d "$PROJ" ]; then
  for p in "$PROJ"/*/; do
    [ -d "$p" ] || continue
    if matches_keep "$(basename "$p")"; then continue; fi
    rm_path "$p"
  done
fi

# --- 2) store per-account effimeri ---
# Per conservare resume/undo dei progetti preservati tra una sessione e l'altra, togli
# 'sessions' e 'file-history' dalla lista. 'daemon', 'skills', 'plugins' e 'hooks'
# restano fuori: sono stato vivo o configurazione, non residui di sessione.
for e in sessions session-env shell-snapshots file-history plans tasks paste-cache \
         backups memory cache jobs ide todos statsig telemetry; do
  rm_path "${BASE:?}/$e"
done
rm_file "$BASE/history.jsonl"
rm_file "$BASE/mcp-needs-auth-cache.json"

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
    if matches_keep "$b"; then continue; fi
    rm_path "$p"
  done
fi

# --- 4) .claude.json: rimuovi le voci 'projects' dei percorsi non preservati ---
# Senza questo passaggio l'elenco dei percorsi aperti sopravvive al wipe. Il file
# custodisce login e configurazione, quindi la modifica e' delegata a
# scrub-claude-json.js, che valida il risultato prima di sostituire l'originale. Se Node
# non c'e', il passaggio si salta senza toccare il file. Si ripulisce anche l'eventuale
# .backup, che altrimenti conserverebbe le stesse voci.
# Percorso di .claude.json: con CLAUDE_CONFIG_DIR impostato sta DENTRO la home
# dell'account; nella home di default sta invece accanto ad essa, in $HOME/.claude.json.
CFG_FILE="$BASE/.claude.json"
if [ ! -f "$CFG_FILE" ] && [ -f "$HOME/.claude.json" ]; then CFG_FILE="$HOME/.claude.json"; fi
case "${KEEP_PATH_PREFIXES[0]:-}" in
  ""|*"<"*">"*)
    log "Blocco 4 saltato: KEEP_PATH_PREFIXES non compilato, .claude.json resta intatto."
    ;;
  *)
    SCRUB_JS="$BASE/hooks/scrub-claude-json.js"
    if [ -f "$SCRUB_JS" ] && command -v node >/dev/null 2>&1; then
      for target in "$CFG_FILE" "$CFG_FILE.backup"; do
        [ -f "$target" ] || continue
        if [ "$MODE" = "dry" ]; then
          log "  [dry-run] node scrub-claude-json.js $target ${KEEP_PATH_PREFIXES[*]}"
        else
          node "$SCRUB_JS" "$target" "${KEEP_PATH_PREFIXES[@]}" >/dev/null 2>&1
          rm -f "$target.tmp"
        fi
      done
    else
      log "Blocco 4 saltato: scrub-claude-json.js o node non disponibili."
    fi
    ;;
esac

log "Fatto."
