---
name: bib-sync
description: >
  Mantiene research-vault/bibliography.bib allineato alla libreria di lavoro Zotero: per ogni
  fonte nello stato verificata secondo citation-tracker, propone l'aggiunta a Zotero (via il MCP
  server zotero-mcp se connesso, o manualmente se assente), esporta o aggiorna il .bib, segnala i
  duplicati, e ricorda che il file non va mai considerato definitivo finche' l'utente non lo ha
  aperto e validato in JabRef. Usare dopo che una o piu' fonti sono passate allo stato verificata,
  o su richiesta di sincronizzare il .bib con lo stato corrente della libreria.
disable-model-invocation: true
---

## Premessa

Questa skill implementa il pattern a due strumenti descritto nella sezione 3 di `research-vault/reference/claude-ricercatore-universitario-completo.md`: Zotero come libreria di lavoro viva, JabRef come editor e validatore finale del `.bib`. Il ponte tra i due e' il file stesso, `research-vault/bibliography.bib`.

## Flusso

Per ogni fonte nello stato verificata prodotta da `citation-tracker`, la skill propone l'aggiunta a Zotero. Se il progetto ha connesso il server MCP `zotero-mcp` (vedi `../PACKAGES.md`), l'aggiunta e il successivo export BibTeX passano dal MCP; altrimenti si chiede all'utente di aggiungere la fonte a Zotero manualmente (o direttamente al `.bib`, se il progetto non usa Zotero) e si registra l'operazione come manuale nel work-log. Dopo l'aggiunta, il `.bib` locale si aggiorna con le nuove voci, senza duplicare quelle gia' presenti: prima di scrivere, si confrontano titolo, autori e anno delle nuove voci con quelle esistenti nel file, e si segnala all'utente qualunque possibile duplicato invece di scriverlo silenziosamente due volte.

## Cosa non fa mai

Questa skill non inserisce mai nel `.bib` una fonte che non sia nello stato verificata secondo `citation-tracker`: la responsabilita' della verifica resta a monte, questa skill si limita a sincronizzare cio' che e' gia' stato verificato. Non considera mai il `.bib` risultante "definitivo": ogni volta che propone una modifica al file, ricorda esplicitamente che il controllo qualita' umano finale (duplicati residui, coerenza delle chiavi di citazione, formattazione BibLaTeX) resta un passaggio in JabRef a carico dell'utente, coerentemente con la regola `no-uncited-claims`.

## Prima esecuzione

Se `research-vault/bibliography.bib` non esiste ancora, lo si crea vuoto alla prima invocazione della skill, e si verifica con l'utente che si apra correttamente in JabRef sulla sua macchina prima di procedere con la prima sincronizzazione reale.
