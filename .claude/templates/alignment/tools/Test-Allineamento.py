#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Controllo di allineamento: dice quali affermazioni di un progetto stanno invecchiando
# in silenzio.
#
# Perché ESISTE. Un'affermazione scritta in un documento non ha alcun legame con la
# realtà che descrive: nasce vera, e il momento in cui smette di esserlo non lascia
# traccia da nessuna parte. Il rischio di un progetto documentale non è quindi la
# contraddizione, che si vede, ma l'obsolescenza silenziosa, cioè una scheda che
# descrive correttamente lo stato di tre settimane fa e non dichiara di essere vecchia.
# Nel progetto reale da cui questo strumento è estratto, in una sola mattina se ne sono
# misurate tre insieme, e nessuna era visibile a un lettore attento: una copia di backup
# fuori sede ferma da sei settimane che ogni documento dava per esistente, una scheda
# dello stack che elencava cinque script su ventuno, e una pendenza che dichiarava
# scaduta una cadenza invece rispettata. Nello stesso passaggio si è contato che nei
# file tracciati vivevano sedici date di scadenza scritte in prosa, e che nessun
# meccanismo le guardava: ogni incidente che in quel progetto aveva fatto danno era una
# di quelle date.
#
# IL PRINCIPIO CHE ATTUA, e che va adottato insieme allo strumento perché senza di
# esso il registro resta vuoto: ogni affermazione dei file tracciati deve avere una
# verifica meccanica, una scadenza dichiarata dopo la quale torna automaticamente a
# stato non verificata, oppure una marcatura esplicita di non verificabile con scritte
# accanto la domanda da porre e la persona a cui porla. Non esiste un quarto caso.
#
# COSA CONTROLLA, in quattro famiglie. Le SCADENZE, cioè le date scritte in prosa che
# nessuno guarda. La FRESCHEZZA delle misure, cioè l'eta' di un file di output contro
# la cadenza dichiarata per la fonte che lo produce. Gli INVARIANTI, cioè i confronti
# meccanici fra ciò che i documenti affermano e ciò che sta davvero nel repository. E
# le ASSERZIONI UMANE, quelle che nessun programma può verificare e che ricevono perciò
# una validità dichiarata: quando scade tornano come domanda.
#
# DOVE STANNO I DATI E DOVE STA LA LOGICA. I dati stanno nel registro JSON, tracciato,
# perché una scadenza è un fatto del progetto; la logica sta qui, perché un invariante
# è strutturale. La divisione non è estetica: significa che aggiungere una scadenza non
# richiede di toccare codice, e che aggiungere un invariante non richiede di toccare i
# dati. I percorsi che il progetto usa si dichiarano nel blocco "percorsi" del registro,
# così lo strumento non porta cablata l'anatomia di nessun progetto in particolare.
#
# COSA NON FA, ed è deliberato. Non aggiorna niente e non decide niente: dice che
# un'affermazione è scaduta, non la corregge. Non rinfresca le misure, perché quello
# richiede credenziali e questo controllo deve restare leggibile, veloce e innocuo.
# Non blocca: è rumoroso all'avvio di sessione e basta. Ed esce con codice diverso da
# zero quando trova qualcosa, così che un domani possa diventare bloccante senza
# riscriverlo.
#
# COSA NON STAMPA. Nessun valore reale. Dei file di output legge la sola data di
# modifica, mai il contenuto, quindi nomi host, utenti e indirizzi non entrano
# nell'output nemmeno per errore. Il registro va tenuto pulito allo stesso modo: porta
# date, cadenze e riferimenti a documenti, non importi né identificativi.
#
# Uso:
#   python <percorso>/Test-Allineamento.py               report completo
#   python <percorso>/Test-Allineamento.py --silenzioso  solo il verdetto finale
#   python <percorso>/Test-Allineamento.py --giorni 30   orizzonte delle scadenze mostrate
#   python <percorso>/Test-Allineamento.py --radice X     radice del repository
#   python <percorso>/Test-Allineamento.py --registro Y   percorso del registro JSON
#
# Codici di uscita: 0 allineato, 1 c'è qualcosa di scaduto o arretrato,
# 2 non giudicabile (registro mancante o illeggibile).

import json
import os
import re
import subprocess
import sys
from datetime import date, datetime

REGISTRO_DEFAULT = os.path.join('data', 'scadenze.json')

