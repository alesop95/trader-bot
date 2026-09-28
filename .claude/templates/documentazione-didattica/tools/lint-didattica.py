# -*- coding: utf-8 -*-
"""
Segnala quando i fatti hanno superato le spiegazioni.

## Perché esiste

Questo progetto tiene due registri paralleli con scopi diversi. `memory/progress.md` registra
**che cosa è accaduto e quando**, in ordine cronologico inverso. `context/studio-didattico-master.md`
registra **perché una scelta è migliore di un'altra**, come racconto evolutivo, e ogni sua voce
rimanda a una scheda `refactor-NN` che entra nel dettaglio.

Il 7 settembre 2026 lo stakeholder ha segnalato che il primo teneva il passo e il secondo no: sei
passi di lavoro registrati come fatti, e il racconto fermo alla voce precedente. La ragione per cui
capita è strutturale e va detta, perché non è pigrizia: **ogni singolo passo sembra troppo piccolo
per meritare una voce, e la somma di sei passi piccoli non lo è.** La decisione di scrivere la
voce si prende sempre sul passo, mai sulla somma, quindi si rimanda sempre.

Un controllo automatico non scrive la voce. Fa l'unica cosa che serve: **rende visibile il
divario** nel momento in cui si apre, invece di lasciarlo scoprire a chi legge fra sei mesi e non
trova il perché di niente.

## Che cosa controlla

Tre cose, tutte meccaniche.

**La didattica dichiarata.** Ogni voce di work-log dal 2026-09-08 in avanti deve portare una riga
`**Didattica:**` che rimanda alla voce del racconto e alla scheda, oppure che dice `nessuna` con la
ragione. Il silenzio è l'unica cosa non ammessa: dichiarare che un passo non ha prodotto una lezione
è una risposta legittima, dimenticarsene no. Il numero di commit di scarto fra i due registri resta
stampato, ma come informazione e non come difetto, perché una voce di work-log senza voce di master
è il caso NORMALE.

La prima versione contava invece le date **scritte nel testo** del racconto, e rispondeva
"2027-06-09": una data futura, la scadenza delle conferme citata nella prosa di una voce.
Confondeva il contenuto con la paternità, ed è un errore istruttivo perché sembrava funzionare, con
una data ben formata e realmente la più recente. Solo che rispondeva a un'altra domanda. **Un
segnale che si trova nel testo non è per questo un segnale sul testo.**

**Le schede orfane.** Una scheda `refactor-NN` che nessuna voce del racconto cita è irraggiungibile:
esiste ma nessuno la trova, perché l'unico indice di quelle schede è narrativo.

**I rimandi rotti.** Una voce che rimanda a una scheda inesistente promette un dettaglio che non c'è.

## Che cosa NON controlla

Se una voce sia scritta bene, se spieghi davvero il perché, se la scheda sia autoconsistente come
richiesto. Sono giudizi, e nessuno strumento li sostituisce. Questo controlla soltanto che le due
serie di documenti **esistano nella stessa quantità e si citino a vicenda**.

## Uso

    python tools/lint-didattica.py

Esce con codice diverso da zero se c'è un divario o un rimando rotto, così si può mettere in una
verifica automatica.
"""
import glob
import io
import os
import re
import subprocess

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

WORKLOG = ".claude/memory/progress.md"
MASTER = ".claude/context/studio-didattico-master.md"

problemi = []


def date_worklog():
    """Le date delle voci del work-log, dalla più recente alla più vecchia."""
    testo = io.open(WORKLOG, encoding="utf-8").read()
    return re.findall(r"^## (\d{4}-\d{2}-\d{2})", testo, re.MULTILINE)


def voci_master():
    """(numero, titolo) di ogni voce del racconto evolutivo."""
    testo = io.open(MASTER, encoding="utf-8").read()
    return [(int(n), t.strip()) for n, t in re.findall(r"^## (\d+)\.\s+(.*)$", testo, re.MULTILINE)]


