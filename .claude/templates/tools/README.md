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

Rileva, in sola lettura, i profili SSH verso GitHub configurati sulla macchina dove gira, e serve al Passo 0.5 dell'inizializzazione e dell'allineamento. Esiste perché la regola `git-identity-and-repo.md` non può sapere quali alias e quali chiavi esistano dove viene letta: un alias e una convenzione della singola installazione, non un fatto del sistema di progetto, e assumerlo porta a configurare un remoto che punta a un profilo inesistente, con un errore che si manifesta solo al primo push. Lo strumento e unico e non ha una variante per sistema operativo, perché il formato di `ssh_config` non ne ha.

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

Determina l'account attivo da `CLAUDE_CONFIG_DIR`, con fallback su `%USERPROFILE%\.claude`, e ne legge il `settings.json`. Esce con codice 0 se l'account è in regola, 1 altrimenti. Su Linux la variante equivalente e `check-account-hygiene.sh` (`bash .claude/templates/tools/check-account-hygiene.sh`), che legge il JSON con `python3` e, in sua mancanza, ricade su un controllo testuale.

## session-end-wipe.ps1

Template del wipe del magazzino nascosto, da installare per-account, non per-progetto. Si copia in `<CLAUDE_CONFIG_DIR>\hooks\session-end-wipe.ps1` insieme a `scrub-claude-json.js`, si sostituiscono i segnaposto `<CLAUDE_CONFIG_DIR>`, `<KEEP_PREFIXES>` e `<KEEP_PATH_PREFIXES>`, e si registra come hook `SessionEnd` nel `settings.json` dell'account, o nel `settings.local.json` se quella home non ha un `settings.json`. A ogni chiusura di sessione ripulisce i transcript e la memoria nascosta dei progetti non preservati e gli store per-account effimeri, lasciando intatti i progetti il cui slug corrisponde a uno dei prefissi da preservare, la configurazione, il login, le skill, i plugin e lo stato del daemon. I prefissi dipendono dalla macchina, uno per ogni radice dove stanno i progetti di sviluppo, e il template non ne porta uno di default ma un segnaposto che blocca lo script: un default che funziona su una macchina è una trappola su tutte le altre, perché su Linux gli slug derivano dal percorso assoluto e un prefisso come `D--` non corrisponde a niente, l'insieme dei progetti preservati risulta vuoto e il wipe cancellerebbe l'intero magazzino senza segnalare nulla. Da qui le tre guardie che precedono ogni rimozione: la home dell'account deve esistere e assomigliare a un magazzino di Claude Code, i prefissi devono essere stati compilati, e almeno uno slug presente deve corrispondervi, altrimenti lo script si ferma dichiarando che la configurazione è di un'altra macchina. L'esito dell'ultima corsa, rifiuti compresi, finisce in `session-end-wipe.log` nella home dell'account, perché un hook `SessionEnd` gira senza che nessuno ne veda l'output. Su Linux la variante equivalente e `session-end-wipe.sh`, registrata con un hook il cui comando e `bash "<CLAUDE_CONFIG_DIR>/hooks/session-end-wipe.sh"`. I prefissi non si indovinano: entrambe le varianti hanno un modo di sola lettura, `-List` su Windows e `--list` su Linux, che elenca gli slug realmente presenti marcandoli come preservati o da rimuovere e funziona anche sul template non ancora compilato, e un modo `-DryRun` oppure `--dry-run` che stampa ogni rimozione senza farne nessuna. L'ordine corretto è elencare, chiedere all'utente quali radici preservare mostrandogli l'elenco, compilare, provare a vuoto e solo allora registrare l'hook. La procedura completa e le sue varianti sono in PROJECT-SYSTEM.md sezione 15.

