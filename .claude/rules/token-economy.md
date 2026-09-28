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
