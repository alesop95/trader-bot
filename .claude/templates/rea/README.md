# rea

<!-- readme-summary: capire come funziona un software di cui non si ha il sorgente, con le prove accanto a ogni conclusione -->

> Pacchetto opzionale del sistema di progetto. Lo strumento è di terzi, un server MCP con la sua riga di comando, e si registra nel client senza entrare nel progetto; quello che il pacchetto istanzia è la skill `rea-indagine`, che mette in ordine il cammino e apre con il cancello delle autorizzazioni. Ciò che entra in un repository è il documento di indagine, non il bersaglio.

## Perché esiste, sui due piani

Il settore «comprensione di una codebase» del catalogo copre il caso in cui il codice esiste e va capito, e tutti i suoi pacchetti danno per scontato di avere il sorgente sotto mano. Resta fuori il caso opposto, che nella pratica capita spesso: si vede una funzione dentro un programma che non si possiede, si vuole sapere come è fatta, e di quel programma si ha soltanto il binario, il pacchetto distribuito o la pagina che gira nel browser. Chiedere all'agente di indovinare produce una risposta verosimile e non verificabile, che è il modo più caro di sbagliare.

REA copre quel caso dando all'agente degli strumenti invece che delle congetture. L'agente apre il bersaglio con un motore di analisi locale, chiede pseudocodice, simboli, grafo delle chiamate, moduli, rotte, e riceve indietro ogni conclusione accompagnata dall'evidenza che la sostiene e dall'elenco di ciò che resta ignoto. Da lì può spiegare il comportamento oppure scrivere e provare una propria implementazione. Il valore non è che l'agente sappia fare reverse engineering: è che la risposta porti con sé la prova, e che le lacune siano dichiarate invece di colmate.

Sul piano operativo serve quando si deve interoperare con un formato o un protocollo non documentato, quando si indaga un incidente o un campione, quando si preserva un programma che nessuno mantiene più, e quando si vuole capire perché un'applicazione che si usa si comporti in un certo modo prima di riprodurne la funzione nel proprio prodotto.

## Il perimetro, che viene prima dell'installazione

Questo è il solo pacchetto del catalogo il cui uso legittimo dipende da chi possiede il bersaglio e non dalla configurazione del progetto. Il perimetro, con le frasi del progetto e le domande da porsi prima di aprire qualunque cosa, sta in `RIFERIMENTO-uso.md` accanto a questo file, e va letto prima di installare e non dopo. Riassunto in una riga: si analizza ciò che si possiede o che si è autorizzati a esaminare, e il permesso di ispezionare un file non autorizza di per sé a eseguirlo o a intercettarne il traffico.

## Che cosa fa senza altri motori, e che cosa ne richiede uno

Senza alcun motore di analisi nativo, su qualunque piattaforma, funzionano l'analisi statica di applicazioni JavaScript ed Electron (moduli, importazioni, mappe dei sorgenti, rotte, canali fra i processi, componenti nativi), l'ispezione di assembly .NET gestiti, e la lettura dei metadati di compilazione dei binari Go. È la parte che copre la maggioranza delle applicazioni desktop moderne, ed è anche la parte che non esegue mai il bersaglio.

I binari nativi richiedono un motore installato a parte, che REA non installa e di cui non fornisce licenza: Hopper, Ghidra o IDA. Su Windows la situazione è quella che segue, e conviene saperla prima di contare su questo pacchetto. Hopper non è disponibile. Ghidra c'è ma in forma dichiarata sperimentale, con un perimetro di sola lettura su applicazioni e librerie PE native a sessantaquattro e trentadue bit, bersaglio su un volume NTFS locale fisso, e venticinque operazioni di inventario, memoria e analisi di funzione; le librerie vengono importate come copie immutabili e non sono mai caricate né eseguite. Restano fuori percorsi di rete, alias di unità, flussi alternativi e punti di reparse. Su Linux e macOS lo stesso motore ammette anche la scrittura di nomi di funzione e commenti.

