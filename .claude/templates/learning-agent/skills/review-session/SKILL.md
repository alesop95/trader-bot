---
name: review-session
description: >
  Apre una sessione di ripasso guidata: interroga l'Anki MCP per le card dovute quando è
  connesso, o il campo progress di LEARNER_PROFILE.md in sua assenza, applica il testing effect
  (interroga prima di dare feedback) e per le lingue straniere offre anche il ripasso derivato
  dalla conversazione libera. Invocata da /review.
disable-model-invocation: true
---

## Premessa

Questa skill copre il motore di memoria dell'apprendimento (livello 2 dell'architettura, sezione 1 di `.claude/context/learning-agent-reference.md`) e l'esecuzione pratica del principio spaced repetition più active recall della sezione 4. Non genera nuove card da zero: quelle le propone `examiner` a chiusura di `learn-topic`; questa skill le porta in revisione.

## Percorso A, con Anki MCP connesso

Se `LEARNER_PROFILE.md` dichiara un Anki MCP connesso, la skill interroga i suoi tool per il numero di card dovute oggi e le recupera. Le presenta al learner una alla volta nell'ordine restituito dal server, applicando sempre l'ordine interroga-poi-feedback: mai mostrare la risposta prima che il learner abbia tentato. Registra la valutazione di ciascuna card (wrong, hard, good, easy o equivalente) tramite il tool di submit del server, così che lo scheduling successivo resti quello nativo di Anki.

## Percorso B, senza Anki MCP

Se nessun Anki MCP è connesso, la skill si basa sul campo `progress` di `LEARNER_PROFILE.md` e sugli errori registrati da `examiner` nelle sessioni precedenti di `learn-topic`. Ricostruisce un piccolo set di domande di richiamo attivo sui moduli già erogati, privilegiando quelli con errori non ancora risolti, e li pone con lo stesso principio interroga-poi-feedback. In questo percorso la cadenza non è calcolata da un algoritmo di scheduling ma dalla cadenza dichiarata dal learner in `LEARNER_PROFILE.md`: la skill lo dichiara esplicitamente, così l'utente sa che il ripasso qui è meno rigoroso di uno spaced repetition automatizzato.

## Ripasso conversation-derived per le lingue straniere

Per topic di categoria lingua straniera, oltre al ripasso di card, la skill offre la modalità descritta nella sezione 4.1 del riferimento: una breve conversazione libera nella lingua target, da cui estrae gli errori commessi, genera un ripasso mirato su quegli errori, e verifica con un mastery check finale invece di limitarsi a segnalarli. Questa modalità va offerta come opzione esplicita, non sostituisce il ripasso di card dovute quando ce ne sono.

## Vincoli

Non mostra mai la risposta o la soluzione prima che il learner abbia tentato la propria. Non tratta il ricordo isolato di un fatto come prova di saperlo applicare: se la card è di puro richiamo (per esempio una definizione o un vocabolo), e la categoria del topic è programmazione o lingua, la skill intercala almeno un compito di applicazione nella sessione, non solo richiamo di definizioni, coerentemente con il limite dichiarato nella sezione 4 del riferimento. Non esegue `git add`, `commit` o `push`.
