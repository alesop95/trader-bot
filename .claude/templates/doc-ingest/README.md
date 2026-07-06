# Pacchetto doc-ingest

> Pacchetto opzionale del sistema di progetto. Estrae un corpus di documenti voluminosi, in
> `.pdf`, `.docx`, `.pptx`, `.xlsx` o `.html`, in una cache Markdown locale e ignorata da git, con
> ingest incrementale a content-hash e un indice di Livello 1 rigenerato a ogni corsa. Zero
> consumo di token: l'estrazione e' interamente locale e deterministica, nessuna chiamata LLM. Si
> offre al gate dei pacchetti (vedi ../PACKAGES.md) ai progetti che hanno o riceveranno piu
> documenti voluminosi da consultare durante il lavoro, senza bisogno di versionarli. Non si
> propone dove basta l'ingestione manuale di un singolo documento gia descritta nel README di
> radice, ne dove serve produrre una documentazione tecnica versionata da un `.docx`: per quel
> caso c'e il pacchetto `docx-to-docs`.

## Rapporto con l'ingestione manuale e con docx-to-docs

Tre strumenti distinti coprono lo stesso principio, la disclosure progressiva descritta in
`.claude/rules/token-economy.md`, su tre scale diverse. L'ingestione manuale a fette, descritta
nel README di radice, resta la via per un singolo documento occasionale: si estrae a mano una
volta e si legge solo la porzione utile, senza alcuno script. Questo pacchetto automatizza lo
stesso principio quando i documenti sono molti, tenendo una cache persistente che si aggiorna in
modo incrementale invece di rifare il lavoro a ogni sessione. Il pacchetto `docx-to-docs` risolve
un problema diverso e non concorrente: parte da un `.docx` che e la fonte di verita umana e lo
trasforma una volta per tutte in un albero `docs/` versionato, destinato a restare come
documentazione del progetto. La cache di `doc-ingest` e invece effimera, pensata per essere
riletta e rigenerata, mai per essere committata come documentazione finale.

## Mappa di istanziazione

L'istanziazione copia lo script nella cartella `tools/` del progetto; la cache si crea alla prima
esecuzione, sotto `_notes/`, gia' ignorato da git secondo `.claude/PROJECT-SYSTEM.md`.

```
templates/doc-ingest/doc-ingest.py  ->  <radice>/tools/doc-ingest.py        (tracciato)
(cache generata dallo script)           <radice>/_notes/.tmp-doc-cache/     (locale, ignorata)
```

## Come funziona

Lo script cammina ricorsivamente la cartella sorgente indicata e converte ogni documento nelle
estensioni supportate. Il motore di default e `markitdown` (Microsoft, licenza MIT), che copre
`.pdf`, `.docx`, `.pptx`, `.xlsx` e `.html` con un'unica dipendenza leggera, senza modelli pesanti
ne GPU. Un manifest a content-hash (`sha256` per file) tiene traccia di cosa e gia stato
convertito: alla corsa successiva i file invariati vengono saltati e solo i nuovi o modificati
vengono riconvertiti, lo stesso pattern di ingest incrementale gia validato nel pacchetto di
riconciliazione delle schede tecniche.

Al termine della corsa lo script rigenera `_INDEX.md` nella cartella di cache: per ogni documento
riporta il titolo, l'albero delle intestazioni Markdown (parsing deterministico dei simboli `#`,
senza alcun LLM coinvolto), il conteggio di parole, tabelle e immagini, e lo stato rispetto alla
corsa precedente. Questo file e lo scheletro di Livello 1 della disclosure progressiva: un agente
lo legge per intero a costo quasi nullo e decide da li quale mirror Markdown aprire e quale
sezione leggere, senza mai caricare l'intero corpus in contesto. I Livelli 2 e 3, la preview di
sezione e la lettura della singola sezione, restano disciplina di lettura sui file gia estratti,
non richiedono altro codice.

Due modalita opzionali estendono il motore di default, entrambe importate solo quando richieste
esplicitamente, cosi che l'installazione minima resti leggera. Il flag `--engine docling` sposta
l'estrazione dei soli `.pdf` su `Docling` (IBM Research, codice open source), che usa modelli di
analisi del layout per i casi dove `markitdown` degrada: tabelle complesse, colonne multiple,
documenti accademici densi. E una dipendenza piu pesante, da installare solo quando il motore di
default produce output visibilmente rotto su un file specifico. Il flag `--ocr` tenta un fallback
via `pytesseract` sui `.pdf` il cui testo nativo estratto risulta sotto una soglia minima,
sintomo tipico di uno scan senza livello di testo; richiede il binario di sistema `tesseract-ocr`
installato a parte, e se manca lo script segnala il file nell'indice invece di interrompere
l'intera corsa.

## Uso

Dipendenza sempre richiesta: `markitdown` (`pip install markitdown`). Le due dipendenze opzionali
si installano solo se si usano i rispettivi flag: `pip install docling` per `--engine docling`,
`pip install pytesseract pdf2image` piu il binario `tesseract-ocr` di sistema per `--ocr`.

```bash
python tools/doc-ingest.py percorso/al/corpus
python tools/doc-ingest.py percorso/al/corpus --engine docling
python tools/doc-ingest.py percorso/al/corpus --ocr
python tools/doc-ingest.py percorso/al/corpus --force
```

Il comando e ripetibile: rieseguito senza modifiche ai sorgenti non riconverte nulla e si limita a
confermare l'indice. `--force` ignora il manifest e riconverte l'intero corpus, utile dopo un
aggiornamento del motore di estrazione. La cartella sorgente dei documenti, la cache e il
manifest restano locali e ignorati da git; solo lo script si versiona.

## Crediti

Costruito su `markitdown` di Microsoft per l'estrazione di default (licenza MIT):
https://github.com/microsoft/markitdown. Modalita accurata opzionale su `Docling` di IBM
Research (codice open source; le licenze dei pesi dei modelli di layout non sono state
verificate in questa sessione e vanno controllate all'installazione):
https://github.com/docling-project/docling. Fallback OCR opzionale su `pytesseract`, wrapper
Apache-2.0 del motore `tesseract-ocr`, anch'esso Apache-2.0.

Ispirato da due riferimenti esterni sulla stessa strategia, non adottati direttamente nello
script per motivi di licenza o di scriptabilita. `LiteDoc` di 0xovo (https://litedoc.xyz/,
https://github.com/0xovo/LiteDoc) converte `.pdf` in Markdown interamente nel browser, senza
alcuna dipendenza server: e un'ottima alternativa manuale per una conversione singola quando non
si vuole installare nulla, ma e uno strumento ad uso umano diretto, non scriptabile da un agente,
ed e licenziato AGPL-3.0. La guida pdf-to-markdown di mcp.directory descrive una pipeline a due
motori, `PyMuPDF4LLM` per la modalita veloce e `Docling` per quella accurata, con cache a
content-hash: l'architettura a due motori e ripresa qui, ma `PyMuPDF4LLM` non e stato adottato
perche si appoggia a `PyMuPDF`, sotto doppia licenza AGPL-3.0 o commerciale, meno adatta come
default per un template pensato per essere riusato anche in progetti proprietari.