# Anatomia predefinita, quella di PROJECT-SYSTEM.md. Ogni voce si sovrascrive nel blocco
# "percorsi" del registro: un progetto che tiene le schede altrove non deve toccare il
# codice, e un progetto che non ha una di queste cose la mette a null e l'invariante
# corrispondente si dichiara non applicabile invece di fallire.
PERCORSI_DEFAULT = {
    'schede': '.claude/context',
    'stack': '.claude/context/STACK.md',
    'decisioni': '.claude/memory/decisions.md',
    'script': 'scripts',
    'estensioni_script': ['.ps1', '.py', '.sh', '.mjs', '.js'],
    'registro_voci': None,
    'marcatori_fallimento': None,
}


def risali_alla_radice(partenza):
    """La radice del repository si risale dalla posizione di questo file, non dalla
    cartella corrente.

    La cartella corrente dipende da chi invoca, e chi invoca può essere una sessione,
    un hook, un'attivita' pianificata o un altro script: quattro cartelle diverse per lo
    stesso comando. Si cerca `.git` sia come cartella sia come file, perché in un
    worktree o in un submodulo è un file che punta altrove.
    """
    corrente = os.path.abspath(partenza)
    while True:
        if os.path.exists(os.path.join(corrente, '.git')):
            return corrente
        genitore = os.path.dirname(corrente)
        if genitore == corrente:
            return os.path.abspath(partenza)
        corrente = genitore


def argomento(nome, predefinito=None):
    if nome in sys.argv:
        try:
            return sys.argv[sys.argv.index(nome) + 1]
        except IndexError:
            return predefinito
    return predefinito


RADICE = risali_alla_radice(argomento('--radice') or os.path.dirname(os.path.abspath(__file__)))

# I colori si accendono solo se l'uscita è un terminale vero. Questo controllo gira
# anche dentro un hook e dentro una pipe, dove le sequenze di colore comparirebbero come
# spazzatura in mezzo al testo: un avviso illeggibile è un avviso che non viene letto,
# che è il difetto che questo script esiste per combattere.
ROSSO = GIALLO = VERDE = GRIGIO = FINE = ''
if sys.stdout.isatty():
    ROSSO, GIALLO, VERDE, GRIGIO, FINE = '\033[31m', '\033[33m', '\033[32m', '\033[90m', '\033[0m'
    if os.name == 'nt':
        try:
            import ctypes
            manico = ctypes.windll.kernel32.GetStdHandle(-11)
            modo = ctypes.c_uint32()
            ctypes.windll.kernel32.GetConsoleMode(manico, ctypes.byref(modo))
            ctypes.windll.kernel32.SetConsoleMode(manico, modo.value | 0x0004)
        except Exception:
            ROSSO = GIALLO = VERDE = GRIGIO = FINE = ''


def colora(testo, colore):
    return colore + testo + FINE if colore else testo


def percorso(rel):
    return os.path.join(RADICE, rel.replace('/', os.sep))


def leggi_json(rel):
    with open(percorso(rel), encoding='utf-8-sig') as f:
        return json.load(f)


def testo_di(rel):
    p = percorso(rel)
    if not os.path.exists(p):
        return ''
    try:
        with open(p, encoding='utf-8-sig', errors='replace') as f:
            return f.read()
    except Exception:
        return ''


def giorni_da(iso):
    if not iso:
        return None
    try:
        quando = datetime.strptime(str(iso)[:10], '%Y-%m-%d').date()
    except ValueError:
        return None
    return (date.today() - quando).days


def giorni_a(iso):
    quanti = giorni_da(iso)
    return None if quanti is None else -quanti


def eta_file(rel):
    p = percorso(rel)
    if not os.path.exists(p):
        return None
    return (date.today() - date.fromtimestamp(os.path.getmtime(p))).days


def git(*argomenti):
    try:
        return subprocess.run(['git'] + list(argomenti), cwd=RADICE, capture_output=True,
                              text=True, encoding='utf-8', errors='replace').stdout.strip()
    except Exception:
        return ''


