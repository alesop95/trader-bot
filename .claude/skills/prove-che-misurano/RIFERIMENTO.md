# Prove che misurano davvero qualcosa

> Riferimento normativo della skill `prove-che-misurano`, che lo carica su richiesta invece di tenerlo in contesto a ogni sessione. Non riguarda come si scrive un test in un linguaggio o con un framework, che cambia da progetto a progetto, ma come si stabilisce che un test stia misurando il difetto che dice di misurare. Si applica ogni volta che si scrive o si valuta una prova automatica. Le quattro sezioni vengono tutte da difetti sopravvissuti a prove verdi in progetti istanziati da questo template, non da considerazioni generali.

## Il problema

Una prova verde può significare due cose diverse e indistinguibili dall'esterno: che il comportamento è corretto, oppure che la prova non esercita il comportamento. Il secondo caso è peggiore dell'assenza di prove, perché produce una copertura dichiarata che nessuno mette in dubbio, e perché la riga verde nel rapporto è esattamente ciò che impedisce di guardare.

Nessuna delle quattro pratiche seguenti riguarda quante prove ci sono. Riguardano tutte la stessa domanda, posta prima di considerare chiusa una correzione: se il difetto tornasse, questa prova cadrebbe?

## Verifica di non vacuità: si reintroduce il difetto e si guarda che cosa cade

La pratica centrale, e l'unica che risponde a quella domanda con una prova invece che con un'opinione. Scritta la correzione e la sua prova, si *rimette il difetto* nel codice, si esegue la suite, e si osserva quali prove cadono. Poi si ripristina il file e si verifica il ripristino con uno strumento, non a memoria.

Due esiti sono interessanti e nessuno dei due è quello atteso. Se *non cade niente*, la prova non misura il difetto: è vacua, e va riscritta prima di andare avanti. Se cade più di quanto previsto, o cadono prove che con quel difetto non c'entrano, allora quelle prove dipendevano dal comportamento corretto per ragioni accidentali, e il legame va reso esplicito o rimosso. In un caso reale una prova cadeva perché si appoggiava a un comportamento che non stava verificando: è stata riscritta, e il difetto che questo ha reso visibile non era nel codice ma nella prova.

Il costo è di minuti e va pagato ogni volta che si chiude un difetto, non solo quando si è in dubbio. Il dubbio non è un segnale affidabile: le prove vacue si scrivono proprio quando si è sicuri.

Il ripristino ha una precondizione che si dimentica: la copia da cui ripristinare deve esistere *prima* della prima mutazione, e va verificato, non presunto. Caso osservato: una sequenza di tre mutazioni ha copiato il file in una cartella temporanea che nel frattempo era stata cancellata, la copia è fallita con un avviso sepolto nell'uscita, e le tre mutazioni si sono sommate nel file. Il controllo finale di ripristino ha colto il danno, ma dopo, e c'erano due costi. Il file era nuovo e non tracciato, quindi git non poteva riportarlo indietro e l'ha salvato solo il fatto che il contenuto originale fosse ancora leggibile altrove. E i risultati della seconda e della terza mutazione misuravano difetti sommati, quindi non valevano niente e sono stati rifatti. La forma sicura è di interrompere la sequenza se la copia non riesce, di verificare dopo ogni mutazione sia che si sia applicata sia che il ripristino sia avvenuto, e di preferire, dove si può, un file già tracciato, che git sa ripristinare da solo.

## La non vacuità vale anche per le guardie, non solo per le prove

Estensione della sezione precedente a un oggetto diverso, osservata chiudendo un presidio mancante. Una *guardia* è qualunque cosa impedisca a un'operazione di toccare qualcosa: un file escluso da una trasformazione automatica, una condizione che salta un ramo, un elenco di eccezioni. Vale per lei la stessa domanda che si pone a una prova, e quasi nessuno la pone: *se la togliessi, cambierebbe qualcosa?*

Il caso osservato. Uno strumento che corregge la tipografia aveva rovinato, mesi prima, il documento che spiegava quella stessa correzione, perché quel documento contiene le grafie sbagliate **come dato**. Chiudendo il presidio mancante, stavano per essere esclusi tre file: i due documenti che parlano di quelle grafie e la regola di stile che le descrive. Provati su una copia prima di scrivere l'elenco, **due dei tre non venivano toccati affatto**: nel frattempo lo strumento aveva imparato a saltare i blocchi di codice, e in quei due file le occorrenze stavano tutte lì dentro. Erano già protetti da un meccanismo diverso.

