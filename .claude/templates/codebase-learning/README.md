# Pacchetto codebase-learning

> Pacchetto opzionale del sistema di progetto. Trasforma un progetto Claude finito o quasi finito di sviluppare in un ambiente di apprendimento guidato della repository stessa: un comando `/learn-repo` che accompagna l'utente fase per fase nella comprensione dello stack, delle astrazioni centrali, dei flussi end-to-end, dei design pattern e degli idiomi dello stack, e un subagent `code-tutor` che esplora il codice al posto della sessione principale e ritorna sempre uno snippet reale con path e riga a sostegno di ogni affermazione. Deriva per intero da `reference/codebase-learning-handoff.md`, un documento di ricerca dell'utente datato luglio 2026 che resta la fonte di verità per ogni scelta di stack MCP e di sequenza didattica riportata qui: in caso di dubbio interpretativo su una fase della skill si consulta prima quel documento. Si offre al gate dei pacchetti (vedi `../PACKAGES.md`) quando lo scopo dichiarato della sessione è *capire* un progetto invece di continuare a svilupparlo; non si propone durante lo sviluppo attivo, dove la comprensione del codice resta compito delle schede tecniche di `.claude/context/` e della skill `sync-context`.

## Distinzione da learning-agent

La distinzione dal pacchetto `learning-agent` è netta e va tenuta presente al gate, perché i due pacchetti rispondono a una domanda diversa nonostante il nome simile. `learning-agent` insegna un topic esterno alla repository, per esempio un linguaggio di programmazione o una lingua straniera, a partire da una knowledge base di file dell'utente e con spaced repetition programmato. `codebase-learning` insegna la repository corrente a chi la sta già aprendo in Claude Code, senza knowledge base esterna e senza ripasso programmato, perché l'oggetto da imparare è il codice stesso, già presente sul disco. I due pacchetti possono coesistere nello stesso progetto senza sovrapporsi.

## Cosa è concreto e cosa resta al gate

Come `learning-agent`, anche questo pacchetto deriva da una ricerca puntuale dell'utente e non da un modulo già rodato su un progetto reale: la stessa onestà dichiarata per quel pacchetto vale qui. Il livello di orchestrazione, cioè la skill `learn-repo` e il subagent `code-tutor`, ha un corpo operativo completo perché il documento di riferimento fissa in modo concreto le cinque fasi e la regola di citazione a riga: è utilizzabile da subito, anche senza alcun server MCP connesso, appoggiandosi a `Grep`, `Glob` e `Read` con la disciplina di lettura a fette. Resta aperta, e va calibrata alla prima attivazione reale, la scelta di quale grafo strutturale collegare per i progetti di dimensione maggiore: il documento di riferimento distingue una via di ingresso a costo zero, `serena` per la navigazione semantica e `repomix` per lo snapshot consolidato, da una via di approfondimento facoltativa che il catalogo copre già con righe separate (`code-context`, `codebase-memory-mcp`, `graphify`), da scegliere in base alla dimensione del repository e non da installare tutte insieme.

## Mappa di istanziazione

```
templates/codebase-learning/agents/code-tutor.md                     ->  <radice>/.claude/agents/code-tutor.md                     (tracciato)
templates/codebase-learning/skills/learn-repo/                        ->  <radice>/.claude/skills/learn-repo/                        (tracciato)
templates/codebase-learning/commands/learn-repo.md                    ->  <radice>/.claude/commands/learn-repo.md                    (tracciato)
templates/codebase-learning/reference/codebase-learning-handoff.md    ->  <radice>/.claude/context/codebase-learning-reference.md    (tracciato)
(creato dalla prima sessione persistita)                               <radice>/docs/learning/                                       (tracciato, opzionale)
```

Il documento di riferimento si instanzia dentro `.claude/context/` invece di restare solo nella cartella del template, così che la skill e il subagent lo raggiungano con lo stesso percorso relativo indipendentemente da dove il pacchetto viene attivato, e così che chi clona il repository lo trovi accanto alle altre schede tecniche di progetto. La cartella `docs/learning/` non si crea vuota all'attivazione: nasce solo se, a valle di una sessione guidata, si sceglie di persistere il materiale prodotto invece di lasciarlo solo nella conversazione.

## MCP server e tool esterni collegati

Il pacchetto non installa da solo alcun server MCP: la scelta resta al gate, secondo lo stesso modello a tre livelli del documento di riferimento. Il livello *struttura* risponde a "chi chiama cosa, dove è definito X": il catalogo offre `serena`, un language server[^1] che naviga a livello di simbolo invece che di testo su venti o più linguaggi, come opzione consigliata per maturità e gratuità, accanto alle righe già esistenti `code-context` (tree-sitter, più leggero, già nel bundle di base) e `codebase-memory-mcp` (call chain e impact analysis su repository grandi); nessuno dei tre è un prerequisito degli altri e si sceglie uno alla volta secondo la dimensione del progetto. Il livello *comprensione* risponde a "cosa fa questo repository, come funziona il flusso X": il catalogo offre `repomix` per lo snapshot consolidato iniziale e `deepwiki-skill` per generare documentazione persistente con citazioni a riga, accanto alla riga già esistente `graphify` per la vista a grafo dell'intero progetto. Il livello *riferimento* risponde a "come si usa questa versione di questo framework": la riga già esistente `context7` copre le docs pubbliche dello stack, mai il codice del progetto. Una quarta opzione, `deepwiki-mcp`, risponde a domande in linguaggio naturale su repository GitHub già pubbliche e indicizzate: si offre solo quando il repository del progetto è effettivamente pubblica, mai per codice proprietario, per lo stesso motivo per cui `context7` resta confinato alle docs pubbliche.