def commit_arretrati():
    """
    Quanti commit hanno toccato il work-log dopo l'ultimo che ha toccato il racconto.

    ## Perché git e non le date scritte nel testo

    La prima versione di questo controllo prendeva il massimo delle date scritte nel racconto, e
    rispondeva "2027-06-09", cioè **una data futura**: la scadenza delle conferme, citata nella
    prosa di una voce. Confondeva il **contenuto** con la **paternità**.

    È un errore istruttivo perché sembrava funzionare: una data c'era, era ben formata, ed era la
    più recente. Solo che rispondeva a un'altra domanda. **Un segnale che si trova nel testo non
    è per questo un segnale sul testo**, e qui la domanda era "quando è stata scritta l'ultima
    voce", che nel testo non è scritta da nessuna parte.

    La risposta vive invece nella storia del repository, che registra la paternità per mestiere.
    """
    ## Perché un intervallo di commit e non `--since` con una data
    ##
    ## La prima versione usava `--since=<data dell'ultimo commit sul racconto>`, e ha segnalato se
    ## stessa: `--since` **include** il commit al confine, quindi il commit che aggiorna entrambi i
    ## registri nello stesso giro veniva contato come successivo a sé stesso. Uno scarto di uno.
    ##
    ## Il rimedio non è spostare la soglia di un secondo, che sarebbe un numero magico appoggiato a
    ## un'assunzione sui tempi. È smettere di usare il tempo: `<hash>..HEAD` chiede al grafo dei
    ## commit "quelli venuti DOPO quel commit", che è la domanda vera e non ha confini ambigui.
    ## **Quando una domanda sull'ordine si può porre al grafo, porla alle date è una scelta
    ## peggiore anche quando funziona.**
    r = subprocess.run(
        ["git", "log", "-1", "--format=%H %cs", "--", MASTER],
        capture_output=True, text=True
    )
    if not r.stdout.strip():
        return None, []
    impronta, quando = r.stdout.strip().split(" ", 1)
    r = subprocess.run(
        ["git", "log", f"{impronta}..HEAD", "--format=%cs %s", "--", WORKLOG],
        capture_output=True, text=True
    )
    righe = [l for l in r.stdout.strip().split("\n") if l.strip()]
    return quando, righe


# ------------------------------------------------------------------ didattica dichiarata
# Ogni voce di work-log dichiara se ha prodotto una lezione, e dove vive.
#
# ### Perché non basta confrontare i due registri
#
# La prima versione contava i commit sul work-log successivi all'ultimo sul racconto, e sarebbe
# diventata **rossa per costruzione**: non ogni passo produce una lezione, quindi una voce di
# work-log senza una voce di master corrispondente è il caso NORMALE, non un difetto. Un controllo
# rosso per costruzione si spegne alla terza volta, e allora non serve nella quarta.
#
# Lo schema giusto è lo stesso già usato due volte in questo progetto per lo stesso genere di
# problema: `// @verifica:` nelle suite di prova e `<!-- ref-assente -->` nella documentazione.
# **L'eccezione si dichiara dove vive il caso**, non in un elenco dentro lo strumento, perché un
# elenco dentro lo strumento è invisibile a chi scrive il caso e sopravvive al caso che lo
# giustificava.
#
# Quindi ogni voce di work-log porta una riga:
#
#     **Didattica:** voce 96 nel master, scheda `refactor-59-...md`
#     **Didattica:** nessuna, passo meccanico senza una lezione da trarre
#
# e questo controllo segnala solo le voci che **non dicono niente**. Il silenzio è l'unica cosa
# che non è ammessa: dichiarare "nessuna" è una risposta legittima e verificabile, dimenticarsene
# no.
#
# ### Perché una data di partenza
#
# Il work-log ha centinaia di voci scritte prima che questa convenzione esistesse, e pretenderle
# tutte marcate renderebbe il controllo inutilizzabile dal primo giorno. Si applica alle voci dal
# 2026-09-08 in avanti, cioè dal giorno dopo la sua introduzione: l'arretrato è un lavoro a sé, e
# un controllo che nasce con centinaia di segnalazioni non lo si guarda mai.
DA_QUANDO = "2026-09-08"


