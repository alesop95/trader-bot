# Sistema di progetto portabile per Claude Code

> File unico e portabile. Descrive il sistema di contesto, documentazione e version control da installare in un progetto, e funge da runbook per il comando di inizializzazione. È distillato da una implementazione reale di riferimento ma non vi è accoppiato: ogni nome di progetto, stack o integrazione citato è esemplificativo. Per riusarlo altrove si copia questo file nella radice del nuovo progetto e si esegue la sezione *Comando di inizializzazione*.

Questo documento è scritto nello stile della documentazione tecnica adottato dal progetto: prosa discorsiva, niente elenchi puntati, niente emoji, acronimi spiegati in note a piè di pagina numerate, termini chiave in corsivo, frammenti di codice e configurazione in blocchi monospazio, alberi del filesystem mantenuti come blocchi preformattati.

---

## 1. Scopo e filosofia

L'obiettivo è disporre di una base di conoscenza che si aggiorna a ogni avanzamento dello sviluppo, tale che lo stato del progetto sia interamente recuperabile in qualsiasi momento e da chiunque cloni il repository. La sessione di chat è effimera e va persa alla chiusura; ciò che persiste è il contesto strutturale su disco, riletto automaticamente all'apertura della sessione successiva nella stessa directory. Il sistema fa in modo che ogni passo di codice, e anche ogni intervento manuale, lasci una traccia versionata e riconciliata, senza che questo costi una rilettura integrale dei documenti ogni volta.

La cartella `.claude/` è il centro di controllo del progetto, ma va tenuta all'essenziale. La maggior parte delle attività quotidiane si gestisce con regole modulari e comandi diretti, senza generare ulteriore struttura. Una *skill*[^1] dedicata si introduce solo quando serve governare una procedura complessa o ripetibile, come un ciclo di deploy o un processo di sicurezza. Per le attività incrementali bastano i comandi e le regole locali. Quando si parte da zero su uno stack noto, conviene partire da skill già predisposte come pacchetti di conoscenza per quel framework, invece di riscrivere tutto. Una skill e un server MCP non sono la stessa cosa: la skill è un workflow locale, fatto di file dentro il progetto, riusabile e versionato col repository; un server MCP è un servizio in rete, tipicamente condiviso tra più persone e agenti con permessi e autenticazione, che espone tool, risorse e prompt. Si sceglie la skill per i flussi di lavoro propri e locali, l'MCP per integrare servizi esterni condivisi.

Ogni nuova feature segue lo stesso ciclo: si descrivono gli obiettivi in modo chiaro, si produce un piano, si analizzano pro e contro con i relativi metodi di mitigazione, si risolvono le incertezze con domande mirate prima di scrivere codice, e solo allora l'agente implementa. A feature completata si genera un documento markdown permanente che fissa la logica implementata, le scelte architetturali e il contesto operativo, così da costituire memoria tecnica per il futuro. Questo ciclo è la ragione per cui il sistema documentale e il sistema di riconciliazione descritti sotto esistono.

---

## 2. Anatomia canonica della cartella `.claude`

Claude Code, all'apertura di una sessione in una directory di progetto, rilegge automaticamente alcuni file. Sono letti sempre `CLAUDE.md` nella radice, come istruzioni di progetto condivise, `CLAUDE.local.md`, come override personali ignorati da git, e i file di memoria sotto `.claude/memory/` come contesto aggiuntivo. Codex legge invece `AGENTS.md` come istruzione persistente di repository e scopre le skill di progetto sotto `.agents/skills/`. Per non mantenere due sistemi divergenti, `CLAUDE.md` e `.claude/skills/` restano le fonti canoniche: `AGENTS.md` è un ponte breve verso il primo, mentre `.agents/skills/` contiene wrapper generati che espongono nome, descrizione e policy e rimandano al `SKILL.md` canonico. Ogni file `.md` sotto `.claude/rules/` viene letto anch'esso sempre, ricorsivamente e per intero, con la stessa priorità del `CLAUDE.md` di progetto, salvo che porti un frontmatter `paths:`; la sezione 24 dice che cosa questo comporta e quale budget ne discende. Vengono invece caricati secondo necessità `.claude/skills/`, `.claude/agents/`, i comandi in `.claude/commands/`, le configurazioni in `.claude/settings.json` e `settings.local.json`, ed eventualmente `.mcp.json` per un server MCP[^2]. L'auto-discovery di alcune sottocartelle non è garantito in ogni contesto, quindi nel `CLAUDE.md` principale conviene includere riferimenti espliciti ai file satellite, così che vengano caricati comunque. Il `CLAUDE.md` indicizza soltanto i satelliti tracciati e non punta mai a file sotto `_notes/` o ad altro materiale locale o ignorato; quando un file referenziato diventa locale, o viene rimosso o rinominato, il suo puntatore va tolto dal `CLAUDE.md`, così che l'indice resti pulito e non rimandi a percorsi inesistenti.

La struttura di riferimento, da adottare nella forma minima e da estendere solo quando la complessità lo richiede, è la seguente.

```
your-project/
├── README.md                  (opzionale) descrizione pubblica del progetto per GitHub, tracciato
├── CLAUDE.md                  istruzioni di team, versionato; indicizza i satelliti
├── AGENTS.md                  ponte Codex verso le istruzioni canoniche, versionato
├── CLAUDE.local.md            override personali, ignorato da git
├── .agents/                   superficie nativa di Codex, versionata
│   └── skills/                wrapper generati verso le skill canoniche
├── .mcp.json                  (opzionale) configurazione di un server MCP
├── _notes/                    livello privato e verboso, ignorato da git
│   ├── DIARIO.md              log cronologico personale degli interventi
│   ├── RESOCONTO.md           sintesi narrativa estesa
│   ├── TEST-CHECKLIST.md      checklist operativa locale di test manuali e non
│   └── .tmp-doc-*/            estratti temporanei di documenti voluminosi, scratch
└── .claude/                   centro di controllo, versionato
    ├── settings.json          permessi e configurazione condivisi, versionato
    ├── settings.local.json    permessi personali, ignorato da git
    ├── commands/              slash command custom (es. review.md → /project:review)
    ├── rules/                 istruzioni modulari (code-style, testing, api, git)
    ├── skills/                workflow richiamabili; uno per cartella, con SKILL.md
    ├── agents/                personae di subagent (es. code-reviewer, security-auditor)
    ├── hooks/                 (opzionale) hook di automazione
    ├── plugins/               (opzionale) plugin
    ├── memory/                meta-stato versionato, letto sempre
    │   ├── index.md           snapshot e indice di sincronizzazione (da leggere per primo)
    │   ├── progress.md        work-log append-only di passi e riconciliazioni
    │   └── decisions.md       registro delle decisioni architetturali
    └── context/               schede tecniche versionate, con frontmatter di riconciliazione
        ├── STACK.md           stack applicativo, flussi di codice, riferimenti a snippet
        ├── design-and-security.md  paradigmi di design e sicurezza applicativa
        ├── deployment.md      livelli test e produzione, hosting, comandi
        ├── dev-testing.md     test di sviluppo (test runner, rotte mockate, hook)
        ├── current-work.md    feature attiva, definition of done, domande aperte
        ├── roadmap.md         direzione e priorità
        └── diagrams/          mappe .svg e sorgenti .mmd, in corrispondenza con le schede
```

Il `CLAUDE.md` è il meccanismo principale di persistenza condivisa, e può essere aggiornato in prompt successivi nel corso delle sessioni. `AGENTS.md` non ne è una seconda copia: istruisce Codex a leggerlo e a tradurre semanticamente i riferimenti agli strumenti, mantenendo invariati permessi, gate e controlli. Distingue le direttive di team dalle preferenze personali, che vivono in `CLAUDE.local.md`, ignorato da git; lo stesso principio separa `settings.json` da `settings.local.json`. Le sottocartelle `commands`, `rules`, `skills` e `agents` rappresentano livelli distinti di orchestrazione: i comandi espongono endpoint semantici come `/project:review`, le regole definiscono normative interne modulari, le skill incapsulano workflow automatizzati e gli agent definiscono personae operative. Claude e Codex aggiornano i file di memoria e di contesto in automatico a ogni giro di lavoro sostanziale, secondo `rules/chat-non-e-memoria.md`; il controllo umano sta sul versionamento, perché è l'utente a rileggere il diff e a committare.

Il `README.md`, quando presente, è un file opzionale ma comune, tracciato in radice e destinato ai visitatori della repository GitHub. Descrive il progetto nella misura in cui il suo contenuto è pubblicamente condivisibile: stack o hardware, workflow principale, standard tecnici, stato corrente. Non sostituisce il `CLAUDE.md`, che è interno al team e descrive le istruzioni di collaborazione con l'agente: il `README.md` è per chi scopre il progetto per la prima volta, il `CLAUDE.md` è per chi ci lavora. Il template di partenza vive in `templates/README-project.md`. La decisione di crearlo si prende in fase di inizializzazione come gate esplicito, mai assunta. Se il README cresce, il pacchetto opzionale `readme-sync` ne mantiene indice, inventario e link; la prosa si verifica leggendo le fonti, perché un controllo deterministico non può dedurre da solo il significato delle modifiche al progetto.

Va distinta da questo sistema la *auto-memory* nativa di Claude Code, una memoria automatica che l'agente scrive di sua iniziativa in un magazzino nascosto fuori dal progetto, sotto `$CLAUDE_CONFIG_DIR/projects/<slug-del-percorso>/memory/`, dove `<slug-del-percorso>` è il percorso assoluto del progetto reso in forma di slug. Questa memoria non vive nel repository e resta solo sulla macchina, quindi viola il principio di recuperabilità totale e sporca l'ambiente con stato per-progetto che un clone non vedrebbe mai. Il sistema la disattiva deliberatamente con `autoMemoryEnabled: false` nel `settings.json` del progetto, così che l'unica memoria sia quella versionata sotto `.claude/memory/` più il `_notes/RESUME-PROMPT.md` ignorato: tutto ciò che persiste vive dentro la cartella di progetto ed è autosufficiente. Chi preferisce imporre la regola a livello di macchina può impostare lo stesso flag nel `settings.json` utente dell'account, o esportare `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`.

Una precisazione che evita un errore architetturale ricorrente: `.mcp.json` e l'eventuale cartella `mcp/` con l'implementazione dei server vivono nella radice del progetto, allo stesso livello del codice e di `.claude`, non sotto `.claude`. La cartella `.claude` è un namespace riservato al comportamento dell'agente, non è il luogo da cui si dichiarano i tool esterni, e Claude Code effettua la discovery dei server MCP esclusivamente dal `.mcp.json` di radice. La cartella `.claude` va inoltre versionata col repository, perché è configurazione deterministica dell'agente e non materiale locale o effimero.

---

## 3. I due livelli documentali e la mappa ibrida

