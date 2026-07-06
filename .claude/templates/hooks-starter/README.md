# Pacchetto hooks-starter

> Pacchetto opzionale del sistema di progetto. Fornisce tre hook di automazione pronti all'uso, in doppia forma PowerShell e shell POSIX, che concretizzano le famiglie descritte nella sezione 14 di `PROJECT-SYSTEM.md`, finora solo descrittiva: un hook di apertura sessione che automatizza la procedura di ripresa, un hook che protegge i file sensibili dalle scritture dell'agente, e un hook che scansiona i secret nel diff in stage prima di un commit. Nessun hook e' attivo dopo l'istanziazione: i file esistono ma non fanno nulla finche' l'utente non li registra esplicitamente nel `settings.json` del progetto, copiando i blocchi dal frammento di esempio. Deriva dal bundle di template generato dall'utente a partire dalla guida community `Cranot/claude-code-guide`, riscritto sul protocollo hook corrente e nella doppia forma per sistema operativo richiesta dal template.

## I tre hook

`session-context` e' un hook `SessionStart`: a ogni apertura di sessione stampa il branch attivo, gli ultimi commit, i file modificati e la testa di `.claude/memory/index.md` con il punto di ripresa, e il suo output entra nel contesto della sessione. E' la prima famiglia della sezione 14: trasforma la procedura di ripresa della sezione 12 da manuale ad automatica. E' l'hook a piu' alto valore del pacchetto e l'unico che conviene attivare quasi sempre.

`protect-sensitive-files` e' un hook `PreToolUse` su `Write` ed `Edit`: blocca le scritture su file sensibili (`.env` e varianti, chiavi `.pem` e `.key`, l'interno di `.git/`), lasciando passare `.env.example`. E' difesa in profondita' rispetto alle regole `deny` gia' presenti nel `settings.json` di baseline: le regole di permesso governano cio' che l'agente puo' chiedere, l'hook intercetta la chiamata anche quando i permessi sono stati allargati, per esempio in una sessione con modalita' piu' permissiva.

`secret-scan` e' un hook `PreToolUse` su `Bash`: quando il comando in arrivo e' un `git commit`, scansiona il diff in stage alla ricerca di pattern di secret (chiavi AWS[^1], blocchi di chiave privata, token GitHub e simili, assegnazioni di api key e password) e blocca il commit se ne trova. Un'onesta' necessaria: nel `settings.json` di baseline di questo sistema il `git commit` dell'agente e' gia' negato, perche' i commit restano manuali dell'utente, quindi questo hook non scatta mai finche' quella baseline resta in vigore. Il suo valore e' nei progetti che scelgono di allentare quel deny, e come promemoria che la scansione dei segreti della sezione 6 puo' anche diventare un hook nativo di git (`core.hooksPath`) per coprire pure i commit fatti dall'utente a mano, che nessun hook di Claude Code puo' vedere.

## Meccanismo di blocco

Gli hook bloccanti usano il meccanismo piu' semplice e stabile del protocollo: escono con codice 2 e scrivono il motivo su stderr, che Claude riceve come spiegazione del blocco. Un hook che non ha nulla da dire esce con codice 0 senza output. L'hook di sessione scrive su stdout, che per `SessionStart` viene aggiunto al contesto. Gli script sono difensivi: se il parsing dell'input fallisce lasciano passare l'operazione invece di bloccare a vuoto, perche' un hook rotto non deve paralizzare il lavoro.

## Mappa di istanziazione

```
templates/hooks-starter/hooks/session-context.ps1            ->  <radice>/.claude/hooks/session-context.ps1            (tracciato; Windows)
templates/hooks-starter/hooks/session-context.sh             ->  <radice>/.claude/hooks/session-context.sh             (tracciato; Linux/macOS, chmod +x)
templates/hooks-starter/hooks/protect-sensitive-files.ps1    ->  <radice>/.claude/hooks/protect-sensitive-files.ps1    (tracciato; Windows)
templates/hooks-starter/hooks/protect-sensitive-files.sh     ->  <radice>/.claude/hooks/protect-sensitive-files.sh     (tracciato; Linux/macOS, chmod +x)
templates/hooks-starter/hooks/secret-scan.ps1                ->  <radice>/.claude/hooks/secret-scan.ps1                (tracciato; Windows)
templates/hooks-starter/hooks/secret-scan.sh                 ->  <radice>/.claude/hooks/secret-scan.sh                 (tracciato; Linux/macOS, chmod +x)
templates/hooks-starter/settings.hooks.windows.json          ->  blocchi da copiare a mano in .claude/settings.json    (non si istanzia)
templates/hooks-starter/settings.hooks.posix.json            ->  blocchi da copiare a mano in .claude/settings.json    (non si istanzia)
```

