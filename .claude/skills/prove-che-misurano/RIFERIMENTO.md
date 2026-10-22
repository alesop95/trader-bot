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

Esiste anche il caso speculare, e non lo vede nessuna delle prove di componente. Chi scrive il contenuto dà per scontato che il destinatario interpreti, e invece il destinatario è trasparente. Caso osservato: testi di interfaccia in una risorsa di traduzione, con il grassetto scritto in sintassi Markdown, stampati da un componente che rende il testo così com'è. A video comparivano gli asterischi in entrambe le lingue, con la suite verde. Il cieco era la finzione della funzione di traduzione, che restituisce la chiave e non il valore: così ogni prova di componente è strutturalmente incapace di guardare il contenuto della risorsa. La prova che misura sta sulla risorsa stessa, dove il difetto nasce, e verifica che nessun valore contenga una sintassi che nessun componente interpreta.

## Un'asserzione di assenza passa anche per la ragione sbagliata

Provare che una cosa c'è e provare che una cosa non c'è non sono simmetrici, e la differenza è il genere di errore che ciascuna ammette. Un'asserzione di presenza fallisce se il selettore è sbagliato, quindi un selettore sbagliato si manifesta subito. Un'asserzione di assenza **passa** se il selettore è sbagliato, perché un selettore che non sa cercare non trova niente, esattamente come non trova niente quando la cosa è stata davvero rimossa. I due casi producono lo stesso verde e non sono distinguibili guardandolo.

Il caso che ha insegnato la regola. Una sezione di interfaccia mostrava una ripartizione per categoria che i dati non popolavano più, e fu rimossa; la prova che ne fissava la rimozione cercava l'etichetta con una corrispondenza **esatta** sul testo dell'elemento. La rimozione però era stata applicata in un punto e non nell'altro, e nel punto rimasto l'etichetta veniva resa insieme al proprio valore, cioè come `Etichetta 50` invece che come `Etichetta`. Il testo completo di quell'elemento non è mai uguale alla stringa cercata, quindi la ricerca esatta non lo trovava e la prova dichiarava assente una sezione ancora presente. È rimasta verde per due settimane, con un nome che affermava per esteso ciò che non stava verificando.

Due prescrizioni, e la seconda vale anche quando la prima è stata rispettata.

**Un'asserzione di assenza si accompagna sempre a una di presenza che usa lo stesso selettore.** Se la prova cerca l'etichetta in una regione e la vuole assente, deve esistere accanto una prova che la stessa ricerca la trova dove c'è: senza, nessuno sa se quel selettore sappia trovare. È l'applicazione diretta della non vacuità al caso dell'assenza, che non si può verificare reintroducendo il difetto perché il difetto è proprio ciò che si sta cercando di non avere.

**L'assenza si asserisce su una regione delimitata, non sull'intero schermo.** "Da nessuna parte" è quasi sempre più di quanto si voglia dire, e paradossalmente è più fragile: circoscrivere la ricerca al riquadro che deve averla persa costringe a nominare quel riquadro, e nominarlo fa emergere che gli altri esistono. La prova che ha fallito qui asseriva sull'intera schermata, ed è esattamente per questo che non si è accorta di parlare del riquadro sbagliato.

Corollario sul nome. Una prova il cui nome dice più di quanto il corpo verifica è peggio della sua assenza, perché chi legge l'elenco dei nomi la conta come copertura acquisita. Quando il corpo non può essere allargato subito, si stringe il nome.

Lo stesso inganno vale per un filtro sull'output di un programma, che è un'asserzione di assenza scritta a mano. Caso osservato in un progetto istanziato il 2026-10-20: le violazioni di una Content-Security-Policy si cercavano nella console del browser filtrando per il nome dell'intestazione, con i trattini, mentre il browser le stampa con le parole «Content Security Policy», separate da spazi. Il filtro non poteva trovare niente, e la console vuota si leggeva come una pagina senza violazioni. Un filtro si scrive con le parole che il programma stampa davvero, lette su una riga reale, e si prova su un caso che deve trovare prima di fidarsi del suo silenzio.

## Una prova scritta su una fixture comoda misura la fixture

Il dato di prova si eredita. Un file di prova che esiste già porta le sue finzioni, e scrivere la prova successiva riusandole costa niente ed è quasi sempre giusto. Il caso in cui è sbagliato, e in cui l'errore non si vede, è quello in cui il difetto che si vuole fissare **dipende dalla forma del dato**: lì una finzione comoda può non contenere affatto il difetto, e la prova passa prima della correzione esattamente come dopo.

Il caso che ha insegnato la regola. Un elenco raggruppato mostrava un'intestazione per gruppo e, sotto, le righe del gruppo. Un cambio di modello aveva reso il gruppo coincidente con il suo unico elemento, quindi l'intestazione ripeteva alla lettera la riga sottostante, ed era quella ripetizione che andava tolta. La prima stesura della prova riusò la finzione già presente nel file, dove il nome del gruppo e quello della riga erano stati scritti diversi per comodità di lettura. Con quel dato i due testi non coincidono, la ripetizione non esiste, e la prova sarebbe stata verde in entrambi i mondi. La finzione fu rifatta andando a leggere **come quel campo viene valorizzato in produzione**, che era una sola riga di codice nel modulo che crea i documenti: da lì la prova è diventata rossa, dichiarando due elementi dove ne chiedeva uno.

La prescrizione. Prima di scrivere l'atteso di una prova che riguarda la forma di un dato, si legge chi scrive quel dato nel percorso reale, e la finzione si costruisce su quello. Non è una regola sulla fedeltà in generale, che costerebbe troppo e non servirebbe: vale per i campi su cui il difetto si gioca, e il modo di riconoscerli è chiedersi se cambiando il valore della finzione il difetto sparirebbe. Se la risposta è sì, la finzione è parte dell'oggetto misurato e non del contorno.

Corollario, perché è il motivo per cui l'errore passa inosservato. Una finzione comoda viene di solito scritta da chi conosceva il dominio al tempo in cui il modello era un altro, e resta corretta rispetto a quel modello. Quel dato è **vecchio**, e un dato vecchio supera ogni rilettura perché non contiene niente di falso, solo qualcosa che non è più il caso.

