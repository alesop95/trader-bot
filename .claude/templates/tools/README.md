# tools

## render-diagrams.mjs

Rende i diagrammi Mermaid di `.claude/context/diagrams/*.mmd` nei corrispondenti `.svg`, riusando il browser Chromium-based già installato sul sistema (Edge o Chrome). Non scarica il Chromium di Puppeteer: il download e disattivato e si punta al browser locale, così la generazione resta snella e ogni progetto e autonomo.

Uso:

```
node tools/render-diagrams.mjs
```

Per rendere una cartella diversa:

```
node tools/render-diagrams.mjs <cartella>
```

Prerequisiti: Node e un browser Edge o Chrome. Alla prima esecuzione `npx` scarica i soli script di mermaid-cli, mai un browser. Se l'autorilevamento del browser fallisce, forzalo con la variabile d'ambiente `PUPPETEER_EXECUTABLE_PATH` puntata all'eseguibile di Edge o Chrome.

I `.svg` prodotti sono versionati accanto ai `.mmd` sorgente, secondo l'anatomia canonica del sistema di progetto.

## lint-md-commands.py

Percorre i blocchi di codice di shell dentro i file Markdown e segnala i comandi che non si possono copiare in una riga sola: continuazioni di riga (backslash di bash, backtick di PowerShell, caret di cmd), heredoc multi-riga e comandi git che proseguono sulla riga seguente. Esiste perché `md-unwrap` per contratto lascia verbatim il contenuto dei blocchi recintati, quindi un comando spezzato dentro un blocco di codice non viene corretto da nessuno strumento e va trovato a parte. Attua la verifica richiesta dalla regola `.claude/rules/git-commands-format.md`.

```
python tools/lint-md-commands.py .
```

È in sola lettura e non scrive nulla: esce 0 se non trova niente, 1 altrimenti, quindi si può usare come gate in pre-commit o in CI accanto a `md-unwrap --check`. Un blocco viene considerato shell solo se lo dichiara la info string (`bash`, `powershell`, `sh`, `console` e simili) oppure se non ha info string e contiene comandi: un blocco `markdown` o `text` che cita un comando resta prosa, e la prosa può finire legittimamente con un backtick di code span. Le continuazioni backslash dentro un blocco dichiarato `bash` restano segnalate ma sono legittime se il comando è specifico di quella shell e non è destinato al copia-incolla cross-piattaforma: la segnalazione serve a decidere, non a imporre.

## lint-md-tables.py

Verifica la struttura delle tabelle Markdown, che `md-unwrap` per contratto non tocca: segnala una riga vuota dentro una cella, che chiude la tabella e manda il resto della cella fuori dalla griglia come prosa, e una riga con meno colonne dell'intestazione, che il renderer lascia vuota senza protestare. Sono i due difetti che la regola `interaction-style.md` enuncia per le tabelle, e nessuno dei due produce un errore visibile. Nato in un progetto istanziato il 2026-09-01, dove due voci di un registro erano rimaste per un giorno senza la colonna obbligatoria.

```
python tools/lint-md-tables.py .
```

È in sola lettura: esce 0 se non trova niente, 1 altrimenti, e si usa come gate accanto a `md-unwrap --check` e a `lint-md-commands.py`.

## detect-ssh-profiles.py

Rileva, in sola lettura, i profili SSH verso GitHub configurati sulla macchina dove gira, e serve al Passo 0.5 dell'inizializzazione e dell'allineamento. Esiste perché il riferimento della skill `identita-git` non può sapere quali alias e quali chiavi esistano dove viene letta: un alias e una convenzione della singola installazione, non un fatto del sistema di progetto, e assumerlo porta a configurare un remoto che punta a un profilo inesistente, con un errore che si manifesta solo al primo push. Lo strumento e unico e non ha una variante per sistema operativo, perché il formato di `ssh_config` non ne ha.

```
python .claude/templates/tools/detect-ssh-profiles.py --repo .
```

Risolve il file di configurazione dell'utente insieme alle sue direttive `Include`, elenca gli alias il cui `HostName` e `github.com` con la chiave che ciascuno seleziona, dichiara se quel file di chiave esiste davvero, segnala le chiavi presenti in `~/.ssh` che nessun alias richiama e i blocchi `Match` che non ha interpretato, e riporta l'identità git globale con `user.useConfigOnly` più identità locale, remoto e `core.sshCommand` del repository indicato da `--repo`. Con `--json` produce la stessa informazione in forma strutturata. Non stampa mai materiale di chiave, solo percorsi e nomi. Esce 0 se trova almeno un alias verso GitHub e 1 se non ne trova nessuno, caso in cui non c'è niente da scegliere e il profilo va creato prima di proseguire.

Il suo output e il materiale della domanda all'utente, non la risposta: il nome di un blocco `Host` e una mnemonica di chi ha configurato quella macchina e non dice a quale identità vada abbinato, quindi alias, `user.name`, `user.email` e owner di destinazione si chiedono e non si deducono.

## check-account-hygiene.ps1

Verifica, in sola lettura, che l'account Claude Code attivo rispetti l'igiene del magazzino nascosto richiesta dal sistema: `autoMemoryEnabled: false`, un hook `SessionEnd` che esegue `session-end-wipe`, e che lo script di wipe installato sia configurato per questa macchina e non per un'altra. Il terzo controllo invoca lo script installato nel suo modo di sola lettura e distingue due guasti che i primi due non vedono: il template copiato ma mai compilato, con i prefissi ancora al segnaposto, e il caso in cui nessuno degli slug presenti corrisponda ai prefissi configurati, che è la firma di una configurazione presa da un'altra macchina. Si esegue al Passo 0 dell'inizializzazione o dell'allineamento di un progetto, e non modifica nulla: stampa un report PASS/FAIL e, se l'account non è in regola, indica cosa aggiungere. Vedi PROJECT-SYSTEM.md sezione 15.

```
powershell -NoProfile -ExecutionPolicy Bypass -File .claude/templates/tools/check-account-hygiene.ps1
```

Dal 2026-10-09 c'è un quarto controllo: il wipe installato deve puntare alla home dell'account che lo esegue, avere accanto `stato-magazzino`, e coincidere con il template fuori dalle righe di configurazione quando il template è raggiungibile. Quel giorno la copia di un account puntava da quattro giorni alla home di un altro, e i primi tre controlli passavano. Determina l'account attivo da `CLAUDE_CONFIG_DIR`, con fallback su `%USERPROFILE%\.claude`, e ne legge il `settings.json`. Esce con codice 0 se l'account è in regola, 1 altrimenti. Su Linux la variante equivalente e `check-account-hygiene.sh` (`bash .claude/templates/tools/check-account-hygiene.sh`), che legge il JSON con `python3` e, in sua mancanza, ricade su un controllo testuale.

## session-end-wipe.ps1

Template del wipe del magazzino nascosto, da installare per-account, non per-progetto. Si copia in `<CLAUDE_CONFIG_DIR>\hooks\session-end-wipe.ps1` insieme a `scrub-claude-json.js`, si sostituiscono i segnaposto `<CLAUDE_CONFIG_DIR>`, `<KEEP_PREFIXES>` e `<KEEP_PATH_PREFIXES>`, e si registra come hook `SessionEnd` nel `settings.json` dell'account, o nel `settings.local.json` se quella home non ha un `settings.json`. A ogni chiusura di sessione ripulisce i transcript e la memoria nascosta dei progetti non preservati e gli store per-account effimeri, lasciando intatti i progetti il cui slug corrisponde a uno dei prefissi da preservare, la configurazione, il login, le skill, i plugin e lo stato del daemon. I prefissi dipendono dalla macchina, uno per ogni radice dove stanno i progetti di sviluppo, e il template non ne porta uno di default ma un segnaposto che blocca lo script: un default che funziona su una macchina è una trappola su tutte le altre, perché su Linux gli slug derivano dal percorso assoluto e un prefisso come `D--` non corrisponde a niente, l'insieme dei progetti preservati risulta vuoto e il wipe cancellerebbe l'intero magazzino senza segnalare nulla. Da qui le tre guardie che precedono ogni rimozione: la home dell'account deve esistere e assomigliare a un magazzino di Claude Code, i prefissi devono essere stati compilati, e almeno uno slug presente deve corrispondervi, altrimenti lo script si ferma dichiarando che la configurazione è di un'altra macchina. L'esito dell'ultima corsa, rifiuti compresi, finisce in `session-end-wipe.log` nella home dell'account, perché un hook `SessionEnd` gira senza che nessuno ne veda l'output. Su Linux la variante equivalente e `session-end-wipe.sh`, registrata con un hook il cui comando e `bash "<CLAUDE_CONFIG_DIR>/hooks/session-end-wipe.sh"`. I prefissi non si indovinano: entrambe le varianti hanno un modo di sola lettura, `-List` su Windows e `--list` su Linux, che elenca gli slug realmente presenti marcandoli come preservati o da rimuovere e funziona anche sul template non ancora compilato, e un modo `-DryRun` oppure `--dry-run` che stampa ogni rimozione senza farne nessuna. L'ordine corretto è elencare, chiedere all'utente quali radici preservare mostrandogli l'elenco, compilare, provare a vuoto e solo allora registrare l'hook. La procedura completa e le sue varianti sono in PROJECT-SYSTEM.md sezione 15.

Le copie installate non si aggiornano da sole, e su una macchina con più account ce n'è una per account. Una correzione a questo template va quindi reinstallata su ogni account che ne ha una copia, non solo su quello in cui è stata scritta. Il caso che lo ha insegnato, in un progetto istanziato il 2026-10-07: la guardia sulle altre sessioni aperte, aggiunta il 2026-10-05, era stata installata su un solo account. La chiusura di una sessione di un altro account, con la copia vecchia senza guardia, ha cancellato la radice degli scratchpad, che è comune a tutti gli account della stessa utenza, sotto i piedi di una sessione ancora aperta. Il diario `session-end-wipe.log` dell'account vecchio diceva "Fatto" senza nessun "Rimandato", ed è così che si è trovata la causa. La verifica dell'igiene dell'account controlla che lo script sia installato e configurato, non che sia la versione corrente: una copia vecchia la passa.

Oltre agli store storici lo script copre tre residui che altrimenti sopravvivono al wipe. Il primo sono le cache e i registri di stato per-account, ovvero `cache/`, `jobs/`, `ide/`, `todos/`, `statsig/`, `telemetry/` e `mcp-needs-auth-cache.json`. Il secondo sono gli scratchpad temporanei che Claude Code tiene in `%LOCALAPPDATA%\Temp\claude\<slug-progetto>` su Windows e in `$TMPDIR/claude/<slug-progetto>` su POSIX, con una sottocartella per sessione e gli output dei task: quella radice e condivisa fra tutti gli account della stessa utenza, quindi il passaggio e idempotente e chi chiude per ultimo la ripulisce. Il terzo e l'elenco dei percorsi aperti dentro `projects` di `.claude.json`, che senza questo passaggio sopravvive a ogni pulizia; se ne occupa `scrub-claude-json.js`. Di quest'ultimo passaggio va tenuto presente un effetto collaterale voluto: rimuovendo la voce di un progetto si rimuove anche il suo `hasTrustDialogAccepted`, quindi Claude Code richiede di nuovo di fidarsi della cartella al successivo avvio su quel percorso.

