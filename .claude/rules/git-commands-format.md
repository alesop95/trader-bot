# Formato dei comandi git per esecuzione manuale

> Regola modulare. Definisce come l'agente deve presentare i comandi git (add, commit, push) che l'utente esegue manualmente: in quale forma, cioè un comando per riga senza caratteri di continuazione, e in quale sintassi, cioè quella della macchina su cui si sta lavorando e non entrambe insieme. Vale ogni volta che l'agente fornisce comandi git da eseguire a mano.

## Principio

I comandi git restano sempre manuali dell'utente. Quando l'agente li presenta, li scrive in un formato immediatamente copiabile senza modifiche nel terminale che l'utente ha davanti: una riga per comando, nessun carattere di continuazione, nessun heredoc multi-riga, e la sintassi della shell su cui quella persona sta davvero lavorando invece di un doppio elenco che le chiede di scegliere.

Un comando non si spezza mai su più righe, per nessun motivo e a nessuna lunghezza. Non si usano caratteri di continuazione, né il backslash di bash, né il backtick di PowerShell, né il caret di cmd: sono specifici di una shell e rompono il copia-incolla sull'altra. Non si va a capo a mano per rientrare in una larghezza di colonna: l'avvolgimento a video è compito del terminale, esattamente come per la prosa di un file Markdown, e una riga lunga incollata resta un comando solo mentre una riga spezzata a mano diventa due comandi rotti. Se l'elenco dei percorsi rende la riga scomoda, la soluzione non è spezzarla ma accorciarla: si passa una cartella invece dei file che contiene, oppure si usa `git add -A` quando le modifiche da includere sono tutte quelle presenti, dichiarando nel testo che cosa entra nel commit. Questo vincolo vale sia per i comandi scritti in un file `.md` sia per quelli scritti direttamente in sessione nel terminale, e vale per ogni comando di shell che l'agente consegna all'utente perché lo esegua a mano, non solo per quelli di git.

Il vincolo va verificato, non solo dichiarato, perché lo strumento `md-unwrap` per contratto non tocca il contenuto dei blocchi recintati: un comando spezzato dentro un blocco di codice non lo corregge nessuno. Il controllo è `tools/lint-md-commands.py`, che percorre i blocchi di shell dei file Markdown e segnala continuazioni di riga, heredoc e comandi git che proseguono sulla riga seguente.

## Formato richiesto

I comandi si consegnano nella sola sintassi della macchina su cui si sta lavorando, non in entrambe. La shell dell'utente non è un'incognita: Claude Code dichiara all'avvio della sessione la piattaforma e la shell primaria, e quello è il dato da usare; dove mancasse lo si rileva in sola lettura, per esempio con `uname -s`, che su una macchina POSIX risponde con il nome del kernel e su Windows nudo non esiste. Su Windows si consegna quindi il solo blocco `powershell`, su Linux e macOS il solo blocco `bash`.

La ragione non è la brevità ma la precisione. Nella pratica di `git add`, `git commit -m` e `git push` i due blocchi sono identici carattere per carattere, e presentarli entrambi non aggiunge informazione: aggiunge una scelta davanti a due testi uguali. Dove invece la sintassi diverge davvero, come nella verifica della configurazione locale che su Windows passa da `Select-String` e su Linux da `grep`, oppure in un percorso o in una variabile d'ambiente, il blocco che non si userà resta comunque copiabile, ed è esattamente quello che prima o poi finisce incollato per sbaglio. Un solo blocco, quello giusto, toglie il problema alla radice.

Su una macchina Windows la consegna è quindi questa, e nient'altro.

```powershell
git add "percorso/file-uno" "percorso/file-due" "percorso/file-tre"
git commit -m "Messaggio sintetico del commit"
git push
```

La stessa sequenza, su Linux o macOS, si consegna così e soltanto così.

