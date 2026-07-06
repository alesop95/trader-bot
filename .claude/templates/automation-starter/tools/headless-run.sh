#!/usr/bin/env bash
# headless-run.sh - Invocazione headless generica di Claude Code, solo su quota di abbonamento.
#
# Esegue "claude -p" in modalita non interattiva per un task ricorrente del progetto (report di
# drift, controllo periodico, sintesi), scrivendo l'output in _notes/automation/, ignorato da
# git. Il pacchetto automation-starter resta vincolato all'uso incluso nei piani Team o Max:
# questo script si rifiuta di girare se rileva ANTHROPIC_API_KEY nell'ambiente, perche' quella
# variabile fa passare l'autenticazione della CLI dall'abbonamento alla fatturazione a consumo
# dell'API, anche se la sessione risulta gia' loggata via "claude login" con un account Team o
# Max.
#
# Uso:
#   ./tools/headless-run.sh "<prompt>" [--permission-mode plan|acceptEdits|dontAsk] [--max-turns N]
#
# Default: --permission-mode plan (sola lettura, nessuna modifica), --max-turns 8.
# Solo i tre valori sopra sono accettati: bypassPermissions non e' un'opzione di questo script,
# vietato su una macchina reale non containerizzata (vedi .claude/rules/security-permissions.md).
#
# Commit e push restano sempre manuali: questo script non tocca mai git.

set -euo pipefail

if [ -n "${ANTHROPIC_API_KEY:-}" ]; then
  echo "ERRORE: ANTHROPIC_API_KEY e' impostata nell'ambiente." >&2
  echo "Il pacchetto automation-starter resta sull'uso incluso nell'abbonamento Team o Max:" >&2
  echo "con quella variabile presente Claude Code fattura a consumo invece di usare la quota" >&2
  echo "dell'abbonamento. Rimuovila da questa shell (unset ANTHROPIC_API_KEY) e verifica di" >&2
  echo "essere loggato con 'claude login'." >&2
  exit 1
fi

if ! command -v claude >/dev/null 2>&1; then
  echo "ERRORE: CLI 'claude' non trovata nel PATH." >&2
  exit 1
fi

PROMPT=""
PERMISSION_MODE="plan"
MAX_TURNS=8

while [ $# -gt 0 ]; do
  case "$1" in
    --permission-mode)
      PERMISSION_MODE="$2"; shift 2 ;;
    --max-turns)
      MAX_TURNS="$2"; shift 2 ;;
    *)
      if [ -z "$PROMPT" ]; then PROMPT="$1"; else echo "Argomento inatteso: $1" >&2; exit 2; fi
      shift ;;
  esac
done

if [ -z "$PROMPT" ]; then
  echo "Uso: $0 \"<prompt>\" [--permission-mode plan|acceptEdits|dontAsk] [--max-turns N]" >&2
  exit 2
fi

case "$PERMISSION_MODE" in
  plan|acceptEdits|dontAsk) ;;
  *)
    echo "ERRORE: --permission-mode '$PERMISSION_MODE' non ammesso da questo script." >&2
    echo "Valori accettati: plan, acceptEdits, dontAsk. Vedi .claude/rules/security-permissions.md." >&2
    exit 1 ;;
esac

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
OUT_DIR="$PROJECT_ROOT/_notes/automation"
mkdir -p "$OUT_DIR"
STAMP="$(date '+%Y%m%d-%H%M%S')"
OUT_FILE="$OUT_DIR/$STAMP.json"

echo "[$STAMP] Esecuzione headless (permission-mode=$PERMISSION_MODE, max-turns=$MAX_TURNS)..."
if claude -p "$PROMPT" --output-format json --permission-mode "$PERMISSION_MODE" --max-turns "$MAX_TURNS" > "$OUT_FILE"; then
  echo "Output salvato in _notes/automation/$STAMP.json"
else
  rc=$?
  echo "ERRORE: la corsa headless e' terminata con codice $rc. Vedi $OUT_FILE." >&2
  exit "$rc"
fi
