# Pacchetto opzionale: backup di una macchina Linux con Veeam Agent

> Allestimento replicabile di Veeam Agent for Linux su una macchina che il progetto deve poter rimettere in piedi: la guida che contiene le decisioni e le trappole, due script che ne attuano la parte meccanica, e un file di valori che raccoglie tutto ciò che cambia da una macchina all'altra. Si istanzia nei progetti la cui sostanza comprende una macchina reale, non in quelli di solo codice, dove il ripristino è un `git clone`.

<!-- readme-summary: backup di una macchina Linux con Veeam Agent, dalla scelta della variante alla rilettura del punto di ripristino, con dieci trappole documentate -->

## Mappa di istanziazione

```
templates/veeam-linux/GUIDA.md                   ->  <radice>/docs/veeam-agent-linux.md   (tracciato)
templates/veeam-linux/tools/veeam-allestisci.sh  ->  <radice>/tools/veeam-allestisci.sh   (tracciato)
templates/veeam-linux/tools/veeam-verifica.sh    ->  <radice>/tools/veeam-verifica.sh     (tracciato)
templates/veeam-linux/valori.example.sh          ->  _notes/veeam/<macchina>.valori.sh    (ignorato)
```

La collocazione del file dei valori non è una preferenza. Quel file nomina un host, i suoi percorsi e la destinazione a cui l'archivio viene portato fuori, cioè dati che identificano una macchina reale: sta nel livello privato del progetto, dove li tiene anche `anonymization`, e non fra i file tracciati. Gli script e la guida non contengono alcun valore reale per costruzione, ed è la ragione per cui possono essere versionati.

## Che cosa fa e che cosa non fa

Gli script attuano le fasi da 0 a 6 della guida, cioè accertare i presupposti, installare, creare deposito e lavoro, eseguire e rileggere il punto di ripristino. Non pianificano nulla: il lavoro nasce manuale, e la decisione di schedularlo resta del progetto, perché una pianificazione che nessuno guarda produce archivi che nessuno ha mai riletto.

Tre cose restano deliberatamente fuori dall'automazione, e la ragione è che nessuna delle tre si può dedurre dalla macchina. La scelta della variante del pacchetto decide se il backup potrà essere una immagine avviabile o soltanto i file, e dipende da che cosa il progetto deve poter ripristinare. L'elenco dei percorsi inclusi dipende da quali filesystem contano. La collocazione del deposito dipende da quali dischi esistono e da dove l'archivio andrà a finire. Il sottocomando `controlli` misura i fatti e propone un blocco di valori già compilato, dichiarando che raccomanda e non decide: la correzione di quel blocco è il momento in cui le tre decisioni vengono prese.

La fase 7, cioè portare l'archivio fuori dalla macchina, non è automatizzata e non è facoltativa. Un deposito sullo stesso disco che si salva protegge dall'errore e non dal guasto del disco, quindi finché `DESTINAZIONE_ESTERNA` resta vuota il backup si dichiara allestito e non messo al sicuro.

## Dopo l'istanziazione

Gli script girano sulla macchina da salvare, non sulla macchina da cui la si amministra: si copiano con `scp`, si rende eseguibile ciò che serve, e si lavora in un terminale dove sia possibile digitare una password, perché i comandi dell'agente richiedono privilegi oppure l'appartenenza al gruppo `veeam`, che si legge al login.

```bash
scp tools/veeam-allestisci.sh tools/veeam-verifica.sh "_notes/veeam/<macchina>.valori.sh" "<ALIAS-SSH>:~/"
```

```bash
ssh "<ALIAS-SSH>"
```

```bash
chmod +x ~/veeam-allestisci.sh ~/veeam-verifica.sh
```

Si parte dai controlli, che non installano niente e non richiedono privilegi, e il cui esito è il blocco di valori da correggere.

```bash
./veeam-allestisci.sh controlli
```

Corretto il file dei valori, le fasi seguono in ordine. L'installazione termina chiedendo l'accettazione di due contratti, che è il punto in cui un comando con l'uscita rediretta sembrerebbe bloccato.

```bash
./veeam-allestisci.sh --valori ./<macchina>.valori.sh installa
```

```bash
./veeam-allestisci.sh --valori ./<macchina>.valori.sh configura
```