```bash
git add "percorso/file-uno" "percorso/file-due" "percorso/file-tre"
git commit -m "Messaggio sintetico del commit"
git push
```

Se i file da aggiungere sono molti, si usa `git add` con tutti i percorsi sulla stessa riga, separati da spazio, ciascuno tra doppi apici.

Quando il repository su cui si opera non è quello aperto nella sessione, il blocco si apre sempre con il proprio `cd`, su una riga a sé, con il percorso tra doppi apici e con le barre in avanti, che entrambe le shell accettano. Non si scrive in prosa di spostarsi in un'altra cartella lasciando i comandi senza: chi copia un blocco lo incolla dove si trova, e un `git add -A` eseguito nella cartella sbagliata è un errore che si scopre dopo il commit. La prescrizione nasce da una richiesta d'uso del 2026-09-15 in un progetto istanziato, dopo due sessioni in cui i comandi per un repository gemello erano stati dati senza.

La scelta si dichiara invece di restare implicita: una riga che dice per quale shell è il blocco basta a rendere verificabile il rilevamento, e a far correggere subito l'agente quando la macchina non è quella che ha creduto.

## Le due eccezioni

La prima eccezione è il testo destinato a essere letto altrove. Un comando scritto dentro un file del repository, cioè un README, una regola o la documentazione di un pacchetto, non ha davanti a sé la macchina di questa sessione ma un lettore ignoto, e là le due forme restano entrambe, affiancate ed etichettate, esattamente come nei due blocchi qui sopra. La distinzione è fra il consegnare e il documentare: si consegna a chi si conosce, si documenta per chi non si conosce.

La seconda eccezione è la richiesta esplicita. Se l'utente chiede entrambe le forme, per esempio perché deve passare i comandi a qualcun altro o perché lavora sulla stessa repository da due macchine, si danno entrambe senza discutere.

## Il contesto di una shell non si deduce, si dichiara

Sezione generalizzata da un progetto istanziato da questo template, dove lo stesso difetto si è ripetuto **cinque volte** con quattro cause diverse e conseguenze ogni volta differenti, a cui un secondo progetto istanziato ne ha aggiunta una quinta il 2026-09-17. Vale la pena leggerla per intero prima di consegnare il primo blocco di comandi, perché ogni singolo comando era corretto in tutti e cinque i casi: il difetto non stava nella conoscenza dei comandi ma in un **presupposto sullo stato che nessuno dei comandi dichiara**.

La prima causa è il **ramo**. Due volte l'agente ha scritto "questo va diretto sul ramo principale" mentre la sessione era su un ramo di lavoro, e la documentazione è atterrata sul ramo. Conseguenza: il blocco dichiara su quale ramo va eseguito, e se il ramo corrente non è quello, il primo comando del blocco è il cambio di ramo.

La seconda è lo **stato dell'albero**. Una sequenza che cambia ramo è stata consegnata con un file tracciato modificato: il cambio di ramo è stato rifiutato, e da lì i due comandi successivi hanno fallito per ragioni che sembravano scollegate, **tre errori a cascata da una sola causa**. Conseguenza: una sequenza che cambia ramo si consegna solo con l'albero pulito, e se ci sono modifiche non committate si risolvono prima, committandole, mettendole da parte, oppure scartandole quando si tratta di un file generato, perché un derivato non si mette da parte, si rigenera.

La terza è la **cartella**, ed è la variante peggiore. Il blocco è stato incollato in un terminale aperto su un altro repository della stessa macchina: il primo comando ha fallito con un percorso non trovato, ma il secondo ha risposto "niente da committare" e il terzo "già aggiornato", cioè **due messaggi di successo su tre**. Chi li legge conclude che non c'era niente da committare, non che stava committando altrove, ed è per questo che l'errore si è ripetuto due volte di fila senza che nessuno se ne accorgesse. Conseguenza: il primo comando di ogni blocco è il posizionamento nella cartella del progetto, **sempre**, anche quando la sessione dell'agente è già lì, perché il terminale dell'utente è un processo diverso e la sua directory corrente non è osservabile né deducibile.

