# Sicurezza, permessi e sandboxing

> Regola modulare. Descrive le sei modalità di permesso di Claude Code, le limitazioni del sandbox per sistema operativo, le linee guida per l'uso di --dangerously-skip-permissions e le avvertenze sugli Agent Teams sperimentali. Si applica a ogni sessione e integra le regole deny già presenti in `.claude/settings.json`.

## Le sei modalità di permesso

Claude Code espone sei modalità di permesso, selezionabili al lancio con `claude --permission-mode <modalita>` oppure ciclando con `Shift+Tab` durante la sessione.

La modalità *default* richiede conferma per ogni operazione potenzialmente rischiosa ed è il punto di partenza corretto per codice non familiare e progetti nuovi. La modalità *acceptEdits* accetta automaticamente le modifiche ai file, mantenendo il prompt per l'esecuzione di comandi; è utile nelle sessioni di sviluppo attivo dove ci si fida delle modifiche. La modalità *plan* mette Claude in sola lettura: nessuna modifica è possibile, il che la rende ideale per l'analisi e la pianificazione prima di toccare il codice.

La modalità *dontAsk* nega silenziosamente tutto cio che non è pre-approvato esplicitamente nelle regole `allow` del `settings.json`; e più sicura del bypass totale per l'automazione hands-off. La modalità *auto*, introdotta nel marzo 2026, sostituisce la fatica da conferma con due livelli di difesa: un probe lato server scansiona l'output di ogni tool prima che entri nel contesto dell'agente, e un classificatore basato su Sonnet 4.6 valuta ogni azione rispetto al suo impatto reale prima dell'esecuzione. E la via di mezzo ufficiale consigliata per le sessioni autonome. La modalità *bypassPermissions* salta tutti i controlli ed è trattata nella sezione dedicata qui sotto.

## Il sandbox: limitazioni per sistema operativo

Il sandbox isola a livello OS cio che i comandi Bash e i loro sottoprocessi possono toccare. Si attiva con `/sandbox` durante la sessione.

Su macOS funziona nativamente via Seatbelt. Su Linux e WSL2[^1] richiede i pacchetti `bubblewrap` e `socat` installati prima (`sudo apt-get install bubblewrap socat`). Su Windows nativo, compreso il setup con PowerShell 7 senza WSL2, il sandbox non è supportato: per l'isolamento a livello OS su progetti sensibili la via pratica e WSL2 oppure Docker. La distinzione tra permessi e sandbox e importante: i permessi controllano quali tool Claude può usare; il sandbox applica l'isolamento a livello OS sui comandi Bash e i loro processi figli, che possono aprire file o fare rete indipendentemente da quanto Claude decide di fare.

Una limitazione documentata dalla stessa Anthropic: la policy di lettura default del sandbox lascia accessibili `~/.aws/credentials` e `~/.ssh/`. Quando si abbina il sandbox a sessioni autonome, aggiungere entrambi a `sandbox.filesystem.denyRead` nel `settings.json` prima di avviare la sessione, non dopo.

## --dangerously-skip-permissions: quando e accettabile

Il consenso unanime di documentazione ufficiale e community e chiaro: questo flag non va mai usato su una macchina reale non containerizzata. In un container o VM completamente isolati e accettabile, a condizione che il container giri come utente non privilegiato (il flag si rifiuta di girare come root su Linux e macOS).

Tre comportamenti del flag che sorprendono spesso. Le chiamate ai tool MCP[^2] si auto-approvano insieme a tutto il resto: più server MCP con permessi di scrittura hai connessi, più ampio e il raggio d'azione in caso di prompt injection. Le regole `deny` esplicite nel `settings.json` continuano a bloccare anche in bypass. `--disallowedTools` funziona correttamente in bypass, mentre `--allowedTools` può essere ignorato: se si vuole limitare i tool disponibili in un container autonomo, usare il primo.

Per le sessioni autonome su macchina reale la modalità consigliata e *auto* oppure *dontAsk* con una lista `allow` ben costruita, non il bypass.

## Agent Teams sperimentali: avvertenza sui permessi

Gli Agent Teams sono una feature sperimentale (disabilitata di default, si attiva con la variabile di ambiente `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`) che permette a più agenti di lavorare in parallelo con comunicazione diretta tra pari, una task list condivisa e file locking. La caratteristica che richiede attenzione prima del lancio: i permessi del lead si propagano a tutti i teammate nel momento dello spawn. Se il lead parte con `bypassPermissions`, tutti i teammate lo ereditano. La postura dei permessi va quindi pianificata sul lead, con cura, prima di avviare il team, non corretta a posteriori.

I team non supervisionati per più di 10-15 minuti tendono a bloccarsi su prompt di permesso, a segnare task come completati prematuramente o a perdere lo scope del lavoro originale. Un check-in periodico sulla task list condivisa non è opzionale per i task lunghi.

## Integrazione con settings.json

Le regole deny nel `templates/settings.json` del progetto coprono il perimetro minimo: commit e push git manuali, reset e rebase git, configurazione git globale, lettura di file di credenziali (`.env`, chiavi SSH, credenziali AWS) e rimozione ricorsiva. Le operazioni distruttive-ma-reversibili (`npm publish`, `docker push`) stanno in `ask` così che Claude chieda conferma invece di bloccare del tutto. Questo schema si committa nel repository e vale per l'intero team, indipendentemente dalla configurazione personale di ciascun membro.

[^1]: *WSL2*, Windows Subsystem for Linux versione 2 - layer di virtualizzazione che esegue un kernel Linux completo dentro Windows, usato per ottenere il sandboxing nativo su macchine Windows.

[^2]: *MCP*, Model Context Protocol - standard che permette a un client AI di parlare con sistemi esterni (GitHub, database, browser) attraverso un'interfaccia comune; ogni server MCP espone tool, risorse e prompt che diventano disponibili all'agente.