Il sistema separa due livelli con trattamento git diverso. Il principio che governa la ripartizione è uno solo: un documento è *tracciato* se è conoscenza tecnica che un qualsiasi contributore deve poter recuperare o revisionare da un clone ed è sicuro pubblicarlo; resta in `_notes/` *ignorato* se è narrativa personale, materiale transitorio di lavorazione, oppure contenuto operativamente sensibile. Questo risolve il requisito di recuperabilità totale, perché tutto ciò che serve a ricostruire lo stato finisce nei commit, mentre nel locale resta solo il rumore. Il modello è ibrido per documento, non per cartella: la collocazione di un file si decide applicando il principio, e la mappa risultante è fissata qui sotto.

Sono tracciati, perché costituiscono lo stato recuperabile e revisionabile, il `CLAUDE.md` come indice di progetto, `AGENTS.md` come ponte Codex, i wrapper generati sotto `.agents/skills/`, `context/roadmap.md`, `memory/decisions.md` con le decisioni architetturali, `memory/index.md` come snapshot e procedura di ripresa, `memory/progress.md` come work-log append-only, `context/current-work.md` per la feature attiva, le skill e i comandi sotto `.claude/`, e i diagrammi sotto `context/diagrams/` in corrispondenza uno a uno con le schede. Sono tracciate inoltre le schede tecniche strutturali, che portano il frontmatter di riconciliazione descritto nella sezione 4: `STACK.md` con stack e le alternative deliberatamente escluse per evitare deriva tecnologica, flussi di codice e riferimenti a snippet e ruolo architetturale dei file, `design-and-security.md` con i paradigmi di software design e di sicurezza applicativa, `deployment.md` con i livelli di test e produzione e i relativi comandi, e `dev-testing.md` con i test di sviluppo.

Sono ignorati, in `_notes/`, perché narrativa personale o materiale transitorio, `DIARIO.md` come log cronologico verboso degli interventi, `RESOCONTO.md` come sintesi narrativa estesa, `TEST-CHECKLIST.md` come checklist operativa locale di test manuali e automatici, i documenti grezzi (`.docx`, `.pdf`, e affini) e gli estratti temporanei `.tmp-doc-*` salvo le eccezioni curate dichiarate nel `.gitignore`.

Due scelte si discostano da una collocazione puramente privata e vanno tenute presenti. Lo `STACK.md` è il documento di recupero più importante e va tracciato, non confinato nel locale, perché un collega che clona deve vederlo. Il work-log di ingestione dei documenti voluminosi, con le date di riconciliazione, non va in un file ignorato a parte ma confluisce in `memory/progress.md` tracciato, così che la data di allineamento sopravviva a un clone e non si duplichi il log.

Parentesi opzionale, non parte del ciclo di default: alcuni progetti aggiungono sotto `context/` un terzo tipo di documento, distinto sia dalle schede di stato sia da `decisions.md`, quando chi ci lavora vuole anche imparare rileggendo le proprie decisioni architetturali. È un racconto evolutivo che contrappone, voce dopo voce, "com'era e perché era fragile" a "il salto di qualità e perché è meglio", con deep-dive che entrano nel codice reale. Non si assume mai per default, va deciso esplicitamente come la scelta del `README.md`, e la procedura completa vive nella skill `.claude/skills/studio-didattico/`.

---

## 4. Il motore di riconciliazione

Il problema che il motore risolve è mantenere i documenti sempre allineati al codice senza rileggerli per intero a ogni sessione. La soluzione àncora ogni scheda a un commit e ne misura il *drift*[^3] confrontando quel commit con lo stato attuale del repository. 

Ogni scheda tecnica tracciata porta in testa un blocco YAML[^4] di riconciliazione. La forma è la seguente.

```yaml
---
generated-from-commit: <hash del commit di prima scrittura>
generated-from-branch: <branch su cui è stata scritta>
generated-date: <YYYY-MM-DD di prima scrittura>
covers-paths:
  - src/app/api/**
  - src/lib/response.ts
last-verified-commit: <hash dell'ultima verifica o aggiornamento>
---
```

Il campo `generated-from-commit` registra il commit di prima scrittura e non cambia. Il campo`generated-from-branch` serve a segnalare quando il branch corrente è diverso, caso in cui il confronto può risultare rumoroso. Il campo `generated-date` è la data calendariale di prima scrittura. Il campo `covers-paths` elenca i pattern glob[^5] dei file e delle cartelle che la scheda descrive, ed è ciò che permette di filtrare il confronto. Il campo `last-verified-commit` registra il commit dell'ultima verifica o aggiornamento, e si aggiorna manualmente o tramite la skill di sincronizzazione.

La logica di verifica, incapsulata in una skill, per ciascuna scheda legge `last-verified-commit` e `covers-paths`, esegue il confronto `git diff --name-only <last-verified-commit>..HEAD` ristretto ai `covers-paths`, e classifica la scheda. È *aggiornata* se nessun file coperto è cambiato. È *stale* se almeno un file coperto è cambiato, e in tal caso la skill propone un edit chirurgico della sola sezione impattata, senza rigenerare il documento. È *obsoleta* se i cambiamenti includono rinominazioni o rimozioni di moduli interi, o se la scheda cita simboli o file che non esistono più, caso che richiede una rilettura più approfondita e non un semplice aggiornamento del frontmatter. La skill non esegue mai operazioni di scrittura su git e non rigenera i documenti da zero: si limita a leggere e proporre. Quando lo stato di tutte le schede coincide con `HEAD`, la risposta è un singolo messaggio di allineamento, senza azioni.

Su questa cadenza vale una regola che nasce da un progetto istanziato e che il template adotta, cioè `.claude/rules/chat-non-e-memoria.md`: nessun contenuto sostanziale resta nella sola conversazione, e i file si aggiornano nello stesso giro di lavoro in cui il contenuto nasce, non alla fine della sessione. La ragione non è di ordine ma di sopravvivenza del dato, perché una sessione finisce, una compattazione riscrive e un crash cade a metà di un commit; il presidio che la rende verificabile invece che dichiarata è che alla fine di ogni giro di lavoro l'agente elenchi in una riga i file che ha scritto, cosicché l'assenza di quella riga sia essa stessa il segnale.

A ogni passo significativo di codice, e a ogni intervento manuale rilevante, si aggiornano le schede impattate, si porta `last-verified-commit` al nuovo commit, si aggiorna lo snapshot in `memory/index.md` e si appende una voce a `memory/progress.md` con data, file toccati, motivo e commit di riferimento, in ordine cronologico inverso. Il file `memory/index.md` è quello da leggere per primo a inizio sessione: contiene il branch attivo, il commit di riferimento, la tabella che mappa ogni scheda al suo stato di verifica, e il punto di ripresa, dichiarato come una riga di prossima azione concreta che dice da dove ricominciare. Il file `current-work.md` tiene la feature in corso, con una riga di stato nel frontmatter, le definition of done a spunte, le domande aperte risolte in loco e un marcatore di riconciliazione datato, con l'avvertenza esplicita che la fonte di verità su cosa sia fatto resta `memory/index.md` e il log, non le spunte del diario. 

Il registro `memory/decisions.md` segue la convenzione *ADR-lite*[^9] append-only. Ogni decisione architetturale non ovvia entra come voce numerata, ad esempio `ADR-007`, con data, stato, contesto, decisione presa, motivazione e conseguenze. Una decisione non si cancella e non si riscrive: quando viene superata, si aggiunge una nuova voce che dichiara di superare la precedente e ne cita il numero, così la storia del ragionamento resta leggibile. Le inferenze non ancora confermate si marcano esplicitamente come da verificare, e si promuovono a decisione solo quando una fonte le conferma.

Ogni feature in `current-work.md` si descrive con uno schema fisso, cosa fa, i file da creare, i file da modificare, la checklist di completamento e uno stato esplicito, così che il lavoro pendente sia leggibile senza dover ricostruire il contesto da capo.

---

## 5. Ingestione di documenti voluminosi (`.docx`, `.pdf`, e affini)

Quando arriva un documento di contesto voluminoso, tipicamente un `.docx` o un `.pdf`, la regola è non leggerlo mai per intero, perché brucerebbe contesto inutilmente. La strategia riusabile è estrarne il contenuto su disco una sola volta, in una cartella scratch ignorata da git come`_notes/.tmp-doc-<nome>/`, e poi caricare in lettura solo le porzioni mirate al task corrente, on demand. Quando i documenti da tenere sotto questa disciplina sono molti insieme, non uno alla volta, il pacchetto opzionale `doc-ingest` (vedi `.claude/templates/doc-ingest/`) automatizza l'estrazione dell'intero corpus in una cache condivisa `_notes/.tmp-doc-cache/`, con manifest a content-hash e indice di Livello 1 rigenerati a ogni corsa.

Sui documenti di contesto si trovano spesso marcatori del tipo `[TBC]`[^6], che indicano punti da confermare. Questi marcatori vanno estratti temporaneamente su disco e confrontati con l'elenco di ciò che le schede `.md` già coprono, così da capire cosa manca davvero senza rileggere il documento intero. Se le schede risultano già allineate a quel documento, non serve rileggerle né modificarle: si registra soltanto la data di riconciliazione. La data di riconciliazione si annota sempre, sia quando si è prodotto un aggiornamento sia quando si è solo verificato l'allineamento, e va in `memory/progress.md`, accompagnata dal nome del documento sorgente e dall'esito. Le schede che derivano da un documento sorgente ne citano il percorso nel frontmatter, in un campo `source-doc`, così che il legame resti tracciabile. Questa stessa strategia va annotata nel work-log la prima volta che si applica, perché diventi patrimonio del progetto e non vada ricostruita a ogni ingestione.

Esiste anche la direzione inversa, complementare a questa. Quando serve consegnare un deliverable in formato Word, conviene generarlo dallo stato del repository tramite uno script, integrando nel documento gli snippet dei file chiave e le voci di decisione, invece di mantenerlo a mano. Così il documento Word resta allineato al codice e si rigenera a comando, e il `.docx` prodotto resta ignorato da git come ogni binario derivato.

Quando invece è il documento Word a essere la fonte di verità umana, conviene la direzione inversa, da `.docx` a `.md`: uno script genera un mirror Markdown del Word, versionato accanto a esso, che rende leggibili i diff in git mentre il Word resta il documento che si modifica a mano. E per non rileggere ogni volta un documento sorgente che non è cambiato, si tiene un piccolo manifesto che ne registra l'impronta, ad esempio hash e data di modifica, e si rilegge solo ciò che l'impronta segnala come nuovo o modificato.

---

## 6. Igiene del version control e scansione segreti

Il sistema impone alcune regole di version control. La cartella `_notes/` è ignorata, e va inserita nel `.gitignore` prima di crearla, altrimenti finisce indicizzata. Le operazioni di `git add`, commit e push restano sempre in mano all'utente; l'agente prepara, non committa.

Prima di considerare sano un repository va verificato che non siano rimasti indicizzati file non tracciati per errore, e soprattutto che non siano mai stati committati segreti. La scansione dei segreti deve coprire i file tracciati e l'intera storia dei commit, e cercare almeno chiavi private, stringhe di connessione con credenziali, password SMTP[^7], token di firma e file di service account. Il controllo tipico verifica se un file `.env` o equivalente sia mai entrato nella storia, anche se in seguito rimosso, perché la rimozione dal working tree non lo cancella dalla storia e il contenuto resta recuperabile da chiunque abbia accesso al remoto.

