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
#   - dal 2026-10-09 cio' che appartiene a una sessione ancora aperta, di qualunque
#     account (blocco 0.4): serve stato-magazzino.py accanto e python3, altrimenti il
#     wipe rimanda tutto finche' e' aperta un'altra sessione
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
# Solo per le prove (tests/test_wipe_per_sessione_linux.py): home, radice temporanea e
# cache dei log MCP finte al posto di quelle compilate, passate nell'ambiente.
if [ -n "${BASE_PROVA:-}" ]; then BASE="$BASE_PROVA"; fi

# --- modo di esecuzione -----------------------------------------------------
MODE="wipe"
FORZA=0
ATTENDI_PID=""      # interno: la copia rilanciata dal modo hook attende la fine di questo PID
SESS_CHIUSA=""      # interno: la sessione chiusa dall'hook, che non si protegge
for arg in "$@"; do
  case "$arg" in
    --dry-run) MODE="dry"  ;;
    --list)    MODE="list" ;;
    --forza)   FORZA=1     ;;
    --attendi-pid=*) ATTENDI_PID="${arg#*=}" ;;
    --sessione-chiusa=*) SESS_CHIUSA="${arg#*=}" ;;
    *) echo "uso: $(basename "$0") [--dry-run|--list] [--forza]" >&2; exit 2 ;;
  esac
done

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
# Le prove a vuoto e il modo --list scrivono in un diario a parte, come nella gemella .ps1.
if [ "$MODE" = "wipe" ]; then LOG="$BASE/session-end-wipe.log"; else LOG="$BASE/session-end-wipe.prova.log"; fi
# La copia rilanciata dal modo hook continua il diario della corsa che l'ha lanciata.
if [ -z "$ATTENDI_PID" ]; then : >"$LOG" 2>/dev/null || LOG=""; fi
log "session-end-wipe: $(date '+%Y-%m-%d %H:%M:%S')  modo=$MODE  base=$BASE"

# 0.2 la configurazione e' stata compilata. Il segnaposto non si sostituisce da solo, e
# un KEEP_PREFIXES vuoto significherebbe "non preservare niente". La guardia non vale in
# modo '--list', che e' proprio il comando con cui si scopre che cosa configurare: li'
# la mancanza si segnala e si prosegue in sola lettura.
KEEP_CONFIGURED=1
case "$KEEP_PREFIXES" in
  ""|*"<"*">"*) KEEP_CONFIGURED=0; KEEP_PREFIXES="" ;;
esac
# ALLOW_EMPTY_KEEP=1 rende "non preservare niente" una scelta dichiarata, come
# $allowEmptyKeep della gemella .ps1, e vale per questa guardia e per la 0.3. Fino al
# 2026-10-09 valeva solo per la 0.3, e su POSIX l'insieme vuoto, che e' la forma normale
# perche' la memoria di un progetto vive nel progetto, non si poteva configurare.
if [ "$KEEP_CONFIGURED" -eq 0 ] && [ "$MODE" != "list" ] && [ "$ALLOW_EMPTY_KEEP" != "1" ]; then
  abort "KEEP_PREFIXES non compilato. Esegui '--list' per vedere gli slug presenti in questo account, poi scegli cosa preservare; se non si vuole preservare nulla, ALLOW_EMPTY_KEEP=1."
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

