# Trading Bot — Claude Code Project Context

Sistema di trading algoritmico automatizzato su Interactive Brokers.
Investitore italiano, regime dichiarativo, azioni growth senza dividendi (US + EU).

> **Documentazione completa**: 4 file `.md` nella root del progetto:
> `HANDOFF-1-architecture.md` · `HANDOFF-2-strategy.md` · `HANDOFF-3-hosting.md` · `HANDOFF-4-missing-pieces.md`
> Leggerli **tutti e 4** prima di implementare qualsiasi file.

---

## Stack Tecnologico (versioni definitive)

| Layer | Tool | Versione | Note |
|---|---|---|---|
| Package manager | **uv** | latest | Rimpiazza pip, venv, pyenv. 10-100x più veloce |
| Python | **3.12** | 3.12.x | Non 3.11 |
| IBKR API wrapper | **ib-async** | ≥1.0 | `pip install ib-async` |
| IB Gateway | **gnzsnz/ib-gateway-docker** | stable | Docker image con IBC+Xvfb inclusi |
| Database | **PostgreSQL 15** | 15+ | Con asyncpg driver |
| ORM | **SQLAlchemy 2.0** | ≥2.0 | Async mode |
| Migrations | **Alembic** | ≥1.13 | |
| Indicatori TA | **pandas-ta-classic** | latest | 252 indicatori, uv-compatible, nessun C dep |
| Warmup data | **yfinance** | latest | Per dati storici senza pacing IBKR |
| Backtesting | **vectorbt** | OSS | Migliaia di config in secondi |
| Calendari | **exchange-calendars** | ≥4.5 | NYSE + XETRA + Euronext |
| Scheduler | **APScheduler** | ≥3.10 | |
| Logging | **Loguru** | latest | Structured, rotation automatica |
| Alerting | **python-telegram-bot** | ≥20 | |
| Linting | **ruff** | latest | check + format (rimpiazza black) |
| Testing | **pytest + pytest-asyncio** | latest | |
| Containerizzazione | **Docker Compose** | v2 syntax | No campo `version:` (deprecato) |
| CI/CD | **GitHub Actions** | — | Deploy via SSH su Oracle Cloud |
| Hosting Fase 0 | **Oracle Cloud Always Free** | ARM | 4 vCPU / 24GB RAM, gratis |
| Hosting Fase 2 | **Vultr NJ High Frequency** | x86 | ~$24/mese, latenza <5ms IBKR |

---

## Comandi Chiave (tutti con uv)

```bash
# Setup iniziale (da zero)
curl -LsSf https://astral.sh/uv/install.sh | sh   # installa uv
uv python install 3.12
uv init trading-bot && cd trading-bot
uv add ib-async sqlalchemy[asyncio] alembic asyncpg pydantic-settings \
       apscheduler loguru python-telegram-bot pandas numpy pyarrow \
       pandas-ta-classic yfinance vectorbt exchange-calendars \
       aiohttp prometheus-client httpx pytz
uv add --dev pytest pytest-asyncio ruff mypy

# Avvio sviluppo
uv run python -m trading.main         # bot
uv run pytest tests/ -v               # test
uv run ruff check src/ && uv run ruff format src/

# DB migrations
uv run alembic revision --autogenerate -m "descrizione"
uv run alembic upgrade head

# Docker
docker compose up -d                  # avvia stack completo
docker compose logs -f trading-bot    # log real-time

# Tax export annuale
uv run python scripts/export_tax_report.py --year 2025

# Emergency stop
docker compose exec trading-bot python scripts/emergency_flatten.py
```

---

## Architettura in 30 secondi

```
GitHub Actions (CI/CD)
       │ SSH deploy
       ▼
Oracle Cloud VM (ARM) / Vultr NJ (x86)
├── gnzsnz/ib-gateway-docker   ← IB Gateway + IBC + Xvfb in un container
│        ↕ socket :4002
├── Trading Bot (Python 3.12)
│   ├── MarketDataManager      ← yfinance warmup + IBKR real-time bars
│   ├── StrategyComposer       ← 6 interfacce: Filter→Signal→Size→Alloc→Exec→Exit
│   ├── RiskManager            ← gate obbligatorio prima di ogni ordine
│   ├── OrderManager           ← limit orders + GTC stop automatici
│   └── Scheduler              ← dual session: EU 09:00 CET + US 09:30 ET
├── PostgreSQL 15              ← trades, positions, signals, P&L
└── Prometheus + Grafana       ← metriche

IBKR Paper (gratis) → IBKR Live (quando pronto)
```