Ne discendono due conseguenze, e la seconda è meno ovvia della prima.

La prima: una delle tre esclusioni è stata tolta, perché *una regola che non restringe niente comunica una protezione che non esiste*. Chi legge un elenco di eccezioni conclude che quei file siano a rischio, e smette di chiedersi se lo siano davvero.

La seconda: una delle due è stata **tenuta**, e la ragione va saputa distinguere dalla simmetria. Quel documento ha una storia reale di danno, dichiara nel proprio testo di dover essere escluso, e la sua sicurezza di oggi dipende **interamente** da un meccanismo implicito, cioè dal fatto che ogni occorrenza resti dentro un blocco di codice: basta che chi lo modifica ne scriva una in prosa perché il difetto torni. *Una protezione ridondante si tiene quando l'altra è implicita e il margine è largo una modifica*, e si toglie quando è semplicemente ridondante. La differenza sta nel sapere da che cosa dipende la protezione che già c'è.

La prescrizione operativa costa pochi minuti: prima di aggiungere una guardia, si prova il caso **senza** di essa, su una copia. Se non cambia niente, o la guardia è inutile, oppure protegge da una regressione futura e allora la ragione da scrivere è quella e non il rischio presente.

## Una prova che sceglie gli argomenti può scegliere quelli che il difetto non produce

Caso osservato: una funzione riceveva un insieme di celle occupate e un ordinale, e restituiva una cella libera. Le prove la chiamavano due volte con ordinali diversi e confrontavano i risultati. Una si chiamava perfino "due elementi nuovi finiscono in due celle diverse". Era verde, leggibile, e sembrava esattamente la prova giusta.

Il difetto è sopravvissuto perché in esercizio quell'ordinale non lo sceglieva nessuno: lo calcolava un elenco che cambiava composizione da solo, e due chiamate reali potevano riceverne uno uguale, o uno diverso da quello del passaggio precedente. Chiamando con `0` e poi con `1`, la prova aveva costruito il caso facile senza accorgersene.

La regola che ne discende. Quando una proprietà riguarda un insieme, l'unità da provare è l'insieme, non l'elemento. La domanda che il chiamante pone davvero non era "dove va questo elemento" ma "dove vanno tutti", e finché la funzione rispondeva alla prima domanda nessuna prova poteva esprimere la seconda. La correzione ha cambiato la firma prima delle prove, da "un risultato dato un indice" a "una mappa da identificativo a risultato", e la prova è diventata una sola chiamata seguita da "non ci sono due risultati uguali". Quella forma non ha argomenti da scegliere, quindi non può sceglierli gentili.

Il corollario, che vale come criterio di scrittura: se una prova deve *inventare* un valore che in esercizio viene calcolato da qualcun altro, quel valore è un'ipotesi non verificata dentro la prova. O lo si fa calcolare alla funzione stessa, allargando l'unità, oppure si prova anche chi lo calcola.

## Il calcolo giusto che non arriva a destinazione

Caso osservato, e il più istruttivo perché la funzione pura era *già corretta* e tutte le sue prove passavano. Il risultato del calcolo veniva consegnato una volta sola, alla prima costruzione del componente, a un contenitore che ignorava gli aggiornamenti successivi. Ricalcolare non muoveva niente. Il difetto non stava nel calcolo ma nella relazione fra un valore ricalcolato e ciò che l'utente vede, che per definizione non esiste dentro una funzione pura.

Formulazione generale, da tenere presente prima di dichiarare chiusa una correzione: nessuna quantità di prove su funzioni pure dimostra che il risultato di quelle funzioni arrivi a destinazione. Serve una prova che monti il pezzo vero, faccia cambiare l'ingresso e osservi l'uscita osservabile. È la stessa famiglia dei difetti che vivono nella relazione temporale fra due scritture, invisibili a qualunque prova su una funzione sola.

