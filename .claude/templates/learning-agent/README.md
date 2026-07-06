# Pacchetto learning-agent

> Pacchetto opzionale del sistema di progetto. Trasforma un progetto Claude in uno o più agenti di apprendimento guidato che insegnano un topic specifico, per esempio un linguaggio di programmazione o una lingua straniera, a partire da una knowledge base di file dell'utente (`.docx`, `.pdf`, libri) e da una memoria di ripasso a intervalli. Deriva per intero da `reference/learning-agent-handoff.md`, un documento di ricerca dell'utente datato luglio 2026 che resta la fonte di verità per ogni scelta pedagogica riportata qui: in caso di dubbio interpretativo su una skill si consulta prima quel documento. Si offre al gate dei pacchetti (vedi `../PACKAGES.md`) ai progetti il cui scopo dichiarato è l'apprendimento personale di un topic, non lo sviluppo di un prodotto; non si propone se il progetto ha già un proprio sistema di tutoraggio o di spaced repetition equivalente.

## Architettura a tre livelli

Il documento di riferimento distingue tre livelli disaccoppiati, pensati per essere sostituiti indipendentemente l'uno dall'altro. Il primo è la knowledge base, cioè l'ingestione e il retrieval dei file dell'utente, esposta come server MCP locale interrogabile. Il secondo è il motore di memoria dell'apprendimento, cioè lo spaced repetition che traccia cosa è stato imparato e cosa è dovuto per il ripasso, tipicamente Anki via MCP. Il terzo è il livello di orchestrazione, cioè il tutor che pianifica la roadmap, spiega, interroga e adatta stile e tecniche: vive dentro `.claude/` come agenti, skill e comandi. Questo pacchetto scaffolda soltanto il terzo livello. Il primo e il secondo restano server MCP esterni, non installati automaticamente: si scelgono al gate come righe separate del catalogo (`knowledge-mcp`, `anki-mcp` in `../PACKAGES.md`), esattamente come `academic-researcher` lascia a righe di catalogo separate i propri MCP di ricerca. Il livello di orchestrazione è comunque utilizzabile da solo, senza i primi due, appoggiandosi a file locali letti direttamente invece che a un retrieval strutturato, e senza spaced repetition automatizzato se Anki non è connesso.

## Cosa è concreto e cosa resta da calibrare

L'intero pacchetto nasce da una ricerca puntuale dell'utente, non da un modulo già rodato su un progetto reale come `academic-researcher`: questa differenza va dichiarata con la stessa onestà con cui quel pacchetto dichiara le proprie parti stub. Il livello di orchestrazione, cioè i tre agenti e le tre skill, ha un corpo operativo completo perché il documento di riferimento fissa in modo concreto la pedagogia per dominio (linguaggio di programmazione, lingua straniera, materia concettuale) e gli adattamenti per profilo cognitivo (ADHD, spettro autistico, dislessia): sono utilizzabili da subito. Restano aperte, e vanno calibrate alla prima attivazione reale, tre cose che nessun documento di ricerca può fissare in astratto. La scelta e l'installazione dei server MCP di livello 1 e 2, che dipendono dai file e dallo strumento di spaced repetition che l'utente ha già o vuole adottare. La categoria pedagogica di un topic nuovo che non rientra chiaramente in nessuna delle tre descritte nel documento di riferimento, che va discussa con l'utente invece che dedotta. La cadenza reale di ripasso e la dimensione dei chunk, che il documento fissa come principio (per esempio dieci esposizioni distribuite meglio di cento in un giorno) ma che nessuna skill può tradurre in un numero esatto senza sapere quanto tempo l'utente dedica davvero allo studio.

## Mappa di istanziazione

```
templates/learning-agent/agents/tutor.md                    ->  <radice>/.claude/agents/tutor.md                    (tracciato)
templates/learning-agent/agents/kb-retriever.md              ->  <radice>/.claude/agents/kb-retriever.md              (tracciato)
templates/learning-agent/agents/examiner.md                  ->  <radice>/.claude/agents/examiner.md                  (tracciato)
templates/learning-agent/skills/build-roadmap/                ->  <radice>/.claude/skills/build-roadmap/                (tracciato)
templates/learning-agent/skills/learn-topic/                  ->  <radice>/.claude/skills/learn-topic/                  (tracciato)
templates/learning-agent/skills/review-session/                ->  <radice>/.claude/skills/review-session/                (tracciato)
templates/learning-agent/commands/profile.md                  ->  <radice>/.claude/commands/profile.md                  (tracciato)
templates/learning-agent/commands/learn.md                    ->  <radice>/.claude/commands/learn.md                    (tracciato)
templates/learning-agent/commands/review.md                   ->  <radice>/.claude/commands/review.md                   (tracciato)
templates/learning-agent/LEARNER_PROFILE.md                    ->  <radice>/LEARNER_PROFILE.md                    (tracciato, scaffold vuoto, popolato da /profile)
templates/learning-agent/reference/learning-agent-handoff.md   ->  <radice>/.claude/context/learning-agent-reference.md   (tracciato)
```