Quando un segreto risulta trapelato nella storia, l'unica azione che neutralizza davvero l'esposizione, indipendentemente dalla storia git, è la rotazione del segreto stesso: cambiare la password, rigenerare la chiave, invalidare il token. La riscrittura della storia con uno strumento dedicato è possibile ma confligge con la regola di non riscrivere la storia di branch condivisi e impone un force-push coordinato di tutto il team, quindi va trattata come decisione di team, secondaria rispetto alla rotazione, mai eseguita unilateralmente su `staging` o sul branch stabile.

Distinto dalla scansione segreti, ma parte della stessa igiene, c'è il problema dell'identità con cui si firmano i commit. Su una macchina che ospita più identità, tipicamente una di lavoro e una personale, il rischio e committare un progetto con l'email sbagliata. La regola del sistema e impostare sempre l'identità a livello locale di repository, con la coppia `user.name` e `user.email` e l'alias SSH corretto, e abilitare a livello globale `user.useConfigOnly` perché git rifiuti il commit dove l'identità locale non è stata impostata. La procedura completa, con i profili disponibili, il bootstrap del remoto via alias SSH e il caso del repository remoto già inizializzato con README, vive in una regola dedicata, `.claude/rules/git-identity-and-repo.md`. Anche qui commit e push restano sempre manuali dell'utente.

---

## 7. Disciplina dei diagrammi

I flussi applicativi e i pattern architetturali vanno rappresentati con mappe versionate sotto`context/diagrams/`, in formato `.svg` per la versione resa e con il sorgente accanto quando il diagramma è generato da testo, ad esempio in `.mmd`[^8]. Ogni diagramma è registrato in una tabella dentro la scheda che lo riferisce, e il vincolo non negoziabile è la corrispondenza uno a uno: ogni componente disegnato deve esistere nella mappa testuale registrata e viceversa, così che il diagramma non diverga mai dal codice descritto. Quando un flusso cambia, il diagramma e la scheda si aggiornano insieme, nello stesso passo che bumpa `last-verified-commit`.

---

## 8. Stile della documentazione tecnica

La documentazione si rivolge a un lettore tecnico esperto e va scritta come ci si rivolgerebbe a un responsabile tecnico: diretta ed esaustiva, senza ridondanza. L'impianto è discorsivo: i concetti vengono prima inquadrati architetturalmente, poi approfonditi con estratti di codice annotati, infine collegati ai flussi attraverso paragrafi di raccordo. Non si usano elenchi puntati né emoji né grassetto nella prosa. Gli acronimi si spiegano in note a piè di pagina numerate, per non interrompere il discorso con parentesi inline. I termini chiave densi si marcano in corsivo, le keyword di codice nei blocchi sintattici in grassetto, e i frammenti di codice e configurazione stanno in blocchi monospazio. Gli alberi del filesystem si mantengono come blocchi preformattati con indentazione. Non si usano i trattini lunghi; sono ammessi solo i trattini brevi. Non si presenta mai come fatto un contenuto inferito o non verificato: ciò che non è verificabile va etichettato come tale, e ciò che non si conosce va dichiarato invece di essere riempito per ipotesi. Si preferisce spiegare una cosa una volta sola, in modo descrittivo, senza dare per scontato nemmeno il semplice.

Questo stesso stile conviene codificarlo in un file di regola, `.claude/rules/interaction-style.md`, che essendo lì viene caricato a ogni sessione e diventa vincolante invece di essere affidato alla memoria; è uno dei casi in cui il costo permanente di contesto è giustificato, perché lo stile vale per ogni risposta e per ogni file scritto. Sullo stesso principio, le pratiche di risparmio di contesto descritte in più punti di questo documento sono consolidate nella regola `.claude/rules/token-economy.md`, che indica anche quando valutare uno strumento esterno di ottimizzazione dei token.

---

## 9. Workflow di feature

Una feature non parte dal codice. Parte da una descrizione chiara degli obiettivi, seguita da un piano, da un'analisi dei pro e dei contro con i metodi di mitigazione, e dalla risoluzione delle incertezze tramite domande mirate poste prima dell'implementazione, così da arrivare all'esecuzione con un piano rifinito. Questo ciclo si riassume in cinque momenti ripetibili e indipendenti dalla sessione: pianificare, eseguire, documentare, tracciare nel work-log, verificare; nessuno step si considera chiuso finché documentazione e tracciamento non sono allineati al codice. Durante lo sviluppo si lavora su un branch di feature, si prova la modifica eseguendo l'applicazione, e quando un passo richiede un riscontro visivo che l'agente non può osservare da sé, ad esempio lo stato di una interfaccia o l'esito di un'azione manuale, si chiede all'utente uno screenshot e lo si legge dalla cartella di cattura secondo `.claude/rules/manual-screenshots.md`; prima del commit si eseguono i controlli di qualità del progetto, tipicamente lint e build. Quando il passo chiude un difetto, il controllo che conta non è che le prove siano verdi ma che sarebbero cadute se il difetto fosse rimasto: si rimette il difetto, si guarda quali prove cadono, si ripristina il file e si verifica il ripristino con uno strumento invece che a memoria. La norma `.claude/skills/prove-che-misurano/RIFERIMENTO.md` raccoglie questa pratica e i tre modi documentati in cui una prova passa senza misurare niente, tutti osservati su progetti istanziati da questo template e nessuno dedotto: una prova che sceglie i propri argomenti può sceglierli gentili, una prova su funzione pura non dimostra che il risultato arrivi a destinazione, e verificare che cosa si consegna non basta quando chi riceve interpreta. A feature completata si genera un documento markdown permanente che fissa la logica implementata, le scelte architetturali e il contesto operativo, si consolidano nelle schede strutturali le parti rilevanti emerse dal `current-work.md`, si aggiorna il work-log e si bumpano i `last-verified-commit`.

Le parti del diario relative alla feature chiusa si archiviano.

Una skill dedicata si introduce solo se la feature comporta una procedura complessa o ripetibile; per il lavoro incrementale bastano i comandi e le regole. Su progetti con un ciclo lungo conviene strutturare il lavoro per fasi numerate, dove ogni fase si apre con una spiegazione discorsiva degli obiettivi, attende la conferma esplicita prima di scrivere codice, e si chiude con un riepilogo standardizzato che aggiorna il work-log. Questo ciclo si può irrobustire con strumenti dedicati: una skill che chiude la fase producendo il recap, un comando che apre la fase successiva e funge da cancello prima dell'implementazione, un comando che aggiunge una voce di decisione, e un agente guardiano che verifica gli invarianti del progetto. Le procedure ripetibili e generative, come scaffoldare insieme codice, schema e test per un nuovo endpoint o una nuova tabella, sono il caso d'uso tipico di una skill; le revisioni specializzate, di sicurezza o di audit, sono il caso d'uso tipico di un agente dedicato.

---

## 10. Comando di inizializzazione

L'inizializzazione installa il sistema in un progetto nuovo o lo allinea in uno esistente. Quando questo file è presente nella radice e l'utente invoca il comando di  inizializzazione, l'agente esegue, nell'ordine, i passi seguenti, fermandosi a chiedere conferma dove un'azione è difficilmente reversibile o tocca il version control.

Quando il bundle portabile include una cartella `templates/` con gli scheletri canonici dell'anatomia, ovvero `CLAUDE.md`, `AGENTS.md`, `CLAUDE.local.md`, `settings.json`, lo snippet di `.gitignore`, i file di `memory/`, le schede di `context/`, i file di `_notes/`, lo strumento `sync-codex-skills.py` e, opzionalmente, `.mcp.json`, i passi che creano file li istanziano da quei template sostituendo i segnaposto tra parentesi angolari, invece di rigenerarne il contenuto a memoria. La mappa di istanziazione, con la collocazione e lo stato git di ciascun file, vive in `templates/README.md`. In assenza della cartella `templates/`, i file si ricostruiscono dalla descrizione di questa sezione e della sezione 2.

Primo, verifica il version control secondo la sezione 6: scansiona file tracciati e storia alla ricerca di segreti, individua file indicizzati per errore, e riporta gli esiti senza committare. Subito dopo sceglie con l'utente l'identità git con cui verranno firmati i commit e a quale repository agganciare il remoto, e la configura a livello locale del repo secondo `.claude/rules/git-identity-and-repo.md`, senza mai committare ne pushare.

Secondo, predispone il `.gitignore` aggiungendo le esclusioni del livello privato, almeno `_notes/`, `CLAUDE.local.md`, `.claude/settings.local.json`, i documenti grezzi (`.docx`, `.pdf`, e affini) con le eventuali eccezioni curate, e le cartelle scratch `.tmp-doc-*`, che coprono sia l'estrazione manuale di un singolo documento sia la cache condivisa del pacchetto `doc-ingest`.

Terzo, crea l'anatomia di `.claude`descritta nella sezione 2 nella forma minima: `settings.json` con una whitelist minima di permessi allow/deny e le variabili di progetto utili come nome e fase, le cartelle `commands`, `rules`, `skills`, `agents`, la cartella `memory` con `index.md`, `progress.md` e `decisions.md`, e la cartella `context` con le schede `STACK.md`, `design-and-security.md`, `deployment.md`, `dev-testing.md`, `current-work.md`, `roadmap.md` e la sottocartella `diagrams`.

Quarto, crea o aggiorna `CLAUDE.md` nella radice in modo che indicizzi esplicitamente i soli file satellite tracciati, senza puntatori a materiale in `_notes/` o locale, e contenga la procedura di ripresa della sezione 12. Crea o aggiorna anche `AGENTS.md` dal template canonico come ponte verso `CLAUDE.md`, senza duplicare le direttive. Accanto a essi crea, se non esiste, uno stub di `CLAUDE.local.md` per gli override personali, ignorato da git e mai indicizzato dal `CLAUDE.md` di team.

Quinto, crea la cartella `_notes` con `DIARIO.md`, `RESOCONTO.md` e `TEST-CHECKLIST.md`, dopo aver confermato che `_notes` è ignorato.

Sesto, installa le skill del motore di riconciliazione e del flusso git, ciascuna come `SKILL.md` dentro la propria cartella sotto `.claude/skills`. Installa `sync-codex-skills.py` sotto `tools/`, lo esegue per generare i wrapper corrispondenti sotto `.agents/skills/` e verifica con `--check`; la stessa sincronizzazione si ripete dopo ogni aggiunta, rimozione o modifica di una skill canonica. In questo passo si pone anche il gate sulla **GitHub CLI**, che non si installa mai per inerzia perché la domanda è duplice e le due metà hanno risposte indipendenti. Serve a questo progetto, cioè le pull request hanno una descrizione lunga e curata che vive come file nel repository, oppure se ne consultano spesso stato e commenti? E si vuole che esista su questa macchina, sapendo che l'autorizzazione crea un legame durevole fra la macchina e l'account? Se la risposta è sì a entrambe, l'inizializzazione verifica che l'eseguibile risponda e che `gh auth status` nomini l'account atteso, e **registra l'autorizzazione fra le operazioni manuali** con la data e il collegamento alla pagina di revoca: un legame che nessuno ha scritto è un legame che nessuno saprà sciogliere il giorno in cui quella macchina non servirà più. Il dettaglio dei quattro assi di identità, della trappola del PATH e dell'alias SSH che rompe il riconoscimento del repository sta in `rules/git-identity-and-repo.md`; resta fermo che commit, push e merge restano gesti dell'utente anche quando lo strumento renderebbe facile automatizzarli.

