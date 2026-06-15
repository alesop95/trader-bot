---
name: latex-build
description: >
  Bootstrap e compilazione dell'ambiente LaTeX del progetto (TinyTeX user-local),
  guidati dal manifesto tex-packages.txt e dagli script in scripts/. Usare per
  preparare l'ambiente la prima volta (o dopo aver aggiunto pacchetti al manifesto)
  e per compilare il documento in modo riproducibile con l'engine pdflatex fissato
  in .latexmkrc. Riusabile su qualsiasi progetto LaTeX che adotti questo stesso layout.
disable-model-invocation: true
---

## Premessa

Questa skill non duplica logica: si appoggia ai file versionati del progetto. La fonte di verita'
dell'ambiente e' il manifesto `tex-packages.txt` (sezione 13 di `.claude/PROJECT-SYSTEM.md`); la
distribuzione TeX (TinyTeX) e' invece esterna al repository, installata user-local e condivisa fra
i progetti, quindi non versionata. Gli script invocano i binari dell'ambiente per percorso, senza
attivazione interattiva, cosi' il comportamento e' identico in locale e in CI.

Gli script non eseguono operazioni git: preparano e compilano soltanto. Commit e push restano
manuali dell'utente.

## Quando usarla

Bootstrap dell'ambiente la prima volta, oppure dopo aver aggiunto una `\usepackage` nel `.tex` e la
relativa voce nel manifesto. Compilazione del documento per ottenere il PDF (artefatto derivato,
ignorato da git).

## Procedura

### 1. Preparare l'ambiente dal manifesto

Su Windows (Windows PowerShell 5.1, gia' presente di serie; con PowerShell 7+ funziona anche `pwsh`):

```
powershell -ExecutionPolicy Bypass -File scripts\setup-tex.ps1
```

Su Unix/macOS:

```
sh scripts/setup-tex.sh
```

Lo script localizza TinyTeX (default user-local: `%APPDATA%\TinyTeX` su Windows, `~/.TinyTeX` su
Unix); se assente lo installa scaricando l'installer ufficiale; poi esegue `tlmgr install` dei
pacchetti elencati nel manifesto e verifica con una compilazione minima. La prima esecuzione
scarica diversi pacchetti, quindi richiede rete e qualche minuto. Flag utili: `-Reinstall` /
`--reinstall` per ricreare da zero, `-TexDir` / `--tex-dir` per forzare la cartella,
`-SkipPackages` / `--skip-packages` per il solo bootstrap della distribuzione.

### 2. Compilare il documento

Su Windows:

```
powershell -ExecutionPolicy Bypass -File scripts\build.ps1
```

Su Unix/macOS:

```
sh scripts/build.sh
```

Se nella radice c'e' un solo `.tex` viene usato quello; altrimenti passare `-Main` / `--main
<file.tex>`. La pulizia degli ausiliari e' `-Clean` / `--clean` (lascia il PDF) o `-CleanAll` /
`--clean-all` (rimuove anche il PDF).

### 3. Aggiungere un pacchetto

Quando il documento introduce un nuovo pacchetto, aggiungerne il nome `tlmgr` al manifesto
`tex-packages.txt` (una voce per riga), poi rieseguire lo script di setup: installa solo cio' che
manca. Il manifesto resta la fonte riproducibile dell'ambiente.

## Note di manutenzione

Se la build fallisce per un pacchetto mancante, il messaggio di pdflatex indica il file `.sty`
assente: cercare il pacchetto tlmgr che lo fornisce (`tlmgr search --file <nome>.sty`), aggiungerlo
al manifesto e rilanciare il setup. Non installare pacchetti a mano senza registrarli nel
manifesto, altrimenti l'ambiente non resta riproducibile su un'altra macchina.
