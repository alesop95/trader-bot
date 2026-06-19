#!/usr/bin/env bash
# ============================================================================
# check-account-hygiene.sh  (variante POSIX di check-account-hygiene.ps1)
# Verifica, in sola lettura, che l'ACCOUNT Claude Code ATTIVO rispetti l'igiene
# del magazzino nascosto richiesta dal sistema:
#   1. "autoMemoryEnabled": false
#   2. hook SessionEnd -> session-end-wipe
# Da eseguire al Passo 0 dell'inizializzazione/allineamento di un progetto.
# Esce 0 se in regola, 1 altrimenti. Usa python3 se disponibile, con fallback grep.
# ============================================================================
set -u
CFG="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
SETTINGS="$CFG/settings.json"
echo "Account attivo (CLAUDE_CONFIG_DIR): $CFG"
[ -f "$SETTINGS" ] || { echo "FAIL: settings.json non trovato in $CFG"; exit 1; }

ok_mem=1; ok_hook=1
if command -v python3 >/dev/null 2>&1; then
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
else
  grep -Eq '"autoMemoryEnabled"[[:space:]]*:[[:space:]]*false' "$SETTINGS" && ok_mem=0
  grep -q 'session-end-wipe' "$SETTINGS" && ok_hook=0
fi

[ "$ok_mem" = "0" ]  && echo "[PASS] autoMemoryEnabled = false" || echo "[FAIL] autoMemoryEnabled = false"
[ "$ok_hook" = "0" ] && echo "[PASS] hook SessionEnd -> session-end-wipe" || echo "[FAIL] hook SessionEnd -> session-end-wipe"

if [ "$ok_mem" = "0" ] && [ "$ok_hook" = "0" ]; then
  echo; echo "OK: l'account attivo e' in regola."; exit 0
fi
echo; echo "AZIONE RICHIESTA: l'account attivo NON e' in regola."
[ "$ok_mem"  = "0" ] || echo ' - aggiungi  "autoMemoryEnabled": false  al settings.json dell'\''account'
[ "$ok_hook" = "0" ] || echo ' - installa session-end-wipe.sh e registra un hook SessionEnd che lo esegua'
echo '   (riferimenti: templates/tools/session-end-wipe.sh e PROJECT-SYSTEM.md sezione 15)'
exit 1
