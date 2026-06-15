#!/bin/sh
# Bootstrap dell'ambiente LaTeX (TinyTeX) per Unix/macOS, guidato dal manifesto.
# Sezione 13 di .claude/PROJECT-SYSTEM.md. Localizza TinyTeX (installazione user-local
# condivisa), se assente lo installa, installa i pacchetti da tex-packages.txt con tlmgr,
# e verifica con una compilazione minima. Invoca i binari per percorso, niente attivazione
# interattiva, cosi' il comportamento e' identico in locale e in CI.
#
# Uso:
#   sh scripts/setup-tex.sh [--reinstall] [--tex-dir DIR] [--skip-packages] [--manifest FILE]
set -eu

REINSTALL=0
SKIP_PACKAGES=0
TEX_DIR=""
TEX_DIR_SET=0
MANIFEST=""

while [ $# -gt 0 ]; do
  case "$1" in
    --reinstall)      REINSTALL=1 ;;
    --skip-packages)  SKIP_PACKAGES=1 ;;
    --tex-dir)        TEX_DIR="$2"; TEX_DIR_SET=1; shift ;;
    --manifest)       MANIFEST="$2"; shift ;;
    *) echo "[setup-tex] Argomento sconosciuto: $1" >&2; exit 2 ;;
  esac
  shift
done

# --- Percorsi -------------------------------------------------------------------
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJECT_ROOT=$(dirname -- "$SCRIPT_DIR")
[ -n "$MANIFEST" ] || MANIFEST="$PROJECT_ROOT/tex-packages.txt"
# Installazione user-local condivisa: default standard di TinyTeX su Unix.
[ -n "$TEX_DIR" ] || TEX_DIR="$HOME/.TinyTeX"

find_tlmgr() {
  # 1) gia' sul PATH
  if command -v tlmgr >/dev/null 2>&1; then command -v tlmgr; return 0; fi
  # 2) nelle root candidate (override esplicito, default Linux, default macOS): bin/<arch>/tlmgr
  for root in "$TEX_DIR" "$HOME/.TinyTeX" "$HOME/Library/TinyTeX"; do
    for p in "$root"/bin/*/tlmgr; do
      [ -x "$p" ] && { echo "$p"; return 0; }
    done
  done
  return 1
}

# --- Reinstallazione su richiesta ----------------------------------------------
if [ "$REINSTALL" -eq 1 ] && [ -d "$TEX_DIR" ]; then
  echo "[setup-tex] Rimuovo l'installazione esistente: $TEX_DIR"
  rm -rf "$TEX_DIR"
fi

# --- Localizza o installa TinyTeX ----------------------------------------------
if ! TLMGR=$(find_tlmgr); then
  echo "[setup-tex] TinyTeX non trovato. Installazione in: $TEX_DIR"
  export TINYTEX_DIR="$TEX_DIR"   # onorato dall'installer ufficiale (best-effort)
  if command -v wget >/dev/null 2>&1; then
    wget -qO- "https://yihui.org/tinytex/install-bin-unix.sh" | sh
  elif command -v curl >/dev/null 2>&1; then
    curl -fsSL "https://yihui.org/tinytex/install-bin-unix.sh" | sh
  else
    echo "[setup-tex] Servono wget o curl per scaricare l'installer." >&2; exit 1
  fi
  TLMGR=$(find_tlmgr) || { echo "[setup-tex] Installazione fallita: tlmgr non trovato." >&2; exit 1; }
fi
echo "[setup-tex] tlmgr: $TLMGR"
TEX_BIN=$(dirname -- "$TLMGR")

# --- Aggiorna tlmgr e installa i pacchetti dal manifesto ------------------------
echo "[setup-tex] Aggiorno tlmgr ..."
"$TLMGR" update --self

if [ "$SKIP_PACKAGES" -eq 0 ]; then
  [ -f "$MANIFEST" ] || { echo "[setup-tex] Manifesto non trovato: $MANIFEST" >&2; exit 1; }
  # Pacchetti: una voce per riga, righe vuote e con # ignorate.
  PKGS=$(sed -e 's/#.*$//' -e 's/[[:space:]]*$//' "$MANIFEST" | grep -v '^[[:space:]]*$' || true)
  if [ -n "$PKGS" ]; then
    echo "[setup-tex] Installo i pacchetti dal manifesto ..."
    # shellcheck disable=SC2086
    "$TLMGR" install $PKGS
  fi
fi

# --- Verifica con una compilazione minima --------------------------------------
echo "[setup-tex] Verifica: compilo un documento di prova ..."
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
cat > "$TMP/probe.tex" <<'EOF'
\documentclass{article}
\usepackage[utf8]{inputenc}\usepackage[T1]{fontenc}
\usepackage[italian]{babel}\usepackage{siunitx}\usepackage{circuitikz}
\begin{document}Prova \SI{600}{\ohm}.\end{document}
EOF
"$TEX_BIN/pdflatex" -interaction=nonstopmode -halt-on-error -output-directory "$TMP" "$TMP/probe.tex" >/dev/null
[ -f "$TMP/probe.pdf" ] || { echo "[setup-tex] Verifica fallita: nessun PDF prodotto." >&2; exit 1; }

echo "[setup-tex] OK. Ambiente LaTeX pronto."
echo "[setup-tex] Per compilare il progetto: sh scripts/build.sh"
echo "[setup-tex] Nota: aggiungi '$TEX_BIN' al PATH per usare pdflatex/latexmk a mano."
