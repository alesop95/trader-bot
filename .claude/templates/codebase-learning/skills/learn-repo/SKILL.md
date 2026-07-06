---
name: learn-repo
description: >
  Guida l'utente fase per fase nell'apprendimento di una repository già finita o quasi finita di
  sviluppare: panoramica dello stack, astrazioni centrali, flussi end-to-end, design pattern e
  principi, idiomi dello stack rispetto alla versione in uso. Ogni affermazione tecnica cita
  codice reale con path e riga. Delega l'esplorazione al subagent code-tutor per non sporcare il
  contesto della sessione principale. Sola lettura, non modifica mai il progetto. Invocata da
  /learn-repo.
disable-model-invocation: true
---

## Premessa

Questa skill è l'orchestrazione descritta nelle sezioni 4.2 e 5 di `.claude/context/codebase-learning-reference.md`: cinque fasi in sequenza fissa, con una pausa di verifica dopo ognuna. Se il progetto dispone del subagent `code-tutor` con accesso al tool `Task`, questa skill gli delega l'esplorazione di ogni fase passandogli solo il nome della fase e l'eventuale argomento ricevuto da `/learn-repo`; se `Task` non è disponibile nell'ambiente, la skill esegue essa stessa la stessa procedura nello stesso turno, dichiarando esplicitamente che opera in modalità degradata senza isolamento di contesto.

## Le cinque fasi

Panoramica: usa `repomix` se connesso, altrimenti il file tree letto con `Glob`, per dare stack, moduli principali e punto di ingresso, e identificare il paradigma architetturale dominante (a strati, esagonale, event-driven, MVC o altro). Astrazioni centrali: usa `serena` (`find_symbol`, `find_references`) se connesso, altrimenti `Grep` mirato, per elencare cinque-otto astrazioni chiave e come si collegano, ciascuna con uno snippet preciso di path e intervallo di righe. Flussi: traccia uno o due flussi end-to-end, per esempio una richiesta dal controller al database, citando i simboli reali del call graph disponibile. Design puro: spiega i design pattern e i principi, per esempio i principi SOLID[^1] o la dependency injection, effettivamente usati, ancorando ogni affermazione a codice reale invece che a definizioni da manuale. Idiomi dello stack: confronta l'uso del framework nel progetto con le best practice della versione dichiarata, usando `context7` solo per le docs pubbliche del framework, mai per interrogare il codice del progetto.

[^1]: *SOLID*, acronimo dei cinque principi di design orientato agli oggetti: Single responsibility, Open-closed, Liskov substitution, Interface segregation, Dependency inversion.

## Regola di citazione e di ritmo

Ogni affermazione tecnica deve puntare a un file e un intervallo di righe reali del repository, o a una pagina di docs pubbliche interrogata da `context7`: una spiegazione generica scollegata dal codice non è un output valido di questa skill. Al termine di ogni fase la skill si ferma e propone due domande di autovalutazione sul contenuto appena coperto, prima di procedere alla fase successiva: l'utente può rispondere, chiedere approfondimento sulla stessa fase, o dire esplicitamente di proseguire.

## Vincoli

La skill non modifica mai un file del progetto: è sola lettura anche quando individua codice migliorabile, che al massimo segnala come osservazione separata dalla lezione. Non salta una fase e non ne inverte l'ordine senza una richiesta esplicita dell'utente, perché la sequenza panoramica-astrazioni-flussi-design-idiomi riflette una dipendenza di comprensione crescente. Se l'utente chiede di persistere il materiale prodotto, la skill non lo scrive da sé in `docs/learning/`: rimanda a `deepwiki-skill`, se attivata, o chiede conferma esplicita prima di scrivere qualunque file fuori dalla conversazione.
