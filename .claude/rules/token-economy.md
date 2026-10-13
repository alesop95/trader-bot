# Token economy

> Regola modulare. Consolida le pratiche di risparmio di contesto del sistema e indica quando valutare uno strumento esterno di ottimizzazione dei token. Si applica sempre, a ogni sessione.

## Principi nativi

Il sistema è già progettato per non sprecare contesto, e queste pratiche valgono sempre.

Densità sopra completezza: una sintesi densa vale più di un estratto lungo. Si scrive e si legge per segnale, non per volume.

On-demand: le skill, i capitoli di una skill-libro, le schede di `context/` e le pagine della wiki si caricano solo quando servono al task, mai tutte insieme. Il `CLAUDE.md` indicizza i satelliti, non li incorpora.

Niente riletture integrali: il motore di riconciliazione confronta i commit e legge solo le schede pertinenti; i documenti voluminosi come i `.docx` si estraggono a fette, mai letti per intero, e si tiene un mirror `.md` per i diff invece di rileggere il binario.

Si legge un file quando serve davvero, e solo la porzione necessaria, non l'intero file se non occorre.

## Più agenti insieme: quattro numeri misurati, non stimati

Sezione ricavata da un pilota reale su un corpus di trecentosettantuno documenti, portato a termine. I numeri valgono per quella forma di lavoro, non in generale, ma i rapporti fra loro sono il dato che si trasferisce.

**Il parallelismo non riduce i token.** Consuma gli stessi token in metà tempo: la quota si consuma proporzionalmente alla concorrenza, quindi il parallelismo **avvicina** il limite invece di allontanarlo. Si usa quando serve il risultato prima, mai quando si teme di esaurire la finestra. Un sistema multi-agente consuma più di una conversazione singola sullo stesso compito, e il consumo maggiore **è la ragione per cui funziona meglio**, non un effetto collaterale.

**Il modello e il livello di ragionamento valgono un fattore nove.** Lo stesso lotto, stesso mandato: centoventiduemila token per elemento con il modello generico a ragionamento medio, **tredicimila** con il modello economico a ragionamento basso. Il tempo è sceso nella stessa proporzione, il che è una buona prova che la misura sia pulita. Per una mappatura meccanica il ragionamento non serve: si paga e non produce nulla.

**Il costo per elemento cresce con la dimensione del lotto.** Ventimila token per elemento su un lotto da dieci, centoventiduemila su uno da ventiquattro, a parità di modello: è il contesto che si accumula. Ne discende che **molte sessioni brevi costano meno di una lunga**, e che un lotto unico su tutto il corpus è il modo più caro di farlo, non il più economico.

**Il limite è su finestra mobile, non giornaliero.** Nel pilota una radice ha consumato tredici milioni di token distribuiti su tredici lotti senza mai fermarsi, mentre un'altra si è fermata a nove milioni spesi in **una sola sessione concentrata**. Gli stessi token spesi a raffica esauriscono la finestra, spesi distribuiti no.

### La conseguenza operativa, in ordine

Prima **togliere elementi**: la parte deterministica di una mappatura non deve vedere un modello, e portare N da trecento a trenta vale più di qualunque ottimizzazione sui trecento. Poi **rendere il lavoro riprendibile**, perché un lavoro che riparte da capo non si conclude mai. Poi **instradare su serbatoi indipendenti**, dove esistono più flotte con quote separate. Solo alla fine **parallelizzare**, sapendo che comprime il tempo e non il costo.

Il pacchetto `lavoro-a-lotti` è l'attuazione di questi quattro punti; `agenti-terminale` fornisce le flotte su cui il terzo poggia.


### Il lavoro locale non costa token, e la sua uscita va letta per intero

Conversione, OCR, impronte e indicizzazione girano con strumenti locali e non consumano token: all'agente costano il lancio e la lettura di un riepilogo di poche righe, quindi si lanciano in background e non si rifanno a mano. Il riepilogo però va letto per intero e non solo nel codice di uscita. In un caso reale un OCR su 424 scansioni è uscito con zero e ha riportato 455 documenti assenti, perché il disco esterno era stato scollegato. L'uscita di un lavoro lungo si scrive in una cartella ignorata del progetto e non nella cartella temporanea della sessione. Un'altra sessione dell'agente sulla stessa macchina, nella sua pulizia d'avvio, può cancellare la temporanea, ed è successo tre volte nella stessa giornata. Quando gli elementi da giudicare sono molti e piccoli vale la sezione sulle etichette chiuse del pacchetto `lavoro-a-lotti`.

## Il modello si sceglie dal compito

