# Identità git e bootstrap del repository

> Regola modulare. Definisce come scegliere l'identità git con cui si commetteranno e pusheranno le modifiche, come collegare il repository locale a GitHub tramite l'alias SSH corretto, e come proteggersi dal commit involontario con l'identità sbagliata su una macchina condivisa. Il commit e il push restano sempre operazioni manuali dell'utente: questa regola e la skill di inizializzazione preparano la configurazione, non committano e non pushano mai.

## Concetto

L'identità git, ovvero la coppia `user.name` e `user.email` con cui git firma i commit, e indipendente dall'account Claude Code e dalla chiave SSH[^1] usata per autenticarsi a GitHub. Su una stessa macchina possono convivere più identità: tipicamente una di lavoro e una personale. Il rischio concreto su un computer aziendale e committare un progetto personale con l'email di lavoro per distrazione, o viceversa. La regola e impostare sempre l'identità a livello locale di repository, così che ogni repo porti la firma giusta a prescindere dal default globale.

## Account Claude Code, un asse a parte e il re-auth silenzioso

L'account con cui Claude Code e autenticato e un terzo asse, distinto sia dall'identità git sia dalla chiave SSH: determina quale abbonamento e quali impostazioni di account si usano nella sessione, non chi firma i commit. Lo si seleziona con la variabile `CLAUDE_CONFIG_DIR`, una directory di configurazione per profilo. Ogni directory conserva le proprie credenziali nel file `<dir>/.credentials.json`, separato dalle altre, quindi in linea di principio ogni profilo mantiene il proprio account. Il comando `claude` nudo usa la directory di default, `%USERPROFILE%\.claude` su Windows e `~/.claude` su POSIX; le altre si selezionano impostando la variabile prima di lanciare il comando, e come le si sia rese comode sulla singola macchina, con funzioni di profilo della shell o con alias, è una scelta di quella installazione e va rilevata invece che assunta. Le directory presenti si elencano cercando i nomi `.claude*` nella home dell'utente, che è l'unica via che non presuppone come siano state chiamate.

Il legame fra una directory e il suo account, pero, non è garantito stabile, ed è la causa di un comportamento che sembra inspiegabile. Quando il token OAuth[^2] di una directory scade e il rinnovo automatico fallisce, cosa che può accadere dopo giorni di inattivita o in seguito a un riavvio, al primo avvio successivo Claude riapre l'autenticazione e adotta in modo silenzioso l'account che in quel momento risulta attivo nel browser su claude.ai, senza chiedere quale. Se il browser e loggato sull'account sbagliato, la directory viene ri-vincolata a quello. E esattamente il meccanismo per cui un riavvio sembra "scombussolare" gli account: una directory che era su un account si ritrova sull'altro perché al momento del re-auth il browser era su quell'altro, non per un guasto del profilo.

Ne discende la regola operativa. Il binding di una directory non va mai dedotto dal suo nome ma verificato a inizio sessione con `/status`, o leggendo il campo `emailAddress` in `<dir>/.claude.json`. Dove una macchina adotti una numerazione delle directory, per esempio una `.claude-account1` e una `.claude-account2` associate a due indirizzi diversi, quella corrispondenza è una convenzione locale e non un invariante, e il meccanismo di re-auth appena descritto è precisamente ciò che può smentirla senza preavviso. Per riportare o cambiare l'account di una directory si imposta prima il browser su claude.ai sull'account desiderato, e solo dopo, in una sessione avviata con quel `CLAUDE_CONFIG_DIR`, si eseguono `/logout` e `/login`, confermando infine con `/status`. Toccare l'altra directory mentre il browser e ancora sull'account sbagliato la ri-vincolerebbe a sua volta a quello: il browser va sempre allineato prima di ogni `/login`.

Questo asse resta indipendente dall'identità git descritta sotto. Un progetto personale può girare sotto l'account Claude di lavoro e farsi comunque firmare i commit dall'identità git personale: i due assi non devono coincidere e si verificano separatamente, l'account con `/status` e l'identità git con `git log -1 --format="%an <%ae>"`.

[^2]: *OAuth*, Open Authorization - protocollo di autorizzazione con cui Claude Code ottiene e rinnova un token di accesso all'account senza conservare la password; il token ha una scadenza e si rinnova tramite un refresh token, e quando il rinnovo non va a buon fine occorre ri-autenticarsi.

## GitHub CLI, il quarto asse: l'API non passa da SSH