def voci_worklog_senza_didattica():
    """Le voci del work-log dalla data di partenza che non dichiarano la propria didattica."""
    testo = io.open(WORKLOG, encoding="utf-8").read()
    # Si spezza sui titoli di secondo livello che cominciano con una data.
    pezzi = re.split(r"^(## \d{4}-\d{2}-\d{2}[^\n]*)$", testo, flags=re.MULTILINE)
    mancanti = []
    for i in range(1, len(pezzi), 2):
        titolo, corpo = pezzi[i], pezzi[i + 1] if i + 1 < len(pezzi) else ""
        data = re.match(r"## (\d{4}-\d{2}-\d{2})", titolo).group(1)
        if data < DA_QUANDO:
            continue
        if "**Didattica:**" not in corpo:
            mancanti.append(titolo.replace("## ", "").strip()[:90])
    return mancanti


date_fatti = date_worklog()
quando_master, arretrati = commit_arretrati()
senza_didattica = voci_worklog_senza_didattica()

if not date_fatti:
    problemi.append("nessuna voce trovata nel work-log: il formato dei titoli è cambiato?")
print(f"ultima voce di work-log:            {max(date_fatti) if date_fatti else '?'}")
print(f"ultimo commit sul racconto:         {quando_master or '?'}")
print(f"commit sul work-log dopo di quello: {len(arretrati)} (informativo, non un difetto)")
print(f"voci dal {DA_QUANDO} senza didattica dichiarata: {len(senza_didattica)}")

if senza_didattica:
    problemi.append(
        f"{len(senza_didattica)} voci di work-log non dichiarano la propria didattica. Ognuna deve "
        f"portare una riga `**Didattica:**` che rimanda alla voce del master e alla scheda, oppure "
        f"che dice `nessuna` con la ragione: "
        + "; ".join(senza_didattica)
    )

# ------------------------------------------------------------------ schede orfane e rimandi rotti
# Le schede vere hanno un numero nel nome. L'indice generato da `tools/indice-refactor.py` si
# chiama `refactor-indice.md` e combaciava con il modello, quindi veniva segnalato come scheda
# orfana: un file generato non e' una scheda e non puo' essere citato dal racconto, perche' il
# racconto cita argomenti e quello e' un elenco. Corretto il 2026-09-21, ed e' il caso generale
# **di un controllo che riconosce i propri bersagli dal nome**: basta che nasca un file con un
# nome compatibile perche' il controllo produca un difetto che non esiste.
schede = sorted(
    os.path.basename(p) for p in glob.glob(".claude/context/refactor-*.md")
    if re.match(r"refactor-\d+-", os.path.basename(p))
)
testo_master = io.open(MASTER, encoding="utf-8").read()

orfane = [s for s in schede if s not in testo_master]
citate = set(re.findall(r"(refactor-\d+[a-z0-9-]*\.md)", testo_master))
rotte = sorted(c for c in citate if not os.path.exists(os.path.join(".claude/context", c)))

print(f"schede refactor sul disco:     {len(schede)}")
print(f"schede citate dal racconto:    {len(citate)}")

if orfane:
    problemi.append(
        f"{len(orfane)} schede che nessuna voce del racconto cita, quindi irraggiungibili "
        f"(l'unico indice di quelle schede è narrativo): " + ", ".join(orfane)
    )
if rotte:
    problemi.append(
        f"{len(rotte)} rimandi a schede inesistenti, cioè un dettaglio promesso e assente: "
        + ", ".join(rotte)
    )

# ------------------------------------------------------------------ esito
voci = voci_master()
print(f"voci nel racconto evolutivo:   {len(voci)} (l'ultima è la {voci[-1][0] if voci else '?'})")

if problemi:
    print("\nDA SISTEMARE:")
    for p in problemi:
        print(f"  - {p}")
    raise SystemExit(f"\n{len(problemi)} problemi.")
print("\nfatti e spiegazioni allineati")