Lezione generale nata il 2026-10-06 in un progetto istanziato. Un compito che consuma molti token ma non richiede giudizio fine va al modello più economico che lo sa fare, e il modello più capace si riserva alla parte che ne ha bisogno. La scelta si fa per compito e non per sessione, e si misura su un lotto piccolo prima di estenderla. Nello stesso caso il costo è dipeso più dal numero di turni degli agenti che dalla lunghezza del testo letto: i numeri e la procedura stanno nel pacchetto `lavoro-a-lotti`.

Una regola che va ricordata a ogni spawn è una regola che prima o poi smette di essere applicata, e nessuno se ne accorge perché il suo fallimento è silenzioso. Dal 2026-10-12 il template la rende meccanica con il pacchetto opzionale `instradamento-modelli`, una mod di Claude Code che riscrive il modello di un subagent secondo una tabella da tipo di agente a modello, ne regola lo sforzo di ragionamento e somma i token di ogni richiesta separandoli per modello. La tabella vive nella radice dell'account, quindi due account della stessa macchina possono avere politiche diverse, e il modo predefinito dichiara che cosa instraderebbe senza instradare niente, perché la linea di partenza si misura prima di spostare il traffico.

Tre avvertenze valgono anche dove quel pacchetto non è istanziato, perché riguardano la scelta e non lo strumento. L'instradamento non riduce i token, riduce il costo dei token, con la stessa distinzione che questa regola fa sul parallelismo. La conversazione principale non è il posto dove risparmiare, perché ogni suo passo si appoggia al precedente e un modello economico che ne sbaglia uno costa tutto ciò che vi si appoggia dopo, mentre un subagent ha un mandato chiuso e restituisce un risultato che l'agente principale rilegge. E un modello cambiato a metà turno invalida la cache del prompt, quindi la richiesta successiva si ripaga per intero.

## Un instradamento senza delega non instrada niente

Sezione nata il 2026-10-12 da una domanda del proprietario che ha scoperto un difetto di disegno: l'instradamento tocca soltanto i subagent, ma l'agente non apre subagent di propria iniziativa, perché la configurazione predefinita di Claude Code glielo vieta se non glielo chiede l'utente o un file di istruzioni. Le due impostazioni si tengono a vicenda, e chi ne attiva una sola ottiene un risparmio che non arriva mai: la tabella è scritta, il modo è `instrada`, e non passa di lì nessuno. Il risparmio di questa leva vale quindi quanto il lavoro che viene davvero delegato, non quanto la tabella promette.

Ne segue che l'autorizzazione a delegare si scrive dove l'agente la legge da sé a ogni sessione, cioè in un file di istruzioni, e non si ridà a voce ogni volta. Dove gli account di una macchina condividono l'impostazione, la sede giusta è il `CLAUDE.md` della radice di account, perché vale per ogni progetto aperto sotto quell'account; dove la scelta è di un progetto solo, sta nel suo `CLAUDE.md`. Il permesso ha due facce e vanno scritte entrambe, perché l'una senza l'altra produce o il risparmio che non arriva o la spesa che nessuno ha chiesto.

La prima faccia dice che cosa si delega. È meccanico il lavoro che si giudica su una regola e non su un contesto: cercare dove sta qualcosa in un repository, leggere molti file per estrarne lo stesso dato, mappare o classificare molti elementi su etichette chiuse, convertire, inventariare, contare. La seconda dice che cosa non si delega mai, ed è il resto: la revisione del codice, l'audit di sicurezza, la progettazione, la scelta fra due architetture, e ogni passo su cui si appoggia il passo successivo della conversazione principale, per la ragione già misurata qui sopra. Il numero di subagent lo decide il numero di mandati indipendenti, e un subagent non si apre per una manciata di chiamate che l'agente principale farebbe da sé; a fine giro l'agente dichiara quanti ne sono partiti, perché un conto implicito non si corregge.

Una terza condizione è meno ovvia e vale verificarla una volta per macchina, perché il suo fallimento è silenzioso. I nomi della tabella devono essere quelli che la sessione offre davvero, e un tipo di agente definito da un progetto, sotto `.claude/agents/`, è un nome in più che le sessioni di quel progetto offrono e le altre no. Il modello dichiarato nel frontmatter di quella definizione non protegge dall'instradamento e non va confuso con un modello chiesto da chi apre il subagent: il campo che la mod rispetta è il secondo, cioè il parametro passato alla chiamata, mentre il frontmatter è proprio ciò che l'instradamento sovrascrive. Verificato il 2026-10-12 sui tipi della propria interfaccia di programmazione, dove il campo è documentato come «il parametro `model` dello strumento Agent come è stato dato». Ne segue che mettere in tabella un agente di progetto è una decisione sul suo lavoro, non una svista, e va presa sapendo che vince sulla scelta scritta nella sua definizione.