Il documento di riferimento cita altre alternative locali equivalenti a `serena` e `codebase-memory-mcp` per il livello struttura, in particolare CodeGraph, CodeGraphContext, GitNexus e RepoMapper: restano annotate nel documento invece che come righe di catalogo separate, perché coprono lo stesso bisogno già coperto da una riga esistente, e il limite di tre o quattro MCP nuovi per sessione fissato in `../PACKAGES.md` sconsiglia di proporli tutti insieme. Si valutano puntualmente, consultando il documento di riferimento, solo se `serena` o `codebase-memory-mcp` risultano insufficienti su un progetto specifico.

## Come si usa, passo per passo

1. Attivazione al gate: crea l'anatomia sopra, con il documento di riferimento già popolato in `.claude/context/codebase-learning-reference.md`.
2. Se il progetto è grande o multi-linguaggio, si sceglie con l'utente se collegare `serena` e/o `repomix` per l'indicizzazione, rispettando il limite di MCP nuovi per sessione; su un progetto piccolo i tool nativi bastano e si può partire subito con `/learn-repo`.
3. `/learn-repo` avvia la sessione guidata: la skill `learn-repo` delega ogni fase al subagent `code-tutor`, che esplora con i tool connessi e ritorna solo il materiale della fase corrente, mai un file intero.
4. Dopo ogni fase la skill si ferma e propone due domande di verifica, secondo la regola del documento di riferimento: non passa alla fase successiva senza che l'utente abbia risposto o abbia chiesto esplicitamente di procedere.
5. Se si vuole persistere il materiale, si invoca `deepwiki-skill` (se attivata) per generare `docs/learning/*.md` con citazioni a riga, poi si rifiniscono gli snippet mancanti con `code-tutor`.

## Sicurezza e privacy

Per codice proprietario il pacchetto resta per default sui tool locali (`serena`, `repomix`, `code-context`, `codebase-memory-mcp`, `graphify`, `deepwiki-skill`): nessuno di questi invia codice a un servizio esterno. `deepwiki-mcp` e `context7` fanno entrambi chiamate esterne e restano confinati rispettivamente a repository effettivamente pubbliche e a docs pubbliche dello stack, mai al codice del progetto. Come per ogni server MCP del catalogo, la versione va pinnata all'attivazione invece di lasciare un tag mobile come `@latest`.

## Verificato dal vivo (pilota 2026-07-02/03)

Un primo tentativo di esercitare la Fase 1 di `/learn-repo` tramite una corsa headless di `automation-starter` in `-PermissionMode plan` non ha completato: il modello ha correttamente deciso di delegare al subagent `code-tutor` come da procedura, ma delegare a un subagent e' un'azione multi-passo che in modalita' piano richiede di uscire dal piano con `ExitPlanMode`, tool non abilitato in un contesto headless. La corsa si e' fermata con un piano scritto su disco, senza mai invocare `code-tutor`. Non e' un difetto di questo pacchetto: e' un limite generale di `-PermissionMode plan` in `claude -p`, documentato nel README di `automation-starter`.

Ripetuto con `-PermissionMode acceptEdits`, il test e' riuscito per intero: il subagent `code-tutor` e' stato effettivamente invocato tramite il tool `Agent` (non simulato in-process), ha esplorato il repository con 9 chiamate a tool e restituito la Fase 1 (panoramica dello stack) con citazioni reali `file:riga` per ogni affermazione (stack, moduli, entry point, paradigma), le due domande di autovalutazione previste, e si e' fermato correttamente senza proseguire alla fase successiva ne' modificare alcun file, come da vincolo della skill. Il subagent ha girato su `claude-sonnet-4-6`, un modello diverso da quello della sessione orchestrante, confermando che il frontmatter del subagent viene rispettato anche in esecuzione headless.

## Recap dei comandi

- Avviare o riprendere la sessione guidata: `/learn-repo`, opzionalmente con un modulo, un servizio o una cartella come argomento per restringere il focus.
- Consultare l'architettura completa e le raccomandazioni originali: apri `.claude/context/codebase-learning-reference.md`.
- Versionare il materiale prodotto: `git add docs/learning/ .claude/agents/code-tutor.md .claude/skills/learn-repo/ .claude/commands/learn-repo.md .claude/context/codebase-learning-reference.md` seguito da commit (operazione manuale dell'utente).

## Riferimenti e crediti

Il documento di riferimento cita l'intero ecosistema di strumenti alla base delle scelte di questo pacchetto; i crediti completi, con licenza e repository, sono nella sezione "Riferimenti e strumenti open source" del `README.md` di radice del template e nelle righe di catalogo dedicate in `../PACKAGES.md`. In sintesi: `oraios/serena` per il grafo semantico via language server, Repomix (repomix.com) per lo snapshot consolidato, `natsu1211/deepwiki-skill` per la documentazione con citazioni a riga, l'endpoint ufficiale DeepWiki per il Q&A su repository pubbliche. Le righe di catalogo già esistenti `code-context`, `codebase-memory-mcp`, `graphify` e `context7` restano i crediti di riferimento per le capacità che questo pacchetto riusa invece di duplicare.

[^1]: *LSP*, Language Server Protocol - protocollo con cui un editor o un agente comunica con un language server (per esempio `gopls` per Go o `clangd` per C/C++) per ottenere definizioni, riferimenti e diagnosi a livello di simbolo invece che di testo; Serena riusa gli stessi language server di VS Code.
