# Profilo di stack: Python (scripting, data, RAG)

> Regola modulare istanziata dal pacchetto `stack-profiles` come `stack-profile.md`. Prescrive le convenzioni con cui si scrive il codice di questo stack; la descrizione dello stack reale del progetto resta nella scheda `context/STACK.md`. Adattare i comandi agli strumenti reali del progetto alla prima istanziazione, e su un progetto esistente dividere le prescrizioni in "vale già" e "da adottare" (README del pacchetto, passo 2).

## Ambiente e tipi

L'ambiente è sempre separato da quello di sistema e non si versiona: `uv` dove si può scegliere, oppure un venv classico, con la cartella dell'ambiente ignorata da git, secondo la sezione 13 di `PROJECT-SYSTEM.md`. Le dipendenze sono bloccate, non solo dichiarate: il manifesto dice che cosa serve, il file di blocco (`uv.lock`, oppure un `requirements.txt` generato con le versioni esatte) dice che cosa è stato installato, ed è versionato. Senza il file di blocco due macchine installano versioni diverse dallo stesso manifesto, e la differenza si scopre in produzione. La versione di Python è dichiarata nel manifesto e non lasciata a quella che la macchina ha. Type hints ovunque, con `mypy` o `pyright` puliti come condizione di merge. Formattazione e lint con ruff, cioè `ruff format` e `ruff check`, con la configurazione nel manifesto e non in opzioni passate a mano (o black per la sola formattazione, se il progetto lo usa già).

## Test

I test girano con pytest. L'I/O esterno si isola nelle fixture, e i test unitari non toccano mai la rete: ciò che parla con l'esterno si mocka o si sposta nei test di integrazione, marcati come tali.

## Pipeline RAG

Nei progetti RAG[^1] le quattro fasi, ingestion, indexing, retrieval e generation, restano moduli separati con confini espliciti, e le fonti recuperate si loggano sempre insieme alla risposta generata, così che ogni output sia riconducibile a ciò che lo ha fondato. Vale il principio della regola `token-economy`: il lavoro deterministico va in script, l'LLM si chiama solo per il salto semantico.

## Gli stessi controlli in locale e in CI

I controlli sono gli stessi comandi, nello stesso ordine, in tre posti: a mano, nell'hook che precede il commit e nella CI. Si ottiene scrivendoli una volta sola, in un bersaglio del `Makefile` o in uno script del progetto, e facendoli chiamare da tutti e tre: una CI che lancia comandi propri, diversi da quelli locali, è verde su un codice che in locale nessuno ha controllato allo stesso modo. La CI installa dal file di blocco e fallisce se il blocco non corrisponde al manifesto, con `uv sync --locked` o l'equivalente. Dove il progetto usa `pre-commit`, l'hook chiama lo stesso script e non una copia della sua lista.

La base di questa sezione è la ricognizione del 2026-11-16 sui progetti allineati, in `docs/filone-stack-benchmark.md` del template: pytest compare in undici progetti, `uv` con il file di blocco in tre e ruff in tre, e nessuno di quelli letti dichiarava la CI e il locale legati allo stesso script.

## Comandi tipici

Da adattare agli strumenti reali del progetto.

```
uv sync --locked       # installa dal file di blocco, fallisce se non corrisponde
ruff format --check .  # formattazione
ruff check .           # lint
pyright                # typecheck
uv run pytest          # test
```

## Prima di committare

Lint, typecheck e test verdi, diff rivisto, nessun secret in stage. Il commit resta manuale dell'utente, secondo la regola generale del sistema.

[^1]: *RAG*, Retrieval-Augmented Generation - architettura in cui il modello genera risposte a partire da contenuto recuperato da una base di conoscenza.