Dal 2026-10-05 lo script, in entrambe le varianti, rimanda il wipe se è viva un'altra sessione di Claude Code, escludendo la catena di processi della sessione che sta chiudendo e l'app desktop. La radice degli scratchpad è comune a tutti gli account della stessa utenza e le cartelle effimere sono comuni alle sessioni di un account, quindi chiudere una sessione cancellava scratchpad, piani e task di quelle ancora aperte: è successo davvero, e la sessione colpita ha visto sparire a metà lavoro il proprio piano e lo scratchpad. Il rinvio si scrive nel diario dell'account, e `-Forza` (PowerShell) o `--forza` (POSIX) lo salta per chi sa che le altre sessioni non contano.

Dal 2026-10-09 il rinvio totale resta solo come ripiego, e il wipe lavora per sessione: toglie subito ciò che appartiene a sessioni chiuse e conserva ciò che appartiene a una sessione con un processo vivo, decidendolo con `stato-magazzino` installato accanto. In modo hook, riconosciuto dal payload di `SessionEnd` sullo standard input letto con un limite di due secondi, lo script si rilancia staccato, perché Claude Code interrompe l'hook di fine sessione dopo circa 1,4 secondi, misurati con un hook sonda, dall'albero dei processi di Claude, con WMI su Windows e `setsid` su POSIX, e la copia rilanciata pulisce solo dopo l'uscita del processo della sessione, escludendo dalla protezione la sessione appena chiusa; lanciato a mano conta come viva anche la sessione da cui eventualmente parte. Copre inoltre i log dei server MCP in `%LOCALAPPDATA%\claude-cli-nodejs\Cache\<slug>` e, su Linux, in `${XDG_CACHE_HOME:-~/.cache}/claude-cli-nodejs/<slug>`, verificato su Ubuntu con Claude Code 2.1.295, mentre su macOS il percorso resta inferito; e chiama `scrub-claude-json.js` con `--solo-config`, che dalle voci di `.claude.json` conservate toglie le metriche dell'ultima sessione. Sulla variante POSIX è stato corretto lo stesso giorno un difetto preesistente: la guardia sui prefissi rifiutava l'insieme vuoto anche con `ALLOW_EMPTY_KEEP=1`. Il disegno completo, la storia e la tabella di che cosa si pulisce e che cosa resta stanno nella sezione 15 di `PROJECT-SYSTEM.md`. Le prove sono `tests/test-wipe-per-sessione.ps1`, 34 casi in sette scenari con un `claude.exe` finto copiato da `cmd.exe`, e `tests/test_wipe_per_sessione_linux.py`, gli stessi sette scenari su Linux con un `claude` finto copiato da `sleep` e da `bash`; girano su home e radici finte passate con `-BaseProva`, `-TempProva`, `-McpProva` o con le variabili `BASE_PROVA`, `TEMP_PROVA`, `MCP_PROVA`, e non toccano niente di reale.

## stato-magazzino.ps1 / stato-magazzino.py