Oltre agli store storici lo script copre tre residui che altrimenti sopravvivono al wipe. Il primo sono le cache e i registri di stato per-account, ovvero `cache/`, `jobs/`, `ide/`, `todos/`, `statsig/`, `telemetry/` e `mcp-needs-auth-cache.json`. Il secondo sono gli scratchpad temporanei che Claude Code tiene in `%LOCALAPPDATA%\Temp\claude\<slug-progetto>` su Windows e in `$TMPDIR/claude/<slug-progetto>` su POSIX, con una sottocartella per sessione e gli output dei task: quella radice e condivisa fra tutti gli account della stessa utenza, quindi il passaggio e idempotente e chi chiude per ultimo la ripulisce. Il terzo e l'elenco dei percorsi aperti dentro `projects` di `.claude.json`, che senza questo passaggio sopravvive a ogni pulizia; se ne occupa `scrub-claude-json.js`. Di quest'ultimo passaggio va tenuto presente un effetto collaterale voluto: rimuovendo la voce di un progetto si rimuove anche il suo `hasTrustDialogAccepted`, quindi Claude Code richiede di nuovo di fidarsi della cartella al successivo avvio su quel percorso.

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

```
python tools/lint-doc-references.py
python tools/lint-doc-references.py --solo-vivi
python tools/lint-doc-references.py --bundle
python tools/lint-doc-references.py --self-test
```

## verifica-ripresa.py

Dice, alla riapertura di una sessione, se fra l'ultima e questa si e perso qualcosa. Confronta l'impronta registrata a fine sessione, cioè il commit e la forma dell'albero di lavoro in quel momento, con lo stato reale, e riporta i commit comparsi dopo l'ultima registrazione, i file rimasti a meta, i documenti di memoria che dichiarano un commit più vecchio di HEAD e le schede ancorate a un commit che non esiste.

Il danno che intercetta non è la perdita del lavoro, che sta su disco e in git, ma il fatto che una sessione nuova prenda un file di ripresa vecchio per lo stato corrente: un file di ripresa non aggiornato ha esattamente lo stesso aspetto di uno aggiornato. La skill `riprendi` e la procedura che ne interpreta l'esito.

```
python tools/verifica-ripresa.py
python tools/verifica-ripresa.py --registra
python tools/verifica-ripresa.py --breve
python tools/verifica-ripresa.py --self-test
```

## chiudi-sessione.ps1 / chiudi-sessione.sh / installa-chiudi.sh

Chiude una sessione con un comando solo, nell'ordine in cui i passi non si danneggiano a vicenda. Mostra ramo, file cambiati e diff riassuntivo senza pager; trova da solo i controlli istanziati nel progetto e li esegue tutti, fermandosi prima del commit se uno fallisce; prende il messaggio di commit da `-Messaggio`, oppure da `_notes/COMMIT-MSG.txt` che l'agente prepara a fine lavoro, oppure lo chiede; chiede conferma, committa tutto e pusha; verifica che HEAD coincida con il ramo remoto; registra l'impronta con `verifica-ripresa.py --registra`; infine esegue lo script di wipe di ogni account che ne ha uno installato, ma solo se nessun processo Claude Code da terminale o da editor è ancora aperto, altrimenti stampa i comandi da lanciare dopo.

Si lancia dal proprio terminale dopo aver chiuso Claude Code, perché il wipe lavora sui file che Claude riscrive finché è aperto. Commit e push restano un gesto dell'utente: è l'utente a lanciare lo script e a confermare dopo aver visto file e messaggio, e l'agente prepara il messaggio senza usarlo. Nel repository del template lo script riconosce di essere nel bundle e aggiunge ai controlli le opzioni `--bundle`, `--includi-modelli` e `--oracle require`, più i controlli propri del bundle.

```powershell
.\tools\chiudi-sessione.ps1
.\tools\chiudi-sessione.ps1 -SoloControlli
.\tools\chiudi-sessione.ps1 -Messaggio "Aggiornato X: cosa cambia" -Si
.\tools\chiudi-sessione.ps1 -NoWipe
.\tools\chiudi-sessione.ps1 -Account account2
```

```bash
bash tools/chiudi-sessione.sh
bash tools/chiudi-sessione.sh --solo-controlli
bash tools/chiudi-sessione.sh -m "Aggiornato X: cosa cambia" --si
bash tools/chiudi-sessione.sh --no-wipe
bash tools/chiudi-sessione.sh --account account2
```

