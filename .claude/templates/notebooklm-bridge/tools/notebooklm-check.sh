#!/usr/bin/env bash
#
# notebooklm-check.sh - Verifica di disponibilita' di NotebookLM (piano gratuito) per il
# pacchetto notebooklm-bridge. Variante Linux; la variante Windows e' notebooklm-check.ps1.
#
# Enumera i browser Chromium presenti (Chrome, Chromium, Edge) e, per ciascuno, legge dal file
# "Local State" i profili con nome ed email dell'account Google, per mostrare quali account sono
# candidati all'uso di NotebookLM. Segnala se esiste gia' un profilo persistito del server di
# automazione notebooklm-mcp e se nel .mcp.json del progetto risulta un MCP di automazione del
# browser.
#
# Cosa NON puo' fare: dall'esterno del browser non si conferma che un account sia loggato su
# NotebookLM. Quella conferma e' visiva: lo script chiude indicando lo screenshot di
# notebooklm.google.com loggato, che l'agente legge (regola manual-screenshots.md).
#
# Piano gratuito tassativo: nessuna API Enterprise a pagamento e' coinvolta.

set -euo pipefail

have_jq() { command -v jq >/dev/null 2>&1; }

read_profiles() {
    local local_state="$1" browser="$2"
    [ -f "$local_state" ] || return 0
    echo "  [$browser]"
    if have_jq; then
        jq -r '
          (.profile.info_cache // {}) | to_entries[]
          | "    - profilo \x27\(.value.name // .key)\x27  ->  \(.value.user_name // "(nessun account Google collegato al profilo)")"
        ' "$local_state" 2>/dev/null || echo "    Local State non parsabile"
    else
        echo "    (jq non installato: profili non elencabili in dettaglio; installa jq per il dettaglio)"
    fi
}

echo ''
echo "=== notebooklm-bridge: verifica di disponibilita' (NotebookLM gratuito) ==="
echo ''
echo 'Account Google candidati (dai profili dei browser Chromium):'

CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
CHROME_LS="$CONFIG_HOME/google-chrome/Local State"
CHROMIUM_LS="$CONFIG_HOME/chromium/Local State"
EDGE_LS="$CONFIG_HOME/microsoft-edge/Local State"

any_browser=0
for pair in "Chrome:$CHROME_LS" "Chromium:$CHROMIUM_LS" "Edge:$EDGE_LS"; do
    name="${pair%%:*}"; path="${pair#*:}"
    if [ -f "$path" ]; then any_browser=1; read_profiles "$path" "$name"; fi
done
[ "$any_browser" -eq 0 ] && echo '  nessun browser Chromium trovato: il modo manuale richiede un browser con un account Google loggato su NotebookLM'

echo ''
echo "Modo assistito (opzionale, community, zona grigia dei ToS):"

MCP_PROFILE="$HOME/.local/share/notebooklm-mcp/chrome_profile"
if [ -d "$MCP_PROFILE" ]; then
    echo "  - profilo notebooklm-mcp gia' presente: $MCP_PROFILE (login assistito probabilmente gia' persistito)"
else
    echo '  - nessun profilo notebooklm-mcp persistito'
fi

if [ -f .mcp.json ]; then
    grep -q 'notebooklm' .mcp.json && echo '  - .mcp.json contiene una voce notebooklm'
    grep -q 'playwright' .mcp.json && echo '  - .mcp.json contiene una voce playwright'
    if ! grep -q 'notebooklm' .mcp.json && ! grep -q 'playwright' .mcp.json; then
        echo '  - .mcp.json presente ma senza MCP di automazione del browser (notebooklm/playwright)'
    fi
else
    echo '  - nessun .mcp.json nel progetto: il modo assistito richiederebbe di connettere prima un MCP'
fi

echo ''
echo 'Passo manuale di conferma (obbligatorio):'
echo '  Lo stato di login non e verificabile da qui. Apri https://notebooklm.google.com'
echo "  loggato con l'account scelto e fornisci uno screenshot: l'agente lo legge per"
echo "  confermare l'account attivo prima di avviare il loop (regola manual-screenshots.md)."
echo ''
