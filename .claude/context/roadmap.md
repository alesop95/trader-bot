---
generated-from-commit: 8a47d3039a88d6258bc44197ff3ea5189dd0f5b9
generated-from-branch: main
generated-date: 2026-06-15
covers-paths: []
last-verified-commit: 8a47d3039a88d6258bc44197ff3ea5189dd0f5b9
---

# Roadmap

## Direzione

Sistema di trading algoritmico automatizzato su Interactive Brokers per investitore italiano
(regime dichiarativo). Universo: azioni growth senza dividendi su US (NYSE/NASDAQ) + EU
(XETRA + Euronext Amsterdam). Strategia di partenza: MA Crossover con 6 interfacce
componibili. Obiettivo: operativo in paper (Fase 0) entro la prima sessione di sviluppo,
live (Fase 1) dopo 2 settimane di paper positivo.

## Priorità

1. **Step 1–5 (infrastruttura dati)** — pyproject.toml, config, models, Alembic, repository.
   È il fondamento: senza DB e config non si può testare nient'altro.

2. **Step 6–9 (connessione broker)** — broker layer (IBClient, MarketData, Orders) +
   features pipeline. Richiede IB Gateway attivo in paper su macchina di sviluppo o VM.

3. **Step 10–13 (logica di trading)** — le 6 interfacce, composer, registry, strategia MA
   Crossover, risk manager, circuit breaker. Il cuore del sistema.

4. **Step 14–18 (scheduler + notifiche + main)** — dual session EU + US, Telegram, health
   check, reporting fiscale, entrypoint completo.

5. **Step 19–21 (containerizzazione + CI/CD)** — Docker Compose con
   `gnzsnz/ib-gateway-docker`, Dockerfile uv-based, GitHub Actions deploy.

6. **Step 22–23 (test + script)** — unit test, script di emergenza, export fiscale.

7. **MCP servers** — configurare prima degli step core (dopo Step 5): GitHub MCP,
   PostgreSQL MCP, Context7 (documenta ib_async/SQLAlchemy/APScheduler), Sequential Thinking.
   Vedi `CLAUDE.md` sezione Promemoria MCP.

8. **Paper trading 2 settimane** — prerequisito obbligatorio prima del go-live Fase 1.

9. **Scala Vultr NJ** — quando le commissioni generate superano il costo infrastrutturale.

## Idee e ipotesi da verificare

La PDT rule (Pattern Day Trader, $25.000 minimum equity) è stata eliminata dalla SEC
il 4 giugno 2026 — per clienti IBKR Ireland/Central Europe (account italiano) non era
mai stata applicata, ma vale la pena confermare lo status dell'account prima del go-live.

Per la gestione valuta (investitore EUR, azioni USD): verificare se conviene IDA
(Integrated Data Access, auto FX conversion) o gestione manuale del saldo USD. Il Trade
model dovrebbe registrare `eur_usd_rate` e `pnl_eur` per semplificare la dichiarazione.

W-8BEN: compilare su IBKR Account Management prima del go-live — riduce la ritenuta
dividendi USA dal 30% al 15% (irrilevante per il nostro universo senza dividendi, ma
buona pratica se l'universo cambia in futuro).

Estrategia alternativa alla MA Crossover: considerare mean reversion o momentum puro
dopo aver validato la MA Crossover in paper. Il `StrategyRegistry` supporta nativamente
più strategie in parallelo con allocazione capitale percentuale.