Resoconto in sola lettura di ciò che resta nel magazzino nascosto di tutti gli account della stessa utenza Windows, e delle sessioni di Claude Code che lo trattengono. Nasce il 2026-10-08: account1 aveva cinque progetti sotto `projects\` dopo la chiusura, il diario del wipe diceva «Rimandato» per un PID aperto da un giorno e mezzo, e il promemoria di chiusura continuava ad affermare che l'hook faceva il wipe da solo. Il rinvio era scritto, ma in un file che nessuno apre.

```
powershell -NoProfile -ExecutionPolicy Bypass -File tools/stato-magazzino.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File tools/stato-magazzino.ps1 -Dettagli
powershell -NoProfile -ExecutionPolicy Bypass -File tools/stato-magazzino.ps1 -SenzaTesti
powershell -NoProfile -ExecutionPolicy Bypass -File tools/stato-magazzino.ps1 -Chiudi <PID>
powershell -NoProfile -ExecutionPolicy Bypass -File tools/stato-magazzino.ps1 -Autotest
python3 tools/stato-magazzino.py
python3 tools/stato-magazzino.py --chiudi <PID>
python3 tools/stato-magazzino.py --autotest
```

Dal 2026-10-09 lo strumento è anche la libreria con cui il wipe decide che cosa conservare: `session-end-wipe.ps1` lo carica con `-Libreria` e ne usa `Get-Protezione`, `session-end-wipe.sh` interroga `stato-magazzino.py --protezione-sh`, così che ciò che l'utente vede come aperto sia esattamente ciò che il wipe conserva. Per un processo vivo senza file di sessione legge dal processo stesso, in sola lettura, `CLAUDE_CONFIG_DIR` e la cartella corrente, dal PEB su Windows e da `/proc` su Linux, e limita le candidate a quel progetto di quell'account; l'ipotesi a tre candidate prese da tutti gli account resta solo per i processi non leggibili. La prova `tests/test-wipe-per-sessione.ps1` ne ha uno scenario, il settimo, e lo stesso vale per la gemella Linux; il diario del wipe riporta anche le rimozioni per categoria. Per questo va installato accanto al wipe, in `<CLAUDE_CONFIG_DIR>/hooks/`, e `check-account-hygiene` segnala la sua assenza. La variante Windows mostra in più le sessioni di Codex per radice, vive e chiuse, con il comando di `Pulisci-Codex.ps1` del pacchetto `agenti-terminale`, il conteggio di scratchpad e log MCP comuni a tutti gli account, e un avviso quando VS Code è aperto, perché il pannello delle sessioni dell'estensione mostra anche sessioni già cancellate finché VS Code non viene chiuso del tutto. La variante POSIX, `stato-magazzino.py`, ha il resoconto compatto e `--chiudi`, non `-Dettagli` né la sezione di Codex, il cui pacchetto esiste solo per Windows; l'autotest copre 16 casi, verdi su Windows e su Ubuntu.

Di default la stampa è compatta, una riga per sessione in tre blocchi, perché la prima versione, con titolo, prima e ultima richiesta di ogni sessione, non lasciava distinguere a colpo d'occhio la sola cosa che serve decidere: quali sessioni sono aperte e quali sono chiuse e aspettano soltanto il wipe. *Aperte ora* sono quelle legate a un processo vivo. *Chiuse, da pulire* sono tutti gli altri verbali, e una riga porta il segno «forse PID» quando un processo vivo senza file di sessione potrebbe esserne ancora il proprietario. *Cosa fare* dice per ogni account quante chiuse restano, perché, e il comando. `-Dettagli` stampa il resoconto completo descritto qui sotto.

Le sessioni aperte si individuano con lo stesso criterio della guardia del wipe, così che i PID mostrati siano quelli che il wipe conta. Per ciascuna si stampano l'avvio, la catena di processi che la ospita, cioè il terminale, CPU e memoria, e il legame con un account. Il legame è *certo* quando `<account>\sessions\<pid>.json` esiste e il suo istante di avvio coincide con quello del processo entro due secondi, perché un PID riusato ha lo stesso numero e un altro avvio. Altrimenti è un'*ipotesi*: si propongono i verbali che hanno avuto attività dopo l'avvio e che nessuna sessione legata con certezza rivendica, prima quelli nati dopo l'avvio e poi quelli più vecchi, che una sessione ripresa continua. Per ogni account seguono l'esito dell'ultimo wipe letto dal diario, ogni progetto rimasto con ogni sessione, e per ciascuna date, dimensione, numero di richieste, ramo, titolo, prima e ultima richiesta. Seguono poi le cartelle effimere, gli scratchpad condivisi e un riepilogo che per ogni account dice quanto resta, perché, e il comando da lanciare. I testi si ricavano dalle sole righe `ai-title` e `last-prompt` dei verbali, senza leggerli per intero: il 2026-10-08, su quattro home con otto progetti e quattordici sessioni, la più grande di 23 MB, il resoconto ha richiesto 1,8 secondi. Poiché quei testi possono contenere dati personali, `-SenzaTesti` li omette.

Lo strumento non cancella e non chiude nulla da sé. `-Chiudi <PID>` mostra la sessione e chiede di riscrivere il PID da tastiera; rifiuta un processo che non è una sessione di Claude Code o che è un antenato dello strumento stesso, e lanciato dall'agente, che non ha una tastiera, si ferma. Chiudere così una sessione salta il suo hook `SessionEnd`, quindi il wipe va rilanciato dopo. Si installa come il wipe, in `<CLAUDE_CONFIG_DIR>\hooks\`, e `agenti-terminale/tools/Installa-Claude.ps1` lo copia insieme a esso; `chiudi-sessione.ps1` lo esegue in coda al passo di wipe, cercandolo accanto a sé e poi nelle home degli account. La prova `-Autotest` costruisce un magazzino finto e verifica, con un gemello negativo per ogni caso, l'estrazione dei testi, la lettura del diario, il legame certo, il PID riusato, l'ordine delle ipotesi e i rifiuti di `-Chiudi` e la divisione fra aperte e chiuse. Esiste solo la variante Windows.

## scrub-claude-json.js

Companion di `session-end-wipe`: rimuove da `.claude.json` le sole voci di `projects` i cui percorsi non iniziano con uno dei prefissi da preservare, lasciando intatto tutto il resto del file, login e credenziali compresi. Si installa accanto allo script di wipe, in `<CLAUDE_CONFIG_DIR>\hooks\scrub-claude-json.js`, e non si invoca a mano: lo chiama il blocco 4 del wipe, una volta sul file di configurazione e una sull'eventuale `.claude.json.backup`, che altrimenti conserverebbe le stesse voci.

```
node scrub-claude-json.js <percorso .claude.json> <prefisso> [<prefisso> ...]
```

I prefissi sono percorsi e non slug, passati come argomenti distinti perché i percorsi con spazi non richiedano accorgimenti: su Windows di norma la radice del disco dei progetti (`D:`, `E:`), su POSIX la radice della cartella di sviluppo (`/home/utente/dev`). Il confronto e case-insensitive, che è cio che serve su Windows dove lo stesso progetto compare a volte come `e:/x` e a volte come `E:/x`, ed è comunque il verso prudente per uno script distruttivo. Attenzione a una trappola nel provarlo da Git Bash su Windows: la shell converte gli argomenti che sembrano percorsi POSIX in percorsi Windows prima di passarli a `node.exe`, quindi per un test con prefissi in forma `/home/...` serve `MSYS2_ARG_CONV_EXCL='*'`.

Il passaggio e in Node e non in PowerShell per una ragione precisa: `ConvertFrom-Json` di PowerShell 5.1 tratta le chiavi JSON come case-insensitive e va in errore su un `.claude.json` che contenga sia `e:/progetto` sia `E:/progetto`, condizione tutt'altro che rara. `JSON.parse`/`JSON.stringify` e invece la stessa semantica che Claude Code applica al proprio file. Poiché il file custodisce il login, non viene mai riscritto alla cieca: lo script verifica che l'oggetto in memoria contenga ancora `oauthAccount` e `userID`, valida il JSON prodotto, scrive su un file temporaneo, lo rilegge da disco e solo allora sostituisce l'originale; qualsiasi anomalia annulla tutto, lasciando il file intatto e senza residui. Se Node non è disponibile il wipe salta il passaggio senza toccare nulla.

## lint-doc-references.py

Trova nella documentazione i riferimenti a file che non esistono. Non verifica se una descrizione sia vera, che è un giudizio: verifica se l'oggetto di cui parla esista, che è il sottoinsieme controllabile del problema ed è quello che sul progetto di origine aveva prodotto un documento di contesto primario che descriveva un file mai esistito.

Divide in categorie invece di produrre un elenco unico, e la ragione vale come criterio generale di ogni controllo automatico: cento segnalazioni di cui novanta legittime insegnano a ignorare le altre dieci. Sono da correggere i documenti vivi che nominano un file assente; sono storici il work-log e le schede datate, dove una voce che nomina un file poi cancellato era vera quel giorno; sono modelli i percorsi sotto `templates/`, che sono convenzioni per un progetto che non è questo. La quarta categoria si attiva solo su dichiarazione esplicita e riguarda un repository solo, cioè quello che contiene lo standard invece di averlo adottato.

Le radici che identificano un percorso non si configurano: si leggono da git. Un elenco scritto a mano sarebbe un secondo posto dove vive lo stesso fatto, e divergerebbe in silenzio, perché il sintomo di una cartella non controllata e l'assenza di segnalazioni.

Dal 2026-10-20 c'è una quinta categoria, che vale solo in un progetto ospite: propagato. Un documento che scrive l'allineamento, cioè regole, norme, `PROJECT-SYSTEM.md`, prompt e le skill che il template porta, lette dall'elenco delle skill di sistema e dall'elenco `spediti` del registro delle fonti a monte, non lo corregge il progetto, quindi un suo riferimento rotto si mostra e non ferma la chiusura; lo corregge il template, che quei documenti li controlla in modalità bundle. Nasce dalle lezioni L-002 e L-005 di un progetto istanziato: il marcatore sulla riga era un rimedio puntuale, e la skill `riprendi` del 2026-10-20 ha riaperto il difetto in quattro dei sei progetti che lanciano il controllo.
```
python tools/lint-doc-references.py
python tools/lint-doc-references.py --solo-vivi
python tools/lint-doc-references.py --bundle
python tools/lint-doc-references.py --self-test
```

## test-identita-personali.py

Tiene i dati del profilo personale del proprietario fuori dai repository aziendali, con due barriere. Il 2026-10-21 una vecchia regola del template sulle identità git, con dentro il profilo personale, si è trovata committata e spinta in dieci repository aziendali, e toglierla ha richiesto di riscriverne la storia; lo stesso giorno si è visto che un dato del genere poteva entrare anche scritto a mano nella documentazione di un progetto.

Senza opzioni, nel template, cerca le voci dell'elenco nei file tracciati sotto `.claude/`, cioè in ciò che l'allineamento propaga: `chiudi` lo lancia e ferma il commit del template, `allinea-tutti.ps1` lo lancia e non parte, e in questo modo un elenco mancante ferma, perché un controllo senza elenco direbbe sempre pulito. Con `--stage`, in qualunque progetto, cerca le voci nei file in stage letti dall'indice e nell'identità con cui il commit verrà firmato, autore e committer: `chiudi` lo lancia fra lo stage e il commit e, se trova qualcosa, toglie lo stage e si ferma; il passo `.githooks/pre-commit.d/identita-personali`, modello in `.claude/templates/readme-sync/githooks/pre-commit.d/`, fa lo stesso nei commit manuali.

L'elenco non è mai versionato. Nel template sta in `_notes/allineamento/identita-personali.txt`; il controllo dei commit usa quello della macchina, `~/.config/identita-personali.txt`. Una voce in chiaro si cerca come sottostringa; una voce `sha256:<impronta>`, prodotta da `--impronta "testo"`, si confronta con l'impronta di ogni parola e di ogni email della riga, ed è la forma installata il 2026-10-21 su questo PC e sulle sei VM, dove il dato in chiaro non deve stare. Le righe `ambito: <frammento>` dicono quali repository della macchina sono aziendali, per frammento di remoto o di email: dove ce ne sono, il controllo dei commit vale solo lì, perché su questo PC i progetti personali si firmano legittimamente con l'identità personale; dove non ce ne sono, come sulle VM, vale ovunque. Senza elenco sulla macchina il controllo dei commit avvisa a ogni commit e non ferma.

Dal 2026-10-27 il controllo guarda **nei due versi**. Le righe `lavoro: <voce>` dell'elenco sono gli identificativi del profilo di lavoro e si cercano nei repository **fuori** dall'ambito aziendale: in un repository aziendale non deve comparire l'identità personale, in uno personale non deve comparire quella di lavoro, e il verso lo decide l'ambito e non chi lancia il comando. Nel template, che propaga in entrambi i tipi, si cercano tutte le voci. Il verso mancava, ed è il motivo per cui l'indirizzo di lavoro è rimasto quattro mesi dentro sette repository personali pubblici senza che nessun controllo lo vedesse.

`--tracciati` legge **tutti i file tracciati** del repository, non il perimetro del template e non il solo stage. Serve a ritrovare ciò che è entrato prima che il controllo esistesse: né `--stage`, che vede solo l'indice, né il controllo del template, che vede solo `.claude/`, rileggono mai un file già committato, e un dato entrato prima resta invisibile per sempre. Salta i binari e i file oltre 2 MiB.

Nel perimetro del template vale inoltre un controllo **sulla forma** e non sull'elenco: ogni stringa che abbia l'aspetto di un indirizzo email o di un nome di file di chiave SSH ferma il commit se non è dichiarata in `identita-forme-ammesse.txt`, accanto a questo README e versionato perché contiene solo esempi inventati. È il solo controllo che non dipende da un censimento: riconosce la forma del dato invece dei colpevoli già schedati, quindi ferma anche l'indirizzo di un collega o uno nuovo che nessuno ha pensato di aggiungere. Vale solo nel template, perché il `.claude/` di un progetto contiene legittimamente gli indirizzi del proprio dominio.

L'uscita **2** significa «non ho potuto guardare», ed è distinta sia dal successo sia dal reperto: elenco assente sulla macchina, oppure repository fuori ambito senza voci `lavoro:`. Prima questi due casi uscivano 0, cioè un controllo che non ha guardato si dichiarava verde. Il gancio pre-commit li tratta come rifiuto.

Se la copia del progetto è diversa da quella del template, lo strumento lo dice in testa all'uscita. Il percorso del template si legge da `~/.config/template-claude-path.txt`, file della macchina e non versionato, perché un percorso concreto dentro un file propagato è esattamente il difetto che questo strumento esiste per impedire.

Lo strumento non stampa mai l'identificativo, perché l'uscita finisce in log e trascrizioni. L'`--autotest` ha 31 casi, fra cui quello che riproduce il buco: un file già committato che `--stage` e il controllo del template dichiarano entrambi pulito e che solo `--tracciati` trova.

```
python .claude/templates/tools/test-identita-personali.py
python .claude/templates/tools/test-identita-personali.py --stage
python .claude/templates/tools/test-identita-personali.py --tracciati
python .claude/templates/tools/test-identita-personali.py --impronta "testo"
python .claude/templates/tools/test-identita-personali.py --autotest
```

## verifica-ripresa.py

Dice, alla riapertura di una sessione, se fra l'ultima e questa si e perso qualcosa. Confronta l'impronta registrata a fine sessione, cioè il commit e la forma dell'albero di lavoro in quel momento, con lo stato reale, e riporta i commit comparsi dopo l'ultima registrazione, i file rimasti a meta, i documenti di memoria che dichiarano un commit più vecchio di HEAD e le schede ancorate a un commit che non esiste.

Il danno che intercetta non è la perdita del lavoro, che sta su disco e in git, ma il fatto che una sessione nuova prenda un file di ripresa vecchio per lo stato corrente: un file di ripresa non aggiornato ha esattamente lo stesso aspetto di uno aggiornato. La skill `riprendi` e la procedura che ne interpreta l'esito.

Da riga di comando e in CI esce con un codice diverso da zero quando trova una divergenza. Un hook invece lo chiama con `--hook`, che stampa la stessa riga di `--breve` ed esce sempre con zero, oppure attraverso i wrapper di `hooks-starter`, che fanno lo stesso: Claude Code tratta come errore un'uscita diversa da zero, scarta lo standard output e mostra una riga di fallimento vuota, quindi l'avviso sparirebbe proprio quando c'è. È la lezione L-002 di un progetto istanziato, recepita il 2026-10-21 con il codice che quel progetto aveva scritto.

```
python tools/verifica-ripresa.py
python tools/verifica-ripresa.py --registra
python tools/verifica-ripresa.py --breve
python tools/verifica-ripresa.py --hook
python tools/verifica-ripresa.py --self-test
```

## verifica-schede.py

Misura le schede di `.claude/context/` rispetto al codice che dichiarano di coprire. È il confronto della skill `sync-context` reso meccanico, con tre cecità di quel confronto trasformate in difetti che fanno fallire: una scheda con `covers-paths` ma senza `last-verified-commit`, che nessun confronto guarda; un'ancora che non è un commit del repository, come il segnaposto `PENDING-FIRST-COMMIT` dimenticato dopo il primo commit; un percorso coperto che non corrisponde a nessun file, che segna sempre verde. Le schede superate, cioè con file coperti cambiati dopo l'ancora, sono informazione; con `--rigoroso` fanno fallire anch'esse, ed è la forma da usare quando si dichiara di aver allineato tutto.

Nato in un progetto istanziato, dove la prima corsa ha trovato tre schede mai ancorate dopo che il confronto per commit le aveva date per allineate per tre mesi. Non vede la quarta cecità della skill, cioè una scheda ancorata mentre già divergeva: quella si trova soltanto confrontando per contenuto.

```
python tools/verifica-schede.py
python tools/verifica-schede.py --rigoroso
python tools/verifica-schede.py --self-test
```

## chiudi-sessione.ps1 / chiudi-sessione.sh / installa-chiudi.sh

Chiude una sessione con un comando solo, nell'ordine in cui i passi non si danneggiano a vicenda. Mostra ramo, file cambiati e diff riassuntivo senza pager; trova da solo i controlli istanziati nel progetto e li esegue tutti, fermandosi prima del commit se uno fallisce; prende il messaggio di commit da `-Messaggio`, oppure da `_notes/COMMIT-MSG.txt` che l'agente prepara a fine lavoro, oppure lo chiede; chiede conferma, committa tutto e pusha; verifica che HEAD coincida con il ramo remoto; registra l'impronta con `verifica-ripresa.py --registra`; infine esegue lo script di wipe di ogni account che ne ha uno installato, ma solo se nessun processo Claude Code da terminale o da editor è ancora aperto, altrimenti stampa i comandi da lanciare dopo.

Si lancia dal proprio terminale dopo aver chiuso Claude Code, perché il wipe lavora sui file che Claude riscrive finché è aperto. Commit e push restano un gesto dell'utente: è l'utente a lanciare lo script e a confermare dopo aver visto file e messaggio, e l'agente prepara il messaggio senza usarlo. Nel repository del template lo script riconosce di essere nel bundle e aggiunge ai controlli le opzioni `--bundle`, `--includi-modelli` e `--oracle require`, più i controlli propri del bundle.

```powershell
.\tools\chiudi-sessione.ps1
.\tools\chiudi-sessione.ps1 -SoloControlli
.\tools\chiudi-sessione.ps1 -Messaggio "Aggiornato X: cosa cambia" -Si
.\tools\chiudi-sessione.ps1 -NoWipe
.\tools\chiudi-sessione.ps1 -NoPush
.\tools\chiudi-sessione.ps1 -Account account2
```

```bash
bash tools/chiudi-sessione.sh
bash tools/chiudi-sessione.sh --solo-controlli
bash tools/chiudi-sessione.sh -m "Aggiornato X: cosa cambia" --si
bash tools/chiudi-sessione.sh --no-wipe
bash tools/chiudi-sessione.sh --no-push
bash tools/chiudi-sessione.sh --account account2
```

Su Linux e macOS il comando breve `chiudi` si installa una volta nel profilo Bash o Zsh con `bash .claude/templates/tools/installa-chiudi.sh`, eseguito dal clone del template. L'installatore sceglie `~/.bashrc` o `${ZDOTDIR:-$HOME}/.zshrc`, salva una copia `.chiudi.bak` prima di modificare un profilo esistente e sostituisce solo il proprio blocco delimitato; `--verifica` controlla senza scrivere, `--shell bash|zsh` e `--profilo <percorso>` permettono una scelta esplicita. Dopo l'installazione si apre una nuova shell. La funzione cerca `chiudi-sessione.sh` nel repository corrente, prima in `tools/` e poi nel bundle sotto `.claude/templates/tools/`, e inoltra gli argomenti: `chiudi --solo-controlli`, `chiudi -m "Aggiornato X: cosa cambia"`, `chiudi --no-wipe`. Non dipende dal percorso del clone usato per installarla.

Esce 1 e non committa niente se un controllo fallisce, se il messaggio è vuoto, se la conferma manca o se l'hook di pre-commit rifiuta; esce 1 senza registrare l'impronta se il push non arriva al remoto; esce 3 quando commit e push sono riusciti ma un passo successivo, tipicamente la registrazione dell'impronta senza `_notes/RESUME-PROMPT.md`, ha dato KO, così la riga finale non dichiara completata una chiusura che non lo è. Il push si ritenta da sé fino a tre volte, con attese di cinque e quindici secondi, perché un push caduto sulla rete non è un push rifiutato: il 2026-10-13 dieci push su due tornate di chiusura sono caduti su timeout SSH verso GitHub, e ogni volta bastava rilanciare. Se anche il terzo tentativo non arriva, lo script si ferma senza registrare l'impronta; rilanciarlo dopo aver risolto non ricommitta, perché con l'albero pulito passa direttamente al push e alla registrazione. I casi del ramo nuovo senza ramo remoto, del repository senza `origin`, dell'HEAD staccato e dell'uscita 3 sono stati provati il 2026-09-24 in entrambe le varianti su cloni temporanei con un remoto finto. La variante Bash e l'installatore hanno inoltre prove isolate in `tests/test_chiudi_linux.py`, eseguite su Ubuntu WSL. La guida d'uso completa, in ordine cronologico e con i casi d'uso, è `docs/guida-sessione.html` del template. `_notes/COMMIT-MSG.txt` si cancella dopo un commit riuscito, così un messaggio vecchio non viene riusato alla sessione successiva. Lavora sul ramo in uscita, qualunque sia, e lo nomina nella richiesta di conferma: il push indica sempre `origin` e il ramo corrente, collega il ramo remoto con `-u` e legge direttamente il suo hash per la verifica; un repository senza remoto `origin` committa in locale e salta il push, mentre con HEAD staccato lo script si ferma prima dei controlli senza committare niente.

Non ha regole proprie: applica quelle del progetto e lascia lavorare i presidi che esistono già. Dichiara cartella, ramo e stato prima di tutto, come chiede `git-commands-format.md`; si ferma se mancano `user.name` e `user.email` locali e stampa l'autore accanto al messaggio, come chiede il riferimento della skill `identita-git`; per il messaggio si affida all'hook `.githooks/commit-msg`, che rifiuta le attribuzioni a un agente e l'oggetto oltre i 72 caratteri per ogni commit, non solo per i suoi. È lo stesso per Claude Code e per Codex, perché la chiusura non dipende da quale agente ha lavorato. Su Windows `Installa-Comandi.ps1` del pacchetto `agenti-terminale` mette nel profilo PowerShell la funzione `chiudi`, che trova lo script nel repository in cui si trova il terminale e gli passa gli argomenti: `chiudi`, `chiudi -SoloControlli`. Su Bash e Zsh la installa `installa-chiudi.sh` con la stessa ricerca dal repository corrente. Lo stesso comando fissa anche le milestone a metà sessione: quando un blocco coerente è concluso l'agente scrive il messaggio in `_notes/COMMIT-MSG.txt` e propone di lanciare `chiudi`, una milestone per commit, e il wipe si salta da solo finché la sessione è aperta; la convenzione sta nella sezione "Milestone" di `.claude/rules/git-commands-format.md`.

## check-eol.py

Segnala i file di testo che mescolano CRLF e LF nello stesso file. La convenzione Markdown del sistema prescrive di conservare la fine riga di ciascun file, e md-unwrap la rispetta per contratto: ne segue che l'albero contiene legittimamente entrambe le convenzioni, e che nessun altro controllo si accorge se un file le mescola, perché il rendering a video è identico e la catena tipografica guarda i caratteri e non le interruzioni.

Un file misto non è un problema estetico. Con `core.autocrlf` a false e senza `.gitattributes` git registra le fini riga così come stanno sul disco, quindi il file misto entra nella storia, e alla prima riscrittura da parte di qualunque strumento le interruzioni si uniformano, trasformando una modifica di due righe in una modifica dell'intero file. È di sola lettura e non converte niente, perché la decisione su quale fine riga tenere resta di chi conosce il file.

```
python tools/check-eol.py
python tools/check-eol.py --dettaglio
```

C'è un caso che questo controllo non vede per costruzione: il file convertito **per intero**, che resta coerente e quindi non è misto. Succede ogni volta che un file LF viene riscritto su Windows da uno script Python aperto in modo testo, perché in scrittura ogni `\n` diventa `\r\n`: una sostituzione di due righe produce un diff dell'intero file, e se nessuno guarda la statistica del diff entra così nella storia. Osservato il 2026-09-30 in un progetto istanziato, su quattro file in un solo giro, fra cui un componente di cui si cambiavano due righe e che il diff mostrava riscritto per intero. Il sintomo è un `git diff --stat` sproporzionato rispetto alla modifica. Il controllo è `git ls-files --eol <file>`, che mostra `i/lf w/crlf` quando l'indice e il disco divergono. Il rimedio è a monte: uno script che modifica un file lo legge e lo scrive in binario, oppure con `newline=""` sia in lettura sia in scrittura, così che le interruzioni escano come erano entrate.

## check-copie-modelli.py

Confronta ogni strumento istanziato con il suo modello sotto `.claude/templates/`. Un progetto che adotta lo standard copia gli strumenti condivisi dentro la propria anatomia, e dal momento della copia le due esistono in parallelo senza che niente le tenga insieme: si corregge la copia, perché è quella che gira, e il modello resta indietro.

Il modo in cui questo difetto si manifesta è il peggiore possibile, perché non si manifesta nel repository dove nasce. Il 2026-09-16, in questo bundle, i tre strumenti tipografici avevano ricevuto una guardia che impedisce di riscrivere le copie dei modelli: la guardia era entrata nelle copie sotto `tools/`, dove era stata provata, e non nei modelli. Tutte le prove passavano, perché le prove girano sulle copie, e il difetto sarebbe comparso soltanto nei progetti allineati dopo, sotto forma di strumenti privi di una protezione che la documentazione dichiarava presente.

La corrispondenza fra modello e copia si deduce dalla struttura e non da un elenco: dentro un pacchetto, una cartella che si chiama come una dell'anatomia ospite (`tools`, `hooks`, `rules`, `skills`, `agents`, `commands`) atterra nella cartella omonima del progetto. I README dei pacchetti non hanno copia e non entrano nel confronto; i file che si istanziano proprio per essere adattati, come l'elenco di esclusioni di `fix-dashes`, stanno in una lista di eccezioni dichiarate con il motivo, perché altrimenti produrrebbero una segnalazione perpetua. Un modello senza copia non è un difetto ma un pacchetto non adottato, e si conta senza elencarlo salvo `--tutti`.

```
python tools/check-copie-modelli.py
python tools/check-copie-modelli.py --tutti
python tools/check-copie-modelli.py --allinea
python tools/check-copie-modelli.py --self-test
```

## check-catalogo.py

Verifica che il catalogo dei pacchetti in `.claude/templates/PACKAGES.md` descriva il disco. Le due cose divergono in tre modi, tutti muti: una riga nomina una cartella che non esiste più e il gate propone un pacchetto inesistente; una cartella non ha riga e il pacchetto non viene proposto a nessuno, il che è indistinguibile dall'averlo escluso di proposito; e i totali dichiarati in prosa restano al numero che era giusto quando qualcuno li ha scritti.

Il terzo caso è quello che si nota di meno, ed è il motivo per cui lo strumento esiste: il 2026-09-16 il catalogo dichiarava settantatré voci e ne aveva settantaquattro, mentre `docs/feature-map.html` ne dichiarava sessantuno. Tre numeri per lo stesso fatto, nessuno dei quali sbagliato nel momento in cui era stato scritto.

I totali in prosa non si cercano con una espressione regolare, e la ragione vale come criterio generale. Il testo dice anche che un progetto appartiene a due o tre settori, e quel tre non è un totale ma una osservazione: una regola che cercasse un numero seguito da "settori" segnalerebbe entrambi, e un controllo che segnala ciò che è corretto insegna a ignorarlo. Le affermazioni verificate stanno quindi in un elenco dichiarato, una riga per frase, con accanto che cosa quella frase conta; `--censimento` elenca i numeri candidati perché trovarne di nuove non richieda di ricordarsele. I numeri si leggono in cifre e in lettere italiane fino a novantanove, contrazioni comprese.

```
python tools/check-catalogo.py
python tools/check-catalogo.py --censimento
python tools/check-catalogo.py --self-test
```

## latest-screenshot.ps1

Restituisce il percorso dell'immagine più recente nella cartella di cattura di Screenpresso e la sua eta in secondi, perché l'agente legga lo screenshot appena catturato dall'utente per un passo manuale e visivo dello sviluppo. Si usa insieme alla regola `.claude/rules/manual-screenshots.md`, che stabilisce quando l'agente deve chiedere uno screenshot.

```
powershell -NoProfile -ExecutionPolicy Bypass -File tools/latest-screenshot.ps1
```

Cartella di default `%USERPROFILE%\Pictures\Screenpresso`, sovrascrivibile con `-Folder`. Con `-MaxAgeSeconds N` pretende che l'immagine più recente sia stata salvata da meno di N secondi, per non leggere per errore uno screenshot vecchio. Esce 0 se trova un'immagine valida, 1 altrimenti.

## claude-incognito.ps1 / claude-incognito.sh

Avvia una sessione Claude Code effimera: redirige `HOME` e le cartelle XDG su una directory temporanea e azzera `CLAUDE_CONFIG_DIR`, così la sessione non legge ne scrive nell'account reale e parte vergine; la temp si rimuove alla chiusura. Complementa `session-end-wipe` (quello pulisce dopo, questo non scrive nemmeno) ed è utile per lavorare su materiale sensibile.

```
powershell -NoProfile -ExecutionPolicy Bypass -File tools/claude-incognito.ps1 -ProjectDir "<percorso>"
```

Su Linux la variante e `claude-incognito.sh` (`bash claude-incognito.sh <percorso>`). La tecnica si basa sulla specifica XDG Base Directory più la redirezione di `HOME`; vedi PROJECT-SYSTEM.md sezione 15.

## allinea-dal-template.py

Allinea un progetto istanziato alla testa del template senza modello linguistico, usando la storia git del template come arbitro. Per ogni file del perimetro, cioè `PROJECT-SYSTEM.md`, `rules/`, le skill di sistema, `templates/`, gli strumenti di codice copiati sotto `tools/` e le guide copiate sotto `docs/<pacchetto>/` e, dove il progetto ha `.githooks/pre-commit.d/`, i passi di sistema dell'hook come `identita-personali`, che aggiunge se mancano, calcola l'hash di blob git del file locale a fini riga normalizzate e lo cerca fra tutti i blob che quel percorso ha avuto nel template, rinomine comprese. Un riscontro significa che la copia locale è una versione vecchia mai toccata, e si aggiorna senza perdere niente; nessun riscontro significa che è stata modificata sul posto, e si fonde a tre vie con `git merge-file` su una base che va indovinata, perché l'antenato vero non è osservabile. Il risultato di quel merge si misura invece di crederlo, e la ragione sta nella sezione seguente. Quando nessuna base produce un merge verificato, lo strumento guarda le righe del file che non compaiono in nessuna versione storica del template: se non ce n'è nessuna, oppure sono tutte righe che `--righe-comuni` dichiara condivise fra progetti, il file è una copia anteriore alla storia registrata e si aggiorna alla testa con l'esito SUPERATO, elencato perché una riga tolta di proposito nel progetto tornerebbe; se invece il file ha righe sue da salvare l'esito è CONFLITTO, con la nota che dice quante righe della testa il merge non consegnerebbe e quante ne duplicherebbe. Un file modificato che contiene già tutte le modifiche del template, e non ne perde nessuna, è una personalizzazione e non si tocca. Non tocca mai `memory/`, `context/`, `settings` né i file di dati istanziati sotto `tools/`, perché descrivono il progetto; `CLAUDE.md`, in radice oppure sotto `.claude/` dove il progetto lo tiene, lo tocca soltanto con `--innesco`, e soltanto per aggiungere le righe di innesco delle skill con `RIFERIMENTO.md` che il file non nomina ancora come skill, prese da `templates/CLAUDE.md` e scritte in coda all'indice esistente oppure prima della sezione degli apprendimenti recenti, con l'esito INNESCO. Un file che il progetto ha risolto a mano si registra con `--risolto <percorso>` in `.claude/allineamento-risolti.json`, versionato nel progetto insieme al blob della testa contro cui la risoluzione è stata fatta: da quel momento il file è ADATTATO finché il template non lo cambia di nuovo, e allora torna a chiedere attenzione.

```powershell
python .claude/templates/tools/allinea-dal-template.py --template E:/template-claude-developing --progetto .
python .claude/templates/tools/allinea-dal-template.py --template E:/template-claude-developing --progetto . --applica --rimuovi
python .claude/templates/tools/allinea-dal-template.py --template E:/template-claude-developing --progetto . --applica --innesco
python .claude/templates/tools/allinea-dal-template.py --template E:/template-claude-developing --progetto . --risolto tools/export-discord.py
```

Legge soltanto la storia committata del template: una modifica non committata al template non si propaga, ed è voluto. Esce con 0 senza conflitti, con 1 se ne restano, con 2 per un errore. La fine riga di un file esistente si conserva.

### Perché il risultato del merge si misura invece di crederlo

Una base indovinata sbaglia in silenzio, e in due direzioni opposte, e la propagazione del 2026-09-28 le ha prodotte entrambe nello stesso giro. Se la base è più recente dell'antenato vero, la differenza base-testa non contiene una correzione che il file locale non ha, e quella correzione non arriva a nessuno: in `rodrainaudio-reverse-eng` `fix-accents.py` ha ricevuto il blocco di righe nuove ma non la guardia del 2026-09-09, perché la base scelta la conteneva già. Se la base è più vecchia, la differenza contiene l'aggiunta di un paragrafo che il file locale ha già per conto suo, e il merge ne scrive due copie: in `holiday-template` e in `local-audio-transcriptor` il `PROJECT-SYSTEM.md` si è ritrovato due volte il paragrafo su `studio-didattico`. Nessuno dei due casi produce un conflitto, quindi nessuno dei due si vede.

Da qui le due misure sul risultato, entrambe come differenze di multinsiemi di righe non vuote, cieche a uno spostamento e sensibili a una perdita o a un raddoppio: quante righe della testa il risultato non consegna, e quante ne compaiono più volte del massimo fra copia locale e testa. La base più vicina per contenuto resta la prima ipotesi, e nel caso normale si paga un solo `git merge-file`; se non supera la verifica si provano le altre versioni candidate, e solo se nessuna la supera si decide fra SUPERATO e CONFLITTO. Questo vale anche per ADATTATO, che dichiara "contiene già tutte le modifiche del template" ed è quindi un'affermazione verificabile.

La misura delle righe perse aveva però un falso positivo sistematico, che il 2026-09-29 ha tenuto `retrogame-mod-pok-dev` in CONFLITTO su undici file su undici senza niente da decidere: una riga della testa che il progetto ha adattato, un percorso o un nome, manca dal merge perché il merge ha tenuto la variante locale, e veniva contata come persa. Ora una riga della base si conta come adattata, e non come persa, quando nel confronto fra base e copia locale sta in un blocco sostituito le cui righe locali sono tutte proprie, cioè assenti da ogni versione del template, e una di esse le somiglia per almeno il sessanta per cento dei caratteri, una riga propria per una riga della base. Le due condizioni tengono fuori i due casi che la guardia esiste per prendere. Se la base è troppo recente, al posto della riga corretta il progetto ha la riga vecchia, che è testo storico del template, e la guardia resta. Se il progetto non ha mai ricevuto un blocco e nello stesso punto ha una riga sua, il blocco non somiglia alla riga, e la prova del paragrafo duplicato lo ha mostrato cadendo sulla prima stesura che la somiglianza non la chiedeva. La correzione ha portato i conflitti da 1 a 0 in `compilatore-documenti`, da 2 a 0 in `rodrainaudio-reverse-eng`, da 14 a 4 in `my-wedding-day`, da 3 a 2 in `my-cv` e in `diy-2way-monitors-home`, e da 11 a 5 in `retrogame-mod-pok-dev` misurato sul suo HEAD precedente all'allineamento a mano; i cinque rimasti erano divergenze volute, poi registrate con `--risolto`.

Quella somiglianza aveva un costo che nessun progetto vicino al template mostrava. Su un progetto mai allineato, fermo da mesi, le basi candidate di un file sono centinaia, i blocchi sostituiti sono lunghi e le righe, con la convenzione dei paragrafi su una riga, sono di migliaia di caratteri: la ratio di `difflib` calcolata su ogni coppia e ricalcolata per ogni base ha tenuto il processo a piena CPU per oltre nove minuti su `portale-asset-it` senza finire, il 2026-10-19, alla prima passata sui progetti via SSH. La funzione `somiglianza` decide ora come prima con meno lavoro: `real_quick_ratio` e `quick_ratio` sono limiti superiori della ratio, quindi una coppia che non li supera non l'avrebbe superata, e una coppia già calcolata per un'altra base si legge da una cache. Sullo stesso progetto, clonato in locale, la misura è passata a 74 secondi; su `my-wedding-day`, `log-collector`, `diy-2way-monitors-home` e `harmony-book` i rapporti della versione vecchia e di quella nuova sono identici byte per byte.

Le prove stanno in `tests/test_allinea_dal_template.py`: costruiscono un repository git finto la cui storia riproduce i due meccanismi, con le proporzioni fra i blocchi prese dai file veri, perché sono le proporzioni a decidere quale base la somiglianza sceglie. La verifica di non vacuità è stata eseguita il 2026-09-28 rimettendo un difetto alla volta: senza il controllo sulle righe perse cadono 4 prove, senza quello sulle duplicate 2, senza la ricerca sulle altre basi 1, e con il codice precedente a entrambe ne cadono 5. Le cinque prove del 2026-09-29, sulla riga adattata, sulla correzione mancata, sulla risoluzione registrata e sull'innesco, lanciate contro lo strumento di HEAD `065d0b5` ne vedono cadere 4: la quinta, sulla correzione mancata, passa su entrambe le versioni per costruzione, perché è la prova che la correzione non ha allentato la guardia. La prova della somiglianza del 2026-10-19 confronta la scorciatoia con la ratio piena su coppie che coprono le tre forme, quasi uguali, lontane per contenuto e lontane per lunghezza, più una coppia di pari lunghezza e caratteri diversi; senza quest'ultima la mutazione che sbaglia il ramo di `quick_ratio` sopravviveva, e con essa cadono entrambe le mutazioni provate.

## allinea-tutti.ps1

Porta allo stato corrente del template tutti i progetti che ne portano la struttura, cioè ogni cartella sotto le radici indicate, `D:\` ed `E:\` per default, che contiene `.claude/PROJECT-SYSTEM.md`. Non conosce i progetti per nome: li scopre a ogni corsa. È lo strumento da lanciare ogni volta che il template avanza.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .claude/templates/tools/allinea-tutti.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .claude/templates/tools/allinea-tutti.ps1 -Applica
```