## Una prova che fallisce in modo plausibile manda a cercare nel posto sbagliato

Un evento sintetico che **imposta un valore** non riproduce sempre l'interazione che si vuole provare: alcuni componenti reagiscono alla sequenza di digitazione e non al valore finale, quindi il campo risulta pieno e la logica che dipende dalla digitazione non è mai partita. La prova allora fallisce dicendo che l'effetto atteso non c'è.

Il punto non è la differenza fra i due modi di scrivere in un campo, che cambia da libreria a libreria e si risolve leggendone la documentazione. Il punto è la **forma del fallimento**: la prova fallisce **esattamente come fallirebbe se il difetto non fosse stato corretto**. Non c'è niente, nel messaggio, che distingua "la correzione non funziona" da "l'interazione non è mai avvenuta", e la prima ipotesi è sempre la propria colpa. Si perde tempo a rileggere il codice del progetto mentre la causa sta nell'attrezzo.

La prescrizione è un gesto, non una regola da ricordare. Quando una prova di interazione fallisce dicendo che l'effetto non c'è, prima di toccare il codice si scrive una **prova usa e getta sul componente nudo della libreria**, fuori dal proprio, con dati finti e un effetto riconoscibile. Se lì il comportamento è lo stesso, la causa non è nel progetto. Costa un minuto, separa in un colpo solo il proprio codice da quello della dipendenza, e si cancella appena ha risposto.

Il corollario che vale oltre il caso: **una prova di interazione andrebbe vista fallire per il motivo giusto, non solo fallire.** La non vacuità chiede di vederla rossa prima della correzione; questo aggiunge che il messaggio con cui è rossa va letto, perché due cause diverse producono lo stesso rosso.

## Un guasto per dimenticanza non si coglie con una prova sul comportamento

Prima di scrivere le prove di una funzione conviene chiedersi **in che modo si guasterà**, perché ci sono due specie di guasto e vogliono due specie di prova.

Un guasto per **errore** si manifesta: qualcosa va in eccezione, un valore è diverso da quello atteso, uno schermo resta vuoto. La prova che lo coglie sta sul comportamento, nel punto in cui accade, ed è quella che viene naturale scrivere perché c'è un sintomo a suggerirla.

Un guasto per **dimenticanza** non si manifesta affatto. Nasce dove una funzione è fatta di due pezzi che vivono in posti diversi, e uno dei due è quello che chi lavora nota subito mentre l'altro no: una voce di menù e il testo che le corrisponde, una colonna e la sua etichetta, una chiave di configurazione e il suo valore predefinito. Chi aggiunge il primo pezzo lo vede, perché senza di quello non compare niente; il secondo può dimenticarlo, e il risultato non è un errore ma un'identificazione grezza mostrata al posto di una frase, una colonna senza intestazione, un valore vuoto accettato in silenzio. Niente diventa rosso, e lo vede per primo chi usa il prodotto.

La prova che coglie il secondo genere **non sta sul comportamento**: percorre l'elenco dei pezzi del primo tipo e chiede, per ciascuno, che il pezzo corrispondente esista. è una prova sulla **completezza di una corrispondenza fra due posti**, non su un'esecuzione, e si scrive una volta sola a prescindere da quanti elementi l'elenco conterré. La sua non vacuità si verifica aggiungendo all'elenco un elemento senza il suo corrispondente.

Il motivo per cui va detto invece di essere lasciato all'intuito: questa prova **si salta volentieri**, perché non c'è nessun sintomo che la suggerisca e perché al momento di scriverla la corrispondenza è completa per costruzione, essendo stata appena creata da chi scrive. Il guasto arriva mesi dopo, dalla mano di qualcun altro.

## Quando una verifica manuale smentisce una prova verde

Succede, ed è successo due volte in due giorni nello stesso progetto. La reazione corretta non è correggere il sintomo ma capire perché la prova non l'aveva visto, e scrivere quella ragione dove la leggerà chi scriverà la prossima prova. Un difetto trovato a mano dopo una suite verde è un difetto *della suite* oltre che del codice, e ignorare la seconda metà garantisce la ripetizione.

Vale anche il verso positivo, da dire a chi esegue la verifica manuale: un risultato inatteso vale più di uno atteso, e va riportato insieme al passo che lo ha prodotto invece di essere aggiustato a mano e dimenticato.

Il verso opposto esiste, e prima di cercare il difetto va escluso. Caso osservato: chi verificava una ricerca ha concluso che non cercasse, mentre le prove la davano corretta; il contatore dei risultati sullo schermo diceva "1", quindi cercava. Il suo effetto, cioè l'elenco filtrato, era finito sotto un piè di pagina fisso, spinto in basso da un testo di spiegazione aggiunto nella stessa modifica per rendere la funzione più chiara. Avevano ragione le prove, e il difetto era vero lo stesso: un effetto che non si vede, per chi usa l'interfaccia, è una funzione che non funziona. Ne seguono due cose. Quando una verifica manuale dice che qualcosa non succede, la prima domanda è se succede fuori vista, e la risposta si cerca nello screenshot, in un contatore o in uno stato che il gesto modifica, prima che nel codice. E ogni testo o controllo aggiunto sopra la zona in cui un gesto produce il suo effetto va riverificato a schermo, perché nessuna prova che non calcoli la disposizione può accorgersi che l'effetto è uscito dalla vista.

## Un difetto di forma si corregge in tutte le sue occorrenze, non in quelle viste

Caso osservato, in una sola verifica dal vivo divisa in tre giri. Al primo giro un contatore diceva "1 risultati": corretti i due testi visibili in quella schermata. Al terzo giro un avviso diceva "applicata a 1 invitati", e altri sei testi dello stesso componente avevano lo stesso difetto, che nessuno aveva cercato; insieme è emerso anche il caso dello zero. Ogni giro di verifica ne ha trovato un pezzo, perché la correzione seguiva lo schermo invece che la forma.

