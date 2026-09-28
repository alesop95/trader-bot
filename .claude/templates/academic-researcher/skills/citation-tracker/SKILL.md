---
name: citation-tracker
description: >
  Traccia lo stato di ogni fonte bibliografica del progetto in uno dei tre stati verificata, da
  verificare, scartata, verificando titolo, autori, anno e DOI o arXiv-ID contro Semantic
  Scholar, OpenAlex e Crossref (o il server MCP refchecker-mcp se connesso), incluso il controllo
  delle retrazioni. Usare ogni volta che una fonte nuova entra in conversazione, prima che una
  citazione finisca nel testo o nel research-vault/bibliography.bib, e su richiesta per
  ricontrollare lo stato di fonti già tracciate.
disable-model-invocation: true
---

## Premessa

Questa skill implementa la sezione 7 di `research-vault/reference/claude-ricercatore-universitario-completo.md` ed è il meccanismo con cui la regola `no-uncited-claims` viene rispettata in pratica. Nessuna citazione entra nel testo finale o nel `.bib` senza essere passata da qui.

## I tre stati

Ogni fonte tracciata porta esattamente uno di tre stati, mai un quarto stato improvvisato. *Verificata*: titolo, autori, anno e DOI o arXiv-ID sono stati confermati contro almeno una fonte esterna, e la fonte non risulta ritirata. *Da verificare*: la fonte è stata trovata (da `literature-search`, da un upload dell'utente, o citata da un altro paper) ma non ancora incrociata. *Scartata*: la verifica ha fallito, i metadati non corrispondono, oppure la fonte risulta retracted.

## Come si verifica

Se il progetto ha connesso `refchecker-mcp` (vedi `../PACKAGES.md`), invocare `verify_citation` con titolo, autori, anno e DOI o arXiv-ID. Se ha scelto il connector OpenAlex ufficiale, `resolve_references` controlla fino a 25 riferimenti per chiamata e comunica la confidenza del match; `get_work` permette di confrontare il record completo. Se nessuno dei due MCP è connesso, incrociare manualmente i metadati con Semantic Scholar, OpenAlex o Crossref. In ogni percorso controllare lo stato di retrazione con una fonte adatta e aprire il testo originale prima di attribuire un claim al paper: il match bibliografico conferma l'esistenza del record, non il contenuto della citazione.

## Dove si registra lo stato

Lo stato di ogni fonte tracciata in una sessione di ricerca attiva si registra in `research-vault/tracked-sources.md` (o nel file di scope prodotto da `research-scoping`, se il progetto lo usa come registro unico), con una riga per fonte: titolo abbreviato, stato, data di verifica, motivo se scartata. Solo le fonti verificate passano a `bib-sync` per entrare in `research-vault/bibliography.bib`.

## Cosa fare con ogni stato

Una fonte verificata può essere citata nel testo e proposta per l'aggiunta a Zotero tramite `bib-sync`. Una fonte da verificare non si cita: si segnala esplicitamente all'utente come tale se è comunque rilevante per la conversazione in corso, mai in modo silenzioso. Una fonte scartata non si cita mai e si spiega il motivo dello scarto (mismatch, non trovata, retracted) quando l'utente chiede perché non compare nella sintesi.

## Esclusioni sempre valide

Una fonte proveniente da Sci-Hub o comunque non ad accesso aperto legittimo si scarta automaticamente, senza passare dal ciclo di verifica: l'esclusione è politica del progetto, non un giudizio caso per caso (vedi `no-uncited-claims`).
