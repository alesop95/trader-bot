---
name: book-digest
description: >
  Trasforma un PDF o documento tecnico denso in una skill pre-digerita e interrogabile on-demand,
  creata dentro il progetto sotto .claude/skills/<slug>/. Produce SKILL.md con i modelli mentali e
  l'indice, chapters/ caricati a richiesta, glossary.md, patterns.md e cheatsheet.md. Non e' RAG:
  pre-digerisce il libro in sintesi dense. A invocazione manuale.
disable-model-invocation: true
---

## Premessa

Adatta il pattern di book-to-skill. La skill-libro generata vive nel progetto, sotto
`.claude/skills/<slug>/`, versionata: il default e' locale, non globale. La promozione al contesto
globale di Claude avviene solo su conferma esplicita dell'utente.

## Quando si invoca

Quando si vuole poter interrogare un libro o PDF tecnico durante il lavoro senza rileggerlo. Si
indica il file sorgente e uno slug breve per la skill risultante, per esempio `ddia` per Designing
Data-Intensive Applications.

## Procedura

1. Leggere il documento sorgente a fette, mai tutto in una volta: la lettura dei PDF avviene per
   intervalli di pagine. Ricostruire la struttura in capitoli o sezioni.
2. Per ogni capitolo, scrivere `chapters/ch<NN>-<slug>.md` con una sintesi densa: modelli mentali,
   tecniche e regole pratiche, in voce da praticante ("usa X quando Y"), mai testo grezzo copiato.
3. Scrivere `glossary.md` con i termini chiave e i riferimenti ai capitoli, `patterns.md` con le
   tecniche e i design pattern, `cheatsheet.md` con tabelle decisionali e regole rapide.
4. Scrivere `SKILL.md` con i modelli mentali principali del libro e l'indice dei capitoli, in modo
   che all'invocazione entri in contesto solo la sintesi e non il testo dei capitoli.
5. Riferire dove e' stata creata la skill e ricordare i due path: uso operativo in sessione
   (path A) e, se il progetto ha `knowledge-wiki`, alimentazione della wiki (path B).

## Promozione al globale

La skill-libro resta locale al progetto. Se l'utente vuole renderla disponibile a tutti i progetti,
su sua conferma esplicita la si copia in `~/.claude/skills/<slug>/` e si registra la promozione,
per esempio con una voce nel work-log del progetto. Mai promuovere al globale senza conferma.

## Vincoli

Densita sopra completezza: una sintesi da mille token vale piu di un estratto da diecimila. Mai
testo grezzo: sempre estrazione di segnale. On-demand: i capitoli si caricano solo quando servono.
Non eseguire `git add`, `commit` o `push`: restano all'utente.

Idempotenza: rilanciare `book-digest` sullo stesso slug aggiorna la skill-libro esistente in luogo,
senza duplicarla.
