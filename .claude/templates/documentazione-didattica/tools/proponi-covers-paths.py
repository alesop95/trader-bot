# -*- coding: utf-8 -*-
"""Propone i `covers-paths` di una scheda didattica estraendoli dal testo, senza dedurli.

## Perche' esiste (pendente T-9)

Cinquantatre schede su sessantuno non dichiarano quali file del codice trattano, e quel campo e'
l'unico aggancio meccanico fra una spiegazione e il codice che spiega: senza, non si puo' chiedere
"quali schede parlano di un file appena cambiato", che e' l'unico modo di accorgersi che una
spiegazione e' diventata falsa.

## La distinzione che rende il lavoro lecito, ed e' tutto il punto

Il registro dei pendenti dichiara che questo lavoro **non e' automatizzabile**, perche' dedurre i
percorsi dal testo produrrebbe percorsi plausibili e non percorsi veri, che e' il tipo di errore
peggiore perche' sembra un dato.

Quella affermazione resta vera e questo strumento non la contraddice, perche' **non deduce niente**.
Estrae le stringhe che la scheda ha gia' scritto fra apici inversi, tiene solo quelle che
corrispondono a un file realmente presente sul disco, e le ordina per quante volte la scheda le
nomina. Un percorso che la scheda non nomina non compare mai nella proposta.

La differenza fra dedurre ed estrarre non e' un cavillo: **una deduzione puo' essere sbagliata in
modo invisibile, un'estrazione al massimo e' incompleta in modo visibile.** Le schede che parlano di
un file senza nominarlo restano scoperte, e lo strumento lo dichiara invece di indovinare.

## Che cosa resta al giudizio umano

Due cose, ed e' per questo che lo strumento **propone** invece di scrivere. La prima e' la potatura:
una scheda puo' nominare dieci file e trattarne tre, e distinguere l'argomento dal contorno richiede
di aver capito la scheda. La seconda sono i file citati e non piu' esistenti, che lo strumento
elenca a parte perche' sono un'informazione a se': dicono quali schede parlano di codice cancellato.

## Due difetti trovati usando le proposte, e corretti il 2026-09-21

Le proposte accettate su un corpus reale sono state rilette una per una mentre si completavano
quattro schede, e in **tutte e quattro** mancava il file centrale, cioe' proprio quello di cui la
scheda parlava. Le cause erano due, indipendenti, e nessuna delle due produceva un segnale.

La prima: si estraeva soltanto dagli apici inversi della prosa. Ma un documento didattico nomina il
proprio soggetto **nel commento di intestazione dell'estratto di codice**, cioe' dentro un blocco
recintato, dove non ci sono apici inversi. La prova che fosse quella la causa e' un confronto:
`firestore.rules`, citato in prosa da una scheda, era nel suo elenco; lo stesso file citato solo in
un commento da un'altra scheda non c'era. Ora si leggono anche le righe di commento dei blocchi, e
resta estrazione e non deduzione, perche' quel percorso la scheda lo ha scritto davvero.

La seconda: la proposta era troncata ai primi sei percorsi per numero di menzioni, e il troncamento
**contraddiceva il dosaggio dichiarato nel README** dello stesso pacchetto, secondo cui omettere e'
peggio che includere in piu'. Un file trattato a fondo ma nominato una volta sola cadeva sotto la
soglia mentre sei contorni nominati spesso restavano. Il tetto e' stato tolto: la potatura e' gia'
dichiarata come lavoro umano, e uno strumento che pota da se' toglie alla persona proprio la
decisione che gli si era voluta lasciare.

La lezione generale, che vale oltre questo strumento: la garanzia dichiarata qui era che
un'estrazione **tace dove non sa**, e in entrambi i casi non ha taciuto, ha risposto meno del vero.
Un campo popolato sembra completo, e un'incompletezza e' visibile **solo se qualcuno la guarda**:
una garanzia di questo tipo va quindi accompagnata da un confronto a campione fra cio' che lo
strumento propone e cio' che il documento tratta davvero, almeno la prima volta che lo si usa.

## Uso

    python tools/proponi-covers-paths.py > proposta.txt
    python tools/proponi-covers-paths.py --solo-mancanti

Non scrive mai dentro le schede.
"""

import argparse
import io
import os
import re
import sys

CARTELLA = os.path.join(".claude", "context")
PREFISSO = "refactor-"

# Una stringa fra apici inversi che assomiglia a un percorso del repository: comincia con una delle
# radici note e finisce con un'estensione di codice o configurazione. Volutamente stretta: un falso
# positivo qui diventerebbe un dato sbagliato in un campo che serve a dare fiducia.
RE_CODICE = re.compile(r"`([^`\n]+)`")
RADICI = ("src/", "functions/", "public/", "scripts/", "tools/", "email-templates/")
ESTENSIONI = (".ts", ".tsx", ".js", ".json", ".rules", ".py", ".mjml", ".css", ".html")
CONFIG_IN_RADICE = ("firestore.rules", "firebase.json", "package.json", "tsconfig.json")