```bash
./veeam-allestisci.sh --valori ./<macchina>.valori.sh esegui --attendi
```

```bash
./veeam-verifica.sh --valori ./<macchina>.valori.sh
```

Lo script di verifica termina con stato zero solo se tutte e quattro le verifiche sono state eseguite e superate, con stato 1 se una è fallita e con stato 2 se una non è stata eseguita, così che la differenza fra un verde e un verde parziale non si perda in un riepilogo.

## Dipendenze

Nessuna oltre a ciò che una installazione Ubuntu o Debian ha già: `bash`, `curl`, `dpkg`, `apt`, `findmnt`, `lsblk`, `df`, `sha256sum`. Gli script non aprono connessioni se non per scaricare il pacchetto di repository di Veeam dal sito del produttore, e non scrivono nulla fuori da ciò che l'agente scrive da sé.

## Stato di verifica

Il sottocomando `controlli` è stato eseguito il 2026-10-15 su una macchina reale (Ubuntu 26.04.1, kernel della serie 7.0, partizioni semplici senza LVM) e ha prodotto i fatti corretti, la raccomandazione corretta e un blocco di valori utilizzabile senza correzioni. Il controllo sui file sparsi, aggiunto lo stesso giorno, è stato provato sul caso che lo ha generato e lo riconosce. La versione del pacchetto di repository proposta, `1.0.11`, è stata verificata alla stessa data contro l'elenco pubblicato dal produttore ed era la più recente delle sei disponibili.

Il resto della procedura è stato percorso lo stesso giorno sulla stessa macchina, ma **a mano e non attraverso gli script**: installazione dell'agente `6.3.2.1501` con `cifs-utils`, deposito su condivisione SMB con `Accessible true`, lavoro a livello di file cifrato, ritenzione a quattordici punti, pianificazione giornaliera, prima corsa e rilettura. I comandi che gli script eseguono sono quindi quelli verificati dal vivo, uno per uno, mentre i rami che li incatenano, cioè il deposito SMB, la cifratura e la pianificazione, sono stati scritti dopo e non hanno ancora una corsa completa alle spalle. Finché non ce l'hanno, `installa` e `configura` vanno eseguiti guardando l'uscita invece che lanciati e lasciati andare. Questa riga si aggiorna quando la corsa c'è stata.

Il primo pieno è stato completato e riletto il 2026-10-15: corsa di un'ora e quaranta su 55 GB di sorgente, archivio di 41,41 GB sulla condivisione, punto `Full` non corrotto, e sul punto montato tutte le verifiche superate. Il conteggio merita una riga perché è la verifica che di solito si salta: a fronte di 34.117 elementi sul sistema vivo l'archivio ne porta 34.052, e i sessantacinque di differenza sono stati identificati uno per uno invece di essere attribuiti al rumore, risultando cinquantanove socket, cinque collegamenti simbolici e una directory, cioè zero file regolari mancanti.

Cinque cose di questa pagina e della guida sono state corrette dall'allestimento vero invece che scritte a tavolino, e vale dirlo perché erano tutte plausibili e sbagliate. L'installazione non aggiunge l'utente al gruppo `veeam`, che resta vuoto. Una sottocartella dentro una condivisione SMB funziona come `--location`, cosa che la documentazione non dichiara. Un file sparso fa leggere al lavoro molte volte quello che la macchina contiene, e non si vede né in `du` né nel totale che il lavoro dichiara. Una cancellazione con `--purge` su un deposito remoto non è istantanea, quindi la corsa lanciata subito dopo fallisce con un messaggio che nomina l'effetto e non la causa. E l'health check, che su una catena *forever forward* è la difesa che conta di più, non si abilita affatto da riga di comando su un deposito ordinario: il controllo sintattico pretende il flag della variante leggera, e la variante leggera non è supportata da quel tipo di deposito.

## Origine

Estratto da un progetto istanziato da questo template, dove l'allestimento era stato percorso a mano nel settembre 2026 ed era costato molto più del previsto. Le dieci voci di troubleshooting della guida nascono tutte da sintomi osservati su macchine reali, non da previsioni, e due di esse (il comando che sembra bloccato e lo stato restituito da una pipeline invece che dal comando) valgono oltre Veeam.
