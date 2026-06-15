---
description: >
  Aggiorna il contesto di Claude dopo un git pull o merge. Mostra cosa è
  cambiato rispetto all'ultima sessione. Invocare dopo aver eseguito git pull.
disable-model-invocation: true
---

## Modifiche introdotte dall'ultimo pull

### Commit recenti del branch
!`git log --oneline -10`

### File cambiati negli ultimi commit
!`git log --name-status -5 --format="%h %s"`

### CLAUDE.md è stato modificato di recente?
!`git log --oneline -5 -- CLAUDE.md .claude/`

## Istruzioni

1. Riepiloga le modifiche entrate nel branch corrente
2. Identifica se ci sono cambiamenti a CLAUDE.md o alla cartella `.claude/`
   (indicare esplicitamente se il contesto di progetto è stato aggiornato)
3. Segnala breaking changes nei file di configurazione o nei contratti API
4. Suggerisci se è necessario aggiornare CLAUDE.md con nuove informazioni