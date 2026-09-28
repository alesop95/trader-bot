#!/usr/bin/env python3
"""Legge un post di Reddit e risale ricorsivamente i suoi sottolink.

Perché esiste
-------------

Un post di Reddit e spesso un raccoglitore invece di un documento: dice poco di suo e rinvia a decine di altri post, ciascuno dei quali rinvia altrove. La conoscenza sta nel grafo e non nel nodo di partenza, quindi leggere il solo post che si ha in mano significa leggere l'indice e credere di aver letto il libro. Questo strumento attraversa quel grafo, scarica cio che trova, ne produce una copia leggibile su disco, e dichiara esplicitamente cio che ha lasciato fuori.

La via, e perché non è l'API ufficiale
--------------------------------------

Reddit non è raggiungibile da nessuno degli strumenti di sessione, e la norma `skills/fonti-non-recuperabili/RIFERIMENTO.md` ne tiene il registro. Gli endpoint che restituiscono JSON rifiutano con un codice 403 sia sul dominio corrente sia su quello storico; i frontend alternativi e i proxy di lettura rifiutano allo stesso modo; il crawler del modello dichiara di non poter raggiungere il dominio. La pagina HTML risponde invece con un codice 200, e quella è la trappola: gli ottomila byte che restituisce sono la pagina di verifica anti-bot, con un titolo generico e nessun contenuto, quindi un successo apparente che inganna più di un rifiuto esplicito.

L'API ufficiale avrebbe un flusso a sole credenziali applicative che basterebbe per leggere contenuto pubblico, e sarebbe la via preferibile. Su almeno un account osservato la registrazione dell'applicazione è stata rifiutata dal server senza motivo dichiarato, dopo aver escluso per verifica diretta le due cause note, e la regola registra quel vicolo cieco.

La via che questo strumento percorre è un'altra: l'archivio pubblico Arctic Shift, successore di Pushshift, che pubblica di propria iniziativa un'API documentata sul proprio archivio di Reddit e non chiede alcuna credenziale. La differenza rispetto alle vie vietate non è la quantità di dati né la finalità di chi legge, che sono i criteri sbagliati: è che qui si interroga un canale costruito dal suo proprietario per l'accesso programmatico, con limiti di frequenza pensati per traffico automatico, chiedendogli i propri dati e non quelli di Reddit.

Le due debolezze della via, dichiarate
--------------------------------------

Un archivio non è la fonte, e le conseguenze sono due e opposte. La prima è la latenza: un post recente può non essere ancora indicizzato, quindi l'assenza di un post da questo strumento non prova che il post non esista, ed è la ragione per cui l'esito di un identificativo non trovato si chiama assente e non inesistente. La seconda è il rovescio: un archivio conserva anche cio che su Reddit è stato cancellato, quindi il materiale prodotto qui può contenere testo che il suo autore ha rimosso. Ne segue che l'intestazione di ogni file dichiara la provenienza e il momento in cui il record è stato archiviato, e che l'identificativo dell'autore viaggia accanto al contenuto: senza di esso una richiesta di cancellazione mirata non è eseguibile, e prometterla sarebbe una promessa vuota.

Come attraversa il grafo
------------------------

L'attraversamento è in ampiezza e non in profondità, e la scelta ha due ragioni che non sono di gusto. La prima è economica: l'archivio accetta fino a cinquecento identificativi in una sola richiesta, quindi raccogliere tutti i post di un livello prima di chiamare trasforma centoventi richieste in due. La seconda riguarda la qualità di cio che resta fuori quando un tetto si esaurisce: in ampiezza si taglia il materiale più lontano dal punto di partenza, che è quasi sempre il meno pertinente, mentre in profondità si taglierebbe a caso.

Lo stesso post ricorre nel corpo di un altro in forme diverse, con la coda di parametri che il pulsante di condivisione aggiunge, oppure come collegamento breve, oppure come permalink a un commento: senza normalizzazione verrebbe scaricato più volte e conteggiato più volte contro il tetto. Ogni collegamento viene quindi ridotto a una chiave canonica, che per un post è il suo identificativo in base trentasei, e i collegamenti brevi si risolvono in un lotto prima di essere classificati.

I tetti, e perché dichiarano cio che escludono
----------------------------------------------

I tetti sul numero di post, sul numero di pagine esterne e sulla profondità esistono perché il grafo non ha un confine naturale. Un tetto però introduce un difetto proprio: una corsa troncata è indistinguibile da una completa, e chi ne legge il risultato crede di avere tutto. Il presidio è che cio che il tetto ha escluso non scompare ma finisce elencato nell'indice come non raggiunto e nello stato su disco come pendente, cosicché la copertura parziale resti dichiarata e un rilancio con il tetto alzato prosegua invece di ricominciare.

I link esterni, e i tre modi in cui finiscono
---------------------------------------------

Un collegamento fuori da Reddit finisce in uno di tre stati, e la distinzione va conservata perché i tre non si equivalgono. Scaricato, quando la pagina è stata letta e ridotta a testo. Catalogato, quando l'indirizzo è registrato con il motivo per cui non si scarica: un video, di cui serve la trascrizione e non la pagina, un documento che vive dentro uno scheletro JavaScript, un file binario, una pagina che richiede autenticazione, un dominio escluso da chi ha lanciato la corsa. Fallito, con il codice osservato, quando il tentativo è stato fatto e non è riuscito. Contare un catalogato come uno scaricato produrrebbe una falsa impressione di copertura, che è il difetto che questo strumento cerca di non avere.

Sui video vale una nota, perché l'assenza è voluta e deve restare visibile: la regola prescrive che di un video serva la trascrizione, e il ripulitore dei sottotitoli è uno degli strumenti che questo pacchetto dichiara mancanti. Fino a quando manca, un collegamento a un video resta catalogato con quella ragione accanto.

La buona educazione verso gli host esterni
------------------------------------------

Verso l'archivio non c'è nulla da negoziare, perché si interroga un servizio che si governa da sé con i propri limiti di frequenza dichiarati nelle intestazioni. Verso un sito qualunque, invece, questo strumento è un programma che visita pagine altrui, e si comporta di conseguenza: legge `robots.txt` una volta per host e ne rispetta il divieto, attende un intervallo minimo fra due richieste allo stesso host, dichiara uno user agent descrittivo, e rifiuta le risposte più grandi di un tetto. Non esiste un'opzione per disattivare nulla di questo, per la stessa ragione per cui il lettore di Discord di questo pacchetto non espone un modo per inviare un'intestazione da account personale: una distinzione normativa diventa effettiva soltanto quando è resa meccanica nel punto in cui potrebbe essere violata per distrazione.

Sul significato dei codici di `robots.txt` la scelta è dichiarata perché le implementazioni divergono. Una risposta 200 si interpreta secondo le sue regole; una risposta 4xx significa assenza di regole e quindi permesso, come prescrive la specifica corrente; una risposta 5xx o un guasto di rete si trattano invece come divieto totale, che è la lettura prudente della stessa specifica per il caso di un servizio indisponibile.

Quel divieto prudente, però, non è della stessa natura di quello scritto, e la differenza va resa meccanica perché altrimenti costa una fonte. Un divieto scritto è una proprietà del sito e vale finché il sito non cambia idea; un `robots.txt` che non risponde è una proprietà dell'istante, e trattare i due allo stesso modo trasforma un guasto di pochi minuti in una esclusione permanente, che nessuna ripresa ritenta perché il nodo risulta deciso. Il secondo caso finisce quindi fra i pendenti con il proprio motivo, cioè dove questo programma mette già ciò che un tetto ha escluso, e l'opzione `--riprova-transitori` della ripresa recupera le corse fatte prima che la distinzione esistesse, rimettendo fra i pendenti i nodi che portano quel motivo. Il caso non è ipotetico: una corsa reale del 2026-09-08 ha catalogato per questa ragione centotrenta nodi su trentadue host, ottanta dei quali di un solo sito enciclopedico, e il loro `robots.txt` consente esplicitamente le pagine che erano state escluse.

L'uscita su disco
-----------------

Tutto vive sotto `_notes/fonti/reddit-<sub>-<id>-<data>/`, che il `.gitignore` del sistema esclude, perché è materiale grezzo di terzi e non entra nel version control. Cio che entra è la sintesi con l'attribuzione, nel registro delle fonti del progetto.

    _INDEX.md                        lo scheletro: che cosa c'è, dove, e che cosa manca
    MAPPA.md                         la mappa dei rinvii: chi linka che cosa, ad albero
    mappa.json                       la stessa mappa come grafo, per l'uso da programma
    stato.json                       visti, archi, pendenti e falliti, per la ripresa
    posts/<id>-<slug>.md             un post con il suo albero di commenti
    esterni/<host>/<hash>-<slug>.md  una pagina esterna ridotta a testo
    raw/posts/<id>.json              il record così come l'archivio lo ha restituito
    raw/tree/<id>.json               l'albero dei commenti grezzo
    raw/esterni/<hash>.html          la pagina esterna grezza
    .md-unwrap-ignore                il marcatore che esenta la cartella dal normalizzatore

Il marcatore che chiude l'elenco non è un dettaglio di comodo: i file scritti qui riportano prosa di terzi verbatim, e la convenzione di un paragrafo per riga sorgente è una regola sui documenti che scriviamo noi e non una licenza a riscrivere il testo di qualcun altro. Senza di esso il controllo pre-commit proporrebbe di unire righe dentro le citazioni, che è precisamente cio che l'eccezione dichiarata dalla regola di stile vieta per il materiale copiato da una fonte esterna.

L'indice è il Livello 1 della disclosure progressiva che `token-economy.md` prescrive: si legge quello per decidere dove guardare, e si aprono i singoli file solo dopo. Il grezzo resta accanto al derivato per una ragione precisa e non per completezza: permette di rigenerare meglio in seguito, per esempio con un convertitore vero al posto dell'estrattore minimo che sta qui dentro, senza ri-scaricare nulla.

L'indice e la mappa rispondono a due domande diverse e per questo sono due file invece di uno. L'indice dice che cosa c'è, cioè l'elenco dei nodi con i loro dati e il loro esito. La mappa dice come le fonti si tengono, cioè quale contenuto rinvia a quale altro e con che parole: è la sola forma in cui si vede dove la catena dei rinvii si interrompe, perché un nodo catalogato o non raggiunto compare comunque nell'albero, nel punto in cui qualcuno lo ha citato. Gli archi si registrano anche verso i nodi che non verranno letti, e anzi soprattutto verso quelli. L'albero non è il grafo ma una sua lettura: i post di un raccoglitore si citano a vicenda, quindi il grafo ha cicli, e un nodo già comparso si segnala come tale invece di essere espanso una seconda volta. Il grafo vero, senza quella semplificazione, sta in `mappa.json`.

Uso
---

    python tools/fetch-reddit.py --self-test
    python tools/fetch-reddit.py crawl <url o id> --dry-run
    python tools/fetch-reddit.py crawl <url o id> --max-post 50 --max-profondita 1
    python tools/fetch-reddit.py crawl <url o id> --max-post 500 --esterni
    python tools/fetch-reddit.py crawl <url o id> --esterni --dominio-escluso youtube.com
    python tools/fetch-reddit.py riprendi <cartella> --max-post 1000
    python tools/fetch-reddit.py post <id>

La prova a vuoto merita una precisazione, perché non è la prova a vuoto dell'orchestratore di export di questo pacchetto: per un crawler il grafo non si conosce senza chiamare. Qui scarica il solo punto di partenza, che costa una richiesta, e riferisce la frontiera che genererebbe al primo livello con la proiezione della crescita, senza scrivere nulla su disco.

Istanziazione
-------------

Il file si copia in `tools/` del progetto ospite e funziona da solo: non dipende dagli altri strumenti del pacchetto, non porta alcuna tabella di configurazione da sostituire, perché il punto di partenza è un argomento di riga di comando e i filtri sono opzioni, e non richiede nulla in `.env`, perché la via scelta non usa credenziali. L'unico segnaposto da sostituire è lo user agent qui sotto, che va portato al nome del progetto ospite.

La radice si ricava dalla posizione del file, cioè la cartella che contiene `tools/`, quindi copiato in `<progetto>/tools/` scrive sotto `<progetto>/_notes/fonti/` senza configurazione. Eseguito dove vive nel template quel calcolo cadrebbe dentro il pacchetto e lo sporcherebbe: per quel caso, e solo per quello, esiste `--radice`.

Stato di collaudo
-----------------

Provati contro il trasporto finto, senza rete: la formazione dei lotti di identificativi, la deduplicazione delle cinque forme di indirizzo dello stesso post, la risoluzione dei collegamenti brevi, l'ordine in ampiezza e il conteggio della profondità, i tetti con i pendenti registrati, il rifiuto per eccesso di frequenza con l'attesa dichiarata dal servizio, il guasto transitorio con l'attesa raddoppiata, il budget di tentativi ridotto per le pagine esterne, la risposta di errore che arriva con un codice 200, il divieto di `robots.txt`, la distinzione fra quel divieto e il rifiuto transitorio che lascia il nodo pendente, il recupero di una corsa vecchia che aveva catalogato quel rifiuto, la lettura di una pagina sola chiesta per nome con i suoi rinvii non seminati, l'intervallo fra richieste allo stesso host, la protezione del testo di terzi che aprirebbe un'intestazione, la classificazione di un host da catalogare, il riconoscimento di uno scheletro JavaScript, la registrazione degli archi della mappa anche verso i nodi che non verranno letti, la ripresa che salta cio che è fatto, e la scrittura del marcatore che esenta la cartella della corsa dal normalizzatore di Markdown.

Provati contro il servizio reale: il recupero di un post, l'albero completo dei suoi commenti, il lotto di più identificativi in una richiesta, la ricorsione su un post figlio, la forma della risposta di errore per un campo non selezionabile, e una corsa su un grafo di alcune centinaia di nodi con le pagine esterne attive.

Un difetto è emerso soltanto alla lettura dell'uscita e la suite verde non lo aveva preso, quindi vale registrarlo qui: il campo dell'indirizzo di un post di testo contiene il permalink del post stesso, e seguirlo significa seguire sé stessi. Il confronto va fatto sulla chiave canonica e non sul prefisso della stringa, perché le due forme dello stesso indirizzo differiscono per lo spezzone di titolo che una delle due porta dentro.

Restano non osservati sul servizio il comportamento del limite di frequenza sotto traffico prolungato e il tasso di fallimento sui domini esterni protetti. La distinzione fra i due stati va conservata quando questo file viene modificato.
"""

import argparse
import datetime
import hashlib
import html.parser
import json
import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from collections import OrderedDict

# La radice è la cartella che contiene `tools/`, cosicché lo strumento copiato in un progetto
# scriva dentro quel progetto senza che nessuno configuri un percorso. `--radice` la scavalca, e
# serve al solo caso in cui il file venga eseguito dove vive nel template.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# L'archivio pubblico che questo strumento interroga. Non è Reddit, e la distinzione governa
# tutto il resto: la latenza dell'indicizzazione e la sopravvivenza del cancellato.
ARCTIC = "https://arctic-shift.photon-reddit.com"

# I soli campi che servono. Chiederli tutti costa centoundici campi per post, dei quali se ne
# usano dodici: il parametro esiste per questo, e usarlo riduce risposta e tempo. Il permalink
# non compare perché non è un campo selezionabile del servizio e si ricostruisce da subreddit e
# identificativo; chiederlo produce una risposta con codice 200 e il campo dati a nullo, che è
# il modo più silenzioso di non ottenere niente.
CAMPI_POST = ("id,title,author,author_fullname,created_utc,subreddit,score,num_comments,"
              "selftext,url,link_flair_text,retrieved_on")

# Il servizio accetta cinquecento identificativi per richiesta. Lo strumento ne chiede cento,
# perché una risposta da cinquecento post non si ispeziona a mano quando qualcosa va storto, e
# perché il guadagno fra cento e cinquecento è trascurabile mentre la leggibilità no.
LOTTO_ID = 100
LIMITE_LOTTO = 500

# Quanti collegamenti brevi si risolvono in una richiesta. Il servizio ne accetta mille.
LOTTO_BREVI = 200

# Quante volte si riprova prima di arrendersi, e l'attesa che raddoppia fino a un tetto. Il
# tetto esiste perché un'attesa che cresce senza limite trasforma un guasto in un blocco muto.
TENTATIVI = 6
ATTESA_INIZIALE = 1.0
ATTESA_MASSIMA = 30.0

# Quante volte si riprova una pagina esterna, che è molto meno di quante se ne riprova una
# richiesta all'archivio, e la ragione è la differenza di ruolo fra le due. Una richiesta
# all'archivio è la spina dorsale della corsa e vale la pena insistere; una pagina esterna è
# materiale facoltativo, e sei tentativi con trenta secondi di timeout ciascuno significano
# minuti spesi su un host morto, che su un grafo con centinaia di collegamenti esterni si
# moltiplicano fino a dominare la durata della corsa. E stato osservato dal vivo.
TENTATIVI_ESTERNI = 2

# L'attesa massima che si concede a un rifiuto per eccesso di frequenza, anche quando il
# servizio ne dichiara una più lunga. Senza questo tetto un valore anomalo nell'intestazione
# fermerebbe la corsa per un tempo indefinito senza che nulla lo dica.
ATTESA_MASSIMA_RIFIUTO = 60.0

# Il codice sintetico con cui il trasporto segnala cio che non è una risposta del servizio,
# cioè un errore di rete o un timeout, e quello con cui segnala una risposta oltre il tetto di
# dimensione. Non sono codici HTTP e non collidono con nessuno di essi.
GUASTO = 0
TROPPO_GRANDE = -1

# L'intervallo minimo fra due richieste allo stesso host esterno, e il tetto sulla dimensione di
# una risposta. Il secondo evita che un file da mezzo gigabyte finisca in memoria per errore.
INTERVALLO_HOST = 1.0
LIMITE_BYTE = 4 * 1024 * 1024

# Quanti caratteri di testo estratto bastano perché una pagina si consideri contenuto invece di
# involucro. La soglia è un compromesso dichiarato: più bassa lascerebbe passare pagine vuote
# come scaricate, più alta scarterebbe note brevi che sono contenuto legittimo.
SOGLIA_TESTO = 300

# Oltre queste soglie l'indice e la mappa smettono di elencare una riga per elemento e
# passano a raggruppare, perché un file di sintesi che cresce quanto il materiale che
# riassume non è più una sintesi. La misura viene da una corsa reale: su un grafo di
# settemila nodi l'elenco per riga produceva un indice da quasi tre megabyte e una mappa
# da quasi sette, cioè due file che nessuno apre, mentre il dettaglio per elemento resta
# comunque in `mappa.json`, che è fatto per essere letto da un programma.
SOGLIA_ELENCO = 200
SOGLIA_ARCHI = 500

# Il motivo con cui si rifiuta un host il cui `robots.txt` non si è potuto leggere. Vive in una
# costante e non in una stringa scritta sul posto perché non è un messaggio ma una condizione su
# cui il programma decide: un rifiuto di questa specie non è una proprietà del contenuto ma
# dell'istante in cui la corsa vi è passata, quindi il nodo va dichiarato pendente invece che
# catalogato, e una ripresa deve poterlo riconoscere fra i nodi già registrati per riprovarlo. Il
# testo va tenuto identico a quello che le corse precedenti hanno scritto su disco, perché è la
# chiave con cui `--riprova-transitori` li ritrova.
MOTIVO_ROBOTS_TRANSITORIO = "robots.txt non leggibile per indisponibilità del servizio"

# Da sostituire all'istanziazione con il nome del progetto ospite. Un programma che visita
# pagine altrui dichiara chi è: è la forma minima di rispetto verso chi ne legge i log.
UA = "progetto (lettore ricorsivo di fonti pubbliche, sola lettura)"

# Gli host da cui Reddit si serve. Servono a decidere se un indirizzo con `/comments/` dentro sia
# un post di Reddit o una pagina che per caso ha quella parola nel percorso.
HOST_REDDIT = frozenset([
    "reddit.com", "www.reddit.com", "old.reddit.com", "new.reddit.com", "np.reddit.com",
    "m.reddit.com", "amp.reddit.com", "sh.reddit.com", "i.reddit.com", "out.reddit.com",
])