La corsa ha tre fasi: guardie e prima misura; consenso, cioè le righe assenti da tutta la storia del template ma identiche nello stesso file di almeno `-Consenso` progetti, 3 per default, che vengono da una versione del template anteriore alla sua storia git; seconda misura con quelle righe e, con `-Applica`, scrittura. Sulla prima corsa del 2026-09-28 il consenso ha riconosciuto 9 righe in 4 file, tutte della vecchia regola sull'identità e della vecchia mappatura degli account, e ha portato i progetti con conflitti da 24 a 6 su 35. A vuoto misura e basta. Con `-Applica` scrive solo dove passano tutte le guardie: `.claude` del template committato, un solo processo alla volta, e per ogni progetto repository git, albero principale e non un worktree aggiuntivo, non un clone del template, nessun merge o rebase a metà, una branch in uscita, albero pulito, nessun conflitto. Dopo aver scritto rimisura e pretende zero file da trattare, e controlla che nessun file cambiato stia fuori da `.claude/`, `tools/` e `docs/`; poi esegue la prova interna di ogni strumento sotto `tools/` del progetto che l'allineamento ha appena riscritto e che una prova interna la dichiara, riconoscendola dal `--self-test` o dall'`--autotest` nel proprio sorgente invece di lanciarla alla cieca; solo allora scrive nel progetto `.claude/allineamento-template.json`, che dichiara a quale commit e a quale albero `.claude` del template la sua struttura corrisponde. Se una prova interna fallisce il progetto prende lo stato `prove-fallite`, finisce fra quelli da guardare a mano e **non** riceve il marcatore, perché un progetto i cui strumenti non girano non è un progetto allineato. Un progetto che il proprietario vuole fuori dalla passata, per esempio un repository aziendale con un'adozione volutamente leggera, si elenca in `_notes/allineamento/esclusi.txt` del template, una riga per percorso con il motivo dopo il cancelletto: prende lo stato `escluso`, sta fra i saltati per costruzione e non chiede niente finché la riga non si toglie. Il file sta in `_notes/` e non si versiona, perché i percorsi sono della macchina come quelli del registro. Passa sempre `--innesco` allo strumento, quindi le righe di innesco mancanti sono un esito azionabile: un progetto a cui mancano soltanto quelle è `da-allineare`, e con `-Applica` le riceve; `CLAUDE.md` è per questo l'unico file fuori da `.claude/`, `tools/` e `docs/` che l'allineamento può cambiare senza cadere in `fuori-perimetro`. Lo stato `fuori-perimetro` sottrae ciò che era già sporco prima della scrittura, non ciò che nasce durante la corsa: il 2026-10-13 la sessione viva in `network-design` vi ha creato uno script mentre la passata girava, e il progetto è finito fra quelli da guardare a mano pur avendo scritto esattamente i sette file del suo rapporto. È il verso giusto in cui sbagliare, perché il marcatore non viene scritto e `chiudi-allineamento.ps1`, che prende i soli progetti in stato `applicato`, lo salta invece di committare a scatola chiusa un albero che ha cambiato qualcun altro. Segnala anche, senza bloccare, il carico degli instruction file oltre soglia.