Strumento opzionale, da proporre al gate e mai installato di default: vedi più sotto la sezione sulla scelta. Quando c'è, serve a operare sulle pull request da riga di comando, e in particolare a scrivere la descrizione di una pull request prendendola da un file del repository invece di incollarla a mano nel browser.

La cosa da capire prima di usarlo è che `gh` **non parla con la piattaforma via SSH**, e questo lo rende un asse a sé rispetto agli altri tre. SSH serve a `git push`, cioè a spostare oggetti fra due copie del repository; `gh` usa l'**API HTTPS con un token OAuth** conservato nel gestore credenziali del sistema operativo. Autenticare `gh` quindi non tocca né la chiave SSH, né l'alias host, né l'identità con cui i commit vengono firmati: quattro assi indipendenti che vanno verificati separatamente.

La conseguenza pratica è che `gh auth status` risponde a una domanda diversa da `ssh -T git@<alias>`, e nessuna delle due risposte implica l'altra. Si può avere `gh` autenticato sull'account sbagliato mentre i push funzionano perfettamente, e il sintomo sarebbe una pull request modificata sul repository di qualcun altro.

### Il comando non si chiama `gh` finché non si riapre il terminale

Va detto per primo perché è il punto in cui ci si ferma, e il messaggio di errore sembra un'installazione fallita mentre l'eseguibile c'è e funziona. La causa è che **un processo eredita le variabili d'ambiente quando parte e non le rilegge mai più**: l'installatore ha aggiornato il PATH permanente della macchina, non quello del terminale già aperto. Riaprire il terminale risolve; nella sessione corrente si invoca l'eseguibile per percorso completo. È la stessa famiglia di errori descritta in `git-commands-format.md`, cioè un presupposto sullo stato dell'ambiente che nessun comando dichiara.

### Autenticazione, con le due cose che NON vanno lasciate fare

```powershell
gh auth login --hostname github.com --git-protocol ssh --skip-ssh-key --web
```

I due flag non sono decorativi. `--skip-ssh-key` impedisce a `gh` di proporre la generazione e il caricamento di una chiave nuova, che su una macchina con le chiavi già configurate ne aggiungerebbe una di cui nessuno ha bisogno. E se compare la domanda "Authenticate Git with your GitHub credentials?", si risponde **No**: dire di sì installerebbe un gestore di credenziali per le operazioni git, già risolte via SSH, e si finirebbe con due meccanismi concorrenti per la stessa cosa.

**Come per l'account dell'agente, l'identità adottata è quella attiva nel browser** nel momento dell'autorizzazione. Si apre la piattaforma e si verifica di essere collegati con l'identità giusta **prima** di lanciare il comando. È la stessa trappola del riconoscimento silenzioso descritta più sopra, con la stessa causa e lo stesso rimedio.

La verifica va fatta e non presunta, con `gh auth status`, e deve nominare l'account atteso.

### L'alias SSH rompe il riconoscimento del repository, e la soluzione non è cambiarlo

`gh` ricava il repository su cui operare leggendo il remoto `origin`. Se il remoto usa un alias host definito nella configurazione SSH, quell'alias **non è un host reale** e `gh` non ha modo di sapere che cosa ci sia dietro: può non riconoscere il repository e fallire con un messaggio sul remoto non valido.

La tentazione è cambiare il remoto all'host reale. **Non si fa**, perché l'alias è ciò che seleziona la chiave giusta fra quelle configurate: toglierlo romperebbe l'intero meccanismo a più identità per risolvere un problema che ha una soluzione locale. Si indica il repository esplicitamente su ogni comando con il flag `-R <owner>/<repo>`, che non scrive niente da nessuna parte e quindi non lascia stato da mantenere allineato. Esiste anche un comando che memorizza la scelta nella configurazione git locale, ma va evitato per lo stesso motivo del gestore credenziali: aggiunge una seconda fonte di verità su quale sia il repository, e prima o poi divergerà dal remoto.

### Che cosa resta manuale, e perché

`gh` può anche fondere una pull request. **Non lo si usa per quello.** La regola per cui commit, push e merge restano gesti dell'utente non nasce da un limite tecnico ma da una scelta: l'agente prepara il lavoro, la decisione di farlo atterrare è di una persona. **Uno strumento che rende facile automatizzare quella decisione non è una ragione per cambiarla**, ed è esattamente il momento in cui conviene ribadirla, perché la comodità è il modo in cui le regole si erodono.

### La scelta di adottarlo, al gate e non per inerzia

