#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Converte gli accenti scritti con l'apostrofo negli accenti veri, secondo grammatica.

Perché esiste
--------------
Parte della documentazione di questo progetto, e parte del template da cui viene, scrive
gli accenti come apostrofo posticcio: `è` invece di `e` accentata, `perché` invece di
`perche` con l'acuto, `più` invece di `piu` con l'accento. Non è una convenzione
deliberata, è un residuo: nello stesso template i due documenti normativi usano gli
accenti veri mentre altri file usano l'apostrofo, e alcuni non mettono l'accento affatto.
Un testo che deve essere leggibile come tesi non può avere tre grafie della stessa
parola, quindi si converte, una volta, con uno strumento verificabile.

Perché non una sostituzione a mano
-----------------------------------
Perché la scelta fra accento grave e acuto non è meccanica, e perché esistono
apostrofi che non sono accenti mancanti e che una sostituzione ingenua distruggerebbe.
Il caso di scuola è `un po'`, che è un troncamento di `poco` e si scrive con
l'apostrofo: `un po` con l'accento grave è un errore, ed è fra i più diffusi in
italiano. Nella stessa categoria stanno gli imperativi tronchi `fa'`, `va'`, `sta'`,
`di'`, e le forme come `mo'` e `be'`.

Da qui l'impostazione dello strumento: converte soltanto ciò che sta in una lista
bianca esplicita, e tutto il resto lo segnala perché un umano decida. Non indovina.

La regola grammaticale, in breve
--------------------------------
Sulle vocali a, i, o, u finali l'accento italiano è sempre grave: citta, cosi, puo,
piu diventano con l'accento grave. Sulla e finale il segno dipende dalla parola: è
grave nel verbo essere e in parole come cioe e caffe, ed è acuto nei composti di che,
ne e se, cioè perche, poiche, benche, affinche, purche, finche, nonche, anziche, ne,
se, e in poche altre come pote e ventitre.

Il caso ambiguo dichiarato
--------------------------
`dà` può essere la terza persona dell'indicativo di dare, che si scrive con l'accento
grave, oppure il suo imperativo, che si scrive con l'apostrofo. Le due si distinguono
solo dal senso della frase, quindi lo strumento non lo converte e lo elenca fra i casi
da decidere.

Che cosa non tocca
------------------
Nei file Markdown salta i blocchi di codice recintati e i code span in linea, perché
là un apostrofo può essere sintassi e non prosa. Nei file di codice lavora solo su
commenti e stringhe di documentazione, per la stessa ragione. Conserva la fine riga, il
newline finale e l'eventuale BOM del file, come fa md-unwrap.

Uso
---
    python tools/fix-accents.py --check <percorsi>      elenca senza scrivere
    python tools/fix-accents.py <percorsi>              converte
    python tools/fix-accents.py --residui <percorsi>    elenca solo i casi non in lista

