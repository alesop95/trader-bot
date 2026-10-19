#!/usr/bin/env bash
# Rileva se un modello locale e' utilizzabile su questa macchina, e dice che cosa manca.
# Funziona su Linux nativo e dentro WSL. Su Windows si invoca attraverso Rileva-ModelloLocale.ps1, che entra in WSL.
# Sola lettura: non installa, non scarica, non avvia niente. Esce 0 se un modello e' pronto all'uso, 1 altrimenti.
set -u

VALORI="${1:-}"
COLI_DIR=""; MAGAZZINO=""; EXT4_SCRATCH=""
if [ -n "$VALORI" ] && [ -f "$VALORI" ]; then
  # shellcheck disable=SC1090
  . "$VALORI"
fi
: "${COLI_DIR:=$HOME/colibri/c}"
: "${MAGAZZINO:=$HOME/colibri-run}"

ok=0
riga() { printf '  %-22s %s\n' "$1" "$2"; }

echo "Rilevamento modello locale (colibri)"

# 1. Sistema operativo e, su Windows, il fatto di essere dentro WSL.
KERNEL="$(uname -r 2>/dev/null || echo sconosciuto)"
if printf '%s' "$KERNEL" | grep -qiE "microsoft|wsl"; then
  riga "ambiente" "Windows via WSL2 (kernel $KERNEL) - corretto: il modello gira qui, non su Windows nativo"
else
  riga "ambiente" "Linux nativo (kernel $KERNEL)"
fi

# 2. systemd, che serve al banco per limitare la RAM del processo.
if command -v systemctl >/dev/null && [ "$(systemctl is-system-running 2>/dev/null)" = "running" ]; then
  riga "systemd" "attivo (il banco puo' limitare la RAM con systemd-run)"
else
  riga "systemd" "assente o inattivo (il banco gira, ma senza muro di sicurezza sulla RAM)"
fi

# 3. Strumenti di compilazione.
if command -v gcc >/dev/null && command -v make >/dev/null; then
  riga "build tools" "gcc e make presenti"
else
  riga "build tools" "MANCANO gcc/make: su Debian/Ubuntu 'apt-get install build-essential'"
fi

# 4. Motore colibri compilato.
if [ -x "$COLI_DIR/coli" ]; then
  riga "motore colibri" "presente in $COLI_DIR"
else
  riga "motore colibri" "ASSENTE in $COLI_DIR: clonare JustVugg/colibri e compilare (c/setup.sh, make <famiglia>)"
fi

# 5. Modelli nel magazzino (una cartella con config.json e almeno un .safetensors).
MODELLI_TROVATI=0
if [ -d "$MAGAZZINO" ]; then
  while IFS= read -r cfg; do
    d="$(dirname "$cfg")"
    if ls "$d"/*.safetensors >/dev/null 2>&1; then
      MODELLI_TROVATI=$((MODELLI_TROVATI+1))
      sz="$(du -sh "$d" 2>/dev/null | cut -f1)"
      riga "modello" "$(basename "$d") ($sz)"
    fi
  done < <(find "$MAGAZZINO" -maxdepth 2 -name config.json 2>/dev/null)
fi
[ "$MODELLI_TROVATI" = 0 ] && riga "modello" "NESSUNO in $MAGAZZINO: scaricare un modello colibri (es. hf download <repo> --local-dir ...)"

# 6. Endpoint gia' in ascolto, se c'e'.
if command -v curl >/dev/null && curl -fsS "http://127.0.0.1:${PORTA:-8000}/v1/models" -H "Authorization: Bearer local" >/dev/null 2>&1; then
  riga "endpoint" "in ascolto su 127.0.0.1:${PORTA:-8000} (un server e' gia' avviato)"
else
  riga "endpoint" "non in ascolto (si avvia con coli serve quando serve)"
fi

echo
if [ -x "$COLI_DIR/coli" ] && [ "$MODELLI_TROVATI" -gt 0 ]; then
  echo "ESITO: pronto. Un modello locale e' utilizzabile per l'offload del lavoro meccanico a lotti."
  ok=0
else
  echo "ESITO: non ancora pronto. Vedi le righe MANCA/ASSENTE/NESSUNO qui sopra."
  ok=1
fi
exit $ok
