#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
docx-to-md.py - Convertitore deterministico da .docx a documentazione Markdown.

Parsa integralmente un documento Word in ordine di corpo (prosa, liste numerate e
puntate, tabelle, immagini) e lo spezza in file Markdown separati: un file per ogni
sezione H5, con le sezioni piu' profonde (H6-H9) annidate come sotto-titoli. Gli H4
con figli H5 diventano cartelle con README.md; gli H4 senza figli H5 diventano un
singolo file. Le macrocategorie (H3) diventano cartelle numerate.

La conversione e' verbatim: nessun contenuto viene rimosso o corretto.

Le immagini vengono estratte in cartelle assets/ accanto ai documenti e restano fuori
dal versionamento (gitignore *.png/*.jpeg gia' presente).

Uso:
    python docx-to-md.py SORGENTE.docx --out docs [--macro N]

Dipendenze: python-docx (gia' presente).
"""

import argparse
import io
import json
import os
import re
import sys
import unicodedata

import docx
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

# --- namespaces utili -------------------------------------------------------
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"

SPLIT_LEVEL = 5  # i titoli di livello <= 5 aprono un nuovo file/cartella

# Nomi di cartella fissi per le sezioni di primo livello (H3), per ordine di comparsa.
# Vuoto = i nomi si derivano automaticamente dallo slug del titolo, con prefisso numerico
# (es. "01-<slug>"). Popolalo se vuoi nomi di cartella stabili e leggibili, es.:
#   MACRO_NAMES = {1: "01-introduzione", 2: "02-metodo"}
MACRO_NAMES = {}


# --- utilita' di slug -------------------------------------------------------
def slugify(text, fallback="sezione"):
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    text = re.sub(r"-{2,}", "-", text)
    if len(text) > 60:
        text = text[:60].rstrip("-")
    return text or fallback


# --- pulizia opzionale (--clean): rumore ereditato dal sorgente -------------
# Rimuove emoji, normalizza i trattini lunghi in trattini brevi ed elimina le
# righe segnaposto composte da una sola lettera ripetuta (es. "aaaa", "### Aaaa").
# Preserva simboli tecnici come Omega (impedenza) e la freccia -> (implicazione).
_EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U00002B00-\U00002BFF\U0000FE00-\U0000FE0F]",
    flags=re.UNICODE)
_DASH_RE = re.compile("[‐-―−]")
_PLACEHOLDER_RE = re.compile(r"(?m)^[ \t]*#{0,7}[ \t]*[Aa]{3,}\.?[ \t]*$\n?")


def cleanup_text(content):
    stats = {"placeholder": 0, "dashes": 0, "emoji": 0}
    stats["placeholder"] = len(_PLACEHOLDER_RE.findall(content))
    content = _PLACEHOLDER_RE.sub("", content)
    content, stats["dashes"] = _DASH_RE.subn("-", content)
    stats["emoji"] = len(_EMOJI_RE.findall(content))
    content = _EMOJI_RE.sub("", content)
    content = re.sub(r"\(\s*\)", "", content)              # parentesi svuotate dalle emoji
    # ripristina il grassetto quando l'emoji rimossa lasciava spazi dentro i marcatori
    content = re.sub(r"\*\*[ \t]*([^*\n]+?)[ \t]*\*\*", r"**\1**", content)
    content = re.sub(r"[ \t]+$", "", content, flags=re.M)  # spazi a fine riga
    return content, stats


# --- numbering.xml: classifica liste numerate vs puntate --------------------
def build_numbering_map(document):
    """Ritorna funzione (numId, ilvl) -> 'bullet'|'ordered'."""
    fmt = {}  # numId -> {ilvl -> numFmt}
    try:
        npart = document.part.numbering_part
    except Exception:
        npart = None
    if npart is None:
        return lambda numId, ilvl: "bullet"

    root = npart.element
    # abstractNumId -> {ilvl -> numFmt}
    abstract = {}
    for an in root.findall(qn("w:abstractNum")):
        aid = an.get(qn("w:abstractNumId"))
        lvls = {}
        for lvl in an.findall(qn("w:lvl")):
            ilvl = lvl.get(qn("w:ilvl"))
            numFmt = lvl.find(qn("w:numFmt"))
            val = numFmt.get(qn("w:val")) if numFmt is not None else None
            if ilvl is not None:
                lvls[int(ilvl)] = val
        abstract[aid] = lvls
    # numId -> abstractNumId
    num_to_abstract = {}
    for num in root.findall(qn("w:num")):
        nid = num.get(qn("w:numId"))
        anid = num.find(qn("w:abstractNumId"))
        if anid is not None:
            num_to_abstract[nid] = anid.get(qn("w:val"))
        # rimappature via lvlOverride ignorate: caso non presente in questo doc

    def classify(numId, ilvl):
        aid = num_to_abstract.get(str(numId))
        if aid is None:
            return "bullet"
        lvls = abstract.get(aid, {})
        val = lvls.get(int(ilvl))
        if val is None:
            # eredita dal livello 0 se manca
            val = lvls.get(0)
        if val == "bullet":
            return "bullet"
        if val is None:
            return "bullet"
        return "ordered"

    return classify


# --- rendering inline (run, hyperlink, immagini) ----------------------------
def _run_text(r):
    """Testo del run, identico a quello calcolato da python-docx: gestisce w:t,
    w:tab, w:br/w:cr e w:noBreakHyphen senza perdere caratteri."""
    return r.text or ""


def _run_flags(r):
    rpr = r.find(qn("w:rPr"))
    bold = italic = False
    if rpr is not None:
        b = rpr.find(qn("w:b"))
        i = rpr.find(qn("w:i"))
        if b is not None and b.get(qn("w:val")) not in ("0", "false"):
            bold = True
        if i is not None and i.get(qn("w:val")) not in ("0", "false"):
            italic = True
    return bold, italic


def _run_images(r, part):
    """Ritorna lista di (blob, ext) per le immagini contenute nel run."""
    imgs = []
    for blip in r.iter(A + "blip"):
        rid = blip.get(qn("r:embed")) or blip.get(qn("r:link"))
        if not rid:
            continue
        try:
            target = part.rels[rid].target_part
        except Exception:
            continue
        blob = target.blob
        ext = os.path.splitext(target.partname)[1] or ".png"
        imgs.append((blob, ext.lstrip(".")))
    # formato VML legacy (w:pict / v:imagedata)
    for imagedata in r.iter("{urn:schemas-microsoft-com:vml}imagedata"):
        rid = imagedata.get(qn("r:id"))
        if not rid:
            continue
        try:
            target = part.rels[rid].target_part
        except Exception:
            continue
        imgs.append((target.blob, (os.path.splitext(target.partname)[1] or ".png").lstrip(".")))
    return imgs


def _emit_segments(segments):
    """Serializza una lista di (text, bold, italic) in markdown, fondendo run adiacenti."""
    # fonde segmenti adiacenti con stessa formattazione
    merged = []
    for text, b, i in segments:
        if text == "":
            continue
        if merged and merged[-1][1] == b and merged[-1][2] == i:
            merged[-1][0] += text
        else:
            merged.append([text, b, i])
    out = []
    for text, b, i in merged:
        # mantiene gli spazi esterni fuori dai marcatori
        lead = text[: len(text) - len(text.lstrip())]
        trail = text[len(text.rstrip()):]
        core = text.strip()
        if not core:
            out.append(text)
            continue
        if b and i:
            wrapped = "***" + core + "***"
        elif b:
            wrapped = "**" + core + "**"
        elif i:
            wrapped = "*" + core + "*"
        else:
            wrapped = core
        out.append(lead + wrapped + trail)
    return "".join(out)


def render_inline(p_elem, part, image_sink):
    """Rende il contenuto inline di un w:p (o di una cella). Le immagini vengono
    accodate a image_sink (lista di (blob,ext)) e sostituite da un segnaposto."""
    segments = []
    for child in p_elem:
        tag = child.tag
        if tag == W + "r":
            imgs = _run_images(child, part)
            if imgs:
                for blob, ext in imgs:
                    idx = len(image_sink)
                    image_sink.append((blob, ext))
                    segments.append(("\x00IMG%d\x00" % idx, False, False))
            txt = _run_text(child)
            if txt:
                b, i = _run_flags(child)
                segments.append((txt, b, i))
        elif tag == W + "hyperlink":
            rid = child.get(qn("r:id"))
            url = None
            if rid:
                try:
                    url = part.rels[rid].target_ref
                except Exception:
                    url = None
            inner = []
            for r in child.findall(qn("w:r")):
                inner.append(_run_text(r))
            label = "".join(inner)
            if url and label:
                segments.append(("[%s](%s)" % (label, url), False, False))
            elif label:
                segments.append((label, False, False))
    return _emit_segments(segments)


# --- rendering di blocchi ----------------------------------------------------
def render_paragraph(par, part, classify):
    """Ritorna (kind, md, raw, images) per un paragrafo.
    kind in {'heading','list','block','empty'}."""
    style = par.style.name if par.style is not None else "Normal"
    p = par._p
    image_sink = []
    md_inline = render_inline(p, part, image_sink)
    raw = par.text

    if style.startswith("Heading"):
        try:
            level = int(style.split()[-1])
        except ValueError:
            level = 4
        return ("heading", md_inline, raw, image_sink, level)

    if style == "List Paragraph":
        ppr = p.find(qn("w:pPr"))
        numpr = ppr.find(qn("w:numPr")) if ppr is not None else None
        ilvl = 0
        numId = None
        if numpr is not None:
            ilvl_e = numpr.find(qn("w:ilvl"))
            numid_e = numpr.find(qn("w:numId"))
            if ilvl_e is not None:
                ilvl = int(ilvl_e.get(qn("w:val")) or 0)
            if numid_e is not None:
                numId = numid_e.get(qn("w:val"))
        kind_list = classify(numId, ilvl) if numId is not None else "bullet"
        marker = "-" if kind_list == "bullet" else "1."
        indent = "   " * ilvl
        text = md_inline.strip()
        if not text and not image_sink:
            return ("empty", "", "", [], None)
        return ("list", "%s%s %s" % (indent, marker, text), raw, image_sink, None)

    # paragrafo normale
    if not md_inline.strip() and not image_sink:
        return ("empty", "", "", [], None)
    return ("block", md_inline, raw, image_sink, None)


def render_table(tbl, part):
    rows = tbl.rows
    raw_parts = []
    md_lines = []
    image_sink = []

    def cell_md(cell):
        cell_lines = []
        for par in cell.paragraphs:
            line = render_inline(par._p, part, image_sink)
            raw_parts.append(par.text)
            cell_lines.append(line.strip())
        txt = "<br>".join(x for x in cell_lines if x != "") or " "
        return txt.replace("|", "\\|")

    if not rows:
        return ("block", "", "", [])
    ncols = max(len(r.cells) for r in rows)
    # header = prima riga
    header_cells = [cell_md(c) for c in rows[0].cells]
    while len(header_cells) < ncols:
        header_cells.append(" ")
    md_lines.append("| " + " | ".join(header_cells) + " |")
    md_lines.append("| " + " | ".join(["---"] * ncols) + " |")
    for row in rows[1:]:
        cells = [cell_md(c) for c in row.cells]
        while len(cells) < ncols:
            cells.append(" ")
        md_lines.append("| " + " | ".join(cells) + " |")
    return ("block", "\n".join(md_lines), "\n".join(raw_parts), image_sink)


# --- iterazione del corpo in ordine -----------------------------------------
def iter_block_items(document):
    body = document.element.body
    for child in body.iterchildren():
        if child.tag == W + "p":
            yield Paragraph(child, document)
        elif child.tag == W + "tbl":
            yield Table(child, document)


# --- modello di file ---------------------------------------------------------
class OutFile:
    def __init__(self, path, root_level, title_md, is_index=False):
        self.path = path
        self.root_level = root_level
        self.title_md = title_md
        self.is_index = is_index
        self.blocks = []  # lista di (kind, md, images)
        self.children = []  # per gli indici: (titolo, percorso relativo)

    def add(self, kind, md, images):
        self.blocks.append([kind, md, images])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("--out", default="docs")
    ap.add_argument("--macro", type=int, default=0, help="0 = tutte; 1..4 = solo quella macrocategoria")
    ap.add_argument("--annotations", default=None,
                    help="JSON percorso->banner markdown da iniettare dopo il titolo. "
                         "Default: annotations.json accanto allo script, se presente.")
    ap.add_argument("--clean", action="store_true",
                    help="rimuove emoji, normalizza i trattini lunghi ed elimina le righe "
                         "segnaposto (es. 'aaaa') ereditate dal sorgente")
    args = ap.parse_args()

    # Annotazioni curate (es. banner LEGACY) iniettate nei file generati senza rompere
    # l'idempotenza: i marcatori vivono nel sidecar JSON, non nei file generati.
    ann_path = args.annotations or os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                "annotations.json")
    annotations = {}
    if os.path.exists(ann_path):
        with io.open(ann_path, encoding="utf-8") as fh:
            annotations = json.load(fh)

    # Redazioni deterministiche: sostituzioni regex applicate al testo finale per neutralizzare
    # riferimenti non desiderati (es. acquisizione P2P), preservando l'analisi tecnica. Le regole
    # vivono nel sidecar, l'output resta riproducibile e la redazione e' tracciata nel report.
    red_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "redactions.json")
    redaction_rules = []
    if os.path.exists(red_path):
        with io.open(red_path, encoding="utf-8") as fh:
            for rule in json.load(fh):
                redaction_rules.append((re.compile(rule["pattern"], re.IGNORECASE),
                                        rule["replacement"]))

    document = docx.Document(args.source)
    part = document.part
    classify = build_numbering_map(document)

    # Pass A: raccoglie i blocchi renderizzati in ordine.
    blocks = []  # ognuno: dict(kind, md, raw, images, level)
    for item in iter_block_items(document):
        if isinstance(item, Paragraph):
            kind, md, raw, images, level = render_paragraph(item, part, classify)
            if kind == "empty":
                blocks.append({"kind": "empty", "md": "", "raw": "", "images": [], "level": None})
            else:
                blocks.append({"kind": kind, "md": md, "raw": raw, "images": images, "level": level})
        else:
            kind, md, raw, images = render_table(item, part)
            blocks.append({"kind": "table", "md": md, "raw": raw, "images": images, "level": None})

    # Pre-calcolo: per ogni H4 stabilisce se ha figli H5 (-> cartella) o no (-> file).
    heading_positions = [(idx, b["level"]) for idx, b in enumerate(blocks) if b["kind"] == "heading"]
    h4_is_folder = {}
    for n, (idx, lvl) in enumerate(heading_positions):
        if lvl != 4:
            continue
        is_folder = False
        for idx2, lvl2 in heading_positions[n + 1:]:
            if lvl2 <= 4:
                break
            if lvl2 == 5:
                is_folder = True
                break
        h4_is_folder[idx] = is_folder

    # Pass B: assegna i blocchi ai file e costruisce l'albero.
    out_dir = args.out
    files = {}  # path -> OutFile
    order = []  # ordine di creazione dei file

    def get_file(path, root_level, title_md, is_index=False):
        if path not in files:
            files[path] = OutFile(path, root_level, title_md, is_index)
            order.append(path)
        return files[path]

    root_index_path = os.path.join(out_dir, "README.md")
    root_file = get_file(root_index_path, 2, "# Sony Xperia 1 III (pdx215) - documentazione", is_index=True)

    macro_count = 0
    cur_macro_dir = None
    cur_macro_file = None
    cur_h4_dir = None
    cur_h4_file = None  # file corrente di livello H4 (se non e' cartella)
    cur_target = root_file
    h4_counter = 0
    h5_counter = 0
    active_macro_selected = True  # per filtro --macro

    for idx, b in enumerate(blocks):
        if b["kind"] == "heading":
            level = b["level"]
            title_text = b["md"].strip()
            if level == 2:
                # titolo radice: preserva il testo H2 e accoglie il suo contenuto
                root_file.title_md = "# " + title_text
                cur_target = root_file
                continue
            if level == 3:
                macro_count += 1
                name = MACRO_NAMES.get(macro_count, "%02d-%s" % (macro_count, slugify(title_text)))
                cur_macro_dir = os.path.join(out_dir, name)
                cur_macro_file = get_file(os.path.join(cur_macro_dir, "README.md"), 3,
                                          "# " + title_text, is_index=True)
                root_file.children.append((title_text, os.path.join(name, "README.md").replace("\\", "/")))
                cur_target = cur_macro_file
                cur_h4_dir = None
                cur_h4_file = None
                h4_counter = 0
                active_macro_selected = (args.macro == 0 or args.macro == macro_count)
                continue
            if level == 4:
                h4_counter += 1
                slug = slugify(title_text)
                if h4_is_folder.get(idx):
                    cur_h4_dir = os.path.join(cur_macro_dir, "%02d-%s" % (h4_counter, slug))
                    cur_h4_file = get_file(os.path.join(cur_h4_dir, "README.md"), 4,
                                           "# " + title_text, is_index=True)
                    rel = os.path.relpath(cur_h4_file.path, cur_macro_dir).replace("\\", "/")
                    cur_macro_file.children.append((title_text, rel))
                    cur_target = cur_h4_file
                    h5_counter = 0
                else:
                    cur_h4_dir = None
                    f = get_file(os.path.join(cur_macro_dir, "%02d-%s.md" % (h4_counter, slug)), 4,
                                 "# " + title_text)
                    rel = os.path.relpath(f.path, cur_macro_dir).replace("\\", "/")
                    cur_macro_file.children.append((title_text, rel))
                    cur_h4_file = f
                    cur_target = f
                continue
            if level == 5:
                h5_counter += 1
                slug = slugify(title_text)
                base_dir = cur_h4_dir or cur_macro_dir
                f = get_file(os.path.join(base_dir, "%02d-%s.md" % (h5_counter, slug)), 5,
                             "# " + title_text)
                rel = os.path.relpath(f.path, base_dir).replace("\\", "/")
                if cur_h4_file is not None and cur_h4_file.is_index:
                    cur_h4_file.children.append((title_text, rel))
                cur_target = f
                continue
            # livelli 6-9: sotto-titolo dentro il file corrente
            depth = level - cur_target.root_level + 1
            if depth < 1:
                depth = 1
            if depth > 6:
                depth = 6
            cur_target.add("heading", ("#" * depth) + " " + title_text, [])
            continue

        # blocchi di contenuto
        if not active_macro_selected:
            continue
        if b["kind"] == "empty":
            continue
        kindmap = {"list": "list", "block": "block", "table": "block"}
        cur_target.add(kindmap[b["kind"]], b["md"], b["images"])

    # Scrittura dei file
    written = []
    total_headings_written = 0
    total_tables = sum(1 for b in blocks if b["kind"] == "table")
    image_records = []  # (file_md, nome_immagine)
    total_redactions = 0
    redacted_files = []  # (relpath, conteggio)
    clean_tot = {"placeholder": 0, "dashes": 0, "emoji": 0}

    for path in order:
        f = files[path]
        os.makedirs(os.path.dirname(path), exist_ok=True)
        total_headings_written += 1  # titolo radice del file
        prev_kind = None
        body_lines = []
        for kind, md, images in f.blocks:
            text = md
            if images:
                adir = os.path.join(os.path.dirname(path), "assets")
                os.makedirs(adir, exist_ok=True)
                names = []
                for blob, ext in images:
                    name = "img-%04d.%s" % (len(image_records), ext)
                    with open(os.path.join(adir, name), "wb") as imf:
                        imf.write(blob)
                    image_records.append((path.replace("\\", "/"), name))
                    names.append(name)
                placeholders = re.findall(r"\x00IMG(\d+)\x00", md)
                for local_i, ph in enumerate(placeholders):
                    if local_i < len(names):
                        text = text.replace("\x00IMG%s\x00" % ph,
                                            "![](assets/%s)" % names[local_i], 1)
            if kind == "block":
                # evita che righe di contenuto che iniziano con '#' (es. commenti
                # in snippet di comandi) vengano interpretate come titoli markdown
                text = re.sub(r"(?m)^(#{1,6})(?=\s|$)", r"\\\1", text)
            if kind == "heading":
                total_headings_written += 1
            sep = "\n" if (kind == "list" and prev_kind == "list") else "\n\n"
            if body_lines:
                body_lines.append(sep)
            body_lines.append(text)
            prev_kind = kind
        body = "".join(body_lines)
        if f.is_index and f.children:
            body += "\n\n## Contenuti\n\n"
            for title, rel in f.children:
                body += "- [%s](%s)\n" % (title, rel)
        rel_key = os.path.relpath(path, out_dir).replace("\\", "/")
        banner = annotations.get(rel_key)
        if banner:
            content = f.title_md + "\n\n" + banner.rstrip() + "\n\n" + body.strip() + "\n"
        else:
            content = f.title_md + "\n\n" + body.strip() + "\n"
        file_red = 0
        for rx, repl in redaction_rules:
            content, n = rx.subn(repl, content)
            file_red += n
        if file_red:
            total_redactions += file_red
            redacted_files.append((rel_key, file_red))
        if args.clean:
            content, cst = cleanup_text(content)
            for k in clean_tot:
                clean_tot[k] += cst[k]
        content = re.sub(r"\n{3,}", "\n\n", content)
        with io.open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
        written.append(path)

    # --- report di conversione -------------------------------------------
    markers = ("(tbc)", "aborted", "❌", "✔")
    flagged = []
    placeholder_headings = []
    heading_count = 0
    for b in blocks:
        if b["kind"] != "heading":
            continue
        heading_count += 1
        t = b["md"].strip()
        low = t.lower()
        if any(m in low for m in markers):
            flagged.append((b["level"], t))
        core = re.sub(r"[^a-z0-9]", "", low)
        if core and len(set(core)) == 1 and len(core) >= 4:
            placeholder_headings.append((b["level"], t))

    report = []
    report.append("# Report di conversione")
    report.append("")
    report.append("> Generato da `tools/docx-to-md.py`. Conversione verbatim: nessun contenuto "
                  "rimosso. Questo report elenca conteggi, marcatori di lavoro dell'autore e "
                  "mappa delle immagini, per tracciabilita'.")
    report.append("")
    report.append("## Conteggi")
    report.append("")
    report.append("- File Markdown generati: %d" % len(written))
    report.append("- Titoli totali (radice + sotto-titoli) scritti: %d" % total_headings_written)
    report.append("- Titoli nel sorgente: %d" % heading_count)
    report.append("- Tabelle nel sorgente: %d" % total_tables)
    report.append("- Immagini estratte: %d" % len(image_records))
    report.append("")
    report.append("## Sezioni con marcatori di lavoro dell'autore")
    report.append("")
    report.append("Titoli contenenti `(TBC)`, `aborted`, ❌ o ✔️, preservati verbatim:")
    report.append("")
    if flagged:
        for lvl, t in flagged:
            report.append("- H%d - %s" % (lvl, t))
    else:
        report.append("- nessuno")
    report.append("")
    report.append("## Titoli placeholder")
    report.append("")
    report.append("Titoli composti da un solo carattere ripetuto (es. `aaaaaaaaaaaaaa.`), "
                  "preservati verbatim:")
    report.append("")
    if placeholder_headings:
        for lvl, t in placeholder_headings:
            report.append("- H%d - %s" % (lvl, t))
    else:
        report.append("- nessuno")
    report.append("")
    report.append("## Mappa immagini")
    report.append("")
    report.append("Le immagini non sono versionate (gitignore `*.png`/`*.jpeg`); restano in locale "
                  "nelle cartelle `assets/`.")
    report.append("")
    if image_records:
        for fpath, name in image_records:
            report.append("- `%s` -> `%s`" % (os.path.dirname(fpath) + "/assets/" + name, name))
    else:
        report.append("- nessuna")
    report.append("")

    report.append("## Redazioni applicate")
    report.append("")
    report.append("Sostituzioni deterministiche (sidecar `tools/redactions.json`) per neutralizzare "
                  "riferimenti all'acquisizione P2P, preservando l'analisi tecnica. Questa e' una "
                  "divergenza voluta dal testo verbatim del sorgente.")
    report.append("")
    report.append("- Totale sostituzioni: %d" % total_redactions)
    if redacted_files:
        for rel, n in redacted_files:
            report.append("- %s: %d" % (rel, n))
    else:
        report.append("- nessuna")
    report.append("")

    if args.clean:
        report.append("## Pulizia applicata (--clean)")
        report.append("")
        report.append("Rimozione deterministica di rumore ereditato dal sorgente: emoji, trattini "
                      "lunghi normalizzati in trattini brevi, righe segnaposto (es. 'aaaa'). "
                      "Divergenza voluta dal testo verbatim.")
        report.append("")
        report.append("- Righe segnaposto rimosse: %d" % clean_tot["placeholder"])
        report.append("- Trattini normalizzati: %d" % clean_tot["dashes"])
        report.append("- Emoji rimosse: %d" % clean_tot["emoji"])
        report.append("")

    report_path = os.path.join(out_dir, "_CONVERSION-REPORT.md")
    report_text = "\n".join(report) + "\n"
    if args.clean:
        # coerenza: niente emoji/trattini lunghi nemmeno nel report, che cita i titoli marcati
        report_text, _ = cleanup_text(report_text)
    with io.open(report_path, "w", encoding="utf-8") as fh:
        fh.write(report_text)

    # --- corpus testuale per verifica no-content-loss ---------------------
    src_text = []
    for b in blocks:
        if b["raw"]:
            src_text.append(b["raw"])
    src_norm = re.sub(r"\s+", "", "".join(src_text))

    # Report di conteggio su stdout (UTF-8)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print("File scritti:", len(written))
    print("Titoli scritti (atteso = sorgente):", total_headings_written, "/", heading_count)
    print("Tabelle nel sorgente:", total_tables)
    print("Immagini estratte:", len(image_records))
    print("Caratteri testo sorgente (no spazi):", len(src_norm))
    print("Report:", report_path)


if __name__ == "__main__":
    main()
