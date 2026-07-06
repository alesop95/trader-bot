#!/usr/bin/env bash
# fetch-community-agent.sh - Scarica un singolo subagent da una fonte flat del catalogo (variante Linux/macOS).
#
# Scarica <fonte>/<file>.md via raw.githubusercontent.com dentro .claude/agents/ del progetto e
# registra la provenienza (fonte, commit sha al momento del fetch, data) in
# .claude/agent-catalog/state.json, cosi' resta tracciabile da dove viene ogni agente pescato.
# Non modifica il contenuto del file: il frontmatter YAML (incluso il campo "model", spesso
# fissato dalla fonte a uno snapshot specifico) va rivisto a mano dopo il fetch.
#
# Uso:
#   ./tools/fetch-community-agent.sh 0xfurai react-expert
#   ./tools/fetch-community-agent.sh 0xfurai react-expert --force   # sovrascrive se gia' presente
#   ./tools/fetch-community-agent.sh 0xfurai react-expert --out .claude/agents/react-expert.md
#
# Exit code: 0 = scaricato; 1 = errore (fonte/file non trovato, download fallito, gia' presente senza --force).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SOURCES="$PROJECT_ROOT/.claude/agent-catalog/sources.json"
STATE="$PROJECT_ROOT/.claude/agent-catalog/state.json"

SOURCE_KEY="${1:-}"; AGENT="${2:-}"
FORCE=0; OUT=""
shift 2 2>/dev/null || true
while [ $# -gt 0 ]; do
  case "$1" in
    --force) FORCE=1 ;;
    --out) OUT="$2"; shift ;;
    *) echo "Argomento sconosciuto: $1" >&2; exit 2 ;;
  esac
  shift
done

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"; }

if ! command -v jq >/dev/null 2>&1; then
  echo "ERRORE: serve jq (apt install jq / brew install jq)." >&2
  exit 1
fi
if [ -z "$SOURCE_KEY" ] || [ -z "$AGENT" ]; then
  echo "Uso: $0 <fonte> <agente> [--force] [--out <path>]" >&2
  exit 2
fi
if [ ! -f "$SOURCES" ]; then
  log "ERRORE: non trovo $SOURCES. Il pacchetto agent-catalog e' instanziato correttamente?"
  exit 1
fi

src_json="$(jq -c ".sources[] | select(.key == \"$SOURCE_KEY\")" "$SOURCES")"
if [ -z "$src_json" ]; then
  log "ERRORE: fonte '$SOURCE_KEY' non trovata in sources.json."
  exit 1
fi
type="$(echo "$src_json" | jq -r '.type')"
if [ "$type" = "meta" ]; then
  repo="$(echo "$src_json" | jq -r '.repo')"
  log "ERRORE: '$SOURCE_KEY' e' un indice curato (meta), non ha file da scaricare. Consultare https://github.com/$repo."
  exit 1
fi
repo="$(echo "$src_json" | jq -r '.repo')"
branch="$(echo "$src_json" | jq -r '.branch')"
path="$(echo "$src_json" | jq -r '.path')"

agent_file="${AGENT%.md}.md"
[ -n "$OUT" ] || OUT="$PROJECT_ROOT/.claude/agents/$agent_file"
if [ -f "$OUT" ] && [ "$FORCE" -eq 0 ]; then
  log "ERRORE: $OUT esiste gia'. Usare --force per sovrascrivere."
  exit 1
fi

raw_url="https://raw.githubusercontent.com/$repo/$branch/$path/$agent_file"
log "Scarico $raw_url ..."
tmp="$(mktemp)"; trap 'rm -f "$tmp"' EXIT
if ! curl -fsSL --max-time 30 -H "User-Agent: agent-catalog-script" "$raw_url" -o "$tmp" || [ ! -s "$tmp" ]; then
  log "ERRORE: download fallito. Verificare il nome esatto con list-community-agents.sh."
  exit 1
fi

mkdir -p "$(dirname "$OUT")"
cp "$tmp" "$OUT"
log "Salvato in $OUT"

commit_sha="$(curl -fsSL --max-time 20 -H "User-Agent: agent-catalog-script" "https://api.github.com/repos/$repo/commits/$branch" 2>/dev/null | jq -r '.sha' || echo "")"

mkdir -p "$(dirname "$STATE")"
if [ ! -f "$STATE" ]; then echo '{"sources": {}, "fetch_log": []}' > "$STATE"; fi
tmp_state="$(mktemp)"
jq --arg file "$agent_file" --arg source "$SOURCE_KEY" --arg sha "$commit_sha" --arg date "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" \
  '.fetch_log += [{file: $file, source: $source, commit_sha: $sha, fetched_at: $date}]' \
  "$STATE" > "$tmp_state" && mv "$tmp_state" "$STATE"
log "Provenienza registrata in .claude/agent-catalog/state.json"
log "Rivedere il campo 'model' nel frontmatter prima dell'uso: la fonte puo' fissare uno snapshot di modello non piu' corrente."
exit 0
