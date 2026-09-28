#!/usr/bin/env python3
"""Update the navigational parts of a README and check its local links.

The prose stays owned by the project. Generated blocks are delimited by markers,
so repeated runs have a small, reviewable diff and preserve the file's EOL/BOM.
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import unquote


TOC_START = "<!-- sync-readme:toc:start -->"
TOC_END = "<!-- sync-readme:toc:end -->"
PACKAGES_START = "<!-- sync-readme:packages:start -->"
PACKAGES_END = "<!-- sync-readme:packages:end -->"
NON_PACKAGES = {"_notes", "agents", "context", "memory", "rules", "skills", "tools"}
LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
PACKAGE_ROW = re.compile(r"^\| `([^`]+)`[^|]*\|", re.MULTILINE)
PACKAGE_SUMMARY = re.compile(r"^<!-- readme-summary: (.+?) -->$", re.MULTILINE)
OLD_SUMMARY = re.compile(r"^- `([^`]+)` - (.+?): \[[^\]]+\]\([^)]+\)$", re.MULTILINE)


def read_text(path: Path) -> tuple[str, bytes, str, bool]:
    raw = path.read_bytes()
    bom = b"\xef\xbb\xbf" if raw.startswith(b"\xef\xbb\xbf") else b""
    body = raw[len(bom):].decode("utf-8")
    eol = "\r\n" if body.count("\r\n") > body.count("\n") - body.count("\r\n") else "\n"
    return body.replace("\r\n", "\n"), bom, eol, body.endswith("\n")


def heading_slug(title: str) -> str:
    title = re.sub(r"<[^>]+>", "", title)
    title = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", title)
    title = title.lower().strip()
    title = "".join(ch for ch in title if ch in " -_" or unicodedata.category(ch)[0] in "LN")
    return title.replace(" ", "-")


def headings(markdown: str) -> list[tuple[int, str, str]]:
    result: list[tuple[int, str, str]] = []
    seen: dict[str, int] = {}
    fence: tuple[str, int] | None = None
    for line in markdown.splitlines():
        marker = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if marker:
            run = marker.group(1)
            if fence is None:
                fence = (run[0], len(run))
            elif fence[0] == run[0] and len(run) >= fence[1]:
                fence = None
            continue
        if fence is not None:
            continue
        match = re.match(r"^(#{1,6}) (.+?)(?: +#+)?$", line)
        if not match:
            continue
        level = len(match.group(1))
        title = match.group(2).strip()
        base = heading_slug(title)
        suffix = seen.get(base, 0)
        seen[base] = suffix + 1
        slug = f"{base}-{suffix}" if suffix else base
        result.append((level, title, slug))
    return result


def render_toc(markdown: str) -> str:
    items = [(title, slug) for level, title, slug in headings(markdown) if level == 2 and title != "Indice"]
    if not items:
        raise ValueError("Il README non ha sezioni di livello 2 da indicizzare")
    quick = " · ".join(f"[{title}](#{slug})" for title, slug in items[:4])
    all_items = "\n".join(f"- [{title}](#{slug})" for title, slug in items)
    return f"{quick}\n\n<details>\n<summary>Tutte le sezioni</summary>\n\n{all_items}\n\n</details>"


def managed_block(markdown: str, start: str, end: str, content: str) -> str:
    if markdown.count(start) != 1 or markdown.count(end) != 1:
        raise ValueError(f"Marcatori mancanti o duplicati: {start}, {end}")
    before, rest = markdown.split(start, 1)
    _, after = rest.split(end, 1)
    return f"{before}{start}\n{content}\n{end}{after}"


def ensure_toc(markdown: str) -> str:
    if TOC_START in markdown or TOC_END in markdown:
        return markdown
    match = re.search(r"^## ", markdown, re.MULTILINE)
    if not match:
        raise ValueError("Il README non ha un titolo di livello 2")
    block = f"## Indice\n\n{TOC_START}\n{TOC_END}\n\n"
    return markdown[:match.start()] + block + markdown[match.start():]


def bundle_packages(root: Path, old_markdown: str) -> str:
    catalog = root / ".claude" / "templates" / "PACKAGES.md"
    package_root = catalog.parent
    if not catalog.is_file():
        raise ValueError("--bundle richiede .claude/templates/PACKAGES.md")
    source = catalog.read_text(encoding="utf-8-sig")
    catalog_names = PACKAGE_ROW.findall(source)
    if len(catalog_names) != len(set(catalog_names)):
        raise ValueError("Il catalogo contiene nomi di pacchetto duplicati")
    package_dirs = {p.name for p in package_root.iterdir() if p.is_dir() and p.name not in NON_PACKAGES and (p / "README.md").is_file()}
    missing = sorted(package_dirs - set(catalog_names))
    if missing:
        raise ValueError("Pacchetti senza voce di catalogo: " + ", ".join(missing))
    old_summaries = dict(OLD_SUMMARY.findall(old_markdown))
    groups: list[tuple[str, list[str]]] = []
    current: list[str] | None = None
    for line in source.splitlines():
        if line.startswith("### "):
            current = []
            groups.append((line[4:].strip(), current))
        row = PACKAGE_ROW.match(line)
        if row and current is not None and row.group(1) in package_dirs:
            current.append(row.group(1))
    if sum(len(names) for _, names in groups) != len(package_dirs):
        raise ValueError("Un pacchetto a cartella non appartiene a un settore del catalogo")
    package_label = "pacchetto a cartella" if len(package_dirs) == 1 else "pacchetti a cartella"
    lines = [f"**{len(package_dirs)} {package_label}** su **{len(catalog_names)} voci** del catalogo. Le altre voci non hanno un README di pacchetto dedicato."]
    for title, names in groups:
        if not names:
            continue
        lines.extend(["", f"### {title}", ""])
        for name in names:
            readme = package_root / name / "README.md"
            source_summary = PACKAGE_SUMMARY.search(readme.read_text(encoding="utf-8-sig"))
            summary = source_summary.group(1) if source_summary else old_summaries.get(name)
            if not summary:
                raise ValueError(f"Manca una descrizione breve per {name}: aggiungere <!-- readme-summary: ... --> al README del pacchetto")
            if "\n" in summary or "|" in summary:
                raise ValueError(f"Descrizione breve non valida per {name}")
            path = f".claude/templates/{name}/README.md"
            lines.append(f"- `{name}` - {summary}: [{path}]({path})")
    return "\n".join(lines)


def validate_links(markdown: str, root: Path) -> list[str]:
    slugs = {slug for _, _, slug in headings(markdown)}
    errors: list[str] = []
    for target in LINK.findall(markdown):
        target = target.split(" ", 1)[0].strip("<>")
        if target.startswith(("https://", "http://", "mailto:", "data:")):
            continue
        path, _, anchor = unquote(target).partition("#")
        if not path:
            if anchor and anchor not in slugs:
                errors.append(f"Ancora inesistente: #{anchor}")
        elif not (root / path).exists():
            errors.append(f"Percorso inesistente: {path}")
    return sorted(set(errors))


def sync(root: Path, write: bool, bundle: bool) -> int:
    readme = root / "README.md"
    if not readme.is_file():
        print(f"README mancante: {readme}", file=sys.stderr)
        return 2
    try:
        original, bom, eol, final_newline = read_text(readme)
        proposed = ensure_toc(original) if write else original
        if bundle:
            package_content = bundle_packages(root, proposed)
            proposed = managed_block(proposed, PACKAGES_START, PACKAGES_END, package_content)
        proposed = managed_block(proposed, TOC_START, TOC_END, render_toc(proposed))
        errors = validate_links(proposed, root)
        if errors:
            raise ValueError("\n".join(errors))
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"sync-readme: {exc}", file=sys.stderr)
        return 2
    if proposed == original:
        print("README allineato; link locali validi")
        return 0
    if not write:
        print("README da aggiornare: eseguire sync-readme.py --write" + (" --bundle" if bundle else ""), file=sys.stderr)
        return 1
    rendered = proposed.replace("\n", eol)
    if not final_newline:
        rendered = rendered.rstrip("\r\n")
    readme.write_bytes(bom + rendered.encode("utf-8"))
    print("README aggiornato; link locali validi")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Radice del progetto")
    parser.add_argument("--write", action="store_true", help="Aggiorna i blocchi generati")
    parser.add_argument("--check", action="store_true", help="Verifica senza scrivere (default)")
    parser.add_argument("--bundle", action="store_true", help="Genera anche l'indice dei pacchetti del template")
    args = parser.parse_args()
    if args.write and args.check:
        parser.error("--write e --check sono alternativi")
    return sync(args.root.resolve(), args.write, args.bundle)


if __name__ == "__main__":
    raise SystemExit(main())
