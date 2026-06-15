# Snapshot di sincronizzazione

> Da leggere per primo a inizio sessione. Fotografa lo stato del progetto al commit di
> riferimento e mappa ogni scheda al suo stato di verifica. È la fonte di verità su cosa è fatto,
> non le spunte del diario.

## Stato

```
Branch attivo:         main
Commit di riferimento: PENDING-FIRST-COMMIT
Data snapshot:         2026-06-15
```

## Stato di verifica delle schede

| Scheda | last-verified | Stato |
|---|---|---|
| STACK.md | PENDING-FIRST-COMMIT | aggiornata |
| design-and-security.md | PENDING-FIRST-COMMIT | aggiornata |
| deployment.md | PENDING-FIRST-COMMIT | aggiornata |
| dev-testing.md | PENDING-FIRST-COMMIT | aggiornata |
| current-work.md | PENDING-FIRST-COMMIT | aggiornata |
| roadmap.md | PENDING-FIRST-COMMIT | aggiornata |

## Punto di ripresa

Primo commit non ancora eseguito. Dopo il commit, eseguire la skill `sync-context` per
sostituire ogni PENDING-FIRST-COMMIT con l'hash reale di HEAD. Poi iniziare a popolare
le schede di context/ leggendo il codice.
