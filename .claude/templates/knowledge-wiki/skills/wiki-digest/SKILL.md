---
name: wiki-digest
description: >
  Ingerisce una nuova fonte nella LLM Wiki del progetto. Legge i file aggiunti in
  knowledge/sources/, aggiorna o crea le pagine in knowledge/wiki/ secondo knowledge/WIKI-SCHEMA.md,
  collega i concetti correlati, gestisce le contraddizioni e appende una voce a knowledge/log.md.
  Scrive solo sulla wiki, non esegue git, e si invoca manualmente quando si aggiunge una fonte.
disable-model-invocation: true
---

## Premessa

Questa skill applica lo schema in `knowledge/WIKI-SCHEMA.md`, che e' la fonte di verita del
comportamento della wiki. Leggerlo per primo: i tipi di pagina, le regole di collegamento, di
aggiornamento e di gestione delle contraddizioni sono definiti li, non qui.

## Quando si invoca

Dopo aver aggiunto una o piu fonti in `knowledge/sources/` (note, articoli, PDF, oppure output di
book-to-skill in `sources/books/<slug>/`). L'utente decide quando ingerire: la skill non parte da
sola.

## Procedura

1. Determinare le fonti nuove o cambiate tramite un ingest-state: un piccolo file
   `knowledge/.ingest-state.json` che mappa ogni fonte all'hash SHA256 del suo contenuto e alla data
   di ingestione. Si calcola l'hash dei file in `knowledge/sources/` e si ingeriscono solo quelli
   nuovi o con hash diverso da quello registrato. E' un rilevamento piu robusto del semplice
   confronto col `log.md`, che resta il giornale leggibile delle ingestioni.
2. Per ciascuna fonte nuova: leggerla, estrarne concetti, entita e punti chiave, e produrre o
   aggiornare la pagina `wiki/sources/<fonte>.md` con il riassunto denso della fonte.
3. Aggiornare o creare le pagine in `wiki/concepts/` e `wiki/entities/` toccate dalla fonte,
   secondo lo schema, con i collegamenti reciproci.
4. Gestire le contraddizioni come prescritto dallo schema: registrare la divergenza con le fonti e
   la data, senza sovrascrivere in silenzio.
5. Appendere a `knowledge/log.md` una voce con la data, la fonte ingerita e le pagine toccate.

## Vincoli

Non leggere mai una fonte voluminosa per intero se non serve: estrarne il segnale a fette,
coerentemente con l'ingestione documenti del sistema. Non modificare `knowledge/sources/`: e'
append-only. Non eseguire `git add`, `commit` o `push`: le operazioni git restano all'utente. Non
inventare collegamenti o contenuti non presenti nelle fonti.

Re-ingestione idempotente: ingerire di nuovo una fonte aggiorna in luogo le pagine da essa derivate,
identificate in modo stabile (per esempio per nome di fonte o concetto), senza creare duplicati.