Il gate del sistema operativo istanzia la variante giusta degli script; i due frammenti `settings.hooks.*.json` non si istanziano mai come file, sono il materiale da cui copiare i soli blocchi degli hook che si vogliono attivare.

## Attivazione, sempre esplicita

L'attivazione e' una modifica al `settings.json` del progetto e segue la stessa regola di ogni scelta del sistema: si propone, non si assume. Per attivare un hook si apre il frammento della propria piattaforma, si copia il blocco corrispondente dentro la sezione `hooks` del `settings.json`, e si verifica con `/hooks` che risulti registrato. Nella variante POSIX i comandi usano `$CLAUDE_PROJECT_DIR` per la radice del progetto; nella variante Windows il frammento porta il segnaposto `<CLAUDE_PROJECT_DIR>` da sostituire con il percorso assoluto del progetto, come per l'hook di wipe della sezione 15 di `PROJECT-SYSTEM.md`. Ogni hook si attiva da solo: si puo' registrare `session-context` e lasciare gli altri due dormienti.

## Sicurezza degli hook

Un hook e' codice che gira automaticamente a ogni evento, quindi vale la disciplina della sezione 10 dell'handoff Claude Code e delle docs ufficiali: variabili sempre quotate, path validati, timeout ragionevoli, e nessun hook che esegua contenuto arrivato dall'esterno. I tre script del pacchetto sono di sola lettura sul repository (leggono git e i file di memoria, non scrivono nulla) e non fanno rete.

## Attriti osservati dal vivo (pilota 2026-07-02, due giri)

La prima esecuzione reale di `session-context.ps1` su un repository allo stato zero (nessun commit ancora) ha fatto emergere e correggere tre difetti mai esercitati prima: `git rev-parse --abbrev-ref HEAD` su un branch senza commit restituisce letteralmente la stringa "HEAD" invece del nome del branch, sostituito con `git branch --show-current` (che invece funziona correttamente anche su un branch non ancora "nato"); `Get-Content` senza `-Encoding UTF8` produceva testo accentato corrotto leggendo `.claude/memory/index.md`; `git log --oneline` su un repository senza commit lasciava passare un messaggio "fatal: ..." di git su stderr dentro l'output iniettato in sessione, ora prevenuto con un controllo esplicito (`git rev-parse --verify HEAD`) prima di richiamare il log.

Nel secondo giro la variante POSIX (`session-context.sh`) e' stata riesercitata con lo stesso caso limite (repository senza commit) e aveva lo stesso difetto di branch, in una forma ancora piu' subdola: `branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'n/a')"` cattura l'output combinato di entrambi i rami dell'`||`, perche' su un branch non nato il comando fallisce (exit 128) ma scrive comunque "HEAD" su stdout prima dell'errore su stderr, quindi la variabile finiva per contenere due righe, "HEAD" seguito da "n/a". Corretto con lo stesso approccio della variante Windows: `git branch --show-current`, con fallback a `git rev-parse --abbrev-ref HEAD` solo se il primo non produce output.

Anche `protect-sensitive-files` e' stato verificato dal vivo in questo secondo giro, su entrambe le varianti, simulando il payload JSON di un vero evento `PreToolUse`: blocca correttamente `.env`, lascia passare `.env.example` e i file normali. Nota di metodo, non un difetto dello script: testarlo con `$json | & .\hook.ps1` dentro la stessa sessione PowerShell del chiamante fa restare `[Console]::In.ReadToEnd()` in attesa indefinita, perche' quella chiamata non spawna un vero processo figlio con stdin ridirezionato come fa invece Claude Code quando esegue davvero l'hook; serve invocare lo script come processo esterno reale (`powershell.exe -File ...` da un altro processo, o l'equivalente in bash) perche' il test sia rappresentativo.

## Recap dei comandi

- Verificare gli hook registrati: `/hooks` dentro la sessione, oppure `claude --debug` per la diagnosi.
- Attivare un hook: copiare il blocco dal frammento `settings.hooks.<piattaforma>.json` in `.claude/settings.json`, sezione `hooks`.
- Disattivare un hook: rimuovere il blocco dal `settings.json`; i file degli script possono restare.

## Riferimenti e crediti

Gli hook derivano dal bundle di template generato dall'utente a partire dalla guida community `Cranot/claude-code-guide` (https://github.com/Cranot/claude-code-guide) e dalle docs ufficiali degli hook di Claude Code, riscritti per il protocollo corrente e per la doppia piattaforma. I crediti completi sono nella sezione "Riferimenti e strumenti open source" del `README.md` di radice del template.

[^1]: *AWS*, Amazon Web Services - piattaforma cloud le cui access key hanno il prefisso riconoscibile `AKIA`, usato dai pattern di scansione.
