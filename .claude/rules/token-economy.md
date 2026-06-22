# Token economy

> Regola modulare. Consolida le pratiche di risparmio di contesto del sistema e indica quando
> valutare uno strumento esterno di ottimizzazione dei token. Si applica sempre, a ogni sessione.

## Principi nativi

Il sistema e' gia progettato per non sprecare contesto, e queste pratiche valgono sempre.

Densita sopra completezza: una sintesi densa vale piu di un estratto lungo. Si scrive e si legge
per segnale, non per volume.

On-demand: le skill, i capitoli di una skill-libro, le schede di `context/` e le pagine della wiki
si caricano solo quando servono al task, mai tutte insieme. Il `CLAUDE.md` indicizza i satelliti,
non li incorpora.

Niente riletture integrali: il motore di riconciliazione confronta i commit e legge solo le schede
pertinenti; i documenti voluminosi come i `.docx` si estraggono a fette, mai letti per intero, e si
tiene un mirror `.md` per i diff invece di rileggere il binario.

Si legge un file quando serve davvero, e solo la porzione necessaria, non l'intero file se non
occorre.

## Disclosure progressiva su documenti voluminosi

Un corpus documentale e' troppo grande per entrare in contesto: cento documenti possono valere oltre
un milione di token, e l'ottanta per cento serve come riferimento ricercabile, non come materiale di
ragionamento attivo. Invece di caricare tutto, si accede ai documenti per livelli crescenti di
dettaglio, scendendo solo dove serve.

Livello 1, scheletro: solo titolo, gerarchia delle intestazioni e conteggi per sezione, una manciata
di token per documento. Permette di vedere un'intera cartella in poche decine di migliaia di token e
decidere dove guardare.

Livello 2, preview di sezione: per i soli documenti su cui si vuole ragionare, si aggiungono l'incipit
e la chiusura di ogni sezione piu le entita rilevate, qualche centinaio di token per documento.

Livello 3, sezione completa: lettura puntuale di una sola sezione di un solo documento, attivata solo
per rispondere a una domanda precisa.

Operativamente si parte sempre dal Livello 1 sull'intera cartella, si sale al Livello 2 solo sui
documenti pertinenti al task, e al Livello 3 solo su richiesta esplicita. Vale per qualsiasi corpus,
non solo per i `.docx`.

## Deterministico prima del linguistico

In una pipeline che mescola codice e LLM, si spinge il piu possibile il lavoro su codice
deterministico e si riserva l'LLM al solo lavoro che richiede comprensione semantica. Parsing,
estrazione con regex, trasformazioni, calcoli e generazione di file derivati sono deterministici e
vanno in script. L'estrazione semantica di concetti e relazioni e la sintesi narrativa sono
linguistiche e vanno all'LLM.

Tre benefici concreti. Riproducibilita: rilanciando gli script si ottiene lo stesso risultato.
Economia: il lavoro deterministico costa CPU locale, non token. Ispezionabilita: gli stati intermedi
sono file leggibili, tipicamente JSON, che si possono correggere a mano senza rilanciare l'LLM.

Operativamente, quando un passo si puo fare con codice lo si fa con codice e se ne salva l'output come
stato intermedio ispezionabile; si chiama l'LLM solo per il salto semantico, e anche il suo output
torna a essere uno stato su disco, non un risultato volatile in chat.

## Igiene di sessione

Alcune abitudini operative tagliano il consumo senza installare nulla.

Il comando `/compact` va lanciato proattivamente quando il contesto raggiunge il 40-60%, non
aspettando il limite automatico. Puo essere guidato con istruzioni esplicite: `/compact focus on
the database schema decisions and API endpoints we agreed on`. La soglia di compattazione
automatica si anticipa con la variabile `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` (valori da 1 a 100),
utile per evitare che la compattazione scatti a freddo sul contesto gia degradato.

Prima di ogni `/clear` o di chiudere una sessione su un task non ancora concluso, si fa scrivere
a Claude un file `HANDOFF.md` con le decisioni prese, i pattern stabiliti e i file toccati. La
sessione successiva parte da quel file invece che da zero, recuperando il contesto senza
rileggere l'intera conversazione.

La finestra da un milione di token, disponibile su Sonnet 4.6 e Opus 4.7, e utile come
assicurazione per i task lunghi ma non come obiettivo: oltre i 120-150K token utili la qualita
delle risposte tende comunque a degradare per accumulo di rumore nel contesto. Chunk piccoli con
handoff espliciti producono risultati migliori che riempire la finestra grande.

Il principio "un task, una chat" mantiene il contesto sempre fresco: invece di una sessione fiume
che accumula task diversi, si chiude e riapre per ogni unita di lavoro logica, riducendo le
compattazioni multiple e il rischio di deriva del focus.

## Strumenti esterni, a scelta

Quando il risparmio nativo non basta, per esempio in sessioni operative molto lunghe e ricche di
output, si possono valutare strumenti esterni open source, sempre offerti come scelta al gate dei
pacchetti e mai imposti.

`caveman` riduce i token di output facendo rispondere l'agente in modo telegrafico, senza toccare
il ragionamento. E' utile nelle sessioni operative pesanti, ma va tenuto spento quando il progetto
produce documentazione o prosa leggibile, perche ne degraderebbe lo stile. Vive come tool di
sessione, non come stato del progetto. Vedi la voce `caveman` in `templates/PACKAGES.md`.

Per esigenze piu spinte esistono alternative come un server MCP di compressione e caching del
contesto (per esempio `token-optimizer-mcp`). Si adottano solo se il guadagno giustifica la
dipendenza, valutando caso per caso.

## Cosa non si fa

Non si introduce uno strumento di memoria globale che accumula stato fuori dal progetto: la memoria
del sistema vive dentro il progetto, versionata, e l'auto-memory nativa di Claude resta disattivata
(vedi sezione 15 di `PROJECT-SYSTEM.md`).
