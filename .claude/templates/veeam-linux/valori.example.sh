#!/usr/bin/env bash
# Valori di allestimento Veeam per una macchina Linux.
#
# Si copia accanto agli script come "valori.sh", si adatta, e si carica con
# "source ./valori.sh" nella stessa shell da cui si lanciano gli script.
# Descrive una macchina reale (host, percorsi, destinazione): non va versionato
# in un repository pubblico, il posto giusto e' il livello privato del progetto.
#
# Il sottocomando "controlli" di veeam-allestisci.sh stampa un blocco gia'
# compilato con i fatti della macchina su cui gira: si parte da quello e lo si
# corregge, invece di indovinare i valori qui sotto.

# --- Variante del pacchetto -------------------------------------------------
# "veeam-nosnap" non porta il modulo del kernel: livello di volume solo su LVM.
# "veeam" porta il modulo via DKMS: livello di volume sempre, se il modulo
# compila contro il kernel in uso. La tabella che decide sta in GUIDA.md.
PACCHETTO="veeam-nosnap"

# Livello del lavoro: "fileLevel" oppure "volumeLevel".
LIVELLO="fileLevel"

# Versione del pacchetto di repository di Veeam. E' il solo valore di questa
# procedura che invecchia da solo: va verificato sul sito del produttore.
VERSIONE_REPO="1.0.11"

# --- Deposito ---------------------------------------------------------------
# "local" scrive su un percorso della macchina stessa, "smb" su una condivisione
# di rete. La differenza non e' di comodita': un deposito locale sullo stesso
# disco che si salva protegge dall'errore e non dal guasto del disco, quindi e'
# al piu' un luogo di transito e la fase 7 della guida resta obbligatoria; un
# deposito remoto fa nascere l'archivio gia' fuori dalla macchina, e la fase 7
# decade insieme al rischio che esiste per coprire.
TIPO_DEPOSITO="local"

# Con TIPO_DEPOSITO=local, un percorso. Con smb, //server/condivisione oppure
# //server/condivisione/sottocartella: la sottocartella funziona, anche se la
# documentazione Veeam non lo dichiara.
DEPOSITO="/home/veeam-repo"
NOME_DEPOSITO="repo-locale"

# Solo con TIPO_DEPOSITO=smb. La password non vive in nessun file: si digita al
# prompt, perche' --password viene passato senza valore. Il dominio si lascia
# vuoto per un account locale di un NAS, e si riempie solo se il server lo
# pretende. Richiede cifs-utils, che il sottocomando "installa" aggiunge da se'.
SMB_UTENTE=""
SMB_DOMINIO=""

# --- Lavoro -----------------------------------------------------------------
NOME_LAVORO="backup-file-sistema"

# Punti di innesto da includere, separati da virgola. Ogni filesystem che si
# vuole salvare va nominato esplicitamente: --includeDirs non dichiara se
# l'attraversamento si fermi al confine del filesystem (voce G del
# troubleshooting). Usato solo quando LIVELLO e' "fileLevel".
INCLUDI="/,/home"

# Percorsi da escludere. Il deposito va escluso se si trova dentro un percorso
# incluso, altrimenti il lavoro copia se stesso (voce F del troubleshooting).
ESCLUDI="/home/veeam-repo,/proc,/sys,/dev,/run,/tmp,/snap,/mnt,/media"

# Numero di punti di ripristino conservati. Senza un pieno attivo pianificato la
# catena e' forever forward, cioe' esiste un pieno solo che assorbe il punto piu'
# vecchio quando la finestra si riempie: su una macchina sempre accesa questo
# numero equivale quindi a un numero di giorni, su una spenta di notte copre un
# arco di calendario piu' lungo.
PUNTI="2"

# --- Cifratura --------------------------------------------------------------
# "si" oppure "no", e si decide ora: si cifra il lavoro e non l'archivio, quindi
# attivarla dopo significa rifare il backup. Vale "si" ogni volta che l'archivio
# lascia la macchina, perche' un backup a livello di file contiene l'intero
# sistema, quindi anche /etc/shadow e le chiavi private. La password si digita
# al prompt e va custodita fuori dalla macchina: senza di essa l'archivio non si
# ripristina e nessuno la puo' recuperare.
CIFRATURA="no"

# --- Pianificazione ---------------------------------------------------------
# Ora della corsa giornaliera, nella forma HH:MM. Vuoto lascia il lavoro
# manuale, e un backup manuale e' un backup che qualcuno deve ricordarsi di
# fare. Su una macchina sempre accesa conviene un'ora in cui la destinazione non
# sia contesa: una destinazione condivisa con altre macchine diventa il collo di
# bottiglia molto prima della rete.
ORARIO=""

# --- Verifica (fase 6) ------------------------------------------------------
# File confrontati per impronta fra sistema vivo e archivio montato: vanno
# scelti in modo da coprire tutti i filesystem inclusi e piu' ordini di
# grandezza. Separati da virgola, percorsi assoluti.
CAMPIONI="/etc/fstab,/etc/hostname"

# Albero su cui si confronta il conteggio dei file fra vivo e archivio.
ALBERO_CONTEGGIO="$HOME"

# --- Destinazione esterna (fase 7) ------------------------------------------
# Dove l'archivio viene portato fuori dalla macchina. Finche' resta vuoto, la
# fase 7 e' dichiarata non eseguita invece di essere data per fatta.
DESTINAZIONE_ESTERNA=""