# Dentro un blocco recintato non ci sono apici inversi, e il percorso del file compare nel commento
# di intestazione dell'estratto: e' li' che una scheda didattica nomina il proprio soggetto.
RE_FENCE = re.compile(r"^\s*(?:```|~~~)")
MARCATORI_COMMENTO = ("//", "#", "/*", "*", "<!--", "--")
RE_TOKEN = re.compile(r"[A-Za-z0-9_.\-/]+")


def ha_front_matter(testo):
    return testo.lstrip().startswith("---")


def indice_nomi():
    """Mappa da nome file a elenco dei percorsi che lo portano, dentro le radici note.

    Serve a risolvere i nomi nudi: molte schede scrivono `useFamilyData.ts` senza la cartella,
    perche' chi le ha scritte aveva il progetto in testa. Risolverli e' ancora estrazione, non
    deduzione, **a una condizione**: si accetta solo la corrispondenza unica. Se due file portano
    lo stesso nome la scheda non ha detto quale, e sceglierne uno sarebbe inventare.
    """
    mappa = {}
    for radice in RADICI:
        if not os.path.isdir(radice):
            continue
        for cartella, sottocartelle, file in os.walk(radice):
            sottocartelle[:] = [d for d in sottocartelle if d not in ("node_modules", "__pycache__")]
            for n in file:
                if n.endswith(ESTENSIONI):
                    mappa.setdefault(n, []).append(os.path.join(cartella, n).replace(os.sep, "/"))
    return mappa


NOMI = None


def token_nei_commenti_recintati(testo):
    """I token che somigliano a un percorso, presi dalle righe di commento dei blocchi recintati.

    Si guardano solo le righe che aprono con un marcatore di commento, e non l'intero blocco, per
    la stessa ragione per cui non si deduce: dentro il codice un percorso puo' comparire come
    argomento di una chiamata, e prenderlo significherebbe dichiarare che la scheda tratta un file
    che sta soltanto nominando di passaggio. Il commento di intestazione, invece, e' la dichiarazione
    esplicita di da dove viene l'estratto.
    """
    dentro = False
    for riga in testo.split("\n"):
        if RE_FENCE.match(riga):
            dentro = not dentro
            continue
        if not dentro:
            continue
        spogliata = riga.strip()
        if not spogliata.startswith(MARCATORI_COMMENTO):
            continue
        for token in RE_TOKEN.findall(spogliata):
            yield token


def candidati(testo):
    """I percorsi nominati dalla scheda, con quante volte ciascuno compare, e gli ambigui.

    Restituisce (conta, ambigui). Un nome nudo che corrisponde a piu' file finisce fra gli
    ambigui e non fra i candidati: la scheda non ha detto quale, e questo strumento non sceglie.
    """
    global NOMI
    if NOMI is None:
        NOMI = indice_nomi()

    conta, ambigui = {}, {}

    def classifica(s, permetti_nome_nudo):
        # Percorso completo, la forma migliore perche' non ha ambiguita'.
        if s.startswith(RADICI) and s.endswith(ESTENSIONI):
            conta[s] = conta.get(s, 0) + 1
            return

        # File di configurazione in radice, riconosciuti per nome esatto.
        if s in CONFIG_IN_RADICE:
            conta[s] = conta.get(s, 0) + 1
            return

        # Nome nudo: si risolve solo se la corrispondenza nel repository e' unica.
        if permetti_nome_nudo and "/" not in s and s.endswith(ESTENSIONI):
            trovati = NOMI.get(s, [])
            if len(trovati) == 1:
                conta[trovati[0]] = conta.get(trovati[0], 0) + 1
            elif len(trovati) > 1:
                ambigui[s] = trovati

    for grezzo in RE_CODICE.findall(testo):
        classifica(grezzo.strip(), permetti_nome_nudo=True)

    # Dai commenti dei blocchi recintati si accettano i soli percorsi completi e i file di
    # configurazione in radice, mai i nomi nudi: dentro un commento un nome senza cartella e'
    # una prova troppo debole, e la risoluzione per corrispondenza unica lo promuoverebbe a
    # percorso certo senza che la scheda abbia detto quale file intendeva.
    for token in token_nei_commenti_recintati(testo):
        classifica(token, permetti_nome_nudo=False)

    return conta, ambigui


