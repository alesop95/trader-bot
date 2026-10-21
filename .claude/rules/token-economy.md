# Token economy

> Regola modulare. Consolida le pratiche di risparmio di contesto del sistema e indica quando valutare uno strumento esterno di ottimizzazione dei token. Si applica sempre, a ogni sessione. I casi osservati che hanno prodotto queste prescrizioni, con le misure e le date, stanno in `.claude/norme/token-economy.md`: quel file non si carica all'avvio di una sessione e non serve per applicare la regola, serve a chi deve estenderla o rimetterla in discussione.

## Principi nativi

Il sistema è già progettato per non sprecare contesto, e queste pratiche valgono sempre.

Densità sopra completezza: una sintesi densa vale più di un estratto lungo. Si scrive e si legge per segnale, non per volume.

On-demand: le skill, i capitoli di una skill-libro, le schede di `context/` e le pagine della wiki si caricano solo quando servono al task, mai tutte insieme. Il `CLAUDE.md` indicizza i satelliti, non li incorpora.

Niente riletture integrali: il motore di riconciliazione confronta i commit e legge solo le schede pertinenti; i documenti voluminosi come i `.docx` si estraggono a fette, mai letti per intero, e si tiene un mirror `.md` per i diff invece di rileggere il binario.

Si legge un file quando serve davvero, e solo la porzione necessaria, non l'intero file se non occorre.

## Il costo si sceglie: parallelismo, modello, delega, server

Quattro leve decidono quanto costa un lavoro, e tre si scelgono prima di cominciare. Il parallelismo non riduce i token: consuma gli stessi token in metà tempo, quindi avvicina il limite invece di allontanarlo, e si usa quando serve il risultato prima, mai quando si teme di esaurire la finestra. Il modello e il livello di ragionamento valgono un fattore nove su un lavoro meccanico, a parità di mandato, e il costo per elemento cresce con la dimensione del lotto, da cui segue che molte sessioni brevi costano meno di una lunga e che un lotto unico su tutto il corpus è il modo più caro di farlo. L'ordine in cui conviene intervenire è sempre lo stesso: togliere elementi, perché la parte deterministica di una mappatura non deve vedere un modello; rendere il lavoro riprendibile, perché un lavoro che riparte da capo non si conclude mai; instradare su serbatoi indipendenti; e solo alla fine parallelizzare.

Un compito che consuma molti token ma non richiede giudizio fine va al modello più economico che lo sa fare, e il modello più capace si riserva alla parte che ne ha bisogno: la scelta si fa per compito e non per sessione, e si misura su un lotto piccolo prima di estenderla. La conversazione principale non è il posto dove risparmiare, perché ogni suo passo si appoggia al precedente e un errore intermedio costa tutto ciò che vi si appoggia dopo. È meccanico il lavoro che si giudica su una regola e non su un contesto, cioè cercare dove sta qualcosa in un repository, leggere molti file per estrarne lo stesso dato, mappare o classificare molti elementi su etichette chiuse, convertire, inventariare, contare; non si delegano mai la revisione del codice, l'audit di sicurezza, la progettazione, la scelta fra due architetture e ogni passo su cui si appoggia il passo successivo. Un instradamento senza delega non instrada niente, quindi l'autorizzazione a delegare si scrive dove l'agente la legge da sé a ogni sessione, cioè in un file di istruzioni; e a fine giro l'agente dichiara quanti subagent sono partiti, perché un conto implicito non si corregge.

Un server MCP dichiara i propri strumenti all'apertura della sessione, e quella dichiarazione entra in contesto prima del primo messaggio sia che gli strumenti vengano usati sia che restino fermi; un comando di shell non dichiara niente e costa la riga che lo lancia più il riepilogo che risponde. Il server conviene al lavoro che torna indietro, cioè guardare, provare e correggere tenendo lo stato aperto; il comando conviene al lavoro che va avanti. Ne segue che un lavoro a passo unico non passa mai da un server, che dove il server offre un modo ridotto lo si usa, e che un server si collega per il lavoro che lo richiede e si toglie quando quel lavoro è finito, tenendo le voci spente in `disabledMcpjsonServers` invece di cancellarle. Non più di sei server restano connessi in tutto, contati sul totale e non per settore.

Vale infine una cautela sui flussi di verifica adversariale a più voti, come `deep-research`, che con qualche decina di affermazioni esauriscono il limite di sessione in pochi secondi: quando succede non si rilancia lo stesso flusso identico, si restringe la domanda a un angolo di ricerca più stretto, si riprende dalla cache del flusso, oppure si scende a una verifica mirata delle sole fonti primarie già trovate.

## Disclosure progressiva su documenti voluminosi

Un corpus documentale è troppo grande per entrare in contesto: cento documenti possono valere oltre un milione di token, e l'ottanta per cento serve come riferimento ricercabile, non come materiale di ragionamento attivo. Invece di caricare tutto, si accede ai documenti per livelli crescenti di dettaglio, scendendo solo dove serve.

