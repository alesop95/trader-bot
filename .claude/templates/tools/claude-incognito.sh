#!/usr/bin/env bash
# ============================================================================
# claude-incognito.sh  (variante POSIX di claude-incognito.ps1)
# Avvia una sessione Claude Code effimera: redirige HOME e le cartelle XDG su una
# directory temporanea e azzera CLAUDE_CONFIG_DIR, cosi la sessione parte vergine
# e non tocca l'account reale. La temp viene rimossa a fine sessione.
# Tecnica basata sulla specifica XDG Base Directory piu la redirezione di HOME.
#
# Uso:
#   bash claude-incognito.sh <percorso-progetto>
# ============================================================================
set -u
PROJECT_DIR="${1:-.}"
tmp="$(mktemp -d "${TMPDIR:-/tmp}/claude-incognito-XXXXXX")"
mkdir -p "$tmp/.config" "$tmp/.cache"
export HOME="$tmp"
export XDG_CONFIG_HOME="$tmp/.config"
export XDG_CACHE_HOME="$tmp/.cache"
unset CLAUDE_CONFIG_DIR
echo "Sessione incognito in: $tmp"
cd "$PROJECT_DIR" || exit 1
claude
rm -rf "$tmp"
echo "Temp incognito rimossa: $tmp"