# 0.4 le sessioni ancora aperte. Stessa storia e stesse regole della gemella .ps1, dove
# sono spiegate per esteso: fino al 2026-10-05 il wipe toglieva tutto anche alle sessioni
# aperte, dal 2026-10-05 rimandava tutto ("chi chiude per ultimo pulisce") e lasciava il
# magazzino a meta', dal 2026-10-09 lavora PER SESSIONE. Toglie subito cio' che appartiene a
# sessioni chiuse e conserva cio' che appartiene a una sessione con un processo vivo, come
# lo decide stato-magazzino.py nella stessa cartella; senza python3 o senza lo strumento si
# torna al rinvio totale. --forza ignora le sessioni aperte.
#
# Modo hook o modo manuale: lanciato dall'hook SessionEnd lo script riceve su stdin il
# payload dell'evento, e la sessione da cui discende sta chiudendo e si pulisce; lanciato a
# mano, anche dal terminale di una sessione aperta, quella sessione e' viva e si protegge.
# La lettura ha un limite di due secondi, perche' uno stdin rediretto che nessuno chiude
# la terrebbe ferma per sempre (successo il 2026-10-09 con la gemella .ps1).
MODO_HOOK=0
if [ ! -t 0 ]; then
  PAYLOAD=""
  IFS= read -r -t 2 -d '' PAYLOAD || true
  case "$PAYLOAD" in *'"hook_event_name"'*'"SessionEnd"'*) MODO_HOOK=1 ;; esac
fi
if [ "$MODO_HOOK" = "1" ] && [ -z "$SESS_CHIUSA" ]; then
  SESS_CHIUSA="$(printf '%s' "$PAYLOAD" | sed -n 's/.*"session_id"[[:space:]]*:[[:space:]]*"\([0-9A-Za-z-]*\)".*/\1/p' | head -n 1)"
fi
# Il modo hook non lavora dentro l'hook, come nella gemella .ps1 dove la ragione e' scritta
# per esteso: si rilancia staccato dall'albero dei processi di Claude, con setsid dove c'e',
# e la copia rilanciata attende che il processo della sessione in chiusura sia uscito.
if [ "$MODO_HOOK" = "1" ] && [ "$MODE" = "wipe" ] && [ -z "$ATTENDI_PID" ]; then
  CLAUDE_PID="$(ps -eo pid=,ppid=,args= 2>/dev/null | awk -v self="$$" '
    { pid[$1] = $2; a = $0; sub(/^[ \t]*[0-9]+[ \t]+[0-9]+[ \t]+/, "", a); args[$1] = a }
    END {
      p = pid[self]; n = 0
      while ((p in pid) && n < 64) {
        split(args[p], w, " ")
        if (w[1] ~ /(^|\/)claude(\.exe)?$/ || args[p] ~ /@anthropic-ai\/claude-code/) { print p; exit }
        p = pid[p]; n++
      }
    }')"
  if [ -n "$CLAUDE_PID" ]; then
    EXTRA=()
    [ "$FORZA" = "1" ] && EXTRA+=(--forza)
    [ -n "$SESS_CHIUSA" ] && EXTRA+=("--sessione-chiusa=$SESS_CHIUSA")
    if command -v setsid >/dev/null 2>&1; then
      setsid bash "$0" "--attendi-pid=$CLAUDE_PID" ${EXTRA[@]+"${EXTRA[@]}"} </dev/null >/dev/null 2>&1 &
    else
      nohup bash "$0" "--attendi-pid=$CLAUDE_PID" ${EXTRA[@]+"${EXTRA[@]}"} </dev/null >/dev/null 2>&1 &
    fi
    log "Modo hook: SessionEnd della sessione ${SESS_CHIUSA:-?}. Rilanciato fuori dall'hook come PID $!, che attende la fine del PID $CLAUDE_PID e poi pulisce."
    exit 0
  fi
fi
if [ -n "$ATTENDI_PID" ]; then
  attesa=0
  while kill -0 "$ATTENDI_PID" 2>/dev/null && [ "$attesa" -lt 480 ]; do sleep 0.25; attesa=$((attesa + 1)); done
  if kill -0 "$ATTENDI_PID" 2>/dev/null; then log "Il PID $ATTENDI_PID e' ancora vivo dopo 120 s: si pulisce comunque, e la sua sessione conta come aperta."
  else log "Modo distaccato: il PID $ATTENDI_PID e' uscito, si pulisce."; fi