La misura a coppia che lo dimostra, presa il 2026-10-12 su questo template. Lo stesso identico mandato meccanico, elencare le cartelle di un albero e dire per ciascuna se contiene un README, dato a due subagent dello stesso tipo: uno lasciato instradare su Haiku 5.5, uno forzato su Opus 5 passando il modello alla chiamata. Le due risposte coincidono, 43 cartelle e 39 con README, e coincide il numero di chiamate di strumento, due e due, il che rende il confronto legittimo invece che suggestivo; che il braccio di controllo non fosse instradato lo conferma il contatore delle proposte della mod, salito di uno e non di due. Token totali: 21 879 sul braccio instradato contro 21 235 su quello a Opus, cioè uguali entro il tre per cento, con il braccio economico che ne ha consumati di più. Convertito in costo di listino, quel lavoro vale circa 0,0035 dollari su Haiku e circa 0,175 sullo stesso profilo di token su Opus: una cinquantina di volte, che è esattamente il rapporto fra i due listini.

Ne segue la prescrizione per chi verifica. Dopo aver acceso un instradamento non si guarda se i token siano calati, perché non caleranno e si concluderebbe che non funziona: si guarda su quale modello siano stati spesi. Il segnale giusto è la comparsa di una seconda riga di modello nei conteggi, non un numero più piccolo nella prima.

Ne segue anche una domanda che va posta prima di accendere qualunque instradamento, perché la risposta cambia che cosa ci si deve aspettare, e il 2026-10-12 il proprietario di questo template l'ha posta nella forma giusta: se il prezzo dei token non lo pago io, a che serve? Verificato sulla documentazione, e la risposta si divide in due. Su un account a consumo il risparmio è diretto e si legge in fattura, nel rapporto fra i listini. Su un abbonamento no, non su quell'asse: la pagina degli errori di Claude Code dichiara che i limiti di sessione e settimanale sono condivisi fra tutti i modelli e che cambiare modello non ripristina l'accesso, quindi instradare non allarga la finestra che conta di più. Il guadagno che resta, ed è documentato, sta nei limiti per famiglia: Opus e Sonnet ne hanno uno proprio, che solo le richieste di quella famiglia consumano, e un subagent mandato su un modello di un'altra famiglia non lo intacca. Chi instrada il lavoro meccanico fuori da Opus sta quindi conservando il limite di Opus per il lavoro che Opus lo richiede davvero.

Un buco va dichiarato e non colmato, perché è esattamente il punto su cui si costruirebbe una stima sbagliata: nessuna pagina ufficiale dice a quale velocità ciascun modello consumi la finestra condivisa, né pubblica un fattore del tipo «Opus consuma N volte più in fretta di Sonnet». Le cifre che circolano su siti di terzi non sono ufficiali e si contraddicono fra loro, e non vanno citate come se lo fossero. Chi vuole saperlo per il proprio caso lo misura con `/usage`, che sui piani in abbonamento attribuisce l'uso recente anche ai subagent, prima e dopo aver acceso l'instradamento. Vale infine ricordare, perché è documentato e tocca l'altra leva di questa regola, che i subagent attingono allo stesso budget della conversazione principale, e che accendere i crediti d'uso sopra un abbonamento accorcia la vita della cache del prompt da un'ora a cinque minuti.

## Un server MCP si paga a ogni sessione, un comando si paga una volta

Sezione nata il 2026-10-12 misurando le applicazioni Craft, ma il principio non riguarda quelle: riguarda qualunque server MCP, ed è la forma che la disclosure progressiva prende quando l'oggetto non è un documento ma uno strumento.

La differenza fra le due vie non è di potenza ma di dove cade il costo. Un server MCP dichiara i propri strumenti all'apertura della sessione, con nome, descrizione e schema dei parametri, e quella dichiarazione entra in contesto prima del primo messaggio, sia che gli strumenti vengano usati sia che restino fermi. Un comando di shell non dichiara niente: costa la riga che lo lancia e il riepilogo che risponde, e quando il processo muore non resta niente in contesto. Ne segue che il server conviene al lavoro che torna indietro, cioè guardare, provare, rivedere e correggere tenendo lo stato aperto, mentre il comando conviene al lavoro che va avanti, cioè convertire, estrarre, rendere, applicare una trasformazione nota a molti file.

