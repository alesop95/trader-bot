#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verifica la struttura delle tabelle Markdown: celle su riga sola e colonne complete.

Perché esiste
-------------
La convenzione di scrittura del sistema vuole ogni paragrafo di prosa su una riga
sorgente unica, e lo strumento che la attua è `md-unwrap`. Quello strumento però ha per
contratto di non toccare le tabelle, che conserva riga per riga e senza riallineare, e la
ragione è giusta: in una tabella l'a capo è strutturale. Ne segue però un punto cieco, e
questo programma lo copre.

I due difetti che copre, entrambi osservati sul campo il 2026-09-01, hanno in comune di non
produrre alcun errore e di superare una revisione a video del sorgente.

Il primo è una riga vuota dentro una cella. Chi scrive una cella lunga è tentato di spezzarla
in paragrafi, e il risultato è che la tabella si chiude a quella riga vuota: il renderer
mette il resto della cella fuori dalla griglia, come prosa, e la tabella perde le righe
successive. Nel sorgente la cosa si vede solo se si guarda, e chi ha appena scritto la cella
sa cosa intendeva e non la guarda.

Il secondo è una riga con meno colonne dell'intestazione. Il renderer non protesta e lascia
le celle mancanti vuote, quindi un campo obbligatorio per convenzione, come la colonna che in
`SOURCES.md` dichiara quale sottoprogetto una fonte serve, può essere assente su una voce
senza che nessuno lo noti. Due voci di quel registro sono rimaste in quello stato per un
giorno.

Che cosa considera una tabella
------------------------------
Un blocco di righe consecutive che cominciano con una barra verticale, con almeno due righe.
La riga di separazione fatta di trattini è riconosciuta e non conteggiata. I blocchi di codice
recintati sono esclusi, perché al loro interno una barra verticale non è una tabella.

Il criterio con cui la cella spezzata si riconosce merita una nota, perché le prime due
versioni di questo programma lo avevano sbagliato nello stesso modo. Esse guardavano ciò che
segue la tabella e sospettavano una cella spezzata quando vi trovavano prosa: la prima
sospettava qualunque prosa, la seconda escludeva i titoli e gli elenchi. Entrambe erano
euristiche sul contenuto, e la prosa piana fra due tabelle è legittima, tanto che il catalogo
generato degli eventi di questo progetto la impiega per etichettare i propri blocchi e
produceva quattordici falsi positivi su sedici segnalazioni.

Il criterio giusto è strutturale e sta nella tabella e non fuori di essa: una riga di tabella
si chiude con la barra verticale, e una cella tagliata da una riga vuota lascia l'ultima riga
del blocco priva di quella barra, perché è stata interrotta a metà. Il criterio non ha falsi
positivi sulle tabelle di questo progetto, si applica anche quando dopo la tabella non segue
nulla, e non richiede di interpretare la prosa. Vale la generalizzazione: quando un controllo
richiede di indovinare l'intenzione di un testo, conviene cercare se lo stesso difetto lasci
una traccia nella forma, perché la forma si verifica e l'intenzione si congettura.

Uso
---
    python tools/lint-md-tables.py
    python tools/lint-md-tables.py SOURCES.md docs
    python tools/lint-md-tables.py --self-test
"""

import argparse
import io
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IGNORATE = (".git", "__pycache__", "node_modules", ".venv", "_notes")

SEPARATORE = re.compile(r"^\|?[\s:|-]+\|[\s:|-]*$")


def conta_colonne(riga):
    """Il numero di celle di una riga di tabella.

    Si toglie la barra iniziale e quella finale prima di dividere, perché sono delimitatori e
    non separatori: contarle come tali darebbe due celle vuote su ogni riga.

    Una barra preceduta da una barra rovesciata non separa alcuna cella: è il modo che il formato
    prevede per scrivere il carattere dentro una cella, e ignorarlo farebbe segnalare come difetto
    una riga corretta. Il caso non è teorico e nasce da una riga vera: le chiavi dei semi delle
    schede di quarta generazione usano la barra come separatore dei propri campi, e devono restare
    copiabili tali e quali perché è da esse che l'impronta del seme si ricalcola.
    """
    corpo = riga.strip()
    if corpo.startswith("|"):
        corpo = corpo[1:]
    if corpo.endswith("|"):
        corpo = corpo[:-1]
    return len(corpo.replace(chr(92) + "|", chr(1)).split("|"))


def analizza(testo):
    """Restituisce l'elenco dei difetti come terne (riga, tipo, dettaglio)."""
    difetti = []
    righe = testo.split("\n")
    dentro_recinto = False
    i = 0
    while i < len(righe):
        riga = righe[i]
        if riga.lstrip().startswith("```") or riga.lstrip().startswith("~~~"):
            dentro_recinto = not dentro_recinto
            i += 1
            continue
        if dentro_recinto or not riga.lstrip().startswith("|"):
            i += 1
            continue

        # Inizio di un blocco di tabella: si raccolgono le righe consecutive.
        blocco = []
        j = i
        while j < len(righe) and righe[j].lstrip().startswith("|"):
            blocco.append((j, righe[j]))
            j += 1
        if len(blocco) < 2:
            i = j
            continue

        attese = conta_colonne(blocco[0][1])
        for numero, riga_tab in blocco:
            if SEPARATORE.match(riga_tab.strip()):
                continue
            trovate = conta_colonne(riga_tab)
            if trovate != attese:
                difetti.append((numero + 1, "colonne",
                                "%d celle invece di %d" % (trovate, attese)))

        # Il segnale di una cella spezzata non sta in ciò che segue la tabella ma nella
        # tabella stessa. Una riga ben formata si chiude con la barra verticale; una cella
        # tagliata da una riga vuota lascia l'ultima riga del blocco senza quella barra,
        # perché è stata interrotta a metà. È un criterio strutturale e non una congettura
        # sul contenuto, e valeva la pena sostituirvi l'euristica precedente, che sospettava
        # ogni prosa fra due tabelle e sbagliava quattordici volte su sedici.
        for numero, riga_tab in blocco:
            corpo = riga_tab.rstrip()
            if SEPARATORE.match(corpo.strip()):
                continue
            if not corpo.endswith("|"):
                difetti.append((numero + 1, "riga non chiusa",
                                "la riga non termina con la barra verticale: se la cella "
                                "prosegue sotto, la tabella si chiude qui"))
        i = j
    return difetti


