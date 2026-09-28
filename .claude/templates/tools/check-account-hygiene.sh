#!/usr/bin/env bash
# ============================================================================
# check-account-hygiene.sh  (variante POSIX di check-account-hygiene.ps1)
# Verifica, in sola lettura, che l'ACCOUNT Claude Code ATTIVO rispetti l'igiene
# del magazzino nascosto richiesta dal sistema:
#   1. "autoMemoryEnabled": false
#   2. hook SessionEnd -> session-end-wipe
#   3. lo script di wipe installato e' configurato per QUESTA macchina
# Da eseguire al Passo 0 dell'inizializzazione/allineamento di un progetto.
# Esce 0 se in regola, 1 altrimenti. Usa python3 se disponibile, con fallback grep.
# ============================================================================
set -u
CFG="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
SETTINGS="$CFG/settings.json"
echo "Account attivo (CLAUDE_CONFIG_DIR): $CFG"
[ -f "$SETTINGS" ] || { echo "FAIL: settings.json non trovato in $CFG"; exit 1; }

ok_mem=1; ok_hook=1
# Non basta che 'python3' sia sul PATH: su Windows con Git Bash quel nome e' spesso
# l'alias fittizio del Microsoft Store, che si limita a stampare un invito a installare
# e non esegue niente. Lo si prova davvero, e in caso contrario si ricade su grep.
have_python=0
if command -v python3 >/dev/null 2>&1 && python3 -c 'pass' >/dev/null 2>&1; then have_python=1; fi
if [ "$have_python" = "1" ]; then
  ok_mem=$(python3 - "$SETTINGS" <<'PY'
import json,sys
d=json.load(open(sys.argv[1],encoding="utf-8"))
print("0" if d.get("autoMemoryEnabled") is False else "1")
PY
)
  ok_hook=$(python3 - "$SETTINGS" <<'PY'
import json,sys
d=json.load(open(sys.argv[1],encoding="utf-8"))
cmds=[]
for g in (d.get("hooks",{}) or {}).get("SessionEnd",[]) or []:
    for h in g.get("hooks",[]) or []:
        cmds.append(h.get("command",""))
print("0" if any("session-end-wipe" in c for c in cmds) else "1")
PY
)
fi
# Se python3 non c'era, o se per qualunque ragione non ha prodotto un esito leggibile,
# si ricade sul controllo testuale invece di lasciare un FAIL che non significa niente.
case "$ok_mem" in 0|1) ;; *) ok_mem=1; grep -Eq '"autoMemoryEnabled"[[:space:]]*:[[:space:]]*false' "$SETTINGS" && ok_mem=0 ;; esac
case "$ok_hook" in 0|1) ;; *) ok_hook=1; grep -q 'session-end-wipe' "$SETTINGS" && ok_hook=0 ;; esac
if [ "$have_python" != "1" ]; then
  ok_mem=1;  grep -Eq '"autoMemoryEnabled"[[:space:]]*:[[:space:]]*false' "$SETTINGS" && ok_mem=0
  ok_hook=1; grep -q 'session-end-wipe' "$SETTINGS" && ok_hook=0
fi

# --- 3. lo script di wipe installato parla di QUESTA macchina --------------------
# Un hook registrato non basta: lo script puo' essere il template non compilato, oppure
# una copia presa da un'altra macchina con prefissi che qui non corrispondono a niente.
# In quel secondo caso l'insieme dei progetti preservati e' vuoto e il wipe, se le sue
# guardie non lo fermassero, cancellerebbe l'intero magazzino. Il controllo e' in sola
# lettura: invoca lo script installato in modo '--list', che non rimuove nulla.
ok_cfg=1
cfg_note=""
WIPE="$CFG/hooks/session-end-wipe.sh"
if [ ! -f "$WIPE" ]; then
  WIPE="$(grep -o '[^ "]*session-end-wipe\.sh' "$SETTINGS" 2>/dev/null | head -n 1)"
fi
if [ "$ok_hook" != "0" ]; then
  cfg_note="hook assente, niente da verificare"
elif [ -z "$WIPE" ] || [ ! -f "$WIPE" ]; then
  cfg_note="script di wipe non trovato nell'account"
elif grep -q '^KEEP_PREFIXES="<' "$WIPE"; then
  cfg_note="il template e' installato ma NON compilato: KEEP_PREFIXES e' ancora il segnaposto"
else
  listing="$(bash "$WIPE" --list 2>&1)"
  totale="$(printf '%s' "$listing" | sed -n 's/^Totale \([0-9]*\), preservati \([0-9]*\).*/\1/p' | head -n 1)"
  preservati="$(printf '%s' "$listing" | sed -n 's/^Totale \([0-9]*\), preservati \([0-9]*\).*/\2/p' | head -n 1)"
  if [ -z "$totale" ]; then
    cfg_note="lo script installato non risponde a '--list': e' una versione precedente, priva delle guardie"
  elif [ "$totale" -gt 0 ] && [ "$preservati" -eq 0 ] && ! grep -q '^ALLOW_EMPTY_KEEP="\${ALLOW_EMPTY_KEEP:-1}"' "$WIPE"; then
    cfg_note="nessuno dei $totale slug presenti corrisponde ai prefissi configurati: la configurazione e' di un'altra macchina"
  else
    ok_cfg=0
    cfg_note="$preservati slug preservati su $totale"
  fi
fi

[ "$ok_mem" = "0" ]  && echo "[PASS] autoMemoryEnabled = false" || echo "[FAIL] autoMemoryEnabled = false"
[ "$ok_hook" = "0" ] && echo "[PASS] hook SessionEnd -> session-end-wipe" || echo "[FAIL] hook SessionEnd -> session-end-wipe"
[ "$ok_cfg" = "0" ]  && echo "[PASS] wipe configurato per questa macchina ($cfg_note)" || echo "[FAIL] wipe configurato per questa macchina ($cfg_note)"

if [ "$ok_mem" = "0" ] && [ "$ok_hook" = "0" ] && [ "$ok_cfg" = "0" ]; then
  echo; echo "OK: l'account attivo e' in regola."; exit 0
fi
echo; echo "AZIONE RICHIESTA: l'account attivo NON e' in regola."
[ "$ok_mem"  = "0" ] || echo ' - aggiungi  "autoMemoryEnabled": false  al settings.json dell'\''account'
[ "$ok_hook" = "0" ] || echo ' - installa session-end-wipe.sh e registra un hook SessionEnd che lo esegua'
[ "$ok_cfg"  = "0" ] || echo " - compila KEEP_PREFIXES nello script installato: 'bash \"$WIPE\" --list' elenca gli slug presenti, senza rimuovere niente"
echo '   (riferimenti: templates/tools/session-end-wipe.sh e PROJECT-SYSTEM.md sezione 15)'
exit 1