def solo_firma(commit, rel, campi):
    """Vero se quel commit, su quel file, ha toccato i soli campi di firma del frontmatter.

    Serve al confronto del frontmatter, ed è la parte non ovvia di tutto lo strumento.
    Un commit che scrive il solo `last-verified-commit` non cambia la scheda: la firma.
    Contarlo come modifica riporta il confronto in giallo subito dopo ogni bump, cioè
    segnala la sessione proprio per aver rispettato la regola.

    Si guardano le sole righe di diff, quindi un commit che aggiunge una riga di contenuto
    e ribumpa insieme conta come modifica di contenuto, che è il verso prudente
    dell'errore: nel dubbio il controllo segnala.
    """
    diff = git('show', '--format=', '-U0', commit, '--', rel)
    if not diff:
        return False
    cambiate = [r for r in diff.split(chr(10))
                if (r.startswith('+') or r.startswith('-'))
                and not r.startswith('+++') and not r.startswith('---')]
    if not cambiate:
        return False
    atteso = re.compile('^[-+](?:' + '|'.join(re.escape(c) for c in campi) + '):')
    return all(atteso.match(r) for r in cambiate)


def ultima_modifica_di_contenuto(rel, campi):
    """L'hash pieno del commit più recente che ha cambiato il contenuto del file.

    Risale la storia del solo file e salta i commit di sola firma. Si ferma al primo
    commit utile, quindi nel caso normale costa una o due invocazioni di git per scheda.
    """
    storia = [c for c in git('log', '--format=%H', '--', rel).split(chr(10)) if c]
    for commit in storia:
        if not solo_firma(commit, rel, campi):
            return commit
    # Ogni commit del file è di firma: caso teorico (una scheda nata col solo
    # frontmatter), e in quel caso il più antico è la sua nascita.
    return storia[-1] if storia else ''


class Esito(object):
    def __init__(self):
        self.righe = []
        self.problemi = 0
        self.avvisi = 0
        self.controlli = 0

    def ok(self, testo):
        self.righe.append(('ok', testo))
        self.controlli += 1

    def avviso(self, testo):
        self.righe.append(('avviso', testo))
        self.avvisi += 1
        self.controlli += 1

    def grave(self, testo):
        self.righe.append(('grave', testo))
        self.problemi += 1
        self.controlli += 1

    def nota(self, testo):
        self.righe.append(('nota', testo))


# ---------------------------------------------------------------------------
# 1. Scadenze
# ---------------------------------------------------------------------------
def controlla_scadenze(reg, esito, orizzonte):
    lontane = 0
    for voce in sorted(reg.get('scadenze', []), key=lambda v: str(v.get('data', ''))):
        mancano = giorni_a(voce.get('data'))
        etichetta = "%s  %s" % (voce.get('data', '?'), voce.get('cosa', ''))
        preavviso = int(voce.get('preavviso_giorni', 30))
        if mancano is None:
            esito.grave("data illeggibile  %s" % etichetta)
        elif mancano < 0:
            esito.grave("SCADUTA da %d giorni  %s" % (-mancano, etichetta))
            esito.nota("      rompe: %s" % voce.get('rompe', ''))
            esito.nota("      dove:  %s" % voce.get('dove', ''))
        elif mancano <= preavviso:
            esito.avviso("fra %d giorni  %s" % (mancano, etichetta))
            esito.nota("      rompe: %s" % voce.get('rompe', ''))
            esito.nota("      dove:  %s" % voce.get('dove', ''))
        elif mancano <= orizzonte:
            esito.ok("fra %d giorni  %s" % (mancano, etichetta))
        else:
            lontane += 1
            esito.controlli += 1
    if lontane:
        esito.nota("      %d scadenze oltre l'orizzonte di %d giorni: contate e non elencate" % (lontane, orizzonte))