Quel passo risponde a una domanda sola, cioè se il codice appena scritto giri, e copre il caso di un aggiornamento o di una fusione a tre vie che lascia un file sintatticamente valido e funzionalmente rotto: è precisamente ciò che nessuno guarda dopo una passata riuscita. Non copre invece i presupposti sull'ambiente, e vale la pena dirlo perché il difetto che ha motivato il passo era proprio di quella specie: il 2026-09-28 due strumenti si fermavano con `ValueError` quando il bersaglio stava su un'unità diversa dalla radice, e la prova interna di uno dei due **passa anche sulla versione rotta**, perché esercita l'analisi del testo e non la gestione dei percorsi. Una prova interna copre ciò che il suo autore ha pensato di coprire, e un presupposto sull'ambiente non è quasi mai fra quelle cose.

La scoperta ha due limiti che è bene conoscere, perché entrambi producono un silenzio e non un errore. Guarda il primo livello di ogni radice, quindi un progetto annidato più in basso, come `D:\sviluppo-ninjaOne\telegram-notifications`, si raggiunge solo con `-Profondita 1`. E tratta solo le cartelle che hanno `.claude/PROJECT-SYSTEM.md`, perché quello è il marcatore di un progetto istanziato: una cartella che ha `.claude` ma non quel file non è istanziata, non entra nel registro e fino al 2026-10-13 non compariva da nessuna parte. Misurato quel giorno sulle due radici: dei nove progetti di `D:\` che dichiarano il sistema erano coperti tutti e nove, ma dodici cartelle con `.claude` e senza `PROJECT-SYSTEM.md` non erano mai comparse in nessuna corsa, e una di esse, `D:\<progetto-di-esempio>`, aveva una sessione di agente viva. Ora la corsa le elenca a parte, senza toccarle, perché istanziarle con `/init-project-system` o metterle in `esclusi.txt` è una decisione del proprietario; una riga in `esclusi.txt` le toglie anche da quell'elenco.

### Progetti dentro macchine raggiungibili via SSH

Fino al 2026-10-19 la passata guardava soltanto le radici locali, e i progetti istanziati dentro le macchine virtuali raggiungibili con un alias SSH restavano fuori senza che nessun conteggio lo dicesse: misurati quel giorno, sette progetti su sei macchine, nessuno con il marcatore di allineamento. Ora la corsa interroga ogni voce `Host` di `~/.ssh/config` senza caratteri jolly e che non punti a GitHub, oppure i soli alias di `-Ssh`, e cerca `.claude/PROJECT-SYSTEM.md` sotto `-RadiciRemote`, per default `~`, `/opt`, `/srv`, `/var/www` e `/home`, fino a `-ProfonditaRemota` livelli, 5 per default; `-SoloLocali` salta le macchine. Un progetto remoto si scrive `ssh://<alias>/<percorso>` e attraversa le stesse guardie, la stessa misura, lo stesso consenso, la stessa scrittura e le stesse prove interne di un progetto locale, perché tutte le operazioni passano da `trasporto-ssh.ps1`, qui sotto, invece di avere una seconda implementazione. Lo strumento di misura gira sulla macchina, con una copia del template in `~/.cache/template-claude-developing` che arriva come `git bundle` solo quando il suo HEAD differisce da quello locale, e il rapporto torna con `scp`: da lì registro e chiusura lo trattano come gli altri.

