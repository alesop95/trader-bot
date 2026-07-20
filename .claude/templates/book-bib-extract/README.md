# Pacchetto book-bib-extract

> Pacchetto opzionale del sistema di progetto. Estrae i metadati bibliografici (autore, titolo,
> anno, editore, edizione, ISBN) dal frontespizio/colophon di un libro gia' ingerito da
> `doc-ingest`, propone una citekey e aggiorna un registro unificato a tre stati (verificata,
> da-verificare, scartata). Scrive una voce `.bib` reale solo dopo conferma umana esplicita
> contro il colophon: mai un campo stimato o dedotto dal solo nome del file. Si offre al gate dei
> pacchetti (vedi `../PACKAGES.md`) ai progetti che costruiscono una bibliografia da libri fisici
> o scansionati senza DOI, per esempio libri di studio posseduti dall'autore.

## Il vuoto che copre

Due pacchetti vicini non risolvono lo stesso problema. `doc-ingest` estrae struttura e testo di
un corpus, non anagrafica bibliografica: sa dire quante parole ha un documento, non chi ne e'
l'autore. `academic-researcher` e' pensato per paper accademici con DOI, verificabili contro
Semantic Scholar, OpenAlex o Crossref: un metodo che non si applica a un libro di studio senza
DOI, la cui unica fonte di verita' e' il colophon stampato. `book-bib-extract` si inserisce tra i
due: legge la cache gia' prodotta da `doc-ingest`, propone i campi bibliografici, e li fa
verificare a un umano contro il libro vero, non contro un database esterno.

## Rapporto con book-digest (pattern book-to-skill)

Se il progetto ha anche il pacchetto `book-to-skill` attivo (skill `book-digest`, che trasforma un
libro in una skill-libro interrogabile on-demand), i due pacchetti condividono lo stesso registro
`_notes/book-bib-registry.json` invece di tenere due sistemi di stato paralleli da riconciliare a
mano. `book-bib-extract` possiede il campo `bib_status` (la bibliografia), `book-digest` possiede
il campo `skill_status` (la trasformazione in skill): ciascuno aggiorna solo il proprio campo e
legge l'altro in sola lettura. Se `book-to-skill` non e' attivo, il registro funziona comunque da
solo, con `skill_status` sempre a `null`.

## Verifica visiva per PDF scansionati senza OCR affidabile

Nell'unico caso reale osservato finora (corpus di libri di chitarra/armonia, in gran parte
fotocopie o scansioni datate), il fallback `--ocr` di `doc-ingest` e' uscito a zero parole:
l'OCR su scansioni di bassa qualita' e' spesso inaffidabile o rumoroso, non un problema di
attivazione del flag. La via pratica per questi casi, gia' standardizzata nello script
`tools/extract-titlepages.py` del pacchetto, e' estrarre poche pagine di frontespizio/colophon
come immagini PNG (`pdftoppm`/Poppler, DPI e range pagine fissi) e leggerle visivamente, mai
un OCR sull'intero corpus. Per una minoranza di copie con difetti di scansione che omettono la
pagina di copyright, anche questa via puo' non trovare un anno: e' un limite pratico del metodo
da dichiarare come tale (`bib_status: da-verificare` a tempo indeterminato), non un errore di
ricerca insufficiente.

## Mappa di istanziazione

```
templates/book-bib-extract/skills/book-bib-extract/SKILL.md  ->  <radice>/.claude/skills/book-bib-extract/SKILL.md  (tracciato)
templates/book-bib-extract/tools/extract-titlepages.py        ->  <radice>/tools/extract-titlepages.py               (tracciato)
templates/book-bib-extract/tools/render-bib-registry.py       ->  <radice>/tools/render-bib-registry.py              (tracciato)
(registro generato alla prima invocazione)                     <radice>/_notes/book-bib-registry.json               (locale, ignorato)
(tabella rigenerata da render-bib-registry.py)                 <radice>/_notes/book-bib-registry.md                 (locale, ignorato)
```

## Come funziona

Per ogni libro gia' ingerito con `doc-ingest`, la skill legge solo le pagine di
frontespizio/verso/colophon del mirror Markdown (o, per gli scan senza testo nativo, le pagine
renderizzate da `extract-titlepages.py`), propone i campi e una citekey, e si ferma per la
conferma umana "a colophon" prima di scrivere qualunque cosa nel registro con stato `verificata`
o nel `.bib` reale. Il registro tiene traccia di ogni libro con lo stesso hash `sha256` gia'
calcolato da `doc-ingest`; per una fonte identificata ma non ancora fisicamente acquisita (per
esempio un ISBN trovato online) usa una chiave alternativa `manual-<identificatore>`, descritta nel
dettaglio del `SKILL.md`. Dopo ogni aggiornamento del registro si rilancia
`tools/render-bib-registry.py`, che rigenera una tabella leggibile in Markdown senza mai editarla
a mano.

## Uso

```bash
# Precondizione: il file deve gia' essere nel manifest di doc-ingest
python tools/doc-ingest.py percorso/al/corpus

# Per un PDF scansionato senza testo nativo, estrarre le pagine di frontespizio/colophon
python tools/extract-titlepages.py "percorso/libro.pdf" --slug nome-slug --out _notes/.tmp-doc-cache/titlepages

# Invocare la skill (manuale, disable-model-invocation: true)
# poi, dopo conferma e aggiornamento del registro:
python tools/render-bib-registry.py
```

## Crediti

Costruito su `pdftoppm` (Poppler, licenza GPL-2.0), gia' presumibilmente disponibile se il
progetto usa gia' `doc-ingest` con motore Docling o altre pipeline PDF. Non introduce dipendenze
Python nuove oltre alla libreria standard: `render-bib-registry.py` e' puro parsing di testo.