# I parametri di coda che non identificano una risorsa ma la provenienza di chi ci arriva, e che
# vanno tolti prima di confrontare due indirizzi. Tutto cio che apre con `utm_` si tratta allo
# stesso modo senza essere elencato.
PARAMETRI_TRACCIAMENTO = frozenset([
    "share_id", "si", "feature", "ref", "ref_source", "ref_campaign", "context", "rdt",
    "correlation_id", "post_fullname", "chainedposts", "embed", "app", "utm", "amp",
])

# Gli host che non si scaricano, con il motivo per cui non si scaricano. Il motivo entra
# nell'indice accanto all'indirizzo, perché un elenco di link saltati senza ragione è
# indistinguibile da una dimenticanza. Il confronto è per suffisso, cosicché le varianti con
# `www.` o `m.` davanti siano coperte senza elencarle.
CATALOGO = (
    ("youtube.com", "video: serve la trascrizione e non la pagina, e il ripulitore dei "
                    "sottotitoli è uno strumento che questo pacchetto dichiara mancante"),
    ("youtu.be", "video: serve la trascrizione e non la pagina, e il ripulitore dei "
                 "sottotitoli è uno strumento che questo pacchetto dichiara mancante"),
    ("docs.google.com", "documento Google: la pagina è uno scheletro JavaScript e il contenuto "
                        "va esportato a mano"),
    ("drive.google.com", "archivio Google: richiede autenticazione o esportazione manuale"),
    ("x.com", "richiede autenticazione"),
    ("twitter.com", "richiede autenticazione"),
    ("instagram.com", "richiede autenticazione"),
    ("facebook.com", "richiede autenticazione"),
    ("tiktok.com", "richiede autenticazione"),
    ("discord.com", "canale di conversazione: la via è `fetch-discord.py` di questo pacchetto"),
    ("discord.gg", "invito a un canale di conversazione, non contenuto"),
    ("i.redd.it", "immagine, non testo"),
    ("v.redd.it", "video, non testo"),
    ("preview.redd.it", "immagine, non testo"),
    ("imgur.com", "immagine o galleria, non testo"),
    ("reddit.com", "pagina di Reddit che non è un post, quindi non recuperabile dall'archivio "
                   "per identificativo"),
)

# Le estensioni che non sono testo da leggere. Il PDF sta qui e non fra i formati leggibili
# perché esiste uno strumento fatto per quello, e passarlo a un estrattore di HTML produrrebbe
# rumore invece di un errore.
ESTENSIONI_CATALOGO = {
    ".jpg": "immagine", ".jpeg": "immagine", ".png": "immagine", ".gif": "immagine",
    ".webp": "immagine", ".svg": "immagine", ".bmp": "immagine", ".ico": "immagine",
    ".mp4": "video", ".webm": "video", ".mov": "video", ".mkv": "video", ".mp3": "audio",
    ".wav": "audio", ".zip": "archivio", ".rar": "archivio", ".7z": "archivio",
    ".exe": "eseguibile", ".dmg": "eseguibile", ".apk": "eseguibile",
    ".pdf": "documento PDF: la via è il pacchetto `doc-ingest`, non un estrattore di HTML",
    ".docx": "documento: la via è il pacchetto `doc-ingest`",
    ".xlsx": "foglio di calcolo: la via è il pacchetto `doc-ingest`",
    ".pptx": "presentazione: la via è il pacchetto `doc-ingest`",
    ".csv": "dati tabulari, non prosa",
}

# Un identificativo di Reddit è un numero in base trentasei. La lunghezza osservata va da cinque
# a dieci caratteri, e il limite inferiore evita di prendere per identificativo un frammento di
# percorso qualunque.
RE_ID = r"[a-z0-9]{4,10}"
RE_COMMENTS = re.compile(r"/comments/(" + RE_ID + r")(?:/|$|\?)", re.I)
RE_COMMENTO = re.compile(r"/comments/" + RE_ID + r"/[^/]*/(" + RE_ID + r")(?:/|$|\?)", re.I)
RE_REDD_IT = re.compile(r"^https?://(?:www\.)?redd\.it/(" + RE_ID + r")", re.I)
RE_BREVE = re.compile(r"^https?://(?:[a-z0-9.-]*\.)?reddit\.com(/(?:r|u|user)/[^/]+/s/[A-Za-z0-9]+)",
                      re.I)
RE_LINK_MD = re.compile(r"\[([^\]\n]{0,200})\]\(\s*<?(https?://[^\s)>]+)>?\s*\)")
RE_LINK_NUDO = re.compile(r"(?<![\(\]])\bhttps?://[^\s\)\]\<\>\"'`]+")
RE_ANGOLARE = re.compile(r"<(https?://[^\s>]+)>")
# La quarta forma, ed e' quella che l'estrattore da HTML produce da se': il testo dell'ancora
# seguito dall'indirizzo fra parentesi tonde. Mancava, e la sua assenza non si vedeva perche' il
# numero dei collegamenti trovati restava plausibile: su una pagina enciclopedica reale ce ne
# sono sessanta in questa forma e l'estrazione ne trovava due, entrambi dall'intestazione che lo
# strumento stesso scrive. L'ancora si cattura insieme all'indirizzo perche' senza di essa
# l'indice diventa un elenco di indirizzi che nessuno legge.
RE_LINK_TONDO = re.compile(r"([^\n(]{0,200}?)\s*\((https?://[^\s)>]+)\)")


class Errore(Exception):
    """Un errore che va mostrato all'utente come messaggio, non come traccia di stack."""


# ---------------------------------------------------------------------------------------------
# Il trasporto è un parametro e non una dipendenza nascosta, perché è cio che rende la logica
# provabile senza rete: il collaudo passa un trasporto finto e verifica lotti, deduplicazione,
# attese, tetti e ripresa senza toccare alcun servizio. La forma differisce da quella del
# lettore di Discord in tre punti, per necessità e non per gusto: l'indirizzo è assoluto perché
# gli host sono due generi diversi, il corpo torna in byte perché una pagina esterna è HTML e
# non JSON, e non c'è alcuna intestazione di autorizzazione perché non c'è alcuna credenziale.
# ---------------------------------------------------------------------------------------------

def contesto_tls():
    """Il contesto di verifica dei certificati, con un archivio di radici che sia aggiornato.

    Esiste per una ragione misurata su questa macchina il 2026-09-12 e non per prudenza astratta.
    L'archivio delle radici del sistema conteneva nove certificati scaduti, e fra questi una copia
    di ISRG Root X2 scaduta il 15 settembre 2025. I siti che si appoggiano a quell'autorità, che
    sono moltissimi, servono una catena che termina in ISRG Root X2 firmata da ISRG Root X1, la
    quale resta valida fino al 2035; ma la verifica, trovando X2 fra le radici di cui si fida, si
    ferma là e la dichiara scaduta invece di proseguire sul ramo firmato che è valido. L'effetto è
    che siti molto comuni, Wikipedia fra questi, risultano irraggiungibili a questo
    programma mentre rispondono a qualunque browser, e con essi centotrenta nodi di una corsa.

    Il rimedio è un archivio di radici corrente, che il pacchetto `certifi` fornisce e tiene
    aggiornato. Quando non c'è, si torna al comportamento di prima, cioè le radici del sistema,
    perché su una macchina sana quelle bastano. Ciò che non si fa in nessun caso è disattivare la
    verifica: il difetto è nell'elenco di chi ci si fida, non nel fatto di fidarsi.
    """
    try:
        import certifi
    except ImportError:
        return ssl.create_default_context()
    try:
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


class TrasportoHTTP:
    """Il trasporto vero.

    Restituisce sempre una terna con codice, corpo in byte e intestazioni, anche quando la
    richiesta non è arrivata a destinazione: un guasto di rete diventa il codice sintetico
    GUASTO e una risposta troppo grande diventa TROPPO_GRANDE, cosicché la logica di ripresa sia
    una sola e non tre.
    """

    def __init__(self, limite=LIMITE_BYTE):
        self.limite = limite
        self.ultimo_indirizzo = None
        self.contesto = contesto_tls()

    def get(self, url):
        richiesta = urllib.request.Request(url, method="GET", headers={
            "User-Agent": UA,
            "Accept": "text/html,application/json,application/xhtml+xml,text/plain;q=0.9,*/*;q=0.5",
            "Accept-Language": "en;q=0.9,it;q=0.8",
        })
        try:
            with urllib.request.urlopen(richiesta, timeout=30,
                                        context=self.contesto) as risposta:
                intestazioni = {k.lower(): v for k, v in risposta.headers.items()}
                # Si legge un byte oltre il tetto per distinguere una risposta esattamente al
                # tetto da una che lo supera, invece di troncare in silenzio.
                corpo = risposta.read(self.limite + 1)
                self.ultimo_indirizzo = risposta.geturl()
                intestazioni["x-indirizzo-finale"] = self.ultimo_indirizzo or url
                if len(corpo) > self.limite:
                    return TROPPO_GRANDE, b"", intestazioni
                return getattr(risposta, "status", None) or 200, corpo, intestazioni
        except urllib.error.HTTPError as e:
            try:
                corpo = e.read(self.limite)
            except Exception:
                corpo = b""
            intestazioni = {k.lower(): v for k, v in (e.headers or {}).items()}
            return e.code, corpo, intestazioni
        except ssl.SSLCertVerificationError as e:
            # Separato dagli altri guasti perché dice una cosa diversa da tutte: non che il sito
            # non risponda, ma che questa macchina non sa fidarsi di lui. Confonderlo con un
            # guasto di rete è costato centotrenta fonti dichiarate irraggiungibili mentre erano in
            # piedi in una corsa reale, e la diagnosi va quindi scritta nel messaggio e non dedotta.
            messaggio = ("CertificatoNonVerificabile: " + str(e)[:200] + " -- non è il sito a "
                         "essere giù: è la catena di certificati di questa macchina a non "
                         "chiudere. Si rimedia con un archivio di radici aggiornato, per esempio "
                         "il pacchetto certifi, non disattivando la verifica.")
            return GUASTO, messaggio.encode("utf-8"), {}
        except Exception as e:
            # Comprende gli errori di rete, i timeout e la risoluzione del nome fallita. Il
            # messaggio si tronca perché una traccia lunga in un log di corsa nasconde le righe
            # che contano.
            messaggio = type(e).__name__ + ": " + str(e)[:200]
            return GUASTO, messaggio.encode("utf-8"), {}


class TrasportoFinto:
    """Un trasporto che risponde da alcune tabelle, per provare la logica senza rete.

    Conserva l'elenco delle richieste ricevute e delle attese osservate, cosicché il collaudo
    possa verificare non soltanto il risultato ma il modo in cui è stato ottenuto: quante
    richieste, con quali identificativi raggruppati, e se le attese sono state rispettate.

    Il parametro `programma` è una lista di risposte da restituire in testa alle altre, ciascuna
    una terna, e serve a collocare un rifiuto o un guasto in una posizione precisa.
    """

    def __init__(self, post=None, alberi=None, brevi=None, pagine=None, robots=None,
                 programma=None):
        self.post = post or {}
        self.alberi = alberi or {}
        self.brevi = brevi or {}
        self.pagine = pagine or {}
        self.robots = robots or {}
        self.programma = list(programma or [])
        self.chiamate = []
        self.attese = []

    def get(self, url):
        self.chiamate.append(url)
        if self.programma:
            return self.programma.pop(0)
        pezzi = urllib.parse.urlsplit(url)
        parametri = urllib.parse.parse_qs(pezzi.query)
        if url.startswith(ARCTIC):
            return self._arctic(pezzi.path, parametri)
        if pezzi.path == "/robots.txt":
            codice, testo = self.robots.get(pezzi.netloc, (404, ""))
            return codice, testo.encode("utf-8"), {}
        if url in self.pagine:
            codice, testo = self.pagine[url]
            return codice, testo.encode("utf-8"), {"content-type": "text/html; charset=utf-8",
                                                   "x-indirizzo-finale": url}
        return 404, b"", {}

    def _arctic(self, percorso, parametri):
        def risposta(dati):
            return 200, json.dumps({"data": dati}).encode("utf-8"), {}
        if percorso == "/api/posts/ids":
            identificativi = (parametri.get("ids") or [""])[0].split(",")
            if len(identificativi) > LIMITE_LOTTO:
                return 200, json.dumps({"data": None, "error": "too many ids"}).encode(), {}
            return risposta([self.post[i] for i in identificativi if i in self.post])
        if percorso == "/api/comments/tree":
            chiave = (parametri.get("link_id") or [""])[0].replace("t3_", "")
            return risposta(self.alberi.get(chiave, []))
        if percorso == "/api/short_links":
            percorsi = (parametri.get("paths") or [""])[0].split(",")
            return risposta([{"original_path": p, "resolved_path": self.brevi[p]}
                             for p in percorsi if p in self.brevi])
        return 404, b"", {}


def dormi(secondi, trasporto):
    """L'attesa passa dal trasporto quando è finto, così il collaudo la osserva."""
    if isinstance(trasporto, TrasportoFinto):
        trasporto.attese.append(round(float(secondi), 3))
        return
    time.sleep(secondi)


def numero(intestazioni, chiave, difetto=None):
    """Legge un valore numerico da un'intestazione, tollerando assenza e forma sbagliata."""
    valore = intestazioni.get(chiave)
    if valore is None:
        return difetto
    try:
        return float(valore)
    except (TypeError, ValueError):
        return difetto


def attesa_preventiva(intestazioni, trasporto):
    """Attende quando il servizio dichiara esaurite le richieste della finestra corrente.

    E la difesa che evita di arrivare al rifiuto invece di reagirvi. L'archivio non dichiara
    sempre quante richieste restano, quindi questa difesa opera quando l'intestazione c'è e non
    fa nulla quando manca: è corretto che sia così, perché l'alternativa sarebbe attendere per
    ipotesi a ogni richiesta.
    """
    residue = numero(intestazioni, "x-ratelimit-remaining")
    if residue is not None and residue <= 0:
        fra = numero(intestazioni, "x-ratelimit-reset", 1.0)
        if fra and fra > 0:
            dormi(min(fra, ATTESA_MASSIMA_RIFIUTO), trasporto)


def chiama(trasporto, url, tentativi=TENTATIVI):
    """Una richiesta, con le tre difese: attesa preventiva, rifiuto, guasto transitorio.

    Il rifiuto per eccesso di frequenza non è un guasto e non si tratta come tale: il servizio
    dichiara quanto attendere, quindi si prende il maggiore fra i valori dichiarati invece di
    indovinare, e si riprova. Il guasto transitorio, che comprende gli errori di rete e le
    risposte di errore del servizio, fa attendere il doppio della volta precedente fino a un
    tetto. L'abbandono definitivo riferisce l'ultimo esito osservato e non un messaggio generico.
    """
    attesa = ATTESA_INIZIALE
    codice, corpo, intestazioni = GUASTO, b"", {}
    for _ in range(max(1, tentativi)):
        codice, corpo, intestazioni = trasporto.get(url)
        if codice == 429:
            dichiarata = max(numero(intestazioni, "retry-after", 0.0) or 0.0,
                             numero(intestazioni, "x-ratelimit-reset", 0.0) or 0.0,
                             1.0)
            dormi(min(dichiarata, ATTESA_MASSIMA_RIFIUTO), trasporto)
            continue
        if codice == GUASTO or 500 <= codice < 600:
            dormi(attesa, trasporto)
            attesa = min(attesa * 2, ATTESA_MASSIMA)
            continue
        attesa_preventiva(intestazioni, trasporto)
        return codice, corpo, intestazioni
    return codice, corpo, intestazioni


def arctic(trasporto, percorso, parametri):
    """Una richiesta all'archivio, con le due forme di fallimento che sa produrre.

    La prima è un codice diverso da duecento, che si riconosce senza fatica. La seconda merita
    il presidio: davanti a un parametro che non accetta, per esempio un campo non selezionabile,
    il servizio risponde con un codice 200 e un corpo in cui il campo dei dati è nullo e accanto
    compare un campo di errore. Trattare quella risposta come vuota invece che come errata
    produrrebbe una corsa che non trova nulla e non dice perché.
    """
    url = ARCTIC + percorso + "?" + urllib.parse.urlencode(parametri)
    codice, corpo, _ = chiama(trasporto, url)
    if codice != 200:
        estratto = corpo[:200].decode("utf-8", errors="replace")
        raise Errore("l'archivio ha risposto " + str(codice) + " su " + percorso +
                     (": " + estratto if estratto else ""))
    try:
        dati = json.loads(corpo.decode("utf-8", errors="replace"))
    except ValueError:
        raise Errore("l'archivio ha risposto con un corpo che non è JSON su " + percorso)
    if isinstance(dati, dict) and dati.get("data") is None:
        raise Errore("l'archivio ha rifiutato la richiesta su " + percorso + ": " +
                     str(dati.get("error") or "campo dati nullo senza errore dichiarato"))
    return dati


# ---------------------------------------------------------------------------------------------
# Il riconoscimento degli indirizzi. E la parte che decide la qualità del risultato, perché lo
# stesso post ricorre nel corpo di un altro in forme diverse e senza normalizzazione verrebbe
# scaricato più volte e conteggiato più volte contro il tetto.
# ---------------------------------------------------------------------------------------------

def host_di(url):
    try:
        return (urllib.parse.urlsplit(url).netloc or "").lower().split("@")[-1].split(":")[0]
    except ValueError:
        return ""


def suffisso_in(host, elenco):
    """Confronta un host con un elenco di domini per suffisso, non per uguaglianza.

    Serve perché `www.youtube.com` e `m.youtube.com` sono lo stesso posto di `youtube.com`, e
    elencare le varianti è un modo di dimenticarne una.
    """
    for voce in elenco:
        if host == voce or host.endswith("." + voce):
            return True
    return False


def normalizza_web(url):
    """Riduce un indirizzo alla sua forma confrontabile.

    Si abbassa lo schema e l'host, si toglie il frammento perché non identifica una risorsa
    diversa, si tolgono i parametri di provenienza, e si toglie lo slash finale. Non si toccano
    i parametri che restano, perché su molti siti sono l'identificativo della pagina.
    """
    try:
        pezzi = urllib.parse.urlsplit(url.strip())
    except ValueError:
        return None
    if pezzi.scheme.lower() not in ("http", "https"):
        return None
    host = host_di(url)
    if not host or "." not in host:
        return None
    tenuti = []
    for chiave, valore in urllib.parse.parse_qsl(pezzi.query, keep_blank_values=True):
        minuscola = chiave.lower()
        if minuscola.startswith("utm_") or minuscola in PARAMETRI_TRACCIAMENTO:
            continue
        tenuti.append((chiave, valore))
    percorso = pezzi.path or "/"
    if len(percorso) > 1 and percorso.endswith("/"):
        percorso = percorso.rstrip("/") or "/"
    return urllib.parse.urlunsplit((
        pezzi.scheme.lower(), host, percorso,
        urllib.parse.urlencode(tenuti), "",
    ))


def canonica(url):
    """Riduce un indirizzo a una chiave, e dice di che genere è.

    Restituisce una terna con genere, chiave e nota, oppure None quando l'indirizzo non è
    utilizzabile. I generi sono tre: `reddit` per un post, la cui chiave è l'identificativo in
    base trentasei; `breve` per un collegamento che va risolto prima di sapere cosa sia, la cui
    chiave è il percorso da risolvere; e `web` per tutto il resto, la cui chiave è l'indirizzo
    normalizzato. La nota porta l'identificativo del commento quando l'indirizzo puntava a un
    commento invece che al post: si scarica il post, e si annota che il rinvio era a quel punto
    della discussione.
    """
    if not url:
        return None
    url = url.strip().rstrip(".,;:!?'\")")
    if url.startswith("//"):
        url = "https:" + url
    if not url.lower().startswith(("http://", "https://")):
        return None
    breve = RE_BREVE.match(url)
    if breve:
        return "breve", breve.group(1), ""
    corto = RE_REDD_IT.match(url)
    if corto:
        return "reddit", corto.group(1).lower(), ""
    host = host_di(url)
    if host in HOST_REDDIT or suffisso_in(host, ["reddit.com"]):
        percorso = urllib.parse.urlsplit(url).path
        trovato = RE_COMMENTS.search(percorso + "?")
        if trovato:
            commento = RE_COMMENTO.search(percorso + "?")
            return "reddit", trovato.group(1).lower(), (commento.group(1).lower()
                                                        if commento else "")
    normale = normalizza_web(url)
    if not normale:
        return None
    return "web", normale, ""


