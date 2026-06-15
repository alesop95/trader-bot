# Sistema di progetto portabile per Claude Code

> File unico, astratto e portabile. Descrive il sistema di contesto, documentazione e version control da installare in un progetto, e funge da runbook per il comando di inizializzazione. È distillato da una implementazione reale di riferimento ma non vi è accoppiato: ogni nome di progetto, stack o integrazione citato è esemplificativo. Per riusarlo altrove si copia questo file nella radice del nuovo progetto e si esegue la sezione *Comando di inizializzazione*.

Questo documento è scritto nello stile della documentazione tecnica adottato dal progetto: prosa discorsiva, niente elenchi puntati, niente emoji, acronimi spiegati in note a piè di pagina numerate, termini chiave in corsivo, frammenti di codice e configurazione in blocchi monospazio, alberi del filesystem mantenuti come blocchi preformattati.

---

## 1. Scopo e filosofia

L'obiettivo è disporre di una base di conoscenza che si aggiorna a ogni avanzamento dello sviluppo, tale che lo stato del progetto sia interamente recuperabile in qualsiasi momento e da chiunque cloni il repository. La sessione di chat è effimera e va persa alla chiusura; ciò che persiste è il contesto strutturale su disco, riletto automaticamente all'apertura della sessione successiva nella stessa directory. Il sistema fa in modo che ogni passo di codice, e anche ogni intervento manuale, lasci una traccia versionata e riconciliata, senza che questo costi una rilettura integrale dei documenti ogni volta.

La cartella `.claude/` è il centro di controllo del progetto, ma va tenuta all'essenziale.
La maggior parte delle attività quotidiane si gestisce con regole modulari e comandi diretti, senza generare ulteriore struttura. Una *skill*[^1] dedicata si introduce solo quando serve governare una procedura complessa o ripetibile, come un ciclo di deploy, un processo di sicurezza o uno standard avanzato di sviluppo. Per le attività incrementali bastano i comandi e le regole locali. Quando si parte da zero su uno stack noto, conviene partire da skill già predisposte come pacchetti di conoscenza per quel framework, invece di riscrivere tutto. Una skill e un server MCP non sono la stessa cosa: la skill è un workflow locale, fatto di file dentro il progetto, riusabile e versionato col repository; un server MCP è un servizio in rete, tipicamente condiviso tra più persone e agenti con permessi e autenticazione, che espone tool, risorse e prompt. Si sceglie la skill per i flussi di lavoro propri e locali, l'MCP per integrare servizi esterni condivisi.

Ogni nuova feature segue lo stesso ciclo: si descrivono gli obiettivi in modo chiaro, si
produce un piano, si analizzano pro e contro con i relativi metodi di mitigazione, si
risolvono le incertezze con domande mirate prima di scrivere codice, e solo allora l'agente implementa. A feature completata si genera un documento markdown permanente che fissa la logica implementata, le scelte architetturali e il contesto operativo, così da costituire memoria tecnica per il futuro. Questo ciclo è la ragione per cui il sistema documentale e il sistema di riconciliazione descritti sotto esistono.

---

## 2. Anatomia canonica della cartella `.claude`

Claude Code, all'apertura di una sessione in una directory di progetto, rilegge automaticamente alcuni file. Sono letti sempre `CLAUDE.md` nella radice, come  istruzioni di progetto condivise, `CLAUDE.local.md`, come override personali ignorati da git, e i file di memoria sotto `.claude/memory/` come contesto aggiuntivo. Vengono inoltre caricati secondo necessità i file in `.claude/rules/`, `.claude/skills/`, `.claude/agents/`, i comandi in`.claude/commands/`, le configurazioni in `.claude/settings.json` e `settings.local.json`, ed eventualmente `.mcp.json` per un server MCP[^2]. L'auto-discovery di alcune sottocartelle non è garantito in ogni contesto, quindi nel `CLAUDE.md` principale conviene includere riferimenti espliciti ai file satellite, così che vengano caricati comunque. Il `CLAUDE.md` indicizza soltanto i satelliti tracciati e non punta mai a file sotto `_notes/` o ad altro materiale locale o ignorato; quando un file referenziato diventa locale, o viene rimosso o rinominato, il suo puntatore va tolto dal `CLAUDE.md`, così che l'indice resti pulito e non rimandi a percorsi inesistenti.