La regola: quando un difetto ha una forma riconoscibile, cioè un plurale con il numero, un percorso relativo, un testo scritto fuori dalle traduzioni, un colore scritto a mano, prima di chiuderlo si elencano tutte le occorrenze di quella forma nel perimetro toccato, con uno strumento e non a memoria, e si correggono insieme. Si dichiara il perimetro dell'elenco, come per ogni misura. Una verifica dal vivo trova un'occorrenza per volta, e a quella velocità le occorrenze restanti arrivano all'utente.

## In una verifica manuale si marca quale passo è quello discriminante

Caso osservato su una sequenza di quattro passi, scritta apposta per riverificare una correzione che al primo tentativo non aveva chiuso il difetto. I passi erano: creare un elemento e controllare che nasca in una posizione libera, crearne un secondo e controllare che non si sovrapponga, *spostarne uno a mano*, crearne un terzo e controllare che non atterri sopra nessuno.

Solo il terzo e il quarto passo, presi insieme, esercitano il difetto, e la ragione è che lo spostamento cambia la *composizione dell'insieme* da cui il calcolo deriva la posizione: l'elemento spostato acquista una collocazione propria, esce dall'insieme di quelli senza, e fa scalare l'indice di tutti gli altri. I primi due passi percorrono il caso facile.

Che cosa è successo davvero, ed è il motivo per cui la lezione merita di essere scritta. La prima esecuzione si è fermata dopo il primo passo e la cosa è stata registrata come verifica parziale, il che ha funzionato. Ma la seconda esecuzione, in una sessione diversa, ha rifatto **di nuovo il primo passo** prima di arrivare al terzo, e senza un richiamo esplicito si sarebbe fermata di nuovo lì: dall'esterno i passi si assomigliano tutti, sono tutti "crea un elemento e guarda dove finisce", e nulla nella lista diceva quale dei quattro portasse l'informazione. *Il passo facile è stato eseguito due volte, quello discriminante ha rischiato di non esserlo mai.*

La prescrizione che ne discende è minima e costa una riga. Chi scrive una sequenza di verifica manuale dichiara, accanto al passo che conta, **perché** conta e che cosa distingue: non "crea un terzo elemento" ma "crea un terzo elemento, ed è questo che la correzione precedente sbagliava, perché lo spostamento del passo prima ha cambiato l'insieme". Chi esegue, allora, sa che fermarsi prima non è fermarsi a metà ma fermarsi a zero.

Il criterio per riconoscere il passo discriminante, quando la sequenza la si sta scrivendo: è quello che *modifica lo stato da cui il codice deriva il risultato*, non quello che ripete l'operazione osservata. Un passo che ripete l'operazione precedente con un nome diverso aggiunge fiducia e non aggiunge informazione, ed è utile dirlo, perché a quel punto chi esegue può anche saltarlo consapevolmente invece di saltare l'altro per stanchezza.

### Marcare il passo non basta: vanno nominati il luogo dell'osservazione e la precondizione sul dato

Aggiunto dopo che la prescrizione qui sopra è stata applicata e la verifica è **comunque** fallita, in due modi diversi nella stessa esecuzione. Il passo discriminante era marcato, chi eseguiva ha seguito la lista alla lettera e in buona fede, e due passi su quattro non hanno esercitato niente.

Il primo modo è il luogo. La sequenza diceva di cambiare un valore e poi di osservarlo in una certa schermata, e in quell'interfaccia **lo stesso nome compariva due volte**: come voce di menu e come riquadro dentro un'altra schermata. Il difetto viveva solo nel riquadro; la voce di menu era uno dei punti che leggevano già correttamente. Chi eseguiva ha guardato quella, ha visto numeri giusti, e ha concluso che la correzione funzionasse. La conclusione era vera e la prova non c'entrava.

Il secondo modo è la precondizione sul dato. Un passo chiedeva di modificare un record e di osservare uno contatore derivato, ma il contatore per costruzione somma solo i record in un certo stato. Il record scelto non era in quello stato, quindi il contatore **non si sarebbe mosso nemmeno a codice corretto**: la prova sarebbe risultata negativa per una ragione che non ha niente a che vedere con il difetto. Un passo che può fallire per il motivo sbagliato è peggio di un passo assente, perché produce una diagnosi.

Ne discende che una casella di una sequenza manuale porta tre cose e non una. Il gesto, cioè che cosa fare. Il **luogo**, cioè dove si guarda il risultato, disambiguato quando l'interfaccia riusa lo stesso nome. E la **precondizione**, cioè quale proprietà deve avere il dato su cui si opera perché il passo eserciti davvero il codice, scritta accanto al passo e non in una premessa che chi esegue ha letto dieci minuti prima.

Il criterio per scriverla, quando la sequenza la si sta redigendo: si prova a immaginare un'esecuzione che segue ogni parola della casella e che tuttavia non toccherebbe il difetto. Se quell'esecuzione esiste, alla casella manca il luogo o la precondizione.

### Una precondizione che non si può osservare è un'assunzione, e il tempo la logora

Aggiunto dopo che anche la prescrizione qui sopra è stata applicata e la verifica ha trovato un terzo modo di non concludere. La precondizione era scritta accanto al passo, con i numeri attesi, e chi eseguiva l'ha letta. Mancava una cosa sola: **il modo di guardarla**. La proprietà richiesta era l'assenza di un campo su certi record, e quel campo non è mostrato da nessuna schermata, perché si scrive solo alla creazione e in modifica non compare. Chi eseguiva poteva quindi vedere il risultato ma non la premessa, e la premessa restava un'assunzione travestita da controllo.

Una precondizione porta perciò un quarto elemento oltre al gesto, al luogo e alla proprietà: **dove si osserva quella proprietà**, con lo stesso grado di precisione del luogo del risultato. Se la risposta è che non si osserva da nessuna parte, il passo non è verificabile come scritto e la sequenza deve dire cosa fare al suo posto, per esempio leggere il dato alla fonte invece che nell'interfaccia, oppure costruire deliberatamente un record che abbia la proprietà voluta.

