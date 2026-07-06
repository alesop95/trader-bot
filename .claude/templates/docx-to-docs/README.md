# Pacchetto docx-to-docs

> Pacchetto opzionale del sistema di progetto. Converte un documento `.docx` voluminoso in un
> albero di documentazione Markdown navigabile e versionato: un file per sezione, `README.md`
> indice generati per ogni cartella che linkano ai figli, e un hub `DEVELOPMENT.md` come punto di
> ingresso unico. La conversione e' deterministica e ri-eseguibile, con livelli curati che
> sopravvivono alla rigenerazione. Si offre al gate dei pacchetti (vedi ../PACKAGES.md) ai
> progetti che partono da un `.docx` o da un corpus scritto a mano da trasformare in
> documentazione tecnica navigabile. Non si propone dove il progetto non ha un documento sorgente
> di questo tipo, o dove basta l'ingestione a fette gia' descritta nel README di radice.

## Rapporto con l'ingestione .docx del README

Sono due usi distinti dello stesso formato. L'ingestione descritta nel README di radice serve a
caricare in contesto solo le porzioni utili di un documento voluminoso, senza versionare nulla.
Questo pacchetto fa l'opposto e complementare: produce una volta per tutte un albero `docs/`
versionato, che diventa la documentazione tecnica navigabile del progetto, mentre il `.docx`
sorgente resta locale e ignorato come fonte di rigenerazione.

## Mappa di istanziazione

L'istanziazione copia il convertitore e i suoi sidecar nella cartella `tools/` del progetto, e
predispone la cartella `docs/` come destinazione dell'output.

```
templates/docx-to-docs/docx-to-md.py            ->  <radice>/tools/docx-to-md.py           (tracciato)
templates/docx-to-docs/annotations.example.json ->  <radice>/tools/annotations.json        (tracciato, da adattare)
(output generato dal convertitore)                  <radice>/docs/                          (tracciato)
(sidecar di redazione, se serve)                    <radice>/tools/redactions.json          (locale, ignorato)
```

## Come funziona

Il convertitore itera il corpo del documento in ordine reale, cosi' tabelle e immagini restano
nella posizione giusta, e spezza il testo in file al livello di titolo scelto (`SPLIT_LEVEL`, di
default H5): ogni sezione diventa un file, le sezioni piu' profonde restano come sotto-titoli
interni, e le sezioni contenitore diventano cartelle con un `README.md` indice generato che elenca
e linka i figli. I titoli di primo livello danno le cartelle di area; con `MACRO_NAMES` si possono
fissare nomi di cartella stabili, altrimenti derivano dallo slug del titolo. Le immagini si
estraggono in cartelle `assets/` accanto ai documenti e non si versionano.

La verifica di completezza e' integrata: al termine lo script confronta titoli, tabelle e immagini
con il sorgente e scrive un `_CONVERSION-REPORT.md` con i conteggi, le sezioni marcate dall'autore,
la mappa immagini e le trasformazioni applicate.

## I livelli curati che sopravvivono alla rigenerazione

Il valore del pattern e' che le correzioni curate non vanno perse quando si rigenera. Tre livelli,
tutti deterministici e tracciati nel report.

Le annotazioni (`annotations.json`) iniettano un banner subito dopo il titolo di un file preciso,
per esempio una nota LEGACY su una sezione superata o un rimando a `DEVELOPMENT.md` dalla home. La
chiave e' il percorso del file relativo alla cartella `docs/`; il valore e' il banner Markdown.

Le redazioni (`redactions.json`, tenuto locale) applicano sostituzioni regex al testo finale per
neutralizzare riferimenti non desiderati preservando il resto, utili quando il sorgente contiene
materiale sensibile o fuori policy che non deve finire in un repository pubblico.

La pulizia (`--clean`) rimuove il rumore ereditato dal sorgente: emoji, trattini lunghi normalizzati
in trattini brevi, righe segnaposto composte da una sola lettera ripetuta. E' la controparte attiva
della regola `interaction-style` e del pacchetto `humanizer`, applicata in fase di generazione.

## Uso

Dipendenza: `python-docx`. Comando tipico, ri-eseguibile e idempotente:

```powershell
python tools/docx-to-md.py "sorgente.docx" --out docs --clean
```

Senza `--clean` la conversione e' strettamente verbatim; con `--clean` si toglie il rumore. Il
`.docx` sorgente e l'eventuale `redactions.json` restano locali e ignorati da git; l'albero `docs/`
e il convertitore si versionano. Come punto di ingresso della documentazione conviene scrivere a
mano un `docs/DEVELOPMENT.md` che mappi aree, runbook e strumenti, e collegarlo dalla home con
un'annotazione.

## Crediti

Costruito su `python-docx` per la lettura del formato Word. Implementazione di riferimento nel
caso studio del progetto di personalizzazione Sony Xperia (vedi ../../CASE-STUDIES.md).
