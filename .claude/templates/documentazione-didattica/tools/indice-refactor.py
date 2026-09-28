# -*- coding: utf-8 -*-
"""Genera l'indice delle schede didattiche numerate.

## Perché esiste

Un progetto che documenta le proprie scelte accumula schede: qui si chiamano `refactor-NN`, e sono
sessantuno. Finché sono poche, l'indice narrativo basta: il racconto evolutivo le collega una per
una, e chi cerca "la scheda su X" la trova leggendo. A sessanta funziona ancora a fatica, a cento
no, perché **un indice narrativo si consulta leggendolo tutto**, che è il contrario di ciò che
si chiede a un indice.

## Perché generato e non scritto a mano

È la parte che conta e che vale oltre questo strumento. Un indice compilato a mano è una **copia**
dei titoli, quindi una seconda fonte di verità: diverge al primo rinominamento di una scheda, e
nessuno se ne accorge, perché nessuna prova guarda un indice. Generarlo dai file rende la
divergenza impossibile per costruzione invece che improbabile per disciplina.

È lo stesso principio della matrice di tracciabilità e per la stessa ragione: **ciò che si può
derivare non si scrive**. Il corollario operativo è che questo file di uscita non si modifica mai a
mano, perché la modifica sparisce alla prossima esecuzione.

## Che cosa espone, oltre ai titoli

La colonna dei percorsi coperti, letta dal front matter `covers-paths`. Una colonna vuota **non è
un buco dell'indice ma una sua uscita**: dice che quella scheda non è agganciata a nessun file del
codice, quindi che nessuno potrà mai sapere meccanicamente se è diventata falsa quando quel file
cambia. Nascondere quella colonna avrebbe reso l'indice più pulito e il progetto più cieco.

## Uso

    python tools/indice-refactor.py
    python tools/indice-refactor.py --cartella docs/studi --prefisso studio- --uscita docs/studi/INDICE.md

I valori predefiniti sono le convenzioni di questo progetto. I parametri esistono perché lo
strumento vive anche come pacchetto del template, dove le convenzioni sono altre.
"""

import argparse
import io
import os
import re
import sys

# Titolo di primo livello, ovunque si trovi: alcune schede hanno il front matter YAML e altre no,
# quindi si cerca il titolo invece di presumere una riga fissa.
RE_TITOLO = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
RE_COVERS = re.compile(r"^covers-paths:\s*(.+?)\s*$", re.MULTILINE)
# "Refactor 49 - Un default può..." -> si tiene la parte dopo il trattino, perché il numero sta
# già nella sua colonna e ripeterlo nella descrizione ruba larghezza senza aggiungere nulla. Due
# forme convivono in questo progetto, "Studio refactor NN -" nelle prime schede e "Refactor NN -"
# nelle successive: si accettano entrambe invece di rinominare sessanta titoli per compiacere un
# generatore, che sarebbe il verso sbagliato della dipendenza.
RE_PREFISSO_TITOLO = re.compile(r"^(?:Studio\s+)?[A-Za-z]+\s+\d+\s*[-:]\s*")


def schede(cartella, prefisso, uscita):
    """Le schede della cartella, in ordine numerico, escludendo il file generato."""
    re_numero = re.compile(r"^%s(\d+)-" % re.escape(prefisso))
    nome_uscita = os.path.basename(uscita)
    for nome in sorted(os.listdir(cartella)):
        if not nome.endswith(".md") or nome == nome_uscita:
            continue
        m = re_numero.match(nome)
        if m:
            yield int(m.group(1)), nome


def percorsi_coperti(testo):
    """I percorsi dichiarati nel front matter, o stringa vuota se la scheda non li dichiara.

    Non si inventa il contenuto mancante: dedurre i percorsi dal testo produrrebbe percorsi
    plausibili e non percorsi veri, che è il tipo di errore peggiore perché sembra un dato.
    """
    m = RE_COVERS.search(testo)
    if not m:
        return ""
    grezzo = m.group(1).strip()
    voci = re.findall(r'"([^"]+)"|\'([^\']+)\'', grezzo)
    percorsi = [a or b for a, b in voci]
    if not percorsi:
        percorsi = [p.strip() for p in grezzo.strip("[]").split(",") if p.strip()]
    return ", ".join("`%s`" % p for p in percorsi)