Su Linux e macOS il comando breve `chiudi` si installa una volta nel profilo Bash o Zsh con `bash .claude/templates/tools/installa-chiudi.sh`, eseguito dal clone del template. L'installatore sceglie `~/.bashrc` o `${ZDOTDIR:-$HOME}/.zshrc`, salva una copia `.chiudi.bak` prima di modificare un profilo esistente e sostituisce solo il proprio blocco delimitato; `--verifica` controlla senza scrivere, `--shell bash|zsh` e `--profilo <percorso>` permettono una scelta esplicita. Dopo l'installazione si apre una nuova shell. La funzione cerca `chiudi-sessione.sh` nel repository corrente, prima in `tools/` e poi nel bundle sotto `.claude/templates/tools/`, e inoltra gli argomenti: `chiudi --solo-controlli`, `chiudi -m "Aggiornato X: cosa cambia"`, `chiudi --no-wipe`. Non dipende dal percorso del clone usato per installarla.

Esce 1 e non committa niente se un controllo fallisce, se il messaggio è vuoto, se la conferma manca o se l'hook di pre-commit rifiuta; esce 1 senza registrare l'impronta se il push non arriva al remoto; esce 3 quando commit e push sono riusciti ma un passo successivo, tipicamente la registrazione dell'impronta senza `_notes/RESUME-PROMPT.md`, ha dato KO, così la riga finale non dichiara completata una chiusura che non lo è. Se il push fallisce, rilanciare lo script dopo aver risolto non ricommitta: con l'albero pulito passa direttamente al push e alla registrazione. I casi del ramo nuovo senza ramo remoto, del repository senza `origin`, dell'HEAD staccato e dell'uscita 3 sono stati provati il 2026-09-24 in entrambe le varianti su cloni temporanei con un remoto finto. La variante Bash e l'installatore hanno inoltre prove isolate in `tests/test_chiudi_linux.py`, eseguite su Ubuntu WSL. La guida d'uso completa, in ordine cronologico e con i casi d'uso, è `docs/guida-sessione.html` del template. `_notes/COMMIT-MSG.txt` si cancella dopo un commit riuscito, così un messaggio vecchio non viene riusato alla sessione successiva. Lavora sul ramo in uscita, qualunque sia, e lo nomina nella richiesta di conferma: il push indica sempre `origin` e il ramo corrente, collega il ramo remoto con `-u` e legge direttamente il suo hash per la verifica; un repository senza remoto `origin` committa in locale e salta il push, mentre con HEAD staccato lo script si ferma prima dei controlli senza committare niente.

Non ha regole proprie: applica quelle del progetto e lascia lavorare i presidi che esistono già. Dichiara cartella, ramo e stato prima di tutto, come chiede `git-commands-format.md`; si ferma se mancano `user.name` e `user.email` locali e stampa l'autore accanto al messaggio, come chiede `git-identity-and-repo.md`; per il messaggio si affida all'hook `.githooks/commit-msg`, che rifiuta le attribuzioni a un agente e l'oggetto oltre i 72 caratteri per ogni commit, non solo per i suoi. È lo stesso per Claude Code e per Codex, perché la chiusura non dipende da quale agente ha lavorato. Su Windows `Installa-Comandi.ps1` del pacchetto `agenti-terminale` mette nel profilo PowerShell la funzione `chiudi`, che trova lo script nel repository in cui si trova il terminale e gli passa gli argomenti: `chiudi`, `chiudi -SoloControlli`. Su Bash e Zsh la installa `installa-chiudi.sh` con la stessa ricerca dal repository corrente. Lo stesso comando fissa anche le milestone a metà sessione: quando un blocco coerente è concluso l'agente scrive il messaggio in `_notes/COMMIT-MSG.txt` e propone di lanciare `chiudi`, una milestone per commit, e il wipe si salta da solo finché la sessione è aperta; la convenzione sta nella sezione "Milestone" di `.claude/rules/git-commands-format.md`.

## check-eol.py

Segnala i file di testo che mescolano CRLF e LF nello stesso file. La convenzione Markdown del sistema prescrive di conservare la fine riga di ciascun file, e md-unwrap la rispetta per contratto: ne segue che l'albero contiene legittimamente entrambe le convenzioni, e che nessun altro controllo si accorge se un file le mescola, perché il rendering a video è identico e la catena tipografica guarda i caratteri e non le interruzioni.

Un file misto non è un problema estetico. Con `core.autocrlf` a false e senza `.gitattributes` git registra le fini riga così come stanno sul disco, quindi il file misto entra nella storia, e alla prima riscrittura da parte di qualunque strumento le interruzioni si uniformano, trasformando una modifica di due righe in una modifica dell'intero file. È di sola lettura e non converte niente, perché la decisione su quale fine riga tenere resta di chi conosce il file.