Un progetto remoto si tocca solo se il proprietario lo ha approvato in `_notes/allineamento/remoti-approvati.txt`, una riga `ssh://<alias>/<percorso>` con il motivo dopo il cancelletto. Uno nuovo, anche su una macchina già nota, prende lo stato `da-confermare`: si elenca, non si misura e non si scrive, e la corsa esce con 1, perché una macchina nuova con progetti di sviluppo si decide e non si scopre. `esclusi.txt` accetta anche `ssh://<alias>`, che esclude l'host intero senza nemmeno interrogarlo. Una macchina che non risponde, che non ha `git` o `python3`, o su cui il template non arriva, si elenca fra quelle da guardare e la corsa esce con 1: un progetto che la passata non vede resta indietro in silenzio, ed è il difetto che questa sezione chiude.

Il registro di quali progetti sono allineati, e a quale commit, sta in `_notes/allineamento/registro.json` del template, ignorato da git perché contiene percorsi di progetti; ogni corsa lascia accanto il proprio log e i rapporti JSON. Commit e push restano manuali, progetto per progetto, e li chiude `chiudi-allineamento.ps1`, qui sotto, che legge quei rapporti; la memoria e i conflitti veri si chiudono con una sessione nel progetto, che registra con `--risolto` i file risolti a mano. Esce con 0 quando tutto è allineato o applicato, con 1 quando qualche progetto va guardato, con 2 quando una guardia iniziale fallisce.

## chiudi-allineamento.ps1

Chiude la passata: committa e spinge, progetto per progetto, i soli file che la passata ha scritto. È il passo che prima si faceva a mano, con un blocco di comandi lungo quanto i progetti applicati.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .claude/templates/tools/chiudi-allineamento.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .claude/templates/tools/chiudi-allineamento.ps1 -Applica
```

Esiste per tre guasti misurati il 2026-10-13 su due tornate di chiusura a mano, e nessuno dei tre si evita scrivendo meglio il blocco, perché nessuno dei tre dipende da chi lo scrive. Nove push sono caduti su timeout SSH verso GitHub, lasciando altrettanti commit locali non spinti che nessun comando successivo segnalava. Una riga del blocco si è corrotta mentre la console la riceveva, `git push` è arrivato come `git push256c8b7"`, e la virgoletta aperta e mai chiusa ha mandato PowerShell sul prompt di continuazione, dove ha inghiottito in silenzio le sessanta righe seguenti. E in tre progetti su ventinove `git add -A` avrebbe preso anche il lavoro di un'altra sessione aperta sullo stesso albero, perché il suo perimetro è l'albero e non l'allineamento. Per sapere che cosa fosse davvero arrivato sul remoto servirono tre giri di ricognizione repository per repository.

Quello che mette in stage non lo deduce dall'albero: lo legge dal rapporto JSON che la corsa ha già scritto per ogni progetto, dove ogni file porta il proprio esito. Sono scritti i file con esito `NUOVO`, `VECCHIO`, `SUPERATO`, `MERGE` e `INNESCO`, più la destinazione di uno `SPOSTATO`; sono rimossi l'origine di uno `SPOSTATO` e i `RIMOSSO`, più il marcatore `.claude/allineamento-template.json`. Lo stage è l'intersezione fra quell'elenco e ciò che nell'albero risulta davvero modificato, e la riga di esito dichiara quanti file sporchi sono rimasti fuori: quelli sono lavoro di qualcun altro e restano dove sono. Lo stato dell'albero si legge con `git status --porcelain -uall`, e l'opzione non è un dettaglio: senza, git riassume una cartella nuova in una sola riga che finisce con la barra, e l'intersezione con percorsi di file non troverebbe niente proprio dove la passata ha scritto di più.

Il push riprova da sé sugli errori di rete, con attese crescenti di cinque, quindici e trenta secondi, e `-Tentativi` ne cambia il numero; se non basta, il progetto resta elencato fra quelli da riprendere e `-SoloPush -Applica` rifà i soli push mancanti senza toccare altro. Senza `-Applica` non scrive niente e mostra che cosa farebbe. `-Solo` e `-Escludi` restringono per nome, `-SaltaPush` ferma al commit, `-Messaggio` sostituisce quello predefinito, che è `Allineamento dal template al commit <sha7>` e sta nei 72 caratteri che l'hook `commit-msg` pretende.

Una cosa che lo strumento non può garantire, e che perciò dichiara: lo stage si fonda su quali file la passata ha scritto, non su quali modifiche ha fatto, quindi un file che un'altra sessione ha riadattato dopo la corsa risulta comunque fra quelli da committare. L'intestazione stampa perciò quando la corsa è stata misurata e quante ore fa, e oltre le sei avverte di rileggere con `git diff` o di rifare prima la passata. Il caso è reale: lanciato mezz'ora dopo la corsa del 13/10 ha trovato in `log-collector` tre file che la sessione viva in quell'albero aveva nel frattempo adattati al proprio progetto.