def motivo_catalogo(url):
    """Il motivo per cui un indirizzo esterno si registra senza scaricarlo, o None.

    L'ordine dei controlli conta: l'estensione si guarda prima dell'host, perché un'immagine
    ospitata su un sito di prosa resta un'immagine.
    """
    pezzi = urllib.parse.urlsplit(url)
    estensione = os.path.splitext(pezzi.path)[1].lower()
    if estensione in ESTENSIONI_CATALOGO:
        return ESTENSIONI_CATALOGO[estensione]
    host = host_di(url)
    for voce, motivo in CATALOGO:
        if host == voce or host.endswith("." + voce):
            return motivo
    return None


def estrai_link(testo):
    """I collegamenti di un testo Markdown, con l'ancora che li accompagna.

    Si guardano quattro forme, perché fra il corpo di un post e il testo estratto da una pagina
    convivono tutte e quattro: la sintassi Markdown con le parentesi quadre, l'indirizzo
    racchiuso fra parentesi angolari, il testo dell'ancora seguito dall'indirizzo fra parentesi
    tonde, e l'indirizzo nudo. L'ancora si conserva perché nell'indice è cio che dice a che cosa
    serve quel collegamento, e un elenco di indirizzi senza ancore è un elenco che nessuno legge.

    La quarta forma e' stata aggiunta il 2026-09-14 e la sua assenza era un difetto di copertura
    e non di correttezza, che e' la specie peggiore perche' non produce alcun errore. E'
    precisamente la forma che l'estrattore da HTML di questo stesso programma produce, quindi il
    grafo non si espandeva quasi mai attraverso una pagina esterna ma quasi solo attraverso i
    post: su una pagina enciclopedica reale, sessanta collegamenti in quella forma davano due
    estrazioni. Il numero dei collegamenti trovati restava plausibile, ed e' la ragione per cui
    nessuno se ne era accorto.

    L'ordine in cui le quattro si applicano conta e non e' arbitrario: ogni forma consuma dal
    testo residuo cio' che ha riconosciuto, cosicche' la forma piu' specifica venga prima della
    piu' generica e lo stesso indirizzo non sia contato due volte con due ancore diverse.
    """
    if not testo:
        return []
    coppie = []
    visti = set()

    def aggiungi(ancora, indirizzo):
        # La punteggiatura che chiude la frase non appartiene all'indirizzo, e va tolta qui e
        # non solo in fase di normalizzazione: altrimenti lo stesso indirizzo comparirebbe due
        # volte nell'elenco dei collegamenti, una con la virgola e una senza.
        indirizzo = indirizzo.strip().rstrip(".,;:!?'\")")
        if indirizzo and indirizzo not in visti:
            visti.add(indirizzo)
            coppie.append((" ".join((ancora or "").split())[:200], indirizzo))

    resto = testo
    for trovato in RE_LINK_MD.finditer(testo):
        aggiungi(trovato.group(1), trovato.group(2))
    resto = RE_LINK_MD.sub(" ", resto)
    for trovato in RE_ANGOLARE.finditer(resto):
        aggiungi("", trovato.group(1))
    resto = RE_ANGOLARE.sub(" ", resto)
    for trovato in RE_LINK_TONDO.finditer(resto):
        aggiungi(trovato.group(1), trovato.group(2))
    resto = RE_LINK_TONDO.sub(" ", resto)
    for trovato in RE_LINK_NUDO.finditer(resto):
        aggiungi("", trovato.group(0))
    return coppie


# ---------------------------------------------------------------------------------------------
# Il lato archivio: tre endpoint, e il percorso dell'albero dei commenti.
# ---------------------------------------------------------------------------------------------

def post_per_id(trasporto, identificativi, lotto=LOTTO_ID):
    """I post di un elenco di identificativi, in lotti.

    Il raggruppamento è la ragione per cui l'attraversamento è in ampiezza: chiedere cento post
    in una richiesta invece di cento richieste è la differenza fra una corsa che dura minuti e
    una che dura un'ora. Un identificativo che l'archivio non conosce semplicemente non compare
    nella risposta, e chi chiama distingue quel caso confrontando le chiavi che ha chiesto.
    """
    trovati = {}
    puliti = [i for i in OrderedDict.fromkeys(identificativi) if i]
    for inizio in range(0, len(puliti), max(1, min(lotto, LIMITE_LOTTO))):
        pezzo = puliti[inizio:inizio + max(1, min(lotto, LIMITE_LOTTO))]
        dati = arctic(trasporto, "/api/posts/ids",
                      {"ids": ",".join(pezzo), "fields": CAMPI_POST})
        for record in dati.get("data") or []:
            if isinstance(record, dict) and record.get("id"):
                trovati[record["id"]] = record
    return trovati


def albero_commenti(trasporto, identificativo):
    """L'albero completo dei commenti di un post."""
    dati = arctic(trasporto, "/api/comments/tree",
                  {"link_id": "t3_" + identificativo, "limit": "9999"})
    nodi = dati.get("data")
    return nodi if isinstance(nodi, list) else []


def risolvi_brevi(trasporto, percorsi):
    """Risolve i collegamenti brevi in indirizzi completi, in lotti.

    Serve prima di classificare, perché un collegamento breve non dice se punta a un post, a un
    commento o a un profilo: senza risolverlo finirebbe fra gli esterni sconosciuti, che è il
    modo più facile di perdere un ramo del grafo.
    """
    mappa = {}
    puliti = [p for p in OrderedDict.fromkeys(percorsi) if p]
    for inizio in range(0, len(puliti), LOTTO_BREVI):
        pezzo = puliti[inizio:inizio + LOTTO_BREVI]
        dati = arctic(trasporto, "/api/short_links", {"paths": ",".join(pezzo)})
        for record in dati.get("data") or []:
            if not isinstance(record, dict):
                continue
            origine = record.get("original_path")
            destinazione = record.get("resolved_path")
            if origine and destinazione:
                if destinazione.startswith("/"):
                    destinazione = "https://www.reddit.com" + destinazione
                mappa[origine] = destinazione
    return mappa


def percorri_albero(nodi, profondita=0):
    """Percorre l'albero dei commenti restituendo profondità, genere e dato di ogni nodo.

    I nodi collassati arrivano con genere `more` e un elenco di identificativi al posto del
    contenuto: si restituiscono come sono, perché chi rende il file deve poterli dichiarare
    invece di far sparire un ramo in silenzio.
    """
    for nodo in nodi or []:
        if not isinstance(nodo, dict):
            continue
        genere = nodo.get("kind") or "t1"
        dato = nodo.get("data") if isinstance(nodo.get("data"), dict) else nodo
        yield profondita, genere, dato
        figli = dato.get("replies")
        if isinstance(figli, dict):
            figli = (figli.get("data") or {}).get("children") or []
        if isinstance(figli, list):
            for voce in percorri_albero(figli, profondita + 1):
                yield voce


# ---------------------------------------------------------------------------------------------
# L'estrattore di testo da HTML. E la parte più debole di questo strumento e va detto invece di
# lasciarlo scoprire: un estrattore sulla sola libreria standard rende meno di un convertitore
# vero. La conseguenza pratica è che l'HTML grezzo resta su disco, cosicché un convertitore
# migliore possa rifare il lavoro in seguito senza ri-scaricare nulla.
# ---------------------------------------------------------------------------------------------

SCARTA = frozenset(["script", "style", "noscript", "nav", "header", "footer", "aside", "form",
                    "svg", "iframe", "button", "select", "template"])
BLOCCHI = frozenset(["p", "div", "section", "article", "main", "tr", "table", "blockquote",
                     "ul", "ol", "dl", "dd", "dt", "figure", "figcaption", "hr"])


class Estrattore(html.parser.HTMLParser):
    """Riduce una pagina a testo, conservando titoli, elenchi, codice e indirizzi."""

    def __init__(self):
        html.parser.HTMLParser.__init__(self, convert_charrefs=True)
        self.pezzi = []
        self.titolo = ""
        self.script = 0
        self._scarta = 0
        self._in_titolo = False
        self._pre = 0
        self._href = None

    def handle_starttag(self, tag, attributi):
        if tag == "script":
            self.script += 1
        if tag in SCARTA:
            self._scarta += 1
            return
        if self._scarta:
            return
        if tag == "title":
            self._in_titolo = True
            return
        if tag == "pre":
            self._pre += 1
            self.pezzi.append("\n\n```\n")
            return
        if tag == "br":
            self.pezzi.append("\n")
            return
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.pezzi.append("\n\n" + "#" * int(tag[1]) + " ")
            return
        if tag == "li":
            self.pezzi.append("\n- ")
            return
        if tag == "a":
            self._href = dict(attributi).get("href")
            return
        if tag == "img":
            testo = dict(attributi).get("alt")
            if testo:
                self.pezzi.append(" [immagine: " + testo + "] ")
            return
        if tag in BLOCCHI:
            self.pezzi.append("\n\n")

    def handle_endtag(self, tag):
        if tag in SCARTA:
            self._scarta = max(0, self._scarta - 1)
            return
        if self._scarta:
            return
        if tag == "title":
            self._in_titolo = False
            return
        if tag == "pre":
            self._pre = max(0, self._pre - 1)
            self.pezzi.append("\n```\n\n")
            return
        if tag == "a":
            if self._href and self._href.lower().startswith(("http://", "https://")):
                self.pezzi.append(" (" + self._href + ")")
            self._href = None
            return
        if tag in BLOCCHI or tag in ("h1", "h2", "h3", "h4", "h5", "h6", "li"):
            self.pezzi.append("\n")

    def handle_data(self, dati):
        if self._scarta:
            return
        if self._in_titolo:
            self.titolo += dati.strip() + " "
            return
        self.pezzi.append(dati if self._pre else re.sub(r"[ \t\r\n]+", " ", dati))

    def risultato(self):
        testo = "".join(self.pezzi)
        testo = re.sub(r"[ \t]+", " ", testo)
        testo = re.sub(r" *\n *", "\n", testo)
        testo = re.sub(r"\n{3,}", "\n\n", testo)
        return " ".join(self.titolo.split())[:300], testo.strip()


def codifica_di(intestazioni, corpo):
    """La codifica dichiarata dal server o dal documento, con un ripiego che non solleva."""
    tipo = (intestazioni.get("content-type") or "").lower()
    trovato = re.search(r"charset=([a-z0-9_\-]+)", tipo)
    if not trovato:
        trovato = re.search(rb"charset=[\"']?([a-zA-Z0-9_\-]+)", corpo[:4096])
        if trovato:
            return trovato.group(1).decode("ascii", errors="replace")
        return "utf-8"
    return trovato.group(1)


def html_a_testo(corpo, intestazioni):
    """Il titolo e il testo di una pagina, più il motivo per cui quel testo non basta.

    Il terzo valore è quello che evita di scrivere su disco un file che sembra una pagina e non
    lo è, ed è una stringa vuota quando la pagina ha contenuto. Vale precisare il criterio,
    perché la formulazione ingenua sbaglia: cio che conta non è la presenza di script ma
    l'assenza di testo, quindi la condizione è la scarsita di cio che si è estratto, e gli
    script servono soltanto a dire quale sia la causa probabile. Registrare come scaricata una
    pagina da cui non si è estratto nulla sarebbe falsa copertura, che è il difetto che questo
    strumento cerca di non avere.
    """
    testo_sorgente = corpo.decode(codifica_di(intestazioni, corpo), errors="replace")
    estrattore = Estrattore()
    try:
        estrattore.feed(testo_sorgente)
        estrattore.close()
    except Exception:
        pass
    titolo, testo = estrattore.risultato()
    if len(testo) >= SOGLIA_TESTO:
        return titolo, testo, ""
    if estrattore.script:
        return titolo, testo, ("dalla pagina si estraggono " + str(len(testo)) + " caratteri e "
                               "porta " + str(estrattore.script) + " script: è uno scheletro "
                               "JavaScript, e senza un browser non consegna il contenuto")
    return titolo, testo, ("dalla pagina si estraggono " + str(len(testo)) + " caratteri, che "
                           "non sono contenuto: registrarla come scaricata sarebbe falsa "
                           "copertura")


class Educato:
    """Le regole di accesso a un host esterno: `robots.txt` e l'intervallo fra due richieste.

    Le regole si leggono attraverso il trasporto e non con il lettore della libreria standard,
    che aprirebbe una connessione propria: passando dal trasporto restano osservabili dal
    collaudo, che è la sola via per cui un presidio si possa provare.
    """

    def __init__(self, trasporto, intervallo=INTERVALLO_HOST):
        self.trasporto = trasporto
        self.intervallo = intervallo
        self.regole = {}
        self.ultimo = {}

    def _leggi(self, schema, host):
        if host in self.regole:
            return self.regole[host]
        codice, corpo, _ = chiama(self.trasporto, schema + "://" + host + "/robots.txt",
                                  TENTATIVI_ESTERNI)
        esito = None
        if codice == 200 and corpo:
            lettore = urllib.robotparser.RobotFileParser()
            try:
                lettore.parse(corpo.decode("utf-8", errors="replace").splitlines())
                esito = lettore
            except Exception:
                esito = None
        elif codice == GUASTO or codice == TROPPO_GRANDE or 500 <= codice < 600:
            # Servizio indisponibile: la lettura prudente della specifica è il divieto totale.
            esito = "vietato"
        # Ogni altro codice, cioè la famiglia 4xx, significa assenza di regole e quindi permesso.
        self.regole[host] = esito
        return esito

    def permesso(self, url):
        pezzi = urllib.parse.urlsplit(url)
        esito = self._leggi(pezzi.scheme or "https", pezzi.netloc.lower())
        if esito == "vietato":
            return False, MOTIVO_ROBOTS_TRANSITORIO
        if esito is None:
            return True, ""
        if esito.can_fetch(UA, url):
            return True, ""
        return False, "vietato da robots.txt"

    def attendi(self, url):
        host = host_di(url)
        precedente = self.ultimo.get(host)
        adesso = time.time() if not isinstance(self.trasporto, TrasportoFinto) else 0.0
        if precedente is not None:
            if isinstance(self.trasporto, TrasportoFinto):
                dormi(self.intervallo, self.trasporto)
            else:
                resta = self.intervallo - (adesso - precedente)
                if resta > 0:
                    dormi(resta, self.trasporto)
                adesso = time.time()
        self.ultimo[host] = adesso


# ---------------------------------------------------------------------------------------------
# La resa. La forma segue quella delle fonti procurate a mano, per essere citabile, e conserva
# l'identificativo dell'autore accanto al contenuto: è il primo dei quattro accorgimenti che la
# regola sulle fonti non recuperabili prescrive, e senza di esso una richiesta di cancellazione
# mirata non sarebbe eseguibile. Gli altri tre sono il luogo unico, la cancellazione del grezzo
# quando la sintesi lo ha reso superfluo, e i soli permessi necessari.
# ---------------------------------------------------------------------------------------------

def protetto(testo):
    """Impedisce che il contenuto di terzi forgi la struttura della nota.

    Una riga che apre con un cancelletto diventerebbe un'intestazione, e il corpo di un post di
    Reddit ne contiene di vere: senza protezione un solo post spezzerebbe il file in sezioni
    inesistenti e l'indice del documento non corrisponderebbe più al suo contenuto. La
    protezione è minima e conserva la leggibilità, cioè premette una barra rovesciata che i
    lettori di Markdown rendono come il carattere letterale. Dentro un blocco di codice
    recintato non si tocca nulla, perché là il cancelletto appartiene al linguaggio.
    """
    righe = []
    dentro_blocco = False
    for riga in (testo or "").split("\n"):
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


def sigla(testo, lunghezza=48):
    """Una porzione di nome di file, ricavata da un titolo."""
    pulito = re.sub(r"[^a-z0-9]+", "-", (testo or "").lower()).strip("-")
    return pulito[:lunghezza].strip("-") or "senza-titolo"


def impronta(testo):
    return hashlib.sha1((testo or "").encode("utf-8")).hexdigest()[:8]


def data_di(secondi):
    if not secondi:
        return "data ignota"
    try:
        momento = datetime.datetime.fromtimestamp(float(secondi), datetime.timezone.utc)
        return momento.strftime("%Y-%m-%d %H:%M:%S")
    except (TypeError, ValueError, OSError):
        return "data illeggibile"


def permalink_di(record):
    sub = record.get("subreddit") or "unknown"
    return "https://www.reddit.com/r/" + str(sub) + "/comments/" + str(record.get("id")) + "/"


def cella(testo):
    """Il contenuto di una cella di tabella, senza i caratteri che ne romperebbero la forma."""
    return " ".join(str(testo or "").split()).replace("|", "/")[:160]


PROVENIENZA = (
    "Letto con `tools/fetch-reddit.py` attraverso l'archivio pubblico Arctic Shift, che non è "
    "Reddit: un post recente può mancare perché non ancora indicizzato, e uno cancellato su "
    "Reddit può essere ancora qui. Questo file sta sotto `_notes/`, che il `.gitignore` "
    "esclude: è materiale grezzo di terzi e non entra nel version control. Cio che entra è la "
    "sintesi con l'attribuzione, nel registro delle fonti del progetto. I momenti sono in tempo "
    "universale."
)


def markdown_post(record, nodi, scheda):
    """Un post con il suo albero di commenti.

    La profondità di un commento si rende con il livello dell'intestazione, che si ferma al
    sesto perché Markdown non ne ha altri: oltre quel punto la profondità si scrive accanto al
    nome, cosicché non si perda l'informazione che l'annidamento non riesce più a mostrare.
    """
    righe = ["# " + cella(record.get("title")) or "# senza titolo", "", PROVENIENZA, ""]
    righe.append("Post: r/" + str(record.get("subreddit")) + " - " + str(record.get("id")) +
                 " - " + str(record.get("author") or "ignoto") +
                 " (" + str(record.get("author_fullname") or "identificativo assente") + ")")
    righe.append("Pubblicato: " + data_di(record.get("created_utc")) +
                 " - punteggio " + str(record.get("score")) +
                 " - commenti dichiarati " + str(record.get("num_comments")))
    righe.append("Permalink: " + permalink_di(record))
    # Il campo dell'indirizzo, su un post di testo, ripete il permalink con lo spezzone del
    # titolo dentro: mostrarlo la accanto direbbe due volte la stessa cosa. Si mostra soltanto
    # quando porta altrove, cioè quando il post è un rinvio a un contenuto esterno.
    collegamento = record.get("url") or ""
    esito_collegamento = canonica(collegamento) if collegamento else None
    if collegamento and not (esito_collegamento and esito_collegamento[0] == "reddit" and
                             esito_collegamento[1] == str(record.get("id"))):
        righe.append("Collegamento del post: " + collegamento)
    if record.get("link_flair_text"):
        righe.append("Etichetta: " + cella(record.get("link_flair_text")))
    righe.append("Record archiviato il: " + data_di(record.get("retrieved_on")))
    righe.append("Profondità nella corsa: " + str(scheda.get("profondità", 0)) +
                 (", linkato da: " + ", ".join(scheda.get("da") or []) if scheda.get("da")
                  else ", punto di partenza"))
    if scheda.get("commenti_puntati"):
        righe.append("Rinvii puntati a commenti di questo post: " +
                     ", ".join(scheda["commenti_puntati"]))
    righe.append("")
    corpo = record.get("selftext") or ""
    righe.append("## Corpo")
    righe.append("")
    righe.append(protetto(corpo) if corpo.strip() else
                 "(nessun corpo testuale: il post è un collegamento o un contenuto non testuale)")
    righe.append("")
    totale = 0
    collassati = 0
    corpo_commenti = []
    for profondita, genere, dato in percorri_albero(nodi):
        livello = "#" * min(3 + profondita, 6)
        if genere == "more":
            quanti = len(dato.get("children") or [])
            collassati += quanti
            corpo_commenti.append(livello + " (ramo collassato dal servizio: " + str(quanti) +
                                  " commenti non recuperati)")
            corpo_commenti.append("")
            continue
        totale += 1
        autore = str(dato.get("author") or "ignoto")
        identita = str(dato.get("author_fullname") or "identificativo assente")
        intestazione = (livello + " " + autore + " (" + identita + ") - " +
                        data_di(dato.get("created_utc")) + " - " +
                        str(dato.get("score")) + " punti")
        if profondita >= 3:
            intestazione += " - profondità " + str(profondita)
        corpo_commenti.append(intestazione)
        corpo_commenti.append("")
        testo = dato.get("body")
        corpo_commenti.append(protetto(testo) if (testo or "").strip() else
                              "(commento vuoto, cancellato o rimosso)")
        corpo_commenti.append("")
    righe.append("## Commenti (" + str(totale) + " recuperati" +
                 (", " + str(collassati) + " collassati e non recuperati" if collassati else "") +
                 ")")
    righe.append("")
    righe.extend(corpo_commenti if corpo_commenti else ["(nessun commento)", ""])
    return "\n".join(righe).rstrip("\n") + "\n"