La quarta è l'**ambiente**, scoperta installando uno strumento nuovo. Un comando ha fallito tre volte con "termine non riconosciuto" pur essendo l'eseguibile presente e funzionante, perché **un processo eredita le variabili d'ambiente quando parte e non le rilegge mai più**: l'installazione aveva aggiornato il PATH permanente della macchina, non quello del terminale già aperto. Conseguenza: dopo l'installazione di un programma, il primo comando che lo usa si consegna **per percorso completo** e non per nome, finché non c'è conferma che il terminale sia stato riaperto.

La quinta è la macchina, ed è la sola che le altre quattro non potevano vedere perché la davano per scontata. Un blocco che si apriva con `ssh -t <alias>` è stato incollato in un terminale già aperto sulla macchina di destinazione, e la risposta è stata un fallimento di risoluzione del nome: quell'alias non esiste là, perché è una riga nel file di configurazione SSH della macchina di partenza e non una proprietà della rete. Le prime quattro cause riguardano tutte lo stato di una shell su un computer dato, questa riguarda quale sia il computer. Conseguenza: quando un lavoro si svolge su due macchine, il blocco dichiara su quale delle due va incollato prima ancora di dichiarare in quale cartella, e un blocco che contiene un `ssh` dichiara di essere per la macchina di partenza, mai per quella di arrivo.

Questa occorrenza è caduta rumorosamente e nessuno l'ha scambiata per un successo, il che la rende meno istruttiva della terza ma non più innocua. La variante silenziosa esiste ed è facile da incontrare: basta che sulla seconda macchina un alias omonimo esista e punti altrove, e il comando riesce nel posto sbagliato senza dire niente. La regola vale per quella variante, non per questa.

Una sesta causa riguarda la shell stessa e non lo stato che la circonda, e vale enunciarla perché trasforma un errore in una **misura falsa**. In Git Bash su Windows l'argomento nella forma `revisione:percorso`, quello che serve a leggere un file a una certa revisione, viene riscritto dal livello di compatibilità dei percorsi: i due punti diventano un punto e virgola e le barre si rovesciano, e il comando fallisce con un messaggio che parla di revisione ambigua. Il guaio non è il fallimento, che si vede, ma l'uso in catena: quel comando messo in una pipe verso un contatore produce **zero** invece di un errore, e zero è una risposta plausibile alla domanda "questo contenuto c'è?". Si legge come assenza ciò che è stato solo impossibile leggere. Il rimedio è anteporre `MSYS_NO_PATHCONV=1` al comando, e la regola generale è che una misura fatta con uno strumento che può fallire in silenzio si controlla una volta sulla sua forma grezza prima di fidarsi del totale.

Una settima causa riguarda **lo stato di un ramo diverso da quello corrente**, e si distingue dalla prima perché lì il ramo sbagliato era quello su cui si stava, qui è quello verso cui si sta per andare. Un blocco che si apre con un cambio di ramo presuppone in silenzio che il ramo di destinazione sia aggiornato; se è indietro rispetto al remoto e il file che si sta per committare non esiste ancora là, il cambio viene **rifiutato** per non sovrascrivere le modifiche locali. Da lì in poi tutti i comandi successivi del blocco si eseguono sul ramo di partenza, e il difetto è che **riescono**: il commit viene fatto, il push pure, e l'unica traccia dell'errore è che il lavoro si trova dove non doveva. Conseguenza: un blocco che cambia ramo mette l'aggiornamento di quel ramo **prima** del cambio, non dopo, e chi lo scrive si chiede se il ramo di destinazione possa avere commit che la copia locale non ha, cosa normalissima subito dopo che una richiesta di fusione è stata accettata dal server.

