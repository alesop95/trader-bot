# -*- coding: utf-8 -*-
"""
Misura lo stato delle schede di `.claude/context/` rispetto al codice che dichiarano di coprire.

## Perché esiste

La skill `sync-context` confronta il `last-verified-commit` di ogni scheda con i file elencati nei
suoi `covers-paths`, e segnala la scheda come superata se uno di quei file è cambiato dopo. È un
buon confronto, ma ha cecità che lo fanno rispondere "aggiornata" proprio quando non lo è. In un
progetto istanziato, il 2026-10-05, ne sono state misurate tre:

- **Un percorso coperto che non esiste.** `git diff` su un file inesistente non restituisce niente,
  quindi la scheda risulta aggiornata per costruzione: un sensore staccato che segna verde. Erano
  quattro, su file rimossi o scritti sbagliati fin dalla prima stesura.
- **Una scheda con `covers-paths` ma senza ancora.** Il confronto non ha da dove partire, quindi la
  scheda non viene guardata affatto. Erano tre, scritte a giugno e mai più confrontate.
- **Un'ancora segnaposto o inesistente.** Due schede portavano ancora `PENDING-FIRST-COMMIT`, il
  valore delle schede nate prima del primo commit, tre mesi dopo il primo commit.

Questo strumento fa fallire rumorosamente quelle tre condizioni, invece di lasciarle passare come
aree senza cambiamenti. Non vede la quarta cecità dichiarata nella skill, cioè una scheda ancorata
quando già divergeva dal codice: quella la trova soltanto un confronto per contenuto, e nessuno
strumento lo sostituisce.

## Che cosa riporta

Tre categorie di **difetti**, che fanno uscire con codice 1: ancora mancante, ancora che non è un
commit del repository, percorso coperto che non corrisponde a nessun file. Poi l'elenco delle schede
**superate**, cioè con file coperti cambiati dopo l'ancora: è informazione, perché una scheda
superata subito dopo una modifica al codice è il caso normale, e la procedura per trattarla è
`sync-context`. Con `--rigoroso` anche le schede superate fanno uscire con codice 1, che è la forma
da usare quando si dichiara di aver allineato tutto.

## Uso

    python tools/verifica-schede.py
    python tools/verifica-schede.py --rigoroso
    python tools/verifica-schede.py --self-test
"""
import glob
import io
import os
import re
import subprocess
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def leggi_frontmatter(testo):
    """Ritorna (covers_paths, ancora) dal frontmatter, oppure None se il file non ne ha uno."""
    testo = testo.lstrip("﻿")
    if not testo.startswith("---"):
        return None
    parti = testo.split("---", 2)
    if len(parti) < 3:
        return None
    fm = parti[1]
    ancora = re.search(r"^last-verified-commit:\s*(\S+)", fm, re.MULTILINE)
    percorsi = None
    in_linea = re.search(r"^covers-paths:\s*\[(.*?)\]", fm, re.MULTILINE | re.DOTALL)
    if in_linea:
        percorsi = [p.strip().strip("\"'") for p in in_linea.group(1).split(",") if p.strip()]
    else:
        blocco = re.search(r"^covers-paths:\s*\n((?:[ \t]+-[^\n]*\n?)+)", fm, re.MULTILINE)
        if blocco:
            percorsi = [r.strip()[1:].strip().strip("\"'") for r in blocco.group(1).splitlines() if r.strip()]
        elif re.search(r"^covers-paths:", fm, re.MULTILINE):
            percorsi = []
    return percorsi, (ancora.group(1) if ancora else None)


def classifica(nome, percorsi, ancora, esiste, commit_valido, cambiati):
    """
    Classifica una scheda. `esiste`, `commit_valido` e `cambiati` sono funzioni passate dal
    chiamante, così che la logica si possa provare senza un repository.
    Ritorna (difetti, superati): una lista di stringhe e una lista di file cambiati.
    """
    difetti = []
    if percorsi is None:
        return difetti, []
    if not percorsi:
        return difetti, []
    if ancora is None:
        difetti.append(f"{nome}: ha `covers-paths` ma nessun `last-verified-commit`, quindi nessun confronto la guarda")
        return difetti, []
    if not commit_valido(ancora):
        difetti.append(f"{nome}: l'ancora `{ancora}` non è un commit di questo repository")
        return difetti, []
    if ancora == SEGNAPOSTO:
        return difetti, []
    for p in percorsi:
        if not esiste(p):
            difetti.append(f"{nome}: il percorso coperto `{p}` non corrisponde a nessun file")
    return difetti, cambiati(ancora, [p for p in percorsi if esiste(p)])


def esiste_su_disco(percorso):
    return bool(glob.glob(percorso, recursive=True)) or os.path.exists(percorso)


SEGNAPOSTO = "PENDING-FIRST-COMMIT"


def repository_senza_commit():
    return subprocess.run(["git", "rev-parse", "--verify", "HEAD"], capture_output=True).returncode != 0


def ancora_valida(ancora, senza_commit):
    """Il segnaposto è legittimo solo finché il repository non ha commit: dopo è un'ancora dimenticata."""
    if ancora == SEGNAPOSTO:
        return senza_commit
    r = subprocess.run(["git", "cat-file", "-e", f"{ancora}^{{commit}}"], capture_output=True)
    return r.returncode == 0


