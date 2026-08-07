#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""md-unwrap - srotola i paragrafi hard-wrapped nei file Markdown.

L'unica trasformazione applicata e' togliere gli a capo interni a un blocco di testo
(paragrafo, voce di elenco, riga di citazione) e l'indentazione di continuazione,
unendo i pezzi con un singolo spazio. Nient'altro viene normalizzato: marcatori di
lista, tabelle, stili di titolo, escaping e ordine restano come sono.

Zero dipendenze obbligatorie. Se `markdown-it-py` e' importabile, ogni file viene
validato con un oracolo di rendering (l'HTML normalizzato deve restare identico) e in
caso di divergenza il file non viene scritto.

Uso: python md-unwrap.py [percorsi...] [--check] [--diff] [opzioni]
"""

from __future__ import annotations

import argparse
import difflib
import fnmatch
import os
import re
import subprocess
import sys

TAB_STOP = 4

DEFAULT_EXTS = ('.md', '.markdown')

IGNORE_MARKER = '.md-unwrap-ignore'

DEFAULT_EXCLUDES = (
    '.git', '.hg', '.svn', 'node_modules', '.venv', 'venv', '__pycache__',
    '.mypy_cache', '.pytest_cache', '.tox', '.cache', 'dist', 'build', 'out',
    '.next', '.nuxt', 'target', 'vendor', 'site-packages', '.claude-cache',
)

# --------------------------------------------------------------------------- #
# Riconoscitori di riga                                                       #
# --------------------------------------------------------------------------- #

RE_EOL = re.compile(r'(\r\n|\n|\r)\Z')
RE_FENCE = re.compile(r'^(`{3,}|~{3,})(.*)$')
RE_ATX = re.compile(r'^#{1,6}(?:[ \t].*)?$')
RE_TBREAK = re.compile(r'^(?:\*[ \t]*){3,}$|^(?:-[ \t]*){3,}$|^(?:_[ \t]*){3,}$')
RE_SETEXT = re.compile(r'^(?:=+|-+)[ \t]*$')
RE_BQ_CHAIN = re.compile(r'^(?: {0,3}>[ \t]?)+')
RE_LIST = re.compile(r'^([-+*]|\d{1,9}[.)])(?:([ \t]+)(.*)|[ \t]*)$')
RE_LINKDEF = re.compile(r'^\[(?:[^\[\]\\]|\\.)*\]:(.*)$')
# Destinazione di una definizione di link: un solo token senza spazi, o fra
# parentesi angolari, con titolo facoltativo. Se il resto della riga non ha
# questa forma, quella riga non e' una definizione di link ma testo etichettato,
# tipicamente una nota a pie' di pagina `[^n]: testo ...`.
RE_LINK_DEST = re.compile(
    r'^[ \t]*(?:<[^<>]*>|[^\s<>]+)(?:[ \t]+(?:"[^"]*"|\'[^\']*\'|\([^)]*\)))?[ \t]*$'
)
RE_TABLE_DELIM = re.compile(r'^\|?[ \t]*:?-+:?[ \t]*(?:\|[ \t]*:?-+:?[ \t]*)*\|?[ \t]*$')
RE_TITLE_ONLY = re.compile(r'''^[ \t]*(?:"[^"]*"|'[^']*'|\([^)]*\))[ \t]*$''')
RE_TRAILING_SPACES = re.compile(r'( {2,})$')

RE_HTML_RAW = re.compile(r'^<(?:script|pre|style|textarea)(?:[ \t>]|$)', re.I)
RE_HTML_RAW_END = re.compile(r'</(?:script|pre|style|textarea)>', re.I)
RE_HTML_DECL = re.compile(r'^<![A-Za-z]')
RE_HTML_TAG_NAME = re.compile(r'^</?([A-Za-z][A-Za-z0-9-]*)(?:[ \t]|/?>|$)')
RE_HTML_STANDALONE = re.compile(
    r'^(?:<[A-Za-z][A-Za-z0-9-]*'
    r'(?:[ \t]+[^\s"\'=<>`/]+(?:[ \t]*=[ \t]*(?:[^\s"\'=<>`]+|\'[^\']*\'|"[^"]*"))?)*'
    r'[ \t]*/?>|</[A-Za-z][A-Za-z0-9-]*[ \t]*>)[ \t]*$'
)

HTML_BLOCK_TAGS = {
    'address', 'article', 'aside', 'base', 'basefont', 'blockquote', 'body',
    'caption', 'center', 'col', 'colgroup', 'dd', 'details', 'dialog', 'dir',
    'div', 'dl', 'dt', 'fieldset', 'figcaption', 'figure', 'footer', 'form',
    'frame', 'frameset', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'head', 'header',
    'hr', 'html', 'iframe', 'legend', 'li', 'link', 'main', 'menu', 'menuitem',
    'nav', 'noframes', 'ol', 'optgroup', 'option', 'p', 'param', 'search',
    'section', 'summary', 'table', 'tbody', 'td', 'tfoot', 'th', 'thead',
    'title', 'tr', 'track', 'ul',
}

HTML_KINDS = ('html-raw', 'html-comment', 'html-pi', 'html-decl', 'html-cdata', 'html-block')

# Costrutti che interrompono un blocco di testo quando compaiono su una riga di
# continuazione. `html-standalone` (tipo 7) e `code-indent` non interrompono un
# paragrafo secondo CommonMark, quindi non sono qui.
BLOCK_STARTERS = frozenset(
    ('fence', 'atx', 'tbreak', 'list', 'bq', 'linkdef', 'label-text', 'table-delim') + HTML_KINDS
)


def measure_indent(body: str) -> int:
    """Larghezza dell'indentazione iniziale, con i tab espansi a multipli di 4."""
    width = 0
    for ch in body:
        if ch == ' ':
            width += 1
        elif ch == '\t':
            width += TAB_STOP - (width % TAB_STOP)
        else:
            break
    return width


def is_blank(body: str) -> bool:
    return not body.strip()


def fence_open(s: str):
    """(carattere, lunghezza) se `s` apre un blocco recintato, altrimenti None."""
    m = RE_FENCE.match(s)
    if not m:
        return None
    marker, info = m.group(1), m.group(2)
    if marker[0] == '`' and '`' in info:
        return None  # info string con backtick: non e' un'apertura valida
    return marker[0], len(marker)


def fence_close(s: str, char: str, length: int) -> bool:
    """Vero se `s` chiude un fence aperto con `char` ripetuto `length` volte."""
    body = s.strip()
    if not body or set(body) != {char}:
        return False
    return len(body) >= length


def is_table_delim(s: str) -> bool:
    return '|' in s and bool(RE_TABLE_DELIM.match(s.strip()))


def block_kind(s: str) -> str:
    """Classifica una riga di inizio blocco, indentazione iniziale gia' rimossa."""
    if is_blank(s):
        return 'blank'
    if fence_open(s):
        return 'fence'
    if RE_HTML_RAW.match(s):
        return 'html-raw'
    if s.startswith('<!--'):
        return 'html-comment'
    if s.startswith('<?'):
        return 'html-pi'
    if s.startswith('<![CDATA['):
        return 'html-cdata'
    if RE_HTML_DECL.match(s):
        return 'html-decl'
    m = RE_HTML_TAG_NAME.match(s)
    if m and m.group(1).lower() in HTML_BLOCK_TAGS:
        return 'html-block'
    if RE_ATX.match(s):
        return 'atx'
    if RE_TBREAK.match(s):
        return 'tbreak'
    if s.lstrip().startswith('>'):
        return 'bq'
    if RE_LIST.match(s):
        return 'list'
    if is_table_delim(s):
        return 'table-delim'
    m = RE_LINKDEF.match(s)
    if m:
        rest = m.group(1)
        if not rest.strip() or RE_LINK_DEST.match(rest):
            return 'linkdef'
        return 'label-text'
    if RE_HTML_STANDALONE.match(s):
        return 'html-standalone'
    return 'text'


def hard_break_suffix(body: str):
    """Suffisso di interruzione di riga intenzionale, o None se la riga non ne ha."""
    if body.endswith('\\') and not body.endswith('\\\\'):
        return ''  # il backslash sopravvive a strip(), non va reinserito
    m = RE_TRAILING_SPACES.search(body)
    if m:
        return m.group(1)
    return None


def has_hard_break(body: str) -> bool:
    return hard_break_suffix(body) is not None


RE_BACKTICK_RUN = re.compile(r'(?<!\\)(`+)')

# Caratteri con cui si disegnano gli schemi a caratteri: box drawing, blocchi e
# forme geometriche. Nella prosa non compaiono praticamente mai, mentre le frecce
# (`->`, U+2192) sono comuni e restano fuori di proposito.
RE_ART_CHARS = re.compile(r'[─-╿▀-▟■-◿]')
RE_ART_ASCII = re.compile(r'^[ \t]*\||^[ \t]*\+[-=+]|\+--|--\+')


def looks_like_diagram(body: str) -> bool:
    """Vero se la riga sembra parte di uno schema disegnato a caratteri.

    Uno schema ASCII scritto fuori da un blocco di codice e' un paragrafo come
    gli altri per CommonMark, quindi il rendering non cambia se lo si unisce: e'
    gia' collassato anche prima. Nel sorgente pero' l'allineamento e' l'intero
    contenuto informativo del disegno, e unirlo lo distrugge. Quando una riga di
    un blocco di testo sembra un disegno, il blocco si emette verbatim."""
    return bool(RE_ART_CHARS.search(body) or RE_ART_ASCII.search(body))


def code_span_crosses_line(text: str) -> bool:
    """Vero se nel testo un code span inline attraversa un a capo.

    Un code span si apre con una sequenza di backtick e si chiude con una
    sequenza della stessa lunghezza esatta; le sequenze di lunghezza diversa
    incontrate dentro un code span sono contenuto, e una sequenza che non si
    chiude mai e' testo letterale. Solo un code span che si apre su una riga e si
    chiude su un'altra e' un problema: CommonMark normalizza lo spazio ai bordi
    di un code span, quindi unire quelle righe ne cambierebbe il contenuto reso.
    In quel caso il paragrafo si emette verbatim, perche' un code span vive
    dentro un solo blocco e la sua estensione e' quella del paragrafo."""
    open_len, open_end = 0, -1
    for match in RE_BACKTICK_RUN.finditer(text):
        run = len(match.group(1))
        if open_len == 0:
            open_len, open_end = run, match.end()
        elif run == open_len:
            if '\n' in text[open_end:match.start()]:
                return True
            open_len = 0
    return False


# --------------------------------------------------------------------------- #
# Scanner                                                                     #
# --------------------------------------------------------------------------- #

class Scanner:
    """Percorre le righe una volta, emette i blocchi verbatim e unisce i soli
    blocchi di testo. Ogni riga e' una coppia (corpo, terminatore), cosi il
    terminatore originale di ogni riga sopravvissuta resta quello del file."""

    def __init__(self, lines, guard_spans=False):
        self.lines = lines
        self.guard_spans = guard_spans
        self.n = len(lines)
        self.out = []
        self.joins = 0
        self.stack = []  # (indentazione del marcatore, indentazione del contenuto)

    # -- utilita' ---------------------------------------------------------- #

    def inner(self, k: int, bq: bool) -> str:
        """Corpo della riga k privato dell'eventuale catena di citazione."""
        body = self.lines[k][0]
        if bq:
            m = RE_BQ_CHAIN.match(body)
            if m:
                return body[m.end():]
        return body

    def emit(self, a: int, b: int) -> None:
        """Emette verbatim le righe da a incluso a b escluso."""
        self.out.extend(self.lines[a:b])

    # -- ciclo principale -------------------------------------------------- #

    def run(self):
        i = self.front_matter()
        while i < self.n:
            body = self.lines[i][0]
            if is_blank(body):
                self.emit(i, i + 1)
                i += 1
                continue

            bq_match = RE_BQ_CHAIN.match(body)
            bq = bq_match is not None
            if bq:
                # Dentro una citazione non si tiene traccia delle liste: le voci
                # si trattano come blocchi di testo con il proprio prefisso.
                self.stack = []
                inner = body[bq_match.end():]
                base = 0
            else:
                ind = measure_indent(body)
                while self.stack and ind < self.stack[-1][1]:
                    self.stack.pop()
                inner = body
                base = self.stack[-1][1] if self.stack else 0

            ind_inner = measure_indent(inner)
            rel = ind_inner - base
            if rel >= 4:
                i = self.consume_indented_code(i, bq, base)
                continue

            s = inner.lstrip(' \t')
            kind = block_kind(s)

            if kind == 'fence':
                i = self.consume_fence(i, bq, s)
            elif kind in HTML_KINDS:
                i = self.consume_html(i, bq, kind, s)
            elif kind == 'table-delim':
                # Riga separatrice senza intestazione davanti: quello che segue e'
                # corpo di tabella o comunque testo che non conviene toccare.
                i = self.consume_table(i, bq, skip=1)
            elif kind in ('blank', 'atx', 'tbreak', 'html-standalone'):
                # `blank` qui vuol dire riga vuota dentro una citazione (`>` da solo):
                # separa due blocchi e non si attraversa.
                self.emit(i, i + 1)
                i += 1
            elif kind == 'linkdef':
                i = self.consume_linkdef(i, bq, s)
            elif kind == 'label-text':
                # Nota a pie' di pagina o testo etichettato: si comporta come una
                # voce di elenco, cioe' assorbe le proprie righe di continuazione
                # conservando il prefisso `[etichetta]: `.
                i = self.collect_run(i, bq, base)
            elif self.table_starts_at(i, bq, s):
                i = self.consume_table(i, bq)
            elif kind == 'list':
                i = self.consume_list_item(i, bq, inner, ind_inner, s)
            else:
                i = self.collect_run(i, bq, base)
        return self.out, self.joins

    # -- blocchi verbatim -------------------------------------------------- #

    def front_matter(self) -> int:
        """Front matter YAML o TOML in testa al file: verbatim, delimitatori inclusi."""
        if not self.lines:
            return 0
        first = self.lines[0][0].rstrip()
        if first == '---':
            closers = ('---', '...')
        elif first == '+++':
            closers = ('+++',)
        else:
            return 0
        for k in range(1, self.n):
            if self.lines[k][0].rstrip() in closers:
                self.emit(0, k + 1)
                return k + 1
        return 0  # nessuna chiusura: non e' front matter, e' altro

    def consume_fence(self, i: int, bq: bool, s: str) -> int:
        char, length = fence_open(s)
        j = i + 1
        while j < self.n:
            inner_j = self.inner(j, bq)
            if bq and RE_BQ_CHAIN.match(self.lines[j][0]) is None and is_blank(inner_j):
                break  # la citazione finisce, e con lei il fence
            if measure_indent(inner_j) < 4 and fence_close(inner_j, char, length):
                j += 1
                break
            j += 1
        self.emit(i, j)
        return j

    def consume_html(self, i: int, bq: bool, kind: str, s: str) -> int:
        if kind == 'html-raw':
            end = lambda t: bool(RE_HTML_RAW_END.search(t))
        elif kind == 'html-comment':
            end = lambda t: '-->' in t
        elif kind == 'html-pi':
            end = lambda t: '?>' in t
        elif kind == 'html-cdata':
            end = lambda t: ']]>' in t
        elif kind == 'html-decl':
            end = lambda t: '>' in t
        else:
            end = None  # tipo 6: si chiude sulla prima riga vuota
        if end is not None and end(s):
            self.emit(i, i + 1)
            return i + 1
        j = i + 1
        while j < self.n:
            inner_j = self.inner(j, bq)
            if end is None:
                if is_blank(inner_j):
                    break
                j += 1
            else:
                j += 1
                if end(inner_j):
                    break
        self.emit(i, j)
        return j

    def consume_indented_code(self, i: int, bq: bool, base: int) -> int:
        j = i
        last_code = i
        while j < self.n:
            inner_j = self.inner(j, bq)
            if is_blank(inner_j):
                j += 1
                continue
            if measure_indent(inner_j) - base < 4:
                break
            last_code = j
            j += 1
        self.emit(i, last_code + 1)
        return last_code + 1

    def consume_linkdef(self, i: int, bq: bool, s: str) -> int:
        """Definizione di link di riferimento: riga a se', piu' l'eventuale
        continuazione (URL o titolo su riga propria) che le appartiene."""
        j = i + 1
        rest = RE_LINKDEF.match(s).group(1).strip()
        if not rest and j < self.n and not is_blank(self.inner(j, bq)):
            j += 1  # l'URL sta sulla riga successiva
            rest = 'url-consumato'
        if j < self.n and RE_TITLE_ONLY.match(self.inner(j, bq)):
            j += 1  # il titolo sta sulla riga successiva
        self.emit(i, j)
        return j

    def table_starts_at(self, i: int, bq: bool, s: str) -> bool:
        if '|' not in s or i + 1 >= self.n:
            return False
        if bq and RE_BQ_CHAIN.match(self.lines[i + 1][0]) is None:
            return False
        return is_table_delim(self.inner(i + 1, bq).lstrip(' \t'))

    def consume_table(self, i: int, bq: bool, skip: int = 2) -> int:
        j = min(i + skip, self.n)
        while j < self.n:
            if bq and RE_BQ_CHAIN.match(self.lines[j][0]) is None:
                break
            inner_j = self.inner(j, bq)
            if is_blank(inner_j):
                break
            if block_kind(inner_j.lstrip(' \t')) in BLOCK_STARTERS - {'table-delim'}:
                break
            j += 1
        self.emit(i, j)
        return j

    # -- blocchi di testo -------------------------------------------------- #

    def consume_list_item(self, i, bq, inner, ind_inner, s) -> int:
        m = RE_LIST.match(s)
        marker, spaces, content = m.group(1), m.group(2) or '', m.group(3)
        if content is None or not content.strip() or len(spaces) >= 5:
            content_indent = ind_inner + len(marker) + 1
        else:
            content_indent = ind_inner + len(marker) + len(spaces)
        if not bq:
            self.stack.append((ind_inner, content_indent))
        # Se il contenuto della voce apre a sua volta un blocco (un fence, una
        # tabella), la riga si emette verbatim e il blocco si gestisce dopo.
        if content and block_kind(content) != 'text':
            self.emit(i, i + 1)
            return i + 1
        return self.collect_run(i, bq, content_indent)

    def collect_run(self, i: int, bq: bool, base: int) -> int:
        """Raccoglie un blocco di testo e le sue righe di continuazione."""
        head_body, head_term = self.lines[i]
        if has_hard_break(head_body):
            # Interruzione voluta sulla riga di apertura: resta da sola, e la riga
            # seguente ricomincia un blocco per conto proprio.
            self.emit(i, i + 1)
            return i + 1
        pieces = [head_body.rstrip()]
        term = head_term
        verbatim = False
        j = i + 1
        while j < self.n:
            prev_body = self.lines[j - 1][0]
            if has_hard_break(prev_body):
                break
            body = self.lines[j][0]
            if is_blank(body):
                break
            if bq:
                m = RE_BQ_CHAIN.match(body)
                inner = body[m.end():] if m else body  # senza marcatore: lazy
            else:
                if RE_BQ_CHAIN.match(body):
                    break
                inner = body
            if is_blank(inner):
                break  # `>` da solo: riga vuota dentro la citazione
            s = inner.lstrip(' \t')
            if measure_indent(inner) - base < 4:
                # Un sottolineato Setext o una riga separatrice di tabella
                # cambiano la natura del blocco appena raccolto: si lascia intatto.
                if RE_SETEXT.match(s) or is_table_delim(s):
                    verbatim = True
                    break
                if block_kind(s) in BLOCK_STARTERS:
                    break
            piece = s.strip()
            suffix = hard_break_suffix(inner)
            if suffix:
                piece += suffix
            pieces.append(piece)
            term = self.lines[j][1]
            j += 1

        # Deciso l'intervallo del blocco, due controlli sull'insieme delle sue
        # righe. Uno schema disegnato a caratteri ferma sempre l'unione, perche'
        # il rendering non lo protegge: e' il sorgente a perderci. Un code span
        # che attraversa un a capo la ferma solo nella passata prudente, quella
        # di riserva, perche' quasi sempre unire e' innocuo e l'arbitro giusto e'
        # l'oracolo di rendering, non un'euristica.
        if not verbatim and j > i + 1:
            bodies = [self.lines[k][0] for k in range(i, j)]
            if any(looks_like_diagram(b) for b in bodies):
                verbatim = True
            elif self.guard_spans and code_span_crosses_line('\n'.join(bodies)):
                verbatim = True

        if verbatim or len(pieces) == 1:
            end = j if verbatim else i + 1
            self.emit(i, end)
            return end
        self.out.append((' '.join(pieces), term))
        self.joins += len(pieces) - 1
        return j


# --------------------------------------------------------------------------- #
# Trasformazione e verifiche                                                   #
# --------------------------------------------------------------------------- #

def split_lines(text: str):
    lines = []
    for raw in text.splitlines(keepends=True):
        m = RE_EOL.search(raw)
        if m:
            lines.append((raw[:m.start()], m.group(1)))
        else:
            lines.append((raw, ''))
    return lines


def unwrap(text: str, guard_spans: bool = False):
    """Restituisce (testo srotolato, numero di righe unite).

    Con `guard_spans` non si uniscono i blocchi attraversati da un code span
    inline: e' la passata prudente di riserva, usata quando l'oracolo boccia il
    risultato della passata normale."""
    bom = ''
    if text.startswith('\ufeff'):
        bom, text = '\ufeff', text[1:]
    out, joins = Scanner(split_lines(text), guard_spans).run()
    return bom + ''.join(body + term for body, term in out), joins


RE_LINE_BQ_PREFIX = re.compile(r'(?m)^(?: {0,3}>[ \t]?)+')


def check_invariant(before: str, after: str):
    """Invariante forte a costo zero: a parte lo spazio bianco e i marcatori di
    citazione a inizio riga, che l'unione di una citazione assorbe per definizione,
    il flusso dei caratteri deve restare identico. Che i marcatori di citazione
    restino al posto giusto lo verifica poi l'oracolo di rendering."""
    strip = lambda t: re.sub(r'\s+', '', RE_LINE_BQ_PREFIX.sub('', t))
    if strip(before) != strip(after):
        return 'il flusso dei caratteri non-spazio e cambiato'
    return None


_ORACLE = None


def get_oracle():
    """Renderer CommonMark+GFM se `markdown-it-py` e' disponibile, altrimenti None."""
    global _ORACLE
    if _ORACLE is None:
        try:
            from markdown_it import MarkdownIt
            md = MarkdownIt('commonmark')
            for rule in ('table', 'strikethrough'):
                try:
                    md.enable(rule)
                except Exception:
                    pass
            _ORACLE = md
        except Exception:
            _ORACLE = False
    return _ORACLE or None


def render_equal(before: str, after: str):
    """None se il rendering coincide, altrimenti il motivo della divergenza."""
    md = get_oracle()
    if md is None:
        return None
    norm = lambda t: re.sub(r'\s+', ' ', md.render(t)).strip()
    if norm(before) != norm(after):
        return 'il rendering HTML normalizzato differisce'
    return None


def verify(before: str, after: str, oracle_mode: str):
    reason = check_invariant(before, after)
    if reason:
        return reason
    if oracle_mode == 'off':
        return None
    if oracle_mode == 'require' and get_oracle() is None:
        return 'oracolo di rendering richiesto ma markdown-it-py non e installato'
    return render_equal(before, after)


# --------------------------------------------------------------------------- #
# CLI                                                                          #
# --------------------------------------------------------------------------- #

def read_text(path: str):
    with open(path, 'rb') as fh:
        raw = fh.read()
    return raw.decode('utf-8')


def write_text(path: str, text: str) -> None:
    with open(path, 'wb') as fh:
        fh.write(text.encode('utf-8'))


def display_path(path: str) -> str:
    """Percorso da mostrare: relativo se possibile, altrimenti assoluto. Su Windows
    `relpath` solleva un'eccezione quando il file sta su un altro disco rispetto
    alla cartella corrente, ed e' un caso normale, non un errore."""
    try:
        return os.path.relpath(path)
    except ValueError:
        return path


def is_excluded(path: str, root: str, patterns) -> bool:
    try:
        rel = os.path.relpath(path, root).replace(os.sep, '/')
    except ValueError:
        rel = path.replace(os.sep, '/')
    parts = rel.split('/')
    for pat in patterns:
        if any(fnmatch.fnmatch(p, pat) for p in parts):
            return True
        if fnmatch.fnmatch(rel, pat):
            return True
    return False


_MARKER_CACHE = {}


def dir_is_marked(dirpath: str) -> bool:
    """Vero se la cartella, o una qualsiasi delle sue antenate, contiene il file
    marcatore `.md-unwrap-ignore`: quel sottoalbero non si tocca. Serve a proteggere
    materiale che deve restare byte per byte com'e', per esempio le fixture di test."""
    dirpath = os.path.abspath(dirpath)
    chain = []
    current = dirpath
    while True:
        if current in _MARKER_CACHE:
            marked = _MARKER_CACHE[current]
            break
        chain.append(current)
        if os.path.isfile(os.path.join(current, IGNORE_MARKER)):
            marked = True
            break
        parent = os.path.dirname(current)
        if parent == current:
            marked = False
            break
        current = parent
    for item in chain:
        _MARKER_CACHE[item] = marked
    return marked


def collect_files(paths, exts, excludes, only_tracked=False):
    found, marked = [], 0
    for target in paths:
        target = os.path.abspath(target)
        if only_tracked and os.path.isdir(target):
            # Enumerare da git invece che dal filesystem: in un repository che
            # contiene un corpus non tracciato di centinaia di migliaia di file,
            # camminare l'albero costa minuti e serve a nulla, perche' i file da
            # processare sono solo quelli che git conosce.
            prefix = os.path.normcase(target + os.sep)
            entries = tracked_files(target)
            if not entries:
                found.append(('__nogit__',
                              '--only-tracked: %s non e un repository git, o git non e '
                              'disponibile; nessun file processato' % target))
                continue
            for key in sorted(entries):
                if not key.startswith(prefix) or not key.endswith(tuple(exts)):
                    continue
                path = entries[key]
                if dir_is_marked(os.path.dirname(path)):
                    marked += 1
                    continue
                if is_excluded(path, target, excludes):
                    continue
                found.append(path)
            continue
        if os.path.isfile(target):
            if target.lower().endswith(tuple(exts)):
                if dir_is_marked(os.path.dirname(target)):
                    marked += 1
                else:
                    found.append(target)
            continue
        if os.path.isdir(target):
            for dirpath, dirnames, filenames in os.walk(target):
                if os.path.isfile(os.path.join(dirpath, IGNORE_MARKER)):
                    for _, _sub, sub_files in os.walk(dirpath):
                        marked += sum(1 for f in sub_files if f.lower().endswith(tuple(exts)))
                    dirnames[:] = []
                    continue
                dirnames[:] = [
                    d for d in sorted(dirnames)
                    if not is_excluded(os.path.join(dirpath, d), target, excludes)
                ]
                for name in sorted(filenames):
                    full = os.path.join(dirpath, name)
                    if name.lower().endswith(tuple(exts)) and not is_excluded(full, target, excludes):
                        found.append(full)
            continue
        import glob
        matches = sorted(glob.glob(target, recursive=True))
        if not matches:
            found.append(('__missing__', 'percorso inesistente: %s' % target))
            continue
        for match in matches:
            if os.path.isfile(match) and match.lower().endswith(tuple(exts)):
                if dir_is_marked(os.path.dirname(os.path.abspath(match))):
                    marked += 1
                else:
                    found.append(os.path.abspath(match))
    seen, unique = set(), []
    for item in found:
        if isinstance(item, tuple):
            unique.append(item)
            continue
        if item not in seen:
            seen.add(item)
            unique.append(item)
    return unique, marked


_TRACKED_CACHE = {}


def tracked_files(dirpath: str):
    """File tracciati da git nel repository che contiene `dirpath`, come dizionario
    dal percorso assoluto normalizzato (per il confronto, che su Windows va fatto
    senza distinzione di maiuscole) al percorso reale (per aprire il file e per
    scriverlo nei messaggi con il nome giusto). Dizionario vuoto se non e' un
    repository o se git non e' disponibile. Memoizzato per radice."""
    try:
        top = subprocess.run(
            ['git', '-C', dirpath, 'rev-parse', '--show-toplevel'],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        )
    except OSError:
        return {}
    if top.returncode != 0:
        return {}
    root = os.path.abspath(top.stdout.decode('utf-8', 'replace').strip())
    if root in _TRACKED_CACHE:
        return _TRACKED_CACHE[root]
    listing = subprocess.run(
        ['git', '-C', root, 'ls-files', '-z'],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
    )
    entries = listing.stdout.decode('utf-8', 'replace').split('\0') if listing.returncode == 0 else []
    result = {}
    for entry in entries:
        if not entry:
            continue
        real = os.path.join(root, entry.replace('/', os.sep))
        result[os.path.normcase(real)] = real
    _TRACKED_CACHE[root] = result
    return result


def is_tracked(path: str) -> bool:
    return os.path.normcase(os.path.abspath(path)) in tracked_files(os.path.dirname(os.path.abspath(path)))


def build_parser():
    p = argparse.ArgumentParser(
        prog='md-unwrap',
        description='Srotola i paragrafi hard-wrapped nei file Markdown, a diff minimo.',
    )
    p.add_argument('paths', nargs='*', default=['.'],
                   help='file, glob o cartelle da processare (default: cartella corrente)')
    p.add_argument('--check', action='store_true',
                   help='non scrive nulla ed esce 1 se qualche file cambierebbe')
    p.add_argument('--diff', action='store_true',
                   help='mostra il diff unificato invece di scrivere')
    p.add_argument('--exclude', action='append', default=[], metavar='GLOB',
                   help='pattern da escludere, ripetibile (si aggiunge ai default)')
    p.add_argument('--no-default-excludes', action='store_true',
                   help='non applicare la lista di esclusioni di default')
    p.add_argument('--ext', action='append', default=[], metavar='.EST',
                   help='estensione da processare, ripetibile (default: .md, .markdown)')
    p.add_argument('--only-tracked', action='store_true',
                   help='processa solo i file tracciati da git, cosi ogni scrittura '
                        'ha una rete di recupero; salta gli altri dichiarandoli')
    p.add_argument('--oracle', choices=('auto', 'require', 'off'), default='auto',
                   help='oracolo di rendering: auto (se disponibile), require, off')
    p.add_argument('-v', '--verbose', action='store_true', help='una riga per file')
    p.add_argument('-q', '--quiet', action='store_true', help='solo errori e riepilogo')
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    exts = tuple(e.lower() if e.startswith('.') else '.' + e.lower()
                 for e in (args.ext or list(DEFAULT_EXTS)))
    excludes = list(args.exclude)
    if not args.no_default_excludes:
        excludes += list(DEFAULT_EXCLUDES)

    if args.oracle == 'require' and get_oracle() is None:
        print('ERRORE  --oracle require: markdown-it-py non e installato '
              '(pip install markdown-it-py)')
        return 2

    files, marked = collect_files(args.paths or ['.'], exts, excludes, args.only_tracked)
    examined = changed = errors = total_joins = untracked = 0

    def say(line):
        """Stampa subito: su un corpus grande una corsa silenziosa sembra bloccata."""
        print(line, flush=True)

    for entry in files:
        if isinstance(entry, tuple):
            errors += 1
            say('ERRORE  %s' % entry[1])
            continue
        path = entry
        rel = display_path(path)
        if args.only_tracked and not is_tracked(path):
            untracked += 1
            if args.verbose:
                say('salta   %s: non tracciato da git' % rel)
            continue
        try:
            before = read_text(path)
        except UnicodeDecodeError:
            errors += 1
            say('SALTATO %s: non e UTF-8 valido' % rel)
            continue
        except OSError as exc:
            errors += 1
            say('SALTATO %s: %s' % (rel, exc.strerror or exc))
            continue

        examined += 1
        after, joins = unwrap(before)
        if after == before:
            if args.verbose:
                say('ok      %s' % rel)
            continue

        reason = verify(before, after, args.oracle)
        if reason:
            # Ripiego prudente: si rifa' la passata senza unire i blocchi
            # attraversati da un code span inline, che e' l'unico costrutto in
            # grado di cambiare il reso pur restando dentro un solo paragrafo.
            after, joins = unwrap(before, guard_spans=True)
            if after == before:
                # Non e' un errore: il file e' gia' nella forma migliore ottenibile
                # senza cambiare il reso, e non c'e' altro da unire in sicurezza.
                if not args.quiet:
                    say('intatto %s: nulla da unire senza cambiare il rendering' % rel)
                continue
            reason = verify(before, after, args.oracle)
        if reason:
            errors += 1
            say('SALTATO %s: %s' % (rel, reason))
            continue

        again, _ = unwrap(after)
        if again != after:
            errors += 1
            say('SALTATO %s: la trasformazione non e idempotente' % rel)
            continue

        changed += 1
        total_joins += joins
        if args.diff:
            diff = difflib.unified_diff(
                before.splitlines(keepends=True), after.splitlines(keepends=True),
                fromfile=rel + ' (originale)', tofile=rel + ' (srotolato)',
            )
            sys.stdout.writelines(diff)
        elif not args.check:
            try:
                write_text(path, after)
            except OSError as exc:
                errors += 1
                changed -= 1
                total_joins -= joins
                say('SALTATO %s: %s' % (rel, exc.strerror or exc))
                continue
        if not args.quiet:
            verb = 'cambierebbe' if (args.check or args.diff) else 'scritto'
            say('%-11s %s (%d righe unite)' % (verb, rel, joins))

    if not args.quiet:
        oracle_note = 'oracolo di rendering attivo' if get_oracle() else \
            'oracolo di rendering non disponibile (markdown-it-py assente): solo invariante interna'
        if args.oracle == 'off':
            oracle_note = 'oracolo di rendering disattivato'
        marked_note = ', %d ignorati per marcatore %s' % (marked, IGNORE_MARKER) if marked else ''
        if untracked:
            marked_note += ', %d non tracciati da git' % untracked
        print('%d file esaminati, %d %s, %d righe unite, %d saltati%s; %s' % (
            examined, changed,
            'da modificare' if (args.check or args.diff) else 'modificati',
            total_joins, errors, marked_note, oracle_note))

    if errors:
        return 2
    if args.check and changed:
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