Due capacità non esistono affatto su Windows nativo e vanno nominate perché sono proprio quelle che si cercherebbero: la cattura del comportamento di un processo, che richiede Linux o macOS, e l'importazione di sorgente storica di riferimento. Su Windows resta possibile confrontare evidenze di cattura già prodotte altrove, cosa che non lancia nulla.

Il requisito comune è Node.js 22 dalla 22.19, 24 dalla 24.11, oppure 26 e oltre; le versioni 23 e 25 e le prerelease non sono supportate. La parte Android richiede JADX e un JDK completo.

## Statico e a runtime, che è la distinzione che conta

Una parte degli strumenti legge file e non esegue niente. Un'altra parte esegue o pilota codice che non è proprio, ed è marcata come tale nel protocollo: la cattura di processo, il debugger, l'osservazione di Electron e quella del browser. La differenza non è tecnica ma di autorizzazione, ed è la ragione per cui `RIFERIMENTO-uso.md` la riprende.

Vale una precisazione che la documentazione del progetto fa da sé e che conviene non attenuare: REA non è una sandbox, e lo dichiara in tre punti distinti. L'analisi nativa gira con i permessi dell'utente, e i limiti imposti al motore riducono la persistenza accidentale e il consumo, non contengono codice malevolo. Nella cattura di processo i percorsi osservati scelgono che cosa viene fotografato e non limitano ciò che il processo legge o scrive. Nell'osservazione del browser REA si attacca a un browser già avviato con la porta di debug aperta e non lo lancia né lo pilota, ma quel canale dà accesso profondo al profilo e non è un contenimento di rete; la pagina osservata continua a fare le proprie richieste. Chi analizza un campione ostile fa il contenimento per conto proprio, con una macchina virtuale o un contenitore, perché qui non ce n'è.

## Dati, e che cosa può finire nel contesto del modello

L'analisi gira in locale e il bersaglio non viene caricato da nessuna parte. Ciò che esce dal perimetro locale sono i risultati degli strumenti, che l'agente riceve e che quindi ricadono sotto la politica sui dati del fornitore del modello: la documentazione lo dice in questi termini, e non va riassunta in «tutto resta locale», perché sarebbe falso sulla metà che conta.

Le protezioni esistono e sono mirate. L'osservazione del browser oscura sempre i valori di memorizzazione locale, non trattiene mai cookie né intestazioni di autorizzazione, toglie le credenziali dagli indirizzi, non legge i corpi di richiesta e risposta se non glielo si chiede, e omette testo e valori di attributo dalle istantanee del documento. Avverte però che parametri di interrogazione, frammenti, contenuto di script e testo della console possono contenere segreti dell'applicazione e diventare evidenza. Nella cattura di processo gli ingressi marcati come sensibili si riducono a un conteggio di byte. L'importazione di sorgente di riferimento rispetta il file di esclusione di git.

## Mappa di istanziazione

Lo strumento non si copia: l'installazione avviene nel client, cioè nella configurazione dell'account, e questo README con il suo riferimento d'uso resta nel template come documentazione della scelta. Quello che un progetto istanzia è la skill che governa il cammino.

```
skills/rea-indagine/   ->  .claude/skills/rea-indagine/   (tracciato)
```

La skill è ciò che rende lo strumento chiedibile in lingua naturale invece che da riga di comando: le si dice che cosa si vuole capire e di quale programma, e lei fa partire prima il cancello delle autorizzazioni, poi l'analisi che non esegue il bersaglio, e solo se la domanda resta aperta quella che lo esegue, chiudendo con un documento di indagine. Un progetto che installi REA senza istanziare la skill ha lo strumento e non ha l'ordine in cui usarlo, che è la parte che qui conta di più.

Se un progetto conduce una indagine, ciò che si versiona è quel documento, con la sua evidenza e la riga che dichiara l'autorizzazione, mai il bersaglio.