Senza percorsi lavora sulla radice del progetto.
"""

import argparse
import os
import re
import sys


# Le macro LaTeX il cui argomento e' un identificatore e non prosa. Il loro contenuto
# non va mai accentato ne' normalizzato: un'etichetta accentata compila soltanto se
# ogni riferimento viene riscritto insieme a essa, e un riferimento rimasto indietro
# produce due punti di domanda nel PDF senza che nulla lo segnali. E' lo stesso
# principio per cui nei file Markdown si salta il contenuto dei blocchi recintati:
# dentro un file convivono due linguaggi, e soltanto uno dei due vuole gli accenti.
IDENTIFICATORI_TEX = re.compile(
    r"\\(?:label|ref|pageref|eqref|autoref|cite|nocite|input|include"
    r"|includegraphics|bibitem|hypertarget|hyperlink|url|href|usepackage"
    r"|documentclass|newcommand|renewcommand|newenvironment|begin|end)"
    r"(?:\[[^\]]*\])?"
    r"\{[^{}]*\}")


def maschera_identificatori(testo):
    """Sostituisce gli argomenti-identificatore con segnaposto inerti.

    Il segnaposto non contiene lettere accentabili, apostrofi ne' trattini, quindi
    nessuna regola degli strumenti lo tocca. Restituisce il testo mascherato e la
    lista degli originali, nell'ordine in cui vanno ripristinati.
    """
    salvati = []

    def sostituisci(m):
        salvati.append(m.group(0))
        return "%sTEXID%d%s" % (SEGNAPOSTO, len(salvati) - 1, SEGNAPOSTO)

    return IDENTIFICATORI_TEX.sub(sostituisci, testo), salvati


def ripristina_identificatori(testo, salvati):
    for i, originale in enumerate(salvati):
        testo = testo.replace("%sTEXID%d%s" % (SEGNAPOSTO, i, SEGNAPOSTO), originale)
    return testo


SEGNAPOSTO = chr(0)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------------------
# Lista bianca. La chiave è la forma con l'apostrofo, il valore quella accentata.
# Si confronta parola intera e senza distinzione di maiuscole, e la maiuscola iniziale
# viene riportata sul risultato.
# ---------------------------------------------------------------------------

# Accento acuto: i composti di che, ne, se, più poche forme verbali e numerali.
ACUTO = {
    "perche": "perché", "poiche": "poiché", "benche": "benché",
    "affinche": "affinché", "purche": "purché", "finche": "finché",
    "cosicche": "cosicché", "sicche": "sicché", "anziche": "anziché",
    "dopodiche": "dopodiché", "nonche": "nonché", "giacche": "giacché",
    "fuorche": "fuorché", "salvoche": "salvoché", "checche": "checché",
    "ne": "né", "se": "sé", "pote": "poté", "ventitre": "ventitré",
    "trentatre": "trentatré", "quarantatre": "quarantatré",
    "ventunesimo": "ventunesimo",
}

# Accento grave: il verbo essere, le vocali a i o u finali, e le e finali non composte.
GRAVE = {
    "e": "è", "cioe": "cioè", "caffe": "caffè",
    "piu": "più", "gia": "già", "cosi": "così", "puo": "può", "pero": "però",
    "cio": "ciò", "li": "lì", "la": "là", "giu": "giù",
    "pie": "piè", "ahime": "ahimè", "tre": "trè",
    # verbi al futuro e al passato remoto, terza persona
    "sara": "sarà", "verra": "verrà", "andra": "andrà", "dara": "darà",
    "fara": "farà", "stara": "starà", "avra": "avrà", "potra": "potrà",
    "dovra": "dovrà", "sapra": "saprà", "vorra": "vorrà", "terra": "terrà",
    "restera": "resterà", "diventera": "diventerà", "servira": "servirà",
    "cambiera": "cambierà", "sposta": "sposta", "ando": "andò",
    "trovo": "trovò", "risulto": "risultò", "porto": "portò",
    # sostantivi in -ita, -eta, -a tronca
    "unita": "unità", "verita": "verità", "qualita": "qualità",
    "citta": "città", "possibilita": "possibilità", "capacita": "capacità",
    "attivita": "attività", "identita": "identità", "integrita": "integrità",
    "difficolta": "difficoltà", "novita": "novità", "priorita": "priorità",
    "meta": "metà", "eta": "età", "volonta": "volontà", "puntualita": "puntualità",
    "affidabilita": "affidabilità", "compatibilita": "compatibilità",
    "disponibilita": "disponibilità", "ammissibilita": "ammissibilità",
    "praticabilita": "praticabilità", "riservatezza": "riservatezza",
    "specificita": "specificità", "regolarita": "regolarità",
    "commutativita": "commutatività", "invarianza": "invarianza",
    "portabilita": "portabilità", "leggibilita": "leggibilità",
    "tracciabilita": "tracciabilità", "immutabilita": "immutabilità",
    "eleganza": "eleganza", "densita": "densità", "brevita": "brevità",
    "utilita": "utilità", "necessita": "necessità", "curiosita": "curiosità",
    "generalita": "generalità", "particolarita": "particolarità",
    "meccanicita": "meccanicità", "riproducibilita": "riproducibilità",
    "ispezionabilita": "ispezionabilità", "sacrificabilita": "sacrificabilità",
    # prima persona del futuro
    "sapro": "saprò", "potro": "potrò", "faro": "farò", "andro": "andrò",
    "tornero": "tornerò", "scrivero": "scriverò", "leggero": "leggerò",
}

# Forme con apostrofo che NON sono accenti mancanti: non si toccano mai.
APOSTROFO_LEGITTIMO = {
    "po", "fa", "sta", "va", "di", "mo", "be", "ca", "pa", "to", "de",
    "un", "buon", "qual", "tal", "sant", "dell", "nell", "all", "sull",
    "dall", "quell", "bell", "quest", "cos", "com", "anch", "dov", "c",
    "l", "d", "n", "m", "s", "t", "v", "gl",
}

# Forme genuinamente ambigue: si elencano e non si convertono.
AMBIGUE = {
    "da": ("dà se è indicativo di dare, dà se è imperativo: dipende dalla frase"),
}

# Regola per suffisso, che rende inutile elencare a mano ogni parola.
# In italiano l'accento sulle vocali a, i, o, u in fine di parola è sempre grave: non
# esiste una parola italiana che termini con una di queste vocali accentata in modo
# acuto. La conversione di quelle uscite è quindi meccanica e non richiede una lista,
# a differenza della e finale, dove il segno dipende dalla parola e la lista serve.
#
# La regola si applica solo dopo i controlli sugli apostrofi legittimi e sui casi
# ambigui, e solo a parole di almeno due lettere, perché le forme brevi da non
# toccare sono già filtrate dai controlli precedenti. Le parole che finiscono in altre lettere, comprese quelle di altre
# lingue come what', non sono toccate e restano fra i residui da guardare.
VOCALI_SEMPRE_GRAVI = {"a": "\u00e0", "i": "\u00ec", "o": "\u00f2", "u": "\u00f9"}


def per_suffisso(parola):
    """L'accentazione ricavata dalla regola, o None se la regola non si applica."""
    # Due lettere bastano: sì diventa sì, che è una parola legittima. Le forme brevi
    # che non vanno toccate, cioè po', fa', va', di' e simili, sono già state filtrate
    # dai controlli precedenti, quindi la soglia qui serve solo a escludere le singole
    # lettere dell'elisione.
    if len(parola) < 2:
        return None
    ultima = parola[-1].lower()
    accentata = VOCALI_SEMPRE_GRAVI.get(ultima)
    if accentata is None:
        return None
    return parola[:-1] + accentata


# Un token candidato: parola alfabetica seguita da apostrofo dritto o tipografico,
# non seguita da un'altra lettera (per non colpire l'elisione come dell'area).
CANDIDATO = re.compile(r"\b([A-Za-z]+)['’](?![A-Za-z])")

# Il residuo della doppia correzione, che nessuna delle due liste sopra può cogliere
# perché la parola non finisce più con una lettera ASCII. Nasce così: un testo scritto
# nella convenzione con l'apostrofo, per esempio perche', riceve prima la correzione
# degli accenti mancanti, che accenta la vocale e lascia l'apostrofo dov'era, e il
# risultato è perché seguito da apostrofo. In italiano quella sequenza non esiste mai,
# perché l'apostrofo dopo una vocale già accentata non sostituisce nulla e non elide
# nulla, quindi la correzione è togliere l'apostrofo e non decidere fra due letture.
# La causa è stata rimossa in `fix-missing-accents.py`, che ora non tocca una parola
# seguita da apostrofo; questo resta perché i file corrotti prima di quella correzione
# esistono, e un difetto senza il suo rimedio è un difetto che si porta a mano.
RESIDUO_DOPPIA_CORREZIONE = re.compile(r"([àèéìòù])['’](?![A-Za-z])")

