# Pacchetto hooks-starter

> Pacchetto opzionale del sistema di progetto. Fornisce sette hook di automazione pronti all'uso, in doppia forma PowerShell e shell POSIX, che concretizzano le famiglie descritte nella sezione 14 di `PROJECT-SYSTEM.md`, finora solo descrittiva. Si dividono in due famiglie con due scopi diversi: quattro rendono automatico ciò che altrimenti dipende dal ricordarsene, coprendo i quattro momenti del ciclo di lavoro, e tre intercettano una scrittura o un commit pericolosi. Nessun hook è attivo dopo l'istanziazione: i file esistono ma non fanno nulla finché l'utente non li registra esplicitamente nel `settings.json` del progetto, copiando i blocchi dal frammento di esempio. Deriva dal bundle di template generato dall'utente a partire dalla guida community `Cranot/claude-code-guide`, riscritto sul protocollo hook corrente e nella doppia forma per sistema operativo richiesta dal template.

## I quattro hook del ciclo, che tolgono il ricordarsene

Hanno in comune il modo in cui il difetto si manifesta, ed è la ragione per cui vale automatizzarli invece di prescriverli: nessuno dei quattro fallisce in modo visibile. Una prescrizione che dipende dal ricordarsene funziona finché qualcuno ricorda, e la volta che non ricorda nessuno se ne accorge.

`apertura-sessione` è un hook `SessionStart` e fa due cose. La prima è eseguire la verifica di ripresa, cioè confrontare l'impronta che la sessione precedente ha registrato con lo stato reale di git, e riportare che cosa diverge. La seconda è meno ovvia e sfrutta il fatto che l'uscita di un hook `SessionStart` entra nel contesto della sessione: stampa l'istruzione di invocare `sync-context` come secondo atto. È il solo modo di rendere automatico un passo che richiede l'agente e non un programma, perché nessun hook può invocare una skill.

`md-unwrap-auto` è un hook `PostToolUse` su `Write` ed `Edit`: quando il file scritto è un `.md`, ne riporta i paragrafi su riga sorgente unica. Agisce dopo la scrittura e non prima perché è una normalizzazione e non una difesa, e per contratto lo strumento rifiuta di scrivere un file il cui rendering cambierebbe, quindi il caso peggiore è che non faccia nulla.

`pre-commit-checks` è un hook `PreToolUse` su `Bash`: quando il comando è un `git commit`, esegue i quattro controlli che verificano una convenzione dichiarata invece di un comportamento, cioè forma dei paragrafi, tipografia, comandi copiabili in una riga sola e riferimenti a file inesistenti, e blocca se uno fallisce. Un controllo il cui strumento non è istanziato si salta in silenzio, perché un progetto può legittimamente non avere quel pacchetto.

`chiusura-sessione` è un hook `SessionEnd` e registra l'impronta di ripresa. Porta con sé un paradosso che va capito prima di attivarlo: se l'impronta la registrasse solo l'agente, una sessione caduta non la registrerebbe mai, che è il comportamento voluto; se la registra un hook, la registra anche a una chiusura di colpo, e una caduta diventerebbe indistinguibile da una chiusura ordinata. La risoluzione sta in ciò che l'hook copre davvero: un hook `SessionEnd` non gira quando il processo muore per un crash vero, quindi copre la chiusura distratta e lascia scoperta la caduta vera, che è esattamente ciò che si vuole restare visibile. Resta una rete e non il percorso principale: quello è l'agente che aggiorna il file di ripresa con lo stato raggiunto e il prossimo passo, e poi registra.

## Dove i quattro hook cercano gli strumenti, e perché in tre posti

Tre dei quattro hook del ciclo invocano uno strumento condiviso: `verifica-ripresa.py` nei due di apertura e chiusura, `md-unwrap.py` in quello di normalizzazione, e la batteria completa in quello di pre-commit. Dove viva quello strumento non è una sola cosa, ed è il motivo per cui la ricerca ha tre tappe invece di una. In un progetto che ha adottato il sistema gli strumenti stanno in `tools/` della radice, che è la mappa di istanziazione di ogni pacchetto. Nel repository che quegli strumenti li produce, cioè il template stesso, gli originali vivono sotto `.claude/templates/`, dove `md-unwrap` ha per giunta una cartella propria.

La ricerca prova quindi `tools/`, poi `.claude/templates/tools/`, poi `.claude/templates/md-unwrap/tools/`, e prende la prima che risponde. Il difetto che questo chiude era passato inosservato per una ragione che vale come avvertimento generale: un hook che non trova il proprio strumento non fallisce, esce con codice zero senza fare niente, e un hook silenzioso è indistinguibile da un hook che ha lavorato. Registrati nel bundle, `apertura-sessione` e `md-unwrap-auto` giravano a vuoto a ogni sessione senza che nulla lo dicesse.