Il caso ha portato con sé una seconda osservazione, più banale e altrettanto costosa. Fra la scrittura della sequenza e la sua esecuzione era passato un giorno, e **i dati reali erano cambiati**: un record confermato in meno, e la categoria che il passo nominava passata da uno a zero. I numeri attesi scritti nella casella non corrispondevano più, e senza il modo di osservare la precondizione non c'era modo di dire se lo scostamento fosse il dato che si era mosso o il codice che sbagliava. Ne discende che una sequenza manuale scritta su dati vivi dichiara **la data della fotografia** da cui i numeri attesi provengono, e che l'invariante, cioè la relazione fra i numeri, vale più dei numeri stessi: la somma delle categorie deve fare il totale, qualunque sia il totale di oggi.

## Prima di estendere un campo, si contano i suoi lettori e la sua popolazione

Caso osservato: una voce di lavoro chiedeva di aggiungere un terzo valore a un campo che ne ammetteva due. La richiesta era sensata come scritta, e due misure di dieci minuti l'hanno cambiata di natura prima che si toccasse una riga.

La prima misura è **chi legge il campo**, cercato in tutto il codice e non nel punto che si sta per modificare. Risultato: nessuno. Il solo consumatore semantico era stato tolto poco prima da una correzione indipendente, e i due usi rimasti erano entrambi di forma identitaria, cioè il campo compariva dentro una chiave di confronto e dentro una chiave di riconciliazione dell'interfaccia. Un campo senza lettori non ha bisogno di un valore in più: ha bisogno di una decisione sulla propria esistenza, che è una domanda per chi possiede il prodotto e non per chi scrive il codice.

La seconda misura è **quanto il campo sia popolato nei dati veri**. Risultato: sette unità su centonovantotto, cioè il novantasei per cento assente. Ne discendeva subito che la chiave di confronto che lo includeva non stava disambiguando niente per quasi tutti, perché per loro quel termine confrontava un valore assente con un valore assente. Una protezione che i dati rendono inerte è indistinguibile da una assente finché qualcuno non la conta.

La terza, che è la verifica dell'alternativa: **la chiave funzionerebbe senza quel campo?** Contate le coppie residue, erano tutte distinte, e non per fortuna, perché l'identificatore del documento era costruito con gli stessi due elementi e quindi una collisione sarebbe già stata impossibile a monte. La protezione era ridondante per costruzione, non solo inerte nei fatti.

La regola che ne discende è breve. Davanti a una richiesta di estendere un tipo enumerato si contano tre cose prima di scrivere: **chi legge**, **quanto è popolato**, **che cosa resta se lo si toglie**. Nessuna delle tre si deduce dal codice che si sta per modificare, e tutte e tre possono trasformare un'aggiunta in una rimozione.

C'è un secondo corollario, scoperto scrivendo la correzione e non prevedendolo: **rendere modificabile un campo obbliga a toglierlo da ogni chiave che lo contiene**, e le chiavi sono più di quelle che si cercano. Nel caso osservato erano due e di natura diversa: una chiave di identità applicativa, usata per ritrovare un record dentro una lista e aggiornarlo, e una chiave di riconciliazione dell'interfaccia, cioè la chiave con cui il motore di rendering decide se un elemento è lo stesso di prima. La prima, lasciata com'era, avrebbe fatto sparire dal proprio posto la persona che si stava correggendo; la seconda avrebbe ricostruito il componente a ogni battuta, facendo perdere il fuoco a chi scriveva. Nessuna delle due si manifesta come errore: la prima produce un dato sbagliato, la seconda un fastidio che si attribuisce al browser.

Ne discende una verifica meccanica da fare prima di rendere scrivibile un campo che prima non lo era: si cerca il nome del campo in tutto il progetto e si guarda **ogni occorrenza dentro una concatenazione, un confronto di uguaglianza o una chiave**, non solo dentro i calcoli. Un campo immutabile può stare ovunque; un campo modificabile può stare solo dove, cambiando, non rompe un legame.

C'è un corollario sul significato, che è la trappola più silenziosa. Quando il campo è opzionale, l'assenza **già significa** "non specificato": aggiungere un valore esplicito con quel nome crea due rappresentazioni dello stesso stato, che è la stessa famiglia di difetti dei due contatori che contano la stessa cosa e danno risposte diverse. Il valore esplicito si giustifica solo se distingue davvero due stati, per esempio "nessuno ha ancora compilato" da "la persona ha scelto di non dirlo", e quella distinzione va chiesta a chi possiede il prodotto, non dedotta: se nessuno legge il campo, la distinzione non è osservabile da nessuna parte e quindi non esiste ancora.

## Una prova scritta sul modello mentale del codice ne eredita il punto cieco

Caso osservato, e vale per la via con cui il difetto è emerso più che per il difetto. Una funzionalità chiedeva che uno stato sopravvivesse a un ricaricamento. La correzione lo ha messo in un posto che il ricaricamento rilegge, e lo ha letto **all'avvio**. Tutte le prove passavano, automatiche e manuali, perché erano scritte sulla stessa domanda del codice: "dopo un ricaricamento, lo stato c'è ancora?". Nessuna chiedeva chi ALTRO potesse cambiare quello stato, e per quali vie; esisteva una via che non passa dall'avvio, e per quella via lo schermo e la fonte divergevano in silenzio.

Due conseguenze, entrambe sul metodo.

La prima: il difetto l'ha trovato **il passo di non regressione, non quello discriminante**. Il passo discriminante era costruito per confermare la correzione e la confermava; quello di ripiego, messo in lista solo per verificare che un valore sbagliato non rompesse niente, ha esercitato la via che nessuno aveva considerato. È un argomento concreto per non saltare i passi di ripiego perché «tanto passano»: arrivano dove il progetto del passo discriminante non guardava.

La seconda, che si può applicare a tavolino senza aspettare una verifica: davanti a uno stato che si vuole rendere persistente o condiviso, si elencano **tutte le vie per cui quello stato può cambiare**, non solo quella che si sta implementando. Una prova scritta guardando il codice copre le vie che il codice conosce, e quelle sono per costruzione le vie in cui il codice è già corretto.

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

## Una politica dell'ambiente non la vede la prova, e chi sviluppa l'ha già rilassata

