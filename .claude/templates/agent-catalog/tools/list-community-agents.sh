#!/usr/bin/env bash
# list-community-agents.sh - Elenca i subagent disponibili nelle fonti flat del catalogo (variante Linux/macOS).
#
# Legge .claude/agent-catalog/sources.json, interroga l'API GitHub (contenuti della cartella
# indicata da ciascuna fonte "flat") e stampa i nomi dei file .md disponibili, pronti da passare
# a fetch-community-agent.sh. Le fonti "meta" non vengono elencate: si stampa solo un rimando
# a consultarle a mano.
#
# Uso:
#   ./tools/list-community-agents.sh              # elenca tutte le fonti flat
#   ./tools/list-community-agents.sh 0xfurai       # solo una fonte, per chiave
#
# L'API GitHub non autenticata ha un limite di 60 richieste/ora per IP: sufficiente per un uso
# occasionale, non per una corsa automatica frequente. Richiede jq.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SOURCES="$PROJECT_ROOT/.claude/agent-catalog/sources.json"
FILTER_KEY="${1:-}"

if ! command -v jq >/dev/null 2>&1; then
  echo "ERRORE: serve jq (apt install jq / brew install jq)." >&2
  exit 1
fi
if [ ! -f "$SOURCES" ]; then
  echo "ERRORE: non trovo $SOURCES. Il pacchetto agent-catalog e' instanziato correttamente?" >&2
  exit 1
fi

count=$(jq '.sources | length' "$SOURCES")
for i in $(seq 0 $((count - 1))); do
  key="$(jq -r ".sources[$i].key" "$SOURCES")"
  if [ -n "$FILTER_KEY" ] && [ "$key" != "$FILTER_KEY" ]; then
    continue
  fi
  name="$(jq -r ".sources[$i].name" "$SOURCES")"
  license="$(jq -r ".sources[$i].license" "$SOURCES")"
  type="$(jq -r ".sources[$i].type" "$SOURCES")"
  repo="$(jq -r ".sources[$i].repo" "$SOURCES")"

  echo ""
  echo "=== $key ($name, licenza $license) ==="
  if [ "$type" = "meta" ]; then
    echo "Indice curato, non elencabile: consultare a mano https://github.com/$repo"
    continue
  fi
  path="$(jq -r ".sources[$i].path" "$SOURCES")"
  branch="$(jq -r ".sources[$i].branch" "$SOURCES")"
  url="https://api.github.com/repos/$repo/contents/$path?ref=$branch"
  resp="$(curl -fsSL --max-time 30 -H "User-Agent: agent-catalog-script" "$url" 2>/dev/null || echo "")"
  if [ -z "$resp" ]; then
    echo "ERRORE: impossibile leggere $url (limite API GitHub non autenticata di 60/ora per IP, o rete assente)."
    continue
  fi
  names="$(echo "$resp" | jq -r '.[] | select(.type=="file" and (.name | endswith(".md"))) | .name' | sed 's/\.md$//' | sort)"
  echo "$names" | sed 's/^/  /'
  echo "$(echo "$names" | grep -c . || true) agent disponibili."
done