# Impostata dalla riga di comando. Quando è vera, dà viene trattata
# come indicativo e convertita. Resta falsa per default perché la
# scelta prudente è non decidere al posto di chi conosce il testo.
DA_INDICATIVO = False


def maiuscola_come(originale, sostituto):
    """Riporta sul sostituto la maiuscola iniziale dell'originale."""
    if originale[:1].isupper():
        return sostituto[:1].upper() + sostituto[1:]
    return sostituto


def segmenta_markdown(testo):
    """Divide il testo in tratti (tipo, contenuto) la cui concatenazione è l'originale.

    Il tipo vale "prosa" dove la conversione si applica e "verbatim" dove non si applica.
    Sono verbatim i blocchi recintati da tre backtick o tre tilde, comprese le righe di
    recinto, e i code span in linea. La prudenza è la stessa di md-unwrap: dentro un
    blocco di codice un apostrofo può essere sintassi, e riscriverlo cambierebbe il
    significato del documento.

    L'invariante che questa funzione garantisce, e che l'autotest verifica, è che la
    concatenazione dei contenuti sia identica al testo di partenza: ogni a capo sta
    dentro un tratto e nessuno viene aggiunto in fase di ricomposizione.
    """
    tratti = []
    dentro_recinto = False
    # Il front matter e' metadato e non prosa: un tag accentato e' un tag diverso, e
    # due tag che differiscono per un accento non si uniscono in alcun indice. Si
    # riconosce solo in apertura di file, perche' altrove tre trattini sono una linea.
    dentro_front = testo.startswith('---' + chr(10))
    prima_riga = True
    recinto = None
    # Si itera conservando l'a capo dentro la riga, così la concatenazione è esatta.
    for riga in testo.splitlines(keepends=True):
        nudo = riga.rstrip("\n")
        if dentro_front:
            tratti.append(("verbatim", riga))
            if not prima_riga and nudo.strip() == '---':
                dentro_front = False
            prima_riga = False
            continue
        m = re.match(r"^\s*(`{3,}|~{3,})", nudo)
        if not dentro_recinto and m:
            dentro_recinto, recinto = True, m.group(1)[0] * 3
            tratti.append(("verbatim", riga))
            continue
        if dentro_recinto:
            tratti.append(("verbatim", riga))
            if re.match(r"^\s*" + re.escape(recinto), nudo):
                dentro_recinto = False
            continue
        # Fuori dai recinti la riga si spezza sui code span in linea.
        for pezzo in re.split(r"(`+[^`\n]*`+)", riga):
            if not pezzo:
                continue
            tratti.append(("verbatim" if pezzo.startswith("`") else "prosa", pezzo))
    return tratti


def togli_residuo(testo, statistiche):
    """Toglie l'apostrofo rimasto dopo una vocale gia' accentata.

    Non decide nulla e non ha casi ambigui, che e' la ragione per cui non riporta
    residui: una vocale accentata seguita da apostrofo non e' una forma dell'italiano,
    quindi l'unica lettura possibile e' che l'apostrofo sia di troppo. Il conteggio
    entra nelle statistiche sotto una chiave propria, cosicche' una corsa dichiari
    quante volte ha riparato invece di quante volte ha convertito.
    """
    def sostituisci(m):
        statistiche["residuo-apostrofo"] = statistiche.get("residuo-apostrofo", 0) + 1
        return m.group(1)

    return RESIDUO_DOPPIA_CORREZIONE.sub(sostituisci, testo)


def converti_prosa(testo, statistiche, residui, ambigui, per_regola=None):
    if per_regola is None:
        per_regola = set()

    def sostituisci(m):
        parola = m.group(1)
        chiave = parola.lower()
        if chiave in APOSTROFO_LEGITTIMO:
            return m.group(0)
        if chiave in AMBIGUE:
            if chiave == "da" and DA_INDICATIVO:
                statistiche[chiave] = statistiche.get(chiave, 0) + 1
                return maiuscola_come(parola, "dà")
            ambigui[chiave] = ambigui.get(chiave, 0) + 1
            return m.group(0)
        if chiave in ACUTO:
            statistiche[chiave] = statistiche.get(chiave, 0) + 1
            return maiuscola_come(parola, ACUTO[chiave])
        if chiave in GRAVE:
            statistiche[chiave] = statistiche.get(chiave, 0) + 1
            return maiuscola_come(parola, GRAVE[chiave])
        # Nessuna lista la contiene: si tenta la regola per suffisso, che copre tutte
        # le uscite in a, i, o, u senza bisogno di enumerarle.
        dalla_regola = per_suffisso(parola)
        if dalla_regola is not None:
            statistiche[chiave] = statistiche.get(chiave, 0) + 1
            per_regola.add(chiave)
            return dalla_regola
        residui[chiave] = residui.get(chiave, 0) + 1
        return m.group(0)

    testo = CANDIDATO.sub(sostituisci, testo)
    return togli_residuo(testo, statistiche)


