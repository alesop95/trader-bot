"""Estrae le pagine di frontespizio/colophon di un PDF come PNG, per la verifica visiva
richiesta da `.claude/skills/book-bib-extract/SKILL.md`.

Motivo per cui non si usa il mirror Markdown di tools/doc-ingest.py per questo scopo: molti
corpus di libri di studio (specie fotocopie o scansioni datate) sono PDF scansionati senza
livello di testo nativo, quindi il mirror Markdown (via markitdown) esce vuoto anche con
--ocr attivo, perche' l'OCR su scansioni di bassa qualita' e' spesso inaffidabile o rumoroso;
la verifica visiva sulle pagine renderizzate resta il percorso pratico per bib_status.

Convenzione di output: 3 pagine per libro (frontespizio, verso, colophon) sono quasi sempre
sufficienti; si puo' alzare --pages per libri con colophon piu' in profondita'.

Uso:
    py -3 tools/extract-titlepages.py LIBRO.pdf --slug nome-slug --out CARTELLA_DEST
    py -3 tools/extract-titlepages.py LIBRO.pdf --slug nome-slug --out CARTELLA_DEST --pages 5 --dpi 200
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_DPI = 150
DEFAULT_PAGES = 3


def find_pdftoppm():
    path = shutil.which("pdftoppm")
    if not path:
        sys.exit("pdftoppm non trovato in PATH (Poppler). Installarlo prima di procedere.")
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pdf", type=Path, help="PDF sorgente")
    parser.add_argument("--slug", required=True, help="slug del libro, usato come prefisso file")
    parser.add_argument("--out", required=True, type=Path, help="cartella di destinazione dei PNG")
    parser.add_argument("--dpi", type=int, default=DEFAULT_DPI)
    parser.add_argument("--pages", type=int, default=DEFAULT_PAGES, help="numero di pagine dall'inizio del PDF")
    args = parser.parse_args()

    if not args.pdf.exists():
        sys.exit(f"PDF non trovato: {args.pdf}")

    pdftoppm = find_pdftoppm()
    args.out.mkdir(parents=True, exist_ok=True)
    prefix = args.out / args.slug

    cmd = [
        pdftoppm,
        "-png",
        "-r", str(args.dpi),
        "-f", "1",
        "-l", str(args.pages),
        str(args.pdf),
        str(prefix),
    ]
    subprocess.run(cmd, check=True)

    produced = sorted(args.out.glob(f"{args.slug}-*.png"))
    print(f"Generati {len(produced)} PNG in {args.out} (dpi={args.dpi}, pagine={args.pages}):")
    for p in produced:
        print(f"  {p.name}")


if __name__ == "__main__":
    main()
