# <nome progetto>

> Istruzioni di team, versionate. Questo file è l'indice del progetto: indicizza i soli file satellite tracciati e descrive la procedura di ripresa. Le preferenze personali vivono in `CLAUDE.local.md`, ignorato da git, non qui.

## Cos'è questo progetto

<una o due frasi che descrivono lo scopo del progetto; popolare in fase di adozione, non inventare>

## Procedura di ripresa in una sessione nuova

Lo stato del progetto è interamente recuperabile su disco, e il percorso per ritrovarlo sta in un posto solo: `.claude/skills/riprendi/SKILL.md`. A inizio sessione, prima di qualunque altro lavoro, la si esegue con `/riprendi` oppure leggendo quel file e seguendolo: verifica che il file di ripresa `_notes/RESUME-PROMPT.md` descriva davvero il presente, poi guida la lettura di `.claude/memory/index.md`, che resta lo stato canonico, della feature attiva e delle sole schede pertinenti. La chiusura, a fine sessione e a ogni milestone, segue la sezione "Milestone" di `.claude/rules/git-commands-format.md`: l'agente aggiorna il file di ripresa, scrive il messaggio in `_notes/COMMIT-MSG.txt` e propone `chiudi`, che l'utente lancia.

## Indice dei file satellite tracciati

Memoria e meta-stato, sotto `.claude/memory/`, letti sempre a inizio sessione.

```
.claude/memory/index.md       snapshot e tabella di sincronizzazione, da leggere per primo
.claude/memory/progress.md    work-log append-only di passi e riconciliazioni
.claude/memory/decisions.md   registro ADR-lite delle decisioni architetturali
```

Schede tecniche, sotto `.claude/context/`, con frontmatter di riconciliazione.

```
.claude/context/STACK.md                stack, flussi di codice, ruolo architetturale dei file
.claude/context/design-and-security.md  paradigmi di design e sicurezza applicativa
.claude/context/deployment.md           livelli test e produzione, alberi di lavoro, hosting, comandi
.claude/context/dev-testing.md          test di sviluppo, runner, rotte mockate, hook
.claude/context/current-work.md         feature attiva, definition of done, domande aperte
.claude/context/roadmap.md              direzione e priorità
```

Regole sempre attive, sotto `.claude/rules/`, e skill canoniche richiamabili, sotto `.claude/skills/`. La distinzione fra i due livelli non è di forma ma di costo, e va conosciuta prima di aggiungere una regola: ogni file `.md` sotto `.claude/rules/` senza frontmatter `paths:` entra in contesto a ogni sessione e concorre al budget degli instruction file, mentre una skill si carica quando serve. Una norma che vale solo in certe situazioni vive quindi come `RIFERIMENTO.md` dentro la propria skill, e l'indice qui sotto dice quando invocarla. Dentro una regola che vale sempre la divisione si ripete: la prescrizione resta nel file sempre attivo, il caso osservato che la giustifica sta in `.claude/norme/<stesso nome>.md`, che non si carica all'avvio e che il cappello della regola nomina. Lo strumento `tools/misura-istruzioni.py` misura il carico, fallisce oltre la soglia complessiva e oltre il tetto per singola regola. Codex scopre le skill attraverso adapter sottili sotto `.agents/skills/`, che rimandano alla fonte canonica senza duplicarla. Lo standard di sistema completo è in `.claude/PROJECT-SYSTEM.md`.

Norme caricate su richiesta, una riga per situazione con le parole con cui si presenta, così che il caricamento non dipenda dal ricordare che la norma esista. Si tolgono le righe delle skill che questo progetto non ha istanziato. Le skill, gli agenti e i comandi in sé non si elencano: l'ambiente li annuncia a ogni avvio con la loro descrizione, e una copia qui costa caratteri del budget e invecchia senza che nessuno se ne accorga. In un progetto istanziato una tabella di comandi copiata in questo file usava un prefisso d'invocazione superato da una versione dello strumento, `/project:review` per un comando che si invoca `/review`, e occupava i caratteri che mancavano a una riga necessaria (corretto il 2026-10-19). Questo indice nomina le situazioni, non i nomi.

- Si scrive o si valuta una prova automatica, si chiude un difetto, una verifica manuale smentisce una suite verde, si sta per dichiarare completo un intervento il cui scopo era un effetto misurabile: skill `prove-che-misurano`.
- Un recupero web fallisce con 403 o con una pagina di verifica anti-bot, la fonte sta su Reddit o su Discord, serve la trascrizione di un video, si sta per annotare una fonte non letta: skill `fonti-non-recuperabili`.
- `git worktree list` mostra più di un albero, se ne crea o se ne rimuove uno, si deve decidere da dove leggere la memoria versionata: skill `alberi-di-lavoro`.
- Si inizializza o si allinea il progetto, oppure cambia il modo in cui si prova e si rilascia, e va deciso come separare test e produzione: skill `separazione-ambienti`.
- Il progetto è un'applicazione da distribuire e si deve decidere se servono controlli al commit, CI dopo il push, prove del runtime o CD, anche una sola fase: skill `pipeline-app`, solo se istanziata al gate dei pacchetti.
- Va prodotto, modificato o convertito un artefatto visivo o documentale, cioè un documento, una presentazione, un PDF, un'immagine, un'animazione, un audio o un impaginato, oppure si sta per scrivere uno script o installare una libreria per farlo: skill `craft-apps`, che prima verifica in locale le applicazioni Craft installate e le usa senza rete né token.
- Si imposta o si verifica user.name e user.email, si collega o si cambia il remoto o l'alias SSH, si inizializza un repository, un push fallisce per permessi, `/status` mostra un account Claude diverso da quello atteso, si autentica o si usa `gh`: skill `identita-git`.

## Apprendimenti recenti

Voci brevi e datate per le decisioni e le scoperte operative che non hanno ancora una casa definitiva: un comando che funziona diversamente da come documentato, un gotcha dell'ambiente, una scelta presa al volo. La voce nasce qui e migra appena possibile nella sede propria, `memory/decisions.md` se è una decisione architetturale, la scheda di contesto pertinente se è conoscenza strutturale, e si cancella da qui una volta migrata: questa sezione è un buffer, non un archivio.

```
- [<YYYY-MM-DD>] <decisione o scoperta, una riga>
```

## Vincoli di team

Le operazioni di `git add`, commit e push restano sempre manuali dell'utente: l'agente prepara i file, non committa. L'identità git è impostata a livello locale del repo secondo la skill `identita-git`. Lo stile di documentazione e di interazione è quello di `.claude/rules/interaction-style.md`, la cui sezione "Formattazione dei file Markdown" vincola anche la forma dei file `.md`: paragrafi su una riga sorgente continua, senza a capo manuali a metà frase. Dove è istanziato lo strumento `tools/md-unwrap.py` la convenzione si attua eseguendolo sul file appena scritto, e si verifica prima di un commit con `python tools/md-unwrap.py --check .`. Claude aggiorna i file di memoria e di contesto in automatico a ogni giro di lavoro sostanziale, senza attendere una richiesta, secondo `.claude/rules/chat-non-e-memoria.md`; il versionamento resta sotto controllo umano perché commit e push sono manuali.