def markdown_esterno(url, indirizzo_finale, titolo, testo, scheda):
    righe = ["# " + (cella(titolo) or "pagina senza titolo"), ""]
    righe.append("Pagina esterna letta con `tools/fetch-reddit.py`. Questo file sta sotto "
                 "`_notes/`, che il `.gitignore` esclude, e il suo HTML grezzo resta accanto in "
                 "`raw/esterni/`: l'estrattore che lo ha ridotto a testo è minimo per scelta, "
                 "quindi il grezzo serve a rifare meglio il lavoro senza ri-scaricare nulla.")
    righe.append("")
    righe.append("Indirizzo: " + url)
    if indirizzo_finale and indirizzo_finale != url:
        righe.append("Indirizzo finale dopo i rinvii: " + indirizzo_finale)
    righe.append("Letta il: " + data_di(time.time()))
    righe.append("Profondità nella corsa: " + str(scheda.get("profondità", 0)) +
                 (", linkato da: " + ", ".join(scheda.get("da") or []) if scheda.get("da") else ""))
    if scheda.get("ancora"):
        righe.append("Testo del rinvio che ci ha portato qui: " + cella(scheda["ancora"]))
    righe.append("")
    righe.append("## Testo")
    righe.append("")
    righe.append(protetto(testo) if (testo or "").strip() else "(nessun testo estratto)")
    return "\n".join(righe).rstrip("\n") + "\n"


def markdown_indice(stato):
    """Lo scheletro della corsa, cioè il file da cui si decide dove guardare.

    Le tre tabelle non sono un elenco di cose fatte: la prima dice cosa c'è, la seconda dice
    cosa è stato visto senza essere scaricato e con quale ragione, la terza dice cosa è restato
    fuori. La terza è il presidio contro il difetto proprio dei tetti, perché senza di essa una
    corsa troncata sarebbe indistinguibile da una completa.
    """
    visti = stato.get("visti") or {}
    post = [(k, v) for k, v in visti.items() if v.get("tipo") == "reddit"]
    esterni = [(k, v) for k, v in visti.items() if v.get("tipo") == "web"]
    scaricati = [k for k, v in post if v.get("esito") == "scaricato"]
    righe = ["# Corsa su Reddit: " + str(stato.get("seme_url") or stato.get("seme")), ""]
    righe.append(PROVENIENZA)
    righe.append("")
    righe.append("Punto di partenza: " + str(stato.get("seme_url") or stato.get("seme")))
    righe.append("Corsa iniziata il " + str(stato.get("creato")) + " e aggiornata il " +
                 str(stato.get("aggiornato")) + ".")
    tetti = stato.get("tetti") or {}
    righe.append("Tetti: al massimo " + str(tetti.get("max_post")) + " post, " +
                 str(tetti.get("max_esterni")) + " pagine esterne, profondità " +
                 (str(tetti.get("max_profondita")) if tetti.get("max_profondita")
                  else "illimitata") +
                 "; pagine esterne " + ("richieste" if stato.get("esterni") else "non richieste") +
                 ".")
    righe.append("Esito: " + str(len(scaricati)) + " post scaricati su " + str(len(post)) +
                 " visti, " +
                 str(len([k for k, v in esterni if v.get("esito") == "scaricato"])) +
                 " pagine esterne scaricate su " + str(len(esterni)) + " viste, " +
                 str(len(stato.get("pendenti") or [])) + " elementi non raggiunti, " +
                 str(len(stato.get("falliti") or [])) + " fallimenti.")
    righe.append("")
    righe.append("## Post")
    righe.append("")
    righe.append("| id | titolo | autore | pubblicato | punti | commenti | prof | esito | file |")
    righe.append("|---|---|---|---|---|---|---|---|---|")
    for chiave, scheda in sorted(post, key=lambda x: (x[1].get("profondità", 0),
                                                      -(x[1].get("punteggio") or 0))):
        righe.append("| " + " | ".join([
            cella(chiave.split(":", 1)[-1]),
            cella(scheda.get("titolo")),
            cella(scheda.get("autore")),
            cella((scheda.get("pubblicato") or "")[:10]),
            cella(scheda.get("punteggio")),
            cella(scheda.get("commenti")),
            cella(scheda.get("profondità")),
            cella(scheda.get("esito") + (": " + scheda["motivo"] if scheda.get("motivo") else "")),
            cella(scheda.get("file") or ""),
        ]) + " |")
    righe.append("")
    righe.append("## Collegamenti esterni")
    righe.append("")
    righe.append("Un collegamento scaricato ha un file accanto; uno catalogato porta il motivo "
                 "per cui non si scarica, e non è un fallimento; uno fallito porta il codice "
                 "osservato. Le tre cose non si equivalgono, e contarle insieme darebbe una "
                 "falsa impressione di copertura.")
    righe.append("")
    catalogati = [(k, v) for k, v in esterni if v.get("esito") == "catalogato"]
    altri = [(k, v) for k, v in esterni if v.get("esito") != "catalogato"]
    # Un elenco per riga è la forma giusta finché gli elementi sono pochi. Su un grafo grande i
    # catalogati sono la maggioranza schiacciante e sono ripetitivi per costruzione, perché il
    # motivo dipende dall'host: elencarli uno per uno gonfia l'indice fino a renderlo illeggibile
    # proprio mentre pretende di essere il file da cui si decide dove guardare. Si raggruppano
    # quindi per host e motivo, e il dettaglio per indirizzo resta in `mappa.json`.
    if len(catalogati) > SOGLIA_ELENCO:
        gruppi = OrderedDict()
        for chiave, scheda in catalogati:
            indirizzo = chiave.split(":", 1)[-1]
            firma = (host_di(indirizzo), " ".join(str(scheda.get("motivo") or "").split()))
            voce = gruppi.setdefault(firma, [0, indirizzo])
            voce[0] += 1
        righe.append("I catalogati sono " + str(len(catalogati)) + ", troppi per un elenco che "
                     "resti leggibile, e sono ripetitivi per costruzione perché il motivo "
                     "dipende dall'host: qui stanno raggruppati per host e motivo, con un "
                     "indirizzo di esempio, e il dettaglio per singolo indirizzo sta in "
                     "`mappa.json`.")
        righe.append("")
        righe.append("| host | quanti | motivo | esempio |")
        righe.append("|---|---|---|---|")
        for (host, motivo), (quanti, esempio) in sorted(gruppi.items(), key=lambda x: -x[1][0]):
            righe.append("| " + " | ".join([cella(host), cella(quanti), cella(motivo),
                                            cella(esempio)]) + " |")
        righe.append("")
        righe.append("Gli scaricati e i falliti restano elencati uno per uno, perché i primi "
                     "hanno un file da aprire e i secondi un codice da capire.")
        righe.append("")
        esterni = altri
    righe.append("| host | indirizzo | rinvio | prof | esito | file |")
    righe.append("|---|---|---|---|---|---|")
    for chiave, scheda in sorted(esterni, key=lambda x: (host_di(x[0].split(":", 1)[-1]),
                                                         x[1].get("profondità", 0))):
        indirizzo = chiave.split(":", 1)[-1]
        righe.append("| " + " | ".join([
            cella(host_di(indirizzo)),
            cella(indirizzo),
            cella(scheda.get("ancora")),
            cella(scheda.get("profondità")),
            cella(scheda.get("esito") + (": " + scheda["motivo"] if scheda.get("motivo") else "")),
            cella(scheda.get("file") or ""),
        ]) + " |")
    righe.append("")
    righe.append("## Non raggiunti")
    righe.append("")
    pendenti = stato.get("pendenti") or []
    if not pendenti:
        righe.append("Nessuno: la corsa ha esaurito la frontiera prima dei tetti, quindi questa "
                     "è una copertura completa del grafo raggiungibile dal punto di partenza.")
    else:
        righe.append("Questi elementi erano nella frontiera e non sono stati letti, per il "
                     "motivo indicato. Restano in `stato.json` come pendenti, quindi un "
                     "`riprendi` con il tetto alzato li prende senza rifare il resto.")
        righe.append("")
        if len(pendenti) > SOGLIA_ELENCO:
            # Quattordicimila righe di non raggiunti direbbero una cosa sola, cioè che il tetto
            # ha morso presto, e la direbbero quattordicimila volte. Il conteggio per motivo e
            # per profondità la dice una volta e in più mostra dove la corsa si è fermata, che
            # è l'informazione che serve a decidere se e con quale tetto riprendere.
            per_motivo = OrderedDict()
            per_profondita = OrderedDict()
            for voce in pendenti:
                per_motivo[voce.get("motivo")] = per_motivo.get(voce.get("motivo"), 0) + 1
                chiave_prof = voce.get("profondità")
                per_profondita[chiave_prof] = per_profondita.get(chiave_prof, 0) + 1
            righe.append("Sono " + str(len(pendenti)) + ", troppi per un elenco: qui stanno "
                         "contati per motivo e per profondità, e uno per uno in `stato.json`.")
            righe.append("")
            righe.append("| motivo | quanti |")
            righe.append("|---|---|")
            for motivo, quanti in sorted(per_motivo.items(), key=lambda x: -x[1]):
                righe.append("| " + cella(motivo) + " | " + cella(quanti) + " |")
            righe.append("")
            righe.append("| profondità | quanti |")
            righe.append("|---|---|")
            for profondita, quanti in sorted(per_profondita.items(),
                                             key=lambda x: (x[0] is None, x[0])):
                righe.append("| " + cella(profondita) + " | " + cella(quanti) + " |")
        else:
            righe.append("| elemento | prof | motivo | linkato da |")
            righe.append("|---|---|---|---|")
            for voce in pendenti:
                righe.append("| " + " | ".join([
                    cella(voce.get("chiave")),
                    cella(voce.get("profondità")),
                    cella(voce.get("motivo")),
                    cella(", ".join(voce.get("da") or [])),
                ]) + " |")
    righe.append("")
    righe.append("La mappa dei rinvii, cioè chi linka che cosa, sta in `MAPPA.md` per la "
                 "lettura e in `mappa.json` per l'uso da programma: qui ci sono i nodi, la "
                 "non ci sono gli archi.")
    righe.append("")
    falliti = stato.get("falliti") or []
    if falliti:
        righe.append("## Fallimenti")
        righe.append("")
        righe.append("| elemento | codice | messaggio |")
        righe.append("|---|---|---|")
        for voce in falliti:
            righe.append("| " + " | ".join([
                cella(voce.get("chiave")),
                cella(voce.get("codice")),
                cella(voce.get("messaggio")),
            ]) + " |")
        righe.append("")
    return "\n".join(righe).rstrip("\n") + "\n"


def etichetta_nodo(chiave, scheda):
    """Come un nodo si presenta nella mappa: che cosa è, e in che stato è finito.

    Il motivo si tronca, perché nell'albero la sua funzione è dire di che genere di
    interruzione si tratta e non spiegarla: la spiegazione intera sta nell'indice e in
    `mappa.json`, e ripeterla per esteso su ogni riga renderebbe l'albero illeggibile proprio
    dove serve vedere la forma della catena.
    """
    scheda = scheda or {}
    stato_nodo = scheda.get("esito") or "non raggiunto"
    if scheda.get("motivo"):
        motivo = " ".join(str(scheda["motivo"]).split())
        stato_nodo += ": " + (motivo[:57] + "..." if len(motivo) > 60 else motivo)
    genere, _, resto = chiave.partition(":")
    if genere == "reddit":
        return cella(scheda.get("titolo") or resto) + " [" + cella(stato_nodo) + "]"
    if genere == "breve":
        return ("collegamento breve non risolto verso " + cella(resto) +
                " [" + cella(stato_nodo) + "]")
    titolo = scheda.get("titolo")
    return ((cella(titolo) + " - " if titolo else "") + cella(resto) +
            " [" + cella(stato_nodo) + "]")


def mappa_json(stato):
    """Il grafo in forma leggibile da un programma: nodi e archi, senza il contenuto.

    Esiste separato dallo stato perché i due rispondono a domande diverse. Lo stato serve alla
    ripresa e porta cio che serve a non rifare il lavoro; la mappa serve a chi vuole sapere come
    le fonti si tengono, e la sua forma è quella di un grafo e non di un registro di corsa.
    """
    visti = stato.get("visti") or {}
    nodi = []
    for chiave, scheda in visti.items():
        nodo = {
            "chiave": chiave,
            "tipo": scheda.get("tipo"),
            "esito": scheda.get("esito"),
            "profondità": scheda.get("profondità"),
            "file": scheda.get("file"),
        }
        if scheda.get("motivo"):
            nodo["motivo"] = scheda["motivo"]
        if scheda.get("tipo") == "reddit":
            nodo["titolo"] = scheda.get("titolo")
            nodo["autore"] = scheda.get("autore")
            nodo["autore_id"] = scheda.get("autore_id")
            nodo["subreddit"] = scheda.get("subreddit")
            nodo["permalink"] = ("https://www.reddit.com/r/" + str(scheda.get("subreddit")) +
                                 "/comments/" + chiave.split(":", 1)[1] + "/")
        else:
            nodo["indirizzo"] = chiave.split(":", 1)[1]
            nodo["host"] = host_di(chiave.split(":", 1)[1])
            nodo["titolo"] = scheda.get("titolo")
        nodi.append(nodo)
    pendenti = [{"chiave": v.get("chiave"), "tipo": v.get("tipo"),
                 "profondità": v.get("profondità"), "esito": "non raggiunto",
                 "motivo": v.get("motivo")} for v in (stato.get("pendenti") or [])]
    return {
        "versione": 1,
        "seme": stato.get("seme"),
        "seme_url": stato.get("seme_url"),
        "generato": data_di(time.time()),
        "nodi": nodi + pendenti,
        "archi": stato.get("archi") or [],
    }


def markdown_mappa(stato):
    """La mappa dei rinvii in forma di albero, più l'elenco piano degli archi.

    L'albero si percorre dal punto di partenza seguendo gli archi, e un nodo già incontrato non
    si espande una seconda volta ma si segnala come tale: senza quella regola un grafo con un
    ciclo, che nei raccoglitori di Reddit è la norma perché i post si citano a vicenda, non
    finirebbe di stamparsi. L'espansione avviene con una pila esplicita e non per ricorsione,
    perché un grafo profondo esaurirebbe lo stack dell'interprete prima della memoria.
    """
    visti = stato.get("visti") or {}
    pendenti = {v.get("chiave"): v for v in (stato.get("pendenti") or [])}
    figli = OrderedDict()
    for arco in stato.get("archi") or []:
        figli.setdefault(arco.get("da"), []).append(arco)
    righe = ["# Mappa dei rinvii: " + str(stato.get("seme_url") or stato.get("seme")), ""]
    righe.append("Ogni voce è un collegamento trovato dentro il contenuto di quella che la "
                 "precede, e l'annidamento è la catena dei rinvii. Fra parentesi quadre sta "
                 "l'esito del nodo, cosicché si veda a colpo d'occhio dove la catena si è "
                 "interrotta e perché. Un nodo già comparso non si espande una seconda volta: "
                 "il grafo ha cicli, e la sua forma di albero è una scelta di lettura.")
    righe.append("")
    righe.append("La stessa informazione, in forma di grafo per un programma, sta in "
                 "`mappa.json`. L'elenco dei nodi con i loro dati sta in `_INDEX.md`.")
    righe.append("")
    righe.append("## Albero")
    righe.append("")
    partenza = stato.get("seme")
    espansi = set()
    pila = [(partenza, 0, "")]
    if partenza not in visti and partenza not in pendenti:
        righe.append("(il punto di partenza non è stato letto, quindi non c'è albero)")
        pila = []
    while pila:
        chiave, livello, ancora = pila.pop()
        scheda = visti.get(chiave) or pendenti.get(chiave)
        rientro = "  " * livello
        testo_ancora = (' - rinvio: "' + cella(ancora) + '"') if ancora else ""
        if chiave in espansi:
            righe.append(rientro + "- " + chiave + " (già comparso sopra)" + testo_ancora)
            continue
        espansi.add(chiave)
        righe.append(rientro + "- " + chiave + " - " + etichetta_nodo(chiave, scheda) +
                     testo_ancora)
        discendenti = figli.get(chiave) or []
        for arco in reversed(discendenti):
            pila.append((arco.get("a"), livello + 1, arco.get("ancora") or ""))
    orfani = [k for k in visti if k not in espansi]
    if orfani:
        righe.append("")
        righe.append("## Nodi senza catena")
        righe.append("")
        righe.append("Questi nodi sono stati visti ma non compaiono nell'albero, cioè l'arco "
                     "che li ha prodotti non è stato registrato: succede ai nodi rimessi in "
                     "coda da una ripresa, perché l'arco appartiene alla corsa precedente.")
        righe.append("")
        for chiave in orfani:
            righe.append("- " + chiave + " - " + etichetta_nodo(chiave, visti.get(chiave)))
    righe.append("")
    righe.append("## Archi")
    righe.append("")
    archi = stato.get("archi") or []
    # L'elenco piano degli archi è utile finché si può leggere; oltre una certa taglia ripete in
    # forma peggiore ciò che l'albero mostra già, e il posto giusto per lui è il file destinato a
    # essere letto da un programma. Il numero resta scritto qui, perché è la misura del grafo.
    if len(archi) > SOGLIA_ARCHI:
        righe.append("Gli archi sono " + str(len(archi)) + ": l'elenco piano ripeterebbe in "
                     "forma peggiore ciò che l'albero qui sopra mostra meglio, e sta in "
                     "`mappa.json`, che è fatto per essere letto da un programma.")
    else:
        righe.append("| da | a | testo del rinvio |")
        righe.append("|---|---|---|")
        for arco in archi:
            righe.append("| " + cella(arco.get("da")) + " | " + cella(arco.get("a")) + " | " +
                         cella(arco.get("ancora")) + " |")
    return "\n".join(righe).rstrip("\n") + "\n"


# ---------------------------------------------------------------------------------------------
# La corsa.
# ---------------------------------------------------------------------------------------------

def scrivi(percorso, contenuto):
    cartella = os.path.dirname(percorso)
    if cartella and not os.path.isdir(cartella):
        os.makedirs(cartella)
    modo = "wb" if isinstance(contenuto, bytes) else "w"
    with open(percorso, modo, **({} if isinstance(contenuto, bytes)
                                 else {"encoding": "utf-8", "newline": "\n"})) as f:
        f.write(contenuto)


def compatto(dati):
    """JSON senza spazi superflui, per il materiale grezzo che nessuno legge a occhio."""
    return json.dumps(dati, ensure_ascii=False, separators=(",", ":")) + "\n"


def unione(prima, seconda, tetto=10):
    """Unisce due elenchi di provenienze conservando l'ordine e senza superare un tetto."""
    fuse = list(OrderedDict.fromkeys(list(prima or []) + list(seconda or [])))
    return fuse[:tetto]