---

## Universo Azioni

**Regola fondamentale: zero dividendi, zero transaction tax locale.**

```python
# US (NYSE/NASDAQ) — contratti: Stock(symbol, "SMART", "USD")
US = ["NVDA","META","GOOGL","AMZN","TSLA","AMD","CRM","SNOW",
      "PLTR","NET","DDOG","MDB","CRWD","PANW","COIN"]

# EU XETRA — contratti: Stock(symbol, "IBIS", "EUR") — nessuna transaction tax
EU_XETRA = ["SAP","IFX","AIXA","SRT3"]

# EU Euronext Amsterdam — contratti: Stock(symbol, "AEB", "EUR") — nessuna transaction tax
EU_AMS   = ["ASML","ADYEN","BESI"]

# EVITARE:
# - Azioni italiane (BVME/MTAA): Tobin Tax 0,2%
# - Azioni francesi (SBF): TTF ~0,3% su cap >1B€
```

---

## Pattern Strategia — 6 Interfacce

Ogni strategia è composta da 6 interfacce separate. **Non bypassare mai questo pattern.**

```python
# Flusso obbligatorio per ogni bar:
IUniverseFilter   → filtra simboli (dividend-free, liquidità, exchange)
ISignalGenerator  → genera RawSignal (direction, strength, reason)
IPositionSizer    → calcola USD da impegnare (Fixed Fractional default)
IPortfolioAllocator → gestisce segnali multipli simultanei
IExecutionAlgo    → traduce in ordini IBKR (limit aggressivo + GTC stop)
IExitLogic        → decide quando uscire dalla posizione

# Tutte in: src/trading/strategy/interfaces.py
# Esempio completo: src/trading/strategy/implementations/ma_crossover.py
```

---

## Vincoli Critici (non negoziabili)

1. **Nessun Market Order** — sempre Limit Order con prezzo aggressivo (last ±0.1%)
2. **GTC Stop Loss obbligatorio** su ogni BUY — piazzato immediatamente dopo il fill
3. **Nessun ordine bypassa RiskManager** — è il gate assoluto
4. **Pacing IBKR**: 11s tra richieste storiche, max 55 in 10 minuti → usare `yfinance` per warmup
5. **useRTH=True** sempre su `reqHistoricalData` e ordini (no pre/after-hours)
6. **IB Gateway su localhost** — porta :4002 mai esposta pubblicamente
7. **Credenziali** mai nel codice — solo da variabili d'ambiente / `.env`
8. **execId IBKR** è la chiave di idempotenza per `save_trade()` — sempre verificare duplicati
9. **IB Gateway restart 23:45 ET** — il bot gestisce disconnect via evento, non cron
10. **Dual session**: callback EU e US separati nello scheduler

---

## Struttura File (definitiva)

```
trading-bot/
├── CLAUDE.md                 ← questo file
├── pyproject.toml            ← uv, Python 3.12
├── uv.lock                   ← lockfile generato da uv
├── alembic.ini
├── .env.example
├── .env                      ← NON in git
├── docker-compose.yml        ← include gnzsnz/ib-gateway-docker
├── Dockerfile
├── .github/workflows/deploy.yml
│
├── src/trading/
│   ├── main.py
│   ├── config.py
│   ├── broker/
│   │   ├── client.py         ← IBClient con retry e disconnect handler
│   │   ├── market_data.py    ← yfinance warmup + IBKR real-time bars
│   │   └── orders.py         ← get_contract() per EU/US + limit+stop
│   ├── strategy/
│   │   ├── interfaces.py     ← 6 ABC interfaces
│   │   ├── composer.py       ← assembla le 6 interfacce
│   │   ├── registry.py       ← gestisce strategie multiple + capital allocation
│   │   └── implementations/
│   │       └── ma_crossover.py
│   ├── features/
│   │   └── pipeline.py       ← usa pandas-ta-classic (df.ta.rsi(), df.ta.ema(), ecc.)
│   ├── risk/
│   │   ├── manager.py
│   │   └── circuit_breaker.py
│   ├── db/
│   │   ├── models.py
│   │   ├── repository.py
│   │   └── migrations/
│   ├── scheduler/
│   │   └── jobs.py           ← dual session: CET per EU, ET per US
│   ├── notifications/
│   │   └── telegram.py
│   ├── monitoring/
│   │   └── healthcheck.py    ← HTTP :8080/health per UptimeRobot
│   └── reporting/
│       └── flex_query.py     ← export annuale per dichiarazione IT
│
├── tests/
│   ├── unit/
│   │   ├── test_risk_manager.py
│   │   ├── test_position_sizer.py
│   │   └── test_dividend_filter.py
│   └── integration/
│       └── test_ibkr_paper.py
│
└── scripts/
    ├── export_tax_report.py
    ├── emergency_flatten.py
    └── check_positions.py
```

