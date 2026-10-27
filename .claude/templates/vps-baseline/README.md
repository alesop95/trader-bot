# vps-baseline

> Pacchetto opzionale. Porta una macchina noleggiata da un fornitore cloud dallo stato in cui arriva allo stato da cui si può rilasciare, e lo verifica. Nasce il 2026-10-26 dalla risalita di due lezioni di un progetto istanziato (L-012 e L-015), dove la procedura è stata percorsa per intero su una macchina reale.

<!-- readme-summary: baseline di una macchina noleggiata da un fornitore cloud, verificata prima che applicata, con il presupposto dell'immagine del fornitore e le tre cose che si chiamano backup -->

## Che cosa contiene

Uno strumento, `tools/baseline-vps.sh`, che si esegue sulla macchina e che di comportamento predefinito **verifica soltanto**: non applica niente finché non glielo si chiede, perché un errore sul servizio di accesso remoto chiude fuori chi lo sta lanciando.

```bash
scp tools/baseline-vps.sh <alias>:/tmp/
ssh -t <alias> 'bash /tmp/baseline-vps.sh --verifica'
ssh -t <alias> 'bash /tmp/baseline-vps.sh --applica --ammessi <indirizzo>'
```

La copia preventiva invece della redirezione dallo standard input non è un vezzo: la redirezione funziona su una shell POSIX e non su PowerShell, che non ha quell'operatore.

## Il presupposto da smontare per primo

Una consegna ben fatta descrive ciò che chi ha fatto l'impianto ha configurato. Non descrive ciò che l'immagine del fornitore conteneva già, e la differenza fra le due cose è un accesso.

L'immagine standard di una distribuzione porta un utente predefinito proprio. Alla creazione, l'infrastruttura del fornitore vi inietta la **stessa** chiave pubblica indicata per l'amministratore, e il meccanismo di inizializzazione dell'istanza gli concede elevazione totale **senza password**, scrivendo una regola in un file che resta datato alla costruzione dell'immagine e non al giorno dell'impianto. Ne discende che le tre garanzie che una buona consegna dichiara, cioè amministratore non raggiungibile da remoto, lavoro quotidiano con permessi limitati ed elevazione tracciata dietro password, convivono con una via parallela che le aggira tutte: chi possiede quella chiave entra come l'utente predefinito e diventa amministratore senza digitare niente.

Non è un errore di chi ha fatto l'impianto, ed è per questo che sfugge: la consegna è corretta su ciò che afferma. E poiché il difetto appartiene all'immagine e non alla macchina, quando se ne trova uno si verificano **tutte** le altre macchine create dallo stesso pannello.

Il controllo che regge è limitare il servizio di accesso remoto al solo utente operativo, perché continua a valere anche se l'inizializzazione ricrea utente, chiave e regola al riavvio. Svuotare le chiavi dell'utente predefinito, revocargli la shell e rimuovere la regola di elevazione sono misure di contorno utili e disfacibili.

## Tre cose diverse che tutti chiamano backup

È la seconda lezione del pacchetto, e confonderle produce la peggiore delle condizioni: credersi coperti su tre fronti avendone presidiato uno, e scoprirlo quando serve.

L'**istantanea del pannello** è un tasto annulla per una singola operazione rischiosa: si prende pochi minuti prima di toccare qualcosa e si lascia scadere. La sua descrizione va letta invece che assunta, perché durata e vincoli variano e possono sorprendere: in un caso osservato veniva rimossa automaticamente dopo due giorni e, finché esisteva, limitava le modifiche della macchina a due soli parametri. Uno strumento così non è un punto di ritorno, e chiamarlo tale produce la convinzione di avere una rete di sicurezza che il lunedì non c'è più.

La **riproducibilità della macchina**, cioè questo pacchetto, protegge dalla perdita totale e dal cambio di fornitore, e sopravvive a entrambi perché non dipende da nessuna funzione del pannello. Non protegge però nessun dato: ricostruisce una macchina corretta e vuota.

Il **salvataggio dei dati** è l'unico che protegge da cancellazione, corruzione ed errore umano, e l'unico che non vale niente finché un ripristino non è stato provato davvero.

I tre si nominano con tre parole diverse nei documenti, compaiono come voci separate nella pianificazione ciascuna con il proprio stato, e l'istantanea del fornitore si prende immediatamente prima dell'operazione che la giustifica e non in anticipo per prudenza generica, altrimenti scade inutilizzata.

## L'ordine dei passi, e perché non è negoziabile

Si legge l'impronta della chiave di host dall'interno e la si confronta con quella che il client ha accettato al primo contatto: la fiducia al primo incontro non è una verifica ma una scommessa, e questo è il momento di trasformarla in riscontro. Dove esiste una macchina che accedeva già da prima, il confronto con il suo registro degli host noti è una corroborazione indipendente e anteriore.

Si autorizza poi una seconda chiave intestata all'organizzazione, generata sulla macchina da cui si amministrerà e **mai copiata** da quella esistente: una chiave privata copiata fra macchine distrugge l'attribuzione e moltiplica i luoghi da cui può uscire. La scrittura si fa con una copia di salvataggio del file e preceduta da un a capo, perché un file che non terminasse con un a capo attaccherebbe la chiave nuova a quella esistente rompendole entrambe.

Si legge lo stato interno **prima** di cambiarlo, e in particolare il registro degli accessi riusciti e falliti dal primo avvio: si legge prima della restrizione per provenienza, perché dopo la domanda su chi abbia bussato non si pone più allo stesso modo. Su una macchina esposta da qualche settimana il conteggio dei tentativi falliti è nell'ordine delle decine di migliaia, e il dato che conta non è quello ma il suo complemento, cioè se esista anche un solo accesso riuscito che non si riconosce.

Si chiude poi la via parallela, si restringe il filtro, e si riavvia. Il riavvio serve ad attivare i nuclei installati, ma serve soprattutto come **prova** che la configurazione appena scritta sopravvive all'inizializzazione automatica dell'istanza, e si fa mentre la macchina non serve ancora a nessuno.

## I tre esiti dello strumento

Lo strumento restituisce conforme, non conforme e **non verificabile**, e il terzo pesa sull'esito complessivo come il secondo. La ragione sta in un difetto che lo strumento stesso ha avuto nella prima stesura: i comandi che richiedono elevazione fallivano in silenzio quando l'elevazione non c'era, e il loro ripiego coincideva con il valore che segnala l'assenza del problema. La prima esecuzione riportò tre voci in regola e quattro fuori regola, e tutte e sette erano fittizie. La disponibilità dei permessi si accerta perciò una volta sola all'inizio e decide che cosa lo strumento ha il diritto di affermare.

## Che cosa questa baseline non copre

Non copre l'applicazione che girerà sopra, che ha una propria postura da irrobustire. Non copre il salvataggio, che è un passo a sé e il cui script va letto prima di attivarlo, perché uno script incompleto produce lo stato peggiore dei due, cioè un salvataggio che esiste e che nessuno rimette in discussione. Non copre il presidio. E non sostituisce la via di emergenza fuori banda: finché la console del pannello non è stata **provata**, la ridondanza di accesso è dichiarata e non reale.

Prima di costruire il salvataggio si verifica che i dati siano persistiti fuori dal contenitore che li produce. Nel caso che ha prodotto questo pacchetto, il descrittore dei contenitori non montava le cartelle dei file caricati: quei file sarebbero spariti a ogni ricreazione, e un salvataggio costruito sopra avrebbe copiato una cartella destinata a svuotarsi.
