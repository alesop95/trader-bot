# Pacchetto opzionale: ambiente LaTeX

> Scheletro riusabile dell'ambiente di build LaTeX descritto nella sezione 13 di
> `PROJECT-SYSTEM.md`. Si istanzia solo nei progetti che producono un documento LaTeX. Modello
> manifesto + ambiente-esterno: si versiona la fonte riproducibile (manifesto e script), si ignora
> la distribuzione TeX materializzata (TinyTeX), installata user-local e condivisa fra i progetti.

## Mappa di istanziazione

```
templates/latex/scripts/setup-tex.ps1   ->  <radice>/scripts/setup-tex.ps1   (tracciato)
templates/latex/scripts/setup-tex.sh    ->  <radice>/scripts/setup-tex.sh    (tracciato)
templates/latex/scripts/build.ps1       ->  <radice>/scripts/build.ps1       (tracciato)
templates/latex/scripts/build.sh        ->  <radice>/scripts/build.sh        (tracciato)
templates/latex/tex-packages.txt        ->  <radice>/tex-packages.txt        (tracciato, da adattare)
templates/latex/latexmkrc               ->  <radice>/.latexmkrc              (tracciato)
templates/latex/skills/latex-build/     ->  <radice>/.claude/skills/latex-build/   (tracciato)
```

Aggiungere inoltre al `.gitignore` del progetto le esclusioni degli artefatti LaTeX (PDF e
ausiliari): vedi il blocco LaTeX in `templates/gitignore.snippet`.

## Dopo l'istanziazione

Adattare `tex-packages.txt` al preambolo reale del proprio `.tex` (aggiungere i pacchetti delle
`\usepackage` non coperti dalla base). Poi eseguire `scripts/setup-tex.{ps1,sh}` per installare
TinyTeX e i pacchetti, e `scripts/build.{ps1,sh}` per compilare. La procedura e' incapsulata nella
skill `latex-build`. L'engine e' pdflatex, fissato in `.latexmkrc`: per documenti che richiedono
fontspec/unicode-math passare a lualatex/xelatex modificando `.latexmkrc` e il manifesto.

L'auto-rilevamento del file principale (`build.ps1`/`.sh` senza argomenti) cerca un solo `.tex`
nella radice del progetto: se il documento vive altrove, per esempio `docs/relazione.tex`, va
passato esplicitamente con `-Main docs\relazione.tex` (Windows) o `--main docs/relazione.tex`
(Linux/macOS), path relativo alla radice. Verificato dal vivo (pilota 2026-07-02): la build passa
senza altre modifiche.

Un secondo difetto, trovato eseguendo davvero lo script invece di limitarsi a `pdflatex` a mano
(pilota 2026-07-03): quando `-Main`/`--main` punta a un file in una sottocartella, `latexmk`
invocato senza `-cd` esegue `pdflatex` restando nella radice del progetto, e `pdflatex` scrive
per default il PDF e tutti gli ausiliari (`.aux`, `.log`, `.fls`, `.synctex.gz`,
`.fdb_latexmk`) nella directory corrente, non accanto al sorgente: la build riusciva, ma
sporcava la radice del progetto invece di `docs/`, e il messaggio finale dello script
dichiarava una posizione (`docs/diploma.pdf`) diversa da quella reale. Corretto aggiungendo
`-cd` a ogni invocazione di `latexmk` in `build.ps1` e `build.sh`, che gli fa cambiare
directory di lavoro in quella del file principale prima di compilare: verificato dal vivo, ora
il PDF e gli ausiliari finiscono correttamente accanto al `.tex` sorgente.

## Non versionato

La distribuzione TinyTeX (default `%APPDATA%\TinyTeX` su Windows, `~/.TinyTeX` su Unix) e il PDF e
gli ausiliari di compilazione sono derivati: restano fuori da git.

## Attriti osservati dal vivo (pilota 2026-07-02)

Su un TinyTeX gia' installato ma non aggiornato di recente, `tlmgr install <pacchetto>` puo'
rifiutarsi con "tlmgr itself needs to be updated": va lanciato prima `tlmgr update --self`, che
puo' restare silenzioso per una manciata di secondi prima di completare, poi si ripete il comando
di installazione. Inoltre, un documento che unisce `psnfss`/`times` a `\texttt` su un preambolo
`fontenc` T1 fallisce con "Font T1/pcr/.../not loadable: Metric (TFM) file not found" se manca il
pacchetto `courier`: TinyTeX, a differenza di una TeX Live completa, non lo installa di default
insieme a `psnfss`. Il manifesto base in `tex-packages.txt` documenta ora questa coppia.
