#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Legge la cronologia di un canale Discord tramite un bot account ufficiale.

Perché esiste, e che problema risolve davvero
---------------------------------------------
Per certe tecniche, in certi domini, un canale di conversazione di community è la sola
documentazione esistente, e la norma `.claude/skills/fonti-non-recuperabili/RIFERIMENTO.md` lo
registra fra le fonti che nessuno strumento di sessione raggiunge. Le vie di accesso sono
tre e vanno tenute distinte, perché differiscono sul piano delle regole prima che su
quello tecnico.

La prima è il token del proprio account personale, cioè il self-bot: automatizzare un
account utente è vietato dalle condizioni d'uso di Discord e la sanzione dichiarata è la
terminazione dell'account, senza distinzione di intenzioni. La seconda è la copia manuale
dei messaggi pertinenti, che funziona sempre e non richiede il permesso di nessuno.

La terza è quella che questo strumento implementa: un bot account creato nel portale per
sviluppatori di Discord. Non è un modo di aggirare la regola sui self-bot, è la porta che
Discord ha costruito per l'automazione, con una API pubblica, documentata e con limiti di
frequenza pensati per traffico automatico. La distinzione poggia su fatti verificabili e
non su una interpretazione: tipo di token diverso, accesso subordinato a un invito
autorizzato, contrassegno visibile a tutti, e rischio che ricade sull'applicazione invece
che sull'account personale.

Il limite di questa via, che va conosciuto prima di allestirla
--------------------------------------------------------------
Un bot entra in un server soltanto se qualcuno con il permesso di gestione del server lo
invita, e non esiste alcuna altra via perché è l'unico flusso che l'API preveda. Per un
server di cui non si è amministratori la via richiede quindi il consenso di terzi: non è
un ostacolo tecnico aggirabile con una configurazione, è il meccanismo di consenso su cui
poggia la legittimità dell'intera via. Chiedere è gratis e va fatto; ricevere un no è un
esito possibile, e in quel caso resta la copia manuale.

Va detto anche il rovescio, perché è la parte che si scopre dopo aver allestito tutto: il
cancello non è sui dati ma sul bot. I messaggi di un canale di cui si è membri sono già
visibili a chi guarda, e nessuno autorizza a leggere ciò che il server mostra già; ciò che
l'invito autorizza è far entrare una seconda identità dentro quel server. È questo che
richiede il consenso, ed è corretto che lo richieda.

Come si allestisce, una volta sola
----------------------------------
1. Su https://discord.com/developers/applications si crea una applicazione e, nella
   sezione Bot, il bot; si copia il token, che va trattato come una password e che il
   portale mostra una volta sola.
2. Nella stessa sezione si abilita Message Content Intent, senza il quale Discord
   consegna i messaggi privi di testo anche a un bot che ha i permessi. La soglia oltre la
   quale quell'intent richiede una revisione è di diecimila utenti, non di cento server:
   i cento server sono la soglia della verifica formale dell'applicazione, che è cosa
   diversa, e confondere le due porta a credere di dover chiedere un'approvazione che non
   serve. Requires OAuth2 Code Grant va lasciato spento, perché romperebbe l'invito. Su
   Public Bot la scelta dipende da chi deve invitare il bot e la sezione seguente la
   spiega: spento soltanto il proprietario dell'applicazione può installarla, quindi un
   amministratore di un server altrui non potrebbe farlo.
3. Si genera l'URL di invito con i soli permessi di lettura, cioè View Channels e Read
   Message History, che sommati danno 66560, ossia 1024 più 65536. Lo strumento non scrive
   nulla e non ha bisogno di altro.
4. Si invita il bot nel server, che richiede di esserne amministratori o di ottenere il
   consenso di chi lo è.
5. Il token va in `.env` nella radice del progetto, che il `.gitignore` esclude:

       DISCORD_BOT_TOKEN=...

   Dove le regole di permesso del progetto negano i percorsi che corrispondono a `.env*`,
   e nel sistema di progetto di questo template lo fanno, l'agente non può creare né
   leggere quel file nemmeno come modello: va scritto a mano, e la variabile che serve è
   quella sola.

L'unica operazione che non è una lettura, e perché esiste
---------------------------------------------------------
Il comando `leave` fa uscire il bot da un server, e va dichiarato perché è la sola cosa che
questo strumento fa oltre a leggere. Esiste per una conseguenza dell'allestimento che non è
evidente: perché un amministratore di un server altrui possa invitare il bot,
l'applicazione deve essere pubblica, e con essa pubblica chiunque abbia il link di invito
può aggiungerla a un proprio server. Da un server di cui non si è amministratori non si può
cacciare il proprio bot, quindi la sola via è che il bot esca da sé.

Conviene tenere l'applicazione pubblica soltanto mentre le richieste di invito sono in
corso, e rimetterla privata quando gli inviti sono stati concessi: il comando `guilds` dice
in ogni momento dove il bot si trova, e un server inatteso in quell'elenco è il segnale che
serve. Se l'applicazione sia pubblica lo dice il comando `stato`, che legge la
configurazione dal servizio e non dalla schermata del portale: una schermata mostra ciò che
il browser ha in cache, e un salvataggio non premuto ha l'aspetto di uno premuto. Il comando pretende `--conferma`, perché l'uscita non si annulla da qui e il
rientro richiede un invito nuovo.

Il presidio contro l'uso di un token personale
----------------------------------------------
Questo strumento invia sempre l'intestazione di autorizzazione nella forma prevista per i
bot, e prima di qualunque lettura interroga l'endpoint dell'identità corrente per
verificare che l'account autenticato sia dichiarato un bot. Se non lo è, si arresta e
spiega perché, invece di procedere: un token utente inserito per errore in quella
variabile non produce una lettura riuscita ma un rifiuto. È un presidio deliberato e non
va rimosso, perché la differenza fra le due vie non è visibile nell'esito di una singola
richiesta ma nelle conseguenze sull'account.

Il principio che quel presidio esemplifica vale oltre il caso, e governa anche il
controllo degli identificativi e quello della data: un presidio va collocato nel punto in
cui l'errore si produce e non in quello in cui si manifesta.

Uso
---
    python tools/fetch-discord.py stato
    python tools/fetch-discord.py guilds
    python tools/fetch-discord.py channels <id del server>
    python tools/fetch-discord.py fetch <id del canale> --limit 500
    python tools/fetch-discord.py fetch <id del canale> --limit 0 --nuovi
    python tools/fetch-discord.py fetch <id del canale> --grep "link cable" --grep checksum
    python tools/fetch-discord.py fetch <id> --append --out _notes/fonti/2026-01-31-canale.md
    python tools/fetch-discord.py leave <id del server> --conferma
    python tools/fetch-discord.py --self-test