def autotest():
    """Verifica le due proprieta' corrette il 2026-09-21, piu' quella che NON deve cambiare.

    Una prova che non cadrebbe reintroducendo il difetto non protegge niente, quindi ciascuna di
    queste asserisce esattamente cio' che prima della correzione era falso, o cio' che deve restare
    vero perche' la correzione non ha allargato la fiducia dello strumento.
    """
    global NOMI
    NOMI = {"soloQui.ts": ["src/soloQui.ts"], "duplicato.ts": ["src/a/duplicato.ts", "src/b/duplicato.ts"]}

    # 1. Il percorso nominato SOLO nel commento di intestazione di un blocco viene estratto.
    testo = "prosa qualsiasi\n\n```ts\n// src/utils/esempio.ts\nconst x = 1;\n```\n"
    conta, _ = candidati(testo)
    assert "src/utils/esempio.ts" in conta, "percorso nel commento recintato non estratto"

    # 2. Un percorso che compare nel CODICE e non in un commento non viene estratto: sarebbe
    #    dedurre che la scheda lo tratta, mentre lo sta solo nominando di passaggio.
    testo = "```ts\nimport x from 'src/utils/passaggio.ts';\n```\n"
    conta, _ = candidati(testo)
    assert "src/utils/passaggio.ts" not in conta, "estratto un percorso dal corpo del codice"

    # 3. Un nome nudo dentro un commento resta non risolto, anche se la corrispondenza e' unica.
    testo = "```ts\n// soloQui.ts (invariato)\n```\n"
    conta, _ = candidati(testo)
    assert not conta, "nome nudo in un commento promosso a percorso"

    # 4. Un nome nudo nella PROSA resta risolto per corrispondenza unica, come sempre.
    conta, _ = candidati("la funzione vive in `soloQui.ts` e la si prova a parte")
    assert conta == {"src/soloQui.ts": 1}, "regressione sulla risoluzione dei nomi nudi in prosa"

    # 5. Un nome nudo ambiguo resta ambiguo e non viene scelto.
    _, ambigui = candidati("vedi `duplicato.ts` per il dettaglio")
    assert "duplicato.ts" in ambigui, "nome ambiguo risolto arbitrariamente"

    NOMI = None
    print("autotest: 5 proprieta' verificate, tutte a posto")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Propone i covers-paths estraendoli dalle schede.")
    ap.add_argument("--solo-mancanti", action="store_true",
                    help="salta le schede che hanno gia' il front matter")
    ap.add_argument("--autotest", action="store_true",
                    help="esegue le prove interne dello strumento e non legge nessuna scheda")
    args = ap.parse_args(argv)

    if args.autotest:
        return autotest()

    nomi = sorted(n for n in os.listdir(CARTELLA)
                  if n.startswith(PREFISSO) and n.endswith(".md") and n != PREFISSO + "indice.md")

    senza_nulla, assenti_globali = [], {}
    for nome in nomi:
        percorso = os.path.join(CARTELLA, nome)
        testo = io.open(percorso, encoding="utf-8").read()
        if args.solo_mancanti and ha_front_matter(testo):
            continue

        conta, ambigui = candidati(testo)
        esistono = {p: c for p, c in conta.items() if os.path.exists(p)}
        assenti = {p: c for p, c in conta.items() if not os.path.exists(p)}
        for p, c in assenti.items():
            assenti_globali[p] = assenti_globali.get(p, 0) + c

        print("### %s" % nome)
        if esistono:
            # Nessun tetto al numero di percorsi proposti: la potatura e' dichiarata come lavoro
            # umano, e troncare qui toglierebbe alla persona proprio la decisione che le si voleva
            # lasciare. Il dosaggio del README dice che omettere e' peggio che includere in piu'.
            ordinati = sorted(esistono.items(), key=lambda x: (-x[1], x[0]))
            print("    proposta: [%s]" % ", ".join('"%s"' % p for p, _ in ordinati))
            print("    menzioni: %s" % ", ".join("%s x%d" % (p, c) for p, c in ordinati))
        else:
            print("    NESSUN percorso esistente nominato: serve lettura umana")
            senza_nulla.append(nome)
        if assenti:
            print("    citati ma NON piu' esistenti: %s"
                  % ", ".join("%s x%d" % (p, c) for p, c in sorted(assenti.items())))
        if ambigui:
            print("    nomi ambigui, NON risolti: %s"
                  % "; ".join("%s -> %s" % (n, "|".join(v)) for n, v in sorted(ambigui.items())))
        print()

    print("=" * 72)
    print("schede senza nessun percorso estraibile: %d" % len(senza_nulla))
    for n in senza_nulla:
        print("  %s" % n)
    print()
    print("file citati dalle schede e non piu' esistenti: %d" % len(assenti_globali))
    for p, c in sorted(assenti_globali.items(), key=lambda x: -x[1]):
        print("  %-60s citato %d volte" % (p, c))
    return 0


if __name__ == "__main__":
    sys.exit(main())