Una parte del comportamento non sta nel codice ma nell'ambiente che lo esegue, e una prova di componente, che sostituisce l'ambiente, non la può vedere. Caso osservato in un progetto istanziato il 2026-10-21: la richiesta di un token OAuth con finestra partiva dopo la scelta di un file invece che sul clic, e il browser, che apre una finestra nuova solo in risposta diretta a un gesto dell'utente, la bloccava. Il flusso falliva sempre al primo uso di un utente vero e mai a chi lo sviluppava, perché il suo browser aveva già consentito i popup a quel dominio; e il codice scartava l'errore della libreria che lo diceva. Ne discendono tre cose: la verifica di un comportamento che dipende da una politica dell'ambiente si fa dal vivo con le impostazioni predefinite, per esempio un profilo nuovo del browser con il blocco dei popup attivo; il codice non scarta l'errore con cui la libreria segnala quel rifiuto; e dove l'ambiente pone una condizione temporale, come il gesto dell'utente, il passo che la richiede sta prima di ogni attesa.

## Una proprietà dei dati non la sorveglia nessuna prova

L'ultima forma, osservata tre volte nello stesso progetto istanziato e diversa da tutte le precedenti perché la prova non sbaglia niente: semplicemente non può vedere. Una suite esercita il codice su dati costruiti per l'occasione, quindi resta verde qualunque cosa contengano i dati veri. Tre decisioni dipendevano proprio da quello: una vista che raggruppava per un campo che nessun record popolava, costruita e rimossa tre volte su tre criteri diversi; un ripiego di lettura che si poteva togliere solo quando nessun record fosse rimasto senza il campo nuovo; un campo compilato a mano di cui nessuno sapeva a che punto fosse. In tutti e tre i casi la scoperta è arrivata dopo, guardando il risultato vuoto.

Il presidio non è una prova ma una **misura**: uno strumento di sola lettura che, dato un campo, conta su quanti record reali è valorizzato, vuoto, assente, oppure irraggiungibile perché il percorso si interrompe prima. Separare l'ultimo esito dall'assenza non è pedanteria: un record senza il contenitore non è un elemento senza il campo, e sommarli mette due unità di misura nello stesso numero. La conta va scritta come funzione pura, provata sui record già letti, e la lettura va tenuta a parte, così che la logica si provi senza toccare la rete.

La regola che ne discende: **prima di costruire una vista che raggruppa per un campo, o di togliere un ripiego che dipende dalla migrazione di un campo, si conta quante righe quel campo lo hanno.** La prima misura, nel caso osservato, ha dato zero su centonovantacinque per il campo del grafico rimosso e cinque su centonovantacinque per quello che lo aveva sostituito, cioè ha confermato in un comando ciò che tre giri di costruzione avevano scoperto a posteriori. Due riserve vanno dichiarate accanto a ogni misura. La prima è l'ambiente su cui è stata presa, perché un conteggio sullo sviluppo non autorizza una rimozione in produzione. La seconda è che due conteggi uguali non sono gli stessi record: se una decisione dipende dalla corrispondenza fra due campi, serve l'incrocio e non il confronto dei totali.

## Un controllo di esistenza non misura un servizio il cui valore è un tasso

La stessa cecità ha una forma in esercizio, osservata il 2026-10-20 in un progetto istanziato che costruiva il presidio di una rete. Quando il valore di un servizio è un tasso, cioè quanto produce per unità di tempo, un controllo che ne verifica l'esistenza non lo misura: la porta risponde, il processo è attivo, il controllo resta verde, e il servizio può essere degradato fino a non produrre quasi niente. Il guasto ha la forma di un gradino che nessuna sonda di disponibilità vede, perché tutto ciò che la sonda interroga è vero.

Ne discendono tre prescrizioni. Ogni sorgente di un presidio dichiara da che cosa dipende il suo valore, e se è un tasso raccoglie quel segnale accanto alla disponibilità: righe ricevute, campioni scritti, byte trasferiti nell'intervallo. Il segnale si conserva come serie e non come ultimo valore, perché un gradino si riconosce solo confrontandolo con ciò che c'era prima. E una misura presa su un sistema che potrebbe essere degradato porta la data accanto, e si ricontrolla prima di appoggiarvi una decisione, come vuole il principio generale per cui un intervento il cui scopo è un effetto misurabile non si chiude senza la misura.

## Un rosso che non ha eseguito niente

Specchio della prova verde che non esercita il difetto, e altrettanto capace di far perdere tempo nella direzione opposta. Osservato il 2026-09-30 in un progetto istanziato: tutti i lavori della verifica automatica di una pull request rossi in tre o quattro secondi, compresi quelli su parti del codice che la modifica non toccava. La tentazione è cercare il difetto nel diff. La causa era che **nessun lavoro era partito**: il servizio di integrazione continua aveva esaurito i minuti inclusi nel piano per un repository privato, con un limite di spesa a zero che blocca invece di fatturare. Confermato dalla notifica del fornitore (2000 minuti usati su 2000, rinnovo il giorno dopo), non solo dall'annotazione del lavoro.

Due segni lo distinguono da un fallimento vero, e si guardano prima di aprire il codice. Il **tempo**: un lavoro che installa dipendenze non fallisce in tre secondi per una causa nel programma. La **coincidenza**: se cadono insieme lavori che verificano parti indipendenti, la causa sta in ciò che hanno in comune, cioè l'infrastruttura, e non in una modifica che ne tocca una sola. La conferma sta nell'annotazione del lavoro, che dice esplicitamente se è stato eseguito.

Il punto che vale oltre il caso: **sulla pagina della pull request un lavoro non eseguito e un lavoro fallito hanno lo stesso segno rosso**, così come un lavoro verde che non esercita niente ha lo stesso segno di uno che misura. Finché i lavori non girano, per quella modifica valgono soltanto le verifiche eseguite a mano, e va scritto così, invece di lasciar credere che la verifica automatica l'abbia vista. Un dato utile per prevedere il blocco: il consumo fatturato è sensibilmente più alto della durata delle esecuzioni sommata, perché si paga per lavoro e con arrotondamento per eccesso al minuto; nel caso osservato 1103 minuti di durata a parete sono diventati circa 2000 fatturati, poco meno del doppio, con quattro lavori in parallelo per esecuzione.