elif [ "$MODO_HOOK" = "1" ]; then log "Modo hook: SessionEnd della sessione ${SESS_CHIUSA:-?}, che si pulisce."
else log "Modo manuale: anche la sessione da cui eventualmente e' stato lanciato conta come aperta."; fi

altre_sessioni() {
  ps -eo pid=,ppid=,args= 2>/dev/null | awk -v self="$$" -v conanc="$1" '
    {
      pid[$1] = $2
      a = $0
      sub(/^[ \t]*[0-9]+[ \t]+[0-9]+[ \t]+/, "", a)
      args[$1] = a
    }
    END {
      p = self; n = 0
      while ((p in pid) && n < 64) { anc[p] = 1; p = pid[p]; n++ }
      for (k in args) {
        if ((k in anc) && conanc != "1") continue
        if (k == self) continue
        s = args[k]
        if (s ~ /--type=/) continue
        if (s ~ /stato-magazzino\.py/) continue
        split(s, w, " ")
        if (w[1] ~ /(^|\/)claude(\.exe)?$/ || s ~ /@anthropic-ai\/claude-code/) printf "%s ", k
      }
    }'
}
CON_ANTENATI=1
[ "$MODO_HOOK" = "1" ] && CON_ANTENATI=0
ALTRE="$(altre_sessioni "$CON_ANTENATI")"
ALTRE="${ALTRE% }"
PROT=0
PROT_IDS=""; PROT_PRIMO=""; PROT_VIVE=""; PROT_INCERTI=""; PROT_ACCOUNT_VIVI=""; PROT_DETTAGLI=""
PROT_SLUG_ACCOUNT=""; PROT_SLUG_COMUNE=""
if [ -n "$ALTRE" ] && [ "$FORZA" != "1" ]; then
  LIB="$(cd "$(dirname "$0")" && pwd)/stato-magazzino.py"
  if [ -f "$LIB" ] && command -v python3 >/dev/null 2>&1; then
    MANUALE=""
    [ "$MODO_HOOK" = "1" ] || MANUALE="--manuale"
    if ASSEGNA="$(python3 "$LIB" --protezione-sh --radice "$(dirname "$BASE")" $MANUALE 2>/dev/null)"; then
      eval "$ASSEGNA"
      PROT=1
      if [ -n "$SESS_CHIUSA" ]; then
        case " $PROT_IDS " in *" $SESS_CHIUSA "*)
          PROT_IDS="$(for i in $PROT_IDS; do [ "$i" = "$SESS_CHIUSA" ] || printf '%s ' "$i"; done)"
          log "La sessione $SESS_CHIUSA e' quella chiusa dall'hook: non si protegge, anche se candidata di un processo senza file di sessione." ;;
        esac
      fi
    fi
  fi
  if [ "$PROT" != "1" ]; then
    log "Rimandato: altre sessioni di Claude Code aperte (PID $ALTRE). Senza python3 e stato-magazzino.py accanto a questo script non si sa che cosa appartenga a loro, e cancellare ora toglierebbe scratchpad e piani a sessioni ancora al lavoro: pulira' l'ultima sessione che si chiude, oppure un'esecuzione manuale con --forza."
    if [ "$MODE" != "dry" ]; then
      log "Nessuna rimozione eseguita."
      exit 0
    fi
    log "  [dry-run] in un'esecuzione reale lo script si fermerebbe qui; segue cio' che farebbe con --forza."
  else
    n_ids=0; for _i in $PROT_IDS; do n_ids=$((n_ids + 1)); done
    log "Sessioni aperte: PID $PROT_VIVE, di cui senza file di sessione: ${PROT_INCERTI:-nessuna}. Si toglie cio' che appartiene a sessioni chiuse."
    log "Conservate $n_ids sessioni, e cio' che non porta il nome di una sessione se scritto dopo l'epoch ${PROT_PRIMO:-?}: $PROT_DETTAGLI"
  fi
elif [ -n "$ALTRE" ]; then
  log "--forza: sessioni aperte ignorate (PID $ALTRE)."