`--limit 0` significa nessun tetto, e ha senso soltanto insieme a `--nuovi`: senza cursore
scaricherebbe la cronologia intera di un canale, che su un canale attivo sono decine di
migliaia di messaggi e altrettante decine di richieste.

`--nuovi` legge soltanto ciò che è arrivato dopo l'ultima lettura riuscita di quel canale,
usando il cursore conservato in `_notes/.discord-cursori.json`, che sta sotto `_notes/` e
quindi fuori dal version control. Il cursore avanza fino all'ultimo messaggio letto e non
all'ultimo scritto, cosicché un filtro restrittivo non faccia rileggere ogni volta i
messaggi che ha scartato.

Che cosa questo strumento fa contro un canale vero
--------------------------------------------------
Un canale di prova non esercita nulla di ciò che rompe un lettore, quindi le difese qui
sotto sono state scritte guardando la documentazione dell'API e provate contro un
trasporto finto, non contro un canale affollato.

Limiti di frequenza, in due modi. Il modo reattivo è la risposta di rifiuto, dove si
attende quanto il servizio dichiara e si riprova. Il modo preventivo, che è quello che
evita di arrivare al rifiuto, legge a ogni risposta le intestazioni con cui il servizio
dichiara quante richieste restano nella finestra corrente e fra quanto la finestra si
azzera: quando le richieste residue sono zero si attende prima di proseguire, invece di
tirare fino al rifiuto.

Guasti transitori. Un errore di rete, un timeout o una risposta di errore del servizio
non sono un motivo per fermarsi a metà di una cronologia: si riprova con attesa
crescente, e si abbandona soltanto dopo un numero dichiarato di tentativi, riferendo
l'ultimo esito invece di un messaggio generico.

Discussioni e forum. Nelle community di sviluppo la conoscenza sta spesso in una
discussione dentro un canale, o in un post di un forum, che nell'API sono a loro volta
canali con un proprio identificativo. Il comando che elenca i canali elenca anche le
discussioni attive, e la lettura funziona su un identificativo di discussione come su
quello di un canale.

Contenuto che non è testo. Un messaggio può portare il proprio contenuto in un blocco
incorporato invece che nel testo, e in un canale tecnico capita spesso, per esempio con
l'anteprima di un collegamento o con l'uscita di un altro bot. La resa include titolo,
descrizione, campi e collegamento dei blocchi incorporati, e la citazione del messaggio a
cui una risposta si riferisce, perché in una discussione tecnica la catena delle risposte
è metà del significato. Anche i filtri guardano quel contenuto e non il solo testo, perché
altrimenti scarterebbero per lunghezza un messaggio che di contenuto ne ha.

Integrità del file prodotto. Il testo di un messaggio è contenuto di terzi e può
cominciare con un cancelletto: senza precauzione quel messaggio diventerebbe
un'intestazione e romperebbe la struttura della nota. Le righe che aprono con un
cancelletto vengono quindi protette, tranne dentro un blocco di codice recintato, dove il
cancelletto appartiene al linguaggio e non alla struttura del documento.

Stato di collaudo
-----------------
La logica è provata con `--self-test`, che la esercita contro un trasporto finto e
comprende controlli negativi, cioè verifiche che fallirebbero se un presidio venisse
rimosso: il rifiuto di un token non di bot, il riconoscimento locale di un identificativo
non numerico e di una data mal scritta, e la protezione delle righe che aprono con un
cancelletto.

Il flusso è stato eseguito contro il servizio su un progetto reale, su un server di prova
di proprietà di chi lo conduceva, e ha funzionato in tutti i suoi passi: elenco dei
server, elenco dei canali di testo e delle discussioni attive, lettura della cronologia
con il testo dei messaggi presente, filtro per parola chiave, aggiunta in coda a un file
esistente, e cursore che alla corsa successiva riferisce correttamente che non c'è nulla di
nuovo. Da quella corsa vengono due osservazioni che vale registrare. La prima è che fra i
messaggi letti compare anche la riga di sistema che annuncia l'ingresso del bot nel
canale, perché per il servizio è un messaggio come gli altri; chi vuole escluderla usa
`--min-length`. La seconda è che il messaggio di errore del servizio, quando
l'identificativo non è un numero, è quattrocento con la dicitura sul corpo della richiesta
non valido, che non nomina il campo: è la ragione per cui il controllo
dell'identificativo è stato spostato in locale.

Resta non osservato sul servizio ciò che un server di prova non può esercitare, cioè
l'impaginazione su una cronologia più lunga di cento messaggi, l'attesa preventiva e
quella dopo un rifiuto per eccesso di frequenza, la ripresa dopo un guasto transitorio, e
la lettura di una discussione o di un post di forum. Tutto questo è provato contro il
trasporto finto e nessuna di quelle situazioni è stata vista sul campo: la distinzione fra
i due stati va conservata e non appianata.
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CURSORI = os.path.join(ROOT, "_notes", ".discord-cursori.json")
BASE = "https://discord.com/api/v10"

# Il numero massimo di messaggi che l'API restituisce in una sola richiesta. Non è una
# scelta di questo strumento ma un limite del servizio, e determina il numero di richieste
# necessarie a leggere una cronologia: mille messaggi costano dieci richieste.
PER_PAGINA = 100

# Quante volte si riprova prima di arrendersi, sia dopo un rifiuto per eccesso di
# frequenza sia dopo un guasto transitorio. Il servizio dichiara quanti secondi attendere
# nel primo caso, quindi il numero di tentativi non serve a indovinare l'attesa ma a non
# restare in un ciclo indefinito; nel secondo l'attesa è nostra e cresce.
TENTATIVI = 6

# L'attesa iniziale dopo un guasto transitorio, che raddoppia a ogni tentativo fino al
# tetto. Il tetto esiste perché un'attesa che cresce senza limite trasforma un guasto in
# un blocco silenzioso.
ATTESA_INIZIALE = 1.0
ATTESA_MASSIMA = 30.0

# I tipi di canale che questo strumento sa leggere, con la loro etichetta. I numeri sono
# quelli dell'API e non vanno tradotti; l'etichetta serve a chi legge l'elenco. Le
# discussioni sono canali a tutti gli effetti e si leggono con il medesimo comando.
TIPI_CANALE = {
    0: "testo",
    5: "annunci",
    10: "disc.ann",
    11: "discuss.",
    12: "disc.priv",
    15: "forum",
    16: "media",
}