La forma più robusta, però, è non avere bisogno della danza: **si decide dove scrivere prima di scrivere**, non dopo. Un contenuto destinato a un ramo diverso da quello corrente si produce dopo esserci andati, e l'abitudine di scriverlo dove capita per poi spostarlo paga ogni volta il costo di una sequenza che dipende da stato non osservabile.

Un'ottava causa è la sola che non riguarda lo stato di una shell ma la presenza di qualcun altro, ed è la più insidiosa perché non produce nessun fallimento: **un altro agente sta lavorando nello stesso albero**. Osservata tre volte nella stessa giornata, il 2026-10-12, su questo template, con due sessioni aperte sullo stesso repository. Due volte un `git add -A` lanciato dall'altra sessione ha raccolto il lavoro di questa e l'ha committato sotto un messaggio che parlava d'altro: il lavoro c'è, i controlli sono verdi, e la storia non sa più dire chi ha fatto che cosa, il che si scopre solo mesi dopo cercando quando una certa riga sia comparsa. La terza volta è andata al contrario, e il tempo si è speso a districare un indice in cui metà dei file in stage erano di un'altra sessione.

Ne discende una verifica che costa un comando e va fatta **prima** di consegnare qualunque sequenza che committi: si guarda `git status` e si confronta l'elenco con ciò che si è scritto davvero in questa sessione. Un file modificato che non si riconosce non è una svista propria, è un indizio: qualcun altro sta scrivendo qui. Lo stesso vale per un file già in stage che non si è messo in stage, e per un commit comparso nel registro da quando la sessione è cominciata.

Riconosciuta la situazione valgono tre prescrizioni. `git add -A` smette di essere lo strumento giusto, perché il suo perimetro è l'albero e non il proprio lavoro: si nominano i percorsi, che è la forma ordinaria prevista più in alto in questa regola. Uno script di chiusura che faccia `add -A` per conto proprio non si lancia affatto, e questo è il caso di `chiudi`, che va rimandato finché l'altra sessione non ha committato il suo. E se due file portano il lavoro di entrambe le sessioni, come succede a un catalogo o a un indice che tutte e due aggiornano, non si tenta di separarli per riga: si aspetta che l'altra committi, e si committa dopo, perché un commit sbagliato costa più di cinque minuti di attesa.

Due cose rendono quella attesa non negoziabile, e si sono viste entrambe lo stesso giorno. La prima è che il presidio di pre-commit, dove esiste, rigenera i file derivati leggendo **l'albero di lavoro** e non l'indice: un commit parziale viene allora rifiutato perché il README rigenerato dal lavoro ancora su disco non coincide con quello messo in stage, e il rifiuto si ripete finché l'altra sessione non ha finito. Separare i due lavori con `git commit` sul solo indice, che in teoria sarebbe la mossa giusta, in pratica non passa. La seconda è che `_notes/COMMIT-MSG.txt` è una risorsa a slot singolo: due sessioni che vi scrivono il proprio messaggio si sovrascrivono a vicenda senza accorgersene, e la seconda consegna all'utente il messaggio sbagliato. Chi apre la seconda sessione tiene quindi il proprio messaggio nella risposta finché non è il suo turno di committare.

La forma robusta, però, è non arrivarci: **una milestone alla volta per albero**. Due sessioni sullo stesso repository si dividono il lavoro per file o si alternano sul commit, e chi apre la seconda sessione lo sa fin dall'inizio invece di scoprirlo da un indice sporco.

La regola che le sette cause di contesto e questa ottava insieme dimostrano: **un comando corretto eseguito in un contesto diverso da quello presupposto non è un comando corretto**, e il contesto, cioè macchina, cartella, ramo, stato dell'albero, variabili d'ambiente e presenza di altri agenti, non si deduce mai, si dichiara nel blocco stesso. La verifica costa un secondo e va fatta prima di scrivere il blocco, non dopo che qualcosa è fallito.