Della stessa famiglia è il perimetro, che i due hook di apertura e chiusura ora passano esplicitamente con `--radice`. Un hook non gira per contratto nella radice del progetto ma nella cartella corrente del processo che lo ospita, e uno strumento che risolvesse la radice sul punto leggerebbe un altro repository o nessuno: nel caso osservato dichiarava che il file di ripresa non esisteva, invece di dire che lo stava cercando altrove, cioè travestiva un difetto da diagnosi.

Una terza asimmetria vale solo per `pre-commit-checks` e riguarda il bundle. I tre strumenti tipografici rifiutano di scrivere sotto `.claude/templates/`, perché in un progetto ospite quelli sono copie e correggerle le farebbe divergere dall'originale; nel repository che gli originali li contiene la guardia va disattivata con `--includi-modelli`, e il controllo sui riferimenti vuole `--bundle` per la stessa ragione simmetrica. Senza quei due argomenti i controlli guardano una frazione dei file e passano, che è un via libera indistinguibile da quello vero. L'hook riconosce il bundle dalla presenza dei due prompt di istanziazione, che nessun progetto ospite riceve: si distingue per ciò che il repository fa, non per come si chiama la sua cartella.

## Lo stato, che è cosa diversa dalla verifica

`session-context` è un hook `SessionStart`: a ogni apertura di sessione stampa il branch attivo, gli ultimi commit, i file modificati e la testa di `.claude/memory/index.md` con il punto di ripresa, e il suo output entra nel contesto della sessione. È la prima famiglia della sezione 14: trasforma la procedura di ripresa della sezione 12 da manuale ad automatica. È l'hook a più alto valore del pacchetto e l'unico che conviene attivare quasi sempre.

Con `apertura-sessione` non si sovrappone e non si sostituisce, e la distinzione conta: questo stampa lo stato corrente, quello lo confronta con lo stato che la sessione precedente aveva registrato. Nessuna stampa dello stato rivela che un file di ripresa descriva un passato, perché un file di ripresa non aggiornato ha esattamente lo stesso aspetto di uno aggiornato: serve il confronto. I due si attivano insieme.

## I due hook di difesa