# Il codice sintetico con cui il trasporto segnala un guasto che non è una risposta del
# servizio, cioè un errore di rete o un timeout. Non è un codice HTTP e non collide con
# nessuno di essi.
GUASTO = 0


class Errore(Exception):
    """Un errore che va mostrato all'utente come messaggio, non come traccia di stack."""


# ---------------------------------------------------------------------------------------
# Il trasporto è un parametro e non una dipendenza nascosta, perché è ciò che rende la
# logica provabile senza credenziali: il self-test passa un trasporto finto e verifica
# impaginazione, cursore, attese e ripresa senza toccare la rete.
# ---------------------------------------------------------------------------------------

class TrasportoHTTP:
    """Il trasporto vero, che parla con l'API di Discord.

    Restituisce sempre una terna con codice, dati e intestazioni, anche quando la
    richiesta non è arrivata a destinazione: un guasto di rete diventa il codice
    sintetico GUASTO, cosicché la logica di ripresa sia una sola e non due.
    """

    def __init__(self, token):
        self.token = token

    def get(self, percorso, parametri=None):
        return self._richiesta("GET", percorso, parametri)

    def delete(self, percorso):
        return self._richiesta("DELETE", percorso, None)

    def _richiesta(self, metodo, percorso, parametri=None):
        url = BASE + percorso
        if parametri:
            url += "?" + urllib.parse.urlencode(parametri)
        richiesta = urllib.request.Request(url, method=metodo, headers={
            # La forma dell'intestazione è il presidio: si dichiara sempre un bot, mai un
            # account utente, e non esiste un'opzione per cambiarla.
            "Authorization": "Bot " + self.token,
            # Discord chiede uno user agent descrittivo e limita quelli generici delle
            # librerie: il nome del progetto va sostituito all'istanziazione.
            "User-Agent": "progetto (lettore di fonti di community, sola lettura)",
            "Accept": "application/json",
        })
        try:
            with urllib.request.urlopen(richiesta, timeout=30) as risposta:
                intestazioni = {k.lower(): v for k, v in risposta.headers.items()}
                corpo = risposta.read().decode("utf-8")
                # Una cancellazione riuscita risponde senza corpo, e chiedere a un
                # decodificatore JSON di leggere il vuoto è un errore evitabile.
                dati = json.loads(corpo) if corpo.strip() else {}
                return 200, dati, intestazioni
        except urllib.error.HTTPError as e:
            corpo = e.read().decode("utf-8", errors="replace")
            try:
                dati = json.loads(corpo)
            except ValueError:
                dati = {"message": corpo[:400]}
            intestazioni = {k.lower(): v for k, v in (e.headers or {}).items()}
            return e.code, dati, intestazioni
        except Exception as e:
            # Comprende gli errori di rete, i timeout e la risoluzione del nome fallita.
            # Il token non compare in alcun messaggio, perché sta in un'intestazione e non
            # nell'indirizzo.
            return GUASTO, {"message": type(e).__name__ + ": " + str(e)[:200]}, {}


class TrasportoFinto:
    """Un trasporto che risponde da una tabella, per provare la logica senza credenziali.

    Conserva l'elenco delle richieste ricevute e delle attese osservate, cosicché il
    self-test possa verificare non soltanto il risultato ma il modo in cui è stato
    ottenuto: quante pagine, con quale cursore, e se le attese sono state rispettate.

    Il parametro `programma` è una lista di risposte da restituire in testa alle altre,
    ciascuna una terna, e serve a simulare rifiuti e guasti in una posizione precisa.
    """

    def __init__(self, identita, messaggi=None, programma=None, canali=None,
                 discussioni=None, intestazioni=None):
        self.identita = identita
        self.messaggi = messaggi or []
        self.programma = list(programma or [])
        self.canali = canali or []
        self.discussioni = discussioni or []
        self.intestazioni = intestazioni or {}
        self.chiamate = []
        self.attese = []
        self.cancellazioni = []

    def delete(self, percorso):
        self.cancellazioni.append(percorso)
        if self.programma:
            return self.programma.pop(0)
        return 200, {}, {}

    def get(self, percorso, parametri=None):
        self.chiamate.append((percorso, dict(parametri or {})))
        if self.programma:
            return self.programma.pop(0)
        if percorso == "/users/@me":
            return 200, self.identita, {}
        if percorso.endswith("/threads/active"):
            return 200, {"threads": self.discussioni}, {}
        if percorso.endswith("/channels"):
            return 200, self.canali, {}
        if "/messages" in percorso:
            prima = (parametri or {}).get("before")
            limite = int((parametri or {}).get("limit", PER_PAGINA))
            # L'API restituisce i messaggi dal più recente al più vecchio, e `before`
            # chiede quelli anteriori a un identificativo: il finto rispetta questa forma,
            # perché è proprio la forma che la logica di impaginazione deve gestire.
            elenco = self.messaggi
            if prima is not None:
                indici = [i for i, m in enumerate(elenco) if m["id"] == prima]
                if indici:
                    elenco = elenco[indici[0] + 1:]
            return 200, elenco[:limite], dict(self.intestazioni)
        raise AssertionError("percorso non previsto dal trasporto finto: " + percorso)


def dormi(secondi, trasporto):
    """L'attesa passa dal trasporto quando è finto, così il self-test la osserva."""
    if isinstance(trasporto, TrasportoFinto):
        trasporto.attese.append(round(float(secondi), 3))
        return
    time.sleep(secondi)


def numero(intestazioni, chiave, difetto=None):
    """Legge un valore numerico da un'intestazione, tollerando assenza e forma sbagliata."""
    v = intestazioni.get(chiave)
    if v is None:
        return difetto
    try:
        return float(v)
    except (TypeError, ValueError):
        return difetto


def attesa_preventiva(intestazioni, trasporto):
    """Attende quando il servizio dichiara esaurite le richieste della finestra corrente.

    È la difesa che evita di arrivare al rifiuto invece di reagirvi. Il servizio dichiara
    a ogni risposta quante richieste restano e fra quanto la finestra si azzera: quando le
    residue sono zero, proseguire significa ottenere un rifiuto con certezza.
    """
    residue = numero(intestazioni, "x-ratelimit-remaining")
    if residue is not None and residue <= 0:
        fra = numero(intestazioni, "x-ratelimit-reset-after", 1.0)
        if fra and fra > 0:
            dormi(fra, trasporto)