## Milestone: la consegna ordinaria è `chiudi`

Dove il progetto ha istanziato `chiudi-sessione`, un commit non si consegna più come sequenza di comandi `git add`, `git commit` e `git push`, ma come proposta di lanciare `chiudi` dal terminale dell'utente. Il momento lo decide il lavoro: quando un blocco coerente è concluso e verificato, cioè una funzionalità, una correzione, una regola o un documento che ha senso ritrovare da solo nella storia, l'agente, Claude Code o Codex, scrive in `_notes/COMMIT-MSG.txt` il messaggio che descrive quella milestone e lo dice in una riga, con il messaggio accanto. L'utente lancia `chiudi`, rilegge file, ramo, autore e messaggio, e conferma o rifiuta.

Una milestone è un commit, e `chiudi` è il solo modo ordinario di farlo, sia a metà sessione sia alla fine: a metà il wipe si salta da solo perché la sessione è aperta, alla fine parte. Ne seguono due conseguenze. Un giro di lavoro che produce più milestone ne propone una alla volta, ciascuna con il proprio messaggio, invece di accumularle in un commit unico che la storia non sa più distinguere. E un giro che non chiude niente di coerente non propone nessun commit: la memoria su disco si aggiorna comunque a ogni giro sostanziale secondo `chat-non-e-memoria.md`, e il commit resta la fotografia di un punto fermo, non un salvataggio continuo.

Prima di proporre `chiudi`, l'agente esegue lui stesso i controlli di chiusura con `chiudi -SoloControlli`, cioè `powershell -NoProfile -ExecutionPolicy Bypass -File tools/chiudi-sessione.ps1 -SoloControlli` oppure `bash tools/chiudi-sessione.sh --solo-controlli`, e la propone solo se l'ultima riga dice «Controlli verdi». Lanciare a mano alcuni controlli non basta: caso osservato il 2026-10-05 in un progetto istanziato, l'agente aveva eseguito cinque dei dodici controlli, tutti verdi, e `chiudi` si è fermato sul correttore degli accenti per sedici forme in quattro file. Due di quei file erano note generate, e l'errore stava nel testo scritto dentro lo strumento che le genera, che lo riportava nelle note a ogni rigenerazione; le altre erano parole fra apici semplici in annotazioni appena scritte, che il correttore legge come accenti scritti con l'apostrofo. Ne segue anche che un difetto di questo genere in un documento generato si corregge nello strumento che lo scrive, e le citazioni brevi in prosa si scrivono fra caporali e non fra apici semplici. Al proprietario una proposta di commit che fallisce costa un giro intero, e chi lavora a blocchi lo vive come un commit perso.

I comandi git per esteso, nel formato descritto sopra, restano per i casi che `chiudi` non copre: un progetto dove lo script non è istanziato, un commit che deve includere solo una parte delle modifiche presenti, un'operazione diversa dal commit sul ramo in uscita.

## Il push si raggruppa, il commit no, e a dirlo è il budget della verifica automatica

Sezione nata da un progetto istanziato che ha esaurito la quota mensile di minuti della propria verifica automatica e si è bloccato per un giorno e mezzo su una modifica pronta. La misura che l'ha chiarita non è il numero di corse ma il loro costo per lavoro: la fatturazione arrotonda **per lavoro** al minuto superiore, quindi un flusso da quattro lavori e uno da due costano insieme una ventina di minuti **a ogni push**, qualunque cosa contenga quel push. Convertita in budget, una quota mensile di duemila minuti vale circa novanta push su un ramo con richiesta di fusione aperta, non novanta giornate di lavoro.

Ne discende una separazione che vale ovunque esista una verifica a consumo. **Il commit resta granulare**, perché la storia deve poter distinguere una milestone dall'altra e un commit non costa niente: è scrittura locale. **Il push si raggruppa**, perché è il push a innescare la spesa. Più milestone maturate nello stesso giro restano commit distinti e partono con un solo `git push`.

