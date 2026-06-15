---
generated-from-commit: 8a47d3039a88d6258bc44197ff3ea5189dd0f5b9
generated-from-branch: main
generated-date: 2026-06-15
covers-paths:
  - tests/**
  - pyproject.toml
last-verified-commit: 8a47d3039a88d6258bc44197ff3ea5189dd0f5b9
---

# Test di sviluppo

## Test runner e comandi

Framework: `pytest` + `pytest-asyncio` (asyncio_mode = "auto" in pyproject.toml).
Tutte le dipendenze dev gestite da uv come dev-dependencies.

```bash
uv run pytest tests/ -v                          # tutti i test
uv run pytest tests/unit/ -v                     # solo unit
uv run pytest tests/integration/ -v             # solo integration (richiedono IBKR Paper attivo)
uv run ruff check src/ && uv run ruff format src/  # lint + format
uv run mypy src/                                 # type check (strict=false)
```

## Struttura test

```
tests/
├── unit/
│   ├── test_risk_manager.py      — logica di blocco, limiti daily loss, max posizioni
│   ├── test_position_sizer.py    — FixedFractionalSizer, calcolo shares, edge cases
│   └── test_signal_generator.py  — EMACrossoverSignal su dati sintetici, warmup_bars
└── integration/
    └── test_ibkr_paper.py        — connessione reale al paper account (richiede IB Gateway attivo)
```

Unit test prioritari (non richiedono IBKR attivo):
- `test_risk_manager.py`: verifica blocco su max_open_positions, daily loss limit, quantità ≤ 0
- `test_position_sizer.py`: fixed fractional sizing, cap 20% del portafoglio, fallback senza stop loss
- `test_signal_generator.py`: EMA crossover su DataFrame sintetico, nessun segnale prima di warmup_bars

## Backtesting

Il backtesting usa `vectorbt` (dev dependency) con un adapter su `ISignalGenerator`.
`src/trading/backtesting/runner.py:backtest_signal_generator()` esegue il generatore su dati
storici senza toccare IBKR e calcola: total_return, sharpe_ratio, max_drawdown, win_rate.

Workflow raccomandato prima del go-live:
1. Backtest in-sample su dati 2022–2024 (scaricabili con `scripts/download_historical.py`)
2. Walk-forward validation out-of-sample su 2024–2025
3. Paper trading ≥ 2 settimane (risultati coerenti col backtest)
4. Live con capitale ridotto (10-20% del target) per 4 settimane
5. Full scale solo se paper + small-live sono coerenti

## Rotte e dati mockati

In sviluppo: account IBKR Paper (porta 4001). `TRADING_MODE=paper` nel `.env`.
Il paper account è identico al live per API ma non esegue ordini reali.
Fill in paper: immediato al last price (senza slippage) — differenza da live da tenere presente.

Non ci sono endpoint mockati o fixture statiche per i test unit: i test costruiscono DataFrame
pandas sintetici internamente.

## Hook e controlli di qualità

ruff: linting + formatting (rimpiazza black). Configurato per Python 3.12, line-length 100.
mypy: type checking con strict=false (ignora missing imports per librerie non stubs).
Pre-live checklist (da completare manualmente prima del go-live, see deployment.md):
- IB Gateway si riavvia automaticamente
- Reconnect automatico dopo restart
- Risk manager blocca daily loss limit
- GTC stop loss piazzato ad ogni BUY
- `emergency_flatten.py` funziona in paper
- Flex Report XML valido
- Telegram alerts funzionanti
- PostgreSQL salva trade con exec_id univoco
