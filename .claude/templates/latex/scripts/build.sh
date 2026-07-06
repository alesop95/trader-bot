#!/bin/sh
# Compila il documento LaTeX del progetto in modo riproducibile (Unix/macOS).
# Sezione 13 di .claude/PROJECT-SYSTEM.md. Trova latexmk nell'ambiente TinyTeX
# user-local (o sul PATH) e compila con l'engine pdflatex fissato in .latexmkrc.
#
# Uso:
#   sh scripts/build.sh [--main FILE.tex] [--clean] [--clean-all] [--tex-dir DIR]
set -eu

MAIN=""
MODE="build"
TEX_DIR=""

while [ $# -gt 0 ]; do
  case "$1" in
    --main)      MAIN="$2"; shift ;;
    --clean)     MODE="clean" ;;
    --clean-all) MODE="cleanall" ;;
    --tex-dir)   TEX_DIR="$2"; shift ;;
    *) echo "[build] Argomento sconosciuto: $1" >&2; exit 2 ;;
  esac
  shift
done

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJECT_ROOT=$(dirname -- "$SCRIPT_DIR")
[ -n "$TEX_DIR" ] || TEX_DIR="$HOME/.TinyTeX"

find_latexmk() {
  if command -v latexmk >/dev/null 2>&1; then command -v latexmk; return 0; fi
  for p in "$TEX_DIR"/bin/*/latexmk; do
    [ -x "$p" ] && { echo "$p"; return 0; }
  done
  return 1
}

LATEXMK=$(find_latexmk) || { echo "[build] latexmk non trovato. Esegui prima sh scripts/setup-tex.sh." >&2; exit 1; }

# Determina il file principale.
if [ -z "$MAIN" ]; then
  set -- "$PROJECT_ROOT"/*.tex
  if [ "$#" -eq 1 ] && [ -f "$1" ]; then
    MAIN=$(basename -- "$1")
  elif [ "$#" -eq 0 ] || [ ! -f "$1" ]; then
    echo "[build] Nessun .tex nella radice: specifica --main." >&2; exit 1
  else
    echo "[build] Piu' .tex nella radice: specifica --main FILE.tex." >&2; exit 1
  fi
fi

cd "$PROJECT_ROOT"
# -cd: latexmk cambia directory di lavoro in quella del file principale, cosi' il PDF e gli
# ausiliari finiscono accanto al sorgente (es. docs/diploma.pdf) invece che nella radice del
# progetto, dove pdflatex scriverebbe altrimenti per default quando $MAIN e' in una
# sottocartella (osservato dal vivo nel pilota 2026-07-03).
case "$MODE" in
  clean)    "$LATEXMK" -cd -c "$MAIN" ;;
  cleanall) "$LATEXMK" -cd -C "$MAIN" ;;
  build)
    echo "[build] Compilo $MAIN con latexmk (pdflatex) ..."
    "$LATEXMK" -cd -pdf "$MAIN"
    echo "[build] Fatto: ${MAIN%.tex}.pdf"
    ;;
esac