L'adozione si propone come gate esplicito in fase di inizializzazione, insieme agli altri pacchetti, e la domanda è duplice. Prima: **serve a questo progetto?** Ha senso dove le pull request hanno una descrizione lunga e curata che vive come file nel repository, o dove si consultano spesso stato e commenti senza voler aprire il browser; non ha senso dove le pull request sono poche e brevi, perché uno strumento in più da autenticare e mantenere allineato costa più di quanto renda. Seconda: **si vuole che esista su questa macchina?** L'autorizzazione crea un legame durevole fra la macchina e l'account, che va tracciato dove il progetto registra le operazioni manuali sui pannelli web, insieme al luogo in cui si revoca. Un legame che nessuno ha scritto è un legame che nessuno saprà sciogliere il giorno in cui quella macchina non servirà più.

Se il progetto lo adotta, l'inizializzazione verifica che l'eseguibile risponda, che `gh auth status` nomini l'account atteso, e registra l'autorizzazione fra le operazioni manuali con la data e il collegamento alla pagina di revoca.

## I profili non si assumono: si rilevano

Un profilo è la terna formata da un alias host SSH, dalla chiave che quell'alias seleziona e dall'identità git da abbinargli. Nessuno dei tre termini è una proprietà del sistema di progetto: sono scelte di chi ha configurato quella macchina, e cambiano da una macchina all'altra anche a parità di persona. Una versione precedente di questa regola elencava due profili concreti come se fossero un dato, e su una seconda macchina si è rivelata non soltanto estranea ma fuorviante, perché là gli alias hanno la forma `github.com-<utente>` e i percorsi non sono quelli di Windows. Il modo in cui un elenco del genere sbaglia è il peggiore possibile: induce a proporre un remoto che punta a un alias inesistente, e il comando fallisce solo al primo push, quando nessuno lo collega più alla configurazione.

La regola è quindi che la configurazione SSH si legge prima di proporre qualunque comando, e si legge sulla macchina dove si sta lavorando. Lo strumento è `templates/tools/detect-ssh-profiles.py`, in sola lettura: risolve il file di configurazione dell'utente insieme alle sue direttive `Include`, elenca gli alias il cui `HostName` è `github.com` con la chiave che ciascuno seleziona, dichiara se quel file di chiave esiste davvero, segnala le chiavi presenti in `~/.ssh` che nessun alias richiama, riporta gli eventuali blocchi `Match` senza fingere di averli interpretati, e affianca a tutto questo l'identità git globale e quella locale del repository indicato. Non stampa mai materiale di chiave, solo percorsi e nomi.

```
python .claude/templates/tools/detect-ssh-profiles.py --repo .
```

Quel rilevamento è il materiale su cui si costruisce la domanda all'utente, non la risposta. Un alias non dice per chi è: il nome che qualcuno ha dato a un blocco `Host` è una mnemonica privata, e dedurne l'identità da usare sarebbe la stessa specie di errore che questa sezione esiste per impedire. Si presentano quindi gli alias trovati con la chiave di ciascuno, e si chiede quale usare per questo progetto, con quale `user.name` e quale `user.email` abbinarlo e quale sia l'owner GitHub di destinazione. Se un alias risulta definito ma la sua chiave manca, lo si dice prima di proporlo, perché è un profilo che fallirà. Se nessun alias verso `github.com` esiste, non c'è niente da scegliere e va creato il profilo prima di proseguire, cosa che richiede una chiave e una configurazione dell'utente e non si fa di propria iniziativa.

Resta buona una convenzione di nomi, purché sia offerta come convenzione e non spacciata per rilevamento: chiamare `github-personal` l'alias dell'identità personale e `github-corp` quello di lavoro rende la stessa logica di selezione leggibile ovunque la si adotti. Su una macchina che usa già altri nomi non si rinomina niente, perché un alias è riferito dai remoti di tutti i repository che lo usano e cambiarlo li romperebbe tutti in una volta.

## Protezione globale dal commit con identità sbagliata

Una sola impostazione globale, da fare una volta per macchina, fa si che git rifiuti di committare in un repository dove non è stata impostata l'identità locale.

```bash
git config --global user.useConfigOnly true
```

Con questa impostazione git non ripiega mai sull'email globale: se il repo non ha `user.email` locale, il commit viene rifiutato finché non lo si imposta esplicitamente. Questo elimina il commit accidentale con l'email di lavoro mentre si sviluppa con identità personale. Essendo una modifica globale, va eseguita solo dopo conferma dell'utente.

