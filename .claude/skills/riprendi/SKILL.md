---
name: riprendi
description: >
  Riapre una sessione partendo dal file di ripresa e verificando prima di fidarsene che
  descriva davvero il presente. Confronta l'impronta registrata a fine sessione con lo stato
  reale di git, individua che cosa una sessione caduta a metà non ha scritto, e solo dopo
  ricostruisce il punto di ripresa leggendo lo snapshot di memoria e la feature attiva. Si
  esegue come primo atto di ogni sessione nuova. È di sola lettura sul codice e non esegue
  mai git add, commit o push.
disable-model-invocation: true
---

## Contesto (best-effort, pre-iniettato)

!`git log -1 --format="%h %ad %s" --date=short` !`git status --short` !`git worktree list`

## Il problema, che non è la perdita del lavoro

La procedura di ripresa del sistema parte da `_notes/RESUME-PROMPT.md`, che l'agente aggiorna alla fine di ogni sessione con lo stato raggiunto e con il prompt da incollare. Lo strumento accetta anche il nome storico `_notes/RESUME_PROMPT.md`, così un progetto già istanziato non deve rinominare il proprio stato locale per adottare il presidio. Quella procedura presuppone una cosa che non sempre è vera: che la sessione precedente sia arrivata alla fine. Una sessione che cade a metà, per un crash, per una compattazione andata male o semplicemente perché la finestra è stata chiusa, lascia il progetto in uno stato che il file di ripresa non descrive.

Il danno non è la perdita del lavoro, che sta su disco e in git. È più sottile, e per questo peggiore: la sessione nuova legge il file di ripresa, lo prende per lo stato corrente, e costruisce sopra una premessa falsa. Nessuno se ne accorge, perché un file di ripresa vecchio ha esattamente lo stesso aspetto di uno aggiornato. Questa skill esiste per rendere meccanica quella distinzione invece di affidarla al ricordo di come sia finita l'ultima volta.

## Passo 1 - Verificare prima di leggere

Il primo comando non legge il file di ripresa: verifica che si possa credergli.

```
python tools/verifica-ripresa.py
```

Lo strumento confronta l'impronta registrata a fine sessione, cioè commit e forma dell'albero di lavoro in quel momento, con lo stato reale di adesso. Esce con codice diverso da zero quando qualcosa diverge, e dice che cosa in ordine di quanto conta: i commit comparsi dopo l'ultima registrazione, con il loro messaggio, perché sono il lavoro che una sessione ha prodotto senza chiudersi; l'albero di lavoro diverso da quello registrato, cioè i file che quella sessione stava toccando quando è caduta; i documenti di memoria che dichiarano un commit più vecchio di HEAD; le schede di contesto ancorate a un commit che nel repository non esiste più; e, dove il progetto usa più alberi di lavoro, gli altri alberi la cui branch porta nella memoria modifiche che questo albero non ha, con il percorso di ciascuno.

Se il progetto non ha lo strumento istanziato, la stessa domanda si pone a mano confrontando il commit dichiarato in `.claude/memory/index.md` con `HEAD`, guardando `git status --short` e, se `git worktree list` elenca più di un albero, confrontando la memoria con quella degli altri come descrive la norma `skills/alberi-di-lavoro/RIFERIMENTO.md`. È meno preciso e va detto quando lo si fa, perché senza impronta non si distingue un albero sporco lasciato di proposito da uno lasciato da una caduta.

## Passo 2 - Che cosa fare di una divergenza

Una divergenza è materiale da riportare all'utente prima di qualunque altra cosa, e non da correggere in silenzio, perché solo l'utente sa che cosa stava facendo. La forma è breve e in ordine di gravità.

Per i commit comparsi dopo la registrazione si guarda che cosa hanno toccato, con `git show --stat`, e si dice in una riga che cosa risulta fatto. Non si assume che il work-log lo sappia: si confronta con `.claude/memory/progress.md`, e se l'ultima voce non copre quei commit lo si dichiara, perché è esattamente il lavoro che la regola sulla persistenza chiede di scrivere e che quella sessione non ha scritto.

Per i file rimasti nell'albero di lavoro si chiede, non si decide. Un file a metà può essere un lavoro da riprendere o uno da buttare, e la differenza non si legge dal contenuto.