def chiama(trasporto, percorso, parametri=None, metodo="GET"):
    """Una richiesta, con le tre difese: attesa preventiva, rifiuto, guasto transitorio.

    Il metodo è un parametro perché la sola operazione non di lettura dello strumento, cioè
    l'uscita da un server, deve godere delle medesime difese: un guasto di rete a metà di
    quella richiesta lascerebbe altrimenti il bot dove non deve stare.
    """
    attesa = ATTESA_INIZIALE
    codice, dati = None, {}
    for _ in range(TENTATIVI):
        if metodo == "DELETE":
            codice, dati, intestazioni = trasporto.delete(percorso)
        else:
            codice, dati, intestazioni = trasporto.get(percorso, parametri)

        if codice == 200:
            attesa_preventiva(intestazioni, trasporto)
            return dati

        if codice == 429:
            # Il servizio dichiara l'attesa in due posti e non sempre negli stessi: si
            # prende il maggiore fra intestazione e corpo, perché attendere di più è
            # sempre sicuro e attendere di meno produce un secondo rifiuto.
            da_intestazione = numero(intestazioni, "retry-after")
            try:
                da_corpo = float(dati.get("retry_after"))
            except (TypeError, ValueError):
                da_corpo = None
            candidati = [x for x in (da_intestazione, da_corpo) if x is not None]
            dormi(max(candidati) if candidati else 1.0, trasporto)
            continue

        if codice == GUASTO or 500 <= codice < 600:
            # Un guasto di rete o un errore del servizio non sono un motivo per fermarsi a
            # metà di una cronologia. L'attesa è nostra e cresce, perché qui il servizio
            # non dichiara nulla.
            dormi(attesa, trasporto)
            attesa = min(attesa * 2, ATTESA_MASSIMA)
            continue

        if codice == 401:
            raise Errore("il token è stato rifiutato: verificare DISCORD_BOT_TOKEN in .env")
        if codice == 403:
            raise Errore("accesso negato su " + percorso + ": il bot non ha View Channels "
                         "e Read Message History su quel canale, oppure non è nel server")
        if codice == 404:
            raise Errore("non trovato: " + percorso + "; verificare l'identificativo")
        raise Errore("il servizio ha risposto " + str(codice) + ": " +
                     str(dati.get("message", dati))[:300])

    raise Errore("non riuscito dopo " + str(TENTATIVI) + " tentativi su " + percorso +
                 "; l'ultimo esito è stato " + str(codice) + ": " +
                 str(dati.get("message", dati))[:200])


def verifica_identita(trasporto):
    """Il presidio: si procede solo se l'account autenticato è dichiarato un bot.

    Restituisce il nome dell'account. Solleva se non è un bot, ed è il controllo che
    distingue questa via da quella che il progetto ha rifiutato: un token personale
    inserito per errore non produce una lettura ma un rifiuto con la sua ragione.
    """
    io_stesso = chiama(trasporto, "/users/@me")
    if not io_stesso.get("bot"):
        raise Errore(
            "l'account autenticato non è un bot.\n"
            "Questo strumento legge soltanto con un bot account creato nel portale per\n"
            "sviluppatori di Discord. Automatizzare un account personale è vietato dalle\n"
            "condizioni d'uso e la sanzione dichiarata è la terminazione dell'account.\n"
            "Le istruzioni per creare il bot sono nel docstring di questo file.")
    return io_stesso.get("username", "senza nome")


def identificativo(valore, cosa):
    """Un identificativo di Discord è un numero decimale, e va verificato prima di partire.

    Il controllo esiste per un errore osservato all'uso: passando il segnaposto della
    documentazione al posto del valore, la richiesta partiva e il servizio rispondeva
    quattrocento con un messaggio che non nomina il campo sbagliato. Riconoscerlo qui
    costa due righe e dice la causa invece del sintomo.
    """
    v = str(valore).strip()
    if not v.isdigit():
        raise Errore(
            "l'identificativo " + cosa + " non è un numero: " + repr(valore) + "\n"
            "Gli identificativi di Discord sono numeri decimali di diciassette cifre o "
            "più.\n"
            "Se hai copiato un segnaposto dalla documentazione, va sostituito con il "
            "valore vero:\n"
            "quello del server lo stampa il comando `guilds`, quello del canale il "
            "comando `channels`.")
    if len(v) < 15:
        raise Errore(
            "l'identificativo " + cosa + " ha solo " + str(len(v)) + " cifre: " + v + "\n"
            "Quelli di Discord ne hanno diciassette o più, quindi questo è troncato o "
            "non è un identificativo.")
    return v


def data_iso(valore):
    """Controlla che una data passata sulla riga di comando sia confrontabile.

    Il confronto con i momenti dei messaggi è fra stringhe, e funziona perché il servizio
    restituisce sempre la forma ISO in tempo universale. Una data scritta in un'altra
    forma, per esempio con le barre, passerebbe silenziosamente e scarterebbe tutto o
    nulla: è il genere di filtro che sbaglia senza dirlo.
    """
    if valore is None:
        return None
    v = str(valore).strip()
    if not re.match(r"^\d{4}-\d{2}-\d{2}([T ]\d{2}:\d{2}(:\d{2})?)?$", v):
        raise Errore(
            "la data " + repr(valore) + " non è nella forma attesa.\n"
            "Si scrive come anno-mese-giorno, per esempio 2026-01-31, eventualmente\n"
            "seguita dall'ora come 2026-01-31T14:30. Il confronto è in tempo universale,\n"
            "che è la forma in cui il servizio dichiara i momenti dei messaggi.")
    return v.replace(" ", "T")


def leggi_token():
    token = os.environ.get("DISCORD_BOT_TOKEN")
    if token:
        return token.strip()
    percorso = os.path.join(ROOT, ".env")
    if os.path.exists(percorso):
        with open(percorso, "rb") as f:
            for riga in f.read().decode("utf-8", errors="replace").split("\n"):
                riga = riga.strip()
                if riga.startswith("DISCORD_BOT_TOKEN="):
                    return riga.split("=", 1)[1].strip().strip("\"'")
    raise Errore(
        "manca DISCORD_BOT_TOKEN.\n"
        "Va scritto a mano in .env nella radice del progetto, che il .gitignore esclude,\n"
        "oppure passato nell'ambiente. L'agente non può creare quel file: le regole di\n"
        "permesso del progetto negano ogni percorso che corrisponda a .env*, ed è voluto.\n"
        "La procedura completa di allestimento è nel docstring di questo file.")


# ---------------------------------------------------------------------------------------
# Cursori: l'unica parte del costo che dipende da noi.
# ---------------------------------------------------------------------------------------

def cursori_letti():
    if not os.path.exists(CURSORI):
        return {}
    with open(CURSORI, "rb") as f:
        try:
            return json.loads(f.read().decode("utf-8"))
        except ValueError:
            return {}