Settimo, popola le schede di `context` con il frontmatter di riconciliazione, ancorato al commit corrente, lasciando i `covers-paths` da affinare man mano che il codice viene mappato. Su un progetto greenfield appena inizializzato il commit corrente non esiste ancora, perché il primo commit è un'operazione manuale dell'utente che segue l'init: in quel caso i campi `generated-from-commit` e `last-verified-commit` si lasciano a un segnaposto esplicito, ad esempio `PENDING-FIRST-COMMIT`, e si ancorano al primo commit reale subito dopo, eseguendo la skill di sincronizzazione che li porta a `HEAD`. Lo snapshot di `memory/index.md` riporta lo stesso segnaposto come commit di riferimento finché il primo commit non è stato creato.

Ottavo, scrive in`memory/progress.md` la prima voce, che registra l'inizializzazione del sistema e la data, e in`memory/index.md` lo snapshot iniziale. Le schede non vanno riempite di contenuto inventato in fase di init: si creano con la struttura e il frontmatter, e si popolano leggendo il codice nei passi successivi. Quando si parte da uno stack noto, in questo passo si possono installare skill già predisposte come pacchetti di conoscenza per quel framework o per la piattaforma di deploy, invece di ricostruirle. Sullo stesso principio, se lo stack riconosciuto è tra quelli coperti dal pacchetto opzionale `stack-profiles` (vedi `templates/stack-profiles/`), si propone al gate l'istanziazione del profilo di convenzioni corrispondente come regola modulare `rules/stack-profile.md`, normativa e complementare alla scheda descrittiva `STACK.md`.

L'integrazione di un server MCP è un passo a parte e opzionale, da eseguire solo se il progetto deve collegarsi a un servizio esterno. In quel caso si creano nella radice del progetto, accanto a `.claude` e mai sotto di esso come stabilito nella sezione 2, il file `.mcp.json` istanziato dal template opzionale e la cartella `mcp/` con l'implementazione del server; entrambi sono tracciati. Diversamente non si creano, e il sistema resta a sole skill locali. La differenza di fondo è quella della sezione 1: la skill è un workflow locale versionato col repository, l'MCP è un servizio in rete, tipicamente condiviso, che Claude Code scopre esclusivamente dal `.mcp.json` di radice.

---

## 11. Adozione su un progetto esistente

Un progetto può avere già codice e una storia git lunga senza adottare questo sistema. L'obiettivo dell'adozione è allineare retroattivamente tracciamento e documentazione allo stesso standard, senza riscrivere la storia git e senza inventare contenuto. La differenza rispetto all'inizializzazione greenfield è che qui si parte da un repository popolato, quindi prima si rileva cosa esiste e poi si colma il divario in modo incrementale.

Il percorso è il seguente. Si fa un inventario di ciò che è già presente, la cartella `.claude/`, `CLAUDE.md`, `AGENTS.md`, `.agents/skills/`, eventuali documenti, il `.gitignore`, la configurazione di test e di integrazione continua, e lo si mappa contro l'anatomia canonica della sezione 2, segnalando i divari senza toccarli. Si esegue la scansione del version control e dei segreti della sezione 6, che qui pesa di più perché la storia è lunga e può contenere file `.env` rimossi ma ancora recuperabili. Si ricostruisce la memoria dalla storia: `memory/decisions.md` si popola rileggendo le decisioni implicite nei commit, ciascuna come voce ADR numerata, e `memory/progress.md` riassume le tappe già fatte senza inventare ciò che la storia non dimostra, mentre `memory/index.md` fotografa lo stato al commit corrente. Si creano le schede di `context` con il frontmatter di riconciliazione ancorato al commit corrente e le si popola leggendo il codice attuale, non la storia, una alla volta a partire dalle aree più critiche, definendo i `covers-paths` sulle aree reali. Per ricavare struttura e simboli del codice esistente in modo preciso ed economico in contesto, invece di leggere ogni file a mano, conviene attivare il server MCP `code-context-provider-mcp`, già configurato in `templates/mcp.json`: è proprio in allineamento, dove la struttura del progetto non è nota a priori, che questo aiuto ripaga di più, mentre in un progetto nuovo lo stack è già noto e resta opzionale. Da quel punto `last-verified-commit` coincide con il commit corrente e il drift futuro si gestisce con la skill di sincronizzazione come in un progetto nato col sistema.

L'adozione è iterativa e va proposta, non imposta: nulla viene sovrascritto in silenzio, ogni passo che tocca git chiede conferma, e le schede si allineano poche alla volta invece di tutte insieme. Quando un documento esistente copre già un'area, lo si dota di frontmatter e lo si riconcilia invece di duplicarlo.

---

## 12. Procedura di ripresa in una sessione nuova

Lo stato del progetto è interamente recuperabile seguendo, all'inizio di una sessione, un percorso fisso. Il percorso comincia però con una verifica e non con una lettura, perché tutto ciò che segue presuppone che la sessione precedente sia arrivata alla fine, e non sempre è vero. Una sessione che cade a metà lascia il progetto in uno stato che il file di ripresa non descrive, e il danno non è la perdita del lavoro, che sta su disco e in git, ma il fatto che la sessione nuova prenda quella fotografia vecchia per il presente e vi costruisca sopra: un file di ripresa non aggiornato ha esattamente lo stesso aspetto di uno aggiornato. Lo strumento `tools/verifica-ripresa.py` rende meccanica la distinzione confrontando l'impronta registrata alla chiusura, cioè commit e forma dell'albero di lavoro in quel momento, con lo stato reale; la skill `riprendi` è la procedura che ne interpreta l'esito. L'impronta si registra come ultimo atto della sessione, dopo i commit dell'utente; lo strumento `tools/chiudi-sessione.ps1`, con la variante `.sh`, lega in un comando i controlli, il commit con conferma dell'utente e con il messaggio che l'agente ha preparato in `_notes/COMMIT-MSG.txt`, il push verificato, la registrazione e il wipe degli account, e una sessione che finisce senza registrarla non produce un danno ma esattamente la condizione che la verifica sa riconoscere. Dove il progetto usa più alberi di lavoro la stessa verifica confronta anche la memoria di questo albero con quella degli altri, perché la memoria versionata vale per la branch su cui è scritta e un albero su una branch indietro ne riceve una ben formata e vecchia: la sezione 22 e la norma `skills/alberi-di-lavoro/RIFERIMENTO.md` dicono da dove si legge allora la memoria.

Fatta la verifica, si legge per primo `.claude/memory/index.md`, che dà branch, commit di riferimento, stato di verifica di ogni scheda e punto di ripresa. Si legge poi `context/current-work.md` se c'è una feature attiva, per sapere cosa è in lavorazione e quali sono i TODO e i limiti d'ambiente. Si invoca la skill di sincronizzazione per verificare il drift tra schede e codice, e si leggono solo le schede pertinenti al task, mai tutte insieme. Il work-log `memory/progress.md` e il registro `memory/decisions.md` forniscono la storia e le decisioni quando servono. Il materiale grezzo sotto `_notes/` si apre solo per verificare un requisito originale. Questa sezione va replicata, in forma sintetica, dentro il `CLAUDE.md`principale, perché è lì che una sessione nuova la cerca per prima.

---

## 13. Bootstrap dell'ambiente di sviluppo

Lo stesso principio che governa i livelli documentali, versionare la fonte riproducibile e ignorare ciò che ne deriva, si applica alla catena di strumenti. Si versiona il manifesto delle dipendenze e si ignora l'ambiente materializzato, perché il manifesto è riproducibile e leggero mentre l'ambiente è derivato e pesante. In un progetto Python questo significa versionare `requirements.txt` o `pyproject.toml` e ignorare la cartella `.venv`, gli `__pycache__`, i file `*.pyc` e gli artefatti di build; in un progetto Node lo stesso principio versiona `package.json`e ignora `node_modules`. Conviene fissare in modo esplicito la versione del runtime, perché un ambiente ricreato su una macchina con un interprete diverso è una fonte silenziosa di divergenze.

Per rendere il bootstrap riproducibile e a un solo comando si forniscono due script di setup paralleli, uno per Windows in PowerShell e uno POSIX[^10] per Unix, che individuano l'interprete corretto, creano l'ambiente, installano dal manifesto e verificano l'esito con un import minimo; gli script accettano un flag per ricreare l'ambiente da zero e uno per forzare il percorso dell'interprete. Un accorgimento utile è tenere la cartella dell'ambiente presente nel repository ma vuota, con al suo interno un `.gitignore` che esclude tutto: la struttura esiste già al clone, il contenuto resta fuori da git e viene ricreato dallo script. Gli script di pipeline invocano direttamente l'interprete dell'ambiente invece di richiedere l'attivazione interattiva della shell, così si comportano in modo identico in locale e in automazione. Il bootstrap si esegue in ogni albero di lavoro, non una volta per repository: un albero aggiunto con `git worktree` condivide gli oggetti git ma non ciò che git ignora, quindi ambiente materializzato, `.env`, `_notes/` e override locali vanno ricreati in ciascuno, come descrive la sezione 22.

---

## 14. Hook di automazione e guard-rail

La cartella `hooks/`, prevista nell'anatomia ma spesso lasciata vuota, ospita automazioni che trasformano procedure facili da dimenticare in comportamenti costanti. Tre famiglie si sono dimostrate utili.

La prima è un hook di apertura sessione che esegue uno script di ripresa: stampa lo snapshot di `memory/index.md`, i file cambiati rispetto al commit di riferimento e la prossima azione concreta, così che la procedura di ripresa della sezione 12 diventi automatica invece che manuale.

La seconda è un hook di pre-commit che rende il `.gitignore` effettivamente vincolante, de-tracciando i file già committati ma ora coperti da una regola di esclusione, in modo che artefatti o materiali aggiunti prima della regola non restino indicizzati; si installa indicando a git il percorso degli hook del repository, così viaggia col progetto.

La terza famiglia è un insieme di guard-rail attorno alle modifiche del codice: prima di creare un simbolo si verifica con una ricerca che non esista già, prima di modificare un file lo si legge per intero e se ne mappano i dipendenti, i file critici richiedono conferma esplicita prima di essere toccati, dopo ogni modifica si produce una checklist di verifica, e una modifica profonda si divide obbligatoriamente in micro-passi con conferma. 

