#!/usr/bin/env bash
# Smonta il laboratorio. Con --pulisci rimuove anche i volumi (i dati di studio non committati).
set -euo pipefail
QUI="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE="$QUI/compose.yaml"
VALORI="$QUI/cyber-lab.valori.sh"
[ -f "$VALORI" ] && . "$VALORI"
if [ "${1:-}" = "--pulisci" ]; then
  docker compose -f "$COMPOSE" --profile con-bersaglio down -v
  echo "laboratorio smontato e volumi rimossi."
else
  docker compose -f "$COMPOSE" --profile con-bersaglio down
  echo "laboratorio smontato (volumi conservati; usa --pulisci per rimuoverli)."
fi