# ---------------------------------------------------------------------------
# 2. Freschezza delle misure
# ---------------------------------------------------------------------------
def controlla_freschezza(reg, esito, percorsi):
    # I marcatori di rinfresco fallito, se il progetto ha un'automazione che li scrive.
    # Un'automazione che fallisce in silenzio produce fiducia mal riposta, che è peggio
    # dell'assenza di automazione: la misura resta quella vecchia e la sua età compare
    # qui sotto, ma il fatto che il rinfresco non stia più funzionando va detto a parte,
    # perché l'eta' da sola non lo spiega.
    marcatori = percorsi.get('marcatori_fallimento')
    if marcatori:
        cartella = percorso(marcatori.get('cartella', 'output'))
        prefisso = marcatori.get('prefisso', '.refresh-fallito-')
        if os.path.isdir(cartella):
            for nome in sorted(n for n in os.listdir(cartella) if n.startswith(prefisso)):
                rel = marcatori.get('cartella', 'output') + '/' + nome
                fonte = nome[len(prefisso):]
                if fonte.endswith('.txt'):
                    fonte = fonte[:-4]
                motivo = ''
                for riga in testo_di(rel).splitlines():
                    if riga.startswith('Motivo:'):
                        motivo = riga.split(':', 1)[1].strip()
                        break
                esito.grave("RINFRESCO FALLITO da %s giorni  fonte %s" % (eta_file(rel), fonte))
                esito.nota("      motivo: %s" % motivo)
                esito.nota("      la misura precedente non è stata toccata: è l'ultima buona")

    for voce in reg.get('freschezza', []):
        rel = voce.get('percorso', '')
        cadenza = int(voce.get('cadenza_giorni', 30))
        nome = voce.get('cosa', voce.get('id', rel))
        eta = None
        # Un file può dichiarare dentro di sé la data della misura, che è più
        # attendibile della data di modifica quando il file viene riscritto per altro.
        if voce.get('campo_data'):
            try:
                dati = leggi_json(rel)
            except Exception:
                dati = None
            if dati is not None:
                eta = giorni_da(dati.get(voce['campo_data']))
        if eta is None:
            eta = eta_file(rel)
        if eta is None:
            esito.grave("misura ASSENTE  %s  (%s)" % (nome, rel))
            continue
        if eta > cadenza * 2:
            esito.grave("misura di %d giorni, cadenza %d  %s" % (eta, cadenza, nome))
            esito.nota("      %s" % voce.get('dove', ''))
        elif eta > cadenza:
            esito.avviso("misura di %d giorni, cadenza %d  %s" % (eta, cadenza, nome))
            esito.nota("      %s" % voce.get('dove', ''))
        else:
            esito.ok("misura di %d giorni, cadenza %d  %s" % (eta, cadenza, nome))


# ---------------------------------------------------------------------------
# 3. Invarianti: la logica sta qui, non nel registro, perché sono strutturali
# ---------------------------------------------------------------------------
def file_tracciati():
    elenco = git('ls-files')
    return [r for r in elenco.split(chr(10)) if r] if elenco else []


def invariante_script(esito, percorsi):
    """Ogni script presente deve essere citato nella scheda dello stack.

    Il difetto che questo invariante trova non è teorico: nel progetto di origine la
    scheda dello stack elencava cinque script su ventuno, e nessuno se n'era accorto
    perché una scheda incompleta si legge esattamente come una completa.
    """
    rel_stack = percorsi.get('stack')
    rel_script = percorsi.get('script')
    if not rel_stack or not rel_script:
        esito.nota("      inventario degli script: non applicabile, percorsi non dichiarati")
        return
    cartella = percorso(rel_script)
    if not os.path.isdir(cartella):
        esito.nota("      inventario degli script: la cartella %s non esiste" % rel_script)
        return
    stack = testo_di(rel_stack)
    if not stack:
        esito.grave("%s non leggibile: l'inventario degli script non è verificabile" % rel_stack)
        return
    estensioni = tuple(percorsi.get('estensioni_script') or PERCORSI_DEFAULT['estensioni_script'])
    presenti = sorted(n for n in os.listdir(cartella)
                      if os.path.isfile(os.path.join(cartella, n))
                      and os.path.splitext(n)[1] in estensioni)
    mancanti = [n for n in presenti if n not in stack]
    if mancanti:
        esito.grave("%d script presenti in %s e non citati in %s"
                    % (len(mancanti), rel_script, os.path.basename(rel_stack)))
        for n in mancanti:
            esito.nota("      %s" % n)
    else:
        esito.ok("tutti i %d script di %s sono citati in %s"
                 % (len(presenti), rel_script, os.path.basename(rel_stack)))


def invariante_decisioni(esito, percorsi, tracciati):
    """Ogni decisione richiamata deve esistere nel registro delle decisioni.

    Un richiamo a una decisione inesistente è peggio di un richiamo assente, perché
    fa credere che la ragione sia scritta da qualche parte.
    """
    rel = percorsi.get('decisioni')
    if not rel:
        esito.nota("      registro delle decisioni: non applicabile, percorso non dichiarato")
        return
    decisioni = testo_di(rel)
    if not decisioni:
        esito.nota("      registro delle decisioni: %s non esiste ancora" % rel)
        return
    definiti = set(re.findall(r'^##\s+(ADR-\d+)', decisioni, re.M))
    citati = set()
    for altro in tracciati:
        if altro.endswith('.md') and altro != rel:
            citati.update(re.findall(r'\bADR-\d+\b', testo_di(altro)))
    orfani = sorted(citati - definiti)
    if orfani:
        esito.grave("%d decisioni richiamate e non definite in %s: %s"
                    % (len(orfani), os.path.basename(rel), ', '.join(orfani)))
    else:
        esito.ok("le %d decisioni richiamate sono tutte definite" % len(citati))