Dal 2026-10-19 mette in stage anche il registro delle risoluzioni a mano, `.claude/allineamento-risolti.json`, e gli adattatori Codex sotto `.agents/skills/`, che la passata rigenera con `sync-codex-skills.py` subito dopo aver scritto: senza, un progetto che riceveva una skill nuova si trovava la chiusura ferma sulla sincronizzazione con Codex, come ha misurato e segnalato un progetto istanziato con `cerca-pacchetto`. L'`-Autotest` ha 16 casi su repository git temporanei, fra cui quei due e i tre del secondo remoto descritti più sotto, e ciascuno oppone ciò che deve entrare nel commit a ciò che non deve entrarci, perché uno strumento che mette in stage tutto passerebbe metà delle prove da solo: il file scritto dalla passata entra, il file nuovo dentro una cartella nuova entra, il file di un'altra sessione resta fuori, un albero pulito non produce un commit vuoto, la cancellazione decisa dalla passata entra come tale, senza `-Applica` non si committa, un progetto senza remoto non fa fallire la corsa, il push riprova e riesce, i tentativi esauriti lasciano l'esito fallito e non riuscito. La verifica di non vacuità è stata eseguita il 2026-10-13 con quattro mutazioni: ignorando il rapporto nello stage cadono 2 casi, committando anche a stage vuoto 1, dichiarando riuscito il primo push 2, togliendo `-uall` a `git status` 2; il ripristino è stato verificato byte per byte da copia.

Per un progetto `ssh://<alias>/<percorso>` stage, commit e push girano sulla macchina, quindi con l'identità git locale, il ramo, gli hook e le chiavi di quel progetto: il commit segue il version control del progetto e non quello della postazione. Le prove qui sopra non passano dal trasporto, e un trasporto che cita male un percorso o perde un codice di uscita le lascerebbe verdi: `-AutotestSsh <alias>` ripete lo stage selettivo su un repository di prova creato in `~/.cache` della macchina e cancellato alla fine, con un nome di file che contiene uno spazio, e nessun progetto viene toccato. Il 2026-10-19 su `studio` ha dato 8 casi su 8.

Un progetto può tenere lo stesso ramo su più remoti, e spingere solo l'upstream lascerebbe gli altri indietro di un commit a ogni passata. I remoti in più si dichiarano in `_notes/allineamento/push-remoti.txt` del template, una riga per progetto con il percorso seguito dai nomi dei remoti e il motivo dopo il cancelletto; dopo l'upstream lo script spinge il ramo corrente su ciascuno, solo se è indietro, e mai con forza, così un ramo divergente resta un `push fallito` da guardare e non un lavoro sovrascritto. Le prove interne coprono i tre casi, il secondo remoto che riceve il commit, l'upstream che lo riceve comunque e il remoto divergente che resta intatto, e salgono a 14; le due mutazioni provate, il secondo remoto mai spinto e il push forzato, fanno cadere rispettivamente 2 casi e 1.

## trasporto-ssh.ps1

Modulo comune di `allinea-tutti.ps1` e `chiudi-allineamento.ps1`, che lo caricano con il punto e non si lancia da solo. Ogni funzione accetta un progetto locale o uno `ssh://<alias>/<percorso>`: `Invoca-Git`, `Esiste`, `Leggi-Testo`, `Scrivi-Testo`, `Esegui-In`, più la scoperta (`Host-Ssh`, `Scopri-Remoti`), la preparazione del template remoto (`Prepara-Template`) e la lettura degli elenchi di esclusione e di approvazione (`Leggi-Elenco`, `In-Elenco`). Il comando remoto viaggia codificato in base64 dentro una sola riga, perché Windows PowerShell 5.1 non protegge le virgolette doppie negli argomenti di un eseguibile e in una pipe converte il testo nella codifica della console aggiungendo un CR a ogni riga; gli argomenti si citano con l'apice singolo della shell POSIX. Le connessioni usano `BatchMode=yes`, quindi un alias che chiede una password o una passphrase non si blocca ma risulta non raggiungibile. Le parti che non chiedono una rete sono provate dall'`-Autotest` di `allinea-tutti.ps1`; quella che la chiede dall'`-AutotestSsh` di `chiudi-allineamento.ps1`.

## passata-in-sospeso.py

Dice se il `.claude` del template è cambiato dall'ultima passata di `allinea-tutti.ps1`. Confronta l'albero `.claude` di HEAD con quello contro cui ogni progetto del registro `_notes/allineamento/registro.json` è stato misurato l'ultima volta, esclusi i progetti che non esistono più e quelli sotto una cartella temporanea. Esce con 1 e stampa il comando della passata se anche un solo progetto è rimasto indietro, con 0 se non c'è niente da propagare. Esiste perché il 2026-09-29 dodici progetti sono rimasti per una giornata con le norme vecchie senza che nessuno sapesse che la passata andava rifatta. `chiudi`, quando gira sul template, lo chiama dopo il push, così la propagazione viene proposta a ogni commit del template invece di dipendere da chi se ne ricorda.

```powershell
python .claude/templates/tools/passata-in-sospeso.py
```

## cerca-pacchetto.py

Cerca nel catalogo `PACKAGES.md` le voci che rispondono al lavoro in corso, confrontando le parole della domanda con la colonna «Quando offrirlo», che è l'innesco di ogni voce, con il nome e con «Cosa fa». È lo strumento della skill di sistema `cerca-pacchetto`, cioè del terzo momento del gate descritto nella sezione 23 di `PROJECT-SYSTEM.md`: fra un'inizializzazione e un allineamento il catalogo arriva nel progetto ma nessun punto letto in sessione lo nomina, e il 2026-10-19 un progetto istanziato ha ricostruito a mano una mappa che `craft-apps` conteneva già. Vive sotto `.claude/templates/tools/` e non sotto `tools/` del progetto, così l'allineamento lo porta ovunque senza istanziarlo.

```powershell
python .claude/templates/tools/cerca-pacchetto.py --progetto . applicazioni grafica pdf impaginazione
python .claude/templates/tools/cerca-pacchetto.py --elenco
python .claude/templates/tools/cerca-pacchetto.py --autotest
```

La ricerca è deterministica e non giudica: riduce le parole alle prime sei lettere senza accenti, il che basta a far combaciare plurali e coniugazioni, e ordina per punteggio. Con `--progetto` segna una voce come istanziata se il progetto ha la skill omonima o uno strumento del pacchetto sotto `tools/`; un pacchetto che istanzia solo schede o regole non si riconosce così, e per questo l'assenza si stampa come «non rilevato» e non come «non adottato». Rieseguita il 2026-10-19 sui due casi del progetto che ha segnalato il difetto, ha messo in testa `craft-apps` per «suite di applicazioni per documentazione, immagini e PDF» e `stack-profiles` per «dipendenze pinnate, lint, controllo dei tipi». L'`--autotest` ha 8 casi su un catalogo finto: le tre forme di riga, la cella con una barra protetta, l'ordinamento per innesco, plurali e accenti, la domanda estranea che non trova niente, la skill omonima che segna l'istanziazione.

## lezioni-template.py

Le lezioni che un progetto istanziato deve al template, visibili da entrambe le parti senza note portate a mano. Nel progetto `nuova` registra una lezione in `.claude/memory/lezioni-template.md`, versionato e del progetto, e `controlla` mostra le lezioni aperte e le voci del work-log, dalla data di adozione in poi, che non portano il campo `**Template:**` o che citano una lezione inesistente; gira dentro `chiudi` e avvisa senza bloccare, salvo `--rigoroso`. Nel template `raccogli` legge i registri di tutti i progetti elencati nel registro di `allinea-tutti.ps1`, anche via SSH, e `recepisci` chiude una lezione scrivendola in `.claude/templates/lezioni-recepite.json`, che l'allineamento porta nei progetti: così il template non scrive mai nel registro di un progetto. Lo SHA del commit è facoltativo, perché si recepisce prima di committare e nello stesso commit della modifica. Nato il 2026-10-19 su direttiva del proprietario e su proposta di un progetto istanziato; il disegno sta nella sezione 16 di `PROJECT-SYSTEM.md`. L'`--autotest` ha 12 casi, fra cui la lezione che si chiude da sé nel progetto quando il template la recepisce e la voce anteriore all'adozione che non si segnala.

```powershell
python .claude/templates/tools/lezioni-template.py nuova "titolo" --testo "che cosa, misurato come"
python .claude/templates/tools/lezioni-template.py controlla
python .claude/templates/tools/lezioni-template.py raccogli
python .claude/templates/tools/lezioni-template.py recepisci <progetto> L-001 --dove "file"
```

## fonti-a-monte.py

Dice quando è cambiata una fonte altrui da cui il sistema prende qualcosa, così che una scheda, una configurazione o una copia installata non resti falsa senza che nessuno se ne accorga. Lo stesso strumento gira nel template e nei progetti, e riconosce dove si trova dal prompt d'inizializzazione insieme ai marcatori del catalogo nel README, perché il prompt da solo sta anche in quattro progetti locali.

Una fonte è tutto ciò che il template installa, configura, importa, consiglia, cita o valuta: un repository GitHub, una GitHub Action di un workflow, un pacchetto npm, PyPI, crates o Homebrew, un'immagine Docker, un pacchetto winget o apt, un modello di Hugging Face, una libreria importata da uno strumento Python, il feed di una fonte di scouting. Il registro `fonti-a-monte.json` ha un elenco solo, `fonti`, e ogni voce porta l'identificativo con il tipo, come `github:owner/repo`, `pypi:markitdown` o `feed:<url>`, il `ruolo` dall'insieme chiuso dello strumento, il `motivo`, cioè che cosa il template ne prende, il pacchetto o il filone e la scheda che la descrive, il `controllo` e l'ultima versione confrontata, con la licenza letta a monte. Il controllo è `release` o `commit` per GitHub, eventualmente su una `cartella`; `versione` per un registro di pacchetti, un'immagine, un modello o un feed; `manuale` con una `scadenza` in giorni per ciò che non ha un'interfaccia interrogabile; e una voce può seguire un'altra fonte con `via`, come un'immagine di ghcr.io che segue le release del repository da cui nasce.

I ruoli sono nove: `skill-e-agenti`, `server-mcp`, `strumenti`, `librerie`, `fonti-di-norme`, `cataloghi`, `ispirazioni`, `candidati` e `scouting`, e per ciascuno lo strumento dice che cosa si verifica quando la fonte cambia. Si chiamano ruoli e non filoni perché nel template un filone è una linea di sviluppo di `docs/FILONI.md`: un repository nominato nel documento di un filone porta il nome del filone come pacchetto e il ruolo `candidati`, uno segnalato dallo scouting porta `scouting` come pacchetto, e il feed della fonte di scouting ha il ruolo `scouting`, così che il controllo all'apertura dica anche quante segnalazioni nuove aspettano un passaggio.