fi

# Le radici consentite: nessuna rimozione fuori da queste, come la guardia di ultima
# istanza della gemella .ps1.
TMP_ROOT="${TEMP_PROVA:-${TMPDIR:-/tmp}/claude}"
TMP_ROOT="${TMP_ROOT%/}"
if [ -n "${MCP_PROVA:-}" ]; then MCP_ROOT="${MCP_PROVA%/}"
elif [ -n "${TEMP_PROVA:-}" ]; then MCP_ROOT=""
elif [ "$(uname -s)" = "Darwin" ]; then MCP_ROOT="$HOME/Library/Caches/claude-cli-nodejs"
else MCP_ROOT="${XDG_CACHE_HOME:-$HOME/.cache}/claude-cli-nodejs"; fi
dentro_perimetro() {
  case "$1" in
    "$BASE"/*|"$TMP_ROOT"/*) return 0 ;;
  esac
  if [ -n "$MCP_ROOT" ]; then case "$1" in "$MCP_ROOT"/*) return 0 ;; esac; fi
  return 1
}
RIMOSSI=0; CONSERVATI=0; CATEGORIE=""
# La categoria di un percorso, per il riepilogo del diario: il primo livello sotto la home
# dell'account, oppure scratchpad e log-MCP per le due radici comuni.
categoria_di() {
  case "$1" in
    "$TMP_ROOT"/*) echo scratchpad; return ;;
  esac
  if [ -n "$MCP_ROOT" ]; then case "$1" in "$MCP_ROOT"/*) echo log-MCP; return ;; esac; fi
  local r="${1#"$BASE"/}"
  echo "${r%%/*}"
}
rm_path() {
  local p="${1%/}"
  [ -e "$p" ] || [ -L "$p" ] || return 0
  if ! dentro_perimetro "$p"; then abort "RIFIUTO: '$p' e' fuori dalle radici consentite ($BASE ; $TMP_ROOT ; $MCP_ROOT)."; fi
  RIMOSSI=$((RIMOSSI + 1))
  CATEGORIE="$CATEGORIE$(categoria_di "$p")
"
  if [ "$MODE" = "dry" ]; then log "  [dry-run] rm -rf $p"; else rm -rf "$p"; fi
  return 0
}
rm_file() { rm_path "$1"; }

# Un nome e' "di sessione" se inizia con un identificativo di sessione, intero o nella
# forma breve di otto cifre esadecimali (jobs/); protetto se corrisponde a una sessione da
# conservare in uno dei tre versi della gemella .ps1.
nome_di_sessione() { [[ "$1" =~ ^[0-9a-f]{8}(-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})?([-.].*)?$ ]]; }
protetta() {
  local n="$1" id
  [ "$PROT" = "1" ] || return 1
  for id in $PROT_IDS; do
    [ "$n" = "$id" ] && return 0
    case "$n" in "$id"-*|"$id".*) return 0 ;; esac
    if [ "${#n}" -eq 8 ]; then case "$id" in "$n"*) return 0 ;; esac; fi
  done
  return 1
}
mtime_di() { stat -c %Y "$1" 2>/dev/null || stat -f %m "$1" 2>/dev/null || echo 0; }
recente() { [ "$PROT" = "1" ] && [ -n "$PROT_PRIMO" ] && [ "$(mtime_di "$1")" -ge "$PROT_PRIMO" ]; }
# Per un progetto di un processo vivo senza file di sessione ma con account e cartella noti
# (stato-magazzino.py): l'avvio del processo in secondi epoch, oppure niente. $1 e' la
# chiave ('account|slug' oppure 'slug'), $2 la tabella.
avvio_slug() {
  local k e chiave
  chiave="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"
  for e in $2; do
    k="${e%=*}"
    if [ "$k" = "$chiave" ]; then echo "${e##*=}"; return 0; fi
  done
  return 1
}
# Vero se sotto l'elemento qualcosa e' stato scritto dopo l'istante $2 (epoch): la data di
# una cartella non cambia quando si scrive in una sua sottocartella.
scritto_dopo() {
  if [ "$(mtime_di "$1")" -ge "$2" ]; then return 0; fi
  [ -d "$1" ] || return 1
  [ -n "$(find "$1" -newermt "@$2" -print 2>/dev/null | head -n 1)" ]
}
da_conservare() {
  local b n
  [ "$PROT" = "1" ] || return 1
  b="$(basename "$1")"
  if [ -d "$1" ]; then n="$b"; else n="${b%.*}"; fi
  if nome_di_sessione "$n"; then protetta "$n"; else recente "$1"; fi
}
# Svuota una cartella mista conservando i figli da conservare; la toglie se resta vuota.
pulisci_mista() {
  local d="${1%/}" f tenuti=0
  [ -e "$d" ] || return 0
  if [ "$PROT" != "1" ]; then rm_path "$d"; return 0; fi
  for f in "$d"/* "$d"/.[!.]*; do
    [ -e "$f" ] || continue
    if da_conservare "$f"; then tenuti=$((tenuti + 1)); CONSERVATI=$((CONSERVATI + 1)); else rm_path "$f"; fi
  done
  [ "$tenuti" -eq 0 ] && rm_path "$d"
  return 0
}

# --- 1) progetti: verbali e memoria nascosta, tranne i prefissi preservati e le sessioni aperte ---
NOME_ACCOUNT_P="$(basename "$BASE")"
[ "$NOME_ACCOUNT_P" = ".claude" ] || NOME_ACCOUNT_P="${NOME_ACCOUNT_P#.claude-}"
if [ -d "$PROJ" ]; then
  for p in "$PROJ"/*/; do
    [ -d "$p" ] || continue
    if matches_keep "$(basename "$p")"; then continue; fi
    if [ "$PROT" != "1" ]; then rm_path "$p"; continue; fi
    avvio_p="$(avvio_slug "$NOME_ACCOUNT_P|$(basename "$p")" "$PROT_SLUG_ACCOUNT" || true)"
    tenuti=0
    for f in "${p%/}"/* "${p%/}"/.[!.]*; do
      [ -e "$f" ] || continue
      b="$(basename "$f")"; n="${b%.jsonl}"
      tieni=0
      if nome_di_sessione "$n" && protetta "$n"; then tieni=1
      elif [ -n "$avvio_p" ] && nome_di_sessione "$n" && scritto_dopo "$f" "$avvio_p"; then tieni=1; fi
      if [ "$tieni" = "1" ]; then tenuti=$((tenuti + 1)); CONSERVATI=$((CONSERVATI + 1)); else rm_path "$f"; fi
    done
    [ "$tenuti" -eq 0 ] && rm_path "$p"
  done
fi

# --- 2) store per-account effimeri ---
# 'daemon', 'skills', 'plugins' e 'hooks' restano fuori: sono stato vivo o configurazione.
# 'sessions' ha un file per processo vivo: si tolgono quelli dei processi che non ci sono piu'.
for e in session-env shell-snapshots file-history plans tasks paste-cache \
         backups memory cache jobs ide todos statsig telemetry; do
  pulisci_mista "${BASE:?}/$e"
done
if [ -d "$BASE/sessions" ]; then
  if [ "$PROT" != "1" ]; then rm_path "$BASE/sessions"
  else
    for f in "$BASE/sessions"/*; do
      [ -e "$f" ] || continue
      pid_f="$(basename "$f")"; pid_f="${pid_f%%.*}"
      case " $PROT_VIVE " in *" $pid_f "*) CONSERVATI=$((CONSERVATI + 1)) ;; *) rm_path "$f" ;; esac
    done
  fi
fi
# history.jsonl: con sessioni aperte restano le sole righe delle sessioni protette, e quelle
# senza sessionId solo se scritte dopo il primo avvio vivo. Lo fa python3, che c'e' per
# costruzione quando PROT vale 1.
HIST="$BASE/history.jsonl"
if [ -f "$HIST" ]; then
  if [ "$PROT" != "1" ]; then rm_file "$HIST"
  elif [ "$MODE" = "dry" ]; then log "  [dry-run] history.jsonl: si tengono le righe delle sessioni protette"
  else
    python3 - "$HIST" "$PROT_IDS" "${PROT_PRIMO:-0}" <<'PYEOF'
import json, os, re, sys
path, ids, primo = sys.argv[1], sys.argv[2].split(), int(sys.argv[3] or 0) * 1000
def protetta(n):
    return any(n == i or n.startswith(i + '-') or n.startswith(i + '.') or (len(n) == 8 and i.startswith(n)) for i in ids)
righe = open(path, encoding='utf-8', errors='replace').read().splitlines()
tenute = []
for r in righe:
    m = re.search(r'"sessionId"\s*:\s*"([^"]+)"', r)
    if m:
        if protetta(m.group(1)): tenute.append(r)
        continue
    m = re.search(r'"timestamp"\s*:\s*(\d+)', r)
    if m and int(m.group(1)) >= primo: tenute.append(r)
if not tenute:
    os.remove(path)
elif len(tenute) < len(righe):
    tmp = path + '.tmp'
    open(tmp, 'w', encoding='utf-8', newline='\n').write('\n'.join(tenute) + '\n')
    os.replace(tmp, path)
PYEOF
  fi
fi
if [ -f "$BASE/mcp-needs-auth-cache.json" ] && ! recente "$BASE/mcp-needs-auth-cache.json"; then rm_file "$BASE/mcp-needs-auth-cache.json"; fi

# --- 3) scratchpad temporanei: $TMPDIR/claude/<slug-progetto>/<id-sessione> ---
# La radice e' condivisa fra tutti gli account della stessa utenza, ed e' per questo che
# l'insieme delle sessioni protette si calcola su tutti gli account. Si toccano solo le
# cartelle che sembrano slug di progetto: 'X--...' con la convenzione Windows, '-...' su
# POSIX, dove derivano da un percorso assoluto.
if [ -d "$TMP_ROOT" ]; then
  for p in "$TMP_ROOT"/*/; do
    [ -d "$p" ] || continue
    b="$(basename "$p")"
    case "$b" in [A-Za-z]--*|-*) ;; *) continue ;; esac
    if matches_keep "$b"; then continue; fi
    avvio_p=""
    [ "$PROT" = "1" ] && avvio_p="$(avvio_slug "$b" "$PROT_SLUG_COMUNE" || true)"
    if [ -z "$avvio_p" ]; then pulisci_mista "$p"; continue; fi
    # progetto di un processo vivo senza file di sessione: si conserva anche cio' che e'
    # stato scritto dopo il suo avvio, perche' il nome della sua sessione non si conosce
    tenuti=0
    for f in "${p%/}"/* "${p%/}"/.[!.]*; do
      [ -e "$f" ] || continue
      if da_conservare "$f" || scritto_dopo "$f" "$avvio_p"; then tenuti=$((tenuti + 1)); CONSERVATI=$((CONSERVATI + 1)); else rm_path "$f"; fi
    done
    [ "$tenuti" -eq 0 ] && rm_path "$p"
  done
fi

# --- 3b) log dei server MCP: <cache>/claude-cli-nodejs/<slug-progetto> ---
# Aggiunto il 2026-10-09. La cartella e' quella che la libreria env-paths di Node assegna
# a 'claude-cli' con il suffisso 'nodejs': su Windows e' stata osservata in
# %LOCALAPPDATA%\claude-cli-nodejs\Cache; su Linux ${XDG_CACHE_HOME:-~/.cache}/claude-cli-nodejs
# e' stato verificato il 2026-10-09 su Ubuntu con Claude Code 2.1.295, XDG_CACHE_HOME
# compresa; su macOS il percorso qui sotto resta inferito dalla convenzione di env-paths.
# Sono per progetto, non per sessione: con sessioni aperte si tolgono i file scritti prima
# dell'avvio del processo vivo piu' vecchio e le cartelle rimaste vuote.
if [ -n "$MCP_ROOT" ] && [ -d "$MCP_ROOT" ]; then
  for p in "$MCP_ROOT"/*/; do
    [ -d "$p" ] || continue
    if matches_keep "$(basename "$p")"; then continue; fi
    if [ "$PROT" != "1" ]; then rm_path "$p"; continue; fi
    while IFS= read -r f; do
      if recente "$f"; then CONSERVATI=$((CONSERVATI + 1)); else rm_path "$f"; fi
    done < <(find "${p%/}" -type f 2>/dev/null)
    if [ "$MODE" != "dry" ]; then
      find "${p%/}" -mindepth 1 -depth -type d -empty -exec rmdir {} \; 2>/dev/null
      rmdir "${p%/}" 2>/dev/null || true
    fi
  done
