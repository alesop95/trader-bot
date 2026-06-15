---
generated-from-commit: 8a47d3039a88d6258bc44197ff3ea5189dd0f5b9
generated-from-branch: main
generated-date: 2026-06-15
covers-paths:
  - pyproject.toml
  - src/trading/**
  - Dockerfile
  - docker-compose.yml
last-verified-commit: 8a47d3039a88d6258bc44197ff3ea5189dd0f5b9
---

# Stack applicativo

## Stack e runtime

Linguaggio Python 3.12 (non 3.11). Package manager `uv` (astral-sh), che gestisce Python
version pinning, virtual environment e lockfile in un unico tool, 10-100x più veloce di pip.
File `uv.lock` versionato; nessun `requirements.txt`.

| Layer | Tecnologia | Versione minima |
|---|---|---|
| Python | 3.12 | 3.12.x (via `uv python pin 3.12`) |
| Package manager | uv | latest |
| IBKR API wrapper | ib-async | ≥1.0 (`pip install ib-async`) |
| IB Gateway containerizzato | gnzsnz/ib-gateway-docker | stable (include IBC + Xvfb) |
| Database | PostgreSQL | 15+ con asyncpg driver |
| ORM | SQLAlchemy | ≥2.0 async mode |
| Migrations | Alembic | ≥1.13 |
| Indicatori tecnici | pandas-ta-classic | latest — 252 indicatori, uso `df.ta.rsi()` |
| Warmup storico | yfinance | latest — no pacing limits IBKR |
| Backtesting | vectorbt (OSS) | ≥0.26 — dev dependency |
| Calendari mercato | exchange-calendars | ≥4.5 — NYSE + XETRA + Euronext |
| Scheduler | APScheduler | ≥3.10 — AsyncIOScheduler |
| Logging | Loguru | latest — structured, rotation automatica |
| Alerting | python-telegram-bot | ≥20 |
| Health check HTTP | FastAPI + uvicorn | ≥0.115 / ≥0.30 — porta :8080 |
| Monitoring | Prometheus + Grafana | latest |
| Linting / format | ruff | latest — line-length 100, target py312 |
| Type check | mypy | ≥1.10, strict=false |
| Testing | pytest + pytest-asyncio | ≥8.0 / ≥0.23 |
| Containerizzazione | Docker Compose v2 | nessun campo `version:` (deprecato) |
| CI/CD | GitHub Actions | deploy via SSH su VM cloud |

## Alternative deliberatamente escluse

`pip` / `pyenv` / `venv` sostituiti da `uv` — medesima interfaccia, molto più veloce e senza
dipendenze di sistema per il Python version management.

`pandas-ta` (originale) sostituito da `pandas-ta-classic` — fork mantenuto, compatibile con uv,
nessuna dipendenza C che blocca la build su ARM.

`aiohttp` per health check sostituito da `FastAPI + uvicorn` — più robusto e testabile.

Market order mai usati — sempre `LimitOrder` con prezzo aggressivo (last ±0.1%) per evitare
slippage. Regola non negoziabile.

`IBKR Pro` obbligatorio (no IBKR Lite, che vende order flow PFOF e non ha smart routing).

## Flussi di codice e ruolo architetturale dei file

```
src/trading/
├── main.py              entrypoint, TradingBot class, signal handlers SIGTERM/SIGINT
├── config.py            Pydantic Settings da env vars / .env, unico source of truth config
├── broker/
│   ├── client.py        IBClient — connessione ib_async, retry, disconnect handler, fill event
│   ├── market_data.py   MarketDataManager — yfinance warmup + stream 5s → aggregazione 5min
│   └── orders.py        OrderManager — get_contract() EU/US, LimitOrder + GTC StopOrder
├── strategy/
│   ├── interfaces.py    6 ABC: IUniverseFilter, ISignalGenerator, IPositionSizer,
│   │                    IPortfolioAllocator, IExecutionAlgo, IExitLogic + dataclass RawSignal
│   ├── composer.py      StrategyComposer — collante delle 6 interfacce, nessuna logica trading
│   ├── registry.py      StrategyRegistry — più strategie in parallelo con allocazione capitale %
│   └── implementations/
│       └── ma_crossover.py  esempio completo con DividendFreeFilter, EMACrossoverSignal,
│                            FixedFractionalSizer, MaxPositionsAllocator,
│                            AggressiveLimitExecution, TimeAndTrailingExit
├── features/
│   └── pipeline.py      compute_features() — pandas-ta-classic strategy, vol_ratio, gap_pct
├── risk/
│   ├── manager.py       RiskManager.validate() — gate obbligatorio prima di ogni ordine
│   └── circuit_breaker.py CircuitBreaker — ferma bot su daily loss >5% o IB Gateway non risponde
├── db/
│   ├── models.py        Trade, Position, Signal, DailyPnL — SQLAlchemy 2.0 declarative
│   ├── repository.py    Repository pattern — unico punto di accesso DB, nessuna query altrove
│   └── migrations/      Alembic env.py + versions/ — URL da env var in env.py
├── scheduler/
│   └── jobs.py          dual session: EU CET (09:00–17:30) + US ET (09:30–16:00) via APScheduler
├── notifications/
│   └── telegram.py      send() + send_daily_report() — livelli INFO/WARNING/CRITICAL
├── monitoring/
│   └── healthcheck.py   FastAPI su :8080/health — stato IB Gateway + uptime
└── reporting/
    └── flex_query.py    IBKR Flex Web Service — XML annuale per dichiarazione IT
```

## Riferimenti a snippet chiave

`src/trading/strategy/interfaces.py` — le 6 ABC e i dataclass `RawSignal`, `AllocatedSignal`
`src/trading/strategy/implementations/ma_crossover.py:DividendFreeFilter` — universo EU/US curato
`src/trading/broker/market_data.py:MarketDataManager._on_realtime_bar` — aggregazione 5s→5min
`src/trading/db/repository.py:save_trade` — idempotenza su `ibkr_exec_id`
`src/trading/risk/manager.py:RiskManager.validate` — gate ordini