Questi guard-rail si possono esprimere come istruzioni in una regola caricata sempre, oppure, dove il meccanismo lo consente, come hook che intercettano la chiamata allo strumento. Le automazioni che eseguono comandi vanno bilanciate con la whitelist di `settings.json`, che ammette esplicitamente solo le operazioni sicure e nega quelle distruttive o verso l'esterno, in particolare commit, push e deploy, coerentemente con la regola che queste restano sempre manuali.

Il pacchetto opzionale `hooks-starter` (vedi `templates/hooks-starter/`) e l'implementazione pronta di queste famiglie: l'hook di apertura sessione della prima famiglia, la protezione dei file sensibili e la scansione dei secret in stage come guard-rail della terza, in doppia forma PowerShell e shell POSIX, mai attivi finché l'utente non registra esplicitamente i blocchi scelti nel `settings.json` del progetto. Resta uno strumento, non un sostituto del principio: gli hook che un progetto non attiva continuano a valere come disciplina descritta in questa sezione.

---

## 15. Auto-memory nativa: gate per progetto e wipe del magazzino nascosto

La auto-memory nativa introdotta nella sezione 2 è disattivata per default dal sistema con `autoMemoryEnabled: false`, perché l'unica memoria legittima è quella versionata sotto `.claude/memory/` insieme al `_notes/RESUME-PROMPT.md` ignorato, e tutto ciò che persiste deve vivere dentro la cartella di progetto ed essere autosufficiente. La scelta non è però imposta una volta per tutte: all'inizio di ogni progetto, e a ogni sessione, l'agente chiede esplicitamente come gestire la auto-memory, senza mai assumere. L'utente sceglie tra due strade. La prima lascia il flag a `false`, ed è il default consigliato. La seconda lo porta temporaneamente a `true`, a livello dell'account attivo o del solo progetto, quando in quella sessione si vuole sfruttare la memoria nativa; in quel caso vale la regola tassativa di riportarlo a `false` prima di chiudere la sessione o di cambiare progetto, così che il magazzino nascosto non resti sporco oltre la sessione che lo ha usato. La domanda si pone per ogni progetto: anche con il default a `false`, la decisione resta esplicita.

Il flag si imposta a tre livelli, con precedenza crescente: nel `settings.json` utente dell'account per valere su tutti i progetti, nel `settings.json` del progetto per quel solo progetto, e via la variabile d'ambiente `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` come override. Il magazzino nascosto vive sotto `$CLAUDE_CONFIG_DIR/projects/<slug-del-percorso>/memory/`, dove `$CLAUDE_CONFIG_DIR` è la home dell'account attivo nei setup multi-account e `<slug-del-percorso>` è il percorso assoluto del progetto reso come slug.

Anche con il flag a `false`, sessioni passate possono aver lasciato residui nel magazzino nascosto, oppure una sessione con il flag temporaneamente a `true` può non essere stata riportata a `false` in tempo. Per questo il sistema prevede un *wipe* del magazzino nascosto come operazione di manutenzione esplicita, mai automatica, da eseguire quando si vogliono azzerare i residui. Il wipe non tocca mai i file dei progetti su disco né la memoria versionata dentro le cartelle di progetto: agisce solo sugli store che Claude Code tiene nella home dell'account. Si distinguono due livelli. Il livello *per-progetto* rimuove, sotto `projects/<slug>/`, i transcript di sessione `*.jsonl`, le cartelle uuid omonime e la `memory/` nascosta, e si applica a ciascuno slug che si vuole pulire preservando per nome quelli da tenere. Il livello *totale* aggiunge gli store per-account effimeri, ovvero `sessions/`, `session-env/`, `shell-snapshots/`, `history.jsonl`, `file-history/`, `plans/`, `tasks/`, `paste-cache/`, `backups/` e l'eventuale `memory/` a livello di account, ai quali si affiancano le cache e i registri di stato `cache/`, `jobs/`, `ide/`, `todos/`, `statsig/`, `telemetry/` e `mcp-needs-auth-cache.json`. Restano intatti configurazione, credenziali, skill, plugin, hook e stato del daemon, cioè `settings.json`, `.credentials.json`, `skills/`, `plugins/`, `hooks/` e `daemon/`. Prima di un wipe totale va verificato che quegli store non contengano l'unica copia di qualcosa che serve, perché artefatti come gli script salvati sotto `plans/` o i backup di `file-history/` spariscono con essi.

Il wipe totale, per essere davvero totale, deve raggiungere due residui che non stanno nell'elenco appena dato e che una pulizia ingenua lascia indietro. Il primo è lo scratchpad temporaneo, che Claude Code tiene fuori dalla home dell'account, in `%LOCALAPPDATA%\Temp\claude\<slug-progetto>` su Windows e in `$TMPDIR/claude/<slug-progetto>` su POSIX, con una sottocartella per sessione dove finiscono gli scratchpad e gli output dei task; quella radice è condivisa fra tutti gli account della stessa utenza, quindi ripulirla è idempotente e chi chiude per ultimo la ripulisce per tutti. Il secondo è l'elenco dei percorsi aperti che vive dentro `projects` di `.claude.json`: il file va preservato perché custodisce login e configurazione, ma le sue voci `projects` registrano ogni cartella su cui si è lavorato e sopravvivono a qualunque pulizia degli store. Di quel file si rimuovono quindi le sole voci dei percorsi non preservati, insieme a quelle del gemello `.claude.json.backup`, lasciando tutto il resto al suo posto. La rimozione ha un effetto collaterale voluto di cui essere consapevoli: sparisce anche il `hasTrustDialogAccepted` di quel percorso, quindi al successivo avvio su quella cartella Claude Code chiede di nuovo di fidarsi dei file.

```sh
# Wipe per-progetto del magazzino nascosto. KEEP elenca gli slug da preservare;
# l'insieme e specifico della macchina (qui i progetti di sviluppo stanno sotto D: ed E:).
# Agisce solo nella home dell'account, mai sul codice dei progetti su disco.
KEEP="D-- D--scenia- E--"
find "$CLAUDE_CONFIG_DIR/projects" -mindepth 1 -maxdepth 1 -type d | while read -r p; do
  case " $KEEP " in *" $(basename "$p") "*) continue ;; esac
  rm -rf "$p"
done

# Wipe totale: aggiunge gli store per-account effimeri e le cache di stato.
# Preserva config, login, skill, plugin, hook e daemon.
rm -rf "$CLAUDE_CONFIG_DIR"/{sessions,session-env,shell-snapshots,file-history,plans,tasks,paste-cache,backups,memory}/* "$CLAUDE_CONFIG_DIR"/{cache,jobs,ide,todos,statsig,telemetry}/* "$CLAUDE_CONFIG_DIR/history.jsonl" "$CLAUDE_CONFIG_DIR/mcp-needs-auth-cache.json"

# Scratchpad temporanei, che stanno FUORI dalla home dell'account: una cartella per
# slug di progetto, una sottocartella per sessione. Radice condivisa fra gli account.
for p in "${TMPDIR:-/tmp}/claude"/*/; do
  case " $KEEP " in *" $(basename "$p") "*) continue ;; esac
  rm -rf "$p"
done

# Voci 'projects' di .claude.json: si rimuovono i percorsi non preservati, il resto
# del file (login, configurazione) resta intatto. Vedi templates/tools/scrub-claude-json.js.
```

L'esecuzione manuale di questo wipe resta in mano all'utente come ogni operazione difficilmente reversibile: l'agente lo propone, mostra prima cosa verrebbe rimosso e cosa preservato, e procede solo su conferma esplicita.

Il wipe può essere reso automatico, come scelta opt-in dell'utente, installando per ogni account un hook `SessionEnd` che lo esegue a ogni chiusura di sessione, così che il magazzino nascosto resti pulito nel tempo senza comandi a mano. Su Windows lo script è `session-end-wipe.ps1`, il cui template vive in `templates/tools/`: si copia in `<CLAUDE_CONFIG_DIR>/hooks/session-end-wipe.ps1` sostituendo il segnaposto del percorso dell'account, e si registra nel `settings.json` dell'account con `"hooks": { "SessionEnd": [ { "hooks": [ { "type": "command", "command": "powershell.exe -NoProfile -ExecutionPolicy Bypass -File \"<CLAUDE_CONFIG_DIR>\\hooks\\session-end-wipe.ps1\"" } ] } ] }`; senza `matcher` l'hook gira a ogni chiusura. Vale un caveat onesto e non documentato sul timing: Claude Code può riscrivere alcuni file di sessione dopo l'esecuzione dell'hook, quindi l'automazione è best-effort, perché la coda dell'ultima sessione può ricomparire e venire rimossa solo alla chiusura successiva; l'hook non scatta inoltre su una terminazione anomala del processo. Per non perdere resume e undo dei progetti preservati tra una sessione e l'altra, le voci `sessions` e `file-history` dell'elenco degli store effimeri si possono escludere dallo script, accettando che restino tracce di quegli store. Su Linux la variante equivalente è `session-end-wipe.sh`, installata allo stesso modo ma registrata con un comando hook `bash "<CLAUDE_CONFIG_DIR>/hooks/session-end-wipe.sh"`.

L'insieme dei prefissi degli slug da preservare è la parte pericolosa dell'installazione, e merita il paragrafo che segue perché il modo in cui sbaglia non somiglia a un errore. Quei prefissi sono una scelta specifica della macchina, uno per ogni radice su cui vivono i progetti di sviluppo, e la loro forma dipende da come Claude Code deriva lo slug dal percorso: su Windows nasce dalla lettera del disco, quindi assume l'aspetto `D--` o `E--`, mentre su POSIX nasce dal percorso assoluto e ha l'aspetto di quel percorso con i separatori sostituiti, quindi non comincia con nessuna lettera di disco. Ne segue che un insieme di prefissi corretto su una macchina non è semplicemente inutile su un'altra: non corrisponde a nessuno slug, l'insieme dei progetti preservati risulta vuoto, e un wipe che si fidasse della propria configurazione cancellerebbe l'intero magazzino senza emettere un errore, perché dal suo punto di vista sta facendo esattamente ciò che gli è stato chiesto. Il caso si è presentato per davvero, portando su Linux uno script con i prefissi di una installazione Windows.

Per questo i due script non escono dal template in condizione di funzionare, e non hanno un valore di default per i prefissi ma un segnaposto che li blocca. Le guardie che eseguono prima di qualunque rimozione sono tre. La prima verifica che il percorso della home dell'account esista e assomigli a un magazzino di Claude Code, cioè contenga almeno `projects/` o un `settings.json`, così che un segnaposto non sostituito o un percorso sbagliato non si traducano in rimozioni altrove. La seconda rifiuta di procedere finché i prefissi sono il segnaposto, perché un insieme vuoto significherebbe non preservare niente. La terza è quella che coglie il caso descritto sopra: se esistono progetti nel magazzino e nessuno di essi corrisponde ai prefissi configurati, lo script si ferma dichiarando che la configurazione è di un'altra macchina, e va forzato con una deroga esplicita solo da chi voglia davvero un account in cui nulla è preservato. Poiché un hook `SessionEnd` gira senza che nessuno ne veda l'output, l'esito dell'ultima corsa, rifiuti compresi, viene scritto in `session-end-wipe.log` dentro la home dell'account.