```
python tools/check-eol.py
python tools/check-eol.py --dettaglio
```

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

Allinea un progetto istanziato alla testa del template senza modello linguistico, usando la storia git del template come arbitro. Per ogni file del perimetro, cioè `PROJECT-SYSTEM.md`, `rules/`, le skill di sistema, `templates/`, gli strumenti di codice copiati sotto `tools/` e le guide copiate sotto `docs/<pacchetto>/`, calcola l'hash di blob git del file locale a fini riga normalizzate e lo cerca fra tutti i blob che quel percorso ha avuto nel template, rinomine comprese. Un riscontro significa che la copia locale è una versione vecchia mai toccata, e si aggiorna senza perdere niente; nessun riscontro significa che è stata modificata sul posto, e si fonde a tre vie con `git merge-file` su una base che va indovinata, perché l'antenato vero non è osservabile. Il risultato di quel merge si misura invece di crederlo, e la ragione sta nella sezione seguente. Quando nessuna base produce un merge verificato, lo strumento guarda le righe del file che non compaiono in nessuna versione storica del template: se non ce n'è nessuna, oppure sono tutte righe che `--righe-comuni` dichiara condivise fra progetti, il file è una copia anteriore alla storia registrata e si aggiorna alla testa con l'esito SUPERATO, elencato perché una riga tolta di proposito nel progetto tornerebbe; se invece il file ha righe sue da salvare l'esito è CONFLITTO, con la nota che dice quante righe della testa il merge non consegnerebbe e quante ne duplicherebbe. Un file modificato che contiene già tutte le modifiche del template, e non ne perde nessuna, è una personalizzazione e non si tocca. Non tocca mai `memory/`, `context/`, `settings` né i file di dati istanziati sotto `tools/`, perché descrivono il progetto; `CLAUDE.md`, in radice oppure sotto `.claude/` dove il progetto lo tiene, lo tocca soltanto con `--innesco`, e soltanto per aggiungere le righe di innesco delle skill con `RIFERIMENTO.md` che il file non nomina ancora come skill, prese da `templates/CLAUDE.md` e scritte in coda all'indice esistente oppure prima della sezione degli apprendimenti recenti, con l'esito INNESCO. Un file che il progetto ha risolto a mano si registra con `--risolto <percorso>` in `.claude/allineamento-risolti.json`, versionato nel progetto insieme al blob della testa contro cui la risoluzione è stata fatta: da quel momento il file è ADATTATO finché il template non lo cambia di nuovo, e allora torna a chiedere attenzione.

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

Le prove stanno in `tests/test_allinea_dal_template.py`: costruiscono un repository git finto la cui storia riproduce i due meccanismi, con le proporzioni fra i blocchi prese dai file veri, perché sono le proporzioni a decidere quale base la somiglianza sceglie. La verifica di non vacuità è stata eseguita il 2026-09-28 rimettendo un difetto alla volta: senza il controllo sulle righe perse cadono 4 prove, senza quello sulle duplicate 2, senza la ricerca sulle altre basi 1, e con il codice precedente a entrambe ne cadono 5. Le cinque prove del 2026-09-29, sulla riga adattata, sulla correzione mancata, sulla risoluzione registrata e sull'innesco, lanciate contro lo strumento di HEAD `065d0b5` ne vedono cadere 4: la quinta, sulla correzione mancata, passa su entrambe le versioni per costruzione, perché è la prova che la correzione non ha allentato la guardia.

## allinea-tutti.ps1

Porta allo stato corrente del template tutti i progetti che ne portano la struttura, cioè ogni cartella sotto le radici indicate, `D:\` ed `E:\` per default, che contiene `.claude/PROJECT-SYSTEM.md`. Non conosce i progetti per nome: li scopre a ogni corsa. È lo strumento da lanciare ogni volta che il template avanza.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .claude/templates/tools/allinea-tutti.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .claude/templates/tools/allinea-tutti.ps1 -Applica
```