def commit_del_repository(ancora):
    return ancora_valida(ancora, repository_senza_commit())


def file_cambiati(ancora, percorsi):
    if not percorsi:
        return []
    r = subprocess.run(["git", "diff", "--name-only", f"{ancora}..HEAD", "--"] + percorsi,
                       capture_output=True, text=True)
    return [riga for riga in r.stdout.splitlines() if riga.strip()]


def self_test():
    casi = []

    def prova(nome, ok, dettaglio=""):
        casi.append((nome, bool(ok), dettaglio))

    fm = leggi_frontmatter('---\ncovers-paths: ["a.ts", "b.ts"]\nlast-verified-commit: abc\n---\n')
    prova("legge una lista in linea e l'ancora", fm == (["a.ts", "b.ts"], "abc"), str(fm))
    fm = leggi_frontmatter("---\ncovers-paths:\n  - a.ts\n  - b.ts\nlast-verified-commit: abc\n---\n")
    prova("legge una lista a righe", fm == (["a.ts", "b.ts"], "abc"), str(fm))
    fm = leggi_frontmatter("---\ncovers-paths: []\n---\n")
    prova("una lista vuota non è assenza di lista", fm == ([], None), str(fm))
    prova("un file senza frontmatter non è una scheda", leggi_frontmatter("# titolo\n") is None)

    tutto = lambda p: True
    niente_cambiato = lambda a, ps: []
    valido = lambda a: a == "abc"
    d, s = classifica("x", ["a.ts"], None, tutto, valido, niente_cambiato)
    prova("percorsi senza ancora sono un difetto", len(d) == 1 and "nessun" in d[0], str(d))
    d, s = classifica("x", ["a.ts"], "PENDING-FIRST-COMMIT", tutto, valido, niente_cambiato)
    prova("un'ancora segnaposto è un difetto", len(d) == 1 and "non è un commit" in d[0], str(d))
    d, s = classifica("x", ["a.ts", "sparito.ts"], "abc", lambda p: p != "sparito.ts", valido, niente_cambiato)
    prova("un percorso inesistente è un difetto, non un'area ferma", len(d) == 1 and "sparito.ts" in d[0], str(d))
    d, s = classifica("x", ["a.ts"], "abc", tutto, valido, lambda a, ps: ["a.ts"])
    prova("un file cambiato rende la scheda superata, non difettosa", d == [] and s == ["a.ts"], str((d, s)))
    prova("il segnaposto è valido in un repository senza commit", ancora_valida(SEGNAPOSTO, True))
    prova("il segnaposto è un difetto in un repository con commit", not ancora_valida(SEGNAPOSTO, False))
    d, s = classifica("x", [], None, tutto, valido, niente_cambiato)
    prova("covers-paths vuoto: non applicabile, nessun difetto", d == [] and s == [], str((d, s)))
    chiamati = []
    classifica("x", ["a.ts", "sparito.ts"], "abc", lambda p: p != "sparito.ts", valido,
               lambda a, ps: chiamati.append(ps) or [])
    prova("il confronto riceve solo i percorsi esistenti", chiamati == [["a.ts"]], str(chiamati))

    falliti = sum(0 if ok else 1 for _, ok, _ in casi)
    for nome, ok, dettaglio in casi:
        print(f"  {nome.ljust(62)}  {'ok' if ok else 'FALLITO'}{('  ' + dettaglio[:120]) if not ok else ''}")
    print(f"\n{len(casi)} prove, {falliti} fallite.")
    return 1 if falliti else 0


def main():
    if "--self-test" in sys.argv[1:]:
        return self_test()
    rigoroso = "--rigoroso" in sys.argv[1:]
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    difetti, superate = [], []
    con_frontmatter = non_applicabili = 0
    for f in sorted(glob.glob(".claude/context/**/*.md", recursive=True)):
        fm = leggi_frontmatter(io.open(f, encoding="utf-8", errors="replace").read())
        if fm is None or fm[0] is None:
            continue
        con_frontmatter += 1
        percorsi, ancora = fm
        if not percorsi:
            non_applicabili += 1
            continue
        nome = os.path.relpath(f, ".claude/context").replace("\\", "/")
        d, cambiati = classifica(nome, percorsi, ancora, esiste_su_disco, commit_del_repository, file_cambiati)
        difetti += d
        if cambiati:
            superate.append((nome, ancora, cambiati))
    print(f"schede con covers-paths: {con_frontmatter}, di cui non applicabili (lista vuota): {non_applicabili}")
    print(f"superate rispetto all'ancora: {len(superate)}")
    for nome, ancora, cambiati in superate:
        print(f"  {nome} ({ancora[:9]}): {', '.join(cambiati[:6])}{' ...' if len(cambiati) > 6 else ''}")
    print(f"difetti: {len(difetti)}")
    for d in difetti:
        print(f"  {d}")
    if difetti or (rigoroso and superate):
        return 1
    print("nessun difetto" + ("" if superate else ", nessuna scheda superata"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
