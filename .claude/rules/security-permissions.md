# Sicurezza, permessi e sandboxing

> Regola modulare. Descrive le sei modalità di permesso di Claude Code, le limitazioni del sandbox per sistema operativo, e il rimando alla norma per i due casi che non si presentano a ogni sessione. Si applica a ogni sessione e integra le regole deny già presenti in `.claude/settings.json`.

## Le sei modalità di permesso

Claude Code espone sei modalità di permesso, selezionabili al lancio con `claude --permission-mode <modalita>` oppure ciclando con `Shift+Tab` durante la sessione.

La modalità *default* richiede conferma per ogni operazione potenzialmente rischiosa ed è il punto di partenza corretto per codice non familiare e progetti nuovi. La modalità *acceptEdits* accetta automaticamente le modifiche ai file, mantenendo il prompt per l'esecuzione di comandi; è utile nelle sessioni di sviluppo attivo dove ci si fida delle modifiche. La modalità *plan* mette Claude in sola lettura: nessuna modifica è possibile, il che la rende ideale per l'analisi e la pianificazione prima di toccare il codice.

La modalità *dontAsk* nega silenziosamente tutto cio che non è pre-approvato esplicitamente nelle regole `allow` del `settings.json`; e più sicura del bypass totale per l'automazione hands-off. La modalità *auto*, introdotta nel marzo 2026, sostituisce la fatica da conferma con due livelli di difesa: un probe lato server scansiona l'output di ogni tool prima che entri nel contesto dell'agente, e un classificatore basato su Sonnet 4.6 valuta ogni azione rispetto al suo impatto reale prima dell'esecuzione. E la via di mezzo ufficiale consigliata per le sessioni autonome. Dal 2026-11-06, versione 2.1.319, quella via di mezzo ha una condizione che va conosciuta: con la telemetria o i feature flag disattivati, compresi i montaggi dietro un gateway, le chiamate che il server non può verificare vengono chieste o negate e non ricadono più sul classificatore locale, che si riattiva solo con `CLAUDE_CODE_AUTO_MODE_SERVER=0`; nella stessa versione `claude -p` in modo automatico esce con codice 1 quando un'azione viene rifiutata per mancanza del controllo, il che rompe uno script che lo invocava, ed esiste l'impostazione `permissions.denyInsteadOfPrompting`, che nega invece di chiedere. La modalità *bypassPermissions* salta tutti i controlli ed è trattata nella sezione dedicata qui sotto.

## Il sandbox: limitazioni per sistema operativo

Il sandbox isola a livello OS cio che i comandi Bash e i loro sottoprocessi possono toccare. Si attiva con `/sandbox` durante la sessione.

Su macOS funziona nativamente via Seatbelt. Su Linux e WSL2[^1] richiede i pacchetti `bubblewrap` e `socat` installati prima (`sudo apt-get install bubblewrap socat`). Su Windows nativo, compreso il setup con PowerShell 7 senza WSL2, il sandbox non è supportato: per l'isolamento a livello OS su progetti sensibili la via pratica e WSL2 oppure Docker. La distinzione tra permessi e sandbox e importante: i permessi controllano quali tool Claude può usare; il sandbox applica l'isolamento a livello OS sui comandi Bash e i loro processi figli, che possono aprire file o fare rete indipendentemente da quanto Claude decide di fare.

Una limitazione documentata dalla stessa Anthropic: la policy di lettura default del sandbox lascia accessibili `~/.aws/credentials` e `~/.ssh/`. Quando si abbina il sandbox a sessioni autonome, aggiungere entrambi a `sandbox.filesystem.denyRead` nel `settings.json` prima di avviare la sessione, non dopo.

## I due casi che vivono nella norma

Due situazioni hanno regole proprie e non si presentano a ogni sessione, quindi stanno in `.claude/norme/security-permissions.md` e si caricano quando servono. La prima è l'uso di `--dangerously-skip-permissions`, con le condizioni in cui è accettabile, i tre comportamenti del flag che sorprendono e la modalità da preferire per una sessione autonoma su macchina reale. La seconda sono gli Agent Teams sperimentali, dove i permessi del lead si propagano a ogni teammate nel momento dello spawn e la postura va decisa prima dell'avvio.

## Integrazione con settings.json

Le regole deny nel `templates/settings.json` del progetto coprono il perimetro minimo: commit e push git manuali, reset e rebase git, configurazione git globale, lettura di file di credenziali (`.env`, chiavi SSH, credenziali AWS) e rimozione ricorsiva. Le operazioni distruttive-ma-reversibili (`npm publish`, `docker push`) stanno in `ask` così che Claude chieda conferma invece di bloccare del tutto. Questo schema si committa nel repository e vale per l'intero team, indipendentemente dalla configurazione personale di ciascun membro.

[^1]: *WSL2*, Windows Subsystem for Linux versione 2 - layer di virtualizzazione che esegue un kernel Linux completo dentro Windows, usato per ottenere il sandboxing nativo su macchine Windows.