## Il servizio di prova deve esistere prima della suite

Un progetto istanziato usa prove di integrazione che chiamano un PostgreSQL reale, ma alcuni gruppi sono dichiarati con `skipIf(!DATABASE_URL)`. Se manca la variabile, Vitest può terminare verde perché esegue solo le prove indipendenti dal database. Se la variabile arriva dalla shell e punta per errore a un servizio remoto, i test scrivono dove non dovrebbero. La stessa classe di problema vale per emulatori di altri servizi avviati in CI: la presenza di una suite nel workflow non dimostra che essa abbia incontrato il bersaglio previsto.

Il tool `verifica-ambiente-test.py`, che in questo repository vive accanto alla skill in `.claude/skills/prove-che-misurano/tools/` e che un progetto istanzia nella propria cartella `tools/`, è un controllo preliminare per URL di servizi locali. Legge prima l'ambiente del processo e, solo se la variabile manca, un file di test indicato esplicitamente. Richiede uno schema, un host loopback e una porta esplicita; con `--tcp` verifica anche che il servizio accetti connessioni. Fallisce prima della suite se il bersaglio manca, è remoto o non risponde. Non stampa password o stringhe di connessione. Esempio, dalla radice di un progetto che lo ha istanziato: `python tools/verifica-ambiente-test.py --env-file .env.test --loopback-url DATABASE_URL --tcp`.

Questo presidio misura soltanto la disponibilità e la destinazione del servizio. Non dimostra che le prove abbiano eseguito i casi importanti, né che l'emulatore riproduca i limiti della piattaforma remota. Dopo la suite si controllano i test eseguiti e quelli saltati; per i limiti osservabili solo nel servizio pubblicato serve una prova di staging distinta.

## Prima di modificare un file con uno strumento, si misura il giro a vuoto

Quando un file si modifica dentro uno strumento che lo importa e lo riesporta, come un editor di animazioni, di diagrammi o di fogli di calcolo, la prima cosa da misurare è il giro senza modifiche, confrontando il prima e il dopo **valore per valore**. Contare le strutture non basta: stesso numero di livelli, di forme e di nodi con zero avvisi è compatibile con una curva di interpolazione cambiata o con un numero arrotondato. Senza quella misura, ogni differenza vista dopo la modifica vera viene attribuita alla modifica, anche quando la produce lo strumento.

Il confronto separa due specie di differenza, e la distinzione va fatta caso per caso perché a prima vista si somigliano. Le differenze **di scrittura**, cioè valori predefiniti scritti per esteso, uno scalare diventato vettore di un elemento, un terzo asse a zero, una curva lineare riscritta con altri punti di controllo ancora sulla diagonale, non cambiano niente a video. Le differenze **di sostanza** sì. Caso osservato: un giro in un editor di animazioni ha riscritto 2.414 valori, e otto curve sembravano diventate davvero non lineari. Cercate una per una, stavano tutte fra due valori uguali, dove la curva non sposta niente. Il criterio con cui si decide è l'effetto sul valore interpolato, non la forma della curva.

La seconda conseguenza riguarda la revisione. Un'esportazione che riscrive tutto il file produce un diff in cui le righe cambiate davvero si perdono fra migliaia di righe solo riscritte. Dove la modifica è esprimibile sul sorgente, cioè colori, spessori, tempi o valori di un fotogramma chiave, si scrive con uno script che tocca solo quei campi, e lo strumento serve a vedere il risultato, non a produrlo.

## Uno strumento d'anteprima è un altro motore

Quando un file viene disegnato dall'applicazione con un motore e guardato durante il lavoro con un altro, cioè l'editor del formato, un visualizzatore o un'esportazione in immagine, quello che si vede nel secondo è una previsione di quello che mostrerà il primo, non una sua misura. Caso osservato: in un'animazione vettoriale un contorno aggiunto come gruppo sopra il contenuto di un livello appariva giusto nell'editor e coperto a metà nell'applicazione. Il motore dell'applicazione applica uno stile del contenitore a tutti i tracciati che lo precedono, gruppi compresi, e l'editor no. Lo ha mostrato il motore vero, fatto girare fuori dal browser dentro un DOM simulato: l'SVG prodotto ripeteva lo stesso tracciato tre volte. Ne segue che, dove i due motori possono divergere, la verifica si fa con quello dell'applicazione, e la regola che il confronto ha fatto emergere diventa una prova sul file, con un caso costruito sul difetto perché la prova non passi per costruzione.

## Una correzione si chiude nominando la causa, non il sintomo

Un sintomo può avere due cause, e una correzione chiusa sul sintomo dichiara chiusa anche quella che non ha toccato. Caso osservato: "la figura mostrava lo sfondo all'interno" è stato segnato come risolto dopo aver riempito una delle due regioni vuote. L'altra, aperta da un altro tracciato, è rimasta così per due mesi e mezzo mentre il registro diceva che il difetto non c'era più. La chiusura va scritta sulla causa tolta, cioè quale elemento e quale regola, perché è la sola forma che chi rilegge può confrontare con ciò che vede ancora.

## Un difetto trovato dal vivo è un esemplare di una famiglia

Salita il 2026-10-19 da un progetto istanziato. Una verifica dal vivo ha mostrato una frase con il plurale sbagliato, "2 importo escluso". Prima di correggerla si è cercata la forma del difetto in tutte le traduzioni, cioè ogni frase con un numero e una sola forma, e se ne sono trovate altre sette, alcune visibili agli utenti finali e mai notate. Correggere la sola frase segnalata avrebbe lasciato le altre, e la nona scritta il giorno dopo avrebbe riaperto la famiglia.

