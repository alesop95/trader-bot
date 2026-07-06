#!/usr/bin/env bash
# Hook SessionStart (variante Linux/macOS): inietta il contesto di ripresa a inizio sessione.
# Stampa branch, ultimi commit, file modificati e la testa di .claude/memory/index.md con il
# punto di ripresa; l'output su stdout entra nel contesto della sessione (sezioni 12 e 14 di
# PROJECT-SYSTEM.md). Sola lettura, nessuna rete. NON attivo finche' non registrato nel
# settings.json del progetto (vedi settings.hooks.posix.json).
set -u

cd "${CLAUDE_PROJECT_DIR:-.}" 2>/dev/null || exit 0

echo "=== Contesto di ripresa (hook session-context) ==="

branch="$(git branch --show-current 2>/dev/null)"
if [ -z "$branch" ]; then branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null)"; fi
if [ -z "$branch" ]; then branch="n/a"; fi
echo "Branch: $branch"

echo "Ultimi commit:"
git log --oneline -3 2>/dev/null || echo "  (nessuna storia git)"

changed="$(git status --short 2>/dev/null | head -20)"
if [ -n "$changed" ]; then
  echo "File modificati non committati:"
  echo "$changed"
else
  echo "Working tree pulito."
fi

if [ -f ".claude/memory/index.md" ]; then
  echo "--- .claude/memory/index.md (testa) ---"
  head -40 ".claude/memory/index.md"
  echo "--- (leggere il file completo per la tabella di sincronizzazione) ---"
else
  echo "Nota: .claude/memory/index.md non trovato (sistema non ancora inizializzato?)."
fi

exit 0