I prefissi giusti, del resto, non vanno indovinati: si leggono. Entrambi gli script accettano un modo di sola lettura, `-List` su Windows e `--list` su Linux, che elenca gli slug realmente presenti marcando ciascuno come preservato o da rimuovere, e funziona anche quando la configurazione è ancora il segnaposto, perché è proprio il comando con cui si scopre che cosa configurare. Un secondo modo, `-DryRun` e `--dry-run`, stampa ogni rimozione che verrebbe fatta senza farne nessuna, ed è il modo in cui l'installazione si prova prima di registrare l'hook. La procedura corretta è quindi elencare, chiedere all'utente quali radici preservare mostrandogli l'elenco, compilare, provare a vuoto e solo allora registrare l'hook.

Accanto allo script va copiato il suo companion `scrub-claude-json.js`, che è ciò che esegue la pulizia delle voci `projects` di `.claude.json` descritta sopra: senza di esso il wipe si limita agli altri passaggi, senza errori. La delega a Node non è un vezzo ma una necessità, e vale documentarla perché non è ovvia: `ConvertFrom-Json` di PowerShell 5.1 tratta le chiavi JSON come case-insensitive e va in errore su un `.claude.json` che contenga sia `e:/progetto` sia `E:/progetto`, cosa che accade appena si apre la stessa cartella scrivendo la lettera del disco in modo diverso, mentre `JSON.parse` è la stessa semantica che Claude Code applica al proprio file. Poiché quel file custodisce il login, la riscrittura è difensiva: si verifica che `oauthAccount` e `userID` siano ancora presenti, si valida il JSON prodotto, si scrive su un temporaneo, lo si rilegge da disco e solo allora si sostituisce l'originale, e qualunque anomalia annulla tutto senza lasciare residui. Due dettagli di installazione ricorrenti: il percorso di `.claude.json` non è sempre dentro la home dell'account, perché con `CLAUDE_CONFIG_DIR` impostato vi sta dentro ma nella home di default sta accanto, in `$HOME/.claude.json`; e quella stessa home di default può non avere un `settings.json`, nel qual caso l'hook si registra nel `settings.local.json`.

Poiché l'hook è una proprietà dell'account e non del progetto, il sistema verifica che l'account attivo sia in regola tramite `templates/tools/check-account-hygiene` (`.ps1` su Windows, `.sh` su Linux), uno script di sola lettura che controlla tre cose e stampa un report PASS/FAIL con le azioni di rimedio: `autoMemoryEnabled: false`, la presenza dell'hook `SessionEnd` di wipe, e che lo script di wipe installato sia configurato per questa macchina. Il terzo controllo esiste perché i primi due passano anche su un account dove il wipe è installato ma inservibile o pericoloso: invoca lo script installato nel suo modo di sola lettura e segnala sia il segnaposto mai sostituito, sia il caso in cui nessuno slug presente corrisponda ai prefissi configurati. Il check si esegue al Passo 0 dell'inizializzazione e dell'allineamento di un progetto, prima di toccare il repository, e in caso di FAIL l'agente propone di installare lo script e registrare l'hook, senza mai modificare il `settings.json` dell'account senza conferma.

Complementare al wipe c'è la sessione incognito: invece di pulire dopo, si evita del tutto di scrivere nell'account reale, redirigendo `HOME` e le cartelle XDG (`XDG_CONFIG_HOME`, `XDG_CACHE_HOME`) su una directory temporanea e azzerando `CLAUDE_CONFIG_DIR`, così la sessione parte vergine e la temp si rimuove alla chiusura. Gli script `templates/tools/claude-incognito.ps1` e `claude-incognito.sh` la avviano su un progetto a scelta. È utile per lavorare su materiale sensibile senza lasciare traccia in credenziali, cronologia o configurazione dell'account. La tecnica si basa sulla specifica XDG Base Directory più la redirezione di `HOME`.

---

## 16. Il ritorno dai progetti istanziati

Un template che non impara dai progetti che ne nascono invecchia mentre loro migliorano, e la distanza non si recupera più perché nessuno sa più quali delle due versioni sia quella giusta. Il canale che lo evita non è una revisione periodica, che nessuno fa, ma una domanda posta nel momento esatto in cui la conoscenza esiste.

La domanda è questa. Quando in un progetto istanziato si corregge un difetto, si scopre una trappola o si scrive una regola, prima di considerare chiuso il passo si stabilisce se quella conoscenza sia **specifica di quel progetto o generale del modo di lavorare**. Se è generale, sale qui nello stesso giro di lavoro, non in un momento futuro.

Il criterio pratico per distinguere è meccanico e va usato come tale: si prova a riscrivere la lezione togliendo ogni nome proprio del progetto, il dominio, i nomi dei file e la tecnologia. Se dopo quella ripulitura resta vera e utile, è del template; se non sta più in piedi, era un fatto di quel progetto. **La ripulitura non è un passaggio formale ma la verifica stessa.**

Il momento conta quanto il criterio. La domanda va posta **al momento della correzione**, quando il ragionamento è ancora presente, e non a fine progetto quando resta solo l'esito: il perché di una scelta è la prima cosa che si perde, ed è precisamente la parte che rende una regola utile a chi non c'era.

Vale la pena dire che cosa questo canale produce davvero, perché è meno prevedibile di quanto sembri. Nell'arco di due giorni su un progetto istanziato ha prodotto una regola sulle prove che misurano davvero qualcosa, una sezione sui presupposti non dichiarati di una shell con le sue quattro cause distinte, la trattazione della GitHub CLI come quarto asse di identità con il relativo gate di adozione, un pacchetto per la documentazione didattica e una guardia dentro uno strumento che aveva appena rotto una compilazione. **Nessuna di queste cose era stata pianificata: sono tutte uscite da un difetto.** Un template si irrobustisce dove qualcuno ha sbagliato, non dove qualcuno ha progettato.

La direzione opposta resta quella dell'inizializzazione e dell'allineamento, e le due non vanno confuse. Dal template scende la struttura; dai progetti sale la conoscenza guadagnata sul campo. Un progetto che non ha mai fatto salire niente è probabilmente un progetto che non ha ancora incontrato nulla di interessante, oppure uno in cui la domanda non viene posta.

## 17. Una regola senza presidio è una speranza

Principio generalizzato da un progetto istanziato, dove la stessa conclusione è stata raggiunta **tre volte in una settimana** per ragioni completamente diverse. La ripetizione è il dato che lo rende un principio e non un aneddoto.

La prima volta riguardava le prove. Una suite verde non dice che il comportamento è corretto, dice che le prove non hanno protestato, e le due cose coincidono solo se le prove esercitano davvero il difetto. Il presidio è diventato un passo obbligato: si rimette il difetto, si guarda quali prove cadono, si ripristina.

La seconda riguardava uno strumento di sostituzione tipografica, lanciato su file sorgente dove ha rotto la compilazione. Chi lo aveva lanciato aveva nominato il rischio prima di eseguire e ha verificato subito, quindi il danno è stato nullo. Ma il presidio non poteva restare quella prudenza: è diventato una guardia dentro lo strumento, che rifiuta le estensioni di codice e spiega perché.

La terza riguardava la regola sul documentare mentre si lavora. Scritta, poi riaffermata in forma enfatica, poi richiamata ancora. Il presidio è diventato un controllo che confronta le date dei commit con quelle del registro.

Il principio che le tre insieme dimostrano si enuncia così. **Una regola che dipende dalla memoria o dalla disciplina di chi esegue fallisce esattamente quando serve**, cioè nelle sessioni lunghe o sotto pressione, quando l'attenzione è su altro. Scriverla meglio non la rafforza; ripeterla non la rafforza. L'unico rafforzamento reale è un controllo che renda visibile la violazione nel momento in cui accade.

Ne discendono tre conseguenze operative.

**Il sintomo da riconoscere è la ripetizione.** Quando una regola deve essere richiamata una seconda volta, il difetto sta nell'assenza di un presidio, e non in chi l'ha violata né nella sua formulazione. La domanda giusta a quel punto non è come renderla più chiara ma quale controllo meccanico ne osserverebbe la violazione.

**Il presidio va nominato dalla regola che presidia.** Un controllo che esiste e che nessun documento cita non viene eseguito, per la stessa ragione per cui una regola che nessun documento carica non viene applicata. La regola dichiara il proprio controllo e il momento in cui va eseguito.

**Il presidio dichiara che cosa non copre.** Nessun controllo meccanico raggiunge la qualità di un contenuto: distingue il silenzio dalla presenza, non il buono dal mediocre. Dirlo è parte del presidio, perché credere che copra più di quanto copre produce fiducia in una copertura inesistente, che è peggio della sua assenza.

Non tutte le regole ammettono un presidio, e non tutte lo meritano. Il criterio è il costo della violazione: quando è alto e silenzioso, cioè quando nessuno se ne accorge finché non è tardi, il presidio va costruito anche se costa; quando è basso o rumoroso, la regola scritta basta.

## 18. Un piano descrive uno stato che può essere cambiato, e le sue istruzioni sono ipotesi

Generalizzato da un progetto istanziato, dove lo stesso fenomeno si è presentato **cinque volte nello stesso piano di lavoro**, in forme diverse e con esiti diversi. La ripetizione è ciò che lo rende un principio e non un aneddoto.

Un piano dettagliato, scritto da qualcun altro o da noi stessi settimane prima, elenca per ciascun passo i file da toccare e le modifiche da fare. È utilissimo e ha una proprietà che si dimentica sempre: **descrive il codice com'era nel momento in cui è stato scritto**. Fra la stesura e l'esecuzione il codice cambia, per ragioni tutte legittime.

Ne discende la formulazione da tenere presente: le istruzioni di un piano sono **ipotesi da confermare, non fatti da eseguire**, e la conferma costa sempre meno della modifica sbagliata e molto meno della modifica non necessaria.

Le cinque forme osservate meritano di essere elencate, perché sono i modi concreti in cui l'ipotesi risulta falsa e nessuno di essi assomiglia agli altri.

Un passo può richiedere **zero righe di codice**, perché tutte le sue istruzioni risultano già soddisfatte o non applicabili alla variante scelta. È l'esito psicologicamente più difficile da accettare, perché un passo che non produce nulla sembra un passo saltato, e quella pressione è precisamente ciò che genera modifiche non richieste.

Il piano può **nominare il file sbagliato**, perché il componente di cui parla è stato spostato dopo la stesura. La risposta giusta non è ricreare nel file nominato ciò che il piano descrive, ma applicare l'intenzione dove la cosa vive davvero.

Un **criterio di accettazione può mentire**, perché verifica la forma che cerca e non la proprietà che intende: una ricerca di valori esadecimali non trova un colore scritto in un'altra notazione, e il difetto si nasconde sempre nelle forme che il criterio non conosce.

