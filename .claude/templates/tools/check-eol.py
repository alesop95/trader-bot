#!/usr/bin/env python3
"""Segnala i file di testo con fini riga miste, cioe' CRLF e LF nello stesso file.

Perche' serve. La convenzione Markdown di questo progetto prescrive di conservare la
fine riga di ciascun file, CRLF o LF, e lo strumento md-unwrap la rispetta per
contratto. Ne segue che l'albero contiene legittimamente file con entrambe le
convenzioni, e che nessuno degli altri controlli si accorge se un file le mescola:
md-unwrap conserva e non pretende coerenza interna, il rendering a video e' identico,
e la catena tipografica guarda i caratteri e non le interruzioni.

Un file misto non e' un problema estetico. Con core.autocrlf a false e senza
.gitattributes, come in questo repository, git registra le fini riga cosi' come sono
sul disco: il file misto entra nella storia, e alla prima riscrittura da parte di
qualunque strumento le interruzioni si uniformano, trasformando una modifica di due
righe in una modifica dell'intero file. Il difetto e' stato introdotto per davvero il
2026-09-08 inserendo blocchi scritti con LF in due file CRLF, ed e' documentato in
MS-063 di docs/OPERATIONS-LOG.md.

Cosa NON fa. Non impone una convenzione e non converte niente: e' di sola lettura, e
la decisione su quale fine riga tenere resta di chi conosce il file. Le fixture di
prova di md-unwrap sono escluse perche' sono miste di proposito, dato che servono a
dimostrare che lo strumento le conserva.

Uso:
    python tools/check-eol.py              controlla la cartella corrente
    python tools/check-eol.py <percorso>   controlla un file o una cartella
    python tools/check-eol.py --dettaglio  elenca anche i file coerenti, con il formato

Esce con codice 1 se almeno un file risulta misto, 0 altrimenti.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Estensioni di testo su cui la fine riga conta. I binari non entrano.
ESTENSIONI = {".md", ".py", ".sh", ".ps1", ".json", ".txt", ".toml", ".yml", ".yaml", ".cfg"}

# Cartelle da non percorrere: metadati di git, materiale locale non versionato,
# e le fixture di md-unwrap, che sono miste di proposito.
CARTELLE_ESCLUSE = {".git", "_notes", "__pycache__", "node_modules", "fixtures", ".venv", "venv"}


def conta(percorso: Path) -> tuple[int, int]:
    """Numero di interruzioni CRLF e LF isolate in un file."""
    dati = percorso.read_bytes()
    crlf = dati.count(b"\r\n")
    lf = dati.count(b"\n") - crlf
    return crlf, lf


# Caratteri di controllo che in un file di testo non ci devono stare: tutti i C0 tranne
# tabulazione, ritorno a capo e avanzamento riga, il DEL, e i C1 nella forma in cui li
# scrive UTF-8. Nascono da una scrittura per script in cui una barra rovesciata e' stata
# letta come sequenza di escape: lo strumento non segnala niente, il diff mostra una riga
# cambiata come le altre, e il difetto resta finche' qualcuno non legge quei byte.
# Lezione L-007 di un progetto istanziato, 2026-11-09, tre volte su tre file in una sessione.
CONTROLLO = set(range(0, 32)) - {9, 10, 13} | {127}


def controlli(percorso: Path) -> list:
    """Posizioni dei caratteri di controllo trovati, con il loro codice."""
    # Non si passa da splitlines(): quella spezza anche su tabulazione verticale,
    # avanzamento modulo e separatori Unicode, cioe' proprio su alcuni dei caratteri
    # da trovare, che sparirebbero dal conteggio diventando interruzioni di riga.
    testo = percorso.read_text(encoding="utf-8", errors="replace")
    trovati = []
    riga = 1
    for c in testo:
        if c == "\n":
            riga += 1
            continue
        codice = ord(c)
        if codice in CONTROLLO or 0x80 <= codice <= 0x9F:
            trovati.append((riga, codice))
    return trovati


def candidati(radice: Path):
    if radice.is_file():
        yield radice
        return
    # Una cartella che porta il marcatore .md-unwrap-ignore contiene materiale esterno o
    # generato, copiato tale e quale: md-unwrap non la riformatta, e per la stessa ragione
    # non se ne pretende la coerenza delle fini riga, che appartiene alla fonte.
    marcate = {m.parent for m in radice.rglob(".md-unwrap-ignore")}
    for p in sorted(radice.rglob("*")):
        # Prima i filtri sul nome, che non toccano il disco: una cartella esclusa puo'
        # contenere voci che il sistema rifiuta di leggere, come i collegamenti di un
        # pacchetto per macOS estratto su Windows, e interrogarle farebbe cadere il controllo.
        if p.suffix not in ESTENSIONI or CARTELLE_ESCLUSE & set(p.parts):
            continue
        try:
            if not p.is_file():
                continue
        except OSError:
            continue
        if any(m == p.parent or m in p.parents for m in marcate):
            continue
        yield p


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("percorso", nargs="?", default=".", help="file o cartella da controllare")
    ap.add_argument("--dettaglio", action="store_true", help="elenca anche i file coerenti")
    args = ap.parse_args()

    radice = Path(args.percorso)
    if not radice.exists():
        print(f"percorso inesistente: {radice}", file=sys.stderr)
        return 2

    misti: list[tuple[Path, int, int]] = []
    sporchi: list[tuple[Path, int, int]] = []
    esaminati = 0
    formati = {"CRLF": 0, "LF": 0, "senza interruzioni": 0}

    for p in candidati(radice):
        esaminati += 1
        try:
            crlf, lf = conta(p)
        except OSError as e:
            print(f"  illeggibile {p}: {e}")
            continue
        try:
            for riga, codice in controlli(p):
                sporchi.append((p, riga, codice))
        except OSError:
            pass
        if crlf and lf:
            misti.append((p, crlf, lf))
        elif crlf:
            formati["CRLF"] += 1
            if args.dettaglio:
                print(f"  CRLF {p}")
        elif lf:
            formati["LF"] += 1
            if args.dettaglio:
                print(f"  LF   {p}")
        else:
            formati["senza interruzioni"] += 1

    for p, crlf, lf in misti:
        prevalente, minoritario = ("CRLF", "LF") if crlf > lf else ("LF", "CRLF")
        print(f"  MISTO {p}: {crlf} CRLF e {lf} LF, prevalente {prevalente}")
        print(f"        va normalizzato a {prevalente}, che e' la fine riga originale del file")

    print(
        f"{esaminati} file esaminati, {len(misti)} misti, "
        f"{formati['CRLF']} CRLF, {formati['LF']} LF, "
        f"{formati['senza interruzioni']} senza interruzioni"
    )
    for percorso, riga, codice in sporchi:
        print(f"  CONTROLLO {percorso}:{riga}: carattere U+{codice:04X} in un file di testo")
        print("        nasce da una barra rovesciata letta come escape in una scrittura per script;")
        print("        nei testi scritti da script i percorsi si scrivono con le barre in avanti")
    if misti:
        print("Le fini riga miste entrano nella storia di git: core.autocrlf e' false e")
        print("non esiste .gitattributes, quindi git registra cio' che trova sul disco.")
    return 1 if misti or sporchi else 0


if __name__ == "__main__":
    sys.exit(main())