Il gesto è in due tempi. Prima si scrive la domanda che ha fatto notare il difetto in una forma cercabile e la si pone a tutto il codice o a tutti i testi. Poi, se la famiglia ha più di un esemplare, la si chiude con una prova strutturale che percorre tutti gli elementi e accetta solo quelli conformi o dichiarati in un elenco di eccezioni con la ragione: è la prova di completezza di una corrispondenza descritta più sopra, applicata a ciò che un difetto ha appena insegnato a cercare. La sua non vacuità si vede lanciandola prima della correzione, quando deve elencare esattamente gli esemplari trovati.

## Prima di togliere un doppione, si verifica che lo sia

Due schermate che mostrano gli stessi numeri con le stesse etichette sembrano un doppione, e togliere la seconda sembra un'operazione senza rischio. Non lo è finché non si è controllato che contino **lo stesso insieme con lo stesso criterio**. Caso osservato: una scheda da smantellare aveva un riepilogo delle risposte identico a quello del cruscotto, quattro numeri con gli stessi nomi. Il cruscotto contava tutti gli invitati, la scheda solo quelli che potevano rispondere, e la differenza erano persone che per costruzione restano "in attesa" per sempre. Togliere la scheda avrebbe tolto l'unico posto in cui si leggeva quante risposte mancavano davvero. La decisione di smantellarla non lo nominava, perché a vista era un doppione. Il controllo costa una lettura delle due espressioni che producono i numeri, e il rimedio è decidere con chi usa i dati quale criterio tenere e dove mostrare l'altro.

Lo stesso vale nell'altra direzione, quando si sposta un blocco in una schermata che ha già qualcosa di simile: prima si guarda che cosa la destinazione mostra già, e si porta solo la parte che le manca, completando l'elemento che c'è invece di affiancargliene un secondo che ripete metà del primo.

## Un silenzio che non ha eseguito niente

È lo stesso inganno del rosso che non ha eseguito niente, applicato a un controllo di assenza. Caso osservato in un progetto istanziato: per sapere se un file di prove esistesse, l'agente lo aveva cercato in coda a un comando composto, dopo un cambio di ramo. Il cambio di ramo era fallito e la catena si era fermata lì, quindi la ricerca non era partita. Il suo silenzio è stato letto come "il file non c'è", e una suite di sedici prove è stata sovrascritta da un file nuovo di tre. Se n'è accorto più tardi, per un caso: un documento elencava quel modulo fra quelli con una suite. Il file è stato recuperato da git, perché era committato.

Due regole ne discendono. Un controllo di assenza **dice esplicitamente l'esito in entrambi i casi**, per esempio stampando "assente" o "presente", così che un silenzio non possa essere una risposta. E sta **in un comando suo**, non in coda a un'operazione che può fermarsi prima. Il segnale che smentisce, quando c'è, è lo strumento di scrittura che risponde "aggiornato" invece di "creato": va letto, perché è l'ultimo momento in cui l'errore costa una riga.

## Una decisione presa guardando lo schermo si rilegge sul codice prima di eseguirla

Una decisione scritta guardando l'interfaccia descrive ciò che si vede, e il codice dice che cosa c'è sotto. Caso osservato in un progetto istanziato: la decisione di fondere due schede chiedeva che nella scheda unita si potessero modificare tre campi di un elemento. Un inventario delle due schede, fatto prima di disegnare, ha mostrato che due di quei campi non si erano mai potuti modificare dopo la creazione. Erano il nome stesso dei documenti dell'elemento, e cambiarli avrebbe significato spostare quei documenti e ogni riferimento a loro, cioè un'operazione grande e rischiosa che nessuno usava. La richiesta descriveva una funzione che non esisteva.

L'inventario è meccanico e si può delegare: per ogni modulo coinvolto, che cosa crea, modifica e cancella, con il riferimento alla riga, verificato poi a campione. Il passo che non si delega è il seguito: ogni differenza fra la decisione e il codice torna a chi ha deciso, con la strada raccomandata e il costo dell'alternativa, prima di scrivere codice. Eseguire alla lettera una decisione su un presupposto falso costruisce una cosa che nessuno ha chiesto davvero.

## Un difetto dedotto si prova nella sua premessa, prima di correggerlo

Caso osservato in un progetto istanziato. Una coda di messaggi scriveva ogni elemento con un identificativo deterministico, e il commento diceva che un ritentativo avrebbe riscritto lo stesso documento. Leggendo le regole del database si deduceva il contrario: la scrittura su un documento esistente era un aggiornamento, e l'aggiornamento era negato. Ne seguiva che un ritentativo dopo una risposta persa veniva respinto, e un messaggio accodato davvero risultava fallito. La deduzione era scritta da settimane come "non provato".

Prima di correggere si è scritta la prova della premessa, contro l'emulatore delle regole: due scritture sullo stesso identificativo, la seconda respinta. È passata, e solo allora si è cambiato il codice, che ora legge quel rifiuto come successo quando segue un tentativo fallito per un errore transitorio. Due ragioni per l'ordine. Se la premessa fosse stata falsa, la correzione avrebbe aggiunto un ramo per un caso che non esiste, e un ramo che tratta un errore come successo è il più pericoloso da avere senza motivo. E la prova della premessa non si butta dopo la correzione: resta a dire che cosa succede il giorno in cui qualcuno cambia le regole, perché la correzione dipende da lei e da nient'altro.

La regola: quando un difetto è dedotto leggendo un sistema che non si controlla, cioè regole, configurazione, comportamento di una libreria, la prima prova da scrivere non è quella della correzione ma quella della deduzione. La seconda prova, quella della correzione, si scrive dopo e si fa cadere togliendo la correzione, come sempre.

## Una prova dal vivo si fa dove sta il codice, e il dove si legge

Caso osservato in un progetto istanziato: una correzione pubblicata a mano sull'ambiente di prova è stata dichiarata "smentita dal vivo", perché la ricetta del difetto falliva ancora. Il pacchetto pubblicato era stato controllato, e conteneva la correzione. Ma la scheda in cui la prova girava era aperta sull'anteprima della pull request, un'origine diversa, costruita giorni prima dalla pipeline con il codice vecchio. Controllare il pacchetto pubblicato verifica il sito, non la scheda di chi prova. La conclusione falsa è rimasta scritta per un giro, con la sua correzione accanto.