Un'istruzione può chiedere di modificare qualcosa che **non è visibile**, e ogni istruzione della forma "cambia l'aspetto di X" contiene il presupposto silenzioso che X si veda. Quel presupposto è verificabile, spesso senza nemmeno aprire l'applicazione.

E un'istruzione estetica generica può chiedere di rimuovere una struttura che **esiste per una ragione funzionale**, decisa mesi prima da chi conosceva un problema che il piano non conosce. Qui la regola sovraordinata, che un piano ben scritto dichiara da sé, è che una modifica estetica non tocca una scelta funzionale: si segnala e si prosegue.

La conseguenza operativa è una sola domanda, da porsi prima di eseguire ciascuna istruzione: **questa istruzione è ancora vera per questo codice, in questa variante?** A volte la risposta è che non c'è nulla da fare, a volte che il bersaglio è un altro, a volte che esiste un problema che il piano non aveva previsto. Nessuno dei tre casi è un'anomalia da correggere seguendo il documento più alla lettera: è il lavoro di chi un piano lo esegue invece di copiarlo.

## 19. Un controllo che dipende da ciò che deve controllare non è un controllo

Generalizzato dallo stesso progetto, dove il principio si è presentato in quattro forme lontanissime fra loro, il che è il segno che riguarda la struttura di un controllo e non il dominio in cui vive.

Un controllo ha sempre due parti: una condizione e **i dati su cui la valuta**. Si rilegge quasi sempre la prima e quasi mai la seconda, e questo è il punto: una condizione scritta bene su un dato non affidabile è indistinguibile, leggendola, da un controllo che funziona.

La prima forma riguarda i dati. Un controllo che verifica un campo **scrivibile da chi deve superarlo** non verifica nulla: chi lo aggira scrive prima il campo e poi supera il controllo. La domanda da porsi davanti a qualunque verifica non è se la condizione sia corretta, ma **da dove venga il dato che consulta**.

La seconda riguarda la composizione delle regole. In diversi sistemi di autorizzazione le regole sono **additive**: quando più regole coprono lo stesso oggetto, basta che una conceda. Restringere un permesso aggiungendo una regola più specifica non restringe niente, se quella generica continua a coprire lo stesso oggetto concedendo di più. È l'errore più facile da commettere in quei linguaggi, ed è invisibile perché la regola stretta esiste e si legge.

La terza riguarda le prove. Una finzione scritta **guardando il codice che deve soddisfare** descrive quel codice, non la dipendenza che sostituisce, e da quel momento conferma qualunque cosa il codice faccia. Nel caso osservato la finzione dichiarava una proprietà che nel sistema reale non esisteva nella stessa forma, proprio perché il codice ne aveva bisogno.

La quarta riguarda l'ambiente. Un comportamento che funziona perché due parti del sistema coincidono **per caso** sulla macchina di chi sviluppa risulta soltanto non ancora smentito.

La forma generale che le tiene insieme si enuncia in una riga, ed è quella da ricordare: **un controllo che dipende da qualcosa che chi lo deve superare può influenzare non è un controllo.** Chi lo deve superare può essere una persona che attacca, ma anche il codice stesso, una regola più larga, o un ambiente che nessuno ha dichiarato.

## 20. Prima di costruire strumentazione, si guarda che cosa il sistema produce già

Principio breve e con un ritorno sproporzionato, osservato durante la messa a punto di una verifica automatica.

Un fallimento non diceva la propria causa. Si è aggiunta strumentazione per ottenerla, si è verificato che non cambiava nulla, si è aggiunta altra strumentazione. **La prova decisiva era già stata prodotta e conservata dal sistema a ogni fallimento, per giorni, e nessuno l'aveva scaricata**: era un artefatto di esecuzione con dentro una schermata del momento del guasto e l'errore letterale.

La domanda che avrebbe accorciato quella ricerca va posta presto e costa niente: **che cosa questo sistema sta già producendo che non ho ancora guardato?** Registri conservati, artefatti di esecuzione, rapporti generati, cartelle di uscita che nessuno apre. Quasi ogni strumento moderno produce più di quanto chi lo usa consulti.

Un corollario dallo stesso episodio, indipendente e altrettanto utile. **Un registro che non cambia affatto dopo una correzione prova che la correzione ha toccato una leva non collegata al problema, e va trattato come tale invece di essere minimizzato.** Riconoscerlo subito impedisce di costruire una seconda ipotesi sopra la prima, che è il modo in cui una diagnosi si allontana dalla causa invece di avvicinarsi.

## 21. Il sistema risponde alla domanda che gli è stata posta, non a quella che avevi in mente

Principio osservato in **quattro forme in una sola giornata**, su quattro sistemi senza alcun rapporto fra loro: una console di amministrazione, un registro di consegna della posta, un pannello di consumo e la diagnostica di uno strumento da terminale. La ripetizione su domini così distanti è ciò che lo rende un principio strutturale e non un difetto di un prodotto.

In tutti e quattro i casi l'indicatore letto era **letteralmente vero**, ed è stato inteso come risposta a una domanda diversa da quella cui rispondeva. Nessuno dei quattro sistemi ha mentito; tutti e quattro hanno prodotto una diagnosi sbagliata e sicura di sé.

Un pannello dichiarava l'assenza di una licenza, il che era vero, e da lì si è concluso che l'oggetto governato da quella licenza non esistesse. Non esisteva la licenza: l'oggetto esisteva e funzionava, perché in quel modello non ne richiede una. **La domanda "esiste?" era stata posta a un pannello che risponde a "quanto costa?".**

Il riepilogo di un registro di consegna riportava un esito negativo per un messaggio che, aperti i suoi eventi, risultava **consegnato con successo** a un indirizzo di inoltro. Il riepilogo rispondeva a "è arrivato nella cassetta di destinazione originale?", non a "è arrivato?".

Un indicatore di consumo esprimeva una percentuale di **disponibilità residua**, letta come percentuale consumata. Il valore era corretto e l'interpretazione lo ribaltava: si è creduto di essere quasi al limite mentre si era appena partiti.

La diagnostica di uno strumento riportava un componente di sicurezza come disattivato, e si è concluso che la protezione fosse dichiarata ma non imposta. Era vero che il componente era disattivato, ma per una ragione diversa da quella immaginata: non era **ancora stato installato**, e lo strumento lo avrebbe proposto alla prima esecuzione interattiva.

Ne discendono tre conseguenze operative.

**Prima di fidarsi di un indicatore, si stabilisce a quale domanda risponde.** In pratica è la differenza fra "questo campo dice che la cassetta non c'è" e "questo campo dice che non c'è una licenza". La seconda formulazione contiene già il dubbio che la prima nasconde.

**Dove esistono un riepilogo e un dettaglio, il dettaglio ha ragione.** Un riepilogo è una proiezione calcolata per uno scopo, quasi mai il proprio. La regola operativa è che una diagnosi non si chiude mai su una colonna di stato quando sotto c'è un elenco di eventi: si apre l'elenco. Costa dieci secondi e ha evitato, nel caso osservato, ore di ricerca nella direzione sbagliata.

**Si cerca la fonte autoritativa per quella domanda, non quella più vicina.** Ogni dominio ne ha una, ed è spesso una console diversa da quella in cui si stava già lavorando. Restare dove si è già loggati è la ragione più comune per cui si consulta la fonte sbagliata.

Un corollario della stessa famiglia, osservato nella stessa giornata su un quinto sistema. Uno strumento la cui configurazione seleziona il perimetro di lavoro, quando quella configurazione non arriva, **non fallisce: ricade su un default e prosegue dichiarando successo**. L'unico segnale era una riga di errore della shell che sembrava scollegata dal resto. La difesa non è ricordarsi la sintassi giusta ma non digitare mai quel comando a mano: ci si arriva da uno script che verifica il perimetro prima di eseguire, secondo la sezione 17.

### Tre occorrenze successive, e la terza è la più istruttiva

Registrate il giorno dopo le prime cinque, in un solo lavoro di mezza giornata sulla verifica di un hook di fine sessione. La ripetizione così ravvicinata è essa stessa il dato: **questa è la forma normale in cui si sbaglia**, e non basta averla fatta una volta per impararla.

**Un'assenza non è una risposta finché non si sa di che cosa è l'assenza.** Un file marcatore non comparso sembrava rispondere a *"l'hook funziona?"*. Rispondeva invece a *"la sessione è finita?"*, e la sessione era ancora aperta. La diagnosi sbagliata stava per essere chiusa con sicurezza; l'ha impedita l'apertura del registro interno dello strumento, che mostrava un battito ogni trentun secondi.

**Un pannello che dice `Active` risponde a "è armato?", non a "funziona?".** Il comando diagnostico dello strumento dichiarava l'hook `Installed 1, Active 1`, ed era letteralmente vero: era installato, approvato e abilitato. Non veniva eseguito lo stesso, perché il comando configurato era malformato. Nessuna delle due colonne mentiva, e nessuna delle due rispondeva alla domanda che si stava ponendo.

**Una prova costruita male risponde a una domanda vicina a quella giusta, e la si scambia per quella giusta.** Serviva sapere se una sessione si potesse rimuovere *dal processo che la stava chiudendo*. È stata misurata invece la rimozione di *un'altra* sessione mentre *un altro* processo era vivo: più semplice da allestire, a costo nullo, e con esito positivo. La conclusione, "nessun conflitto", è stata smentita mezz'ora dopo dal percorso vero, che falliva. **La frugalità aveva selezionato lo scenario più comodo, non quello che serviva.**

Ne discende una quarta conseguenza operativa, che si aggiunge alle tre sopra e riguarda chi le prove le progetta, non chi legge gli indicatori.

**Prima di fidarsi di una prova, si dichiara quale differenza rispetto al caso reale si sta accettando.** Una prova è un modello, e ogni modello omette qualcosa: finché l'omissione resta implicita, l'esito positivo si estende senza accorgersene al caso che non è stato provato. Scrivere per esteso *"questa prova differisce dal caso reale in X"* costa una riga e rende visibile se X sia proprio la variabile in esame. Nel caso osservato, X era **chi possiede la sessione**, cioè esattamente l'oggetto della domanda.

## 22. Separare test e produzione: un gate, non un default

Generalizzato da una ricognizione su nove progetti istanziati o affiancati al template, che separano test e produzione in modi diversissimi e quasi sempre adatti al proprio caso: due progetti gemelli su una piattaforma gestita con anteprime per ogni richiesta di modifica, una branch di staging su una VPS, due stack di container sulla stessa macchina virtuale di cui uno acceso a richiesta, una macchina di staging interna davanti a una produzione che esegue soltanto immagini, un ERP con una branch per ambiente e una copia della base dati resa innocua, un'applicazione di terze parti che non ha altro ambiente che la produzione e ne ha diritto. Nessuna di queste forme è quella del template, e il template non ne raccomanda nessuna: il catalogo con i casi, i costi e i rischi osservati sta nella norma `skills/separazione-ambienti/RIFERIMENTO.md`, che è la fonte normativa e che qui non si duplica; la spiegazione tecnico-didattica di ogni forma, con trentasette fonti pubblicate registrate una per una, sta nel pacchetto `templates/separazione-ambienti/`, e la procedura dell'interazione nella skill `separazione-ambienti`. È il primo caso completo del principio della sezione 23.