La misura che lo rende concreto, presa il 2026-10-12 avviando i server e contando gli strumenti dichiarati: tre applicazioni della stessa suite costano rispettivamente 21, 27 e 143 strumenti, cioè circa 4 800, 6 400 e 33 800 token a sessione. Il terzo numero vale più o meno la lettura di trenta file di codice, pagata ogni volta che si apre una sessione in quel progetto, anche per lavorarci su altro. Lo stesso lavoro fatto dalla riga di comando dello stesso programma costa zero token di dichiarazione.

Tre conseguenze operative, in ordine di quanto rendono. La prima è che un lavoro a passo unico non passa mai da un server: si guarda se lo strumento abbia una riga di comando, e quasi sempre ce l'ha. La seconda è che dove il server offre un modo ridotto lo si usa, perché un modo ridotto che conservi la ricerca e la chiamata degli strumenti nascosti non toglie capacità ma solo la dichiarazione anticipata di tutte, ed è la stessa disclosure progressiva vista dal lato degli strumenti: nel caso misurato il modo compatto scende da 143 strumenti a 17, cioè da circa 33 800 a circa 3 200 token, senza perdere nulla. La terza è che un server si collega per il lavoro che lo richiede e si toglie quando quel lavoro è finito.

Per la terza esiste una forma che non obbliga a riscrivere la configurazione ogni volta, e poggia su un fatto verificato: un server dichiarato in `.mcp.json` ma non approvato resta in attesa e non viene connesso, quindi i suoi strumenti non entrano in contesto. Lo dichiara l'aiuto di `claude mcp list`. Le voci restano allora scritte, con il loro confinamento già verificato, e si tengono spente elencandole in `disabledMcpjsonServers` dentro `.claude/settings.local.json`; accenderne una è togliere una riga, e il costo si paga solo nelle sessioni in cui è accesa. La modifica vale dalla sessione successiva, il che è un motivo in più perché il lavoro di adesso resti sulla riga di comando.

Vale infine il vincolo che il catalogo dei pacchetti già enuncia e che questa misura spiega: non più di sei server connessi in tutto, contati sul totale e non per settore, perché il costo è fisso e si paga sempre.

## Disclosure progressiva su documenti voluminosi

Un corpus documentale è troppo grande per entrare in contesto: cento documenti possono valere oltre un milione di token, e l'ottanta per cento serve come riferimento ricercabile, non come materiale di ragionamento attivo. Invece di caricare tutto, si accede ai documenti per livelli crescenti di dettaglio, scendendo solo dove serve.

Livello 1, scheletro: solo titolo, gerarchia delle intestazioni e conteggi per sezione, una manciata di token per documento. Permette di vedere un'intera cartella in poche decine di migliaia di token e decidere dove guardare.

Livello 2, preview di sezione: per i soli documenti su cui si vuole ragionare, si aggiungono l'incipit e la chiusura di ogni sezione più le entità rilevate, qualche centinaio di token per documento.

Livello 3, sezione completa: lettura puntuale di una sola sezione di un solo documento, attivata solo per rispondere a una domanda precisa.

Operativamente si parte sempre dal Livello 1 sull'intera cartella, si sale al Livello 2 solo sui documenti pertinenti al task, e al Livello 3 solo su richiesta esplicita. Vale per qualsiasi corpus, non solo per i `.docx`.

Il pacchetto opzionale `doc-ingest` (vedi `templates/doc-ingest/`) e l'implementazione di riferimento di questo principio su un corpus di più documenti: converte `.pdf`, `.docx`, `.pptx`, `.xlsx` e `.html` in una cache Markdown locale con manifest a content-hash (non riconverte l'invariato) e rigenera a ogni corsa lo scheletro di Livello 1 in un `_INDEX.md`. Resta uno strumento, non un sostituto del principio: i Livelli 2 e 3 restano disciplina di lettura sull'output che produce.

Una variante dello stesso principio sposta il corpus non su una cache locale ma su un motore di recupero esterno ancorato alle fonti. Il pacchetto opzionale `notebooklm-bridge` (vedi `templates/notebooklm-bridge/`) tiene il corpus dentro NotebookLM, nel piano gratuito accessibile solo da browser, e in conversazione fa entrare solo una sintesi densa e citata invece del testo grezzo: è un Livello 1 prodotto da un motore che risponde anche a domande mirate senza mai versare le fonti in contesto. Il risparmio è lo stesso della disclosure progressiva, con in più l'ancoraggio alle fonti che riduce le allucinazioni; il costo è che l'accesso resta manuale nel browser, o assistito via un MCP di automazione opt-in, mai un'API a pagamento.

## Deterministico prima del linguistico

