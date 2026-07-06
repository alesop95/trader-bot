# Profilo di stack: Python (scripting, data, RAG)

> Regola modulare istanziata dal pacchetto `stack-profiles` come `stack-profile.md`. Prescrive le convenzioni con cui si scrive il codice di questo stack; la descrizione dello stack reale del progetto resta nella scheda `context/STACK.md`. Adattare i comandi agli strumenti reali del progetto alla prima istanziazione.

## Ambiente e tipi

L'ambiente si gestisce con `uv` oppure con un venv classico, con le dipendenze pinnate nel manifesto versionato e l'ambiente materializzato ignorato, secondo la sezione 13 di `PROJECT-SYSTEM.md`. Type hints ovunque, con `mypy` o `pyright` puliti come condizione di merge. Formattazione e lint con ruff (o black per la sola formattazione, se il progetto lo usa gia').

## Test

I test girano con pytest. L'I/O esterno si isola nelle fixture, e i test unitari non toccano mai la rete: cio' che parla con l'esterno si mocka o si sposta nei test di integrazione, marcati come tali.

## Pipeline RAG

Nei progetti RAG[^1] le quattro fasi, ingestion, indexing, retrieval e generation, restano moduli separati con confini espliciti, e le fonti recuperate si loggano sempre insieme alla risposta generata, cosi che ogni output sia riconducibile a cio' che lo ha fondato. Vale il principio della regola `token-economy`: il lavoro deterministico va in script, l'LLM si chiama solo per il salto semantico.

## Comandi tipici

Da adattare agli strumenti reali del progetto.

```
uv run pytest      # test
ruff check .       # lint
pyright            # typecheck
```

## Prima di committare

Lint, typecheck e test verdi, diff rivisto, nessun secret in stage. Il commit resta manuale dell'utente, secondo la regola generale del sistema.

[^1]: *RAG*, Retrieval-Augmented Generation - architettura in cui il modello genera risposte a partire da contenuto recuperato da una base di conoscenza.