Due trappole pratiche nello scriverla, entrambe capaci di produrre una prova che passa senza misurare niente. Molte librerie di interfaccia non scrivono nel supporto durante l'aggiornamento ma in un proprio ciclo differito: leggere subito dopo misura lo stato precedente, e l'asserzione va messa dentro un'attesa. E ciò che si osserva deve essere il *contratto pubblico* del pezzo, cioè il modo in cui il risultato diventa visibile a chi guarda, non una struttura interna: osservare l'interno produce una prova che si rompe a ogni riorganizzazione senza che nulla sia peggiorato.

## Verificare il carico non basta quando il destinatario interpreta

Verificare che cosa si è scritto, e non solo che una scrittura sia avvenuta, è già meglio di quanto molte suite facciano. Ma vale finché chi riceve è trasparente, cioè scrive ciò che gli arriva così com'è.

Caso osservato: un'interfaccia di persistenza con semantica di *fusione*, dove una chiave assente significa "non toccare quel campo" e non "cancellalo". La prova verificava che il componente consegnasse il campo con valore nullo, e passava; sul dato reale il campo restava al valore precedente, e il difetto compariva solo ricaricando. Per cancellare serviva un valore sentinella, che è un valore e non un'assenza.

La domanda da porsi prima di fermarsi al carico: fra quello che consegno e l'effetto che voglio, c'è qualcosa che interpreta? Se sì, la prova va scritta al livello dove quell'interpretazione è osservabile, non a quello che ci sta sopra.

## Quando una verifica manuale smentisce una prova verde

Succede, ed è successo due volte in due giorni nello stesso progetto. La reazione corretta non è correggere il sintomo ma capire perché la prova non l'aveva visto, e scrivere quella ragione dove la leggerà chi scriverà la prossima prova. Un difetto trovato a mano dopo una suite verde è un difetto *della suite* oltre che del codice, e ignorare la seconda metà garantisce la ripetizione.

Vale anche il verso positivo, da dire a chi esegue la verifica manuale: un risultato inatteso vale più di uno atteso, e va riportato insieme al passo che lo ha prodotto invece di essere aggiustato a mano e dimenticato.

## In una verifica manuale si marca quale passo è quello discriminante

Caso osservato su una sequenza di quattro passi, scritta apposta per riverificare una correzione che al primo tentativo non aveva chiuso il difetto. I passi erano: creare un elemento e controllare che nasca in una posizione libera, crearne un secondo e controllare che non si sovrapponga, *spostarne uno a mano*, crearne un terzo e controllare che non atterri sopra nessuno.

Solo il terzo e il quarto passo, presi insieme, esercitano il difetto, e la ragione è che lo spostamento cambia la *composizione dell'insieme* da cui il calcolo deriva la posizione: l'elemento spostato acquista una collocazione propria, esce dall'insieme di quelli senza, e fa scalare l'indice di tutti gli altri. I primi due passi percorrono il caso facile.

Che cosa è successo davvero, ed è il motivo per cui la lezione merita di essere scritta. La prima esecuzione si è fermata dopo il primo passo e la cosa è stata registrata come verifica parziale, il che ha funzionato. Ma la seconda esecuzione, in una sessione diversa, ha rifatto **di nuovo il primo passo** prima di arrivare al terzo, e senza un richiamo esplicito si sarebbe fermata di nuovo lì: dall'esterno i passi si assomigliano tutti, sono tutti "crea un elemento e guarda dove finisce", e nulla nella lista diceva quale dei quattro portasse l'informazione. *Il passo facile è stato eseguito due volte, quello discriminante ha rischiato di non esserlo mai.*

La prescrizione che ne discende è minima e costa una riga. Chi scrive una sequenza di verifica manuale dichiara, accanto al passo che conta, **perché** conta e che cosa distingue: non "crea un terzo elemento" ma "crea un terzo elemento, ed è questo che la correzione precedente sbagliava, perché lo spostamento del passo prima ha cambiato l'insieme". Chi esegue, allora, sa che fermarsi prima non è fermarsi a metà ma fermarsi a zero.

Il criterio per riconoscere il passo discriminante, quando la sequenza la si sta scrivendo: è quello che *modifica lo stato da cui il codice deriva il risultato*, non quello che ripete l'operazione osservata. Un passo che ripete l'operazione precedente con un nome diverso aggiunge fiducia e non aggiunge informazione, ed è utile dirlo, perché a quel punto chi esegue può anche saltarlo consapevolmente invece di saltare l'altro per stanchezza.