Fino al 2026-10-21 il registro aveva un secondo elenco, i repository «soltanto citati», che il controllo non interrogava. Quel giorno `taste-skill` è passata da tredici skill a una e il controllo all'apertura non l'ha vista, perché stava fra i citati benché il catalogo ne descrivesse contenuto e installazione; la stessa classificazione sbagliata colpiva altre undici righe del catalogo, e il censimento non vedeva affatto pacchetti, immagini, librerie, GitHub Action, modelli e i documenti di `docs/`. Su direttiva del proprietario non esiste più un criterio di esclusione. L'unico elenco a parte è `falsi`, per le stringhe che il censimento scambia per una fonte senza che lo siano, come una parola dopo `npx` in una frase: `falso` ne accetta una solo dopo aver verificato che a monte non esiste, e `controlla` la rilegge a ogni corsa, così una fonte vera non si può nascondere fra i falsi. Un registro nella forma di prima si legge ancora: i sorvegliati restano verificati, i citati diventano fonti da classificare e verificare.

Il censimento rende il registro completo da sé. Nel template percorre pacchetti, catalogo, skill, regole, norme, `PROJECT-SYSTEM.md`, il README e `docs/`, compresi script e pagine HTML, e raccoglie i repository negli URL, nei comandi d'installazione, nelle righe `uses:` dei workflow e fra apici inversi quando il nome non è un percorso locale; i pacchetti nei comandi npx, npm, pip, uv, pipx, cargo, brew, winget, apt e docker e negli `args` di una configurazione MCP; i modelli negli URL di Hugging Face; i feed negli URL che finiscono in `rss`, `feed` o `atom`; e le librerie non di sistema importate dagli strumenti Python. Una fonte nuova entra senza ruolo e senza motivo, una che non compare più si toglie, e il registro porta anche l'elenco `spediti` delle skill, degli agenti e dei comandi che il template manda nei progetti. Ogni scrittura del registro rigenera `.claude/templates/fonti-a-monte.md`, il documento che traccia tutte le fonti per ruolo con motivo, pacchetto o filone, scheda, controllo e data della verifica. In un progetto il registro è `.claude/fonti-a-monte.json`, il censimento percorre solo i posti dove si installa materiale altrui, `.claude/skills`, `.claude/agents`, `.claude/commands`, `.claude/agent-catalog` e `.agents`, salta ciò che l'elenco `spediti` dice arrivare dal template, e deduce ruolo e motivo dal posto.

`controlla` censisce e poi interroga a monte tutte le fonti, otto alla volta, senza scaricare niente: tace sulle invariate, e per le altre dice quanti commit, quale versione nuova o quante voci nuove di un feed, se la fonte è sparita, archiviata o deprecata, rinominata o trasferita, se la licenza è cambiata, se un controllo a mano è scaduto, con il link alla differenza dove c'è. Una rinomina registrata con `segna` non si ripete: un documento datato o copiato da una fonte esterna tiene il nome che aveva, perché correggerlo lì, il 2026-10-21, ha messo in conflitto l'allineamento di tre progetti che ne avevano una copia normalizzata. Alla prima corsa sceglie da sé release o commit per un repository che non lo dichiara. Esce con 0 anche quando trova cambiamenti o non raggiunge la rete, salvo `--rigoroso`, e al limite orario dell'API di GitHub dice quante fonti non ha controllato. Il token si prende da `GH_TOKEN`, `GITHUB_TOKEN` o `gh auth token`, e i certificati da `certifi` quando c'è, perché su questa macchina l'archivio di sistema rifiuta Docker Hub. `classifica` assegna ruolo, motivo ed eventualmente controllo, cartella, via e scadenza; `segna` registra la verifica dopo aver corretto la scheda, e la rifiuta a una fonte senza ruolo o motivo; `elenca` stampa il documento, e con `--scrivi` lo riscrive. Gira all'apertura di ogni sessione, dal `CLAUDE.md` del template e da `riprendi` nei progetti. `chiudi` lancia `censisci --check`: nel template ferma il commit se una fonte manca dal registro, è senza ruolo o senza motivo, non è mai stata verificata, se il documento non corrisponde al registro, o se una riga che nomina un solo repository noto dichiara una licenza diversa da quella letta a monte; nel progetto avvisa soltanto.

La revisione del 2026-10-21 ha portato il registro da 113 repository GitHub, 20 sorvegliati e 93 citati, a 176 fonti tutte sorvegliate, classificate e verificate: 137 repository GitHub, 14 pacchetti PyPI, 12 npm, 5 apt, 2 immagini Docker, 2 pacchetti winget, uno ciascuno per Homebrew, crates, Hugging Face e feed, più 2 falsi verificati come inesistenti. Per ruolo sono 50 candidati, 46 strumenti, 25 server MCP, 18 librerie, 15 skill e agenti, 8 fonti di norme, 7 cataloghi, 6 ispirazioni e una fonte di scouting; il controllo è per release su 91, per commit su 51, per versione su 31 e a mano su 3. La verifica, divisa in cinque lotti fra subagent e riletta, ha trovato le schede sbagliate sulla licenza di nove repository, otto dati MIT che a monte sono Apache-2.0, Elastic o GPL e uno dato AGPL che è MIT, su otto repository rinominati o trasferiti, l'ultimo dei quali, ccusage, segnalato dal controllo nuovo, sette corretti nelle schede e uno, flonat, lasciato col nome vecchio nel documento di ricerca copiato da fonte esterna e registrato come rinomina riconosciuta, su un server MCP raccomandato e archiviato dall'autore, una via d'installazione cambiata, cinque conteggi e la versione fissata di GROBID; il confronto delle licenze, scritto dopo, ha trovato caveman e una seconda occorrenza di LiteDoc che la verifica dei lotti aveva mancato. La simulazione sui 38 progetti locali con lo strumento nuovo trova fonti installate in due, dove il controllo avvisa e non ferma. L'`--autotest` ha 62 casi, senza rete, e dodici mutazioni, fra cui il falso accettato senza verifica, la rinomina ignorata, le licenze non confrontate e il documento non controllato al commit, fanno cadere ciascuna almeno un caso.

```powershell
python .claude/templates/tools/fonti-a-monte.py controlla
python .claude/templates/tools/fonti-a-monte.py censisci --check
python .claude/templates/tools/fonti-a-monte.py classifica Leonxlnx/taste-skill --ruolo skill-e-agenti --motivo "skill consigliata dal catalogo" --controllo release
python .claude/templates/tools/fonti-a-monte.py segna Leonxlnx/taste-skill
python .claude/templates/tools/fonti-a-monte.py falso npm:diretto --motivo "parola di una frase, non un pacchetto"
python .claude/templates/tools/fonti-a-monte.py elenca --scrivi
```

## lint-cultura.py

Segnala le conversioni PowerShell da testo a numero o a data che dipendono dalla cultura di sistema: `[double]::Parse`, `TryParse` e `[Convert]::ToDouble`, e gli stessi per `decimal`, `single`, `float` e `datetime`, chiamati senza un fornitore di formato. Nasce da una lezione di un progetto istanziato del 2026-10-20: la durata di un video letta da ffprobe come `300.012000` diventava trecento milioni in cultura italiana, senza nessun errore. Lo strumento conta gli argomenti di primo livello della chiamata e accetta la riga se oltre al testo c'è un argomento che non è un `[ref]` né uno stile, cioè la cultura, anche passata per variabile; i tipi interi, il cast `[double]"1.5"` e `-as` restano fuori perché non sbagliano in silenzio, e `# cultura-ok` marca un'eccezione voluta. Percorre i `.ps1` e `.psm1` tracciati. `chiudi` lo lancia in ogni progetto: nel template un riscontro ferma il commit, in un progetto avvisa, salvo `--rigoroso`. Alla prima corsa ha trovato nel template `[datetime]::Parse` in `chiudi-allineamento.ps1`, corretto anche se il formato letto è ISO e quindi oggi non sbagliava, e nei progetti locali tre conversioni in due progetti. L'`--autotest` ha 17 casi, e le mutazioni sul conteggio degli argomenti e sul riconoscimento degli stili ne fanno cadere almeno uno.

```powershell
python .claude/templates/tools/lint-cultura.py .
```

## retro-segnali.py

La parte deterministica della skill `retrospettiva`: legge la trascrizione JSONL della sessione più recente del progetto, sotto `CLAUDE_CONFIG_DIR` oppure `~/.claude`, e conta senza modello i comandi falliti, le chiamate negate, i file letti almeno tre volte, le ricerche ripetute, i risultati oltre ventimila caratteri e i messaggi dell'utente che correggono o interrompono, ciascuno con il turno e un estratto. Le chiamate dei subagent restano fuori. Con `--json` scrive i segni in un file, di norma sotto `_notes/retrospettiva/`. Su questa macchina il wipe cancella la trascrizione di una sessione chiusa, quindi lo strumento si lancia nella sessione stessa, prima di chiudere; le trascrizioni di Codex non sono ancora lette. L'`--autotest` ha 12 casi su una trascrizione costruita.

```powershell
python .claude/templates/tools/retro-segnali.py --json _notes/retrospettiva/segnali.json
```

## lint-strumenti.py

Esegue ruff, alle regole predefinite, sugli strumenti Python del template, ed è fra i controlli di chiusura del solo template. Attua la regola della sezione 16 di `PROJECT-SYSTEM.md` sui controlli di qualità adottati da un progetto: il 2026-10-19 un progetto istanziato ha trovato con ruff riscontri in quattro copie del template, e misurati qui con le stesse regole erano 42 in 17 strumenti, corretti alla fonte. Le regole sono `E4,E7,E9,F`, scritte nello strumento e non lasciate al predefinito di ruff: sono il predefinito fino alla 0.14, cioè il minimo che un progetto adotta senza configurare niente, e il predefinito cambia con la versione. Al primo commit lo stesso albero, a zero con ruff 0.14.2, dava 1.098 riscontri con la 0.17.1, tutti di regole entrate nel predefinito dopo. Le fixture di `md-unwrap` restano fuori, perché sono materiale di confronto byte per byte. Se ruff non è installato il controllo fallisce e dice come installarlo, invece di saltarsi da solo.

```powershell
python .claude/templates/tools/lint-strumenti.py
```

## Ponte Codex e adattatori delle skill

`sync-codex-skills.py --check` controlla i wrapper e, nei progetti del sistema, anche AGENTS.md alla radice. Un ponte mancante non può più dare verde quando i wrapper sono già corretti. Senza --check viene creato dal modello; un ponte personalizzato esistente resta intatto. La passata gestisce AGENTS con il rapporto e la storia ordinari nei soli progetti già Codex. Dettaglio e limiti nella [scheda della correzione](../../../docs/correzione-ponte-codex.md).

Le prove funzionali si eseguono con `python -m pytest .claude/templates/tools/tests/test_codex_bridge.py .claude/templates/tools/tests/test_allinea_dal_template.py -q`; includono repository temporanei per misurare il report reale di allineamento, senza commit nei progetti di lavoro.
