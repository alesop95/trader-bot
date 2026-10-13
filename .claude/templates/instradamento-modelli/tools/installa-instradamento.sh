#!/usr/bin/env bash
# installa-instradamento.sh - gemella POSIX di installa-instradamento.ps1.
#
# Registra la mod instradamento-modelli in una o piu' radici (account) locali di
# Claude Code e vi depone la configurazione di partenza. La mod NON si copia
# dentro le radici: ogni account la carica dal percorso del template tramite
# env.CLAUDE_CODE_PLUGIN_DIRS nel proprio settings.json. Cio' che e' per account
# e' la configurazione, che vive in <radice>/instradamento-modelli.json.
#
# Uso:
#   ./installa-instradamento.sh [--account N]... [--includi-default]
#                               [--radice <percorso>]... [--mod <cartella>]
#                               [--verifica] [--rimuovi] [--forza]
#
# Senza --account serve le radici 1, 2 e 3, cioe' ~/.claude-account<N>.
# --radice sostituisce i numeri con percorsi espliciti: serve alle prove e alle
# installazioni dove la radice non segue quella convenzione.
#
# --verifica chiede lo stato a merge-instradamento-settings.js in modo --stato,
# che confronta percorsi normalizzati dopo JSON.parse. Cercare il percorso nel
# testo grezzo del settings.json da' la risposta sbagliata appena il percorso
# contiene una barra rovesciata, perche' il JSON la raddoppia.
set -euo pipefail

pacchetto="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mod="$pacchetto/mod"
riferimento="$pacchetto/instradamento-modelli.riferimento.json"
fusione="$pacchetto/tools/merge-instradamento-settings.js"
account=()
radici_esplicite=()
includi_default=0
verifica=0
rimuovi=0
forza=0

while [ $# -gt 0 ]; do
  case "$1" in
    --account) account+=("$2"); shift 2 ;;
    --includi-default) includi_default=1; shift ;;
    --radice) radici_esplicite+=("$2"); shift 2 ;;
    --mod) mod="$2"; shift 2 ;;
    --verifica) verifica=1; shift ;;
    --rimuovi) rimuovi=1; shift ;;
    --forza) forza=1; shift ;;
    -h|--help) sed -n '2,16p' "${BASH_SOURCE[0]}"; exit 0 ;;
    *) echo "ERRORE: argomento sconosciuto: $1" >&2; exit 1 ;;
  esac
done

if [ ${#account[@]} -eq 0 ]; then account=(1 2 3); fi

esci() { echo "ERRORE: $1" >&2; exit 1; }

[ -f "$mod/.claude-plugin/plugin.json" ] || esci "la cartella della mod non contiene .claude-plugin/plugin.json: $mod"
[ -f "$riferimento" ] || esci "manca la copia di riferimento: $riferimento"
[ -f "$fusione" ] || esci "manca lo script di fusione: $fusione"
command -v node >/dev/null 2>&1 || esci "serve Node.js: senza, ne' la scrittura del settings.json ne' la verifica sono affidabili"


radici=()
if [ ${#radici_esplicite[@]} -gt 0 ]; then
  radici=("${radici_esplicite[@]}")
else
  for n in "${account[@]}"; do radici+=("$HOME/.claude-account$n"); done
  if [ "$includi_default" -eq 1 ]; then radici+=("$HOME/.claude"); fi
fi

echo
echo "Mod: $mod"
echo

for radice in "${radici[@]}"; do
  nome="$(basename "$radice")"
  if [ ! -d "$radice" ]; then
    echo "$nome : saltata, la radice non esiste"
    continue
  fi

  impostazioni="$radice/settings.json"
  configurazione="$radice/instradamento-modelli.json"

  if [ "$verifica" -eq 1 ]; then
    stato="NON registrata"
    if [ -f "$impostazioni" ]; then
      risposta="$(node "$fusione" "$impostazioni" "$mod" --stato 2>&1)" && codice=0 || codice=$?
      if [ "$codice" -eq 0 ]; then stato="registrata"
      elif [ "$codice" -ne 3 ]; then esci "la verifica di $impostazioni e' fallita: $risposta"; fi
    fi
    modo="(nessuna configurazione)"
    if [ -f "$configurazione" ]; then
      modo="$(node -e 'try{process.stdout.write(String(JSON.parse(require("fs").readFileSync(process.argv[1],"utf8")).modo))}catch(e){process.stdout.write("(JSON non valido)")}' "$configurazione" 2>/dev/null || echo "(non letta)")"
    fi
    echo "$nome : mod $stato, modo $modo"
    continue
  fi

  if [ "$rimuovi" -eq 1 ]; then
    node "$fusione" "$impostazioni" "$mod" --rimuovi
    echo "$nome : la configurazione $configurazione resta sul disco, cancellala a mano se non serve"
    continue
  fi

  if [ -f "$configurazione" ] && [ "$forza" -eq 0 ]; then
    echo "$nome : configurazione gia' presente, lasciata com'e'"
  else
    cp "$riferimento" "$configurazione"
    echo "$nome : configurazione scritta in modo osserva"
  fi

  node "$fusione" "$impostazioni" "$mod"
  echo
done

if [ "$verifica" -eq 0 ] && [ "$rimuovi" -eq 0 ]; then
  echo "Fatto. Apri una sessione nuova (o lancia /reload-plugins) e poi /instradamento."
  echo "Si misura la linea di partenza in modo osserva, e solo dopo si passa a instrada."
fi