---

## Indicatori Tecnici — pandas-ta-classic

Usare **sempre** `pandas-ta-classic` invece di implementazioni manuali in `features/pipeline.py`.

```python
import pandas_ta as ta

# ❌ NON fare (manuale)
def _rsi(series, period):
    delta = series.diff()
    ...

# ✅ FARE (pandas-ta-classic)
df.ta.rsi(length=14, append=True)       # aggiunge colonna RSI_14
df.ta.ema(length=9, append=True)        # EMA_9
df.ta.ema(length=21, append=True)       # EMA_21
df.ta.bbands(length=20, append=True)    # BBL_20, BBM_20, BBU_20
df.ta.atr(length=14, append=True)       # ATRr_14
df.ta.macd(append=True)                 # MACD_12_26_9, MACDh, MACDs
df.ta.vwap(append=True)                 # VWAP_D

# Applica tutto insieme (più efficiente)
df.ta.strategy("all")   # oppure custom strategy
```

---

## Warmup Data — yfinance (no pacing)

Per il warmup storico all'apertura del mercato usare **yfinance**, non IBKR.
IBKR ha pacing limits (11s tra richieste) che rallentano l'avvio.
yfinance è gratuito, senza limiti di frequenza per uso normale.

```python
import yfinance as yf

def warmup_from_yfinance(symbol: str, ibkr_exchange: str, n_bars: int = 200) -> pd.DataFrame:
    """
    Scarica dati storici da Yahoo Finance.
    Per simboli EU su IBKR, il ticker Yahoo è diverso:
      SAP (IBIS) → "SAP.DE"
      ASML (AEB) → "ASML.AS"
      ADYEN (AEB) → "ADYEN.AS"
    """
    YAHOO_MAP = {
        "SAP": "SAP.DE", "IFX": "IFX.DE", "AIXA": "AIXA.DE", "SRT3": "SRT3.DE",
        "ASML": "ASML.AS", "ADYEN": "ADYEN.AS", "BESI": "BESI.AS",
    }
    ticker = YAHOO_MAP.get(symbol, symbol)
    df = yf.download(ticker, period="60d", interval="5m", auto_adjust=True, progress=False)
    df.columns = [c.lower() for c in df.columns]
    df = df.rename(columns={"adj close": "close"})
    return df.tail(n_bars)
```

---

## Configurazione MCP per Claude Code

Installare questi MCP server **prima** di avviare lo sviluppo. Eseguire nella directory del progetto:

### 1. GitHub MCP (obbligatorio)
```bash
claude mcp add github \
  --command docker \
  --args "run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN ghcr.io/github/github-mcp-server" \
  --env GITHUB_PERSONAL_ACCESS_TOKEN=<tuo_token>
```
→ Permette a Claude Code di leggere PR, creare issue, ispezionare CI failures.

### 2. PostgreSQL MCP (obbligatorio per sviluppo)
```bash
claude mcp add postgres \
  -- npx -y @modelcontextprotocol/server-postgres \
  postgresql://trader:password@localhost:5432/trading
```
→ Permette query dirette al DB dei trade durante sviluppo e debug.
→ **Read-only in produzione** — usare solo su paper account.

### 3. Context7 (altamente raccomandato)
```bash
claude mcp add context7 -- npx -y @upstash/context7-mcp
```
→ Inietta documentazione aggiornata di `ib_async`, `pandas-ta-classic`, `SQLAlchemy 2.0`, `APScheduler` nei prompt. Impedisce che Claude Code usi API deprecate. Attivare con `use context7` nei prompt.

### 4. Sequential Thinking (raccomandato per problemi complessi)
```bash
claude mcp add sequential-thinking \
  -- npx -y @modelcontextprotocol/server-sequential-thinking
```
→ Aiuta Claude Code a ragionare step-by-step su architetture complesse (es. gestione dual session, reconnect logic, partial fills).

