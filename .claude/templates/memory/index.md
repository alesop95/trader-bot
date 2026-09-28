# Snapshot di sincronizzazione

> Da leggere per primo a inizio sessione. Fotografa lo stato del progetto al commit di riferimento e mappa ogni scheda al suo stato di verifica. È la fonte di verità su cosa è fatto, non le spunte del diario. Vale per la branch dichiarata qui sotto e non per il progetto: se il progetto usa più alberi di lavoro e questa non è la branch più avanti, la memoria valida è quella dell'albero autorevole indicato (norma `.claude/skills/alberi-di-lavoro/RIFERIMENTO.md`).

## Stato

```
Branch attivo:        <branch>
Commit di riferimento: <hash del commit corrente>
Data snapshot:        <YYYY-MM-DD>
Albero autorevole:    <percorso assoluto, o "unico" se il progetto ha un solo albero>
Ambienti:             <solo con una branch per ambiente: commit di produzione e di staging sul remoto, e divergenza del ramo corrente, dopo un fetch>
```

## Stato di verifica delle schede

| Scheda | last-verified | Stato |
|---|---|---|
| STACK.md | <hash> | <aggiornata / stale / obsoleta> |
| design-and-security.md | <hash> | <stato> |
| deployment.md | <hash> | <stato> |
| dev-testing.md | <hash> | <stato> |
| current-work.md | <hash> | <stato> |
| roadmap.md | <hash> | <stato> |

## Punto di ripresa

<una riga di prossima azione concreta che dice da dove ricominciare>