La regola: ogni passo di una verifica dal vivo nomina l'indirizzo esatto, e prima di leggere l'esito si legge l'indirizzo davvero aperto (la barra, o la riga di navigazione della console con il log conservato). Quando esistono più ambienti con lo stesso codice a versioni diverse, come un ambiente di prova pubblicato a mano e un'anteprima costruita dalla pipeline, il tester va avvisato di quale non usare.

L'indirizzo giusto non basta, e lo ha mostrato un secondo caso nello stesso progetto, a una settimana dal primo. La correzione era pubblicata, il pacchetto servito era quello nuovo e la scheda era sull'ambiente giusto; la verifica ha dato lo stesso esito di prima e la correzione è stata dichiarata non risolutiva. La scheda era stata aperta prima della pubblicazione, e una pagina a scheda singola esegue il pacchetto che ha caricato, finché non la si ricarica; l'istruzione di verifica, anzi, chiedeva di non ricaricare, per non perdere uno stato della pagina. Una prova end-to-end scritta per separare le ipotesi, che legge lo stato grezzo fra la scrittura e la lettura, ha mostrato la correzione funzionante nei due versi, e la verifica dal vivo rifatta dopo un ricaricamento forzato le ha dato ragione.

La regola si allarga di conseguenza. Ogni verifica dal vivo dopo una pubblicazione comincia con il ricaricamento forzato della pagina, scritto come primo passo e non lasciato al buon senso del tester. E una verifica che smentisce una correzione si controlla prima nelle sue premesse, cioè quale codice stava davvero girando nella scheda, prima di cambiare diagnosi: la smentita è anch'essa un'osservazione, e ha le sue precondizioni. Quando due ipotesi restano in piedi, scrittura o lettura, la prova che le separa legge lo stato grezzo nel mezzo, e dove una persona non può farlo una prova end-to-end contro gli emulatori lo fa senza chiederle niente.

## Una prova che discrimina usa ciò che l'ipotesi chiama in causa

Caso osservato in un progetto istanziato: un pannello rifiutava a volte i permessi con una sessione valida. La causa era una memoria condivisa fra le schede della stessa origine, una cache di database con una scheda capofila che parla col server per tutte, mentre la sessione stava in una memoria per scheda: con un'altra scheda autenticata con un'identità diversa, le letture del pannello partivano con l'identità sbagliata. Una prima prova dell'ipotesi l'aveva "esclusa" aprendo una seconda scheda senza accesso: ma una pagina che non usa il database non partecipa all'elezione della capofila, quindi quella prova non poteva vedere niente. Un mese dopo, la stessa prova con una seconda scheda che usava davvero il database ha riprodotto il difetto al primo colpo.

Due lezioni. Una prova discrimina solo se la variabile che introduce partecipa al meccanismo ipotizzato: una scheda vuota non è una scheda "più severa", è una scheda che non c'entra. E due memorie del browser con portate diverse, una per scheda e una per origine, messe a lavorare insieme, condividono un'identità senza che nessuno l'abbia deciso; se la sessione è per scheda, la cache che porta le sue letture al server deve esserlo anch'essa.

## Una fixture che fallisce prima di misurare il codice

Salita il 2026-10-20 da un progetto istanziato. Sotto un runner confinato di Windows una cartella temporanea creata dalla libreria standard nasceva, ma la sua riapertura o la sua pulizia fallivano con accesso negato; la prova sintetica di un controllo si interrompeva sul temporaneo mentre la scansione ordinaria passava, e la stessa prova, rieseguita invariata con il prefisso di test che il runner autorizzava, dava venti casi su venti. Il difetto non era nel codice provato ma nella fixture, e un test verde fuori dal confinamento non dimostrava che la fixture fosse portabile.

La prescrizione: una fixture temporanea si prova nel suo ciclo completo, crea, riapri e pulisci, sotto lo stesso utente e lo stesso confinamento del runner che la userà, e la pulizia verifica che il percorso sia suo prima di cancellare. E un errore di accesso su una fixture non si converte in un salto verde: un salto dice che la prova non ha oggetto, mentre qui l'oggetto c'era e non è stato misurato.

## Un'affermazione di protezione si scrive con il livello e il comando che la verifica

Le affermazioni che durano di più sono quelle che sembrano constatazioni, e per questo nessuno le mette alla prova. In un progetto istanziato, nel 2026-10, «filtro attivo con politica di rifiuto in ingresso» è rimasta scritta per settanta giorni in più schede, vera per i processi dell'host e falsa per i servizi in contenitore; un ramo principale era dato per aggiornato mentre era fermo da sette settimane. Erano tutte verificabili con un comando. Quando una scheda afferma che qualcosa protegge, copre o contiene qualcos'altro, l'affermazione dice a quale livello vale e porta accanto il comando che la verifica, perché una frase senza il proprio perimetro si ripete ma non si controlla (lezione L-003 di un progetto istanziato).

## Ciò che gira si chiede al motore, e nell'ambito in cui vive

Un componente nato a mano continua a funzionare mentre la documentazione lo cerca altrove: un contenitore avviato prima che il descrittore lo descrivesse, un'unità di sistema fuori dal repository, servizi lasciati in ascolto. Una modifica al descrittore allora non cambia ciò che gira, e una porta pubblicata si fissa alla creazione del contenitore, quindi la correzione richiede una ricreazione e non un riavvio. Prima di fidarsi di un file di configurazione si chiede al motore che cosa sta eseguendo (lezione L-005). E la domanda va fatta nell'ambito giusto: nello stesso progetto tre servizi erano stati dati per processi orfani perché il gestore di sistema dichiarava inattiva la loro unità, mentre le unità vivevano nell'istanza d'utente, attive e con riavvio automatico; fermarli sarebbe stato un rimedio dichiarato fatto e inefficace. Quando una misura dice assente o inattivo ciò che dovrebbe esserci, si verifica di aver interrogato l'ambito in cui l'oggetto vive, perché un ambito sbagliato risponde senza errore; e un rimedio che ferma qualcosa si scrive solo dopo aver guardato chi lo fa ripartire (lezione L-007).
