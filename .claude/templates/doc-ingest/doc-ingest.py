#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
doc-ingest.py - Ingestione deterministica e incrementale di un corpus documentale
(.pdf, .docx, .pptx, .xlsx, .html) in una cache Markdown locale, a zero consumo di
token: l'estrazione è interamente locale, nessuna chiamata LLM.

Cammina ricorsivamente una cartella sorgente, converte ogni documento supportato in
Markdown e scrive il risultato in una cache che rispecchia la struttura di cartelle
della sorgente. Un manifest a content-hash (sha256) evita di riconvertire i file
invariati tra una corsa e l'altra. Al termine rigenera _INDEX.md: lo scheletro di
Livello 1 della disclosure progressiva descritta in ../../rules/token-economy.md,
con titolo, albero delle intestazioni, conteggi (parole, tabelle, immagini) e stato
di ciascun documento, così che un agente possa decidere cosa leggere per intero senza
aprire l'intero corpus.

Motore di default: markitdown (MIT). Con --engine docling si usa Docling sui soli
.pdf per i layout complessi (tabelle, multi-colonna) dove markitdown degrada; e una
dipendenza opzionale, importata solo se il flag è passato. Con --ocr si tenta il
fallback OCR via pytesseract sui PDF scansionati senza testo estraibile; richiede il
binario di sistema tesseract-ocr, anch'esso opzionale.

Uso:
    python doc-ingest.py SORGENTE --out _notes/.tmp-doc-cache
    python doc-ingest.py SORGENTE --engine docling
    python doc-ingest.py SORGENTE --ocr
    python doc-ingest.py SORGENTE --force   # ignora il manifest, riconverte tutto