### Verifica installazione
```bash
claude mcp list
# Output atteso:
# github     ✓ connected
# postgres   ✓ connected
# context7   ✓ connected
# sequential-thinking ✓ connected
```

---

## Ordine di Implementazione (per Claude Code)

Implementare nell'ordine esatto. Ogni step deve compilare e passare i test prima di procedere.

```
Step  1: pyproject.toml (uv, Python 3.12, tutte le dipendenze)
Step  2: .env.example + config.py (Pydantic Settings)
Step  3: db/models.py (Trade, Position, Signal, DailyPnL)
Step  4: db/migrations/ (Alembic setup + env.py + prima migration)
Step  5: db/repository.py (tutte le operazioni CRUD)
Step  6: broker/client.py (IBClient + disconnect handler + fill handler)
Step  7: broker/market_data.py (yfinance warmup + IBKR real-time loop)
Step  8: broker/orders.py (get_contract() EU/US + limit+GTC stop)
Step  9: features/pipeline.py (pandas-ta-classic, sostituisce implementazioni manuali)
Step 10: strategy/interfaces.py (6 ABC)
Step 11: strategy/composer.py + registry.py
Step 12: strategy/implementations/ma_crossover.py (DividendFreeFilter incluso)
Step 13: risk/manager.py + risk/circuit_breaker.py
Step 14: scheduler/jobs.py (dual session EU CET + US ET)
Step 15: notifications/telegram.py
Step 16: monitoring/healthcheck.py (aiohttp, :8080/health)
Step 17: reporting/flex_query.py
Step 18: main.py (integrazione completa + signal handlers)
Step 19: docker-compose.yml (gnzsnz/ib-gateway-docker + bot + postgres + grafana)
Step 20: Dockerfile
Step 21: .github/workflows/deploy.yml (GitHub Actions: test → SSH deploy)
Step 22: tests/unit/ (risk_manager, position_sizer, dividend_filter)
Step 23: scripts/ (emergency_flatten, check_positions, export_tax_report)
```

---

## Variabili d'Ambiente Richieste

```bash
# IBKR
IBKR_USERNAME=         # username IBKR
IBKR_PASSWORD=         # password IBKR
TRADING_MODE=paper     # paper | live
IBKR_PORT=4001         # 4001=paper, 4002=live
IBKR_CLIENT_ID=1
IBKR_ACCOUNT=          # formato U1234567

# Database
DATABASE_URL=postgresql://trader:password@postgres:5432/trading
POSTGRES_PASSWORD=

# Telegram
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Tax reporting
IBKR_FLEX_TOKEN=
IBKR_FLEX_QUERY_ID=

# Risk limits
MAX_POSITION_SIZE_USD=10000.0
MAX_DAILY_LOSS_USD=500.0
MAX_OPEN_POSITIONS=5
DEFAULT_STOP_LOSS_PCT=0.02

# Monitoring
VNC_PASSWORD=          # per debug IB Gateway via VNC
GRAFANA_PASSWORD=
```

---

## Fasi del Progetto

| Fase | TRADING_MODE | Hosting | Costo |
|---|---|---|---|
| **0 — Dev** | `paper` | Oracle Cloud ARM (free) | €0 |
| **1 — Smoke test live** | `live` | Oracle Cloud ARM (free) | €0 + commissioni |
| **2 — Full scale** | `live` | Vultr NJ HF x86 (~$24/mese) | $24/mese |

**Non passare alla Fase 1 prima di:** 2 settimane paper trading + backtest out-of-sample positivo + tutte le checklist di Part 2 e Part 3 completate.

---

## Gotcha Principali (da ricordare sempre)

| Problema | Soluzione |
|---|---|
| Pacing violation (errore 162) | Usare yfinance per warmup; 11s tra req IBKR |
| IB Gateway restart 23:45 ET | Gestire via `ib.disconnectedEvent`, non cron |
| Partial fill | Salvare ogni fill con `execId` come chiave idempotente |
| EU stock ticker Yahoo ≠ IBKR | Vedi `YAHOO_MAP` in market_data.py |
| ARM vs x86 Docker | `platform: linux/amd64` su Oracle ARM, nativo su Vultr |
| `IBKR_HOST` in Docker | Usare nome servizio (`ib-gateway`), non `127.0.0.1` |
| Tobin Tax | Mai azioni BVME/MTAA (IT) o SBF (FR) nell'universo |

---

*CLAUDE.md — Versione 1.0 — Giugno 2026*
*Stack finale. Aggiornare questo file se cambia l'architettura.*