def elabora(percorso, statistiche, residui, ambigui):
    """Converte un file conservandone la forma binaria: fine riga, BOM, newline finale."""
    with open(percorso, "rb") as f:
        grezzo = f.read()

    bom = grezzo.startswith(b"\xef\xbb\xbf")
    corpo = grezzo[3:] if bom else grezzo
    crlf = b"\r\n" in corpo
    testo = corpo.decode("utf-8").replace("\r\n", "\n")

    # Su un file .tex gli identificatori si mascherano prima di convertire: il nome di
    # un'etichetta o di una chiave bibliografica non e' prosa, e riscriverlo produce un
    # riferimento irrisolto silenzioso invece di un errore.
    tex = percorso.lower().endswith((".tex", ".sty", ".cls", ".lytex"))
    salvati = []
    if tex:
        testo, salvati = maschera_identificatori(testo)

    if percorso.lower().endswith(".py"):
        nuovo = converti_python(testo, statistiche, residui, ambigui)
    elif percorso.lower().endswith(".md"):
        tratti = segmenta_markdown(testo)
        # Invariante: la concatenazione dei tratti è il testo di partenza. Se non lo
        # fosse, la conversione produrrebbe un file diverso per un motivo che non è
        # la conversione, quindi si preferisce fallire.
        if "".join(c for _, c in tratti) != testo:
            raise AssertionError("segmentazione non fedele su %s" % percorso)
        nuovo = "".join(
            converti_prosa(c, statistiche, residui, ambigui) if t == "prosa" else c
            for t, c in tratti)
    else:
        nuovo = converti_prosa(testo, statistiche, residui, ambigui)

    if tex:
        nuovo = ripristina_identificatori(nuovo, salvati)
        testo = ripristina_identificatori(testo, salvati)
    if nuovo == testo:
        return False, None
    uscita = nuovo.replace("\n", "\r\n") if crlf else nuovo
    dati = uscita.encode("utf-8")
    if bom:
        dati = b"\xef\xbb\xbf" + dati
    return True, dati


# ---------------------------------------------------------------------------
# Modalità Python, deliberatamente più prudente di quella Markdown.
# ---------------------------------------------------------------------------
# In un file di codice l'apostrofo non è solo punteggiatura: delimita le stringhe. Una
# stringa come 'tipo' offre al riconoscitore la sequenza tipo seguita da apostrofo, che
# la regola per suffisso trasformerebbe in tipo con l'accento, rompendo il programma. Il
# rischio non è teorico: nel repository esistono 'voci', 'tipo', 'metà e altre chiavi
# che finiscono in una vocale.
#
# Da qui due limitazioni. La prima è dove si converte: soltanto nei commenti, nelle
# stringhe di documentazione e nelle stringhe delimitate da doppi apici, mai in quelle
# delimitate da apici singoli, il cui apostrofo di chiusura è precisamente ciò che
# confonde il riconoscitore. La seconda è come si converte: solo con la lista bianca,
# senza la regola per suffisso, perché anche dentro un commento può comparire il nome
# di una chiave citata fra apici singoli.
# Nei file di codice il riconoscitore va reso più stretto di un elemento: la parola
# non deve essere preceduta da un apostrofo. La ragione è che dentro un docstring o
# un commento si citano gli identificatori fra apici singoli, e in una citazione come
# quella la sequenza che il riconoscitore vede è la parola seguita dall'apostrofo di
# chiusura, indistinguibile da un accento mancante. Il lookbehind risolve il caso
# senza euristiche: se prima della parola c'e' un apostrofo, quello che segue è una
# chiusura di citazione. Con questa distinzione la regola per suffisso torna sicura
# anche qui, e non serve elencare a mano le decine di parole che finiscono in -ita.
# Una sola lettera basta come candidata, perché le forme di una lettera sono tutte
# nell'elenco degli apostrofi legittimi dell'elisione e vengono scartate là.
_AP = chr(39) + chr(0x2019)
CANDIDATO_CODICE = re.compile(
    r"(?<![A-Za-z" + _AP + r"])([A-Za-z]+)[" + _AP + r"](?![A-Za-z])")

STRINGA_DOPPIA = re.compile(r'"(?:[^"\\\n]|\\.)*"')
DOCSTRING = re.compile(r'"""(?:.|\n)*?"""')


def converti_lista_bianca(testo, statistiche, residui, ambigui):
    """La conversione per i file di codice.

    Si distingue da converti_prosa in un punto solo, il riconoscitore: qui una
    parola preceduta da apostrofo non è candidata, perché in un file di codice
    quello è il delimitatore di una citazione e non un accento mancante. Con
    quella garanzia la regola per suffisso si può applicare anche qui.
    """
    def sostituisci(m):
        parola = m.group(1)
        chiave = parola.lower()
        if chiave in APOSTROFO_LEGITTIMO:
            return m.group(0)
        if chiave in AMBIGUE:
            if chiave == "da" and DA_INDICATIVO:
                statistiche[chiave] = statistiche.get(chiave, 0) + 1
                return maiuscola_come(parola, "d\u00e0")
            ambigui[chiave] = ambigui.get(chiave, 0) + 1
            return m.group(0)
        if chiave in ACUTO:
            statistiche[chiave] = statistiche.get(chiave, 0) + 1
            return maiuscola_come(parola, ACUTO[chiave])
        if chiave in GRAVE:
            statistiche[chiave] = statistiche.get(chiave, 0) + 1
            return maiuscola_come(parola, GRAVE[chiave])
        dalla_regola = per_suffisso(parola)
        if dalla_regola is not None:
            statistiche[chiave] = statistiche.get(chiave, 0) + 1
            return dalla_regola
        residui[chiave] = residui.get(chiave, 0) + 1
        return m.group(0)

    testo = CANDIDATO_CODICE.sub(sostituisci, testo)
    return togli_residuo(testo, statistiche)


def converti_python(testo, statistiche, residui, ambigui):
    """Converte solo docstring, stringhe a doppi apici e commenti.

    L'ordine conta: prima i docstring, che possono contenere qualunque cosa, poi le
    stringhe a doppi apici che restano, poi i commenti sulle righe rimaste. I tre
    insiemi non si sovrappongono perché ciascun passaggio lavora su ciò che il
    precedente non ha consumato, e le sostituzioni non allungano né accorciano il testo
    in modo che sposti gli indici degli altri, perché avvengono in una sola passata di
    espressione regolare per categoria.
    """
    def in_docstring(m):
        return converti_lista_bianca(m.group(0), statistiche, residui, ambigui)

    testo = DOCSTRING.sub(in_docstring, testo)

    def in_stringa(m):
        return converti_lista_bianca(m.group(0), statistiche, residui, ambigui)

    testo = STRINGA_DOPPIA.sub(in_stringa, testo)

    # I commenti: si converte solo la parte dopo il cancelletto, e solo se il cancelletto
    # non è dentro una stringa. La verifica è approssimata contando gli apici prima di
    # esso, che è sufficiente su codice normalmente formattato e prudente in caso di
    # dubbio, perché in caso di conteggio dispari la riga viene lasciata stare.
    righe = []
    for riga in testo.split("\n"):
        pos = riga.find("#")
        if pos < 0:
            righe.append(riga)
            continue
        prima = riga[:pos]
        if prima.count('"') % 2 or prima.count("'") % 2:
            righe.append(riga)
            continue
        righe.append(prima + converti_lista_bianca(
            riga[pos:], statistiche, residui, ambigui))
    return "\n".join(righe)


