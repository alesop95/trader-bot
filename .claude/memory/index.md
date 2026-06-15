# Snapshot di sincronizzazione

> Da leggere per primo a inizio sessione. Fotografa lo stato del progetto al commit di
> riferimento e mappa ogni scheda al suo stato di verifica. È la fonte di verità su cosa è fatto,
> non le spunte del diario.

## Stato

```
Branch attivo:         main
Commit di riferimento: 8a47d30
Data snapshot:         2026-06-15
```

## Stato di verifica delle schede

| Scheda | last-verified | Stato |
|---|---|---|
| STACK.md | 8a47d30 | aggiornata |
| design-and-security.md | 8a47d30 | aggiornata |
| deployment.md | 8a47d30 | aggiornata |
| dev-testing.md | 8a47d30 | aggiornata |
| current-work.md | 8a47d30 | aggiornata |
| roadmap.md | 8a47d30 | aggiornata |

## Punto di ripresa

Sistema inizializzato, ancorato al commit 8a47d30 e schede populate dalla specifica in
`primo-prompt/`. Nessun file sorgente ancora scritto (greenfield). Prossimo passo:
**Step 1** — scrivere `pyproject.toml` con uv, Python 3.12 e tutte le dipendenze.
Ordine di implementazione completo in `context/current-work.md` (23 step).

Prima di iniziare gli step core (dopo Step 5), configurare i MCP servers (GitHub MCP,
PostgreSQL MCP, Context7, Sequential Thinking) — vedi `CLAUDE.md` §Promemoria MCP.
