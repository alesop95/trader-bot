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

## Non versionato

La distribuzione TinyTeX (default `%APPDATA%\TinyTeX` su Windows, `~/.TinyTeX` su Unix) e il PDF e
gli ausiliari di compilazione sono derivati: restano fuori da git.