# Se falso, i file sotto .claude/templates/ non si riscrivono: vedi la guardia in raccolta.
MODELLI_AMMESSI = False


def raccogli(percorsi, estensioni):
    # Uno strumento che riscrive testo italiano non deve riscrivere il proprio sorgente:
    # i suoi casi di prova contengono di proposito le sequenze che cerca, e una corsa su
    # se stesso li altererebbe. E' accaduto due volte durante lo sviluppo, e la difesa
    # e' strutturale invece che mnemonica.
    # Gli strumenti tipografici della stessa famiglia si escludono a vicenda, non solo se
    # stessi: i loro casi di prova contengono di proposito le sequenze che cercano, e una
    # corsa incrociata li altera. E' accaduto tre volte durante lo sviluppo.
    # Le copie dei modelli sotto .claude/templates/ non si correggono dentro il progetto
    # che le ospita: sono copie di questo template, e riscriverle la' allarga la divergenza
    # che la loro ri-propagazione esiste per chiudere. Il divieto viveva nella sola prosa di
    # CLAUDE.md ed e' stato violato due volte nella stessa sessione, la seconda meno di un'ora
    # dopo averlo scritto come regola: una convenzione che un comando puo' violare per
    # distrazione va difesa dal comando, non dalla memoria di chi lo lancia. La difesa e'
    # quindi strutturale, come l'auto-esclusione qui sopra, e parla invece di tacere.
    def sotto_templates(percorso):
        parti = os.path.abspath(percorso).replace("\\", "/").split("/")
        for i in range(len(parti) - 1):
            if parti[i] == ".claude" and parti[i + 1] == "templates":
                return True
        return False

    # La famiglia non sono soltanto i tre convertitori: sono anche il banco di prova che li
    # esercita e l'elenco delle esclusioni, perche' entrambi contengono di proposito le forme
    # che gli strumenti cercano. Una corsa che li riscrivesse romperebbe le prove invece di
    # correggere un testo, ed e' lo stesso genere di ricorsione che l'auto-esclusione previene.
    FAMIGLIA = {"fix-accents.py", "fix-missing-accents.py", "fix-dashes.py",
                "test-tipografia.py", "dashes-exclude.txt", "accents-exclude.txt"}
    IO_STESSO = os.path.abspath(__file__)

    # Esclusioni per singolo file, con lo stesso formato e la stessa regola di fix-dashes.py:
    # una voce senza motivo viene rifiutata. Aggiunte il 2026-09-23 (voce C-46) per una ragione
    # che vale la pena scrivere qui, perche' e' il difetto che questo meccanismo chiude.
    # Il 2026-09-01 una passata di questo strumento rovino' `refactor-53`, che contiene le
    # grafie sbagliate COME DATO, cioe' come esempi di cio' che lo strumento corregge. La
    # scheda `refactor-54` racconto' l'errore, ne trasse la conclusione giusta - una nota in
    # prosa non e' una guardia - e mostro' un frammento di codice come rimedio. Quel codice
    # non e' mai atterrato: verificato sull'intera storia del repository, zero occorrenze.
    # Per ventidue giorni il rimedio e' esistito solo nella scheda che lo mostrava, ed e' una
    # condizione peggiore dell'assenza dichiarata, perche' chi legge smette di cercare.
    esclusi, malformate = leggi_esclusioni()
    if malformate:
        print("esclusioni senza motivo, rifiutate:", file=sys.stderr)
        for r in malformate:
            print("  %s" % r, file=sys.stderr)
        raise SystemExit(1)

    def relativo(percorso):
        """Il percorso relativo alla radice del repository, oppure None se sta fuori.

        Su Windows `relpath` solleva quando i due percorsi stanno su unita' diverse, e non e'
        un caso di scuola: lo strumento puo' legittimamente essere puntato su una cartella
        altrove, per esempio su una copia di prova. Le esclusioni sono dichiarate relative alla
        radice, quindi un file fuori dalla radice non puo' essere escluso: si risponde None e
        chi chiama lo tratta come non escluso, invece di interrompere il programma.
        """
        try:
            return os.path.normpath(os.path.relpath(os.path.abspath(percorso), ROOT))
        except ValueError:
            return None

    def escluso(percorso):
        rel = relativo(percorso)
        return rel is not None and rel in esclusi

    file = []
    for p in percorsi:
        ap = p if os.path.isabs(p) else os.path.join(ROOT, p)
        if not os.path.exists(ap):
            # C-52: un percorso relativo si cercava soltanto dalla radice del progetto, e se non
            # esisteva os.walk non produceva niente e lo strumento rispondeva "0 file esaminati, 0
            # da modificare", cioe' un successo vuoto. Lanciato da un'altra cartella, anche un file
            # vero spariva cosi'. Ora si cerca anche dalla cartella corrente, e se non esiste in
            # nessuno dei due posti lo strumento si ferma invece di dichiarare che va tutto bene.
            dal_cwd = os.path.abspath(p)
            if os.path.exists(dal_cwd):
                ap = dal_cwd
            else:
                print("percorso inesistente: {} (cercato dalla radice del progetto e dalla "
                      "cartella corrente)".format(p), file=sys.stderr)
                sys.exit(2)
        if os.path.isfile(ap):
            if sotto_templates(ap) and not MODELLI_AMMESSI:
                print(f"rifiutato, sta sotto .claude/templates/: {p}", file=sys.stderr)
                continue
            if escluso(ap):
                # Il salto si dichiara invece di tacere: una protezione silenziosa sembra una
                # svista a chi guarda l'uscita, ed e' cosi' che una guardia smette di esistere.
                rel = relativo(ap)
                print(f"escluso ({esclusi[rel]}): {rel}", file=sys.stderr)
                continue
            if os.path.abspath(ap) != IO_STESSO and os.path.basename(ap) not in FAMIGLIA:
                file.append(ap)
            continue
        for radice, cartelle, nomi in os.walk(ap):
            cartelle[:] = [c for c in cartelle
                           if c not in (".git", "__pycache__", "node_modules",
                                        ".venv", "_notes")]
            # Una cartella marcata .md-unwrap-ignore contiene materiale di confronto byte per
            # byte, e riscriverne anche una lettera lo invalida. Il marcatore lo rispettavano
            # md-unwrap e il controllo dei comandi, non i tre strumenti tipografici: una
            # protezione dichiarata che due strumenti su cinque non vedevano, cioe' nessuna
            # protezione. Qui il ramo si pota invece di filtrare i singoli file, perche' il
            # marcatore parla della cartella.
            if ".md-unwrap-ignore" in nomi:
                cartelle[:] = []
                continue
            for n in sorted(nomi):
                if os.path.splitext(n)[1].lower() in estensioni:
                    completo = os.path.join(radice, n)
                    if sotto_templates(completo) and not MODELLI_AMMESSI:
                        continue
                    if escluso(completo):
                        rel = relativo(completo)
                        print(f"escluso ({esclusi[rel]}): {rel}", file=sys.stderr)
                        continue
                    if os.path.abspath(completo) != IO_STESSO and n not in FAMIGLIA:
                        file.append(completo)
    return file


