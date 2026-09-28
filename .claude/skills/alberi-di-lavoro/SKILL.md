---
name: alberi-di-lavoro
description: >
  Governa il caso in cui un progetto abbia più di un albero di lavoro git, cioè più cartelle
  agganciate allo stesso repository con git worktree, per tenere insieme produzione, test e
  una funzionalità in corso. Si carica quando `git worktree list` mostra più di un albero,
  quando si crea o si rimuove un albero, quando si apre una sessione in un albero che non è
  quello principale, e quando si deve decidere da dove leggere o dove scrivere la memoria
  versionata del progetto. Stabilisce che la memoria versionata descrive la branch e non il
  progetto, come si diagnostica in dieci secondi un albero che sta leggendo la verità di
  un'altra branch, e perché copiarla o fonderla sono entrambe correzioni sbagliate.
---

## Che cosa fa questa skill

La norma sta per intero in `RIFERIMENTO.md`, accanto a questo file, e va letta prima di operare. Il suo oggetto non è la tecnica di `git worktree` ma la conseguenza che quella tecnica ha su un sistema che versiona la memoria dell'agente dentro il repository: da quel momento la memoria non descrive lo stato del progetto, descrive lo stato della branch su cui è scritta, e chi apre un albero su una branch indietro riceve una fotografia vecchia che ha tutta l'aria di essere quella giusta.

## Quando si carica

Si carica quando il contesto pre-iniettato di sessione, o un `git worktree list`, mostra più di un albero, e in ogni momento in cui si sta per creare, rimuovere o entrare in un albero secondario. Si carica anche quando il progetto sta scegliendo la forma L2 al gate della separazione degli ambienti, perché è quel gate a deciderne l'adozione.

## Procedura minima

Entrando in un albero, prima di leggere qualunque scheda, si confronta lo stato dichiarato dalla memoria con quello osservabile del repository e degli altri alberi. Dove il progetto ha istanziato `tools/verifica-ripresa.py`, lo fa quello strumento nella sua prima riga di esito; altrove la stessa domanda si pone a mano confrontando la memoria di questo albero con quella delle altre branch.

La regola che ne discende è una sola: la memoria si legge dall'albero autorevole, per percorso assoluto, e non si copia né si fonde negli altri. Copiarla crea due memorie divergenti; fonderla porta nella branch nuova commit che non le appartengono. Una decisione presa lavorando in un albero secondario si registra nella memoria dell'albero autorevole e arriva agli altri quando le branch si fondono.

## Vincoli

La skill non crea né rimuove alberi di lavoro di propria iniziativa. Non esegue `git add`, commit o push, che restano manuali dell'utente. Un albero si rimuove con `git worktree remove` e non cancellando la cartella, altrimenti git continua a considerare in uscita la sua branch.