Livello 1, scheletro: solo titolo, gerarchia delle intestazioni e conteggi per sezione, una manciata di token per documento. Permette di vedere un'intera cartella in poche decine di migliaia di token e decidere dove guardare.

Livello 2, preview di sezione: per i soli documenti su cui si vuole ragionare, si aggiungono l'incipit e la chiusura di ogni sezione più le entità rilevate, qualche centinaio di token per documento.

Livello 3, sezione completa: lettura puntuale di una sola sezione di un solo documento, attivata solo per rispondere a una domanda precisa.

Operativamente si parte sempre dal Livello 1 sull'intera cartella, si sale al Livello 2 solo sui documenti pertinenti al task, e al Livello 3 solo su richiesta esplicita. Vale per qualsiasi corpus, non solo per i `.docx`.

Il pacchetto opzionale `doc-ingest` ne è l'implementazione di riferimento: converte `.pdf`, `.docx`, `.pptx`, `.xlsx` e `.html` in una cache Markdown con manifest a content-hash e rigenera a ogni corsa lo scheletro di Livello 1 in `_INDEX.md`; i Livelli 2 e 3 restano disciplina di lettura.

Una variante dello stesso principio sposta il corpus non su una cache locale ma su un motore di recupero esterno ancorato alle fonti. Il pacchetto opzionale `notebooklm-bridge` (vedi `templates/notebooklm-bridge/`) tiene il corpus dentro NotebookLM, nel piano gratuito accessibile solo da browser, e in conversazione fa entrare solo una sintesi densa e citata invece del testo grezzo: è un Livello 1 prodotto da un motore che risponde anche a domande mirate senza mai versare le fonti in contesto. Il risparmio è lo stesso della disclosure progressiva, con in più l'ancoraggio alle fonti che riduce le allucinazioni; il costo è che l'accesso resta manuale nel browser, mai un'API a pagamento. Ne discende un dovere in ogni progetto: quando un'analisi deve ragionare su più di una ventina di documenti dell'utente, o oltre la soglia del degrado, con risposte citate, l'agente chiede all'utente se convenga passare per un momento a NotebookLM, e dove il pacchetto manca lo propone con `cerca-pacchetto`. Claude non lo pilota: l'utente lo usa in una finestra privata, senza login né sessioni salvati, e ciò che ne torna resta nel progetto.

## Deterministico prima del linguistico

In una pipeline che mescola codice e LLM, si spinge il più possibile il lavoro su codice deterministico e si riserva l'LLM al solo lavoro che richiede comprensione semantica. Parsing, estrazione con regex, trasformazioni, calcoli e generazione di file derivati sono deterministici e vanno in script. L'estrazione semantica di concetti e relazioni e la sintesi narrativa sono linguistiche e vanno all'LLM.

Tre benefici concreti. Riproducibilità: rilanciando gli script si ottiene lo stesso risultato. Economia: il lavoro deterministico costa CPU locale, non token. Ispezionabilità: gli stati intermedi sono file leggibili, tipicamente JSON, che si possono correggere a mano senza rilanciare l'LLM.

Operativamente, quando un passo si può fare con codice lo si fa con codice e se ne salva l'output come stato intermedio ispezionabile; si chiama l'LLM solo per il salto semantico, e anche il suo output torna a essere uno stato su disco, non un risultato volatile in chat.

## Igiene di sessione

Alcune abitudini operative tagliano il consumo senza installare nulla.

`/compact` si lancia presto, fra il 40 e il 60% del contesto, con istruzioni su che cosa tenere; la soglia automatica si anticipa con `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE`, così che non scatti su un contesto già degradato.

Prima di un `/clear` o della chiusura su un task aperto si scrive un `HANDOFF.md` con decisioni, pattern e file toccati, da cui la sessione successiva riparte.

La finestra da un milione di token è un'assicurazione per i task lunghi, non un obiettivo: oltre i 120-150 mila token utili la qualità tende a degradare, e chunk piccoli con handoff espliciti rendono di più.

Il principio "un task, una chat" mantiene il contesto sempre fresco: invece di una sessione fiume che accumula task diversi, si chiude e riapre per ogni unita di lavoro logica, riducendo le compattazioni multiple e il rischio di deriva del focus.

## Strumenti esterni, a scelta

Quando il risparmio nativo non basta, gli strumenti esterni, come `caveman` per l'output o un server MCP di compressione del contesto, si offrono solo al gate dei pacchetti e non si impongono; `caveman` resta spento dove il progetto produce prosa da leggere. Il ragionamento esteso sta nella norma di questa regola.

## Cosa non si fa

Non si introduce uno strumento di memoria globale che accumula stato fuori dal progetto: la memoria del sistema vive dentro il progetto, versionata, e l'auto-memory nativa di Claude resta disattivata (vedi sezione 15 di `PROJECT-SYSTEM.md`).