La corsa ha tre fasi: guardie e prima misura; consenso, cioè le righe assenti da tutta la storia del template ma identiche nello stesso file di almeno `-Consenso` progetti, 3 per default, che vengono da una versione del template anteriore alla sua storia git; seconda misura con quelle righe e, con `-Applica`, scrittura. Sulla prima corsa del 2026-09-28 il consenso ha riconosciuto 9 righe in 4 file, tutte della vecchia regola sull'identità e della vecchia mappatura degli account, e ha portato i progetti con conflitti da 24 a 6 su 35. A vuoto misura e basta. Con `-Applica` scrive solo dove passano tutte le guardie: `.claude` del template committato, un solo processo alla volta, e per ogni progetto repository git, albero principale e non un worktree aggiuntivo, non un clone del template, nessun merge o rebase a metà, una branch in uscita, albero pulito, nessun conflitto. Dopo aver scritto rimisura e pretende zero file da trattare, e controlla che nessun file cambiato stia fuori da `.claude/`, `tools/` e `docs/`; poi esegue la prova interna di ogni strumento sotto `tools/` del progetto che l'allineamento ha appena riscritto e che una prova interna la dichiara, riconoscendola dal `--self-test` o dall'`--autotest` nel proprio sorgente invece di lanciarla alla cieca; solo allora scrive nel progetto `.claude/allineamento-template.json`, che dichiara a quale commit e a quale albero `.claude` del template la sua struttura corrisponde. Se una prova interna fallisce il progetto prende lo stato `prove-fallite`, finisce fra quelli da guardare a mano e **non** riceve il marcatore, perché un progetto i cui strumenti non girano non è un progetto allineato. Passa sempre `--innesco` allo strumento, quindi le righe di innesco mancanti sono un esito azionabile: un progetto a cui mancano soltanto quelle è `da-allineare`, e con `-Applica` le riceve; `CLAUDE.md` è per questo l'unico file fuori da `.claude/`, `tools/` e `docs/` che l'allineamento può cambiare senza cadere in `fuori-perimetro`. Segnala anche, senza bloccare, il carico degli instruction file oltre soglia.

Quel passo risponde a una domanda sola, cioè se il codice appena scritto giri, e copre il caso di un aggiornamento o di una fusione a tre vie che lascia un file sintatticamente valido e funzionalmente rotto: è precisamente ciò che nessuno guarda dopo una passata riuscita. Non copre invece i presupposti sull'ambiente, e vale la pena dirlo perché il difetto che ha motivato il passo era proprio di quella specie: il 2026-09-28 due strumenti si fermavano con `ValueError` quando il bersaglio stava su un'unità diversa dalla radice, e la prova interna di uno dei due **passa anche sulla versione rotta**, perché esercita l'analisi del testo e non la gestione dei percorsi. Una prova interna copre ciò che il suo autore ha pensato di coprire, e un presupposto sull'ambiente non è quasi mai fra quelle cose.

Il registro di quali progetti sono allineati, e a quale commit, sta in `_notes/allineamento/registro.json` del template, ignorato da git perché contiene percorsi di progetti; ogni corsa lascia accanto il proprio log e i rapporti JSON. Commit e push restano manuali, progetto per progetto, e la memoria e i conflitti veri si chiudono con una sessione nel progetto, che registra con `--risolto` i file risolti a mano. Esce con 0 quando tutto è allineato o applicato, con 1 quando qualche progetto va guardato, con 2 quando una guardia iniziale fallisce.

## passata-in-sospeso.py

Dice se il `.claude` del template è cambiato dall'ultima passata di `allinea-tutti.ps1`. Confronta l'albero `.claude` di HEAD con quello contro cui ogni progetto del registro `_notes/allineamento/registro.json` è stato misurato l'ultima volta, esclusi i progetti che non esistono più e quelli sotto una cartella temporanea. Esce con 1 e stampa il comando della passata se anche un solo progetto è rimasto indietro, con 0 se non c'è niente da propagare. Esiste perché il 2026-09-29 dodici progetti sono rimasti per una giornata con le norme vecchie senza che nessuno sapesse che la passata andava rifatta. `chiudi`, quando gira sul template, lo chiama dopo il push, così la propagazione viene proposta a ogni commit del template invece di dipendere da chi se ne ricorda.

```powershell
python .claude/templates/tools/passata-in-sospeso.py
```