I documenti di memoria arretrati si aggiornano subito, nello stesso giro, come vuole `rules/chat-non-e-memoria.md`, e si dichiara quali file sono stati scritti così che l'utente li rilegga nel diff prima del commit.

Per una memoria più avanti in un altro albero non si propone nessun delta, perché copiarla o fonderla qui sono le due correzioni sbagliate che la norma `skills/alberi-di-lavoro/RIFERIMENTO.md` descrive: si dichiara che la memoria di questo albero è quella di un'altra branch, e da quel momento `index.md`, `decisions.md` e `progress.md` si leggono dall'albero autorevole per percorso assoluto, mentre codice e schede di contesto restano quelli di questo albero. Se il file di ripresa di questo albero non si apre già con quell'avviso, si propone di aggiungerlo in testa, che è il solo posto non versionato e quindi il solo che non eredita il tranello.

E per ciò che si sospetta perduto ma non si vede, cioè una decisione presa a voce nella sessione caduta, si dice chiaramente che non è ricostruibile da qui e si chiede se ce ne fosse una. È il buco che la regola `chat-non-e-memoria.md` previene a monte scrivendo nel giro di lavoro in cui il contenuto nasce; a valle resta solo la domanda.

## Passo 3 - Ricostruire il punto di ripresa

Solo quando lo stato è chiaro si segue la procedura ordinaria, che è quella scritta nel `CLAUDE.md` del progetto e che non va duplicata qui: si legge `.claude/memory/index.md` per lo snapshot, `.claude/context/current-work.md` se c'è una feature attiva, si invoca `sync-context` per misurare il drift fra schede e codice, e si leggono le sole schede pertinenti al task, mai tutte insieme.

Il file di ripresa si legge dopo, non prima, e con la consapevolezza di quanto sia attendibile: se la verifica non ha trovato divergenze descrive il presente, e allora il prompt che contiene si può eseguire così com'è; se ne ha trovate, il file resta utile per il contesto ma il punto di ripresa vero è quello ricostruito adesso.

## Passo 4 - Il recap, e poi fermarsi

Si consegna un recap conciso in quattro righe: dove siamo, che cosa risulta fatto, che cosa la verifica ha trovato di non scritto, e il prossimo passo concreto. Poi ci si ferma e si aspetta, senza cominciare il lavoro: una sessione che riprende e si mette subito a fare toglie all'utente l'unico momento in cui può correggere una premessa sbagliata.

## Chiudere la sessione, che è la metà che rende utile l'altra

Questa skill funziona solo se qualcuno registra l'impronta, e registrarla è l'ultimo atto di una sessione, non il primo della successiva.

```
python tools/verifica-ripresa.py --registra
```

Va fatto insieme all'aggiornamento del file di ripresa, cioè dopo aver scritto lo stato raggiunto e il prossimo passo, e dopo che l'utente ha fatto i propri commit, perché l'impronta fotografa lo stato in quel momento. Se si registra prima dei commit, la sessione successiva troverà una divergenza che non è una caduta ma una registrazione fatta troppo presto, e quel falso positivo insegna a ignorare il controllo, che è il modo in cui un presidio muore.

Il modo ordinario di farlo è `chiudi`, che l'utente lancia dopo aver chiuso la sessione: sul progetto esegue `tools/chiudi-sessione.ps1` in PowerShell oppure `tools/chiudi-sessione.sh` in Bash o Zsh, e registra solo dopo aver verificato che il commit sia arrivato a `origin` sul ramo corrente. All'agente resta di aggiornare il file di ripresa e di scrivere in `_notes/COMMIT-MSG.txt` il messaggio di commit proposto.

Una sessione che finisce senza registrare non produce un danno: produce esattamente la situazione che questa skill sa riconoscere, cioè un file di ripresa che non descrive il presente. È il comportamento voluto, ed è la ragione per cui l'impronta si registra e non si deduce.

## Automatizzarlo, se il progetto lo vuole

Il pacchetto `hooks-starter` copre la famiglia degli hook di apertura sessione. Dove sia attivo, la forma breve dello strumento sta in una riga e stampa un solo esito, così che la divergenza si veda senza che nessuno debba invocare niente.

```
python tools/verifica-ripresa.py --breve
```

Resta un presidio e non un sostituto della skill: l'hook dice che qualcosa diverge, questa procedura dice che cosa farne.
