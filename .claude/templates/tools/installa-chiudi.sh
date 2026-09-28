#!/usr/bin/env bash
# Installa il comando chiudi nel profilo Bash o Zsh senza fissare un repository.
set -euo pipefail

profilo=""
modo=installa
shell_nome="${SHELL##*/}"
while [ $# -gt 0 ]; do
    case "$1" in
        --profilo|--shell)
            [ $# -ge 2 ] && [ -n "$2" ] || { echo "Valore mancante per $1" >&2; exit 2; }
            if [ "$1" = --profilo ]; then profilo="$2"; else shell_nome="$2"; fi
            shift 2 ;;
        --verifica) modo=verifica; shift ;;
        *) echo "Opzione sconosciuta: $1" >&2; exit 2 ;;
    esac
done

case "$shell_nome" in
    bash) [ -n "$profilo" ] || profilo="$HOME/.bashrc" ;;
    zsh) [ -n "$profilo" ] || profilo="${ZDOTDIR:-$HOME}/.zshrc" ;;
    *) echo "Shell non supportata: $shell_nome (usare --shell bash o --shell zsh)." >&2; exit 2 ;;
esac
command -v python3 >/dev/null || { echo "Python 3 non trovato." >&2; exit 2; }

python3 - "$profilo" "$modo" <<'PY'
import os
from pathlib import Path
import shutil
import sys
import tempfile

path = Path(sys.argv[1]).expanduser()
modo = sys.argv[2]
inizio = b"# >>> chiudi (template-claude-developing) >>>"
fine = b"# <<< chiudi (template-claude-developing) <<<"
blocco = b"""# >>> chiudi (template-claude-developing) >>>
chiudi() {
    local radice script
    radice="$(git rev-parse --show-toplevel 2>/dev/null)" || { printf '%s\\n' "chiudi: la cartella corrente non e' dentro un repository git." >&2; return 2; }
    for script in "$radice/tools/chiudi-sessione.sh" "$radice/.claude/templates/tools/chiudi-sessione.sh"; do
        if [ -f "$script" ]; then bash "$script" --radice "$radice" "$@"; return $?; fi
    done
    printf '%s\\n' "chiudi: chiudi-sessione.sh non e' istanziato in $radice." >&2
    return 2
}
# <<< chiudi (template-claude-developing) <<<
"""
vecchio = path.read_bytes() if path.exists() else b""
if (vecchio.count(inizio) != vecchio.count(fine) or vecchio.count(inizio) > 1
        or (inizio in vecchio and vecchio.index(fine) < vecchio.index(inizio))):
    raise SystemExit(f"Marcatori chiudi incompleti o duplicati in {path}; nessuna modifica.")
newline = b"\r\n" if b"\r\n" in vecchio and b"\n" not in vecchio.replace(b"\r\n", b"") else b"\n"
blocco = blocco.replace(b"\n", newline)
if inizio in vecchio:
    a = vecchio.index(inizio)
    b = vecchio.index(fine, a) + len(fine)
    if vecchio[b:b + len(newline)] == newline:
        b += len(newline)
    nuovo = vecchio[:a] + blocco + vecchio[b:]
else:
    separatore = b"" if not vecchio or vecchio.endswith(newline) else newline
    nuovo = vecchio + separatore + (newline if vecchio else b"") + blocco
if modo == "verifica":
    print(f"{path}: {'installato e aggiornato' if vecchio == nuovo and inizio in vecchio else 'da installare o aggiornare'}")
    raise SystemExit(0 if vecchio == nuovo and inizio in vecchio else 1)
if vecchio == nuovo:
    print(f"{path}: comando chiudi gia' aggiornato.")
    raise SystemExit(0)
if not path.parent.is_dir():
    raise SystemExit(f"Directory del profilo assente: {path.parent}")
if path.exists():
    backup = path.with_name(path.name + ".chiudi.bak")
    shutil.copy2(path, backup)
    print(f"Backup: {backup}")
fd, tmp = tempfile.mkstemp(prefix=".chiudi-", dir=path.parent)
try:
    with os.fdopen(fd, "wb") as out:
        out.write(nuovo)
    if path.exists():
        shutil.copymode(path, tmp)
    os.replace(tmp, path)
finally:
    if os.path.exists(tmp):
        os.unlink(tmp)
print(f"{path}: comando chiudi installato. Aprire una nuova shell per usarlo.")
PY