## Un avviso che ricompare sempre uguale smette di essere un avviso

Riguarda l'uscita degli strumenti di controllo, ed è la ragione per cui un controllo può esistere, funzionare, e non proteggere più niente.

Un controllo che gira spesso finisce per segnalare, accanto ai difetti veri, un insieme di casi noti e deliberati: un file che contiene di proposito la forma che lo strumento cerca, un valore che è un requisito e non una svista, una convenzione a cui si è scelto di derogare. Nessuno di questi va corretto, quindi si impara a scorrere l'uscita fino in fondo cercando ciò che è nuovo. *Il costo vero arriva il giorno in cui non si scorre più*, molto più del tempo speso a scorrere, e la prima segnalazione vera arriva in mezzo a un rumore che si è imparato a ignorare.

Il caso osservato: due controlli tipografici segnalavano da settimane nove e due occorrenze rispettivamente, tutte note e tutte legittime. Dichiararle, con la ragione scritta accanto a ciascuna, ha portato entrambe le uscite a zero. Nei file non è cambiato niente; da quel momento però **qualunque cosa compaia è nuova**.

Da qui la prescrizione, che è più forte di quanto sembri: *un caso noto e accettato va dichiarato, non tollerato*. Le due cose si somigliano e differiscono in tutto. Tollerare significa che la conoscenza vive nella testa di chi guarda l'uscita, quindi si perde quando cambia chi guarda; dichiarare significa che vive accanto al caso, con il motivo, e che l'uscita torna a essere leggibile.

Il meccanismo che rende la dichiarazione affidabile è una sola regola, e vale la pena adottarla sempre: **un'esclusione senza motivo viene rifiutata dallo strumento**. Costringe a scrivere la ragione nel momento in cui si esclude, che è l'unico momento in cui la si conosce, e rende un elenco di eccezioni un documento invece di una lista di nomi. Chi lo rilegge fra sei mesi può giudicare se ciascuna valga ancora.

Il corollario per chi scrive lo strumento: il salto va **stampato**, non taciuto. Una protezione silenziosa sembra una svista a chi guarda l'uscita, e questo è il modo in cui una guardia smette di esistere senza che nessuno la tolga.

## Uno strumento che riscrive i file deve poter girare su una copia

Piccola e trovata per caso, ma con una conseguenza sproporzionata alla sua dimensione.

Uno strumento che modifica i file sul posto si prova nel modo ovvio: si copia qualcosa in una cartella temporanea e glielo si dà in pasto. Su una delle macchine in uso la cartella temporanea stava su un'unità diversa dal repository, e la funzione della libreria standard che calcola un percorso relativo **solleva un'eccezione** quando i due percorsi stanno su unità diverse. Lo strumento si interrompeva.

Il difetto era piccolo, era lì da mesi, e la sua conseguenza no: *l'unico modo di provare quello strumento era lanciarlo sui file veri*. Su uno strumento che riscrive, e che in passato aveva già rotto la compilazione di un progetto, è precisamente la proprietà che non si può permettere.

Ne discende una verifica da fare una volta per ogni strumento di questa famiglia, e costa un minuto: **si prova a puntarlo su una copia fuori dal repository**. Se non funziona, il difetto è che la prova sicura non esiste, e la scomodità ne è solo il sintomo. Nel caso osservato il rimedio è stato trattare un percorso fuori dalla radice come non escludibile invece di interrompere, che è anche la semantica corretta, dato che le esclusioni sono dichiarate relative alla radice.

## Una finzione scritta guardando il codice descrive il codice, non la dipendenza

Quarta forma di prova che passa senza misurare, osservata su un progetto istanziato e distinta dalle tre precedenti perché non riguarda l'asserzione ma ciò che la circonda.

Una prova unitaria sostituisce le dipendenze con oggetti scritti a mano. È una pratica corretta, e dimostra esattamente questo: **il mio codice si comporta come mi aspetto, dato che questa dipendenza si comporta come l'ho immaginata.** La seconda metà di quella frase è il limite, e di solito non si legge.