def invariante_registro_voci(esito, percorsi, tracciati):
    """Un registro numerato non assegna due volte lo stesso numero, e i richiami non
    puntano oltre il suo massimo.

    Nasce da una collisione reale: due voci diverse, scritte lo stesso giorno da due
    sessioni di lavoro che non sapevano di condividere il file, sono arrivate in un
    commit con lo stesso numero e lo stesso identificatore. Non è un difetto di forma:
    il numero è il modo in cui ogni documento si riferisce a una voce, quindi due voci
    allo stesso numero rendono ambiguo ogni richiamo, quello esistente e quello futuro.

    Il numero non ammette eccezioni e la sua collisione è perciò rossa.
    L'identificatore ne ammette due, dichiarate, ed è la ragione per cui il suo esito è
    un avviso: una riga di aggiornamento che porta un parentetico nella cella, e una riga
    di seguito numerata con un suffisso di lettera. Senza quelle due tolleranze il
    controllo segnalerebbe voci legittime a ogni esecuzione, e un controllo che segnala
    sempre la stessa cosa insegna a ignorarlo.
    """
    rel = percorsi.get('registro_voci')
    if not rel:
        return
    corpo = testo_di(rel)
    if not corpo:
        esito.nota("      registro numerato: %s non leggibile" % rel)
        return
    righe = re.findall(r'^\|\s*(\d+[a-z]?)\s*\|\s*([^|]*)\|', corpo, re.M)
    if not righe:
        esito.nota("      registro numerato: nessuna riga riconosciuta in %s" % rel)
        return

    per_numero = {}
    per_id = {}
    for numero, cella in righe:
        per_numero[numero] = per_numero.get(numero, 0) + 1
        cella = cella.strip()
        if '(' in cella:
            continue
        trovato = re.match(r'^\*{0,2}([A-Z]{2,6}-\d+[a-z]*)', cella)
        if trovato:
            per_id.setdefault(trovato.group(1), []).append(numero)

    def radice_numerica(n):
        return int(re.match(r'\d+', n).group())

    ripetuti = sorted((n for n, quanti in per_numero.items() if quanti > 1),
                      key=lambda n: (radice_numerica(n), n))
    if ripetuti:
        esito.grave("%d numeri assegnati a più di una voce di %s: %s"
                    % (len(ripetuti), os.path.basename(rel), ', '.join('#' + n for n in ripetuti)))
        esito.nota("      un numero vale per una voce sola: ogni richiamo a un numero doppio è ambiguo")
        esito.nota("      si rinumera la voce più recente, che è quella con meno richiami da rompere")
    else:
        esito.ok("i %d numeri del registro sono tutti distinti" % len(per_numero))

    collisi = []
    for identificativo, numeri in sorted(per_id.items()):
        if len(numeri) > 1 and len(set(radice_numerica(n) for n in numeri)) > 1:
            collisi.append((identificativo, sorted(numeri, key=lambda n: (radice_numerica(n), n))))
    if collisi:
        esito.avviso("%d identificatori portati da voci diverse del registro" % len(collisi))
        for identificativo, numeri in collisi:
            esito.nota("      %-12s su %s" % (identificativo, ', '.join('#' + n for n in numeri)))
        esito.nota("      due voci distinte con lo stesso nome: da guardare, non da rinominare a scatola chiusa")
    else:
        esito.ok("nessun identificatore è portato da due voci distinte")

    massimo = max(radice_numerica(n) for n in per_numero)
    # L'ampiezza del richiamo si dichiara, e il default è stretto per una ragione misurata:
    # allargandolo a quattro cifre, su un corpus reale, il controllo ha segnalato come
    # richiamo a una voce inesistente il numero di un ticket di un sistema esterno citato in
    # prosa. Un invariante che inventa un falso positivo la prima volta che viene eseguito
    # perde la fiducia di chi lo legge, e la perde per sempre. Un progetto che numera oltre
    # il migliaio allarga questa finestra dichiarandolo.
    cifre = percorsi.get('richiami_cifre') or [2, 3]
    atteso = r'#(\d{%d,%d})\b' % (int(cifre[0]), int(cifre[-1]))
    citati = set()
    for altro in tracciati:
        if altro.endswith('.md'):
            citati.update(re.findall(atteso, testo_di(altro)))
    oltre = sorted((n for n in citati if int(n) > massimo), key=int)
    if oltre:
        # Avviso e non diagnosi: un registro cresciuto per fasi può portare anche una
        # numerazione per sezione che convive con quella principale e non è un errore.
        # Uno strumento che non sa distinguere i due mondi lo dichiara, invece di
        # decidere al posto di chi legge.
        # L'elenco si tronca, e non è pigrizia. Se il massimo del registro è molto più
        # basso dei numeri citati intorno, per esempio perché il percorso dichiarato punta
        # al file sbagliato, questa riga stampa cento voci e affoga tutto il resto del
        # report: un avviso illeggibile è un avviso che non viene letto, che è il difetto
        # che questo strumento esiste per combattere.
        mostrati = oltre[:12]
        coda = '' if len(oltre) == len(mostrati) else ' e altri %d' % (len(oltre) - len(mostrati))
        esito.avviso("%d richiami oltre il massimo del registro (#%d): %s%s"
                     % (len(oltre), massimo, ', '.join('#' + n for n in mostrati), coda))
        esito.nota("      possono essere riferimenti a una numerazione per sezione: da guardare")
        if len(oltre) > 12:
            esito.nota("      se sono molti, il sospetto è il percorso: registro_voci punta al file giusto?")
    else:
        esito.ok("nessun richiamo oltre il massimo definito (#%d)" % massimo)


