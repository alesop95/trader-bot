# <nome progetto>

> Istruzioni di team, versionate. Questo file è l'indice del progetto: indicizza i soli file satellite tracciati e descrive la procedura di ripresa. Le preferenze personali vivono in `CLAUDE.local.md`, ignorato da git, non qui.

## Cos'è questo progetto

<una o due frasi che descrivono lo scopo del progetto; popolare in fase di adozione, non inventare>

## Procedura di ripresa in una sessione nuova

Lo stato del progetto è interamente recuperabile su disco. All'inizio di una sessione si esegue `python tools/sync-codex-skills.py --check`, che controlla che Claude Code e Codex scoprano le stesse skill, poi si segue il percorso fisso che comincia con una verifica e non con una lettura: la skill `riprendi` esegue `tools/verifica-ripresa.py`, che confronta l'impronta registrata alla chiusura precedente con lo stato reale di git e dice che cosa una sessione caduta a metà non ha scritto. Solo dopo si legge `.claude/memory/index.md`, che dà branch, commit di riferimento, stato di verifica di ogni scheda e punto di ripresa. Se il progetto usa più alberi di lavoro, la memoria vale per la branch su cui è scritta: quando la verifica segnala un albero con la memoria più avanti, `index.md`, `progress.md` e `decisions.md` si leggono da quell'albero per percorso assoluto, senza copiarli né fonderli qui, come prescrive `.claude/skills/alberi-di-lavoro/RIFERIMENTO.md`. Si legge poi `.claude/context/current-work.md` se c'è una feature attiva, per sapere cosa è in lavorazione e quali sono i TODO e i limiti d'ambiente. Si invoca la skill `sync-context` per verificare il drift tra schede e codice, e si leggono solo le schede pertinenti al task, mai tutte insieme. Il work-log `.claude/memory/progress.md` e il registro `.claude/memory/decisions.md` forniscono la storia e le decisioni quando servono. Il materiale grezzo sotto `_notes/` si apre solo per verificare un requisito originale. Per una ripresa rapida esiste, quando presente, `_notes/RESUME-PROMPT.md`, privato e ignorato: riporta lo stato raggiunto e un prompt pronto da incollare. Va aggiornato alla fine di ogni sessione con il punto in cui si e arrivati, mentre lo stato canonico resta `.claude/memory/index.md`. Nello stesso momento l'agente scrive in `_notes/COMMIT-MSG.txt` il messaggio di commit proposto, una riga di al massimo 72 caratteri, e la chiusura la esegue l'utente con `tools/chiudi-sessione.ps1` dopo aver chiuso la sessione. Lo stesso vale per ogni milestone a metà sessione: a blocco concluso l'agente scrive il messaggio e propone `chiudi`, una milestone per commit, secondo la sezione "Milestone" di `.claude/rules/git-commands-format.md`.

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

Regole sempre attive, sotto `.claude/rules/`, e skill canoniche richiamabili, sotto `.claude/skills/`. La distinzione fra i due livelli non è di forma ma di costo, e va conosciuta prima di aggiungere una regola: ogni file `.md` sotto `.claude/rules/` senza frontmatter `paths:` entra in contesto a ogni sessione e concorre al budget degli instruction file, mentre una skill si carica quando serve. Una norma che vale solo in certe situazioni vive quindi come `RIFERIMENTO.md` dentro la propria skill, e l'indice qui sotto dice quando invocarla. Lo strumento `tools/misura-istruzioni.py` misura il carico e fallisce oltre la soglia. Codex scopre le skill attraverso adapter sottili sotto `.agents/skills/`, che rimandano alla fonte canonica senza duplicarla. Lo standard di sistema completo è in `.claude/PROJECT-SYSTEM.md`.

Norme caricate su richiesta, una riga per situazione con le parole con cui si presenta, così che il caricamento non dipenda dal ricordare che la norma esista. Si tolgono le righe delle skill che questo progetto non ha istanziato.

- Si scrive o si valuta una prova automatica, si chiude un difetto, una verifica manuale smentisce una suite verde, si sta per dichiarare completo un intervento il cui scopo era un effetto misurabile: skill `prove-che-misurano`.
- Un recupero web fallisce con 403 o con una pagina di verifica anti-bot, la fonte sta su Reddit o su Discord, serve la trascrizione di un video, si sta per annotare una fonte non letta: skill `fonti-non-recuperabili`.
- `git worktree list` mostra più di un albero, se ne crea o se ne rimuove uno, si deve decidere da dove leggere la memoria versionata: skill `alberi-di-lavoro`.
- Si inizializza o si allinea il progetto, oppure cambia il modo in cui si prova e si rilascia, e va deciso come separare test e produzione: skill `separazione-ambienti`.

## Apprendimenti recenti

Voci brevi e datate per le decisioni e le scoperte operative che non hanno ancora una casa definitiva: un comando che funziona diversamente da come documentato, un gotcha dell'ambiente, una scelta presa al volo. La voce nasce qui e migra appena possibile nella sede propria, `memory/decisions.md` se è una decisione architetturale, la scheda di contesto pertinente se è conoscenza strutturale, e si cancella da qui una volta migrata: questa sezione è un buffer, non un archivio.

```
- [<YYYY-MM-DD>] <decisione o scoperta, una riga>
```

## Vincoli di team

Le operazioni di `git add`, commit e push restano sempre manuali dell'utente: l'agente prepara i file, non committa. L'identità git è impostata a livello locale del repo secondo `.claude/rules/git-identity-and-repo.md`. Lo stile di documentazione e di interazione è quello di `.claude/rules/interaction-style.md`, la cui sezione "Formattazione dei file Markdown" vincola anche la forma dei file `.md`: paragrafi su una riga sorgente continua, senza a capo manuali a metà frase. Dove è istanziato lo strumento `tools/md-unwrap.py` la convenzione si attua eseguendolo sul file appena scritto, e si verifica prima di un commit con `python tools/md-unwrap.py --check .`. Claude aggiorna i file di memoria e di contesto in automatico a ogni giro di lavoro sostanziale, senza attendere una richiesta, secondo `.claude/rules/chat-non-e-memoria.md`; il versionamento resta sotto controllo umano perché commit e push sono manuali.