Nel caso osservato, tre file di codice pubblicato usavano una proprietà che nel sistema reale non esisteva nella forma in cui la usavano. Tutte le loro prove erano verdi, e la ragione è la più insidiosa possibile: ogni finzione dichiarava quella proprietà a mano, **proprio perché il codice ne aveva bisogno**, senza che nessuno si chiedesse se esistesse davvero. La finzione era stata costruita per far passare il codice, non per descrivere la dipendenza, e da quel momento confermava qualunque cosa il codice facesse.

Il difetto è stato trovato solo da una prova che attraversava un sistema reale, la prima volta che ne è stata scritta una.

Due conseguenze operative.

Quando si scrive una finzione, ci si chiede se la si stia costruendo **guardando la documentazione della dipendenza oppure guardando il codice che deve passare**. Il secondo caso produce una prova che conferma se stessa, e nessuna revisione la distingue dall'altra leggendola.

E la piramide che raccomanda molte prove unitarie e poche che attraversano il sistema vero non viene smentita da questo: **il valore delle poche non sta in quanto coprono, ma nel fatto che esista almeno un percorso in cui nessuno ha potuto immaginare la dipendenza.** Per quella ragione non sono facoltative, per quanto poche.

La stessa trappola ha una variante fuori dalle prove unitarie, nelle verifiche di ciò che è stato pubblicato. Se il valore atteso si ricava dal file di configurazione, la verifica confermerà qualunque cosa quel file dica, errori compresi. Caso osservato: una politica di cache espressa come regole in un file di configurazione, dove i valori erano giusti e l'ordine di precedenza no. Uno strumento che leggesse il file e controllasse che il server restituisse i valori scritti lì non avrebbe visto niente di strano, perché il file non mente sui valori. Si sbagliava soltanto su quale regola vincesse. Lo strumento corretto tiene la politica come dato proprio, scritto per esteso, e chiede al server che cosa restituisce davvero. Un dettaglio che la verifica di non vacuità ha fatto emergere in quel caso vale da solo: controllare l'intestazione non basta se non si controlla anche lo stato della risposta, perché una pagina d'errore può portare l'intestazione giusta.

## Una proprietà dei dati non la sorveglia nessuna prova

L'ultima forma, osservata tre volte nello stesso progetto istanziato e diversa da tutte le precedenti perché la prova non sbaglia niente: semplicemente non può vedere. Una suite esercita il codice su dati costruiti per l'occasione, quindi resta verde qualunque cosa contengano i dati veri. Tre decisioni dipendevano proprio da quello: una vista che raggruppava per un campo che nessun record popolava, costruita e rimossa tre volte su tre criteri diversi; un ripiego di lettura che si poteva togliere solo quando nessun record fosse rimasto senza il campo nuovo; un campo compilato a mano di cui nessuno sapeva a che punto fosse. In tutti e tre i casi la scoperta è arrivata dopo, guardando il risultato vuoto.

Il presidio non è una prova ma una **misura**: uno strumento di sola lettura che, dato un campo, conta su quanti record reali è valorizzato, vuoto, assente, oppure irraggiungibile perché il percorso si interrompe prima. Separare l'ultimo esito dall'assenza non è pedanteria: un record senza il contenitore non è un elemento senza il campo, e sommarli mette due unità di misura nello stesso numero. La conta va scritta come funzione pura, provata sui record già letti, e la lettura va tenuta a parte, così che la logica si provi senza toccare la rete.

La regola che ne discende: **prima di costruire una vista che raggruppa per un campo, o di togliere un ripiego che dipende dalla migrazione di un campo, si conta quante righe quel campo lo hanno.** La prima misura, nel caso osservato, ha dato zero su centonovantacinque per il campo del grafico rimosso e cinque su centonovantacinque per quello che lo aveva sostituito, cioè ha confermato in un comando ciò che tre giri di costruzione avevano scoperto a posteriori. Due riserve vanno dichiarate accanto a ogni misura. La prima è l'ambiente su cui è stata presa, perché un conteggio sullo sviluppo non autorizza una rimozione in produzione. La seconda è che due conteggi uguali non sono gli stessi record: se una decisione dipende dalla corrispondenza fra due campi, serve l'incrocio e non il confronto dei totali.