Il caso peggiore, e il più facile da commettere, è il commit di sola documentazione spinto da solo su un ramo con richiesta di fusione aperta: costa come uno di codice e non verifica niente che non fosse già verde. Si tiene in locale fino al push di codice, oppure va sul ramo principale se la convenzione del progetto ci manda la documentazione, dove un filtro per percorso può escluderlo davvero.

Quel "davvero" è letterale e contiene la trappola. Un filtro di percorso sull'innesco della richiesta di fusione **si valuta sul diff completo della richiesta**, testa contro base, non sui file dell'ultimo push: se la richiesta contiene anche una riga di codice, il filtro non esclude più nessuno dei push successivi, e chi lo legge nel file del flusso crede di avere una protezione che non c'è. Sull'innesco del push verso il ramo principale, invece, il filtro si valuta sui file di quel push e funziona come ci si aspetta. Una protezione che si crede attiva e non lo è costa più di una assente, perché fa smettere di cercare il risparmio altrove.

Due verifiche da fare una volta per progetto, prima di accusare il ritmo dei commit. Che i flussi dichiarino `concurrency` con `cancel-in-progress`, altrimenti due push ravvicinati sullo stesso ramo pagano entrambi per intero. E che la misura venga dai tempi per lavoro, perché l'endpoint di temporizzazione delle corse può rispondere zero minuti fatturabili anche su una corsa di sei minuti.

## Creare una pull request che esiste già non ne aggiorna la descrizione

Il comando che crea una pull request, lanciato quando per quel ramo ne esiste già una aperta, **rifiuta e stampa il collegamento a quella esistente**. è un esito che si legge come riuscito: compare un indirizzo, nessun errore in rosso, e chi ha lanciato il comando conclude che la descrizione sia stata consegnata. **Non lo è stata.** La descrizione resta quella del momento in cui la pull request fu aperta, mentre il file nel repository è andato avanti, e i due divergono senza che niente lo segnali.

La conseguenza è peggiore di una semplice omissione, perché sotto quella descrizione vecchia continuano ad arrivare commit nuovi: chi apre la pull request legge uno stato del lavoro che il lavoro ha già superato, e non ha modo di accorgersene.

La prescrizione: dopo ogni giro che cambia il file della descrizione si lancia il comando di **modifica**, non quello di creazione, e si guarda che risponda. Il comando di creazione si usa una volta sola, quando la pull request davvero non esiste; se non si sa se esista, lo si chiede prima invece di dedurlo dall'esito del comando di creazione.

## Messaggio di commit

Il messaggio di commit è una sola stringa tra doppi apici, al massimo 72 caratteri, che descrive le modifiche in italiano nella forma "Aggiunte X, Y" oppure "Nuova regola X: descrizione" oppure "Aggiornato Y: cosa cambia". Se il contesto richiede più dettaglio, lo si scrive nella risposta testuale prima dei comandi, non nel messaggio di commit.

Nessun commit porta attribuzioni a un agente: niente righe `Co-Authored-By`, niente firme del tipo "Generated with", né per Claude Code né per Codex, in nessun commit del progetto e anche quando le istruzioni di sistema dell'agente le suggerirebbero. Un commit porta soltanto l'identità git locale dell'utente, che è l'autore. Il presidio è l'hook `.githooks/commit-msg`, modello in `.claude/templates/readme-sync/githooks/commit-msg`, che rifiuta un messaggio con un'attribuzione o con l'oggetto oltre i 72 caratteri, qualunque sia la via da cui il commit parte.

## Identità da verificare

Prima di fornire i comandi, l'agente verifica che la configurazione locale del repository sia corretta (user.name, user.email, remote origin) secondo il riferimento della skill `identita-git`, che si carica se la verifica non è già stata fatta in sessione. Se l'identità locale non è impostata, propone i comandi di configurazione prima di quelli di commit.