def invariante_frontmatter(esito, percorsi):
    """Il frontmatter di una scheda deve dichiarare un commit a partire dal quale il
    contenuto della scheda non è più cambiato.

    Questo invariante è stato sbagliato due volte prima di essere giusto, e vale la pena
    conservare entrambi gli errori perché sono istruttivi.

    Il primo confrontava il campo con HEAD: segnalava tutte le schede dopo qualunque
    commit, anche uno che non le riguardava, cioè un giallo perpetuo.

    Il secondo confrontava il campo con il commit che aveva toccato la scheda per ultimo.
    Meglio, e ancora impossibile: la regola prescrive di bumpare dopo il commit, ma il
    bump scrive dentro la scheda, quindi genera un commit nuovo che la tocca e riporta il
    confronto in giallo. Una sessione veniva segnalata per aver rispettato la regola, che
    è la forma peggiore di avviso perpetuo perché punisce il comportamento corretto.

    La distinzione che scioglie il nodo è fra una modifica e una firma. Il controllo
    salta i commit di sola firma, trova l'ultima modifica di contenuto, e verifica per
    discendenza e non per uguaglianza: la scheda è allineata se l'hash dichiarato è
    quel commit o un suo discendente. Così resta verde anche chi rilegge una scheda
    immutata a una data successiva e porta l'hash in avanti, che è esattamente ciò che
    la regola del bump chiede di fare.
    """
    rel_schede = percorsi.get('schede')
    if not rel_schede:
        esito.nota("      frontmatter delle schede: non applicabile, percorso non dichiarato")
        return
    cartella = percorso(rel_schede)
    if not os.path.isdir(cartella):
        esito.nota("      frontmatter delle schede: la cartella %s non esiste" % rel_schede)
        return

    campi = percorsi.get('campi_firma') or ['last-verified-commit', 'last-verified']

    # Il percorso si estrae separando sul primo spazio, non tagliando a posizione fissa:
    # il taglio a posizione fissa si rompe perché l'output viene normalizzato e lo spazio
    # iniziale della prima riga sparisce, sfasando quella sola riga di un carattere. Nel
    # caso di una rinomina la porcelain scrive "vecchio -> nuovo": interessa il nuovo.
    sporche = set()
    for riga in git('status', '--porcelain').split(chr(10)):
        riga = riga.strip()
        if not riga:
            continue
        pezzi = riga.split(None, 1)
        if len(pezzi) < 2:
            continue
        candidato = pezzi[1].strip().strip('"')
        if ' -> ' in candidato:
            candidato = candidato.split(' -> ', 1)[1].strip().strip('"')
        sporche.add(candidato)

    atteso = re.compile('^(?:' + '|'.join(re.escape(c) for c in campi) + r'):\s*(\S+)', re.M)
    disallineate = []
    illeggibili = []
    quante = 0
    for nome in sorted(n for n in os.listdir(cartella) if n.endswith('.md')):
        rel = rel_schede + '/' + nome
        trovato = atteso.search(testo_di(rel))
        if not trovato:
            continue
        quante += 1
        dichiarato = trovato.group(1)
        if rel in sporche:
            # Modificata e non ancora committata: il bump si valuta al commit, non ora.
            continue
        contenuto = ultima_modifica_di_contenuto(rel, campi)
        if not contenuto:
            continue
        pieno = git('rev-parse', '--verify', dichiarato + '^{commit}')
        if not pieno:
            # Un hash che non risolve non è un disallineamento ma un riferimento rotto:
            # o è stato scritto a mano sbagliato, o la storia è stata riscritta sotto.
            illeggibili.append((nome, dichiarato))
            continue
        discende = subprocess.run(['git', 'merge-base', '--is-ancestor', contenuto, pieno],
                                  cwd=RADICE, capture_output=True).returncode == 0
        if not discende:
            disallineate.append((nome, dichiarato, contenuto[:7]))

    if illeggibili:
        esito.grave("%d schede dichiarano un commit che non esiste nella storia" % len(illeggibili))
        for nome, dichiarato in illeggibili:
            esito.nota("      %-26s dichiara %s, che non risolve" % (nome, dichiarato))
    if disallineate:
        esito.avviso("%d schede il cui contenuto è cambiato dopo il commit dichiarato" % len(disallineate))
        for nome, dichiarato, contenuto in disallineate:
            esito.nota("      %-26s dichiara %s, contenuto cambiato in %s" % (nome, dichiarato, contenuto))
        esito.nota("      il bump va fatto dopo aver riletto la scheda, non in blocco: l'hash dichiara una rilettura")
    if not disallineate and not illeggibili:
        if quante:
            esito.ok("il frontmatter delle %d schede copre l'ultima modifica di contenuto" % quante)
        else:
            esito.nota("      frontmatter delle schede: nessuna scheda porta un campo di firma")


