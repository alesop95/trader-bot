---
description: >
  Verifica e sincronizza le schede tecniche in .claude/context/ con lo stato corrente del
  codice. Confronta il last-verified-commit di ogni scheda con HEAD del branch, individua i
  file cambiati nelle covers-paths, e propone delta update mirati senza rigenerare i documenti.
  Usare a inizio sessione, dopo modifiche significative al codice, o dopo un git pull.
---

## Stato attuale del contesto

### Commit HEAD corrente
!`git log -1 --format="%H  %h  %ad  %s" --date=short`

### Branch corrente
!`git branch --show-current`

### Commit recenti
!`git log --oneline --no-decorate -10`

### Snapshot e frontmatter delle schede
Leggere con lo strumento Read: prima `.claude/memory/index.md` (snapshot), poi i file
`.claude/context/*.md` (elencabili con Glob), estraendo dal frontmatter di ciascuna scheda
`last-verified-commit` e `covers-paths`. Questi contenuti non si iniettano via comando di shell, per
restare portabili tra Windows e Unix e per non dipendere da `cat`, `sed` o cicli `for` (che il
controllo permessi blocca).

## Istruzioni operative

Le schede tecniche tracciate vivono in `.claude/context/` (ad esempio `STACK.md`,
`design-and-security.md`, `deployment.md`, `dev-testing.md`, `current-work.md`) e ognuna porta
in testa un frontmatter con `covers-paths` e `last-verified-commit`. La skill scopre le schede
da quella cartella, non da una lista fissa.

### 0. Primo ancoraggio dopo un init greenfield

Prima del confronto di drift, gestire il caso del progetto appena inizializzato. Se una scheda
porta `generated-from-commit` o `last-verified-commit` uguale al segnaposto `PENDING-FIRST-COMMIT`,
significa che è stata creata in greenfield prima che esistesse un commit. In questo caso, quando
il repository ha ora almeno un commit (`git rev-parse HEAD` riesce), sostituire il segnaposto con
l'hash di `HEAD` in tutte le schede che lo portano, impostando sia `generated-from-commit` sia
`last-verified-commit` a `HEAD`, e aggiornare il commit di riferimento in `memory/index.md` con lo
stesso hash. Appendere una sola voce in `memory/progress.md` che registra l'ancoraggio iniziale,
con data, hash e l'elenco delle schede ancorate. Da quel momento il confronto di drift dei passi
successivi vale normalmente. Se invece il repository non ha ancora alcun commit, segnalare che
l'ancoraggio è rimandato al primo commit e non procedere al confronto.

### 1. Per ogni scheda, determinare lo stato

Per ciascuna scheda presente in `.claude/context/`:

- Leggere `last-verified-commit` e `covers-paths` dal frontmatter (con `Read` se non già visibile sopra).
- Eseguire `git diff --name-only <last-verified-commit>..HEAD -- <covers-paths>`, usando i `covers-paths` della scheda come argomenti dopo il `--`.
- Classificare:
  - aggiornata: nessun file coperto è cambiato.
  - stale: almeno un file coperto è cambiato; mostrare la lista dei file all'utente.
  - obsoleta: i cambi includono rename o delete di moduli interi, oppure la scheda cita simboli o file che non esistono più (verificare con una ricerca dei nomi citati).

### 2. Mostrare un report all'utente

Formato esempio:

```
## Sync report (HEAD = abc1234 @ 2026-06-15)

| Scheda | last-verified | Stato | File toccati nelle aree coperte |
|---|---|---|---|
| STACK.md | cdcf031 | aggiornata |  |
| deployment.md | cdcf031 | stale | infra/compose.yml |
| dev-testing.md | cdcf031 | aggiornata |  |
```

### 3. Per ogni scheda stale, proporre il delta update

Non rigenerare il file. Leggere `git diff <last-verified-commit>..HEAD -- <file_toccato>` per
capire la modifica reale, individuare la sola sezione della scheda che descrive l'area cambiata,
e proporre un edit chirurgico con `Edit` della sola sezione impattata. Non rifare la struttura
della scheda.

### 4. Dopo l'edit, aggiornare frontmatter e meta-stato

Per ogni scheda effettivamente aggiornata: bumpare `last-verified-commit` al nuovo HEAD nel
frontmatter, aggiornare la riga corrispondente nella tabella di stato in `.claude/memory/index.md`,
e appendere una voce in `.claude/memory/progress.md` con data, commit, file toccati e motivo, in
ordine cronologico inverso.

### 5. Schede aggiornate

Anche se non cambiate, su conferma dell'utente bumpare `last-verified-commit` a HEAD come
checkpoint, così il prossimo confronto parte da qui e non accumula rumore. Chiedere: "Le schede
aggiornate sono ancora valide al commit attuale? Bumpare il last-verified?"

### 6. Caso obsoleto

Non bumpare in automatico. Avvisare che serve una rilettura più approfondita della sezione
impattata, e proporre se aggiornarla mantenendo la struttura, marcarla come superata creando una
nuova sezione di stato corrente, oppure rigenerarla da zero come ultimo ricorso.

## Note

- Non eseguire mai `git pull` o altre operazioni di scrittura su git: la skill legge e propone soltanto.
- Se una scheda porta ancora `PENDING-FIRST-COMMIT`, eseguire prima il passo 0 di primo ancoraggio: quel segnaposto va sostituito con l'hash di HEAD al primo commit, non trattato come drift.
- Se HEAD coincide con tutti i `last-verified-commit`, rispondere con un singolo messaggio di allineamento, senza azioni.
- Se il branch corrente è diverso dal `generated-from-branch` di una scheda, avvisare l'utente che il confronto può risultare rumoroso.