In una pipeline che mescola codice e LLM, si spinge il più possibile il lavoro su codice deterministico e si riserva l'LLM al solo lavoro che richiede comprensione semantica. Parsing, estrazione con regex, trasformazioni, calcoli e generazione di file derivati sono deterministici e vanno in script. L'estrazione semantica di concetti e relazioni e la sintesi narrativa sono linguistiche e vanno all'LLM.

Tre benefici concreti. Riproducibilità: rilanciando gli script si ottiene lo stesso risultato. Economia: il lavoro deterministico costa CPU locale, non token. Ispezionabilità: gli stati intermedi sono file leggibili, tipicamente JSON, che si possono correggere a mano senza rilanciare l'LLM.

Operativamente, quando un passo si può fare con codice lo si fa con codice e se ne salva l'output come stato intermedio ispezionabile; si chiama l'LLM solo per il salto semantico, e anche il suo output torna a essere uno stato su disco, non un risultato volatile in chat.

## Igiene di sessione

Alcune abitudini operative tagliano il consumo senza installare nulla.

Il comando `/compact` va lanciato proattivamente quando il contesto raggiunge il 40-60%, non aspettando il limite automatico. Può essere guidato con istruzioni esplicite: `/compact focus on the database schema decisions and API endpoints we agreed on`. La soglia di compattazione automatica si anticipa con la variabile `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` (valori da 1 a 100), utile per evitare che la compattazione scatti a freddo sul contesto già degradato.

Prima di ogni `/clear` o di chiudere una sessione su un task non ancora concluso, si fa scrivere a Claude un file `HANDOFF.md` con le decisioni prese, i pattern stabiliti e i file toccati. La sessione successiva parte da quel file invece che da zero, recuperando il contesto senza rileggere l'intera conversazione.

La finestra da un milione di token, disponibile su Sonnet 4.6 e Opus 4.7, e utile come assicurazione per i task lunghi ma non come obiettivo: oltre i 120-150K token utili la qualità delle risposte tende comunque a degradare per accumulo di rumore nel contesto. Chunk piccoli con handoff espliciti producono risultati migliori che riempire la finestra grande.

Il principio "un task, una chat" mantiene il contesto sempre fresco: invece di una sessione fiume che accumula task diversi, si chiude e riapre per ogni unita di lavoro logica, riducendo le compattazioni multiple e il rischio di deriva del focus.

## Cautela sui workflow multi-agente costosi

Alcuni workflow integrati (per esempio `deep-research`) fanno verificare ogni affermazione estratta da più agenti indipendenti in parallelo: con qualche decina di affermazioni il numero di chiamate di verifica sale rapidamente a svariate decine, con un consumo di token che può esaurire il limite di sessione in pochi secondi, prima ancora che il workflow completi la sintesi finale. È il costo intrinseco della verifica adversariale a più voti, già osservato sul campo, e il workflow in quel caso funziona come previsto. Quando succede, non insistere rilanciando lo stesso workflow identico: o si restringe la domanda a un angolo di ricerca più stretto per lancio, invece di chiedere tutto insieme, o si riprende con il meccanismo di resume del workflow (che rilegge dalla cache gli stadi già completati e paga solo cio che manca), oppure si scende a una verifica manuale mirata delle sole fonti primarie già trovate nella fase di ricerca, con una singola chiamata di recupero pagina per fonte invece del panel a più voti: quest'ultima via è quasi sempre la più economica quando restano poche affermazioni da controllare.

## Strumenti esterni, a scelta

Quando il risparmio nativo non basta, per esempio in sessioni operative molto lunghe e ricche di output, si possono valutare strumenti esterni open source, sempre offerti come scelta al gate dei pacchetti e mai imposti.

`caveman` riduce i token di output facendo rispondere l'agente in modo telegrafico, senza toccare il ragionamento. È utile nelle sessioni operative pesanti, ma va tenuto spento quando il progetto produce documentazione o prosa leggibile, perché ne degraderebbe lo stile. Vive come tool di sessione, non come stato del progetto. Vedi la voce `caveman` in `templates/PACKAGES.md`.

Per esigenze più spinte esistono alternative come un server MCP di compressione e caching del contesto (per esempio `token-optimizer-mcp`). Si adottano solo se il guadagno giustifica la dipendenza, valutando caso per caso.

## Cosa non si fa

Non si introduce uno strumento di memoria globale che accumula stato fuori dal progetto: la memoria del sistema vive dentro il progetto, versionata, e l'auto-memory nativa di Claude resta disattivata (vedi sezione 15 di `PROJECT-SYSTEM.md`).