def cursore_scritto(canale, ultimo):
    dati = cursori_letti()
    dati[str(canale)] = str(ultimo)
    os.makedirs(os.path.dirname(CURSORI), exist_ok=True)
    with open(CURSORI, "wb") as f:
        f.write((json.dumps(dati, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))


# ---------------------------------------------------------------------------------------
# Lettura.
# ---------------------------------------------------------------------------------------

def elenca_canali(trasporto, guild):
    """I canali leggibili di un server, comprese le discussioni attive.

    Le discussioni sono canali con un identificativo proprio e nelle community di sviluppo
    sono spesso il posto dove sta la conoscenza: ometterle darebbe l'impressione che un
    canale con dieci discussioni aperte sia vuoto. Stanno su un endpoint diverso, e la
    loro assenza non è un errore, perché un server può non averne alcuna.
    """
    fuori = []
    for c in chiama(trasporto, "/guilds/" + guild + "/channels"):
        if c.get("type") in TIPI_CANALE:
            fuori.append({"id": str(c.get("id")), "tipo": c.get("type"),
                          "nome": str(c.get("name")), "discussione": False})
    dati = chiama(trasporto, "/guilds/" + guild + "/threads/active")
    for t in (dati.get("threads") or []):
        fuori.append({"id": str(t.get("id")), "tipo": t.get("type"),
                      "nome": str(t.get("name")), "discussione": True})
    return fuori


def messaggi_del_canale(trasporto, canale, limite, dopo=None):
    """Scorre la cronologia dal più recente al più vecchio, e restituisce l'ordine naturale.

    Il parametro `dopo` è l'identificativo dell'ultimo messaggio già letto in una corsa
    precedente: la lettura si arresta quando lo incontra, invece di continuare fino al
    limite richiesto. Gli identificativi di Discord crescono nel tempo, quindi il
    confronto numerico fra due di essi è un confronto cronologico, e questo è ciò che
    rende il cursore affidabile senza consultare l'orologio.

    Un `limite` nullo significa nessun tetto, e ha senso solo con un cursore: senza, la
    lettura scaricherebbe la cronologia intera del canale.
    """
    raccolti, prima = [], None
    while limite == 0 or len(raccolti) < limite:
        quanti = PER_PAGINA if limite == 0 else min(PER_PAGINA, limite - len(raccolti))
        parametri = {"limit": quanti}
        if prima is not None:
            parametri["before"] = prima
        pagina = chiama(trasporto, "/channels/" + str(canale) + "/messages", parametri)
        if not pagina:
            break
        fermati = False
        for m in pagina:
            if dopo is not None and int(m["id"]) <= int(dopo):
                fermati = True
                break
            raccolti.append(m)
        if fermati or len(pagina) < quanti:
            break
        prima = pagina[-1]["id"]
    raccolti.reverse()
    return raccolti


def testo_di(m):
    """Il contenuto leggibile di un messaggio, comprese le parti che non sono testo.

    Un messaggio può portare il proprio contenuto in un blocco incorporato invece che nel
    testo, e in un canale tecnico capita spesso: l'anteprima di un collegamento, l'uscita
    di un altro bot, una citazione formattata. Ignorarli renderebbe quei messaggi come
    vuoti, che è il modo più silenzioso di perdere informazione.
    """
    parti = []
    testo = (m.get("content") or "").strip()
    if testo:
        parti.append(testo)
    for e in (m.get("embeds") or []):
        pezzi = []
        if e.get("title"):
            pezzi.append(str(e["title"]).strip())
        if e.get("description"):
            pezzi.append(str(e["description"]).strip())
        if e.get("url"):
            pezzi.append(str(e["url"]).strip())
        for campo in (e.get("fields") or []):
            nome = str(campo.get("name", "")).strip()
            valore = str(campo.get("value", "")).strip()
            if nome or valore:
                pezzi.append(nome + ": " + valore if nome else valore)
        if pezzi:
            parti.append("Incorporato: " + " - ".join(pezzi))
    return "\n\n".join(parti)


def protetto(testo):
    """Impedisce che il contenuto di terzi forgi la struttura della nota.

    Una riga che apre con un cancelletto diventerebbe un'intestazione, e un messaggio che
    ne contiene diverse spezzerebbe il file in sezioni inesistenti. La protezione è minima
    e conserva la leggibilità: si premette una barra rovesciata, che i lettori di Markdown
    rendono come il carattere letterale. Dentro un blocco di codice recintato non si tocca
    nulla, perché là il cancelletto appartiene al linguaggio e non alla struttura.
    """
    righe = []
    dentro_blocco = False
    for riga in testo.split("\n"):
        if riga.lstrip().startswith("```"):
            dentro_blocco = not dentro_blocco
            righe.append(riga)
            continue
        if not dentro_blocco and riga.lstrip().startswith("#"):
            spazi = riga[:len(riga) - len(riga.lstrip())]
            righe.append(spazi + "\\" + riga.lstrip())
            continue
        righe.append(riga)
    return "\n".join(righe)


def markdown(messaggi, canale, nome_bot, intestazione=True):
    """La resa segue la convenzione delle fonti procurate a mano, per essere citabile.

    L'autore viene conservato con il proprio identificativo accanto al nome, e non per
    completezza formale: senza di esso una richiesta di cancellazione mirata non è
    eseguibile, ed è il primo dei quattro accorgimenti che la regola sulle fonti non
    recuperabili prescrive per rendere quella richiesta fattibile invece che improvvisata.
    Gli altri tre sono il luogo unico, la cancellazione del materiale grezzo quando la
    sintesi lo ha reso superfluo, e i soli permessi necessari.

    La catena delle risposte viene conservata perché in una discussione tecnica è metà del
    significato: un messaggio che dice che il valore è sbagliato non dice nulla se si è
    perso a quale valore rispondeva.
    """
    righe = []
    if intestazione:
        righe.append("# Canale Discord " + str(canale))
        righe.append("")
        righe.append("Letto con `tools/fetch-discord.py` attraverso il bot account `" +
                     nome_bot + "`, in sola lettura. Questo file sta sotto `_notes/`, che "
                     "il `.gitignore` esclude: è materiale grezzo di terzi e non entra nel "
                     "version control. Ciò che entra è la sintesi con l'attribuzione, nel "
                     "registro delle fonti del progetto. I momenti sono in tempo universale.")
        righe.append("")
    for m in messaggi:
        autore = m.get("author") or {}
        nome = autore.get("global_name") or autore.get("username") or "ignoto"
        quando = (m.get("timestamp") or "")[:19].replace("T", " ")
        righe.append("## " + nome + " (" + str(autore.get("id", "?")) + ") - " + quando)
        righe.append("")
        riferito = m.get("referenced_message")
        if riferito:
            rautore = (riferito.get("author") or {}).get("username", "ignoto")
            rtesto = testo_di(riferito).replace("\n", " ")
            if len(rtesto) > 200:
                rtesto = rtesto[:200] + "..."
            righe.append("In risposta a " + rautore + ": " + (rtesto or "(senza testo)"))
            righe.append("")
        corpo = testo_di(m)
        righe.append(protetto(corpo) if corpo else
                     "(nessun contenuto testuale: allegato, adesivo o messaggio di sistema)")
        allegati = m.get("attachments") or []
        if allegati:
            righe.append("")
            for a in allegati:
                righe.append("Allegato: " + str(a.get("filename", "?")) + " (" +
                             str(a.get("size", "?")) + " byte)")
        righe.append("")
    return "\n".join(righe).rstrip("\n") + "\n"


def filtra(messaggi, chiavi, lunghezza_minima, da):
    """I tre filtri sono gli stessi di read-chat-export.py, per non avere due grammatiche.

    Il filtro guarda il contenuto leggibile e non il solo testo, cosicché un messaggio il
    cui contenuto sta in un blocco incorporato non venga scartato per lunghezza né manchi
    una parola chiave che in realtà contiene.
    """
    fuori = []
    for m in messaggi:
        testo = testo_di(m)
        if lunghezza_minima and len(testo) < lunghezza_minima:
            continue
        if da and (m.get("timestamp") or "") < da:
            continue
        if chiavi:
            minuscolo = testo.lower()
            if not any(k.lower() in minuscolo for k in chiavi):
                continue
        fuori.append(m)
    return fuori


# ---------------------------------------------------------------------------------------
# Il self-test: prova la logica e comprende i controlli negativi.
# ---------------------------------------------------------------------------------------

def self_test():
    esiti = []

    def prova(nome, condizione, dettaglio=""):
        esiti.append((nome, bool(condizione), dettaglio))

    finti = [{"id": str(1000 - i), "content": "messaggio " + str(1000 - i),
              "timestamp": "2026-08-2" + str(i % 10) + "T10:00:00.000000+00:00",
              "author": {"id": "7", "username": "tizio"}} for i in range(250)]

    bot = {"bot": True, "username": "lettore-di-fonti"}
    utente = {"bot": False, "username": "persona"}

    # 1. Impaginazione: 250 messaggi richiedono tre pagine da cento.
    t = TrasportoFinto(bot, finti)
    verifica_identita(t)
    letti = messaggi_del_canale(t, 42, 250)
    pagine = [c for c in t.chiamate if "/messages" in c[0]]
    prova("impaginazione, messaggi raccolti", len(letti) == 250, str(len(letti)))
    prova("impaginazione, richieste effettuate", len(pagine) == 3, str(len(pagine)))
    prova("impaginazione, cursore passato dalla seconda", pagine[1][1].get("before") == "901",
          str(pagine[1][1].get("before")))
    prova("ordine cronologico crescente",
          letti[0]["id"] == "751" and letti[-1]["id"] == "1000",
          letti[0]["id"] + ".." + letti[-1]["id"])

    # 2. Limite nullo: nessun tetto, si legge finché il servizio consegna.
    t = TrasportoFinto(bot, finti)
    prova("limite nullo, tutta la cronologia",
          len(messaggi_del_canale(t, 42, 0)) == 250)

    # 3. Il cursore ferma la lettura, invece di leggere tutto e scartare dopo.
    t = TrasportoFinto(bot, finti)
    letti = messaggi_del_canale(t, 42, 250, dopo="990")
    prova("cursore, solo il delta", len(letti) == 10, str(len(letti)))
    prova("cursore, una sola richiesta",
          len([c for c in t.chiamate if "/messages" in c[0]]) == 1)

    # 4. Rifiuto per eccesso di frequenza: si attende il maggiore fra i due valori
    #    dichiarati, perché attendere di più è sicuro e attendere di meno rifiuta ancora.
    t = TrasportoFinto(bot, finti, programma=[
        (200, bot, {}),
        (429, {"retry_after": 0.05}, {"retry-after": "0.20"}),
    ])
    verifica_identita(t)
    letti = messaggi_del_canale(t, 42, 10)
    prova("rifiuto, esito comunque ottenuto", len(letti) == 10, str(len(letti)))
    prova("rifiuto, si attende il maggiore dei due valori", t.attese == [0.2], str(t.attese))

    # 5. Attesa preventiva: quando il servizio dichiara zero richieste residue si attende
    #    prima di proseguire, invece di tirare fino al rifiuto.
    t = TrasportoFinto(bot, finti, intestazioni={"x-ratelimit-remaining": "0",
                                                 "x-ratelimit-reset-after": "0.5"})
    letti = messaggi_del_canale(t, 42, 150)
    prova("attesa preventiva su richieste esaurite", t.attese == [0.5, 0.5], str(t.attese))
    prova("attesa preventiva, lettura completata", len(letti) == 150, str(len(letti)))

    # 6. Guasto transitorio: un errore di rete e un errore del servizio non fermano la
    #    lettura, e l'attesa cresce.
    t = TrasportoFinto(bot, finti, programma=[
        (200, bot, {}),
        (GUASTO, {"message": "TimeoutError"}, {}),
        (503, {"message": "Service Unavailable"}, {}),
    ])
    verifica_identita(t)
    letti = messaggi_del_canale(t, 42, 10)
    prova("guasto transitorio, ripresa", len(letti) == 10, str(len(letti)))
    prova("guasto transitorio, attesa crescente", t.attese == [1.0, 2.0], str(t.attese))

    # 7. Guasto permanente: dopo i tentativi dichiarati si abbandona riferendo l'ultimo
    #    esito, invece di restare in un ciclo.
    t = TrasportoFinto(bot, finti, programma=[(GUASTO, {"message": "DNS"}, {})] * TENTATIVI)
    try:
        chiama(t, "/users/@me")
        prova("guasto permanente, si abbandona", False, "non ha sollevato")
    except Errore as e:
        prova("guasto permanente, si abbandona",
              "tentativi" in str(e) and "DNS" in str(e))

    # 8. Controllo negativo: il presidio deve rifiutare un token non di bot. Se questa
    #    prova passasse senza sollevare, il presidio non ci sarebbe.
    t = TrasportoFinto(utente, finti)
    try:
        verifica_identita(t)
        prova("presidio contro il token personale", False, "non ha rifiutato")
    except Errore as e:
        prova("presidio contro il token personale", "non è un bot" in str(e))

    # 9. Controllo locale dell'identificativo, con il caso che lo ha motivato: il
    #    segnaposto della documentazione passato per errore al posto del valore.
    for cattivo in ("ID_CANALE", "", "12345", "123456789012345678x"):
        try:
            identificativo(cattivo, "del canale")
            prova("identificativo rifiutato: " + repr(cattivo), False, "accettato")
        except Errore:
            prova("identificativo rifiutato: " + repr(cattivo), True)
    prova("identificativo valido accettato",
          identificativo(" 123456789012345678 ", "del canale") == "123456789012345678")

    # 10. La data del filtro va nella forma confrontabile, altrimenti scarta senza dirlo.
    for cattiva in ("31/01/2026", "gennaio", "2026-1-1"):
        try:
            data_iso(cattiva)
            prova("data rifiutata: " + repr(cattiva), False, "accettata")
        except Errore:
            prova("data rifiutata: " + repr(cattiva), True)
    prova("data valida normalizzata", data_iso("2026-01-31 14:30") == "2026-01-31T14:30")

    # 11. Elenco dei canali: comprende le discussioni, che stanno su un endpoint diverso.
    t = TrasportoFinto(bot,
                       canali=[{"id": "1" * 18, "type": 0, "name": "generale"},
                               {"id": "2" * 18, "type": 2, "name": "vocale"},
                               {"id": "3" * 18, "type": 15, "name": "forum-tecnico"}],
                       discussioni=[{"id": "4" * 18, "type": 11, "name": "checksum gen 3"}])
    elenco = elenca_canali(t, "9" * 18)
    prova("elenco, il canale vocale è escluso",
          all(c["tipo"] != 2 for c in elenco), str([c["tipo"] for c in elenco]))
    prova("elenco, forum incluso", any(c["tipo"] == 15 for c in elenco))
    prova("elenco, discussione inclusa e marcata",
          any(c["discussione"] and c["tipo"] == 11 for c in elenco))

    # 12. Contenuto che non è testo: un messaggio con il solo blocco incorporato non è
    #     vuoto, e il filtro deve vederne il contenuto.
    con_incorporato = {"id": "1" * 18, "content": "", "timestamp": "2026-01-01T00:00:00",
                       "author": {"id": "1", "username": "a"},
                       "embeds": [{"title": "Pan Docs", "description": "registri SB e SC",
                                   "url": "https://gbdev.io/pandocs/"}]}
    prova("contenuto incorporato letto", "registri SB e SC" in testo_di(con_incorporato))
    prova("filtro vede il contenuto incorporato",
          len(filtra([con_incorporato], ["registri"], 0, None)) == 1)

    # 13. Catena delle risposte conservata.
    risposta = {"id": "2" * 18, "content": "quel valore è sbagliato",
                "timestamp": "2026-01-01T00:01:00", "author": {"id": "2", "username": "b"},
                "referenced_message": {"content": "il checksum sta a 0x0AF8",
                                       "author": {"username": "a"}}}
    prova("catena delle risposte conservata",
          "In risposta a a: il checksum sta a" in markdown([risposta], 42, "bot"))

    # 14. Controllo negativo: il contenuto di terzi non deve forgiare intestazioni, ma
    #     dentro un blocco di codice il cancelletto va lasciato intatto.
    ostile = {"id": "3" * 18, "content": "# finta intestazione\n## anche questa\ntesto",
              "timestamp": "2026-01-01T00:02:00", "author": {"id": "3", "username": "c"}}
    reso = markdown([ostile], 42, "bot")
    intestazioni_vere = [r for r in reso.split("\n") if r.startswith("#")]
    prova("nessuna intestazione forgiata dal contenuto",
          len(intestazioni_vere) == 2, str(len(intestazioni_vere)))
    prova("il cancelletto in un blocco di codice resta intatto",
          "```\n#define X\n```" in markdown(
              [{"id": "4" * 18, "content": "```\n#define X\n```",
                "timestamp": "2026-01-01T00:03:00",
                "author": {"id": "4", "username": "d"}}], 42, "bot"))

    # 15. L'uscita da un server: usa il metodo di cancellazione, sull'indirizzo giusto, e
    #     gode delle stesse difese contro i guasti transitori.
    t = TrasportoFinto(bot)
    chiama(t, "/users/@me/guilds/" + "9" * 18, metodo="DELETE")
    prova("uscita, indirizzo corretto",
          t.cancellazioni == ["/users/@me/guilds/" + "9" * 18], str(t.cancellazioni))
    t = TrasportoFinto(bot, programma=[(GUASTO, {"message": "TimeoutError"}, {}),
                                       (200, {}, {})])
    chiama(t, "/users/@me/guilds/1", metodo="DELETE")
    prova("uscita, ripresa dopo un guasto", t.attese == [1.0], str(t.attese))

    # 16. I filtri.
    campione = [
        {"id": "1", "content": "parla del link cable", "timestamp": "2026-01-01T00:00:00",
         "author": {"id": "1", "username": "a"}},
        {"id": "2", "content": "ok", "timestamp": "2026-01-02T00:00:00",
         "author": {"id": "2", "username": "b"}},
        {"id": "3", "content": "checksum additivo e permutazioni",
         "timestamp": "2025-01-01T00:00:00", "author": {"id": "3", "username": "c"}},
    ]
    prova("filtro per parola chiave",
          [m["id"] for m in filtra(campione, ["link cable"], 0, None)] == ["1"])
    prova("filtro per lunghezza minima",
          [m["id"] for m in filtra(campione, None, 10, None)] == ["1", "3"])
    prova("filtro per data",
          [m["id"] for m in filtra(campione, None, 0, "2026-01-01")] == ["1", "2"])

    # 17. La resa conserva l'identificativo dell'autore, che serve alla cancellazione
    #     mirata, e sa omettere l'intestazione per aggiungersi in coda a un file.
    reso = markdown(campione, 42, "lettore-di-fonti")
    prova("la resa conserva l'identificativo dell'autore", "(1)" in reso and "(3)" in reso)
    prova("l'intestazione si può omettere",
          not markdown(campione, 42, "x", intestazione=False).startswith("# Canale"))

    larghezza = max(len(n) for n, _, _ in esiti)
    falliti = 0
    for nome, esito, dettaglio in esiti:
        stato = "ok      " if esito else "FALLITO "
        if not esito:
            falliti += 1
        print("  " + stato + nome.ljust(larghezza) + ("  " + dettaglio if dettaglio else ""))
    print("self-test: " + str(falliti) + " controlli falliti su " + str(len(esiti)))
    return 1 if falliti else 0


# ---------------------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--self-test", action="store_true",
                    help="prova la logica contro un trasporto finto, senza credenziali")
    sub = ap.add_subparsers(dest="comando")

    sub.add_parser("stato", help="la configurazione dell'applicazione, letta dal servizio")

    sub.add_parser("guilds", help="i server in cui il bot è stato invitato")

    p_ch = sub.add_parser("channels",
                          help="i canali leggibili di un server, discussioni comprese")
    p_ch.add_argument("guild")

    p_l = sub.add_parser("leave", help="fa uscire il bot da un server")
    p_l.add_argument("guild")
    p_l.add_argument("--conferma", action="store_true",
                     help="richiesto: senza questa opzione il comando non agisce")

    p_f = sub.add_parser("fetch", help="la cronologia di un canale o di una discussione")
    p_f.add_argument("canale")
    p_f.add_argument("--limit", type=int, default=200,
                     help="quanti messaggi al massimo; 0 significa nessun tetto, "
                          "sensato solo con --nuovi")
    p_f.add_argument("--grep", action="append", help="tieni solo i messaggi con questa parola")
    p_f.add_argument("--min-length", type=int, default=0, help="scarta i messaggi più corti")
    p_f.add_argument("--since", help="scarta i messaggi anteriori a questa data, forma ISO")
    p_f.add_argument("--nuovi", action="store_true",
                     help="leggi solo ciò che è arrivato dopo l'ultima lettura di questo canale")
    p_f.add_argument("--append", action="store_true",
                     help="aggiungi in coda al file invece di sovrascriverlo")
    p_f.add_argument("--out", help="dove scrivere; per difetto sotto _notes/fonti/")

    a = ap.parse_args()

    if a.self_test:
        return self_test()
    if not a.comando:
        ap.print_help()
        return 2

    try:
        trasporto = TrasportoHTTP(leggi_token())
        nome_bot = verifica_identita(trasporto)

        if a.comando == "stato":
            # La configurazione si legge dal servizio e non dalla schermata del portale,
            # per la stessa ragione per cui un PDF si verifica sui byte: una schermata
            # mostra ciò che il browser ha in cache, e un salvataggio non premuto ha
            # l'aspetto di uno premuto.
            app = chiama(trasporto, "/oauth2/applications/@me")
            pubblica = bool(app.get("bot_public"))
            print("applicazione:        " + str(app.get("name", "?")))
            print("identificativo:      " + str(app.get("id", "?")))
            print("bot pubblico:        " + ("sì" if pubblica else "no") +
                  ("  (un amministratore di un server altrui può invitarlo)" if pubblica
                   else "  (solo il proprietario può installarla: un amministratore di un "
                        "server altrui riceverebbe un errore)"))
            print("richiede code grant: " +
                  ("sì  ATTENZIONE: romperebbe il link di invito, va spento"
                   if app.get("bot_require_code_grant") else "no"))
            return 0

        if a.comando == "guilds":
            for g in chiama(trasporto, "/users/@me/guilds"):
                print(str(g.get("id", "?")) + "  " + str(g.get("name", "?")))
            return 0

        if a.comando == "leave":
            guild = identificativo(a.guild, "del server")
            if not a.conferma:
                print("questo comando fa uscire il bot dal server " + guild + " e l'uscita "
                      "non si annulla da qui: per rientrare serve un nuovo invito da chi "
                      "amministra quel server.\nRilanciare con --conferma se è ciò che si "
                      "vuole.")
                return 1
            chiama(trasporto, "/users/@me/guilds/" + guild, metodo="DELETE")
            print("il bot è uscito dal server " + guild)
            return 0

        if a.comando == "channels":
            for c in elenca_canali(trasporto, identificativo(a.guild, "del server")):
                etichetta = TIPI_CANALE.get(c["tipo"], "altro").ljust(9)
                marca = "  (discussione)" if c["discussione"] else ""
                print(c["id"] + "  " + etichetta + "  #" + c["nome"] + marca)
            return 0

        if a.comando == "fetch":
            canale = identificativo(a.canale, "del canale")
            da = data_iso(a.since)
            if a.limit == 0 and not a.nuovi:
                print("avviso: --limit 0 senza --nuovi scarica la cronologia intera del "
                      "canale, che su un canale attivo sono molte migliaia di messaggi e "
                      "altrettante richieste")
            dopo = cursori_letti().get(canale) if a.nuovi else None
            messaggi = messaggi_del_canale(trasporto, canale, a.limit, dopo=dopo)
            if not messaggi:
                print("nessun messaggio nuovo" if a.nuovi else "nessun messaggio")
                return 0
            # Il cursore avanza fino all'ultimo messaggio letto e non all'ultimo scritto,
            # cosicché un filtro restrittivo non faccia rileggere ciò che ha scartato.
            ultimo = messaggi[-1]["id"]
            letti = len(messaggi)
            messaggi = filtra(messaggi, a.grep, a.min_length, da)
            destinazione = a.out or os.path.join(
                ROOT, "_notes", "fonti",
                time.strftime("%Y-%m-%d") + "-discord-" + canale + ".md")
            os.makedirs(os.path.dirname(destinazione), exist_ok=True)
            esisteva = os.path.exists(destinazione)
            if esisteva and not a.append:
                # Il nome predefinito dipende da canale e data, quindi due corse dello
                # stesso giorno sullo stesso canale finiscono sullo stesso file. Il
                # materiale è rileggibile e rifiutare sarebbe sproporzionato, ma una
                # sovrascrittura silenziosa è il genere di cosa che un giorno costa un'ora.
                print("avviso: " + os.path.relpath(destinazione, ROOT) +
                      " esiste già e viene sovrascritto; con --append si aggiunge in coda")
            modo = "ab" if (a.append and esisteva) else "wb"
            testo = markdown(messaggi, canale, nome_bot,
                             intestazione=not (a.append and esisteva))
            with open(destinazione, modo) as f:
                if modo == "ab":
                    f.write(b"\n")
                f.write(testo.encode("utf-8"))
            scartati = letti - len(messaggi)
            print("scritti " + str(len(messaggi)) + " messaggi in " +
                  os.path.relpath(destinazione, ROOT) +
                  ("" if not scartati else ", " + str(scartati) + " scartati dai filtri"))
            cursore_scritto(canale, ultimo)
            print("cursore aggiornato: la prossima corsa con --nuovi parte da " + ultimo)
            return 0

    except Errore as e:
        print(str(e), file=sys.stderr)
        return 1
    return 2


if __name__ == "__main__":
    sys.exit(main())
