---
description: >
  Analizza lo stato corrente della repository: branch attivo, commit recenti,
  file modificati, differenze non committate. Usare quando si vuole un
  riepilogo aggiornato della repo o prima di iniziare una sessione di sviluppo.
---

## Stato Git corrente

### Branch e commit recenti
!`git log --oneline -20`

### Branch corrente
!`git branch --show-current`

### File modificati (non committati)
!`git status --short`

### Diff non committato (riepilogo per file)
!`git diff --stat HEAD -- . ":(exclude)*.lock" ":(exclude)dist/"`

### Tag e versioni
!`git tag --sort=-version:refname`

## Istruzioni

Il diff sopra è un riepilogo per file (`--stat`); per il dettaglio riga-per-riga di un file
specifico eseguire su richiesta `git diff HEAD -- <percorso>`.

Sulla base dei dati sopra:
1. Descrivere il lavoro in corso (branch + commit recenti)
2. Identificare file in stato modificato che potrebbero richiedere attenzione
3. Segnalare eventuali conflitti o stato anomalo
4. Suggerire il prossimo step coerente con la storia dei commit