def controlla_invarianti(esito, percorsi):
    tracciati = file_tracciati()
    if not tracciati:
        esito.grave("git non risponde: gli invarianti non sono calcolabili")
        return
    invariante_script(esito, percorsi)
    invariante_decisioni(esito, percorsi, tracciati)
    invariante_registro_voci(esito, percorsi, tracciati)
    invariante_frontmatter(esito, percorsi)


# ---------------------------------------------------------------------------
# 4. Asserzioni umane
# ---------------------------------------------------------------------------
def controlla_asserzioni(reg, esito):
    for voce in reg.get('asserzioni_umane', []):
        eta = giorni_da(voce.get('verificata_il'))
        validita = int(voce.get('validita_giorni', 30))
        testa = "%s  %s" % (voce.get('stato', '?'), voce.get('afferma', ''))
        if eta is None:
            esito.avviso("MAI VERIFICATA  %s" % voce.get('afferma', ''))
            esito.nota("      chiedere a %s: %s" % (voce.get('a_chi', '?'), voce.get('domanda', '')))
            esito.nota("      dove:  %s" % voce.get('dove', ''))
        elif eta > validita:
            esito.avviso("verificata %d giorni fa, validità %d  %s" % (eta, validita, voce.get('afferma', '')))
            esito.nota("      chiedere a %s: %s" % (voce.get('a_chi', '?'), voce.get('domanda', '')))
        else:
            esito.ok("verificata %d giorni fa  %s" % (eta, testa))


# ---------------------------------------------------------------------------
def stampa(titolo, esito, silenzioso):
    if silenzioso:
        return
    print('')
    print(titolo)
    print('-' * 78)
    if not esito.righe:
        print(colora('  nessuna voce', GRIGIO))
    for tipo, testo in esito.righe:
        if tipo == 'grave':
            print(colora('  ' + testo, ROSSO))
        elif tipo == 'avviso':
            print(colora('  ' + testo, GIALLO))
        elif tipo == 'ok':
            print(colora('  ' + testo, VERDE))
        else:
            print(colora(testo, GRIGIO))


