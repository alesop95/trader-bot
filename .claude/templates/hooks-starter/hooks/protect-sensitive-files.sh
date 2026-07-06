#!/usr/bin/env bash
# Hook PreToolUse su Write|Edit (variante Linux/macOS): blocca le scritture su file sensibili.
# Difesa in profondita' rispetto alle regole deny del settings.json: intercetta la chiamata
# anche quando i permessi sono stati allargati. Blocco = exit 2 con motivo su stderr; in caso
# di input non parsabile lascia passare (un hook rotto non deve paralizzare il lavoro).
# NON attivo finche' non registrato nel settings.json (vedi settings.hooks.posix.json).
set -u

input="$(cat)"
path="$(printf '%s' "$input" | grep -oE '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed -E 's/.*"file_path"[[:space:]]*:[[:space:]]*"([^"]*)".*/\1/')"

# Nessun file_path estraibile: non e' una scrittura su file riconoscibile, lascia passare.
[ -z "$path" ] && exit 0

# Normalizza i separatori Windows per il matching.
norm="$(printf '%s' "$path" | tr '\\' '/')"

# Eccezione esplicita: .env.example e' il template pubblico delle variabili, va scrivibile.
case "$norm" in
  *.env.example) exit 0 ;;
esac

case "$norm" in
  *.env|*.env.*|*.pem|*.key|*/.git/*|.git/*)
    echo "File protetto dall'hook protect-sensitive-files: $path. Scrittura non consentita dagli hook di progetto (secret o area .git)." >&2
    exit 2 ;;
esac

exit 0