def leggi_esclusioni():
    """Le esclusioni per singolo file, con il motivo obbligatorio.

    Stesso formato e stessa regola di `tools/dashes-exclude.txt`: una riga per percorso, il
    motivo dopo un cancelletto, e una voce senza motivo viene rifiutata invece di essere
    applicata in silenzio. Il senso di quella severita' e' costringere a dichiarare la ragione
    nel momento in cui si esclude, perche' un'esclusione senza motivo e' indistinguibile da una
    dimenticanza il giorno in cui qualcuno la rilegge.

    I due elenchi restano separati e non condivisi, ed e' una scelta dosata: le esclusioni dei
    trattini sono specifiche dei trattini (una tabella di sostituzione, un documento copiato
    verbatim) e non valgono per gli accenti. La duplicazione del LETTORE, invece, e' la terza
    occorrenza della stessa forma in questa famiglia di strumenti, quindi e' il momento in cui
    la regola del tre direbbe di estrarre: non e' stato fatto qui perche' toccare tutti e tre
    gli strumenti per un'estrazione va fatto come passo dichiarato e non dentro la chiusura di
    un'altra voce. Annotato come debito invece che nascosto.
    """
    percorso = os.path.join(ROOT, "tools", "accents-exclude.txt")
    esclusi, malformate = {}, []
    if not os.path.exists(percorso):
        return esclusi, malformate
    with open(percorso, "rb") as f:
        for riga in f.read().decode("utf-8").splitlines():
            riga = riga.strip()
            if not riga or riga.startswith("##"):
                continue
            if "#" not in riga:
                malformate.append(riga)
                continue
            p, motivo = riga.split("#", 1)
            p, motivo = p.strip(), motivo.strip()
            if not p or not motivo:
                malformate.append(riga)
                continue
            esclusi[os.path.normpath(p)] = motivo
    return esclusi, malformate


