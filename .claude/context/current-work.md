---
generated-from-commit: 8a47d3039a88d6258bc44197ff3ea5189dd0f5b9
generated-from-branch: main
generated-date: 2026-06-15
covers-paths:
  - src/**
  - pyproject.toml
  - docker-compose.yml
  - Dockerfile
  - .github/**
last-verified-commit: 8a47d3039a88d6258bc44197ff3ea5189dd0f5b9
stato: in sviluppo — step 6/23 completato
---

# Lavoro in corso

## Stato

Il progetto è greenfield: nessun file sorgente ancora scritto. La specifica completa è nei
file `primo-prompt/` (letti e distillati nelle schede di contesto). Il prossimo passo è
l'implementazione nell'ordine definito.

## Ordine di implementazione

L'ordine è prescritto e va rispettato: ogni step deve compilare e passare i test prima di
procedere al successivo.

```
Step  1: pyproject.toml — uv, Python 3.12, tutte le dipendenze (prod + dev)          ✓ 795f243
Step  2: .env.example + src/trading/config.py — Pydantic Settings                    ✓ 795f243
Step  3: src/trading/db/models.py — Trade, Position, Signal, DailyPnL                ✓ 795f243
Step  4: src/trading/db/migrations/ — Alembic setup (alembic.ini, env.py, prima migration) ✓ 795f243
Step  5: src/trading/db/repository.py — tutte le operazioni CRUD                     ✓ 795f243
Step  6: src/trading/broker/client.py — IBClient, retry, disconnect handler, fill handler  ✓ prossimo commit
Step  7: src/trading/broker/market_data.py — yfinance warmup + real-time loop aggregazione 5s→5min
Step  8: src/trading/broker/orders.py — get_contract() EU/US, LimitOrder + GTC StopOrder
Step  9: src/trading/features/pipeline.py — pandas-ta-classic strategy
Step 10: src/trading/strategy/interfaces.py — 6 ABC + dataclass RawSignal/AllocatedSignal
Step 11: src/trading/strategy/composer.py + registry.py
Step 12: src/trading/strategy/implementations/ma_crossover.py — DividendFreeFilter incluso
Step 13: src/trading/risk/manager.py + risk/circuit_breaker.py
Step 14: src/trading/scheduler/jobs.py — dual session EU CET + US ET
Step 15: src/trading/notifications/telegram.py
Step 16: src/trading/monitoring/healthcheck.py — FastAPI, :8080/health
Step 17: src/trading/reporting/flex_query.py — IBKR Flex Web Service
Step 18: src/trading/main.py — TradingBot, integrazione completa, signal handlers
Step 19: docker-compose.yml — gnzsnz/ib-gateway-docker + bot + postgres + grafana
Step 20: Dockerfile — uv-based (FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim)
Step 21: .github/workflows/deploy.yml — test → SSH deploy
Step 22: tests/unit/ — test_risk_manager, test_position_sizer, test_signal_generator
Step 23: scripts/ — emergency_flatten.py, check_positions.py, export_tax_report.py
```

## Definition of done (per ogni step)

- [ ] File scritto e completo (no placeholder)
- [ ] Nessun errore di import / syntax error
- [ ] `uv run ruff check src/` passa
- [ ] Per gli step 1-5 (infra): `uv run alembic upgrade head` funziona su DB locale
- [ ] Per gli step 6-18 (core): unit test dell'area passa
- [ ] Per gli step 19-21 (infra): `docker compose up -d` avvia lo stack senza errori

## Domande aperte

MCP servers (da CLAUDE.md in primo-prompt, §Configurazione MCP): GitHub MCP, PostgreSQL MCP,
Context7 e Sequential Thinking sono raccomandati. Non configurati in fase di init — aggiungere
prima dell'implementazione degli step core (dopo lo Step 5) per avere accesso a documentazione
aggiornata di ib_async, SQLAlchemy 2.0, APScheduler durante lo sviluppo.

## Riconciliazione

Ultima verifica: 2026-06-15 al commit 8a47d30. Scheda scritta dalla specifica in primo-prompt/
— da aggiornare con i file sorgente effettivi man mano che vengono scritti.
