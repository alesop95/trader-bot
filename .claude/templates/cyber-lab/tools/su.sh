#!/usr/bin/env bash
# Tira su il laboratorio isolato dopo averne verificato l'isolamento. Non modifica nulla fuori da Docker.
# Controlli prima dell'avvio: file dei valori presente, nessuna porta pubblicata, rete interna, immagini per digest.
set -euo pipefail

QUI="$(cd "$(dirname "$0")/.." && pwd)"
VALORI="$QUI/cyber-lab.valori.sh"
COMPOSE="$QUI/compose.yaml"

[ -f "$VALORI" ] || { echo "manca $VALORI: copiare cyber-lab.valori.esempio.sh e compilarlo" >&2; exit 2; }
[ -f "$COMPOSE" ] || { echo "manca $COMPOSE" >&2; exit 2; }
command -v docker >/dev/null || { echo "docker assente" >&2; exit 2; }

# shellcheck disable=SC1090
. "$VALORI"

# 1. Nessuna porta pubblicata verso l'host.
if grep -Eq '^\s*ports:' "$COMPOSE"; then
  echo "RIFIUTO: il compose dichiara una porta pubblicata. Il laboratorio resta interno." >&2; exit 3
fi

# 2. La rete e' interna.
if ! grep -Eq '^\s*internal:\s*true' "$COMPOSE"; then
  echo "RIFIUTO: la rete del laboratorio non e' dichiarata interna." >&2; exit 3
fi

# 3. Le immagini valorizzate sono per digest, non per tag mobile.
controlla_digest() {
  local nome="$1" val="$2"
  [ -z "$val" ] && return 0   # vuoto: gestito dopo
  if ! printf '%s' "$val" | grep -Eq '@sha256:[0-9a-f]{64}$'; then
    echo "RIFIUTO: $nome non e' fissata per digest (@sha256:...): $val" >&2; exit 3
  fi
  if printf '%s' "$val" | grep -q 'METTERE'; then
    echo "RIFIUTO: $nome e' ancora un segnaposto. Leggere il digest reale dal registry e compilarlo." >&2; exit 3
  fi
}
controlla_digest IMG_GREENBONE "${IMG_GREENBONE:-}"
controlla_digest IMG_SCANNER "${IMG_SCANNER:-}"
controlla_digest IMG_DETECT "${IMG_DETECT:-}"
controlla_digest IMG_BERSAGLIO "${IMG_BERSAGLIO:-}"

# 4. Bersaglio: avverte ma non impone.
PROFILI=()
if [ -n "${IMG_BERSAGLIO:-}" ]; then
  PROFILI=(--profile con-bersaglio)
else
  echo "nota: nessun bersaglio dichiarato (IMG_BERSAGLIO vuoto). Il laboratorio parte senza bersaglio." >&2
fi

echo "controlli di isolamento superati: nessuna porta pubblicata, rete interna, immagini per digest."
docker compose -f "$COMPOSE" "${PROFILI[@]}" up -d

echo "laboratorio su. La rete '${LAB_RETE}' e' interna: i servizi si raggiungono solo fra loro."
echo "per entrare nel contenitore degli strumenti: docker compose -f \"$COMPOSE\" exec scanner sh"