Dipendenze: markitdown (sempre). docling e pytesseract+pdf2image sono opzionali,
richiesti solo dai rispettivi flag.
"""

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".xlsx", ".html", ".htm"}
MANIFEST_NAME = ".manifest.json"
INDEX_NAME = "_INDEX.md"
OCR_MIN_CHARS = 200  # sotto questa soglia di testo estratto, un .pdf è sospetto scan


# --- hashing e manifest ------------------------------------------------------
def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_manifest(cache_dir):
    manifest_path = cache_dir / MANIFEST_NAME
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_manifest(cache_dir, manifest):
    manifest_path = cache_dir / MANIFEST_NAME
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True, ensure_ascii=False)


# --- conversione --------------------------------------------------------------
def convert_with_markitdown(path):
    from markitdown import MarkItDown

    return MarkItDown().convert(str(path)).text_content


def convert_with_docling(path):
    try:
        from docling.document_converter import DocumentConverter
    except ImportError:
        raise RuntimeError(
            "Il flag --engine docling richiede il pacchetto 'docling' "
            "(pip install docling), non trovato nell'ambiente Python corrente."
        )
    result = DocumentConverter().convert(str(path))
    return result.document.export_to_markdown()


def convert_with_ocr(path):
    try:
        import pytesseract
        from pdf2image import convert_from_path
    except ImportError:
        raise RuntimeError(
            "Il flag --ocr richiede 'pytesseract' e 'pdf2image' "
            "(pip install pytesseract pdf2image) più il binario di sistema "
            "tesseract-ocr, non trovati nell'ambiente corrente."
        )
    pages = convert_from_path(str(path))
    return "\n\n".join(pytesseract.image_to_string(page) for page in pages)


def convert_file(path, engine, ocr):
    """Ritorna (markdown, nota). nota è None o un avviso non bloccante."""
    ext = path.suffix.lower()
    if engine == "docling" and ext == ".pdf":
        text = convert_with_docling(path)
    else:
        text = convert_with_markitdown(path)

    if ocr and ext == ".pdf" and len(text.strip()) < OCR_MIN_CHARS:
        try:
            ocr_text = convert_with_ocr(path)
            if len(ocr_text.strip()) > len(text.strip()):
                return ocr_text, "estratto via OCR (testo nativo insufficiente)"
        except RuntimeError as exc:
            return text, f"OCR saltato: {exc}"
    return text, None


# --- analisi deterministica del markdown estratto -----------------------------
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$", re.MULTILINE)
TABLE_SEP_RE = re.compile(r"^\s*\|?[\s:|-]+\|[\s:|-]*\|?\s*$", re.MULTILINE)
IMAGE_RE = re.compile(r"!\[")


def analyze_markdown(text):
    headings = [(len(m.group(1)), m.group(2).strip()) for m in HEADING_RE.finditer(text)]
    title = headings[0][1] if headings else None
    return {
        "title": title,
        "headings": headings,
        "words": len(text.split()),
        "tables": len(TABLE_SEP_RE.findall(text)),
        "images": len(IMAGE_RE.findall(text)),
    }


# --- indice di Livello 1 -------------------------------------------------------
def render_index(entries):
    lines = [
        "# Indice del corpus (Livello 1 - scheletro)",
        "",
        "> Generato da doc-ingest.py. Non modificare a mano: si rigenera a ogni corsa.",
        "> Livello 2 (preview di sezione) e Livello 3 (sezione singola) sono pratica di",
        "> lettura, non file: apri il Markdown mirror sotto e leggi solo la porzione utile.",
        "",
    ]
    for entry in sorted(entries, key=lambda e: e["source_rel"]):
        lines.append(f"## {entry['source_rel']}  ({entry['status']})")
        lines.append("")
        lines.append(f"- mirror: `{entry['cache_rel']}`")
        if entry.get("title"):
            lines.append(f"- titolo: {entry['title']}")
        lines.append(
            f"- parole: {entry['words']} · tabelle: {entry['tables']} · immagini: {entry['images']}"
        )
        if entry.get("note"):
            lines.append(f"- nota: {entry['note']}")
        for level, text in entry.get("headings", [])[:200]:
            lines.append(f"{'  ' * (level - 1)}- {'#' * level} {text}")
        lines.append("")
    return "\n".join(lines)


# --- orchestrazione -------------------------------------------------------------
def carica_esclusi(percorso):
    """Schemi dei documenti personali da non aprire mai (regola documenti-personali.md).

    Un'espressione regolare per riga, confrontata senza maiuscole con il percorso completo
    del file; righe vuote e righe che iniziano con # si ignorano. Se il file indicato non
    esiste lo strumento si ferma, perché un'ingestione di massa senza esclusione è proprio
    il caso che la regola esiste per impedire.
    """
    p = Path(percorso)
    if not p.exists():
        sys.exit(f"doc-ingest: manca {p}, il file degli schemi dei documenti personali")
    righe = (r.strip() for r in p.read_text(encoding="utf-8").splitlines())
    return [re.compile(r, re.IGNORECASE) for r in righe if r and not r.startswith("#")]


def iter_source_files(source_dir, cache_dir, esclusi=None):
    cache_resolved = cache_dir.resolve()
    for root, dirs, files in os.walk(source_dir):
        root_path = Path(root)
        if root_path.resolve() == cache_resolved or cache_resolved in root_path.resolve().parents:
            dirs[:] = []
            continue
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for name in files:
            path = root_path / name
            if path.suffix.lower() in SUPPORTED_EXTENSIONS:
                # Lo schema si confronta con il percorso completo, perché gli schemi delle
                # cartelle cercano un separatore prima del nome, che il percorso relativo
                # di un file in una sottocartella di primo livello non ha.
                if esclusi and any(s.search(str(path.resolve())) for s in esclusi):
                    print(f"[personale escluso] {path.relative_to(source_dir)}", file=sys.stderr)
                    continue
                yield path


def run(source_dir, cache_dir, engine, ocr, force, esclusi=None):
    source_dir = Path(source_dir)
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)

    manifest = {} if force else load_manifest(cache_dir)
    new_manifest = {}
    entries = []
    counts = {"nuovo": 0, "aggiornato": 0, "invariato": 0, "errore": 0}

    for path in iter_source_files(source_dir, cache_dir, esclusi):
        source_rel = str(path.relative_to(source_dir))
        digest = sha256_of(path)
        cache_rel = source_rel + ".md"
        cache_path = cache_dir / cache_rel

        previous = manifest.get(source_rel)
        if previous == digest and cache_path.exists():
            status = "invariato"
        else:
            status = "aggiornato" if previous else "nuovo"

        new_manifest[source_rel] = digest

        if status == "invariato":
            text = cache_path.read_text(encoding="utf-8")
            note = None
        else:
            try:
                text, note = convert_file(path, engine, ocr)
            except Exception as exc:  # qualunque libreria di conversione può fallire
                print(f"[errore] {source_rel}: {exc}", file=sys.stderr)
                counts["errore"] += 1
                continue
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(text, encoding="utf-8")

        counts[status] += 1
        analysis = analyze_markdown(text)
        entries.append(
            {
                "source_rel": source_rel,
                "cache_rel": cache_rel,
                "status": status,
                "note": note,
                **analysis,
            }
        )

    save_manifest(cache_dir, new_manifest)
    index_path = cache_dir / INDEX_NAME
    index_path.write_text(render_index(entries), encoding="utf-8")

    print(
        f"doc-ingest: {counts['nuovo']} nuovi, {counts['aggiornato']} aggiornati, "
        f"{counts['invariato']} invariati, {counts['errore']} errori. "
        f"Indice: {index_path}"
    )
    return counts["errore"] == 0


def autotest():
    """Prova dell'esclusione dei documenti personali con l'elenco di esempio, dal 2026-10-07.

    Costruisce un albero temporaneo con nomi di file nelle forme in cui si salvano davvero,
    cioè con trattini bassi, spazi, maiuscole e cartelle annidate, e controlla che
    `iter_source_files` salti tutti e soli i personali. La prova è nata da due difetti
    trovati quel giorno nell'elenco: `\\bIBAN\\b` non trovava `coordinate_IBAN.pdf`, perché
    per le espressioni regolari il trattino basso è parte della parola, e conto corrente,
    carte e mutui non erano coperti. Controlla anche che senza elenco i file ci siano tutti,
    perché una prova in cui nessun file viene trovato passerebbe senza misurare nulla.
    """
    import contextlib
    import io
    import tempfile
    elenco = Path(__file__).with_name("esclusi-personali.esempio.txt")
    personali = [
        "Download/estratto_conto_2025-03.pdf", "Download/Estratto Conto Marzo.pdf",
        "Download/coordinate_IBAN.pdf", "Download/modello_F24_2025.pdf", "Download/ISEE-2026.pdf",
        "Download/contabile_bonifico.pdf", "Download/carta_di_credito_rendiconto.pdf",
        "Download/movimenti_conto_corrente.xlsx", "Download/mutuo_piano.pdf",
        "Download/busta_paga_2025.pdf", "Download/carta_identita.pdf", "Download/codice_fiscale.pdf",
        "Banca/2025/qualunque.pdf", "Varie/Fatture/marzo.pdf", "Varie/conferma_ordine_12345.pdf",
    ]
    studio = [
        "Studio/libro_algebra.pdf", "Studio/slides_reti.pptx", "Studio/conto_alla_rovescia.pdf",
        "Studio/ordinamento_algoritmi.pdf", "Studio/carta_geografica.pdf", "Studio/Ibanez_chitarra.pdf",
    ]
    errori = 0
    with tempfile.TemporaryDirectory() as d:
        radice = Path(d) / "sorgente"
        for rel in personali + studio:
            f = radice / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_bytes(b"prova")
        cache = Path(d) / "cache"
        esclusi = carica_esclusi(elenco)
        with contextlib.redirect_stderr(io.StringIO()):
            visti = {str(p.relative_to(radice)).replace(os.sep, "/") for p in iter_source_files(radice, cache, esclusi)}
            tutti = {str(p.relative_to(radice)).replace(os.sep, "/") for p in iter_source_files(radice, cache, None)}
        if tutti != set(personali + studio):
            errori += 1
            print("senza elenco mancano file: %s" % sorted(set(personali + studio) - tutti))
        for rel in personali:
            if rel in visti:
                errori += 1
                print("personale NON escluso: %s" % rel)
        for rel in studio:
            if rel not in visti:
                errori += 1
                print("materiale di studio escluso per errore: %s" % rel)
    print("autotest: %d file, %d errori" % (len(personali) + len(studio), errori))
    return 1 if errori else 0


def main():
    if "--autotest" in sys.argv[1:]:
        sys.exit(autotest())
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[2])
    parser.add_argument("source", help="Cartella sorgente da scansionare ricorsivamente")
    parser.add_argument(
        "--out",
        default="_notes/.tmp-doc-cache",
        help="Cartella di cache (default: _notes/.tmp-doc-cache)",
    )
    parser.add_argument(
        "--engine",
        choices=["markitdown", "docling"],
        default="markitdown",
        help="Motore di estrazione per i .pdf (default: markitdown)",
    )
    parser.add_argument(
        "--ocr",
        action="store_true",
        help="Fallback OCR sui .pdf con testo nativo insufficiente (richiede pytesseract)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Ignora il manifest e riconverte tutti i file",
    )
    parser.add_argument(
        "--esclusi",
        help="File degli schemi dei documenti personali da non aprire, una regex per riga "
             "(regola documenti-personali.md; esempio in esclusi-personali.esempio.txt)",
    )
    args = parser.parse_args()
    esclusi = carica_esclusi(args.esclusi) if args.esclusi else None
    ok = run(args.source, args.out, args.engine, args.ocr, args.force, esclusi)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