class Corsa:
    """L'attraversamento in ampiezza, con i suoi tetti, il suo stato e la sua uscita su disco."""

    def __init__(self, trasporto, educato, cartella, tetti, esterni=False, esclusi=None,
                 soli=None, lotto=LOTTO_ID, riferisci=None, espandi_esterni=False):
        self.t = trasporto
        self.educato = educato
        self.cartella = cartella
        self.tetti = tetti
        self.esterni = esterni
        self.espandi_esterni = espandi_esterni
        self.esclusi = [d.lower().lstrip(".") for d in (esclusi or [])]
        self.soli = [d.lower().lstrip(".") for d in (soli or [])]
        self.lotto = lotto
        self.riferisci = riferisci or (lambda messaggio: None)
        self.stato = {
            "versione": 1,
            "seme": None,
            "seme_url": None,
            "creato": data_di(time.time()),
            "aggiornato": data_di(time.time()),
            "tetti": dict(tetti),
            "esterni": esterni,
            "visti": OrderedDict(),
            "archi": [],
            "pendenti": [],
            "falliti": [],
        }
        # Gli archi già registrati, per non ripetere lo stesso rinvio quando due contenuti
        # diversi portano allo stesso posto e per non gonfiare la mappa a ogni ripresa.
        self.archi_visti = set()

    # -- stato ---------------------------------------------------------------------------------

    def percorso_stato(self):
        return os.path.join(self.cartella, "stato.json")

    def salva(self):
        self.stato["aggiornato"] = data_di(time.time())
        # Il marcatore che esenta questo sottoalbero dal normalizzatore di Markdown del sistema.
        # Non è un dettaglio di comodo: i file scritti qui riportano prosa di terzi verbatim, e
        # la convenzione di questo sistema, cioè un paragrafo per riga sorgente, è una regola
        # sui documenti che scriviamo noi e non una licenza a riscrivere il testo di qualcun
        # altro. Senza il marcatore il controllo pre-commit proporrebbe di unire righe dentro le
        # citazioni, che è esattamente ciò che l'eccezione dichiarata dalla regola di stile
        # vieta per il materiale copiato da una fonte esterna.
        scrivi(os.path.join(self.cartella, ".md-unwrap-ignore"),
               "Materiale di terzi riportato verbatim: la convenzione di un paragrafo per riga\n"
               "sorgente vale per i documenti di questo progetto e non per le citazioni.\n")
        scrivi(self.percorso_stato(),
               json.dumps(self.stato, indent=2, ensure_ascii=False) + "\n")
        scrivi(os.path.join(self.cartella, "_INDEX.md"), markdown_indice(self.stato))
        scrivi(os.path.join(self.cartella, "MAPPA.md"), markdown_mappa(self.stato))
        scrivi(os.path.join(self.cartella, "mappa.json"),
               json.dumps(mappa_json(self.stato), indent=2, ensure_ascii=False) + "\n")

    def arco(self, origine, destinazione, ancora):
        """Registra un rinvio da un contenuto a un altro, che è cio di cui la mappa è fatta."""
        if not origine or not destinazione or origine == destinazione:
            return
        firma = (origine, destinazione)
        if firma in self.archi_visti:
            return
        self.archi_visti.add(firma)
        self.stato.setdefault("archi", []).append({
            "da": origine, "a": destinazione, "ancora": (ancora or "")[:200],
        })

    def rinomina_arco(self, vecchia, nuova):
        """Sposta gli archi che puntavano a un collegamento breve sul posto in cui porta.

        Serve perché un collegamento breve entra nella mappa prima di sapere che cosa sia: senza
        questo passaggio la mappa conserverebbe un nodo intermedio che non è una fonte ma un
        rinvio, e la catena dei rinvii mostrerebbe un passo in più che non esiste.
        """
        for arco in self.stato.get("archi") or []:
            if arco.get("a") == vecchia:
                arco["a"] = nuova
                self.archi_visti.add((arco.get("da"), nuova))

    def carica(self):
        percorso = self.percorso_stato()
        if not os.path.isfile(percorso):
            raise Errore("non c'è alcuno stato da riprendere in " + self.cartella)
        with open(percorso, encoding="utf-8") as f:
            dati = json.load(f)
        dati["visti"] = OrderedDict(dati.get("visti") or {})
        dati.setdefault("archi", [])
        self.stato = dati
        self.archi_visti = set((a.get("da"), a.get("a")) for a in dati["archi"])
        for chiave in ("max_post", "max_esterni", "max_profondita"):
            if self.tetti.get(chiave) is not None:
                self.stato.setdefault("tetti", {})[chiave] = self.tetti[chiave]
        self.tetti = dict(self.stato.get("tetti") or {})
        if self.esterni:
            self.stato["esterni"] = True
        self.esterni = bool(self.stato.get("esterni"))

    def quanti(self, tipo):
        return sum(1 for v in self.stato["visti"].values()
                   if v.get("tipo") == tipo and v.get("esito") == "scaricato")

    def registra(self, chiave, scheda):
        esistente = self.stato["visti"].get(chiave)
        if esistente:
            scheda["da"] = unione(esistente.get("da"), scheda.get("da"))
        self.stato["visti"][chiave] = scheda

    def rinvia(self, elementi, motivo):
        gia = set()
        for voce in self.stato["pendenti"]:
            gia.add(voce.get("chiave"))
        for elemento in elementi:
            if elemento["chiave"] in self.stato["visti"] or elemento["chiave"] in gia:
                continue
            gia.add(elemento["chiave"])
            self.stato["pendenti"].append({
                "chiave": elemento["chiave"],
                "tipo": elemento["tipo"],
                "profondità": elemento["profondità"],
                "da": elemento.get("da") or [],
                "ancora": elemento.get("ancora") or "",
                "motivo": motivo,
            })

    def una_pagina(self, indirizzo, profondita=1):
        """Legge una pagina esterna sola, dentro questa corsa, senza espanderne i rinvii.

        Esiste perché la domanda che il progetto si pone piu' spesso sul corpus non e' quella per
        cui un crawler e' fatto. Un crawler risponde a "che cosa c'e' a partire da qui"; la
        domanda ricorrente e' invece "manca questa pagina, che so gia' quale e'", e per quella
        l'attraversamento e' lo strumento sbagliato due volte, perche' scarica cio' che non serve
        e perche' per arrivare a una pagina nota bisogna passare da chi la linka.

        La pagina entra nella corsa come tutte le altre, cioe' con la stessa verifica di
        `robots.txt`, lo stesso intervallo fra richieste, lo stesso estrattore, il grezzo accanto
        al derivato e la registrazione in `stato.json`, cosicche' il censimento la veda senza
        sapere da dove sia arrivata. Cio' che non fa, ed e' il suo punto, e' seminare i rinvii
        trovati: chi chiede una pagina ha chiesto una pagina.

        La profondita' dichiarata serve solo alla mappa e non a un tetto, perche' qui non c'e'
        frontiera da limitare; il valore predefinito e' uno, che e' la distanza a cui un crawler
        l'avrebbe trovata se fosse partito dal nodo che la cita.
        """
        chiave = "web:" + indirizzo
        if chiave in self.stato["visti"]:
            scheda = self.stato["visti"][chiave]
            return False, scheda.get("esito"), scheda.get("file")
        # Il frontiere fittizio raccoglie i rinvii e viene buttato: gli archi che `semina`
        # registra nella mappa restano, ed e' cio' che si vuole, perche' la mappa deve dire che
        # cosa questa pagina cita anche se non lo leggeremo.
        cestino = OrderedDict()
        self.fai_web([{"chiave": chiave, "tipo": "web", "profondità": profondita,
                       "da": ["richiesta esplicita"], "ancora": ""}], cestino)
        scheda = self.stato["visti"].get(chiave) or {}
        return True, scheda.get("esito"), scheda.get("file")

    def promuovi_transitori(self):
        """Rimette fra i pendenti i nodi catalogati per un `robots.txt` indisponibile.

        Serve alle corse fatte prima che quel rifiuto fosse distinto da un divieto vero, dove il
        nodo risulta deciso e nessuna ripresa lo ritenta. Restituisce quanti nodi sono stati
        promossi e l'insieme degli host a cui appartengono, perché il numero da solo non dice se
        il recupero riguardi una fonte o un dominio intero.

        La promozione toglie il nodo da `visti`: un nodo che restasse registrato verrebbe saltato
        dall'attraversamento, che salta per costruzione tutto ciò che ha già visto.
        """
        promossi, host = [], set()
        for chiave, scheda in list(self.stato["visti"].items()):
            if scheda.get("esito") != "catalogato":
                continue
            if scheda.get("motivo") != MOTIVO_ROBOTS_TRANSITORIO:
                continue
            promossi.append({
                "chiave": chiave,
                "tipo": scheda.get("tipo") or "web",
                "profondità": scheda.get("profondità", 0),
                "da": scheda.get("da") or [],
                "ancora": scheda.get("ancora") or "",
            })
            host.add(scheda.get("host") or host_di(chiave.split(":", 1)[-1]) or "host-ignoto")
            del self.stato["visti"][chiave]
        if promossi:
            self.rinvia(promossi, MOTIVO_ROBOTS_TRANSITORIO)
        return len(promossi), host

    def fallisci(self, chiave, codice, messaggio):
        self.stato["falliti"].append({"chiave": chiave, "codice": codice,
                                      "messaggio": cella(messaggio)})

    # -- semina --------------------------------------------------------------------------------

    def aggiungi(self, gruppo, chiave, tipo, profondita, da, ancora, nota=""):
        if chiave in gruppo:
            gruppo[chiave]["da"] = unione(gruppo[chiave]["da"], da)
            if nota:
                gruppo[chiave]["commenti_puntati"] = unione(
                    gruppo[chiave].get("commenti_puntati"), [nota])
            return
        gruppo[chiave] = {
            "chiave": chiave, "tipo": tipo, "profondità": profondita,
            "da": list(da or []), "ancora": ancora or "",
            "commenti_puntati": [nota] if nota else [],
        }

    def semina(self, gruppo, origine, profondita, coppie):
        """Classifica i collegamenti trovati in un contenuto e li mette nella prossima onda.

        I collegamenti che non si scaricheranno non entrano nella frontiera ma direttamente fra
        i visti, con il proprio esito: sono terminali, quindi tenerli in coda per scartarli più
        tardi sarebbe lavoro inutile, e soprattutto non consumano il tetto delle pagine esterne,
        che deve contare i tentativi e non le classificazioni.
        """
        for ancora, indirizzo in coppie:
            esito = canonica(indirizzo)
            if not esito:
                continue
            tipo, chiave, nota = esito
            piena = tipo + ":" + chiave
            # L'arco si registra sempre, prima di ogni decisione su che cosa fare del nodo: la
            # mappa deve dire che quel rinvio esiste anche quando il nodo non verra letto, e
            # anzi soprattutto allora, perché è così che si vede dove la catena si interrompe.
            self.arco(origine, piena, ancora)
            if tipo == "breve":
                self.aggiungi(gruppo, piena, "breve", profondita, [origine], ancora)
                continue
            if tipo == "reddit":
                if piena in self.stato["visti"]:
                    scheda = self.stato["visti"][piena]
                    scheda["da"] = unione(scheda.get("da"), [origine])
                    if nota:
                        scheda["commenti_puntati"] = unione(scheda.get("commenti_puntati"), [nota])
                    continue
                self.aggiungi(gruppo, piena, "reddit", profondita, [origine], ancora, nota)
                continue
            if piena in self.stato["visti"]:
                scheda = self.stato["visti"][piena]
                scheda["da"] = unione(scheda.get("da"), [origine])
                continue
            motivo = self.perche_non_scaricare(chiave)
            if motivo:
                self.registra(piena, {"tipo": "web", "profondità": profondita,
                                      "esito": "catalogato", "motivo": motivo,
                                      "da": [origine], "ancora": ancora})
                continue
            self.aggiungi(gruppo, piena, "web", profondita, [origine], ancora)

    def perche_non_scaricare(self, indirizzo):
        """Il motivo per cui un indirizzo esterno non si scarica, oppure una stringa vuota."""
        if not self.esterni:
            return "raccolta delle pagine esterne non richiesta per questa corsa"
        host = host_di(indirizzo)
        if self.soli and not suffisso_in(host, self.soli):
            return "fuori dai domini richiesti"
        if self.esclusi and suffisso_in(host, self.esclusi):
            return "dominio escluso da chi ha lanciato la corsa"
        return motivo_catalogo(indirizzo) or ""

    # -- esecuzione ----------------------------------------------------------------------------

    def esegui(self, iniziali):
        coda = list(iniziali)
        while coda:
            profondita = min(v["profondità"] for v in coda)
            onda = OrderedDict()
            resto = []
            for voce in coda:
                if voce["profondità"] == profondita:
                    self.aggiungi(onda, voce["chiave"], voce["tipo"], voce["profondità"],
                                  voce.get("da"), voce.get("ancora"),
                                  ", ".join(voce.get("commenti_puntati") or []))
                else:
                    resto.append(voce)
            coda = resto
            massima = self.tetti.get("max_profondita") or 0
            if massima and profondita > massima:
                self.rinvia(list(onda.values()) + coda, "oltre il tetto di profondità")
                break
            onda = self.risolvi_onda(onda)
            onda = OrderedDict((k, v) for k, v in onda.items()
                               if k not in self.stato["visti"])
            if not onda:
                continue
            prossima = OrderedDict()
            self.riferisci("livello " + str(profondita) + ": " + str(len(onda)) +
                           " elementi da leggere, " + str(len(coda)) + " in attesa")
            reddit = [v for v in onda.values() if v["tipo"] == "reddit"]
            web = [v for v in onda.values() if v["tipo"] == "web"]
            self.fai_reddit(reddit, prossima)
            self.fai_web(web, prossima)
            self.salva()
            coda.extend(prossima.values())
            if self.esaurita() and coda:
                self.rinvia(coda, "tetti esauriti")
                self.salva()
                break

    def esaurita(self):
        post = self.tetti.get("max_post") or 0
        esterni = self.tetti.get("max_esterni") or 0
        fine_post = bool(post) and self.quanti("reddit") >= post
        fine_web = (not self.esterni) or (bool(esterni) and self.quanti("web") >= esterni)
        return fine_post and fine_web

    def risolvi_onda(self, onda):
        """Risolve in un lotto i collegamenti brevi dell'onda, e li riclassifica."""
        brevi = [v for v in onda.values() if v["tipo"] == "breve"]
        if not brevi:
            return onda
        # La chiave di un elemento porta il prefisso del genere, mentre il servizio vuole il
        # solo percorso: passargli la chiave intera produce una risoluzione che fallisce sempre
        # e in silenzio, cioè un ramo del grafo che sparisce senza che nulla lo dica.
        percorsi = dict((v["chiave"], v["chiave"].split(":", 1)[1]) for v in brevi)
        mappa = risolvi_brevi(self.t, list(percorsi.values()))
        risolta = OrderedDict((k, v) for k, v in onda.items() if v["tipo"] != "breve")
        for voce in brevi:
            destinazione = mappa.get(percorsi[voce["chiave"]])
            if not destinazione:
                self.registra(voce["chiave"], {
                    "tipo": "web", "profondità": voce["profondità"], "esito": "catalogato",
                    "motivo": "collegamento breve che l'archivio non sa risolvere",
                    "da": voce.get("da") or [], "ancora": voce.get("ancora") or "",
                })
                continue
            esito = canonica(destinazione)
            if not esito or esito[0] == "breve":
                continue
            tipo, chiave, nota = esito
            piena = tipo + ":" + chiave
            self.rinomina_arco(voce["chiave"], piena)
            if piena in self.stato["visti"]:
                continue
            if tipo == "web":
                motivo = self.perche_non_scaricare(chiave)
                if motivo:
                    self.registra(piena, {
                        "tipo": "web", "profondità": voce["profondità"], "esito": "catalogato",
                        "motivo": motivo, "da": voce.get("da") or [],
                        "ancora": voce.get("ancora") or "",
                    })
                    continue
            self.aggiungi(risolta, piena, tipo, voce["profondità"], voce.get("da"),
                          voce.get("ancora"), nota)
        return risolta

    def fai_reddit(self, elementi, prossima):
        if not elementi:
            return
        tetto = self.tetti.get("max_post") or 0
        if tetto:
            resta = max(0, tetto - self.quanti("reddit"))
            ammessi, rinviati = elementi[:resta], elementi[resta:]
        else:
            ammessi, rinviati = elementi, []
        if rinviati:
            self.rinvia(rinviati, "oltre il tetto dei post")
        if not ammessi:
            return
        identificativi = [v["chiave"].split(":", 1)[1] for v in ammessi]
        trovati = post_per_id(self.t, identificativi, self.lotto)
        for voce in ammessi:
            identificativo = voce["chiave"].split(":", 1)[1]
            record = trovati.get(identificativo)
            if not record:
                self.registra(voce["chiave"], {
                    "tipo": "reddit", "profondità": voce["profondità"], "esito": "assente",
                    "motivo": "non indicizzato nell'archivio, che non prova che il post non "
                              "esista su Reddit",
                    "da": voce.get("da") or [], "ancora": voce.get("ancora") or "",
                })
                continue
            try:
                nodi = albero_commenti(self.t, identificativo)
            except Errore as e:
                nodi = []
                self.fallisci(voce["chiave"], "albero", str(e))
            scheda = {
                "tipo": "reddit", "profondità": voce["profondità"], "esito": "scaricato",
                "da": voce.get("da") or [], "ancora": voce.get("ancora") or "",
                "commenti_puntati": voce.get("commenti_puntati") or [],
                "titolo": record.get("title"), "autore": record.get("author"),
                "autore_id": record.get("author_fullname"),
                "pubblicato": data_di(record.get("created_utc")),
                "punteggio": record.get("score"), "commenti": record.get("num_comments"),
                "subreddit": record.get("subreddit"),
                "archiviato": data_di(record.get("retrieved_on")),
            }
            nome = identificativo + "-" + sigla(record.get("title")) + ".md"
            scheda["file"] = "posts/" + nome
            # Il grezzo si scrive compatto e non indentato, perché è materiale per un
            # programma e non per gli occhi: su un albero di commenti di un thread molto
            # popolare l'indentazione è stata misurata costare più della metà del file.
            scrivi(os.path.join(self.cartella, "raw", "posts", identificativo + ".json"),
                   compatto(record))
            scrivi(os.path.join(self.cartella, "raw", "tree", identificativo + ".json"),
                   compatto(nodi))
            scrivi(os.path.join(self.cartella, "posts", nome),
                   markdown_post(record, nodi, scheda))
            self.registra(voce["chiave"], scheda)
            coppie = estrai_link(record.get("selftext") or "")
            # Un post che è un rinvio porta la sua destinazione nel campo dell'indirizzo, e
            # quella è una fonte a tutti gli effetti; un post di testo porta là invece il
            # proprio permalink, e seguirlo sarebbe seguire sé stessi. Il confronto si fa sulla
            # chiave canonica e non sul prefisso della stringa, perché le due forme
            # dell'indirizzo di uno stesso post differiscono per lo spezzone del titolo.
            collegamento = record.get("url") or ""
            esito_collegamento = canonica(collegamento) if collegamento else None
            if collegamento and not (esito_collegamento and
                                     esito_collegamento[0] == "reddit" and
                                     esito_collegamento[1] == identificativo):
                coppie = coppie + [("collegamento del post", collegamento)]
            for _, _, dato in percorri_albero(nodi):
                coppie = coppie + estrai_link(dato.get("body") or "")
            self.semina(prossima, voce["chiave"], voce["profondità"] + 1, coppie)

    def fai_web(self, elementi, prossima):
        if not elementi:
            return
        if not self.esterni:
            for voce in elementi:
                self.registra(voce["chiave"], {
                    "tipo": "web", "profondità": voce["profondità"], "esito": "catalogato",
                    "motivo": "raccolta delle pagine esterne non richiesta per questa corsa",
                    "da": voce.get("da") or [], "ancora": voce.get("ancora") or "",
                })
            return
        tetto = self.tetti.get("max_esterni") or 0
        if tetto:
            resta = max(0, tetto - self.quanti("web"))
            ammessi, rinviati = elementi[:resta], elementi[resta:]
        else:
            ammessi, rinviati = elementi, []
        if rinviati:
            self.rinvia(rinviati, "oltre il tetto delle pagine esterne")
        for voce in ammessi:
            indirizzo = voce["chiave"].split(":", 1)[1]
            consentito, motivo = self.educato.permesso(indirizzo)
            if not consentito:
                # Due rifiuti che il codice trattava allo stesso modo non sono la stessa cosa,
                # e confonderli è il difetto che questa distinzione ripara. Un divieto scritto in
                # `robots.txt` è una proprietà stabile del sito, e registrarlo come catalogato in
                # via definitiva è corretto. Un `robots.txt` che non si è potuto leggere non dice
                # invece nulla del sito: dice che in quell'istante il servizio, o la rete di chi
                # legge, non rispondeva. Registrarlo come catalogato trasforma un guasto di pochi
                # minuti in una esclusione permanente e silenziosa, che nessuna ripresa ritenta
                # perché il nodo risulta già deciso. Va quindi fra i pendenti, che è lo stesso
                # trattamento che questo programma riserva a ciò che un tetto ha escluso, e per la
                # medesima ragione: l'esclusione non è una proprietà del contenuto.
                if motivo == MOTIVO_ROBOTS_TRANSITORIO:
                    self.rinvia([voce], motivo)
                    continue
                self.registra(voce["chiave"], {
                    "tipo": "web", "profondità": voce["profondità"], "esito": "catalogato",
                    "motivo": motivo, "da": voce.get("da") or [],
                    "ancora": voce.get("ancora") or "",
                })
                continue
            self.educato.attendi(indirizzo)
            codice, corpo, intestazioni = chiama(self.t, indirizzo, TENTATIVI_ESTERNI)
            if codice != 200 or not corpo:
                self.registra(voce["chiave"], {
                    "tipo": "web", "profondità": voce["profondità"], "esito": "fallito",
                    "motivo": "codice " + str(codice),
                    "da": voce.get("da") or [], "ancora": voce.get("ancora") or "",
                })
                self.fallisci(voce["chiave"], codice,
                              corpo[:200].decode("utf-8", errors="replace"))
                continue
            tipo_contenuto = (intestazioni.get("content-type") or "").lower()
            if tipo_contenuto and not any(t in tipo_contenuto for t in
                                          ("text/html", "text/plain", "xhtml", "application/json",
                                           "text/markdown", "application/xml", "text/xml")):
                self.registra(voce["chiave"], {
                    "tipo": "web", "profondità": voce["profondità"], "esito": "catalogato",
                    "motivo": "il server dichiara il tipo " + cella(tipo_contenuto) +
                              ", che non è testo da leggere",
                    "da": voce.get("da") or [], "ancora": voce.get("ancora") or "",
                })
                continue
            titolo, testo, scarso = html_a_testo(corpo, intestazioni)
            if scarso:
                self.registra(voce["chiave"], {
                    "tipo": "web", "profondità": voce["profondità"], "esito": "catalogato",
                    "motivo": scarso,
                    "da": voce.get("da") or [], "ancora": voce.get("ancora") or "",
                })
                continue
            marchio = impronta(indirizzo)
            host = host_di(indirizzo) or "host-ignoto"
            nome = marchio + "-" + sigla(titolo or indirizzo) + ".md"
            scheda = {
                "tipo": "web", "profondità": voce["profondità"], "esito": "scaricato",
                "da": voce.get("da") or [], "ancora": voce.get("ancora") or "",
                "titolo": titolo, "file": "esterni/" + host + "/" + nome,
            }
            scrivi(os.path.join(self.cartella, "raw", "esterni", marchio + ".html"), corpo)
            scrivi(os.path.join(self.cartella, "esterni", host, nome),
                   markdown_esterno(indirizzo, intestazioni.get("x-indirizzo-finale"),
                                    titolo, testo, scheda))
            self.registra(voce["chiave"], scheda)
            # I collegamenti di una pagina esterna si seminano soltanto se qualcuno lo ha
            # chiesto, e la ragione e' misurata invece che prudenziale. Una pagina di wiki
            # rinvia all'intera wiki piu' le proprie voci di navigazione: sulle 287 pagine gia'
            # su disco di questa corsa, seminarle tutte produrrebbe 4016 nodi nuovi, di cui 1213
            # verso l'archivio di immagini del medesimo sito, 950 verso un'enciclopedia
            # generalista e centinaia verso social e negozi di applicazioni. Fino al 2026-09-14
            # non accadeva, ma per un difetto e non per una scelta: l'estrazione non riconosceva
            # la forma con cui l'estrattore da HTML scrive i collegamenti, quindi le pagine
            # esterne erano foglie per caso. Ora sono foglie per scelta, e chi voglia il
            # contrario lo dichiara.
            if self.espandi_esterni:
                self.semina(prossima, voce["chiave"], voce["profondità"] + 1,
                            estrai_link(testo))
            else:
                # Gli archi si registrano comunque, perche' la mappa deve dire che cosa una
                # pagina cita anche quando non la seguiremo: e' la stessa ragione per cui si
                # registrano gli archi verso i nodi che un tetto ha escluso.
                for ancora, indirizzo in estrai_link(testo):
                    esito = canonica(indirizzo)
                    if esito:
                        self.arco(voce["chiave"], esito[0] + ":" + esito[1], ancora)