def autotest():
    """Prove minime dello strumento, eseguibili senza toccare il repository.

    I casi si costruiscono concatenando Q, che è l'apostrofo ottenuto dal suo
    codepoint, invece di scriverlo dentro le stringhe letterali. Così il file di
    questo strumento non contiene le sequenze che lo strumento stesso cerca, e una
    corsa su se stesso non può alterare i propri dati di prova.
    """
    Q = chr(39)
    DQ = chr(34)
    casi = [
        ("Il dato e" + Q + " rotto.", "Il dato \u00e8 rotto."),
        ("perche" + Q + " e" + Q + " cosi" + Q, "perch\u00e9 \u00e8 cos\u00ec"),
        ("E" + Q + " un caso.", "\u00c8 un caso."),
        ("piu" + Q + " di gia" + Q, "pi\u00f9 di gi\u00e0"),
        ("ne" + Q + " l" + Q + "uno ne" + Q + " l" + Q + "altro",
         "n\u00e9 l" + Q + "uno n\u00e9 l" + Q + "altro"),
        ("se" + Q + " stesso", "s\u00e9 stesso"),
        # apostrofi legittimi: non si toccano
        ("un po" + Q + " di tempo", "un po" + Q + " di tempo"),
        ("fa" + Q + " cosi" + Q, "fa" + Q + " cos\u00ec"),
        ("l" + Q + "unita" + Q + " e" + Q + " l" + Q + "area",
         "l" + Q + "unit\u00e0 \u00e8 l" + Q + "area"),
        # elisione: non è un accento e non si tocca
        ("dell" + Q + "area e" + Q + " quella", "dell" + Q + "area \u00e8 quella"),
        # ambiguo: si lascia, salvo il flag
        ("da" + Q + " un risultato", "da" + Q + " un risultato"),
        # regola per suffisso
        ("la modalita" + Q + " e" + Q + " attiva", "la modalit\u00e0 \u00e8 attiva"),
        ("la proprieta" + Q + " di X", "la propriet\u00e0 di X"),
        ("lo segnalera" + Q + " dopo", "lo segnaler\u00e0 dopo"),
        ("si" + Q + " e no", "s\u00ec e no"),
        ("virtu" + Q + " e vizi", "virt\u00f9 e vizi"),
        ("pie" + Q + " di pagina", "pi\u00e8 di pagina"),
        # parola non italiana: la regola non si applica
        ("what" + Q + " resta", "what" + Q + " resta"),
    ]
    # ATTENZIONE: questo blocco contiene di proposito apostrofi che lo strumento non
    # deve toccare. Se una corsa dello strumento su se stesso lo modificasse, il difetto
    # sarebbe nello strumento e non qui: è accaduto una volta, ed è la ragione per cui
    # nella modalità codice il riconoscitore esclude le parole precedute da apostrofo.
    casi_python = [
        # le chiavi fra apici singoli non si toccano, nemmeno se finiscono in vocale
        ("d = {" + Q + "tipo" + Q + ": 1, " + Q + "voci" + Q + ": 2}",
         "d = {" + Q + "tipo" + Q + ": 1, " + Q + "voci" + Q + ": 2}"),
        ("x = " + Q + "meta" + Q, "x = " + Q + "meta" + Q),
        ("# " + Q + "campi" + Q + " e " + Q + "parola" + Q + " restano",
         "# " + Q + "campi" + Q + " e " + Q + "parola" + Q + " restano"),
        # il commento si converte
        ("x = 1  # questo e" + Q + " un commento",
         "x = 1  # questo \u00e8 un commento"),
        # la stringa a doppi apici si converte
        ("t = " + DQ + "il dato e" + Q + " rotto" + DQ,
         "t = " + DQ + "il dato è rotto" + DQ),
        # una parola italiana non preceduta da apostrofo si converte per suffisso
        ("# il valore di personalita" + Q + " conta",
         "# il valore di personalit\u00e0 conta"),
        # e le due cose convivono sulla stessa riga
        ("# " + Q + "tipo" + Q + " e la modalita" + Q + " scelta",
         "# " + Q + "tipo" + Q + " e la modalit\u00e0 scelta"),
    ]
    fallite = 0
    for ingresso, atteso in casi:
        st, re_, am = {}, {}, {}
        ottenuto = converti_prosa(ingresso, st, re_, am)
        if ottenuto != atteso:
            print("  FALLITO  %r -> %r, atteso %r" % (ingresso, ottenuto, atteso))
            fallite += 1
    for ingresso, atteso in casi_python:
        st, re_, am = {}, {}, {}
        ottenuto = converti_python(ingresso, st, re_, am)
        if ottenuto != atteso:
            print("  FALLITO py  %r -> %r, atteso %r" % (ingresso, ottenuto, atteso))
            fallite += 1

    # Fedeltà della segmentazione, compresi recinti e code span.
    doc = ("Prosa con è dentro.\n\n```python\nx = \"è\"\n```\n\n"
           "Altra prosa con `codice è` in linea e più testo.\n")
    tratti = segmenta_markdown(doc)
    if "".join(c for _, c in tratti) != doc:
        print("  FALLITO  la segmentazione non ricompone l'originale")
        fallite += 1
    st, re_, am = {}, {}, {}
    reso = "".join(converti_prosa(c, st, re_, am) if t == "prosa" else c
                   for t, c in tratti)
    if "x = \"è\"" not in reso:
        print("  FALLITO  il blocco di codice è stato toccato")
        fallite += 1
    if "`codice è`" not in reso:
        print("  FALLITO  il code span in linea è stato toccato")
        fallite += 1
    if "Prosa con \u00e8 dentro" not in reso:
        print("  FALLITO  la prosa fuori dai recinti non è stata convertita")
        fallite += 1

    print("autotest: %d casi, %d falliti" % (len(casi) + len(casi_python) + 4, fallite))
    return 1 if fallite else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--autotest", action="store_true", help="esegue le prove interne")
    ap.add_argument("--da-indicativo", action="store_true",
                    help="converte dà nella forma con accento grave. Da usare solo dopo aver letto i contesti e accertato che nessuno sia un imperativo, perché l'imperativo di dare si scrive con l'apostrofo")
    ap.add_argument("percorsi", nargs="*", default=["."])
    # L'interruttore esiste perche' la guardia ha due lati. Dentro un progetto che ospita
    # le copie dei modelli il divieto e' giusto e va imposto. Dentro questo template quei
    # file sono invece gli originali, ed e' proprio li' che vanno corretti: una guardia
    # senza scappatoia avrebbe trasformato una protezione in un difetto nuovo. Il difetto
    # e' stato visto durante la prova della guardia stessa, non dopo.
    ap.add_argument("--includi-modelli", action="store_true",
                    help="permette di scrivere anche sotto .claude/templates/, "
                         "che serve nel template dove quei file sono gli originali")
    ap.add_argument("--check", action="store_true", help="non scrive, riporta")
    ap.add_argument("--residui", action="store_true",
                    help="elenca solo le forme non in lista bianca")
    ap.add_argument("--ext", default=".md,.tex,.txt",
                    help="estensioni da trattare, separate da virgola")
    args = ap.parse_args()
    global MODELLI_AMMESSI
    MODELLI_AMMESSI = args.includi_modelli

    if args.autotest:
        return autotest()

    global DA_INDICATIVO
    DA_INDICATIVO = args.da_indicativo

    estensioni = set(e if e.startswith(".") else "." + e
                     for e in args.ext.split(","))

    # Guardia sui sorgenti, aggiunta il 2026-09-17 dopo un danno reale.
    #
    # Lanciato con `--ext .ts --ext .tsx` su un progetto React, questo strumento ha prodotto
    # settecentotrentasei sostituzioni e **rotto la compilazione**. La causa non e' un caso limite
    # esotico: in un linguaggio con le stringhe fra apici singoli, un letterale come `'che'`
    # termina con la sequenza `e'`, che e' esattamente il bersaglio piu' frequente della tabella.
    # La sostituzione produce `'che` senza chiusura, cioe' `Unterminated string literal`.
    #
    # La lezione, che vale oltre questo strumento: **una regola di prosa applicata a un file che
    # contiene due linguaggi va applicata solo al linguaggio giusto.** E' lo stesso problema gia'
    # risolto per i file di composizione tipografica, dove gli identificatori vengono mascherati
    # prima di operare; qui la soluzione corretta sarebbe distinguere commenti da codice, che
    # richiede un analizzatore sintattico per ogni linguaggio. Finche' non esiste, lo strumento
    # **si rifiuta** invece di fare un lavoro che non sa fare.
    #
    # L'errore era prevedibile e infatti e' stato previsto: chi lo ha lanciato aveva nominato il
    # rischio prima di eseguire e ha verificato subito con il compilatore. Il danno e' stato nullo
    # perche' il codice era committato, ma il presidio non puo' essere la prudenza di chi lancia.
    SORGENTI = {".ts", ".tsx", ".js", ".jsx", ".py", ".java", ".c", ".h", ".cpp", ".cs",
                ".go", ".rb", ".php", ".rs", ".swift", ".kt", ".sql", ".sh", ".ps1"}
    pericolose = sorted(estensioni & SORGENTI)
    if pericolose and not args.check:
        print("rifiutato: estensioni di codice sorgente richieste (%s)."
              % ", ".join(pericolose))
        print("In un linguaggio con stringhe fra apici singoli, un letterale come 'che' finisce")
        print("con la sequenza e', che questo strumento convertirebbe rompendo la stringa.")
        print("Per ispezionare senza scrivere si puo' usare --check; per correggere i commenti")
        print("serve uno strumento che sappia distinguere commenti da codice, che questo non e'.")
        return 2

    file = raccogli(args.percorsi or ["."], estensioni)

    statistiche, residui, ambigui = {}, {}, {}
    cambiati = []

    for percorso in file:
        try:
            cambia, dati = elabora(percorso, statistiche, residui, ambigui)
        except UnicodeDecodeError:
            print("saltato, non è UTF-8: %s" % percorso)
            continue
        if cambia:
            # Difetto preesistente, corretto il 2026-09-23 insieme all'aggiunta delle
            # esclusioni: su Windows `relpath` solleva quando i due percorsi stanno su unita'
            # diverse, quindi lo strumento non poteva essere puntato su una cartella fuori dal
            # repository. Non e' un caso di scuola su questa macchina, dove il repository sta
            # su un'unita' e la cartella temporanea su un'altra, ed e' il modo naturale di
            # provare lo strumento su una copia senza rischiare l'originale. Fuori dalla radice
            # si stampa il percorso assoluto, che e' l'unica cosa sensata da mostrare.
            try:
                rel = os.path.relpath(percorso, ROOT)
            except ValueError:
                rel = os.path.abspath(percorso)
            cambiati.append(rel)
            if not args.check and not args.residui:
                with open(percorso, "wb") as f:
                    f.write(dati)

    if args.residui:
        if residui:
            print("forme con apostrofo non in lista bianca, %d distinte:" % len(residui))
            for k, v in sorted(residui.items(), key=lambda x: -x[1]):
                print("  %-24s x%d" % (k + "'", v))
        else:
            print("nessun residuo")
        return 0

    print("%d file esaminati, %d %s" % (
        len(file), len(cambiati),
        "da modificare" if args.check else "modificati"))
    if statistiche:
        tot = sum(statistiche.values())
        print("\n%d sostituzioni, %d forme distinte:" % (tot, len(statistiche)))
        for k, v in sorted(statistiche.items(), key=lambda x: -x[1])[:25]:
            # La riparazione del residuo non è una conversione e non ha una forma di
            # partenza da mostrare: si dichiara con una riga propria, altrimenti il
            # riquadro le applicherebbe la regola dei suffissi e ne stamperebbe una resa
            # inventata, che è quanto è accaduto alla prima corsa di questa funzione.
            if k == "residuo-apostrofo":
                print("  %-16s    %-26s x%d"
                      % ("(riparazione)", "apostrofo di troppo tolto", v))
                continue
            # La resa va cercata anche nella regola dei suffissi, non solo nelle mappe
            # esplicite: le parole in -ita', -eta' e simili sono convertite dalla regola e
            # non compaiono in ACUTO ne' in GRAVE, quindi senza questo terzo tentativo il
            # report le mostrerebbe come None pur avendole sostituite correttamente.
            reso = ACUTO.get(k) or GRAVE.get(k) or per_suffisso(k) or "?"
            print("  %-16s -> %-16s x%d" % (k + "'", reso, v))
    if ambigui:
        print("\nda decidere a mano, non convertite:")
        for k, v in sorted(ambigui.items()):
            print("  %s' x%d: %s" % (k, v, AMBIGUE[k]))
    if residui:
        print("\n%d forme non riconosciute, rilanciare con --residui per l'elenco"
              % len(residui))
    # In modalita' di verifica l'esito e' anche un codice di uscita, non solo un rapporto. Senza
    # questa riga lo strumento usciva zero pure elencando i file da correggere, e chiunque lo
    # usasse come controllo, l'hook pre-commit o una persona che concatena i comandi, otteneva un
    # via libera indistinguibile da quello vero: il difetto che `skills/prove-che-misurano/RIFERIMENTO.md` chiama
    # vacuita', qui non in una prova ma nel controllo stesso. Fa fede `cambiati`, cioe' cio' che
    # lo strumento sa correggere da se'; le forme ambigue e i residui restano un avviso, perche'
    # nessuno puo' deciderli meccanicamente e farne cadere il controllo lo bloccherebbe per
    # sempre. In modalita' di scrittura l'uscita resta zero: li' correggere e' il lavoro, non un
    # difetto trovato.
    return 1 if (args.check and cambiati) else 0


if __name__ == "__main__":
    sys.exit(main())