## Il quadro normativo, verificato

Il `RIFERIMENTO-uso.md` accanto a questo file porta, dal 2026-10-12, il quadro normativo europeo e italiano con le fonti primarie: la direttiva 2009/24/CE, gli articoli da 64-bis a 64-quater della legge 633/1941, e le sentenze SAS Institute contro World Programming, Top System contro Stato belga e Nintendo contro PC Box. Non è consulenza legale e lo dichiara, ma dice dove passano i confini invece di lasciarli indovinare.

Tre cose, in sintesi, che cambiano il modo di usare lo strumento. Funzionalità, linguaggio di programmazione e formato dei file non sono protetti dal diritto d'autore, quindi riprodurre ciò che un programma fa non è di per sé una violazione. Osservare, studiare e provare un programma di cui si ha diritto di usare una copia è consentito senza chiedere permesso e senza che serva uno scopo di interoperabilità, e una clausola di licenza che lo vieti è nulla per legge. La decompilazione invece ha condizioni strette e, soprattutto, vincola l'uso di ciò che se ne ricava: le informazioni ottenute per interoperabilità servono solo a quella, e mai a produrre qualcosa di sostanzialmente simile nell'espressione. È per questo che il documento di indagine deve dire da quale strada è arrivata ciascuna informazione.

## Uso

L'installazione guidata mostra un piano e chiede approvazione prima di scrivere qualunque cosa; interrompendola non cambia niente. Registra il server MCP nel client scelto e vi installa la skill. Le scritture preservano le voci e i commenti non correlati, usano una sostituzione atomica, verificano il risultato e lasciano un backup con suffisso `.rea.backup`, conservando quello eventualmente già presente invece di sovrascriverlo; una configurazione preesistente malformata blocca l'intera operazione prima che venga scritto alcunché.

```powershell
npx rea-agents@latest setup --client claude_code --dry-run
npx rea-agents@latest setup --client claude_code
```

```bash
npx rea-agents@latest setup --client claude_code --dry-run
npx rea-agents@latest setup --client claude_code
```

La prima forma dichiara il piano senza eseguirlo. Per avere il comando `rea` nel percorso di ricerca serve l'installazione globale del pacchetto, altrimenti l'eseguibile resta dentro `node_modules`. Si disinstalla con `rea uninstall`, che toglie soltanto le registrazioni e i file di skill di REA, e con `rea uninstall --purge-data`, che rimuove anche la sua cache e il suo stato; non tocca il motore di analisi, Node, le evidenze prodotte, né le skill e i server MCP di altri.

Una avvertenza sulla sessione: la registrazione fissa una versione del pacchetto, quindi dopo un aggiornamento vanno rilanciati il setup e l'agente, e una sessione già aperta non vede quanto è stato appena registrato.

## Che cosa resta ignoto, dichiarato

Tre cose non sono state verificate su una fonte del progetto al 2026-10-12 e non vanno riportate come note. Il numero degli strumenti MCP esposti: il catalogo si genera in locale e non è versionato, e la cifra che circola sui siti aggregatori non è confermata da nessuna pagina del progetto. I nomi dei gruppi con cui il server raggruppa gli strumenti a runtime. E l'attribuzione esplicita della scrittura del file di configurazione di Claude Code al comando di installazione: il percorso del file e la chiave sono documentati, la frase che dica che è il setup a scriverli non c'è. Il pacchetto non è stato installato né provato su una macchina di questo sistema: questa scheda è ricavata dalla documentazione del progetto, non da una corsa.

## Crediti

REA, Reverse Engineer Anything, di morluto, `github.com/morluto/rea`, licenza MIT; il materiale di terze parti mantiene le proprie licenze. I motori di analisi non appartengono al progetto e vanno ottenuti e licenziati per conto proprio: Hopper, Ghidra, IDA Pro con i decompilatori Hex-Rays, JEB.