Ciò che appartiene a questo documento è il principio, che è doppio. Il primo è che la separazione si compone di quattro scelte indipendenti, dove girano gli ambienti, come il codice passa dall'uno all'altro, da dove vengono i dati di prova e come stanno i sorgenti sulla macchina di chi sviluppa, e che le discussioni sbagliate nascono dal confonderle. Il secondo è che la scelta si fa al gate dell'inizializzazione e di ogni tornata di allineamento, come quella dei pacchetti: l'agente dichiara i fatti che osserva, pone le domande della regola, propone una combinazione legata a quei fatti, e l'esito si scrive nella scheda `context/deployment.md` e come ADR. In un progetto esistente il modello c'è quasi sempre già, anche se nessuno l'ha scritto, e il gate lo riconosce invece di sostituirlo.

Una delle scelte possibili, sull'asse dei sorgenti, è tenere più alberi di lavoro con `git worktree`, e merita una nota qui perché tocca il sistema di memoria e non solo la tecnica. Un sistema che versiona la memoria nel repository la paga con una proprietà che è la stessa guardata dall'altro lato: la memoria vale per la branch su cui è scritta, non per il progetto. Con un albero solo lo scarto non si vede; con due il progetto ha due memorie, e una sessione aperta sulla branch indietro legge per prima, come la sezione 12 le chiede, uno snapshot coerente ma vecchio. La norma `skills/alberi-di-lavoro/RIFERIMENTO.md` prescrive di leggere la memoria dall'albero della branch più avanti per percorso assoluto, senza copiarla né fonderla, e il presidio secondo la sezione 17 è doppio: l'avviso in testa al file di ripresa degli alberi secondari e il confronto con gli altri alberi dentro `tools/verifica-ripresa.py`. Lo stesso fenomeno si presenta, in forma più lieve, anche con un albero solo e una branch di staging condivisa, che cambia senza che la memoria di chi lavora su un ramo lo veda: per questo lo snapshot porta la riga degli ambienti con i commit di produzione e di staging sul remoto.

La generalizzazione vale per ogni progetto ed è una regola di redazione: ogni documento che descrive uno stato invece di una regola, cioè snapshot, registro delle decisioni, lavoro in corso, roadmap e work-log, dichiara in testa a quale commit e a quale branch si riferisce, e una scheda di ambienti distingue ciò che è in esercizio da ciò che è soltanto previsto. I documenti di regole degradano molto più lentamente di quelli di stato, e la prudenza giusta è proporzionata al ritmo con cui un documento invecchia, non uniforme.

## 23. Ogni capacità del template si raggiunge da un gate, e arriva spiegata

Principio enunciato dall'utente il 2026-09-23, mentre il template acquisiva il catalogo della separazione fra test e produzione, e generale: vale per ogni potenziamento, passato e futuro. Una capacità del template esiste, per chi avvia o allinea un progetto, soltanto se l'inizializzazione o l'allineamento gliela propongono, e gliela propongono in modo utile soltanto se spiegano quando conviene e che cosa comporta rispetto alle alternative. Una capacità che nessun gate nomina non viene adottata da nessuno, e questo è indistinguibile dall'averla esclusa di proposito; una capacità proposta senza spiegazione viene adottata o rifiutata per ragioni che nessuno saprà ricostruire, e la scelta verrà rifatta al primo incidente.

Ne discende una forma in tre parti, che il gate della separazione degli ambienti mostra per intero e che ogni capacità a scelta dovrebbe avere. La norma dice che cosa si sceglie e dove si registra, ed è una regola breve. La procedura conduce l'interazione: raccoglie i fatti prima di fare domande, dichiara che cosa ha riconosciuto perché l'utente possa correggerlo, propone legando la proposta ai fatti, e per ogni proposta spiega che cosa significa sceglierla invece dell'alternativa più vicina, che cosa richiede, che cosa costa e come fallisce, poi registra la scelta o il rinvio e chiude con il recap d'uso. La conoscenza è il documento da cui la procedura attinge le spiegazioni, con le fonti tracciate una per una, così che ciò che l'utente sente al gate e ciò che trova sul disco dopo sia la stessa cosa. Una capacità piccola può tenere le tre parti in un solo file, come fa ogni voce del catalogo dei pacchetti con le sue tre frasi; una capacità che comporta una scelta architetturale le tiene separate.

Il presidio, secondo la sezione 17, è doppio e dichiara che cosa non copre. `templates/tools/check-catalogo.py` verifica che ogni pacchetto abbia una voce nel catalogo che il gate dei pacchetti attraversa. `templates/tools/check-raggiungibilita.py` verifica che ogni regola e ogni skill siano nominate da almeno un punto d'ingresso, cioè dalla skill di inizializzazione, dai due prompt, dai gate, dal catalogo o dal modello del `CLAUDE.md`, salvo le capacità sempre attive, che non si scelgono e stanno in un elenco dichiarato con il motivo di ciascuna. Il giorno in cui è stato scritto ha trovato una lacuna reale: la skill `studio-didattico`, dichiaratamente opzionale, non era proposta da nessun gate. Nessuno dei due controlli giudica la qualità della spiegazione: distinguono il silenzio dalla presenza, e la spiegazione resta affidata a chi scrive il gate e a chi lo rilegge.

## 24. Il budget degli instruction file, e la differenza fra una regola e una skill

Generalizzato da un caso osservato il 2026-09-28 su questo stesso template, che all'apertura di ogni sessione avvisava di aver superato la soglia complessiva degli instruction file con 150.531 caratteri su 150.000. Il difetto non stava nella crescita dei file ma in un'affermazione falsa scritta in questo documento e ripetuta in undici regole, e vale la pena raccontarlo perché è l'archetipo di una politica dichiarata a parole che il meccanismo ignora.

Claude Code legge a ogni avvio, e concatena in contesto, il `CLAUDE.md` utente, quello di progetto, il `CLAUDE.local.md` e ogni file `.md` sotto `.claude/rules/`, trovato ricorsivamente anche nelle sottocartelle. La documentazione è esplicita: una regola senza frontmatter `paths:` viene caricata all'avvio con la stessa priorità del `CLAUDE.md` di progetto. Una soglia complessiva, oggi 150.000 caratteri, produce un avviso all'avvio e su `/status` quando la somma la supera, e ogni `CLAUDE.md`, ogni regola e ogni import `@path` conta come un file a sé. Nulla viene troncato: il solo taglio duro riguarda il singolo file oltre i 4 MiB, che viene saltato.

Il costo non è l'avviso, ed è per questo che il difetto è sopravvissuto mesi. Il primo termine è il contesto speso prima del primo messaggio, che nel caso osservato valeva circa un quarto di una finestra da duecentomila token, speso anche nelle sessioni in cui nessuna delle regole condizionali serviva. Il secondo è l'aderenza, che la documentazione lega direttamente alla dimensione: file più corti producono aderenza migliore, e undici norme sempre presenti competono fra loro per l'attenzione. Tenere tutto sempre attivo non è la scelta prudente che sembra, è il modo in cui ciascuna norma pesa meno.

Ne discende la distinzione fra i due livelli, che è di costo e non di forma. Una regola sotto `.claude/rules/` è una norma che si paga in ogni sessione, quindi vi appartiene soltanto ciò che vale in ogni sessione. Una norma che vale in certe situazioni vive come `RIFERIMENTO.md` dentro la skill che la governa, e si carica quando la situazione si presenta. Il criterio che separa i due casi è verificabile e non discrezionale: una norma resta sempre attiva quando la sua applicabilità non dipende da una scelta di configurazione del progetto. Lo stile di scrittura vale sempre; la norma sugli alberi di lavoro vale solo dove il gate della sezione 22 ha scelto la forma L2.

La scelta ha un costo dichiarato e va conosciuta. Una skill si carica sul giudizio del modello, una regola no, e dopo una compattazione i due livelli si comportano in modo diverso: il `CLAUDE.md` di radice e le regole senza `paths:` vengono re-iniettati da disco, mentre il corpo di una skill invocata rientra con un tetto per skill e complessivo, i più vecchi scartati per primi. La contromisura è l'indice degli inneschi nel `CLAUDE.md`, una riga per norma su richiesta, che nomina la situazione con le parole con cui si presenta invece del nome del file: costa poco più di un migliaio di caratteri e sta nel livello che sopravvive, quindi il giudizio non deve indovinare che la norma esista, deve solo seguire un puntatore. Il frontmatter `paths:` resta la terza via, adatta a una norma davvero legata a un'estensione, con il limite che scatta sulle letture di file corrispondenti e non sulle scritture.

Il budget vale per il progetto istanziato quanto per il template, e anzi vale di più, perché i pacchetti opzionali portano regole che atterrano in `.claude/rules/` di chi li adotta: nel caso osservato sei pacchetti valevano insieme 30.795 caratteri, che un progetto avrebbe accumulato senza scriverne una propria. Per questo il catalogo dichiara il costo di ciascuno, il gate dei pacchetti lo conta invece di scoprirlo, e la misura diventa un controllo secondo la sezione 17: `templates/tools/misura-istruzioni.py` somma ciò che viene davvero caricato, lo elenca dal più pesante, distingue la parte di progetto da quella utente che nessun commit controlla, e fallisce oltre la soglia di guardia come passo di `pre-commit`.

---

[^1]: *Skill* - workflow richiamabile descritto in un file `SKILL.md`, che incapsula istruzioni operative e comandi pre-eseguiti il cui output viene iniettato nel contesto.
[^2]: *MCP*, Model Context Protocol - protocollo per collegare a Claude server esterni che espongono strumenti e dati; configurato in `.mcp.json`.
[^3]: *Drift* - divergenza accumulata tra ciò che un documento descrive e lo stato attuale del codice.
[^4]: *YAML*, YAML Ain't Markup Language - formato di serializzazione leggibile usato qui per il blocco di metadati in testa ai documenti.
[^5]: *Glob* - sintassi di pattern per percorsi di file, dove ad esempio `**` indica una qualsiasi profondità di sottocartelle.
[^6]: *TBC*, to be confirmed - marcatore che segnala un punto del documento ancora da confermare.
[^7]: *SMTP*, Simple Mail Transfer Protocol - protocollo di invio della posta; le sue credenziali sono un segreto da non committare.
[^8]: *MMD*, estensione dei file Mermaid - sorgente testuale da cui si genera un diagramma.
[^9]: *ADR*, Architecture Decision Record - voce numerata che registra una singola decisione architetturale; nella forma *lite* tiene solo contesto, decisione, motivazione e conseguenze.
[^10]: *POSIX*, Portable Operating System Interface - famiglia di standard che definisce l'interfaccia delle shell e degli strumenti di tipo Unix; uno script POSIX gira su Linux e macOS.
