# Formato dei comandi git per esecuzione manuale

> Regola modulare. Definisce come l'agente deve presentare i comandi git (add, commit, push) che l'utente esegue manualmente: in quale forma, cioè un comando per riga senza caratteri di continuazione, e in quale sintassi, cioè quella della macchina su cui si sta lavorando e non entrambe insieme. Vale ogni volta che l'agente fornisce comandi git da eseguire a mano. I casi osservati che hanno prodotto queste prescrizioni, con le misure e le date, stanno in `.claude/norme/git-commands-format.md`: quel file non si carica all'avvio di una sessione e non serve per applicare la regola, serve a chi deve estenderla o rimetterla in discussione.

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

## Il contesto non si deduce, si dichiara

Un comando corretto eseguito in un contesto diverso da quello presupposto non è un comando corretto, e il contesto non si deduce mai: si dichiara nel blocco stesso, prima di consegnarlo. Sono otto i presupposti che un blocco di comandi porta con sé senza nominarli, ciascuno osservato cadere in un progetto istanziato: la macchina su cui il blocco va incollato, la cartella corrente del terminale dell'utente, il ramo corrente, lo stato dell'albero di lavoro, lo stato del ramo di destinazione quando il blocco ne cambia uno, le variabili d'ambiente di un terminale aperto prima di un'installazione, la riscrittura dei percorsi che Git Bash applica a un argomento nella forma `revisione:percorso`, e la presenza di un altro agente che lavora nello stesso albero.

Ne discendono le prescrizioni vincolanti. Il primo comando di ogni blocco è il `cd` alla cartella del progetto, sempre, anche quando la sessione dell'agente è già lì, perché il terminale dell'utente è un processo diverso e la sua directory corrente non è osservabile né deducibile. Il blocco dichiara su quale macchina e su quale ramo va eseguito, e un blocco che contiene un `ssh` dichiara di essere per la macchina di partenza, mai per quella di arrivo. Una sequenza che cambia ramo si consegna solo con l'albero pulito e mette l'aggiornamento del ramo di destinazione prima del cambio, non dopo; più robusto ancora è decidere dove scrivere prima di scrivere, invece di spostare il lavoro dopo. Dopo l'installazione di un programma, il primo comando che lo usa si consegna per percorso completo e non per nome, finché non c'è conferma che il terminale sia stato riaperto. Una misura presa con uno strumento che può fallire in silenzio si controlla una volta sulla sua forma grezza prima di fidarsi del totale, perché dentro una pipe un fallimento si legge come zero, cioè come una risposta plausibile.

L'ottavo presupposto riguarda la presenza di qualcun altro e non produce nessun fallimento, quindi va verificato invece che notato. Prima di consegnare qualunque sequenza che committi si guarda `git status` e si confronta l'elenco con ciò che si è scritto davvero in questa sessione: un file modificato che non si riconosce, un file già in stage che non si è messo in stage, un commit comparso da quando la sessione è cominciata sono tutti indizi che un'altra sessione sta scrivendo qui. Riconosciuta la situazione, `git add -A` smette di essere lo strumento giusto perché il suo perimetro è l'albero e non il proprio lavoro, uno script di chiusura che faccia `add -A` per conto proprio non si lancia affatto, e se due file portano il lavoro di entrambe le sessioni si aspetta che l'altra committi invece di separarli per riga. La forma robusta è non arrivarci: una milestone alla volta per albero.

## Milestone: la consegna ordinaria è `chiudi`

Dove il progetto ha istanziato `chiudi-sessione`, un commit non si consegna più come sequenza di comandi `git add`, `git commit` e `git push`, ma come proposta di lanciare `chiudi` dal terminale dell'utente. Il momento lo decide il lavoro: quando un blocco coerente è concluso e verificato, cioè una funzionalità, una correzione, una regola o un documento che ha senso ritrovare da solo nella storia, l'agente, Claude Code o Codex, scrive in `_notes/COMMIT-MSG.txt` il messaggio che descrive quella milestone e lo dice in una riga, con il messaggio accanto. L'utente lancia `chiudi`, rilegge file, ramo, autore e messaggio, e conferma o rifiuta.

Una milestone è un commit, e `chiudi` è il solo modo ordinario di farlo, sia a metà sessione sia alla fine: a metà il wipe si salta da solo perché la sessione è aperta, alla fine parte. Ne seguono due conseguenze. Un giro di lavoro che produce più milestone ne propone una alla volta, ciascuna con il proprio messaggio, invece di accumularle in un commit unico che la storia non sa più distinguere. E un giro che non chiude niente di coerente non propone nessun commit: la memoria su disco si aggiorna comunque a ogni giro sostanziale secondo `chat-non-e-memoria.md`, e il commit resta la fotografia di un punto fermo, non un salvataggio continuo.

Prima di proporre `chiudi`, l'agente esegue lui stesso i controlli di chiusura con `chiudi -SoloControlli`, cioè `powershell -NoProfile -ExecutionPolicy Bypass -File tools/chiudi-sessione.ps1 -SoloControlli` oppure `bash tools/chiudi-sessione.sh --solo-controlli`, e la propone solo se l'ultima riga dice «Controlli verdi». Lanciare a mano alcuni controlli non basta: caso osservato il 2026-10-05 in un progetto istanziato, l'agente aveva eseguito cinque dei dodici controlli, tutti verdi, e `chiudi` si è fermato sul correttore degli accenti per sedici forme in quattro file. Due di quei file erano note generate, e l'errore stava nel testo scritto dentro lo strumento che le genera, che lo riportava nelle note a ogni rigenerazione; le altre erano parole fra apici semplici in annotazioni appena scritte, che il correttore legge come accenti scritti con l'apostrofo. Ne segue anche che un difetto di questo genere in un documento generato si corregge nello strumento che lo scrive, e le citazioni brevi in prosa si scrivono fra caporali e non fra apici semplici. Al proprietario una proposta di commit che fallisce costa un giro intero, e chi lavora a blocchi lo vive come un commit perso.

I comandi git per esteso, nel formato descritto sopra, restano per i casi che `chiudi` non copre: un progetto dove lo script non è istanziato, un commit che deve includere solo una parte delle modifiche presenti, un'operazione diversa dal commit sul ramo in uscita.

## Messaggio di commit

Il messaggio di commit è una sola stringa tra doppi apici, al massimo 72 caratteri, che descrive le modifiche in italiano nella forma "Aggiunte X, Y" oppure "Nuova regola X: descrizione" oppure "Aggiornato Y: cosa cambia". Se il contesto richiede più dettaglio, lo si scrive nella risposta testuale prima dei comandi, non nel messaggio di commit.

Nessun commit porta attribuzioni a un agente: niente righe `Co-Authored-By`, niente firme del tipo "Generated with", né per Claude Code né per Codex, in nessun commit del progetto e anche quando le istruzioni di sistema dell'agente le suggerirebbero. Un commit porta soltanto l'identità git locale dell'utente, che è l'autore. Il presidio è l'hook `.githooks/commit-msg`, modello in `.claude/templates/readme-sync/githooks/commit-msg`, che rifiuta un messaggio con un'attribuzione o con l'oggetto oltre i 72 caratteri, qualunque sia la via da cui il commit parte.

## Identità da verificare

Prima di fornire i comandi, l'agente verifica che la configurazione locale del repository sia corretta (user.name, user.email, remote origin) secondo il riferimento della skill `identita-git`, che si carica se la verifica non è già stata fatta in sessione. Se l'identità locale non è impostata, propone i comandi di configurazione prima di quelli di commit.