`protect-sensitive-files` è un hook `PreToolUse` su `Write` ed `Edit`: blocca le scritture su file sensibili (`.env` e varianti, chiavi `.pem` e `.key`, l'interno di `.git/`), lasciando passare `.env.example`. È difesa in profondità rispetto alle regole `deny` già presenti nel `settings.json` di baseline: le regole di permesso governano ciò che l'agente può chiedere, l'hook intercetta la chiamata anche quando i permessi sono stati allargati, per esempio in una sessione con modalità più permissiva.

`secret-scan` è un hook `PreToolUse` su `Bash`: quando il comando in arrivo è un `git commit`, scansiona il diff in stage alla ricerca di pattern di secret (chiavi AWS[^1], blocchi di chiave privata, token GitHub e simili, assegnazioni di api key e password) e blocca il commit se ne trova. Un'onestà necessaria: nel `settings.json` di baseline di questo sistema il `git commit` dell'agente è già negato, perché i commit restano manuali dell'utente, quindi questo hook non scatta mai finché quella baseline resta in vigore. Il suo valore è nei progetti che scelgono di allentare quel deny, e come promemoria che la scansione dei segreti della sezione 6 può anche diventare un hook nativo di git (`core.hooksPath`) per coprire pure i commit fatti dall'utente a mano, che nessun hook di Claude Code può vedere.

## Meccanismo di blocco

Gli hook bloccanti usano il meccanismo più semplice e stabile del protocollo: escono con codice 2 e scrivono il motivo su stderr, che Claude riceve come spiegazione del blocco. Un hook che non ha nulla da dire esce con codice 0 senza output. L'hook di sessione scrive su stdout, che per `SessionStart` viene aggiunto al contesto. Gli script sono difensivi: se il parsing dell'input fallisce lasciano passare l'operazione invece di bloccare a vuoto, perché un hook rotto non deve paralizzare il lavoro.

## Mappa di istanziazione

```
templates/hooks-starter/hooks/apertura-sessione.ps1          ->  <radice>/.claude/hooks/apertura-sessione.ps1          (tracciato; Windows)
templates/hooks-starter/hooks/apertura-sessione.sh           ->  <radice>/.claude/hooks/apertura-sessione.sh           (tracciato; Linux/macOS, chmod +x)
templates/hooks-starter/hooks/md-unwrap-auto.ps1             ->  <radice>/.claude/hooks/md-unwrap-auto.ps1             (tracciato; Windows)
templates/hooks-starter/hooks/md-unwrap-auto.sh              ->  <radice>/.claude/hooks/md-unwrap-auto.sh              (tracciato; Linux/macOS, chmod +x)
templates/hooks-starter/hooks/pre-commit-checks.ps1          ->  <radice>/.claude/hooks/pre-commit-checks.ps1          (tracciato; Windows)
templates/hooks-starter/hooks/pre-commit-checks.sh           ->  <radice>/.claude/hooks/pre-commit-checks.sh           (tracciato; Linux/macOS, chmod +x)
templates/hooks-starter/hooks/chiusura-sessione.ps1          ->  <radice>/.claude/hooks/chiusura-sessione.ps1          (tracciato; Windows)
templates/hooks-starter/hooks/chiusura-sessione.sh           ->  <radice>/.claude/hooks/chiusura-sessione.sh           (tracciato; Linux/macOS, chmod +x)
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

L'attivazione è una modifica al `settings.json` del progetto e segue la stessa regola di ogni scelta del sistema: si propone, non si assume. Per attivare un hook si apre il frammento della propria piattaforma, si copia il blocco corrispondente dentro la sezione `hooks` del `settings.json`, e si verifica con `/hooks` che risulti registrato. Nella variante POSIX i comandi usano `$CLAUDE_PROJECT_DIR` per la radice del progetto; nella variante Windows il frammento porta il segnaposto `<CLAUDE_PROJECT_DIR>` da sostituire con il percorso assoluto del progetto, come per l'hook di wipe della sezione 15 di `PROJECT-SYSTEM.md`. Ogni hook si attiva da solo: si può registrare `session-context` e lasciare gli altri due dormienti.

## Sicurezza degli hook

Un hook è codice che gira automaticamente a ogni evento, quindi vale la disciplina della sezione 10 dell'handoff Claude Code e delle docs ufficiali: variabili sempre quotate, path validati, timeout ragionevoli, e nessun hook che esegua contenuto arrivato dall'esterno. I tre script del pacchetto sono di sola lettura sul repository (leggono git e i file di memoria, non scrivono nulla) e non fanno rete.

## Attriti osservati dal vivo (pilota 2026-07-02, due giri)

La prima esecuzione reale di `session-context.ps1` su un repository allo stato zero (nessun commit ancora) ha fatto emergere e correggere tre difetti mai esercitati prima: `git rev-parse --abbrev-ref HEAD` su un branch senza commit restituisce letteralmente la stringa "HEAD" invece del nome del branch, sostituito con `git branch --show-current` (che invece funziona correttamente anche su un branch non ancora "nato"); `Get-Content` senza `-Encoding UTF8` produceva testo accentato corrotto leggendo `.claude/memory/index.md`; `git log --oneline` su un repository senza commit lasciava passare un messaggio "fatal: ..." di git su stderr dentro l'output iniettato in sessione, ora prevenuto con un controllo esplicito (`git rev-parse --verify HEAD`) prima di richiamare il log.

Nel secondo giro la variante POSIX (`session-context.sh`) è stata riesercitata con lo stesso caso limite (repository senza commit) e aveva lo stesso difetto di branch, in una forma ancora più subdola: `branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'n/a')"` cattura l'output combinato di entrambi i rami dell'`||`, perché su un branch non nato il comando fallisce (exit 128) ma scrive comunque "HEAD" su stdout prima dell'errore su stderr, quindi la variabile finiva per contenere due righe, "HEAD" seguito da "n/a". Corretto con lo stesso approccio della variante Windows: `git branch --show-current`, con fallback a `git rev-parse --abbrev-ref HEAD` solo se il primo non produce output.

Anche `protect-sensitive-files` è stato verificato dal vivo in questo secondo giro, su entrambe le varianti, simulando il payload JSON di un vero evento `PreToolUse`: blocca correttamente `.env`, lascia passare `.env.example` e i file normali. Nota di metodo, non un difetto dello script: testarlo con `$json | & .\hook.ps1` dentro la stessa sessione PowerShell del chiamante fa restare `[Console]::In.ReadToEnd()` in attesa indefinita, perché quella chiamata non spawna un vero processo figlio con stdin ridirezionato come fa invece Claude Code quando esegue davvero l'hook; serve invocare lo script come processo esterno reale (`powershell.exe -File ...` da un altro processo, o l'equivalente in bash) perché il test sia rappresentativo.

## Recap dei comandi

- Verificare gli hook registrati: `/hooks` dentro la sessione, oppure `claude --debug` per la diagnosi.
- Attivare un hook: copiare il blocco dal frammento `settings.hooks.<piattaforma>.json` in `.claude/settings.json`, sezione `hooks`.
- Disattivare un hook: rimuovere il blocco dal `settings.json`; i file degli script possono restare.

## Riferimenti e crediti

Gli hook derivano dal bundle di template generato dall'utente a partire dalla guida community `Cranot/claude-code-guide` (https://github.com/Cranot/claude-code-guide) e dalle docs ufficiali degli hook di Claude Code, riscritti per il protocollo corrente e per la doppia piattaforma. I crediti completi sono nella sezione "Riferimenti e strumenti open source" del `README.md` di radice del template.

[^1]: *AWS*, Amazon Web Services - piattaforma cloud le cui access key hanno il prefisso riconoscibile `AKIA`, usato dai pattern di scansione.
