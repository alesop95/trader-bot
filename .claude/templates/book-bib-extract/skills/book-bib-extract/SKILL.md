---
name: book-bib-extract
description: >
  Estrae i metadati bibliografici (autore, titolo, anno, editore, edizione, ISBN) dal
  frontespizio/colophon di un libro gia' ingerito da doc-ingest, propone una citekey e aggiorna
  il registro unificato _notes/book-bib-registry.json. Scrive una voce .bib reale solo dopo
  conferma umana esplicita contro il colophon. A invocazione manuale.
disable-model-invocation: true
---

## Premessa

Copre un vuoto lasciato da `doc-ingest` (estrae struttura, non anagrafica) e da
`academic-researcher` (pensato per paper con DOI, non per libri). Non e' un pacchetto a se: si
appoggia alla cache Markdown gia' prodotta da `doc-ingest` e scrive nello stesso registro unificato
che `book-digest` (pattern `book-to-skill`) aggiorna per la propria coda di trasformazione in
skill. Un solo registro, non due sistemi di stato paralleli da riconciliare a mano.

## Precondizione

Richiede che `doc-ingest` sia gia' stato eseguito sul file bersaglio: la skill legge il mirror
Markdown gia' in cache e il `.manifest.json` della cartella di cache indicata. Se il file non
risulta nel manifest, la skill si ferma e chiede di far girare prima `tools/doc-ingest.py` sulla
cartella sorgente, invece di leggere il PDF originale essa stessa.

Per i PDF scansionati senza testo nativo (il mirror Markdown esce vuoto o quasi), la precondizione
non basta: vedi la sezione "Verifica visiva per PDF scansionati" piu sotto.

## Quando si invoca