## Bootstrap di un repository nuovo

Dalla cartella del progetto, l'inizializzazione di un repo nuovo e l'aggancio al remoto GitHub seguono questa sequenza. La parte di identità e remoto e quella che la skill prepara; il primo commit e il push li esegue l'utente. I quattro valori tra parentesi angolari non hanno un default: `<alias>` è uno degli alias che il rilevamento ha trovato su questa macchina, `<user>` e `<email>` sono l'identità che l'utente ha indicato per questo progetto, `<owner>` è l'utente o l'organizzazione GitHub di destinazione. Sostituirli con valori presi da un'altra installazione produce un remoto sintatticamente valido e funzionalmente morto.

```bash
cd "<path cartella>"

# Inizializza il repo e nomina main il branch di default
git init
git branch -M main

# Forza l'OpenSSH di sistema e l'identita SOLO per questo repo (Windows)
git config --local core.sshCommand "C:/Windows/System32/OpenSSH/ssh.exe"
git config --local user.name "<user>"
git config --local user.email "<email>"

# Collega il remoto tramite l'alias SSH scelto
git remote add origin git@<alias>:<owner>/<nome repo>.git
```

Il remoto `git@<alias>:<owner>/<nome repo>.git` punta a `github.com/<owner>/<nome repo>` usando la chiave che quell'alias seleziona: è l'alias, e non l'URL, a decidere con quale identità ci si autentica, ed è per questo che sbagliarlo non produce un errore di sintassi ma un rifiuto di accesso a un repository che magari esiste.

Differenza per sistema operativo: su Windows si forza `core.sshCommand` all'eseguibile OpenSSH indicato perché git per Windows porta un proprio `ssh` che potrebbe non leggere lo stesso config; su Linux questo passaggio e di norma superfluo, perché `ssh` di sistema e già sul PATH e legge `~/.ssh/config`, quindi si omette `core.sshCommand` oppure lo si imposta a `ssh`.

## Verifica della configurazione

Dopo aver impostato identità e remoto, verificare che tutto sia coerente.

```powershell
# Windows PowerShell
git config --local --list | Select-String "user\.|remote\.|core\.ssh"
```

```bash
# Linux / bash
git config --local --list | grep -E "user\.|remote\.|core\.ssh"
```

La verifica della connessione verso l'alias scelto non è opzionale quando il profilo è stato appena deciso, perché è l'unico modo di sapere prima del push che l'alias e la chiave sono quelli giusti. GitHub risponde rifiutando la shell e dichiarando come quale utente ha riconosciuto la chiave, ed è quel nome che va confrontato con l'owner del remoto: se non corrisponde, l'alias sta selezionando l'identità sbagliata e il push fallirebbe con un errore di permessi che non nomina la causa.

```bash
ssh -T git@<alias>
```

## Primo commit, push e caso del repo con README

Le operazioni seguenti sono dell'utente, non dell'agente.

```bash
git add .
git commit -m "Initial commit: <note del primo commit>"
git push -u origin main
```

Subito dopo il primo commit conviene confermare con quale identità e stato firmato.

```bash
git log -1 --format="%an <%ae>"
```

Se il repository su GitHub e stato creato con un README o una licenza automatica, esiste già un commit remoto e il push diretto verrebbe rifiutato. Si allinea con un rebase prima di pushare.

```bash
git pull origin main --rebase
git push -u origin main
```

Il rebase prende il commit già presente su GitHub, ad esempio il README generato alla creazione del repo, e vi colloca sotto il commit iniziale locale, producendo una storia lineare senza commit di merge e senza modificare alcun file di lavoro. Dalle volte successive il push e semplicemente `git push`.

## Vincolo

L'identità locale, il `core.sshCommand` e il remoto si preparano automaticamente; la protezione globale `user.useConfigOnly` si imposta solo su conferma. Commit e push restano sempre manuali. Nessuno dei valori che entrano in quei comandi, però, si prepara da solo: alias, chiave, nome, email e owner si rilevano con `detect-ssh-profiles.py` e si confermano con l'utente prima di essere scritti, e su una macchina mai vista prima questa non è una formalità ma il passo che impedisce di configurare un remoto verso un profilo che non esiste.

[^1]: *SSH*, Secure Shell - protocollo con cui git si autentica a GitHub tramite una coppia di chiavi; l'alias host nel file di configurazione SSH seleziona quale chiave usare.