Il documento di riferimento si instanzia dentro `.claude/context/` invece di restare solo nella cartella del template, così che le skill lo raggiungano con lo stesso percorso relativo indipendentemente da dove il pacchetto viene attivato, e così che chi clona il repository lo trovi accanto alle altre schede tecniche di progetto. `LEARNER_PROFILE.md` resta invece in radice, accanto a `CLAUDE.md`, perché è lo stato del learner che si vuole visibile subito, non un documento di consultazione.

## MCP server e tool esterni collegati

Il pacchetto non installa da solo alcun MCP server: la scelta resta al gate, con `build-roadmap` (invocata da `/profile`) che registra in `LEARNER_PROFILE.md` se un knowledge-base MCP e un Anki MCP sono connessi o assenti, e i tre agenti che si comportano di conseguenza. Il catalogo `../PACKAGES.md` elenca separatamente le voci concrete raccomandate dal documento di riferimento: per la knowledge base, `knowledge-mcp` (RAG ibrido vettoriale più grafo, basato su LightRAG, il candidato più forte per topic strutturati come un linguaggio di programmazione) con l'alternativa 100% locale via Ollama; per lo spaced repetition, `anki-mcp` (proxy locale verso AnkiConnect, nessuna telemetria) con l'alternativa minimale che espone solo il loop di ripasso. Nessuno dei due è un prerequisito per attivare `learning-agent`: in loro assenza, `kb-retriever` legge direttamente i file indicati dall'utente e `tutor` traccia i progressi solo dentro `LEARNER_PROFILE.md`, senza spaced repetition automatizzato.

## Recap dei comandi

- Creare o aggiornare il profilo del learner: `/profile`, che invoca `build-roadmap` la prima volta e da lì in avanti aggiorna solo i campi cambiati.
- Erogare la prossima unità di apprendimento: `/learn <topic>`, che se manca una roadmap la costruisce, poi delega il retrieval a `kb-retriever` e la verifica finale a `examiner`.
- Aprire una sessione di ripasso guidata sui "due" di Anki, o su quanto tracciato in `LEARNER_PROFILE.md` se Anki non è connesso: `/review`.
- Versionare l'avanzamento: `git add LEARNER_PROFILE.md .claude/agents/ .claude/skills/build-roadmap/ .claude/skills/learn-topic/ .claude/skills/review-session/ .claude/commands/profile.md .claude/commands/learn.md .claude/commands/review.md .claude/context/learning-agent-reference.md` seguito da commit (operazione manuale dell'utente).

## Riferimenti e crediti

Il documento di riferimento cita l'intero ecosistema di strumenti alla base delle scelte architetturali del pacchetto; i crediti completi, con licenza e repository, sono nella sezione "Riferimenti e strumenti open source" del `README.md` di radice del template e nelle righe di catalogo dedicate in `../PACKAGES.md`. In sintesi: `knowledge-mcp` di olafgeibig per la knowledge base RAG ibrida basata su LightRAG, `Local Knowledge RAG MCP` di patakuti come alternativa 100% locale via Ollama, `mcp-local-rag` di nkapila6 come fallback di ricerca web locale, `anki-mcp-server` del progetto ankimcp per lo spaced repetition via AnkiConnect, `mcp-ankiconnect` di samefarrar come alternativa minimale. L'impianto pedagogico cita Roediger e Karpicke (2006) per l'effetto del testing sull'apprendimento e il curriculum a dipendenze strette di `cc-self-train` per la sequenza dei moduli di programmazione; gli adattamenti per profili neurodivergenti sono compilati da fonti divulgative citate nel documento di riferimento (additudemag.com, sachscenter.com, neurolaunch.com, clickvieweducation.com), da trattare come adattamenti didattici dichiarati e non come indicazioni cliniche.