fi

# --- 4) .claude.json: voci 'projects' dei percorsi non preservati, metriche di quelli preservati ---
# Il file custodisce login e configurazione, quindi la modifica e' delegata a
# scrub-claude-json.js, che valida il risultato prima di sostituire l'originale; con
# --solo-config dalle voci preservate si tolgono anche le metriche dell'ultima sessione. Se
# Node non c'e', il passaggio si salta. Si rimanda se questo account ha una sessione aperta,
# che riscrive il file. Con CLAUDE_CONFIG_DIR il file sta DENTRO la home dell'account; nella
# home di default sta accanto ad essa, in $HOME/.claude.json.
CFG_FILE="$BASE/.claude.json"
if [ ! -f "$CFG_FILE" ] && [ -f "$HOME/.claude.json" ]; then CFG_FILE="$HOME/.claude.json"; fi
NOME_ACCOUNT="$(basename "$BASE")"
[ "$NOME_ACCOUNT" = ".claude" ] || NOME_ACCOUNT="${NOME_ACCOUNT#.claude-}"
case "${KEEP_PATH_PREFIXES[0]:-}" in
  ""|*"<"*">"*)
    log "Blocco 4 saltato: KEEP_PATH_PREFIXES non compilato, .claude.json resta intatto."
    ;;
  *)
    if [ "$PROT" = "1" ] && case " $PROT_ACCOUNT_VIVI " in *" $NOME_ACCOUNT "*) true ;; *) false ;; esac; then
      log "Blocco 4 rimandato: questo account ha una sessione aperta che riscrive .claude.json; lo pulira' la prossima chiusura."
    else
      SCRUB_JS="$BASE/hooks/scrub-claude-json.js"
      if [ -f "$SCRUB_JS" ] && command -v node >/dev/null 2>&1; then
        for target in "$CFG_FILE" "$CFG_FILE.backup"; do
          [ -f "$target" ] || continue
          if [ "$MODE" = "dry" ]; then
            log "  [dry-run] node scrub-claude-json.js $target --solo-config ${KEEP_PATH_PREFIXES[*]}"
          else
            node "$SCRUB_JS" "$target" --solo-config "${KEEP_PATH_PREFIXES[@]}" >/dev/null 2>&1
            rm -f "$target.tmp"
          fi
        done
      else
        log "Blocco 4 saltato: scrub-claude-json.js o node non disponibili."
      fi
    fi
    ;;
esac

log "Rimossi $RIMOSSI elementi, conservati $CONSERVATI."
if [ -n "$CATEGORIE" ]; then
  log "Rimossi per categoria: $(printf '%s' "$CATEGORIE" | sort | uniq -c | awk '{printf "%s%s %s", (NR > 1 ? ", " : ""), $2, $1}')."
fi
log "Fatto."
