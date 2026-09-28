# -*- coding: utf-8 -*-
"""Segnala il lavoro che e' atterrato nel repository senza lasciare traccia nella memoria di progetto.

## Perche' esiste

La direttiva 13 dice che si documenta mentre si fa, non dopo, e senza che nessuno lo chieda. E'
scritta dal 2026-09-14 ed e' stata dovuta ripetere piu' volte, il che e' il sintomo preciso di una
regola senza presidio: **una direttiva che dipende dalla memoria di chi esegue non e' un presidio,
e' una speranza.** E' la stessa conclusione gia' tratta due volte su questo progetto, sulla guardia
di `fix-accents.py` e sulla verifica di non vacuita' delle prove.

Questo strumento non scrive niente al posto di nessuno. Fa l'unica cosa che un controllo puo' fare:
**rende visibile il divario nel momento in cui si apre**, invece di lasciarlo scoprire fra sei mesi
a chi cerca il perche' di una cosa e non lo trova.

## Che cosa controlla

**Commit senza voce di work-log.** Ogni commit ha una data; il work-log ha voci datate. Se esistono
commit piu' recenti dell'ultima voce, quel lavoro non e' tracciato. La severita' dipende da cosa
quei commit hanno toccato: codice sorgente senza una voce e' un difetto, documentazione senza una
voce e' un avviso, perche' spesso la documentazione **e'** la voce.

**Pendenti chiusi senza data.** Una voce del registro marcata come fatta deve dire quando. Una
chiusura senza data e' una fotografia senza scatto: non si puo' ne' verificare ne' collocare.

**Voci di work-log senza file toccati.** Una voce che non dichiara su che cosa ha agito costringe
chi legge a ricostruirlo dal diff, che e' precisamente il lavoro che la voce dovrebbe risparmiare.

## Che cosa NON controlla, e va detto

Non verifica che una voce sia **buona**, ne' che dica il perche' invece del solo cosa. Quella e' una
proprieta' di contenuto e nessun controllo meccanico la raggiunge. Lo strumento distingue il
silenzio dalla presenza, che e' meno di quanto servirebbe e molto piu' di niente.

## Uso

    python tools/lint-memoria.py

Esce con codice diverso da zero se trova qualcosa da sistemare.
"""

import io
import os
import re
import subprocess
import sys

WORKLOG = os.path.join(".claude", "memory", "progress.md")
REGISTRO = os.path.join(".claude", "context", "registro-dei-pendenti.md")

RE_VOCE = re.compile(r"^## (\d{4}-\d{2}-\d{2})", re.MULTILINE)
RE_CHIUSA = re.compile(r"\*\*(?:FATTO|FATTA|DECISA|RISOLTO|CHIUSA)\b[^*]*\*\*")
RE_DATA = re.compile(r"\d{4}-\d{2}-\d{2}")


def git(*args):
    return subprocess.check_output(["git"] + list(args), stderr=subprocess.DEVNULL).decode("utf-8", "replace")


def ultima_voce_worklog():
    testo = io.open(WORKLOG, encoding="utf-8").read()
    date = RE_VOCE.findall(testo)
    return (max(date) if date else None), testo


def commit_dopo(data):
    """(sha, data, soggetto, file toccati) dei commit piu' recenti della data data."""
    grezzo = git("log", "--since", data + " 00:00", "--pretty=format:%h|%ad|%s", "--date=short")
    fuori = []
    for riga in grezzo.strip().split("\n"):
        if not riga.strip():
            continue
        sha, data_c, soggetto = riga.split("|", 2)
        if data_c <= data:
            continue
        file = [f for f in git("show", "--name-only", "--pretty=format:", sha).split("\n") if f.strip()]
        fuori.append((sha, data_c, soggetto, file))
    return fuori


def main():
    problemi, avvisi = [], []

    data, testo_worklog = ultima_voce_worklog()
    if not data:
        print("nessuna voce datata nel work-log: non e' un divario, e' un'assenza")
        return 2

    # 1. Commit atterrati dopo l'ultima voce.
    for sha, data_c, soggetto, file in commit_dopo(data):
        codice = [f for f in file if f.startswith(("src/", "functions/"))]
        riga = "%s (%s) %s" % (sha, data_c, soggetto[:70])
        if codice:
            problemi.append("commit su CODICE senza voce di work-log: %s -> %s"
                            % (riga, ", ".join(codice[:3]) + ("..." if len(codice) > 3 else "")))
        else:
            avvisi.append("commit senza voce di work-log (solo documentazione): %s" % riga)

    # 2. Pendenti chiusi senza data.
    if os.path.exists(REGISTRO):
        for n, riga in enumerate(io.open(REGISTRO, encoding="utf-8").read().split("\n"), 1):
            if not riga.startswith("|"):
                continue
            for chiusura in RE_CHIUSA.findall(riga):
                if not RE_DATA.search(chiusura):
                    problemi.append("pendente chiuso senza data, riga %d: %s" % (n, chiusura[:60]))

    # 3. Voci di work-log senza file toccati.
    voci = re.split(r"(?=^## \d{4}-\d{2}-\d{2})", testo_worklog, flags=re.MULTILINE)
    for v in voci:
        m = RE_VOCE.match(v)
        if not m or m.group(1) < "2026-09-01":
            continue  # la regola si applica da quando e' stata adottata, non al passato
        if "File toccati" not in v:
            titolo = v.split("\n", 1)[0][:70]
            avvisi.append("voce senza l'elenco dei file toccati: %s" % titolo)

    for p in problemi:
        print("DIFETTO  %s" % p)
    for a in avvisi:
        print("avviso   %s" % a)
    if not problemi and not avvisi:
        print("memoria di progetto allineata: nessun lavoro senza traccia")
        return 0
    print()
    print("%d difetti, %d avvisi" % (len(problemi), len(avvisi)))
    return 1 if problemi else 0


if __name__ == "__main__":
    sys.exit(main())
