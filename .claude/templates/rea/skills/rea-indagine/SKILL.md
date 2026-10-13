---
name: rea-indagine
description: >
  Conduce una indagine su un software di cui non si ha il sorgente, usando gli strumenti REA, e la
  conduce nell'ordine giusto: prima il cancello delle autorizzazioni, poi l'analisi che non esegue
  il bersaglio, e soltanto se la domanda resta aperta quella che lo esegue. Chiude scrivendo un
  documento di indagine con le prove accanto a ogni conclusione e le lacune dichiarate. Usare
  quando si vuole capire come funziona una funzione di un programma, di una applicazione o di un
  sito di cui non si possiede il codice, quando si deve interoperare con un formato o un
  protocollo non documentato, quando si indaga un difetto che si manifesta dentro un componente
  altrui, o quando si vuole riprodurre nel proprio prodotto una capacità vista altrove. Si invoca
  anche con /rea-indagine. Richiede il pacchetto rea installato nel client.
---

# Indagine su software di cui non si ha il sorgente

Questa skill non sostituisce il giudizio di chi la invoca e non autorizza niente: mette in ordine le domande, e si ferma dove l'ordine dice di fermarsi. La norma completa, con le fonti, sta in `RIFERIMENTO-uso.md` del pacchetto `rea`, e va aperta la prima volta che si percorre questo cammino e ogni volta che il cancello dà una risposta diversa da quella attesa.

## Primo passo, il cancello: non si apre niente prima di queste risposte

Le domande si pongono all'utente, una per volta, e si attende la risposta. Non si deducono dal contesto, non si danno per scontate perché il file è sul suo disco, e non si saltano perché la richiesta sembra innocua. Se una risposta manca, l'indagine non comincia.

1. **Quale è il bersaglio, esattamente.** Un file, una applicazione installata, un sito, un servizio in rete, un dispositivo. La risposta cambia il regime giuridico e cambia quali strumenti sono disponibili.
2. **Hai una copia che hai il diritto di usare.** È la condizione da cui dipendono entrambe le eccezioni di legge. Se il bersaglio è un servizio in rete, di norma una copia non c'è, e si va alla domanda 5.
3. **Che cosa vuoi ottenere.** Capire un comportamento, ricavare un formato o un protocollo per interoperare, correggere un difetto, riprodurre una capacità nel proprio prodotto. Si scrive la risposta, perché determina che cosa si potrà fare del risultato.
4. **Serve eseguire il bersaglio, o basta leggerlo.** Si parte sempre dal presupposto che basti leggerlo, e si chiede il permesso di eseguirlo solo quando la domanda non ha risposta senza. Ispezionare non è eseguire, ed eseguire non è intercettare: sono tre autorizzazioni distinte.
5. **C'è una protezione tecnica di mezzo, o un sistema altrui da raggiungere.** Se sì, ci si ferma qui e si riporta all'utente, senza proseguire e senza proporre vie alternative: è il confine oltre il quale questa skill non accompagna.

Una richiesta generica come «guarda come fa questo programma» non risponde a nessuna delle cinque. Le si pongono comunque.

## Secondo passo, l'analisi che non esegue

Si comincia sempre da qui, per tre ragioni che vale tenere insieme: è il regime giuridico più ampio, cioè quello che nessuna clausola di licenza può validamente togliere; è la parte che su Windows funziona senza installare motori aggiuntivi; ed è la parte che non può fare danno, perché il bersaglio resta inerte.

Secondo il tipo di bersaglio si usano gli strumenti statici di REA: per una applicazione JavaScript o Electron i moduli, le importazioni, le mappe dei sorgenti, le rotte e i canali fra i processi; per un assembly .NET i metadati e le istruzioni; per un binario nativo l'inventario, i simboli, le stringhe e l'analisi di funzione, che però richiedono un motore installato a parte e su Windows passano solo da Ghidra in sola lettura; per un pacchetto Android il manifesto e le classi decompilate.

Si raccoglie man mano, e non alla fine, che cosa si è visto e che cosa resta ignoto. Un'analisi che produca solo conclusioni, senza il riferimento a ciò che le sostiene, ha perso per strada la parte che la rende verificabile, ed è esattamente la parte per cui esiste questo strumento invece di una congettura.

## Terzo passo, solo se serve: l'analisi che esegue

Si passa qui soltanto se la domanda del punto 3 è rimasta senza risposta, e soltanto dopo aver verificato al punto 4 che il permesso copra anche questo. Riguarda la cattura del comportamento di un processo, il debugger, l'osservazione di una applicazione Electron in esecuzione e quella di un browser.

Tre avvertenze valgono prima di lanciare qualunque cosa. Lo strumento non è una sandbox e lo dichiara: il contenimento lo mette chi analizza, con una macchina virtuale o un contenitore, e con un profilo di browser dedicato e vuoto. Tutto gira con i permessi dell'utente corrente, quindi ciò che il bersaglio può leggere o scrivere non è limitato dall'osservazione. E su Windows nativo la cattura di processo non è disponibile affatto, quindi la risposta onesta può essere che questo passo qui non si può fare.

## Quarto passo, il documento di indagine

Il risultato non resta in chat. Si scrive un documento sotto la cartella di materiali del progetto, e contiene, in quest'ordine: quale bersaglio è stato esaminato e in quale versione; con quale autorizzazione, nelle parole con cui l'utente l'ha data al cancello; che cosa si voleva sapere; che cosa si è visto, con il riferimento preciso all'evidenza per ogni affermazione; che cosa resta ignoto; e, quando l'indagine è passata dalla decompilazione, il vincolo che ne discende su ciò che si potrà fare del risultato.

L'ultimo punto non è una formalità. Ciò che si impara osservando il comportamento di un programma si può usare liberamente per scriverne uno proprio, perché le funzionalità non sono protette; ciò che si ottiene decompilando per interoperabilità si può usare soltanto per quella, e mai per produrre qualcosa di sostanzialmente simile nell'espressione. Le due cose si somigliano nel risultato e divergono nelle conseguenze, quindi il documento deve dire da quale delle due strade è arrivata ciascuna informazione.

Dentro il progetto non entrano mai il binario altrui, le catture di traffico, i file del progetto del motore di analisi, né le credenziali che una osservazione può aver raccolto senza che nessuno le chiedesse. L'evidenza si rilegge prima di allegarla.

## Quando questa skill si ferma e chiede

Si ferma, e riporta all'utente invece di proseguire, in quattro casi: quando una delle cinque domande del cancello resta senza risposta; quando compare una protezione tecnica da aggirare; quando il bersaglio è un sistema o un servizio altrui e non una copia in proprio possesso, perché lì le eccezioni di legge non arrivano e restano in piedi contratto, segreti commerciali e diritto penale informatico; e quando l'utente chiede di usare per uno scopo diverso informazioni ottenute decompilando per interoperabilità.

In nessuno di questi casi si propongono vie alternative per ottenere lo stesso risultato. Si dice che cosa manca, e si lascia la decisione a chi ha il titolo per prenderla.