def componi(righe, racconto):
    fuori = io.StringIO()
    fuori.write("# Indice delle schede didattiche\n\n")
    fuori.write("> **File generato da `tools/indice-refactor.py`. Non si modifica a mano**: "
                "una modifica manuale sparisce alla prossima esecuzione, e un indice scritto a mano "
                "è una seconda fonte di verità che diverge dai titoli al primo rinominamento senza "
                "che nessuno se ne accorga, perché nessuna prova guarda un indice.\n\n")
    fuori.write("Questo indice risponde alla domanda **\"dov'e' la scheda su X\"**. La domanda "
                "diversa, **\"come si è evoluto il progetto\"**, ha un altro proprietario ed è il "
                "racconto in `%s`, che collega le stesse schede in ordine narrativo invece che per "
                "argomento. Nessuno dei due sostituisce l'altro: un indice non racconta niente, e un "
                "racconto non si consulta.\n\n" % racconto)
    fuori.write("Schede presenti: **%d**.\n\n" % len(righe))
    fuori.write("| N | Argomento | Scheda | Percorsi coperti |\n")
    fuori.write("|---|---|---|---|\n")
    for numero, titolo, nome, percorsi in righe:
        fuori.write("| %d | %s | [%s](%s) | %s |\n" % (numero, titolo, nome, nome, percorsi or "-"))

    senza = [n for n, _, _, p in righe if not p]
    if senza:
        fuori.write("\n**Schede senza `covers-paths` dichiarati: %d** (numeri %s). "
                    "La colonna vuota non è un difetto dell'indice ma una sua uscita: dice quali "
                    "schede non sono agganciate a nessun file, quindi quali non verranno mai "
                    "segnalate come da riverificare quando quel file cambia.\n"
                    % (len(senza), ", ".join(str(n) for n in senza)))
    return fuori.getvalue(), senza


def main(argv=None):
    ap = argparse.ArgumentParser(description="Genera l'indice delle schede didattiche numerate.")
    ap.add_argument("--cartella", default=os.path.join(".claude", "context"),
                    help="cartella che contiene le schede")
    ap.add_argument("--prefisso", default="refactor-",
                    help="prefisso dei nomi file, seguito dal numero e da un trattino")
    ap.add_argument("--uscita", default=None,
                    help="file da scrivere (predefinito: <cartella>/refactor-indice.md)")
    ap.add_argument("--racconto", default="studio-didattico-master.md",
                    help="nome del racconto narrativo, citato nell'intestazione")
    args = ap.parse_args(argv)

    uscita = args.uscita or os.path.join(args.cartella, "%sindice.md" % args.prefisso)

    if not os.path.isdir(args.cartella):
        print("cartella non trovata: %s" % args.cartella)
        return 1

    righe = []
    for numero, nome in schede(args.cartella, args.prefisso, uscita):
        testo = io.open(os.path.join(args.cartella, nome), encoding="utf-8").read()
        m = RE_TITOLO.search(testo)
        titolo = RE_PREFISSO_TITOLO.sub("", m.group(1).strip()) if m else "[senza titolo]"
        righe.append((numero, titolo, nome, percorsi_coperti(testo)))

    if not righe:
        print("nessuna scheda trovata in %s con prefisso '%s'" % (args.cartella, args.prefisso))
        return 1

    testo, senza = componi(righe, args.racconto)
    io.open(uscita, "w", encoding="utf-8", newline="").write(testo)
    print("scritto %s" % uscita)
    print("  %d schede, %d senza percorsi dichiarati" % (len(righe), len(senza)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