Quando un libro e' stato ingerito e si vuole ricavarne una voce bibliografica citabile per il
`.bib` reale del progetto. Si indica il percorso del file sorgente originale (per risalire
all'hash nel manifest) o direttamente il file Markdown gia' in cache.

## Procedura

1. Risolvere l'hash `sha256` del file dal `.manifest.json` di `doc-ingest` corrispondente alla
   cartella di cache indicata. Se assente, fermarsi (vedi Precondizione).
2. Leggere **solo** le prime pagine del mirror Markdown: frontespizio, verso del frontespizio,
   eventuale colophon, al massimo l'indice. Mai il libro intero: stessa disciplina di disclosure
   progressiva di `doc-ingest`/`book-digest`, applicata qui al solo sottoinsieme "pagine di
   metadati". Se il mirror e' vuoto o troppo corto (PDF scansionato senza OCR riuscito), passare
   alla verifica visiva sotto invece di indovinare i campi dal solo nome del file.
3. Proporre i campi secondo lo schema del paragrafo "Schema campi" e una citekey secondo la
   convenzione descritta li sotto, verificando le collisioni contro il `.bib` reale del progetto e
   contro le citekey gia' presenti nel registro.
4. Presentare la proposta per la conferma "a colophon": chi invoca la skill guarda una volta il
   libro vero (il PDF originale o, se gia' inequivocabile, il frontespizio estratto) e conferma,
   corregge o scarta ogni campo.
5. Aggiornare la voce del registro (vedi "Registro unificato"): stato `verificata` solo se
   confermata dall'utente, altrimenti `da-verificare` (proposta ancora aperta) o `scartata`
   (l'utente ha rifiutato la fonte, per esempio doppione o materiale non citabile).
6. Solo se `bib_status: verificata`, appendere la voce al file `.bib` reale indicato
   dall'utente. Non scrivere mai una voce non confermata.
7. Non toccare mai il campo `skill_status` della voce: e' di proprieta' di `book-digest`, che lo
   aggiorna in modo indipendente quando il libro viene trasformato in skill.
8. Non eseguire mai `git add`, `commit` o `push`: restano manuali dell'utente.

Idempotenza: rilanciare la skill sullo stesso file aggiorna la voce esistente del registro (stesso
hash), non ne crea una seconda. Se l'hash del file e' cambiato rispetto alla voce registrata (nuova
edizione, nuova scansione), la skill lo segnala come potenzialmente obsoleto invece di sovrascrivere
in silenzio.

## Verifica visiva per PDF scansionati

Molti corpus di libri di studio (specie fotocopie o scansioni datate) non hanno un livello di
testo nativo affidabile: il mirror Markdown di `doc-ingest` esce vuoto anche con `--ocr` attivo,
perche' l'OCR su scansioni di bassa qualita' e' spesso inaffidabile o rumoroso. In questo caso il
percorso pratico e' l'estrazione di un piccolo numero di pagine di frontespizio/colophon come
immagini PNG (via `pdftoppm`/Poppler, gia' standardizzata in `tools/extract-titlepages.py` con DPI
e range pagine fissi), lette visivamente pagina per pagina, mai OCR sull'intero corpus. La lettura
visiva diretta della pagina e' piu' economica in token (poche pagine mirate, mai il libro intero) e
piu' affidabile per dati strutturati come anno/editore/ISBN, che vanno citati esattamente o
dichiarati assenti, mai dedotti da OCR rumoroso. Per un buon numero di libri (copie con difetti di
scansione che omettono la pagina di copyright) anche un controllo esteso a diverse pagine puo' non
trovare alcun anno: e' un limite pratico del metodo, non di ricerca insufficiente, e la voce resta
`da-verificare` a tempo indeterminato salvo accesso alla copia fisica.

## Schema campi (.bib)

Solo `@book`, mai altri tipi salvo indicazione esplicita dell'utente:

```bibtex
@book{<citekey>,
  author    = {Cognome, Nome and Cognome2, Nome2},
  title     = {Titolo completo, sottotitolo incluso},
  year      = {YYYY},
  publisher = {Editore},
  address   = {Citta},
  edition   = {solo se dichiarata sul colophon},
  isbn      = {solo se presente},
  note      = {Fonte: <percorso originale> - hash <sha256 troncato>}
}
```

Mai stimare un campo assente dal colophon: si omette, non si inventa. Solo autori/titolo/anno sono
obbligatori; editore, edizione, ISBN si scrivono solo se effettivamente leggibili sul frontespizio.

## Convenzione citekey

`<cognome primo autore><anno>`, tutto minuscolo, senza spazi ne' accenti (traslitterati). In caso
di collisione (stesso cognome, stesso anno, opera diversa), si aggiunge un suffisso `a`/`b`/`c` in
ordine di inserimento. Il controllo di collisione si fa contro il `.bib` reale e contro le citekey
gia' registrate, prima di scrivere.

## Registro unificato

Percorso: `_notes/book-bib-registry.json` (privato, gia' coperto da `/_notes/` in `.gitignore`).
Chiave: lo stesso `sha256` che `doc-ingest` calcola per ogni file. Una voce per libro:

```json
{
  "<sha256>": {
    "source_path": "percorso originale completo del file sorgente",
    "corpus": "etichetta libera della cartella/corpus di provenienza",
    "doc_ingest_cache_dir": "cartella di cache passata a --out",
    "doc_ingest_source_rel": "percorso relativo dentro la cartella sorgente",
    "citekey": "citekey proposta o confermata",
    "bib_status": "da-verificare | verificata | scartata",
    "bib_verified_by": "colophon (sempre, mai un database esterno: i libri non hanno DOI)",
    "bib_verified_date": "YYYY-MM-DD",
    "bib_entry_written": false,
    "bib_file": "percorso del .bib reale a cui e' stata scritta la voce",
    "skill_status": "pending | in_progress | done | skipped | null",
    "skill_slug": null,
    "notes": ""
  }
}
```

Accanto al JSON, rigenerare sempre `_notes/book-bib-registry.md` con `tools/render-bib-registry.py`
(mai editato a mano): una tabella leggibile, colonne citekey / titolo / bib_status / skill_status.

### Caso limite: libro identificato ma non ancora ingerito

Se una fonte e' stata identificata (per esempio da un ISBN o dalla scheda di un rivenditore) ma
non e' ancora stata fisicamente acquisita o scansionata, non esiste un file sorgente da cui
calcolare uno `sha256`. In questo caso si registra comunque una voce, con una chiave alternativa
`manual-<identificatore>` (per esempio `manual-isbn-<ISBN>`) al posto dello sha256, e i campi
`source_path`, `doc_ingest_cache_dir`, `doc_ingest_source_rel` a `null`. Il campo `skill_status` si
lascia a `null` anziche' `pending`: non c'e' ancora nulla da ingerire con `doc-ingest`, quindi la
voce non e' in coda per `book-digest`. `bib_status` resta `da-verificare` finche' non si verifica
il colophon fisico; ogni campo desunto da una fonte secondaria (per esempio una pagina del
rivenditore o una recensione) va annotato come tale nelle `notes`, mai promosso a fatto.

## Rapporto con gli altri pacchetti

`doc-ingest` e' a monte: fornisce testo e manifest, non si tocca. `book-digest` (pattern
`book-to-skill`) e' indipendente: legge la stessa fonte per un digest concettuale, non tocca mai la
bibliografia, e coordina solo il proprio campo `skill_status` nello stesso registro.
`academic-researcher` non si instanzia per questo scopo: la sua skill `citation-tracker` verifica
contro Semantic Scholar/OpenAlex/Crossref, un metodo non applicabile a libri senza DOI; solo il
vocabolario a tre stati (verificata/da-verificare/scartata) e' ripreso qui, con una verifica umana
da colophon al posto della verifica da database.

## Vincoli

Densita' sopra completezza nella proposta di ogni campo. Mai testo grezzo ne' pagine intere in
output: solo i campi estratti. Mai scrivere nel `.bib` reale senza conferma umana esplicita. Mai
inventare un campo assente. Non eseguire `git add`, `commit` o `push`.