# ---------------------------------------------------------------------------------------------
# I comandi.
# ---------------------------------------------------------------------------------------------

def seme_di(argomento):
    """Il punto di partenza, che può essere un indirizzo o un identificativo nudo."""
    argomento = (argomento or "").strip()
    if not argomento:
        raise Errore("serve un indirizzo o un identificativo di post")
    if argomento.lower().startswith(("http://", "https://")) or argomento.startswith("//"):
        esito = canonica(argomento)
        if not esito:
            raise Errore("non riconosco questo indirizzo: " + argomento)
        if esito[0] == "web":
            raise Errore("questo indirizzo non è un post di Reddit: " + argomento)
        return esito[0], esito[1]
    if re.fullmatch(RE_ID, argomento, re.I):
        return "reddit", argomento.lower()
    raise Errore("non riconosco questo punto di partenza: " + argomento)


def cartella_di(radice, record, identificativo):
    nome = ("reddit-" + sigla(record.get("subreddit") if record else "", 24) + "-" +
            identificativo + "-" + datetime.datetime.now().strftime("%Y-%m-%d"))
    return os.path.join(radice, "_notes", "fonti", nome)


def prova_a_vuoto(trasporto, tipo, chiave, riferisci):
    """Scarica il solo punto di partenza e riferisce la frontiera che genererebbe.

    Non è la prova a vuoto dell'orchestratore di export di questo pacchetto, e la differenza va
    detta: quella non chiama nulla, questa chiama una volta, perché il grafo di un crawler non
    si conosce senza guardare il primo nodo. Non scrive nulla su disco.
    """
    if tipo == "breve":
        mappa = risolvi_brevi(trasporto, [chiave])
        if not mappa:
            raise Errore("l'archivio non sa risolvere il collegamento breve " + chiave)
        tipo, chiave, _ = canonica(list(mappa.values())[0])
    trovati = post_per_id(trasporto, [chiave])
    record = trovati.get(chiave)
    if not record:
        raise Errore("l'archivio non ha il post " + chiave + ": può essere troppo recente per "
                     "essere indicizzato, e questo non prova che non esista su Reddit")
    nodi = albero_commenti(trasporto, chiave)
    commenti = [d for _, g, d in percorri_albero(nodi) if g != "more"]
    coppie = estrai_link(record.get("selftext") or "")
    for dato in commenti:
        coppie = coppie + estrai_link(dato.get("body") or "")
    reddit, esterni, catalogo, brevi = OrderedDict(), OrderedDict(), OrderedDict(), OrderedDict()
    for ancora, indirizzo in coppie:
        esito = canonica(indirizzo)
        if not esito:
            continue
        genere, canone, _ = esito
        if genere == "reddit":
            reddit[canone] = ancora
        elif genere == "breve":
            brevi[canone] = ancora
        else:
            motivo = motivo_catalogo(canone)
            if motivo:
                catalogo[canone] = motivo
            else:
                esterni[canone] = ancora
    riferisci("Punto di partenza: r/" + str(record.get("subreddit")) + " - " + str(chiave))
    riferisci("Titolo: " + str(record.get("title")))
    riferisci("Autore: " + str(record.get("author")) + " (" +
              str(record.get("author_fullname")) + ")")
    riferisci("Pubblicato il " + data_di(record.get("created_utc")) + ", archiviato il " +
              data_di(record.get("retrieved_on")))
    riferisci("Corpo: " + str(len(record.get("selftext") or "")) + " caratteri")
    riferisci("Commenti: " + str(record.get("num_comments")) + " dichiarati, " +
              str(len(commenti)) + " nodi nell'albero")
    riferisci("Collegamenti nel post e nei commenti: " + str(len(coppie)) + " prima della "
              "deduplicazione")
    riferisci("")
    riferisci("Frontiera al primo livello, dopo la deduplicazione:")
    riferisci("  post di Reddit da leggere: " + str(len(reddit)))
    riferisci("  collegamenti brevi da risolvere: " + str(len(brevi)))
    riferisci("  pagine esterne scaricabili: " + str(len(esterni)))
    riferisci("  indirizzi da catalogare senza scaricare: " + str(len(catalogo)))
    riferisci("")
    riferisci("Costo del primo livello: " +
              str(max(1, -(-len(reddit) // LOTTO_ID))) + " richieste per i post in lotti, più " +
              str(len(reddit)) + " per i loro alberi di commenti, più " + str(len(esterni)) +
              " per le pagine esterne.")
    riferisci("La proiezione oltre il primo livello non si fa per ipotesi: dipende da quanti "
              "collegamenti portano i post trovati, che si sanno solo leggendoli. Su un post "
              "raccoglitore la crescita è rapida, quindi conviene una corsa con un tetto basso "
              "prima di una piena.")
    if catalogo:
        # Si raggruppa per host, perché dodici righe identiche su YouTube dicono una cosa sola e
        # la dicono dodici volte, nascondendo gli altri motivi sotto il taglio dell'elenco.
        per_host = OrderedDict()
        for indirizzo, motivo in catalogo.items():
            voce = per_host.setdefault(host_di(indirizzo), [0, motivo])
            voce[0] += 1
        riferisci("")
        riferisci("Motivi di catalogazione osservati al primo livello, per host:")
        for host, (quanti, motivo) in sorted(per_host.items(), key=lambda x: -x[1][0]):
            riferisci("  " + host + " (" + str(quanti) + "): " + motivo)
    return 0


def collaudo():
    """Esercita la logica contro il trasporto finto, senza rete e senza scrivere niente.

    I controlli negativi, cioè quelli marcati come tali, fallirebbero se un presidio venisse
    rimosso: sono la ragione per cui questa suite serve a chi modifica il file e non soltanto a
    chi lo ha scritto.
    """
    esiti = []

    def prova(nome, condizione):
        esiti.append((nome, bool(condizione)))

    # -- normalizzazione e riconoscimento degli indirizzi -------------------------------------
    base = "https://www.reddit.com/r/PokemonHome/comments/1laqzce/guide_on_pokemon_home/"
    forme = [
        base,
        base + "?utm_source=share&utm_medium=web3x&utm_term=1&utm_content=share_button",
        "https://old.reddit.com/r/PokemonHome/comments/1laqzce/guide/",
        "https://redd.it/1laqzce",
        "https://www.reddit.com/r/PokemonHome/comments/1laqzce/guide/mxbs7t2/?context=3",
    ]
    chiavi = set()
    for forma in forme:
        genere, chiave, _ = canonica(forma)
        chiavi.add((genere, chiave))
    prova("le cinque forme dello stesso post danno una sola chiave", chiavi == {("reddit", "1laqzce")})
    prova("il permalink a un commento annota il commento",
          canonica(forme[4])[2] == "mxbs7t2")
    prova("un collegamento breve si riconosce come da risolvere",
          canonica("https://www.reddit.com/r/running/s/3TzXiyxaMD") ==
          ("breve", "/r/running/s/3TzXiyxaMD", ""))
    prova("due indirizzi esterni che differiscono per la sola coda di provenienza coincidono",
          canonica("https://pokejungle.net/guida/?utm_source=x")[1] ==
          canonica("https://pokejungle.net/guida")[1])
    prova("il frammento non fa due indirizzi diversi",
          canonica("https://esempio.it/a#uno")[1] == canonica("https://esempio.it/a#due")[1])
    prova("un parametro che non è di provenienza resta",
          "v=abc" in canonica("https://esempio.it/p?v=abc&utm_medium=x")[1])
    prova("uno schema che non è http si rifiuta", canonica("mailto:qualcuno@esempio.it") is None)
    prova("negativo: una pagina di Reddit che non è un post non diventa un post",
          canonica("https://www.reddit.com/r/PokemonHome/")[0] == "web")
    prova("negativo: `comments` nel percorso di un altro sito non diventa un post",
          canonica("https://esempio.it/comments/abcdef/")[0] == "web")

    # -- estrazione dei collegamenti ----------------------------------------------------------
    testo = ("Vedi [questo](https://a.it/uno) e <https://b.it/due> e anche https://c.it/tre, "
             "più [questo di nuovo](https://a.it/uno).")
    coppie = estrai_link(testo)
    prova("le tre sintassi di collegamento si estraggono tutte", len(coppie) == 3)
    prova("l'ancora si conserva", coppie[0][0] == "questo")
    prova("un indirizzo ripetuto non si estrae due volte",
          len([u for _, u in coppie if u == "https://a.it/uno"]) == 1)
    prova("la punteggiatura finale non entra nell'indirizzo",
          "https://c.it/tre" in [u for _, u in coppie])

    # -- catalogazione ------------------------------------------------------------------------
    prova("un video si cataloga", "trascrizione" in (motivo_catalogo("https://youtu.be/xyz") or ""))
    prova("una variante con www si cataloga allo stesso modo",
          motivo_catalogo("https://www.youtube.com/watch?v=x") is not None)
    prova("un PDF rimanda al pacchetto dei documenti",
          "doc-ingest" in (motivo_catalogo("https://esempio.it/a.pdf") or ""))
    prova("una pagina di prosa non si cataloga",
          motivo_catalogo("https://pokejungle.net/guida") is None)

    # -- protezione del testo di terzi --------------------------------------------------------
    prova("negativo: una riga che apre con un cancelletto viene protetta",
          protetto("# titolo di terzi").startswith("\\#"))
    prova("dentro un blocco recintato il cancelletto non si tocca",
          protetto("```\n# commento di codice\n```") == "```\n# commento di codice\n```")

    # -- lotti, deduplicazione e albero -------------------------------------------------------
    molti = {}
    for numero_progressivo in range(250):
        identificativo = "p" + str(numero_progressivo).rjust(5, "0")
        molti[identificativo] = {"id": identificativo, "title": "t", "subreddit": "s",
                                 "selftext": "", "author": "a", "author_fullname": "t2_a"}
    finto = TrasportoFinto(post=molti)
    trovati = post_per_id(finto, list(molti.keys()))
    prova("duecentocinquanta post si chiedono in tre richieste e non in duecentocinquanta",
          len(finto.chiamate) == 3 and len(trovati) == 250)
    finto_dedup = TrasportoFinto(post=molti)
    post_per_id(finto_dedup, ["p00001", "p00001", "p00002"])
    prova("un identificativo ripetuto non si chiede due volte",
          "ids=p00001%2Cp00002" in finto_dedup.chiamate[0])

    albero = [{"kind": "t1", "data": {"body": "a", "author": "u1", "replies": [
        {"kind": "t1", "data": {"body": "b", "author": "u2", "replies": [
            {"kind": "more", "data": {"children": ["x", "y", "z"]}}]}}]}}]
    percorsi = list(percorri_albero(albero))
    prova("l'albero si percorre in profondità conservando il livello",
          [p for p, _, _ in percorsi] == [0, 1, 2])
    prova("un ramo collassato si riconosce",
          percorsi[2][1] == "more" and len(percorsi[2][2]["children"]) == 3)

    # -- limiti di frequenza e guasti ---------------------------------------------------------
    rifiuto = TrasportoFinto(post=molti, programma=[
        (429, b"", {"x-ratelimit-reset": "7"}),
        (200, json.dumps({"data": []}).encode(), {}),
    ])
    chiama(rifiuto, ARCTIC + "/api/posts/ids?ids=p00001")
    prova("un rifiuto per eccesso di frequenza attende quanto il servizio dichiara",
          rifiuto.attese == [7.0])
    anomalo = TrasportoFinto(programma=[
        (429, b"", {"x-ratelimit-reset": "99999"}),
        (200, json.dumps({"data": []}).encode(), {}),
    ])
    chiama(anomalo, ARCTIC + "/api/posts/ids?ids=p00001")
    prova("negativo: un'attesa dichiarata assurda si limita al tetto",
          anomalo.attese == [ATTESA_MASSIMA_RIFIUTO])
    guasti = TrasportoFinto(programma=[
        (GUASTO, b"rete", {}), (GUASTO, b"rete", {}),
        (200, json.dumps({"data": []}).encode(), {}),
    ])
    chiama(guasti, ARCTIC + "/api/posts/ids?ids=p00001")
    prova("un guasto transitorio fa raddoppiare l'attesa", guasti.attese == [1.0, 2.0])
    preventiva = TrasportoFinto(programma=[
        (200, json.dumps({"data": []}).encode(),
         {"x-ratelimit-remaining": "0", "x-ratelimit-reset": "3"}),
    ])
    chiama(preventiva, ARCTIC + "/api/posts/ids?ids=p00001")
    prova("quando le richieste della finestra sono esaurite si attende prima di chiedere",
          preventiva.attese == [3.0])
    errato = TrasportoFinto(programma=[
        (200, json.dumps({"data": None, "error": "'permalink' is not a valid field"}).encode(), {}),
    ])
    fallito = False
    try:
        arctic(errato, "/api/posts/ids", {"ids": "x"})
    except Errore as e:
        fallito = "permalink" in str(e)
    prova("negativo: un errore che arriva con codice duecento non passa per risposta vuota",
          fallito)


    # -- le quattro forme di collegamento ------------------------------------------------------
    prova("la forma Markdown si riconosce con la sua ancora",
          ("guida", "https://a.it/x") in estrai_link("vedi [guida](https://a.it/x) qui"))
    prova("la forma angolare si riconosce",
          ("", "https://a.it/y") in estrai_link("vedi <https://a.it/y> qui"))
    prova("l'indirizzo nudo si riconosce",
          ("", "https://a.it/z") in estrai_link("vedi https://a.it/z qui"))
    # La forma che mancava, ed e' quella che l'estrattore da HTML produce da se'. Senza di essa
    # il grafo non si espandeva quasi mai attraverso una pagina esterna.
    tondo = estrai_link("- YouTube (https://www.youtube.com/user/X)")
    prova("la forma con l'ancora seguita dall'indirizzo fra tonde si riconosce",
          ("- YouTube", "https://www.youtube.com/user/X") in tondo)
    prova("negativo: la forma con le tonde non duplica quella Markdown, che viene prima",
          len(estrai_link("[guida](https://a.it/x)")) == 1)
    prova("su un testo estratto da una pagina si trovano tutti i suoi collegamenti e non due",
          len(estrai_link("\n".join("- voce %d (https://a.it/%d)" % (i, i)
                                    for i in range(20)))) == 20)
    prova("negativo: un indirizzo ripetuto in due forme si conta una volta sola",
          len(estrai_link("[a](https://a.it/x) e poi https://a.it/x")) == 1)

    # -- robots e intervallo fra richieste ----------------------------------------------------
    finto_web = TrasportoFinto(
        robots={"vietato.it": (200, "User-agent: *\nDisallow: /\n"),
                "aperto.it": (200, "User-agent: *\nDisallow: /privato\n"),
                "guasto.it": (503, ""),
                "assente.it": (404, "")},
        pagine={"https://aperto.it/a": (200, "<html><title>T</title><body><p>" + "x" * 500 +
                                        "</p></body></html>")})
    educato = Educato(finto_web)
    prova("negativo: un divieto di robots.txt si rispetta",
          educato.permesso("https://vietato.it/a")[0] is False)
    prova("un percorso consentito passa", educato.permesso("https://aperto.it/a")[0] is True)
    prova("un percorso vietato dello stesso host non passa",
          educato.permesso("https://aperto.it/privato/x")[0] is False)
    prova("un robots.txt indisponibile per guasto del servizio vale come divieto",
          educato.permesso("https://guasto.it/a")[0] is False)
    prova("il divieto per guasto si distingue da quello scritto, e porta il motivo che lo dice",
          educato.permesso("https://guasto.it/a")[1] == MOTIVO_ROBOTS_TRANSITORIO and
          educato.permesso("https://vietato.it/a")[1] != MOTIVO_ROBOTS_TRANSITORIO)
    prova("un robots.txt assente vale come assenza di regole",
          educato.permesso("https://assente.it/a")[0] is True)
    quante = len(finto_web.chiamate)
    educato.permesso("https://aperto.it/b")
    prova("robots.txt si legge una volta per host", len(finto_web.chiamate) == quante)
    # Le attese si azzerano qui perché il caso precedente, cioè il robots.txt di un host che
    # risponde con un guasto del servizio, ne ha già prodotte riprovando: misurarle senza
    # azzerare proverebbe la ripresa invece dell'intervallo.
    finto_web.attese = []
    educato.attendi("https://aperto.it/a")
    prova("la prima richiesta a un host non attende", finto_web.attese == [])
    educato.attendi("https://aperto.it/b")
    prova("fra due richieste allo stesso host si attende", finto_web.attese == [INTERVALLO_HOST])
    educato.attendi("https://altro.it/a")
    prova("un host diverso non eredita l'attesa dell'altro",
          finto_web.attese == [INTERVALLO_HOST])

    # -- estrazione da HTML -------------------------------------------------------------------
    titolo, corpo_testo, scarso = html_a_testo(
        b"<html><head><title>Titolo</title></head><body><script>var a=1</script>"
        b"<h2>Sezione</h2><p>Prosa " + b"lunga " * 80 +
        b"<a href='https://esempio.it/x'>rinvio</a>.</p>"
        b"<pre>codice</pre></body></html>", {"content-type": "text/html; charset=utf-8"})
    prova("il titolo si estrae", titolo == "Titolo")
    prova("il contenuto degli script non entra nel testo", "var a=1" not in corpo_testo)
    prova("un'intestazione HTML diventa un'intestazione Markdown", "## Sezione" in corpo_testo)
    prova("l'indirizzo di un rinvio resta nel testo, così il grafo prosegue",
          "https://esempio.it/x" in corpo_testo)
    prova("un blocco preformattato resta recintato", "```" in corpo_testo)
    prova("una pagina con contenuto non si prende per involucro, nemmeno con script dentro",
          scarso == "")
    _, _, e_scheletro = html_a_testo(
        b"<html><body><script>app()</script><div id=root></div></body></html>",
        {"content-type": "text/html"})
    prova("negativo: uno scheletro JavaScript si riconosce invece di essere salvato vuoto",
          "scheletro JavaScript" in e_scheletro)
    _, _, e_vuota = html_a_testo(b"<html><body><div></div></body></html>",
                                 {"content-type": "text/html"})
    prova("una pagina vuota senza script si dichiara vuota e non scheletro",
          e_vuota and "scheletro" not in e_vuota)

    # -- la corsa completa, con tetti, ampiezza e ripresa -------------------------------------
    import tempfile
    import shutil
    temporanea = tempfile.mkdtemp(prefix="fetch-reddit-collaudo-")
    try:
        def post_finto(identificativo, figli=(), extra=""):
            corpo_post = " ".join("[figlio](https://www.reddit.com/r/s/comments/" + f + "/x/)"
                                  for f in figli)
            return {"id": identificativo, "title": "post " + identificativo, "subreddit": "s",
                    "author": "a", "author_fullname": "t2_a", "created_utc": 1700000000,
                    "score": 1, "num_comments": 0, "selftext": corpo_post + " " + extra,
                    "url": "", "link_flair_text": None, "retrieved_on": 1700000001}

        grafo = {
            "aaa001": post_finto("aaa001", ["bbb001", "bbb002"],
                                 "[video](https://youtu.be/k) [pagina](https://aperto.it/a) "
                                 "[breve](https://www.reddit.com/r/s/s/CODICE1)"),
            "bbb001": post_finto("bbb001", ["ccc001"]),
            "bbb002": post_finto("bbb002", ["aaa001"]),
            "ccc001": post_finto("ccc001"),
            "ddd001": post_finto("ddd001"),
        }
        trasporto_corsa = TrasportoFinto(
            post=grafo,
            alberi={"aaa001": [{"kind": "t1", "data": {
                "body": "commento con [rinvio](https://www.reddit.com/r/s/comments/ddd001/x/)",
                "author": "u", "author_fullname": "t2_u", "created_utc": 1700000000,
                "score": 2}}]},
            brevi={"/r/s/s/CODICE1": "/r/s/comments/ccc001/x/"},
            robots={"aperto.it": (200, "User-agent: *\nAllow: /\n")},
            pagine={"https://aperto.it/a": (200, "<html><title>Esterna</title><body><p>" +
                                            "y" * 600 + "</p></body></html>")})
        cartella = os.path.join(temporanea, "corsa")
        corsa = Corsa(trasporto_corsa, Educato(trasporto_corsa), cartella,
                      {"max_post": 3, "max_esterni": 5, "max_profondita": 0}, esterni=True)
        corsa.stato["seme"] = "reddit:aaa001"
        corsa.stato["seme_url"] = "https://www.reddit.com/r/s/comments/aaa001/x/"
        corsa.esegui([{"chiave": "reddit:aaa001", "tipo": "reddit", "profondità": 0,
                       "da": [], "ancora": "", "commenti_puntati": []}])
        corsa.salva()
        scaricati = [k for k, v in corsa.stato["visti"].items()
                     if v.get("tipo") == "reddit" and v.get("esito") == "scaricato"]
        prova("il tetto dei post si rispetta", len(scaricati) == 3)
        prova("l'ampiezza legge prima il punto di partenza e poi i suoi figli diretti",
              scaricati[:3] == ["reddit:aaa001", "reddit:bbb001", "reddit:bbb002"])
        prova("la profondità si conta dal punto di partenza",
              corsa.stato["visti"]["reddit:bbb001"]["profondità"] == 1)
        prova("negativo: cio che il tetto ha escluso resta dichiarato fra i pendenti",
              any(v["chiave"] == "reddit:ccc001" for v in corsa.stato["pendenti"]))
        prova("un ciclo nel grafo non fa rileggere un post",
              len([k for k in corsa.stato["visti"] if k == "reddit:aaa001"]) == 1)
        prova("un video si registra come catalogato e non come fallito",
              corsa.stato["visti"]["web:https://youtu.be/k"]["esito"] == "catalogato")
        prova("una pagina esterna consentita si scarica",
              corsa.stato["visti"]["web:https://aperto.it/a"]["esito"] == "scaricato")
        prova("un collegamento trovato in un commento entra nella frontiera",
              "reddit:ddd001" in corsa.stato["visti"] or
              any(v["chiave"] == "reddit:ddd001" for v in corsa.stato["pendenti"]))
        prova("il file del post esiste con il suo albero",
              os.path.isfile(os.path.join(cartella, "posts", "aaa001-post-aaa001.md")))
        prova("il grezzo resta accanto al derivato",
              os.path.isfile(os.path.join(cartella, "raw", "posts", "aaa001.json")) and
              os.path.isfile(os.path.join(cartella, "raw", "tree", "aaa001.json")))
        prova("la pagina esterna ha il suo HTML grezzo",
              os.path.isfile(os.path.join(cartella, "raw", "esterni",
                                          impronta("https://aperto.it/a") + ".html")))
        prova("la cartella porta il marcatore che la esenta dal normalizzatore di Markdown, "
              "perché contiene prosa di terzi verbatim",
              os.path.isfile(os.path.join(cartella, ".md-unwrap-ignore")))
        with open(os.path.join(cartella, "_INDEX.md"), encoding="utf-8") as f:
            indice = f.read()
        prova("l'indice dichiara i non raggiunti", "## Non raggiunti" in indice and
              "ccc001" in indice)
        prova("l'indice distingue catalogato da fallito", "catalogato" in indice)
        with open(os.path.join(cartella, "MAPPA.md"), encoding="utf-8") as f:
            mappa = f.read()
        with open(os.path.join(cartella, "mappa.json"), encoding="utf-8") as f:
            grafo = json.load(f)
        archi = set((a["da"], a["a"]) for a in grafo["archi"])
        prova("la mappa registra l'arco dal punto di partenza a un suo figlio",
              ("reddit:aaa001", "reddit:bbb001") in archi)
        prova("la mappa registra anche l'arco verso un nodo che non verra letto, che è il "
              "punto in cui la catena si interrompe",
              ("reddit:aaa001", "web:https://youtu.be/k") in archi)
        prova("la mappa registra l'arco verso un nodo lasciato fuori dal tetto",
              ("reddit:bbb001", "reddit:ccc001") in archi)
        prova("un arco trovato dentro un commento è attribuito al post che lo ospita",
              ("reddit:aaa001", "reddit:ddd001") in archi)
        prova("negativo: un collegamento breve non lascia un nodo intermedio nella mappa",
              not any(a.startswith("breve:") for _, a in archi))
        prova("il breve risolto punta al post a cui portava",
              ("reddit:aaa001", "reddit:ccc001") in archi)
        prova("lo stesso rinvio non si registra due volte",
              len(archi) == len(grafo["archi"]))
        prova("l'albero della mappa parte dal punto di partenza",
              "- reddit:aaa001 - post aaa001" in mappa)
        prova("l'albero annida i figli sotto chi li linka",
              "  - reddit:bbb001" in mappa)
        prova("negativo: un ciclo non fa crescere l'albero all'infinito ma si segnala",
              "già comparso sopra" in mappa)
        prova("l'albero porta l'esito accanto al nodo, così si vede dove la catena si ferma",
              "[catalogato" in mappa and "[non raggiunto" in mappa)
        prova("l'albero conserva il testo del rinvio", "rinvio:" in mappa)
        prova("il grafo per programma porta il permalink dei post",
              any(n.get("permalink", "").endswith("/comments/aaa001/")
                  for n in grafo["nodi"]))
        prova("il grafo per programma comprende i nodi non raggiunti",
              any(n.get("chiave") == "reddit:ccc001" and n.get("esito") == "non raggiunto"
                  for n in grafo["nodi"]))
        with open(os.path.join(cartella, "posts", "aaa001-post-aaa001.md"),
                  encoding="utf-8") as f:
            testo_post = f.read()
        prova("il file del post conserva l'identificativo dell'autore", "t2_a" in testo_post)
        prova("il file del post dichiara che la fonte è l'archivio e non Reddit",
              "Arctic Shift" in testo_post and "non è" in testo_post)

        richieste_prima = len(trasporto_corsa.chiamate)
        ripresa = Corsa(trasporto_corsa, Educato(trasporto_corsa), cartella,
                        {"max_post": 3, "max_esterni": 5, "max_profondita": 0}, esterni=True)
        ripresa.carica()
        ripresa.esegui([])
        prova("una ripresa senza capienza non chiede nulla",
              len(trasporto_corsa.chiamate) == richieste_prima)
        alzata = Corsa(trasporto_corsa, Educato(trasporto_corsa), cartella,
                       {"max_post": 9, "max_esterni": 5, "max_profondita": 0}, esterni=True)
        alzata.carica()
        pendenti = list(alzata.stato["pendenti"])
        alzata.stato["pendenti"] = []
        alzata.esegui([{"chiave": v["chiave"], "tipo": v["tipo"], "profondità": v["profondità"],
                        "da": v.get("da") or [], "ancora": "", "commenti_puntati": []}
                       for v in pendenti])
        alzata.salva()
        prova("con il tetto alzato la ripresa prosegue dai pendenti",
              alzata.stato["visti"].get("reddit:ccc001", {}).get("esito") == "scaricato")
        prova("la ripresa non riscarica cio che era già fatto",
              alzata.stato["visti"]["reddit:aaa001"]["esito"] == "scaricato")

        # Il caso che ha prodotto questa distinzione, riprodotto per intero: una corsa passa
        # mentre il `robots.txt` di un host non risponde, e una seconda corsa lo trova in piedi.
        # Si prova che il nodo non finisca fra i decisi, che l'indice lo dichiari non raggiunto e
        # non catalogato, e che la ripresa lo scarichi davvero. Senza l'ultima delle tre la
        # correzione sarebbe soltanto contabile.
        cartella_t = os.path.join(temporanea, "transitorio")
        pagina_t = {"https://intermittente.it/a": (200, "<html><title>Ripresa</title><body><p>" +
                                                   "z" * 600 + "</p></body></html>")}
        giu = TrasportoFinto(post={"eee001": post_finto(
            "eee001", (), "[pagina](https://intermittente.it/a)")},
            robots={"intermittente.it": (503, "")}, pagine=pagina_t)
        corsa_t = Corsa(giu, Educato(giu), cartella_t,
                        {"max_post": 5, "max_esterni": 5, "max_profondita": 2}, esterni=True)
        corsa_t.stato["seme"] = "reddit:eee001"
        corsa_t.esegui([{"chiave": "reddit:eee001", "tipo": "reddit", "profondità": 0,
                         "da": [], "ancora": "", "commenti_puntati": []}])
        corsa_t.salva()
        prova("negativo: un robots.txt indisponibile non decide il nodo come catalogato",
              "web:https://intermittente.it/a" not in corsa_t.stato["visti"])
        prova("un robots.txt indisponibile lascia il nodo fra i pendenti, con il suo motivo",
              any(v["chiave"] == "web:https://intermittente.it/a" and
                  v.get("motivo") == MOTIVO_ROBOTS_TRANSITORIO
                  for v in corsa_t.stato["pendenti"]))
        su = TrasportoFinto(post={"eee001": post_finto("eee001")},
                            robots={"intermittente.it": (200, "User-agent: *\nAllow: /\n")},
                            pagine=pagina_t)
        ripresa_t = Corsa(su, Educato(su), cartella_t,
                          {"max_post": 5, "max_esterni": 5, "max_profondita": 2}, esterni=True)
        ripresa_t.carica()
        attesi = list(ripresa_t.stato["pendenti"])
        ripresa_t.stato["pendenti"] = []
        ripresa_t.esegui([{"chiave": v["chiave"], "tipo": v["tipo"],
                           "profondità": v.get("profondità", 0), "da": v.get("da") or [],
                           "ancora": "", "commenti_puntati": []} for v in attesi])
        ripresa_t.salva()
        prova("quando il servizio torna, la ripresa scarica la pagina che era stata rinviata",
              ripresa_t.stato["visti"].get("web:https://intermittente.it/a",
                                           {}).get("esito") == "scaricato")

        # Il recupero delle corse fatte prima della distinzione: il nodo è già registrato fra i
        # decisi, e va rimesso fra i pendenti perché l'attraversamento salta ciò che ha visto.
        vecchia = Corsa(su, Educato(su), os.path.join(temporanea, "vecchia"),
                        {"max_post": 5, "max_esterni": 5, "max_profondita": 2}, esterni=True)
        vecchia.stato["visti"]["web:https://intermittente.it/a"] = {
            "tipo": "web", "profondità": 1, "esito": "catalogato",
            "motivo": MOTIVO_ROBOTS_TRANSITORIO, "host": "intermittente.it",
            "da": ["reddit:eee001"], "ancora": "pagina"}
        vecchia.stato["visti"]["web:https://youtu.be/k"] = {
            "tipo": "web", "profondità": 1, "esito": "catalogato",
            "motivo": "video: serve la trascrizione", "host": "youtu.be", "da": [], "ancora": ""}
        quanti, host = vecchia.promuovi_transitori()
        prova("il recupero promuove il solo nodo rifiutato per il robots.txt indisponibile",
              quanti == 1 and host == {"intermittente.it"})
        prova("negativo: il recupero non tocca un nodo catalogato per una ragione sua",
              vecchia.stato["visti"]["web:https://youtu.be/k"]["esito"] == "catalogato")
        prova("il recupero toglie il nodo dai visti, altrimenti la ripresa lo salterebbe",
              "web:https://intermittente.it/a" not in vecchia.stato["visti"] and
              any(v["chiave"] == "web:https://intermittente.it/a"
                  for v in vecchia.stato["pendenti"]))

        # Le pagine esterne sono foglie per scelta e non per caso, ed e' la distinzione che il
        # 2026-09-14 ha reso esplicita: fino a quel giorno lo erano per un difetto di
        # estrazione. Si prova nei due versi, perche' una bandiera spenta che non cambia nulla
        # quando la si accende e' peggio di nessuna bandiera.
        cartella_f = os.path.join(temporanea, "foglie")
        pagina_con_rinvii = ("<html><title>Con rinvii</title><body><p>" + "q" * 600 +
                             " <a href='https://altrove.it/uno'>uno</a></p></body></html>")
        t_f = TrasportoFinto(
            robots={"radice.it": (200, "User-agent: *\nAllow: /\n"),
                    "altrove.it": (200, "User-agent: *\nAllow: /\n")},
            pagine={"https://radice.it/a": (200, pagina_con_rinvii),
                    "https://altrove.it/uno": (200, "<html><title>Uno</title><body><p>" +
                                               "r" * 600 + "</p></body></html>")})
        chiusa = Corsa(t_f, Educato(t_f), cartella_f, {"max_profondita": 3}, esterni=True)
        chiusa.esegui([{"chiave": "web:https://radice.it/a", "tipo": "web", "profondità": 0,
                        "da": [], "ancora": "", "commenti_puntati": []}])
        chiusa.salva()
        prova("negativo: per difetto una pagina esterna non semina i propri collegamenti",
              "web:https://altrove.it/uno" not in chiusa.stato["visti"])
        prova("l'arco verso cio' che la pagina cita si registra comunque, perche' la mappa "
              "deve dirlo",
              any(a2.get("a") == "web:https://altrove.it/uno"
                  for a2 in chiusa.stato["archi"]))
        aperta = Corsa(t_f, Educato(t_f), os.path.join(temporanea, "espansa"),
                       {"max_profondita": 3}, esterni=True, espandi_esterni=True)
        aperta.esegui([{"chiave": "web:https://radice.it/a", "tipo": "web", "profondità": 0,
                        "da": [], "ancora": "", "commenti_puntati": []}])
        aperta.salva()
        prova("con --espandi-esterni la pagina collegata viene letta davvero",
              aperta.stato["visti"].get("web:https://altrove.it/uno",
                                        {}).get("esito") == "scaricato")

        # La lettura di una pagina sola dentro una corsa esistente. Le tre cose che vanno
        # provate sono che la pagina entri come tutte le altre, che i suoi rinvii NON vengano
        # seminati, che e' il punto del sottocomando, e che una pagina gia' presente non venga
        # riscaricata, perche' altrimenti chiamarlo due volte costerebbe due richieste.
        cartella_p = os.path.join(temporanea, "singola")
        t_pag = TrasportoFinto(
            robots={"mirata.it": (200, "User-agent: *\nAllow: /\n"),
                    "vietata.it": (200, "User-agent: *\nDisallow: /\n")},
            pagine={"https://mirata.it/a": (200, "<html><title>Mirata</title><body><p>" +
                                            "w" * 600 + " <a href='https://mirata.it/b'>b</a>"
                                            "</p></body></html>")})
        corsa_p = Corsa(t_pag, Educato(t_pag), cartella_p, {}, esterni=True)
        fatto, esito, file_ = corsa_p.una_pagina("https://mirata.it/a")
        corsa_p.salva()
        prova("una pagina chiesta per nome si scarica", fatto and esito == "scaricato")
        prova("la pagina entra nella corsa con il suo file accanto al grezzo",
              file_ and os.path.isfile(os.path.join(cartella_p, file_)) and
              os.path.isfile(os.path.join(cartella_p, "raw", "esterni",
                                          impronta("https://mirata.it/a") + ".html")))
        prova("negativo: chiedere una pagina non semina i suoi rinvii",
              "web:https://mirata.it/b" not in corsa_p.stato["visti"] and
              not any(v.get("chiave") == "web:https://mirata.it/b"
                      for v in corsa_p.stato["pendenti"]))
        prova("la mappa registra comunque l'arco verso cio' che la pagina cita",
              any(a2.get("a") == "web:https://mirata.it/b" for a2 in corsa_p.stato["archi"]))
        quante_prima = len(t_pag.chiamate)
        fatto2, esito2, _ = corsa_p.una_pagina("https://mirata.it/a")
        prova("negativo: una pagina gia' presente non si riscarica",
              fatto2 is False and esito2 == "scaricato" and
              len(t_pag.chiamate) == quante_prima)
        _, esito3, _ = corsa_p.una_pagina("https://vietata.it/a")
        prova("una pagina vietata da robots.txt si cataloga anche se chiesta per nome",
              esito3 == "catalogato")

        senza = Corsa(trasporto_corsa, Educato(trasporto_corsa),
                      os.path.join(temporanea, "senza"),
                      {"max_post": 1, "max_esterni": 0, "max_profondita": 0}, esterni=False)
        senza.esegui([{"chiave": "reddit:aaa001", "tipo": "reddit", "profondità": 0,
                       "da": [], "ancora": "", "commenti_puntati": []}])
        senza.salva()
        prova("senza le pagine esterne i collegamenti si catalogano comunque",
              senza.stato["visti"]["web:https://aperto.it/a"]["esito"] == "catalogato")
        prova("negativo: senza le pagine esterne nessuna pagina viene scaricata",
              not os.path.isdir(os.path.join(temporanea, "senza", "esterni")))

        # Un host che non risponde deve costare pochi tentativi e non l'intero budget, perché
        # su un grafo con centinaia di collegamenti esterni la somma di quelle attese domina la
        # durata della corsa. Il controllo conta le richieste, non il tempo, perché il tempo nel
        # trasporto finto non passa.
        morto = TrasportoFinto(
            post={"zzz001": post_finto("zzz001", (), "[morta](https://morto.it/a)")},
            robots={"morto.it": (200, "User-agent: *\nAllow: /\n")},
            # Un guasto di rete, non un 404: il primo si riprova perché può essere transitorio,
            # il secondo è una risposta e riprovarlo sarebbe insistere su un no.
            pagine={"https://morto.it/a": (GUASTO, "rete irraggiungibile")})
        caduta = Corsa(morto, Educato(morto), os.path.join(temporanea, "morto"),
                       {"max_post": 1, "max_esterni": 5, "max_profondita": 0}, esterni=True)
        caduta.esegui([{"chiave": "reddit:zzz001", "tipo": "reddit", "profondità": 0,
                        "da": [], "ancora": "", "commenti_puntati": []}])
        tentate = len([c for c in morto.chiamate if c == "https://morto.it/a"])
        prova("negativo: una pagina esterna che non risponde costa pochi tentativi, non tutto "
              "il budget riservato all'archivio",
              tentate == TENTATIVI_ESTERNI and TENTATIVI_ESTERNI < TENTATIVI)
        prova("una pagina esterna irraggiungibile si registra come fallita con il suo codice",
              caduta.stato["visti"]["web:https://morto.it/a"]["esito"] == "fallito")
    finally:
        shutil.rmtree(temporanea, ignore_errors=True)

    # -- l'interfaccia non espone il modo di aggirare i presidi -------------------------------
    aiuto = costruisci_parser().format_help()
    # -- la verifica dei certificati ----------------------------------------------------------
    ctx = contesto_tls()
    prova("il contesto di verifica dei certificati verifica davvero",
          ctx.verify_mode == ssl.CERT_REQUIRED and ctx.check_hostname is True)
    prova("negativo: non esiste un'opzione per non verificare i certificati",
          "--senza-certificati" not in aiuto and "insecure" not in aiuto)
    # Le due prove che seguono non riguardano il programma ma l'archivio di radici con cui gira,
    # ed esistono perché il difetto che ha motivato tutto questo era di quella specie e nessun
    # collaudo lo vedeva. Vale distinguere due cose che si somigliano: una radice scaduta
    # nell'archivio è comune e per lo più innocua, perché nessuna catena viva vi termina, e
    # certifi ne conserva una per compatibilità. Diventa un guasto quando la radice scaduta è
    # anche servita come anello intermedio da una catena viva: allora la verifica si ferma su di
    # essa invece di proseguire sul ramo firmato che è valido, e il sito risulta irraggiungibile.
    # È esattamente ciò che ISRG Root X2 faceva qui, quindi la prova nomina quel caso.
    adesso = datetime.datetime.now(datetime.timezone.utc)

    def scaduta(certificato):
        try:
            quando = datetime.datetime.strptime(certificato.get("notAfter"),
                                                "%b %d %H:%M:%S %Y %Z")
        except Exception:
            return False
        return quando.replace(tzinfo=datetime.timezone.utc) < adesso

    radici = ctx.get_ca_certs()
    ponti = [c for c in radici
             if "ISRG Root X" in str(dict(x[0] for x in c.get("subject", ())).get("commonName"))]
    prova("nessuna radice ISRG scaduta nell'archivio in uso: è la forma esatta del guasto per "
          "cui un sito in piedi risulta irraggiungibile a questo programma",
          not any(scaduta(c) for c in ponti))
    prova("l'archivio in uso porta le radici che servono, e non è vuoto o troncato",
          len(radici) > 100 and len(ponti) >= 1)

    prova("negativo: non esiste un modo di ignorare robots.txt",
          "ignora-robots" not in aiuto and "--robots" not in aiuto)

    falliti = [nome for nome, esito in esiti if not esito]
    for nome, esito in esiti:
        print(("  ok   " if esito else "  FALLITO ") + nome)
    print("")
    print(str(len(esiti) - len(falliti)) + " controlli su " + str(len(esiti)) + " superati.")
    if falliti:
        print("Falliti: " + "; ".join(falliti))
        return 1
    return 0


def costruisci_parser():
    parser = argparse.ArgumentParser(
        prog="fetch-reddit.py",
        description="Legge un post di Reddit e risale ricorsivamente i suoi sottolink, "
                    "attraverso l'archivio pubblico Arctic Shift e senza credenziali.")
    parser.add_argument("--self-test", action="store_true",
                        help="esercita la logica contro un trasporto finto, senza rete")
    parser.add_argument("--radice",
                        help="scavalca la radice ricavata dalla posizione del file; serve solo "
                             "quando lo strumento viene eseguito dove vive nel template")
    comandi = parser.add_subparsers(dest="comando")

    def radice_locale(sotto):
        # La stessa opzione si accetta prima e dopo il sottocomando, con un nome interno
        # diverso per non sovrascrivere il valore generale con il difetto del sottocomando.
        # Un'opzione che esiste ma funziona in una sola posizione è peggio di una che non esiste.
        sotto.add_argument("--radice", dest="radice_sotto", default=None,
                           help="come `--radice` generale, accettata anche qui")

    def tetti(sotto):
        radice_locale(sotto)
        sotto.add_argument("--max-post", type=int, default=500,
                           help="quanti post al massimo, 0 per nessun tetto (default 500)")
        sotto.add_argument("--max-esterni", type=int, default=200,
                           help="quante pagine esterne al massimo, 0 per nessun tetto")
        sotto.add_argument("--max-profondita", type=int, default=0,
                           help="fin dove scendere, 0 per illimitata (default 0)")
        sotto.add_argument("--esterni", action="store_true",
                           help="scarica anche le pagine fuori da Reddit; senza questa opzione "
                                "i collegamenti esterni si catalogano nell'indice senza aprirli")
        sotto.add_argument("--dominio-escluso", action="append", default=[], metavar="DOMINIO",
                           help="ripetibile: un dominio da catalogare senza scaricare")
        sotto.add_argument("--solo-domini", action="append", default=[], metavar="DOMINIO",
                           help="ripetibile: se presente, si scaricano solo questi domini")
        sotto.add_argument("--lotto", type=int, default=LOTTO_ID,
                           help="quanti identificativi per richiesta, al massimo 500")
        sotto.add_argument("--espandi-esterni", action="store_true",
                           help="segue anche i collegamenti trovati dentro le pagine esterne. "
                                "Spento per difetto, e non per prudenza ma per una misura: una "
                                "pagina di wiki rinvia all'intera wiki, e sulle pagine gia' su "
                                "disco di questa corsa seguirle tutte darebbe quattromila nodi "
                                "nuovi, in gran parte di navigazione. Gli archi della mappa si "
                                "registrano comunque")
        sotto.add_argument("--silenzioso", action="store_true",
                           help="non riferisce l'avanzamento")

    passa = comandi.add_parser("crawl", help="attraversa il grafo da un post")
    passa.add_argument("seme", help="indirizzo del post, o suo identificativo nudo")
    passa.add_argument("--dry-run", action="store_true",
                       help="legge il solo punto di partenza e riferisce la frontiera che "
                            "genererebbe, senza scrivere nulla")
    tetti(passa)

    pagina = comandi.add_parser("pagina",
                                help="legge una pagina esterna sola dentro una corsa esistente, "
                                     "senza seguirne i rinvii")
    radice_locale(pagina)
    pagina.add_argument("indirizzo", nargs="+",
                        help="uno o piu' indirizzi di pagina; ripetibile sulla stessa riga")
    pagina.add_argument("--in", dest="corsa", required=True,
                        help="la cartella della corsa in cui la pagina deve entrare")
    pagina.add_argument("--profondita", type=int, default=1,
                        help="la profondita' dichiarata nella mappa; non e' un tetto")
    pagina.add_argument("--silenzioso", action="store_true")

    riprendi = comandi.add_parser("riprendi", help="prosegue una corsa dai suoi pendenti")
    radice_locale(riprendi)
    riprendi.add_argument("cartella", help="la cartella della corsa da riprendere")
    riprendi.add_argument("--riprova-transitori", action="store_true",
                          help="rimette fra i pendenti i nodi che una corsa precedente aveva "
                               "catalogato perché il robots.txt del loro host non rispondeva: "
                               "serve a recuperare le corse fatte prima che quel rifiuto fosse "
                               "riconosciuto come transitorio")
    riprendi.add_argument("--solo-transitori", action="store_true",
                          help="con --riprova-transitori, riprende i soli nodi appena promossi e "
                               "lascia dove sono quelli rinviati da un tetto: riparare un "
                               "difetto e proseguire una frontiera sono due operazioni diverse")
    riprendi.add_argument("--max-post", type=int, default=None)
    riprendi.add_argument("--max-esterni", type=int, default=None)
    riprendi.add_argument("--max-profondita", type=int, default=None)
    riprendi.add_argument("--esterni", action="store_true")
    riprendi.add_argument("--dominio-escluso", action="append", default=[], metavar="DOMINIO")
    riprendi.add_argument("--solo-domini", action="append", default=[], metavar="DOMINIO")
    riprendi.add_argument("--lotto", type=int, default=LOTTO_ID)
    riprendi.add_argument("--espandi-esterni", action="store_true",
                          help="segue anche i collegamenti trovati dentro le pagine esterne, "
                               "spento per difetto per la stessa ragione descritta su `crawl`")
    riprendi.add_argument("--silenzioso", action="store_true")

    solo = comandi.add_parser("post", help="legge un solo post, senza seguire i suoi rinvii")
    radice_locale(solo)
    solo.add_argument("ident", help="indirizzo del post, o suo identificativo nudo")
    solo.add_argument("--silenzioso", action="store_true")
    solo.add_argument("--lotto", type=int, default=LOTTO_ID)
    return parser


def principale(argomenti=None):
    parser = costruisci_parser()
    a = parser.parse_args(argomenti)
    if a.self_test:
        return collaudo()
    if not a.comando:
        parser.print_help()
        return 2
    scelta = getattr(a, "radice_sotto", None) or a.radice
    radice = os.path.abspath(scelta) if scelta else ROOT
    trasporto = TrasportoHTTP()

    def riferisci(messaggio):
        if not getattr(a, "silenzioso", False):
            print(messaggio)

    if a.comando == "pagina":
        cartella = os.path.abspath(a.corsa)
        if not os.path.isdir(cartella):
            riferisci("non esiste la cartella della corsa " + cartella + ": una pagina entra in "
                      "una corsa e non da sola, perche' il censimento legge le corse")
            return 2
        corsa = Corsa(trasporto, Educato(trasporto), cartella, {}, esterni=True,
                      riferisci=riferisci)
        corsa.carica()
        letti, saltati, falliti = 0, 0, 0
        for indirizzo in a.indirizzo:
            fatto, esito, file_ = corsa.una_pagina(indirizzo, a.profondita)
            if not fatto:
                saltati += 1
                riferisci("gia' nella corsa (" + str(esito) + "): " + indirizzo)
                continue
            if esito == "scaricato":
                letti += 1
                riferisci("scaricata: " + indirizzo + " -> " + str(file_))
            else:
                falliti += 1
                riferisci("non scaricata (" + str(esito) + "): " + indirizzo)
        corsa.salva()
        riferisci("pagine scaricate " + str(letti) + ", gia' presenti " + str(saltati) +
                  ", non scaricate " + str(falliti))
        return 1 if falliti else 0

    if a.comando == "riprendi":
        cartella = os.path.abspath(a.cartella)
        corsa = Corsa(trasporto, Educato(trasporto), cartella,
                      {"max_post": a.max_post, "max_esterni": a.max_esterni,
                       "max_profondita": a.max_profondita},
                      esterni=a.esterni, esclusi=a.dominio_escluso, soli=a.solo_domini,
                      lotto=a.lotto, riferisci=riferisci,
                      espandi_esterni=a.espandi_esterni)
        corsa.carica()
        trattenuti = []
        if a.riprova_transitori:
            quanti, quali = corsa.promuovi_transitori()
            if quanti:
                riferisci("Rimessi fra i pendenti " + str(quanti) + " nodi che una corsa "
                          "precedente aveva catalogato per un robots.txt indisponibile, su " +
                          str(len(quali)) + " host: " + ", ".join(sorted(quali)[:8]) +
                          ("..." if len(quali) > 8 else ""))
            else:
                riferisci("Nessun nodo catalogato per un robots.txt indisponibile: non c'è "
                          "nulla da recuperare in " + cartella)
        elif a.solo_transitori:
            riferisci("--solo-transitori ha senso soltanto insieme a --riprova-transitori: "
                      "da solo non seleziona nulla, quindi la corsa si arresta invece di "
                      "riprendere tutta la frontiera senza che nessuno lo abbia chiesto.")
            return 2
        if a.solo_transitori:
            # La selezione guarda il motivo e non la provenienza, cosicché funzioni anche su una
            # corsa dove i nodi transitori sono già fra i pendenti: un recupero interrotto a metà
            # va potuto riprendere, altrimenti il rimedio ha bisogno di un rimedio suo.
            tutti = list(corsa.stato.get("pendenti") or [])
            trattenuti = [v for v in tutti if v.get("motivo") != MOTIVO_ROBOTS_TRANSITORIO]
            corsa.stato["pendenti"] = [v for v in tutti
                                       if v.get("motivo") == MOTIVO_ROBOTS_TRANSITORIO]
            if trattenuti:
                riferisci("Restano da parte " + str(len(trattenuti)) + " pendenti rinviati per "
                          "altre ragioni, che questa corsa non tocca.")
        pendenti = list(corsa.stato.get("pendenti") or [])
        if not pendenti:
            corsa.stato["pendenti"] = trattenuti + (corsa.stato.get("pendenti") or [])
            if trattenuti:
                corsa.salva()
            riferisci("Non c'è nulla di pendente in " + cartella + ": la corsa precedente ha "
                      "esaurito la frontiera.")
            return 0
        corsa.stato["pendenti"] = []
        riferisci("Riprendo " + str(len(pendenti)) + " elementi pendenti da " + cartella)
        corsa.esegui([{"chiave": v["chiave"], "tipo": v["tipo"],
                       "profondità": v.get("profondità", 0), "da": v.get("da") or [],
                       "ancora": v.get("ancora") or "", "commenti_puntati": []}
                      for v in pendenti])
        # I pendenti tenuti da parte tornano in coda, e non in testa: quelli che la corsa ha
        # appena prodotto vengono dalla frontiera nuova e hanno la precedenza naturale.
        if trattenuti:
            gia = set(v.get("chiave") for v in corsa.stato["pendenti"])
            gia |= set(corsa.stato["visti"])
            corsa.stato["pendenti"].extend(v for v in trattenuti if v.get("chiave") not in gia)
        corsa.salva()
        riferisci("Fatto. Indice in " + os.path.join(cartella, "_INDEX.md"))
        return 0

    argomento = a.seme if a.comando == "crawl" else a.ident
    tipo, chiave = seme_di(argomento)

    if a.comando == "crawl" and a.dry_run:
        return prova_a_vuoto(trasporto, tipo, chiave, riferisci)

    if tipo == "breve":
        mappa = risolvi_brevi(trasporto, [chiave])
        if not mappa:
            raise Errore("l'archivio non sa risolvere il collegamento breve " + chiave)
        esito = canonica(list(mappa.values())[0])
        if not esito or esito[0] != "reddit":
            raise Errore("il collegamento breve non porta a un post: " + str(mappa))
        chiave = esito[1]

    trovati = post_per_id(trasporto, [chiave], getattr(a, "lotto", LOTTO_ID))
    seme = trovati.get(chiave)
    if not seme:
        raise Errore("l'archivio non ha il post " + chiave + ": può essere troppo recente per "
                     "essere indicizzato, e questo non prova che non esista su Reddit")
    cartella = cartella_di(radice, seme, chiave)

    if a.comando == "post":
        tetti_corsa = {"max_post": 1, "max_esterni": 0, "max_profondita": 0}
        esterni, esclusi, soli = False, [], []
    else:
        tetti_corsa = {"max_post": a.max_post, "max_esterni": a.max_esterni,
                       "max_profondita": a.max_profondita}
        esterni, esclusi, soli = a.esterni, a.dominio_escluso, a.solo_domini

    corsa = Corsa(trasporto, Educato(trasporto), cartella, tetti_corsa, esterni=esterni,
                  esclusi=esclusi, soli=soli, lotto=getattr(a, "lotto", LOTTO_ID),
                  riferisci=riferisci)
    if os.path.isfile(corsa.percorso_stato()):
        corsa.carica()
        riferisci("Riprendo la corsa che esiste già in " + cartella)
    else:
        corsa.stato["seme"] = "reddit:" + chiave
        corsa.stato["seme_url"] = permalink_di(seme)
    riferisci("Corsa su r/" + str(seme.get("subreddit")) + " da " + chiave + " verso " + cartella)
    partenza = ([] if corsa.stato["visti"].get("reddit:" + chiave)
                else [{"chiave": "reddit:" + chiave, "tipo": "reddit", "profondità": 0,
                       "da": [], "ancora": "", "commenti_puntati": []}])
    pendenti = list(corsa.stato.get("pendenti") or [])
    corsa.stato["pendenti"] = []
    partenza.extend({"chiave": v["chiave"], "tipo": v["tipo"],
                     "profondità": v.get("profondità", 0), "da": v.get("da") or [],
                     "ancora": v.get("ancora") or "", "commenti_puntati": []}
                    for v in pendenti)
    corsa.esegui(partenza)
    corsa.salva()
    riferisci("")
    riferisci("Fatto: " + str(corsa.quanti("reddit")) + " post e " + str(corsa.quanti("web")) +
              " pagine esterne scaricate, " + str(len(corsa.stato["pendenti"])) +
              " elementi non raggiunti, " + str(len(corsa.stato["falliti"])) + " fallimenti.")
    riferisci("Indice: " + os.path.join(cartella, "_INDEX.md"))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(principale())
    except Errore as errore:
        sys.stderr.write("Errore: " + str(errore) + "\n")
        sys.exit(1)
    except KeyboardInterrupt:
        sys.stderr.write("\nInterrotto. Lo stato su disco è coerente: `riprendi <cartella>` "
                         "prosegue da dove si era arrivati.\n")
        sys.exit(130)