def main():
    silenzioso = '--silenzioso' in sys.argv
    orizzonte = 120
    try:
        orizzonte = int(argomento('--giorni', orizzonte))
    except (TypeError, ValueError):
        pass
    rel_registro = argomento('--registro') or REGISTRO_DEFAULT

    if not os.path.exists(percorso(rel_registro)):
        print(colora("NON GIUDICABILE: manca %s, il registro delle affermazioni che invecchiano." % rel_registro, ROSSO))
        print("Senza quel file questo controllo non ha nulla da verificare, e un verde non calcolato")
        print("sarebbe peggio di un rosso: si ferma qui invece di dichiararsi allineato.")
        return 2
    try:
        reg = leggi_json(rel_registro)
    except Exception as errore:
        print(colora("NON GIUDICABILE: %s non è leggibile (%s)" % (rel_registro, errore), ROSSO))
        return 2

    percorsi = dict(PERCORSI_DEFAULT)
    percorsi.update(reg.get('percorsi', {}) or {})

    if not silenzioso:
        print('')
        print("Allineamento - registro revisione %s, aggiornato al %s"
              % (reg.get('revisione', '?'), reg.get('aggiornato', '?')))

    scadenze, freschezza, invarianti, asserzioni = Esito(), Esito(), Esito(), Esito()
    controlla_scadenze(reg, scadenze, orizzonte)
    controlla_freschezza(reg, freschezza, percorsi)
    controlla_invarianti(invarianti, percorsi)
    controlla_asserzioni(reg, asserzioni)

    stampa("SCADENZE  (entro %d giorni; le più lontane sono contate e non elencate)" % orizzonte, scadenze, silenzioso)
    stampa("FRESCHEZZA DELLE MISURE  (età della misura contro la cadenza dichiarata)", freschezza, silenzioso)
    stampa("INVARIANTI  (ciò che i documenti affermano contro ciò che c'è davvero)", invarianti, silenzioso)
    stampa("ASSERZIONI UMANE  (nessun programma può verificarle: sono domande)", asserzioni, silenzioso)

    gravi = sum(e.problemi for e in (scadenze, freschezza, invarianti, asserzioni))
    avvisi = sum(e.avvisi for e in (scadenze, freschezza, invarianti, asserzioni))
    controlli = sum(e.controlli for e in (scadenze, freschezza, invarianti, asserzioni))
    voci = sum(len(reg.get(chiave, []) or []) for chiave in ('scadenze', 'freschezza', 'asserzioni_umane'))

    print('')
    print('-' * 78)
    if not voci:
        # Un registro vuoto non è un progetto allineato, è un progetto che non ha ancora
        # dichiarato nulla. Dirlo verde sarebbe il difetto che questo strumento combatte:
        # un esito che sembra calcolato e non lo è. Gli invarianti valgono comunque, perché
        # si calcolano sul repository e non sul registro.
        print(colora("REGISTRO VUOTO: nessuna scadenza, cadenza o asserzione dichiarata.", GIALLO))
        if controlli:
            print(colora("  Sono stati calcolati i soli invarianti, %d controlli: del registro non c'era nulla da" % controlli, GRIGIO))
            print(colora("  guardare.", GRIGIO))
        else:
            print(colora("  Nemmeno gli invarianti sono applicabili qui: i percorsi dichiarati non esistono in", GRIGIO))
            print(colora("  questo repository, e sono elencati sopra come non applicabili.", GRIGIO))
        print(colora("  Le voci di esempio del pacchetto sono inerti di proposito: si copiano dentro gli array", GRIGIO))
        print(colora("  quando si scrive la prima voce vera.", GRIGIO))
        return 1 if gravi else 0
    if gravi:
        print(colora("ROTTO: %d voci già rotte e %d che stanno invecchiando, su %d controlli."
                     % (gravi, avvisi, controlli), ROSSO))
        return 1
    if avvisi:
        # Il giallo non marca la sessione come fallita, ed è una scelta: un controllo che
        # fallisce sempre smette di essere letto, e questo gira a ogni avvio.
        print(colora("DA GUARDARE: %d voci su %d controlli, nessuna già rotta." % (avvisi, controlli), GIALLO))
        print(colora("  Ciascuna è un'affermazione che sta invecchiando, e l'unico modo in cui fa", GRIGIO))
        print(colora("  danno è che nessuno la legga.", GRIGIO))
        return 0
    print(colora("ALLINEATO: %d controlli, nessuna affermazione scaduta." % controlli, VERDE))
    return 0


if __name__ == '__main__':
    sys.exit(main())
