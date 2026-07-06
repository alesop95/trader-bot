---
name: learn-topic
description: >
  Eroga la prossima unità di apprendimento del topic attivo in LEARNER_PROFILE.md: verifica che
  profilo e roadmap esistano (altrimenti invoca build-roadmap), recupera gli estratti pertinenti
  della knowledge base tramite kb-retriever, applica il template pedagogico della categoria e i
  modificatori del profilo cognitivo dichiarato, ed eroga la verifica finale tramite examiner.
  Invocata da /learn <topic>.
disable-model-invocation: true
---

## Premessa

Questa skill è il ciclo operativo di `tutor` per il caso "nuova unità", descritto nella sezione 3.1 di `.claude/context/learning-agent-reference.md`. Se il progetto dispone del subagent `tutor` con accesso al tool `Task`, questa skill si limita a invocarlo passandogli il topic richiesto; se `Task` non è disponibile nell'ambiente, la skill esegue direttamente la procedura sotto, che è la stessa logica del subagent senza l'isolamento di contesto.

## Procedura

Verifica anzitutto che `LEARNER_PROFILE.md` esista e contenga una roadmap per il topic richiesto: se manca l'uno o l'altra, invoca prima `build-roadmap` e non procede oltre finché non è stata prodotta. Determina poi il prossimo modulo o unità da erogare leggendo `progress.roadmap_module` e, per i topic a dipendenze strette come un linguaggio di programmazione, verifica che i prerequisiti dichiarati dal modulo siano già segnati come completati.

Recupera gli estratti pertinenti al modulo tramite `kb-retriever`, non a memoria: il contenuto della lezione si costruisce solo sugli estratti ricevuti, citati con il loro riferimento a capitolo o sezione. Applica quindi il ciclo della categoria pedagogica dichiarata in `category`. Per un linguaggio di programmazione il ciclo è mini-lezione seguita subito da pratica hands-on a bassa pressione sullo stesso concetto, mai spiegazione senza scrittura di codice immediata; per un topic di questa categoria offri anche l'analogia dalla vita quotidiana seguita da un diagramma, anche ASCII, del flusso, prima del walkthrough passo passo, secondo la skill di supporto descritta nella sezione 4.2 del riferimento. Per una lingua straniera il ciclo alterna esposizione a vocaboli o frasi in contesto e produzione immediata, mai parole isolate senza frase. Per una materia concettuale il ciclo privilegia costruzione di intuizione visiva prima della formalizzazione.

Applica poi i modificatori del profilo cognitivo dichiarato in `cognitive_profile`, secondo la sezione 5 del riferimento. Se è dichiarato ADHD, l'unità si tiene entro un blocco tipo pomodoro (circa 25 minuti di contenuto, non l'intero tempo di sessione dichiarato) con un checkpoint esplicito a metà. Se è dichiarato spettro autistico, la sessione segue sempre la stessa struttura dichiarata all'inizio (agenda esplicita, passi enunciati, niente metafore ambigue) e, quando possibile, aggancia gli esempi agli interessi speciali registrati in `special_interests`. Se è dichiarata dislessia, preferisci diagrammi e organizzatori grafici al testo denso, e segnala se un file va meglio letto con text-to-speech esterno invece che qui in chat. Se nessun profilo è dichiarato, applichi comunque i principi trasversali della sezione 5.4: mind mapping, flashcard, esperimenti hands-on quando pertinenti alla categoria.

Chiudi l'unità delegando la verifica a `examiner`: non consideri l'unità completata finché non è stata posta almeno una domanda di active recall e valutata la risposta. Solo a quel punto aggiorni `progress.roadmap_module` in `LEARNER_PROFILE.md` con il modulo appena completato, e se `examiner` ha proposto card Anki e un Anki MCP è connesso, le registri di conseguenza.

## Vincoli

Non spiega mai un contenuto della knowledge base senza prima averlo recuperato tramite `kb-retriever` nella stessa sessione: citare a memoria un estratto già visto in una sessione precedente è lo stesso errore di citarlo senza averlo mai letto. Non segna un modulo come completato senza una verifica di `examiner`. Non supera la dimensione di chunk implicata dal tempo di sessione dichiarato in `LEARNER_PROFILE.md`, specialmente quando è dichiarato ADHD.