def bersagli(percorsi):
    fuori = []
    for p in percorsi or ["."]:
        assoluto = p if os.path.isabs(p) else os.path.join(RADICE, p)
        if os.path.isfile(assoluto):
            fuori.append(assoluto)
            continue
        for radice, cartelle, nomi in os.walk(assoluto):
            cartelle[:] = [c for c in cartelle if c not in IGNORATE]
            for nome in nomi:
                if nome.endswith(".md"):
                    fuori.append(os.path.join(radice, nome))
    return sorted(set(fuori))


def self_test():
    casi = [
        ("tabella sana",
         "| a | b |\n|---|---|\n| 1 | 2 |\n", 0),
        ("cella con una riga vuota dentro",
         "| a | b |\n|---|---|\n| 1 | 2\n\nsegue la cella\n\n| 3 | 4 |\n", 1),
        ("riga con una colonna in meno",
         "| a | b | c |\n|---|---|---|\n| 1 | 2 |\n", 1),
        ("riga con una colonna in piu",
         "| a | b |\n|---|---|\n| 1 | 2 | 3 |\n", 1),
        ("barra protetta dentro una cella, che non separa nulla",
         "| a | b |\n|---|---|\n| x\\|y | 2 |\n", 0),
        ("barra dentro un blocco recintato",
         "```\n| non | una | tabella\n```\n", 0),
        ("prosa dopo una tabella, senza ripresa",
         "| a | b |\n|---|---|\n| 1 | 2 |\n\nQuesta e prosa normale.\n", 0),
        ("due tabelle separate da un titolo",
         "| a | b |\n|---|---|\n| 1 | 2 |\n\n## Titolo\n\n| c | d |\n|---|---|\n| 3 | 4 |\n", 0),
        ("due tabelle separate da prosa piana, che è legittima",
         "| a | b |\n|---|---|\n| 1 | 2 |\n\nBlocco: Spanish\n\n| c | d |\n|---|---|\n| 3 | 4 |\n", 0),
        ("cella spezzata in coda al documento, senza nulla che segua",
         "| a | b |\n|---|---|\n| 1 | 2\n", 1),
        ("cella spezzata con prosa e ripresa della tabella",
         "| a | b |\n|---|---|\n| 1 | 2\n\ncoda della cella\n\n| 3 | 4 |\n", 1),
    ]
    fallite = 0
    for nome, testo, attesi in casi:
        trovati = len(analizza(testo))
        esito = trovati == attesi
        print(("  ok      " if esito else "  FALLITO ") + nome +
              " (attesi %d, trovati %d)" % (attesi, trovati))
        if not esito:
            fallite += 1
    print("")
    print("self-test: %d casi, %d falliti" % (len(casi), fallite))
    return 1 if fallite else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("percorsi", nargs="*", help="file o cartelle da esaminare")
    ap.add_argument("--self-test", action="store_true", dest="self_test")
    a = ap.parse_args()

    if a.self_test:
        return self_test()

    file = bersagli(a.percorsi)
    totale = 0
    for p in file:
        try:
            testo = io.open(p, encoding="utf-8").read()
        except (UnicodeDecodeError, OSError):
            continue
        for numero, tipo, dettaglio in analizza(testo):
            # Su Windows `relpath` solleva quando i due percorsi stanno su unita' diverse, e
            # non e' un caso di scuola: lo strumento puo' legittimamente essere puntato su una
            # copia in una cartella temporanea, che e' il modo naturale di provarlo senza
            # toccare l'originale. Fuori dalla radice si mostra il percorso assoluto.
            # Corretto il 2026-09-28, stesso difetto gia' chiuso in `fix-dashes.py`.
            try:
                rel = os.path.relpath(p, RADICE)
            except ValueError:
                rel = os.path.abspath(p)
            print("%s:%d %s: %s" % (rel, numero, tipo, dettaglio))
            totale += 1
    print("")
    print("%d file esaminati, %d difetti" % (len(file), totale))
    return 1 if totale else 0


if __name__ == "__main__":
    sys.exit(main())