La struttura di riferimento, da adottare nella forma minima e da estendere solo quando la complessità lo richiede, è la seguente.

```
your-project/
├── CLAUDE.md                  istruzioni di team, versionato; indicizza i satelliti
├── CLAUDE.local.md            override personali, ignorato da git
├── .mcp.json                  (opzionale) configurazione di un server MCP
├── _notes/                    livello privato e verboso, ignorato da git
│   ├── DIARIO.md              log cronologico personale degli interventi
│   ├── RESOCONTO.md           sintesi narrativa estesa
│   ├── TEST-CHECKLIST.md      checklist operativa locale di test manuali e non
│   └── .tmp-docx-*/           estratti temporanei dei .docx, scratch
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

Il `CLAUDE.md` è il meccanismo principale di persistenza condivisa, e può essere aggiornato in prompt successivi nel corso delle sessioni. Distingue le direttive di team dalle preferenze personali, che vivono in `CLAUDE.local.md`, ignorato da git; lo stesso principio separa `settings.json` da `settings.local.json`. Le sottocartelle `commands`, `rules`, `skills` e`agents` rappresentano livelli distinti di orchestrazione: i comandi espongono endpoint semantici come `/project:review`, le regole definiscono normative interne modulari, le skill incapsulano workflow automatizzati e gli agent definiscono personae operative. Claude non scrive autonomamente nei file di memoria e di contesto: è l'utente, o l'agente su richiesta esplicita, ad aggiornarli, così che il versionamento resti sotto controllo umano.

Una precisazione che evita un errore architetturale ricorrente: `.mcp.json` e l'eventuale cartella `mcp/` con l'implementazione dei server vivono nella radice del progetto, allo stesso livello del codice e di `.claude`, non sotto `.claude`. La cartella `.claude` è un namespace riservato al comportamento dell'agente, non è il luogo da cui si dichiarano i tool esterni, e Claude Code effettua la discovery dei server MCP esclusivamente dal `.mcp.json` di radice. La cartella `.claude` va inoltre versionata col repository, perché è configurazione deterministica dell'agente e non materiale locale o effimero.

---

## 3. I due livelli documentali e la mappa ibrida

Il sistema separa due livelli con trattamento git diverso. Il principio che governa la
ripartizione è uno solo: un documento è *tracciato* se è conoscenza tecnica che un qualsiasi contributore deve poter recuperare o revisionare da un clone ed è sicuro pubblicarlo; resta in `_notes/` *ignorato* se è narrativa personale, materiale transitorio di lavorazione, oppure contenuto operativamente sensibile. Questo risolve il requisito di recuperabilità totale, perché tutto ciò che serve a ricostruire lo stato finisce nei commit, mentre nel locale resta solo il rumore. Il modello è ibrido per documento, non per cartella: la collocazione di un file si decide applicando il principio, e la mappa risultante è fissata qui sotto.

Sono tracciati, perché costituiscono lo stato recuperabile e revisionabile, il `CLAUDE.md`
come indice di progetto, `context/roadmap.md`, `memory/decisions.md` con le decisioni
architetturali, `memory/index.md` come snapshot e procedura di ripresa, `memory/progress.md`come work-log append-only, `context/current-work.md` per la feature attiva, le skill e i comandi sotto `.claude/`, e i diagrammi sotto `context/diagrams/` in corrispondenza uno a uno con le schede. Sono tracciate inoltre le schede tecniche strutturali, che portano il frontmatter di riconciliazione descritto nella sezione 4: `STACK.md` con stack e le alternative deliberatamente escluse per evitare deriva tecnologica, flussi di codice e riferimenti a snippet e ruolo architetturale dei file, `design-and-security.md` con i paradigmi di software design e di sicurezza applicativa, `deployment.md` con i livelli di test e produzione e i relativi comandi, e `dev-testing.md` con i test di sviluppo. 

Sono ignorati, in `_notes/`, perché personali, narrativi o transitori, `DIARIO.md` come log cronologico verboso degli interventi, `RESOCONTO.md` come sintesi narrativa estesa,
`TEST-CHECKLIST.md` come checklist operativa locale di test manuali e automatici, i `.docx`grezzi e gli estratti temporanei `.tmp-docx-*` salvo le eccezioni curate dichiarate nel `.gitignore`. 

Due scelte si discostano da una collocazione puramente privata e vanno tenute presenti. Lo `STACK.md` è il documento di recupero più importante e va tracciato, non confinato nel locale, perché un collega che clona deve vederlo. Il work-log di ingestione dei `.docx`, con le date di riconciliazione, non va in un file ignorato a parte ma confluisce in `memory/progress.md` tracciato, così che la data di allineamento sopravviva a un clone e non si duplichi il log.

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

La logica di verifica, incapsulata in una skill, per ciascuna scheda legge
`last-verified-commit` e `covers-paths`, esegue il confronto `git diff --name-only
<last-verified-commit>..HEAD` ristretto ai `covers-paths`, e classifica la scheda. È
*aggiornata* se nessun file coperto è cambiato. È *stale* se almeno un file coperto è cambiato, e in tal caso la skill propone un edit chirurgico della sola sezione impattata, senza rigenerare il documento. È *obsoleta* se i cambiamenti includono rinominazioni o rimozioni di moduli interi, o se la scheda cita simboli o file che non esistono più, caso che richiede una rilettura più approfondita e non un semplice aggiornamento del frontmatter. La skill non esegue mai operazioni di scrittura su git e non rigenera i documenti da zero: si limita a leggere e proporre. Quando lo stato di tutte le schede coincide con `HEAD`, la risposta è un singolo messaggio di allineamento, senza azioni.

A ogni passo significativo di codice, e a ogni intervento manuale rilevante, si aggiornano le schede impattate, si porta `last-verified-commit` al nuovo commit, si aggiorna lo snapshot in `memory/index.md` e si appende una voce a `memory/progress.md` con data, file toccati, motivo e commit di riferimento, in ordine cronologico inverso. Il file `memory/index.md` è quello da leggere per primo a inizio sessione: contiene il branch attivo, il commit di riferimento, la tabella che mappa ogni scheda al suo stato di verifica, e il punto di ripresa, dichiarato come una riga di prossima azione concreta che dice da dove ricominciare. Il file `current-work.md` tiene la feature in corso, con una riga di stato nel frontmatter, le definition of done a spunte, le domande aperte risolte in loco e un marcatore di riconciliazione datato, con l'avvertenza esplicita che la fonte di verità su cosa sia fatto resta `memory/index.md` e il log, non le spunte del diario. 

Il registro `memory/decisions.md` segue la convenzione *ADR-lite*[^9] append-only. Ogni decisione architetturale non ovvia entra come voce numerata, ad esempio `ADR-007`, con data, stato, contesto, decisione presa, motivazione e conseguenze. Una decisione non si cancella e non si riscrive: quando viene superata, si aggiunge una nuova voce che dichiara di superare la precedente e ne cita il numero, così la storia del ragionamento resta leggibile. Le inferenze non ancora confermate si marcano esplicitamente come da verificare, e si promuovono a decisione solo quando una fonte le conferma.

Ogni feature in `current-work.md` si descrive con uno schema fisso, cosa fa, i file da creare, i file da modificare, la checklist di completamento e uno stato esplicito, così che il lavoro pendente sia leggibile senza dover ricostruire il contesto da capo.

---

## 5. Ingestione di documenti `.docx` voluminosi

Quando arriva un documento di contesto voluminoso, tipicamente un `.docx`, la regola è non leggerlo mai per intero, perché brucerebbe contesto inutilmente. La strategia riusabile è estrarne il contenuto su disco una sola volta, in una cartella scratch ignorata da git come`_notes/.tmp-docx-<nome>/`, e poi caricare in lettura solo le porzioni mirate al task corrente, on demand.

Sui documenti di contesto si trovano spesso marcatori del tipo `[TBC]`[^6], che indicano punti da confermare. Questi marcatori vanno estratti temporaneamente su disco e confrontati con l'elenco di ciò che le schede `.md` già coprono, così da capire cosa manca davvero senza rileggere il documento intero. Se le schede risultano già allineate a quel documento, non serve rileggerle né modificarle: si registra soltanto la data di riconciliazione. La data di riconciliazione si annota sempre, sia quando si è prodotto un aggiornamento sia quando si è solo verificato l'allineamento, e va in `memory/progress.md`, accompagnata dal nome del documento sorgente e dall'esito. Le schede che derivano da un documento sorgente ne citano il percorso nel frontmatter, in un campo `source-doc`, così che il legame resti tracciabile. Questa stessa strategia va annotata nel work-log la prima volta che si applica, perché diventi
patrimonio del progetto e non vada ricostruita a ogni ingestione.

Esiste anche la direzione inversa, complementare a questa. Quando serve consegnare un deliverable in formato Word, conviene generarlo dallo stato del repository tramite uno script, integrando nel documento gli snippet dei file chiave e le voci di decisione, invece di mantenerlo a mano. Così il documento Word resta allineato al codice e si rigenera a comando, e il `.docx` prodotto resta ignorato da git come ogni binario derivato.

Quando invece è il documento Word a essere la fonte di verità umana, conviene la direzione inversa, da `.docx` a `.md`: uno script genera un mirror Markdown del Word, versionato accanto a esso, che rende leggibili i diff in git mentre il Word resta il documento che si modifica a mano. E per non rileggere ogni volta un documento sorgente che non è cambiato, si tiene un piccolo manifesto che ne registra l'impronta, ad esempio hash e data di modifica, e si rilegge solo ciò che l'impronta segnala come nuovo o modificato.

---

## 6. Igiene del version control e scansione segreti

Il sistema impone alcune regole di version control. La cartella `_notes/` è ignorata, e va
inserita nel `.gitignore` prima di crearla, altrimenti finisce indicizzata. Le operazioni di
`git add`, commit e push restano sempre in mano all'utente; l'agente prepara, non committa.

Prima di considerare sano un repository va verificato che non siano rimasti indicizzati file non tracciati per errore, e soprattutto che non siano mai stati committati segreti. La
scansione dei segreti deve coprire i file tracciati e l'intera storia dei commit, e cercare
almeno chiavi private, stringhe di connessione con credenziali, password SMTP[^7], token di firma e file di service account. Il controllo tipico verifica se un file `.env` o equivalente sia mai entrato nella storia, anche se in seguito rimosso, perché la rimozione dal working tree non lo cancella dalla storia e il contenuto resta recuperabile da chiunque abbia accesso al remoto.

Quando un segreto risulta trapelato nella storia, l'unica azione che neutralizza davvero
l'esposizione, indipendentemente dalla storia git, è la rotazione del segreto stesso: cambiare la password, rigenerare la chiave, invalidare il token. La riscrittura della storia con uno strumento dedicato è possibile ma confligge con la regola di non riscrivere la storia di branch condivisi e impone un force-push coordinato di tutto il team, quindi va trattata come decisione di team, secondaria rispetto alla rotazione, mai eseguita unilateralmente su `staging` o sul branch stabile.

Distinto dalla scansione segreti, ma parte della stessa igiene, c'e il problema dell'identita con cui si firmano i commit. Su una macchina che ospita piu identita, tipicamente una di lavoro e una personale, il rischio e committare un progetto con l'email sbagliata. La regola del sistema e impostare sempre l'identita a livello locale di repository, con la coppia `user.name` e `user.email` e l'alias SSH corretto, e abilitare a livello globale `user.useConfigOnly` perche git rifiuti il commit dove l'identita locale non e stata impostata. La procedura completa, con i profili disponibili, il bootstrap del remoto via alias SSH e il caso del repository remoto gia inizializzato con README, vive in una regola dedicata, `.claude/rules/git-identity-and-repo.md`. Anche qui commit e push restano sempre manuali dell'utente.

---

## 7. Disciplina dei diagrammi

I flussi applicativi e i pattern architetturali vanno rappresentati con mappe versionate sotto`context/diagrams/`, in formato `.svg` per la versione resa e con il sorgente accanto quando il diagramma è generato da testo, ad esempio in `.mmd`[^8]. Ogni diagramma è registrato in una tabella dentro la scheda che lo riferisce, e il vincolo non negoziabile è la corrispondenza uno a uno: ogni componente disegnato deve esistere nella mappa testuale registrata e viceversa, così che il diagramma non diverga mai dal codice descritto. Quando un flusso cambia, il diagramma e la scheda si aggiornano insieme, nello stesso passo che bumpa `last-verified-commit`.

---

## 8. Stile della documentazione tecnica

La documentazione si rivolge a un lettore tecnico esperto e va scritta come ci si rivolgerebbe a un responsabile tecnico: diretta, chiara, esaustiva, senza ridondanza. L'impianto è discorsivo: i concetti vengono prima inquadrati architetturalmente, poi approfonditi con estratti di codice annotati, infine collegati ai flussi attraverso paragrafi di raccordo. Non si usano elenchi puntati né emoji né grassetto nella prosa. Gli acronimi si spiegano in note a piè di pagina numerate, per non interrompere il discorso con parentesi inline. I termini chiave densi si marcano in corsivo, le keyword di codice nei blocchi sintattici in grassetto, e i frammenti di codice e configurazione stanno in blocchi monospazio. Gli alberi del filesystem si mantengono come blocchi preformattati con indentazione. Non si usano i trattini lunghi; sono ammessi solo i
trattini brevi. Non si presenta mai come fatto un contenuto inferito, speculativo o non
verificato: ciò che non è verificabile va etichettato come tale, e ciò che non si conosce va dichiarato invece di essere riempito per ipotesi. Si preferisce spiegare una cosa una volta sola, in modo descrittivo, senza dare per scontato nemmeno il semplice.

Questo stesso stile conviene codificarlo in un file di regola, `.claude/rules/interaction-style.md`, così da caricarlo on demand e renderlo vincolante per ogni sessione invece di affidarlo alla memoria.

---

## 9. Workflow di feature

Una feature non parte dal codice. Parte da una descrizione chiara degli obiettivi, seguita da un piano, da un'analisi dei pro e dei contro con i metodi di mitigazione, e dalla risoluzione delle incertezze tramite domande mirate poste prima dell'implementazione, così da arrivare all'esecuzione con un piano rifinito. Questo ciclo si riassume in cinque momenti ripetibili e indipendenti dalla sessione: pianificare, eseguire, documentare, tracciare nel work-log, verificare; nessuno step si considera chiuso finché documentazione e tracciamento non sono allineati al codice. Durante lo sviluppo si lavora su un branch di feature, si prova la modifica eseguendo l'applicazione, e prima del commit si eseguono i controlli di qualità del progetto, tipicamente lint e build. A feature completata si genera un documento markdown
permanente che fissa la logica implementata, le scelte architetturali e il contesto operativo, si consolidano nelle schede strutturali le parti rilevanti emerse dal `current-work.md`, si aggiorna il work-log e si bumpano i `last-verified-commit`.

Le parti del diario relative alla feature chiusa si archiviano.

Una skill dedicata si introduce solo se la feature comporta una procedura complessa o ripetibile; per il lavoro incrementale bastano i comandi e le regole. Su progetti con un ciclo lungo conviene strutturare il lavoro per fasi numerate, dove ogni fase si apre con una spiegazione discorsiva degli obiettivi, attende la conferma esplicita prima di scrivere codice, e si chiude con un riepilogo standardizzato che aggiorna il work-log. Questo ciclo si può irrobustire con strumenti dedicati: una skill che chiude la fase producendo il recap, un comando che apre la fase successiva e funge da cancello prima dell'implementazione, un comando che aggiunge una voce di decisione, e un agente guardiano che verifica gli invarianti del progetto. Le procedure ripetibili e generative, come scaffoldare insieme codice, schema e test per un nuovo endpoint o una nuova tabella, sono il caso d'uso tipico di una skill; le revisioni specializzate, di sicurezza o di audit, sono il caso d'uso tipico di un agente dedicato.

---

## 10. Comando di inizializzazione

L'inizializzazione installa il sistema in un progetto nuovo o lo allinea in uno esistente.
Quando questo file è presente nella radice e l'utente invoca il comando di  inizializzazione, l'agente esegue, nell'ordine, i passi seguenti, fermandosi a chiedere conferma dove un'azione è difficilmente reversibile o tocca il version control.

Quando il bundle portabile include una cartella `templates/` con gli scheletri canonici dell'anatomia, ovvero `CLAUDE.md`, `CLAUDE.local.md`, `settings.json`, lo snippet di `.gitignore`, i file di `memory/`, le schede di `context/`, i file di `_notes/` e, opzionalmente, `.mcp.json`, i passi che creano file li istanziano da quei template sostituendo i segnaposto tra parentesi angolari, invece di rigenerarne il contenuto a memoria. La mappa di istanziazione, con la collocazione e lo stato git di ciascun file, vive in `templates/README.md`. In assenza della cartella `templates/`, i file si ricostruiscono dalla descrizione di questa sezione e della sezione 2.

Primo, verifica il version control secondo la sezione 6: scansiona file tracciati e storia alla ricerca di segreti, individua file indicizzati per errore, e riporta gli esiti senza committare. Subito dopo sceglie con l'utente l'identita git con cui verranno firmati i commit e a quale repository agganciare il remoto, e la configura a livello locale del repo secondo `.claude/rules/git-identity-and-repo.md`, senza mai committare ne pushare.

Secondo, predispone il `.gitignore` aggiungendo le esclusioni del livello privato, almeno `_notes/`, `CLAUDE.local.md`, `.claude/settings.local.json`, i `.docx` grezzi con le eventuali eccezioni curate, e le cartelle scratch `.tmp-docx-*`.

Terzo, crea l'anatomia di `.claude`descritta nella sezione 2 nella forma minima: `settings.json` con una whitelist minima di permessi allow/deny e le variabili di progetto utili come nome e fase, le cartelle `commands`, `rules`, `skills`, `agents`, la cartella `memory` con `index.md`, `progress.md` e `decisions.md`, e la cartella `context` con le schede `STACK.md`, `design-and-security.md`, `deployment.md`, `dev-testing.md`, `current-work.md`, `roadmap.md` e la sottocartella `diagrams`.

Quarto, crea o aggiorna `CLAUDE.md` nella radice in modo che indicizzi esplicitamente i soli file satellite tracciati, senza puntatori a materiale in `_notes/` o locale, e contenga la procedura di ripresa della sezione 12. Accanto a esso crea, se non esiste, uno stub di `CLAUDE.local.md` per gli override personali, ignorato da git e mai indicizzato dal `CLAUDE.md` di team.

Quinto, crea la cartella `_notes` con `DIARIO.md`, `RESOCONTO.md` e `TEST-CHECKLIST.md`, dopo aver confermato che `_notes` è ignorato.

Sesto, installa le skill del motore di riconciliazione e del flusso git, ciascuna come
`SKILL.md` dentro la propria cartella sotto `.claude/skills`.

Settimo, popola le schede di `context` con il frontmatter di riconciliazione, ancorato al commit corrente, lasciando i `covers-paths` da affinare man mano che il codice viene mappato. Su un progetto greenfield appena inizializzato il commit corrente non esiste ancora, perché il primo commit è un'operazione manuale dell'utente che segue l'init: in quel caso i campi `generated-from-commit` e `last-verified-commit` si lasciano a un segnaposto esplicito, ad esempio `PENDING-FIRST-COMMIT`, e si ancorano al primo commit reale subito dopo, eseguendo la skill di sincronizzazione che li porta a `HEAD`. Lo snapshot di `memory/index.md` riporta lo stesso segnaposto come commit di riferimento finché il primo commit non è stato creato.

Ottavo, scrive in`memory/progress.md` la prima voce, che registra l'inizializzazione del sistema e la data, e in`memory/index.md` lo snapshot iniziale. Le schede non vanno riempite di contenuto inventato in fase di init: si creano con la struttura e il frontmatter, e si popolano leggendo il codice nei passi successivi. Quando si parte da uno stack noto, in questo passo si possono installare skill già predisposte
come pacchetti di conoscenza per quel framework o per la piattaforma di deploy, invece di ricostruirle.

L'integrazione di un server MCP è un passo a parte e opzionale, da eseguire solo se il progetto deve collegarsi a un servizio esterno. In quel caso si creano nella radice del progetto, accanto a `.claude` e mai sotto di esso come stabilito nella sezione 2, il file `.mcp.json` istanziato dal template opzionale e la cartella `mcp/` con l'implementazione del server; entrambi sono tracciati. Diversamente non si creano, e il sistema resta a sole skill locali. La differenza di fondo è quella della sezione 1: la skill è un workflow locale versionato col repository, l'MCP è un servizio in rete, tipicamente condiviso, che Claude Code scopre esclusivamente dal `.mcp.json` di radice.

---

## 11. Adozione su un progetto esistente

Un progetto può avere già codice e una storia git lunga senza adottare questo sistema. L'obiettivo dell'adozione è allineare retroattivamente tracciamento e documentazione allo stesso standard, senza riscrivere la storia git e senza inventare contenuto. La differenza rispetto all'inizializzazione greenfield è che qui si parte da un repository popolato, quindi prima si rileva cosa esiste e poi si colma il divario in modo incrementale.

Il percorso è il seguente. Si fa un inventario di ciò che è già presente, la cartella `.claude/`, `CLAUDE.md`, eventuali documenti, il `.gitignore`, la configurazione di test e di integrazione continua, e lo si mappa contro l'anatomia canonica della sezione 2, segnalando i divari senza toccarli. Si esegue la scansione del version control e dei segreti della sezione 6, che qui pesa di più perché la storia è lunga e può contenere file `.env` rimossi ma ancora recuperabili. Si ricostruisce la memoria dalla storia: `memory/decisions.md` si popola rileggendo le decisioni implicite nei commit, ciascuna come voce ADR numerata, e `memory/progress.md` riassume le tappe già fatte senza inventare ciò che la storia non dimostra, mentre `memory/index.md` fotografa lo
stato al commit corrente. Si creano le schede di `context` con il frontmatter di riconciliazione ancorato al commit corrente e le si popola leggendo il codice attuale, non la storia, una alla volta a partire dalle aree più critiche, definendo i `covers-paths` sulle aree reali. Da quel punto `last-verified-commit` coincide con il commit corrente e il drift futuro si gestisce con la skill di sincronizzazione come in un progetto nato col sistema.

L'adozione è iterativa e va proposta, non imposta: nulla viene sovrascritto in silenzio, ogni passo che tocca git chiede conferma, e le schede si allineano poche alla volta invece di tutte insieme. Quando un documento esistente copre già un'area, lo si dota di frontmatter e lo si riconcilia invece di duplicarlo.

---

## 12. Procedura di ripresa in una sessione nuova

Lo stato del progetto è interamente recuperabile seguendo, all'inizio di una sessione, un percorso fisso. Si legge per primo `.claude/memory/index.md`, che dà branch, commit di riferimento, stato di verifica di ogni scheda e punto di ripresa. Si legge poi
`context/current-work.md` se c'è una feature attiva, per sapere cosa è in lavorazione e quali sono i TODO e i limiti d'ambiente. Si invoca la skill di sincronizzazione per verificare il drift tra schede e codice, e si leggono solo le schede pertinenti al task, mai tutte insieme. Il work-log `memory/progress.md` e il registro `memory/decisions.md` forniscono la storia e le decisioni quando servono. Il materiale grezzo sotto `_notes/` si apre solo per verificare un requisito originale. Questa sezione va replicata, in forma sintetica, dentro il `CLAUDE.md`principale, perché è lì che una sessione nuova la cerca per prima.

---

## 13. Bootstrap dell'ambiente di sviluppo

Lo stesso principio che governa i livelli documentali, versionare la fonte riproducibile e
ignorare ciò che ne deriva, si applica alla catena di strumenti. Si versiona il manifesto delle dipendenze e si ignora l'ambiente materializzato, perché il manifesto è riproducibile e leggero mentre l'ambiente è derivato e pesante. In un progetto Python questo significa versionare `requirements.txt` o `pyproject.toml` e ignorare la cartella `.venv`, gli `__pycache__`, i file `*.pyc` e gli artefatti di build; in un progetto Node lo stesso principio versiona `package.json`e ignora `node_modules`. Conviene fissare in modo esplicito la versione del runtime, perché un ambiente ricreato su una macchina con un interprete diverso è una fonte silenziosa di divergenze.

Per rendere il bootstrap riproducibile e a un solo comando si forniscono due script di setup paralleli, uno per Windows in PowerShell e uno POSIX[^10] per Unix, che individuano l'interprete corretto, creano l'ambiente, installano dal manifesto e verificano l'esito con un import minimo; gli script accettano un flag per ricreare l'ambiente da zero e uno per forzare il percorso dell'interprete. Un accorgimento utile è tenere la cartella dell'ambiente presente nel repository ma vuota, con al suo interno un `.gitignore` che esclude tutto: la struttura esiste già al clone, il contenuto resta fuori da git e viene ricreato dallo script. Gli script di pipeline invocano direttamente l'interprete dell'ambiente invece di richiedere l'attivazione interattiva della shell, così si comportano in modo identico in locale e in automazione.

---

## 14. Hook di automazione e guard-rail

La cartella `hooks/`, prevista nell'anatomia ma spesso lasciata vuota, ospita automazioni che trasformano procedure facili da dimenticare in comportamenti costanti. Tre famiglie si sono dimostrate utili.

La prima è un hook di apertura sessione che esegue uno script di ripresa:
stampa lo snapshot di `memory/index.md`, i file cambiati rispetto al commit di riferimento e la prossima azione concreta, così che la procedura di ripresa della sezione 12 diventi automatica invece che manuale.

La seconda è un hook di pre-commit che rende il `.gitignore` effettivamente
vincolante, de-tracciando i file già committati ma ora coperti da una regola di esclusione, in modo che artefatti o materiali aggiunti prima della regola non restino indicizzati; si installa indicando a git il percorso degli hook del repository, così viaggia col progetto.

La terza famiglia è un insieme di guard-rail attorno alle modifiche del codice: prima di creare un simbolo si verifica con una ricerca che non esista già, prima di modificare un file lo si legge per intero e se ne mappano i dipendenti, i file critici richiedono conferma esplicita prima di essere toccati, dopo ogni modifica si produce una checklist di verifica, e una modifica profonda si divide obbligatoriamente in micro-passi con conferma. 

Questi guard-rail si possono esprimere come istruzioni in una regola caricata sempre, oppure, dove il meccanismo lo consente, come hook che intercettano la chiamata allo strumento. Le automazioni che eseguono comandi vanno bilanciate con la whitelist di `settings.json`, che ammette esplicitamente solo le operazioni sicure e nega quelle distruttive o verso l'esterno, in particolare commit, push e deploy, coerentemente con la regola che queste restano sempre manuali.

---

[^1]: *Skill* — workflow richiamabile descritto in un file `SKILL.md`, che incapsula istruzioni
operative e comandi pre-eseguiti il cui output viene iniettato nel contesto.
[^2]: *MCP*, Model Context Protocol — protocollo per collegare a Claude server esterni che
espongono strumenti e dati; configurato in `.mcp.json`.
[^3]: *Drift* — divergenza accumulata tra ciò che un documento descrive e lo stato attuale del
codice.
[^4]: *YAML*, YAML Ain't Markup Language — formato di serializzazione leggibile usato qui per il
blocco di metadati in testa ai documenti.
[^5]: *Glob* — sintassi di pattern per percorsi di file, dove ad esempio `**` indica una
qualsiasi profondità di sottocartelle.
[^6]: *TBC*, to be confirmed — marcatore che segnala un punto del documento ancora da confermare.
[^7]: *SMTP*, Simple Mail Transfer Protocol — protocollo di invio della posta; le sue credenziali
sono un segreto da non committare.
[^8]: *MMD*, estensione dei file Mermaid — sorgente testuale da cui si genera un diagramma.
[^9]: *ADR*, Architecture Decision Record — voce numerata che registra una singola decisione
architetturale; nella forma *lite* tiene solo contesto, decisione, motivazione e conseguenze.
[^10]: *POSIX*, Portable Operating System Interface — famiglia di standard che definisce
l'interfaccia delle shell e degli strumenti di tipo Unix; uno script POSIX gira su Linux e macOS.
