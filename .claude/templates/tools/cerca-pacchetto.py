#!/usr/bin/env python3
"""Cerca nel catalogo dei pacchetti quelli che rispondono al lavoro in corso.

Perché esiste. Il catalogo `.claude/templates/PACKAGES.md` arriva in ogni
progetto istanziato con l'allineamento, ma il gate che lo attraversa, la skill
`gate-pacchetti`, si esegue solo all'inizializzazione e a ogni tornata di
allineamento, e non è invocabile dall'agente in sessione. Misurato il 2026-10-19
su un progetto istanziato: nessun punto letto in sessione nominava il catalogo, e
in una giornata l'agente ha ricostruito a mano una mappa che un pacchetto già
conteneva. Questo strumento è il ponte: quando il lavoro si presenta, si
interroga il catalogo con le parole del lavoro e si ottengono le poche voci
pertinenti, invece di caricare in ogni sessione un catalogo di oltre centomila
caratteri o un elenco di nomi che non dice quando servono.

La ricerca è deterministica e non giudica: confronta le parole della domanda con
la colonna "Quando offrirlo", che è l'innesco di ogni voce, con il nome e con
"Cosa fa", e ordina per punteggio. Dire se il pacchetto serva davvero resta
compito di chi legge la voce intera, e proporlo all'utente segue le tre frasi
del gate: che cosa fa, perché qui, che cosa costa.

Uso:
    python .claude/templates/tools/cerca-pacchetto.py applicazioni grafica pdf impaginazione
    python .claude/templates/tools/cerca-pacchetto.py --progetto . lint tipi dipendenze
    python .claude/templates/tools/cerca-pacchetto.py --elenco
    python .claude/templates/tools/cerca-pacchetto.py --autotest

Con --progetto segna le voci che il progetto ha già istanziato, riconoscendole
dalla skill omonima sotto .claude/skills/ o da uno strumento del pacchetto
presente sotto tools/; un pacchetto che istanzia solo schede o regole non si
riconosce così, e per questo l'assenza si dichiara "non rilevato". Esce con 0 se trova almeno una voce, con 1 se non ne
trova nessuna, con 2 per un errore.
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path

RIGA = re.compile(r"^\| `([^`]+)`(?: \(([^)]+)\))? \|")
SEPARATORE = re.compile(r"(?<!\\)\|")
PAROLE_VUOTE = {
    "il", "lo", "la", "i", "gli", "le", "un", "uno", "una", "di", "da", "in", "con", "su",
    "per", "tra", "fra", "e", "o", "che", "del", "della", "dei", "delle", "al", "alla",
    "non", "si", "come", "cosa", "the", "and", "for", "to", "of", "a",
}


@dataclass
class Voce:
    nome: str
    tipo: str
    settore: str
    cosa_fa: str
    quando: str
    riga: int


def normalizza(testo: str) -> str:
    t = unicodedata.normalize("NFKD", testo.casefold())
    return "".join(c for c in t if not unicodedata.combining(c))


def radici(testo: str) -> list[str]:
    """Parole di almeno tre lettere, ridotte alle prime sei: basta a far combaciare
    plurali e coniugazioni italiane senza uno stemmer."""
    parole = re.findall(r"[a-z0-9]+", normalizza(testo))
    return [p[:6] for p in parole if len(p) >= 3 and p not in PAROLE_VUOTE]


def leggi_catalogo(percorso: Path) -> list[Voce]:
    voci: list[Voce] = []
    settore = ""
    testo = percorso.read_text(encoding="utf-8")
    for n, riga in enumerate(testo.splitlines(), start=1):
        if riga.startswith("### "):
            settore = riga[4:].strip()
            continue
        m = RIGA.match(riga)
        if not m:
            continue
        celle = [c.strip() for c in SEPARATORE.split(riga)[1:-1]]
        if len(celle) < 5:
            continue
        voci.append(Voce(m.group(1), m.group(2) or "", settore, celle[1], celle[2], n))
    return voci


def punteggio(voce: Voce, domanda: list[str]) -> int:
    nome = set(radici(voce.nome.replace("-", " ")))
    quando = set(radici(voce.quando))
    fa = set(radici(voce.cosa_fa))
    p = 0
    for d in set(domanda):
        if d in nome:
            p += 3
        if d in quando:
            p += 2
        elif d in fa:
            p += 1
    return p


def adottato(voce: Voce, progetto: Path, template_dir: Path) -> bool:
    if (progetto / ".claude" / "skills" / voce.nome).is_dir():
        return True
    strumenti = template_dir / voce.nome / "tools"
    if strumenti.is_dir() and (progetto / "tools").is_dir():
        for f in strumenti.iterdir():
            if f.is_file() and (progetto / "tools" / f.name).is_file():
                return True
    return False


def tronca(testo: str, n: int) -> str:
    testo = re.sub(r"\s+", " ", testo).strip()
    return testo if len(testo) <= n else testo[: n - 1].rstrip() + "…"


def trova_catalogo(indicato: str | None) -> Path:
    if indicato:
        return Path(indicato)
    vicino = Path(__file__).resolve().parent.parent / "PACKAGES.md"
    if vicino.is_file():
        return vicino
    for base in [Path.cwd(), *Path.cwd().parents]:
        c = base / ".claude" / "templates" / "PACKAGES.md"
        if c.is_file():
            return c
    return vicino


def autotest() -> int:
    import tempfile
    catalogo = (
        "# Catalogo\n\n### Artefatti visivi\n\n"
        "| Pacchetto | Cosa fa | Quando offrirlo | Cosa istanzia | Note |\n"
        "|---|---|---|---|---|\n"
        "| `craft-apps` | Collega applicazioni desktop di grafica | Il progetto produce immagini, PDF o impaginati | skill e tools | alpha |\n"
        "| `serena` (MCP) | Grafo semantico del codice | Codebase grande da navigare per simboli | server | token |\n"
        "| `voce-con-barra` | Testo con \\| una barra protetta | Trascrizioni audio di riunioni | tools | - |\n"
    )
    casi = 0
    rossi = 0

    def caso(nome: str, ok: bool) -> None:
        nonlocal casi, rossi
        casi += 1
        if not ok:
            rossi += 1
        print(("ok   " if ok else "ROSSO ") + nome)

    with tempfile.TemporaryDirectory() as d:
        base = Path(d)
        f = base / "PACKAGES.md"
        f.write_text(catalogo, encoding="utf-8")
        voci = leggi_catalogo(f)
        caso("tre voci lette, anche quella col tipo e quella con la barra protetta", [v.nome for v in voci] == ["craft-apps", "serena", "voce-con-barra"])
        caso("il tipo fra parentesi si legge a parte", voci[1].tipo == "MCP")
        caso("il settore viene dal titolo che precede", voci[0].settore == "Artefatti visivi")
        caso("una barra protetta non spezza la cella", "barra protetta" in voci[2].cosa_fa)
        ordinate = sorted(voci, key=lambda v: -punteggio(v, radici("impaginazione di un PDF con immagini")))
        caso("le parole dell'innesco portano la voce giusta in testa", ordinate[0].nome == "craft-apps")
        caso("plurale e accenti combaciano", punteggio(voci[2], radici("trascrizione audio")) > 0)
        caso("una domanda estranea non trova niente", all(punteggio(v, radici("contabilità fiscale")) == 0 for v in voci))
        prj = base / "progetto"
        (prj / ".claude" / "skills" / "craft-apps").mkdir(parents=True)
        caso("una skill omonima segna il pacchetto come adottato", adottato(voci[0], prj, base) and not adottato(voci[1], prj, base))
    print(f"\n{casi - rossi} casi superati su {casi}")
    return 1 if rossi else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Cerca nel catalogo dei pacchetti le voci pertinenti al lavoro in corso.")
    ap.add_argument("parole", nargs="*", help="le parole del lavoro, come lo si descriverebbe")
    ap.add_argument("--catalogo", help="percorso di PACKAGES.md, per default quello accanto allo strumento")
    ap.add_argument("--progetto", help="radice del progetto, per segnare le voci già istanziate")
    ap.add_argument("--max", type=int, default=5, help="quante voci mostrare, 5 per default")
    ap.add_argument("--elenco", action="store_true", help="elenca tutte le voci per settore, una riga ciascuna")
    ap.add_argument("--autotest", action="store_true")
    a = ap.parse_args()
    if a.autotest:
        return autotest()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    catalogo = trova_catalogo(a.catalogo)
    if not catalogo.is_file():
        print(f"catalogo non trovato: {catalogo}", file=sys.stderr)
        return 2
    voci = leggi_catalogo(catalogo)
    progetto = Path(a.progetto).resolve() if a.progetto else None
    template_dir = catalogo.parent

    def segno(v: Voce) -> str:
        if not progetto:
            return ""
        # "non rilevato" e non "non adottato": la rilevazione vede skill e strumenti, non
        # le schede o le regole che alcuni pacchetti istanziano, quindi un'assenza qui non
        # e' una prova che il progetto non abbia il pacchetto.
        return "  [istanziato]" if adottato(v, progetto, template_dir) else "  [non rilevato]"

    if a.elenco:
        settore = None
        for v in voci:
            if v.settore != settore:
                settore = v.settore
                print(f"\n{settore}")
            print(f"  {v.nome}{' (' + v.tipo + ')' if v.tipo else ''}{segno(v)}")
        print(f"\n{len(voci)} voci in {catalogo}")
        return 0
    domanda = radici(" ".join(a.parole))
    if not domanda:
        ap.error("servono le parole del lavoro, oppure --elenco")
    trovate = sorted(((punteggio(v, domanda), v) for v in voci), key=lambda x: (-x[0], x[1].riga))
    trovate = [(p, v) for p, v in trovate if p > 0][: a.max]
    if not trovate:
        print(f"nessuna voce del catalogo risponde a: {' '.join(a.parole)}  ({len(voci)} voci in {catalogo})")
        return 1
    for p, v in trovate:
        print(f"{v.nome}{' (' + v.tipo + ')' if v.tipo else ''}  punteggio {p}  settore: {v.settore}{segno(v)}")
        print(f"  quando: {tronca(v.quando, 300)}")
        print(f"  voce intera: {catalogo}:{v.riga}")
    print(f"\n{len(trovate)} voci su {len(voci)}. Prima di proporne una si legge la voce intera, e si propone con le tre frasi del gate: che cosa fa, perché qui, che cosa costa.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
