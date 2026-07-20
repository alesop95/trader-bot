"""Rigenera _notes/book-bib-registry.md a partire da _notes/book-bib-registry.json.

Script deterministico, nessuna chiamata LLM. Da rilanciare a ogni aggiornamento del registro
JSON (per esempio dopo ogni libro confermato da book-bib-extract), non come generazione una
tantum. Il titolo mostrato in tabella viene letto dal .bib reale quando la voce e' gia' stata
scritta (bib_entry_written: true); altrimenti si usa il nome del file sorgente come segnaposto,
perche' il registro non conserva il titolo prima della conferma umana.

Uso:
    py -3 tools/render-bib-registry.py [--registry _notes/book-bib-registry.json]
                                        [--bib bib/references.bib]
                                        [--out _notes/book-bib-registry.md]

Il percorso di default di --bib e' un segnaposto generico: nei progetti con uno split
pubblico/privato del contenuto (per esempio un manoscritto in una cartella ignorata da git)
va passato esplicitamente il percorso reale del .bib del progetto.
"""

import argparse
import json
import os
import re
from pathlib import Path

BIB_ENTRY_RE = re.compile(r"@book\{([^,]+),(.*?)\n\}", re.S)
BIB_FIELD_RE = re.compile(r"(\w+)\s*=\s*\{(.*?)\}\s*,?\s*$", re.M)


def parse_bib_titles(bib_path):
    """Ritorna {citekey: titolo} leggendo solo i campi title dal .bib reale."""
    titles = {}
    if not bib_path.exists():
        return titles
    text = bib_path.read_text(encoding="utf-8")
    for citekey, body in BIB_ENTRY_RE.findall(text):
        m = re.search(r"title\s*=\s*\{(.*?)\}\s*,", body, re.S)
        if m:
            titles[citekey.strip()] = " ".join(m.group(1).split())
    return titles


def placeholder_title(entry):
    rel = entry.get("doc_ingest_source_rel") or ""
    if rel:
        return Path(rel).stem
    src = entry.get("source_path") or ""
    return Path(src).stem if src else "(sconosciuto)"


def render_table(registry, titles):
    rows = []
    for sha, entry in registry.items():
        citekey = entry.get("citekey") or "(nessuna citekey)"
        corpus = entry.get("corpus") or ""
        bib_status = entry.get("bib_status") or ""
        skill_status = entry.get("skill_status") or ""
        if entry.get("bib_entry_written") and citekey in titles:
            title = titles[citekey]
        else:
            title = f"(non confermato) {placeholder_title(entry)}"
        rows.append((corpus, citekey, title, bib_status, skill_status, sha))

    rows.sort(key=lambda r: (r[0], r[1]))

    lines = [
        "# Registro bibliografico dei libri ingeriti",
        "",
        "Tabella rigenerata automaticamente da `_notes/book-bib-registry.json` tramite "
        "`tools/render-bib-registry.py`. Mai editata a mano: ogni modifica va fatta sul JSON "
        "e poi si rilancia lo script.",
        "",
        f"Totale voci: {len(rows)}",
        "",
        "| corpus | citekey | titolo | bib_status | skill_status |",
        "| --- | --- | --- | --- | --- |",
    ]
    for corpus, citekey, title, bib_status, skill_status, _sha in rows:
        title_cell = title.replace("|", "\\|")
        lines.append(f"| {corpus} | {citekey} | {title_cell} | {bib_status} | {skill_status} |")
    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", default="_notes/book-bib-registry.json")
    parser.add_argument("--bib", default="bib/references.bib")
    parser.add_argument("--out", default="_notes/book-bib-registry.md")
    args = parser.parse_args()

    registry_path = Path(args.registry)
    bib_path = Path(args.bib)
    out_path = Path(args.out)

    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    titles = parse_bib_titles(bib_path)
    markdown = render_table(registry, titles)
    out_path.write_text(markdown, encoding="utf-8")
    print(f"Scritte {len(registry)} voci in {out_path}")


if __name__ == "__main__":
    main()
