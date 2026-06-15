# Automated Trading System — Technical Handoff
**Scope:** Algorithmic stock trading via Interactive Brokers API  
**Regime fiscale:** Dichiarativo (IBKR, broker estero)  
**Obiettivo:** Sistema completamente automatizzato per compravendita di azioni (US + EU) senza dividendi, con export fiscale annuale  
**Universo:** Azioni growth senza dividendi — US (NYSE/NASDAQ) + EU (XETRA, Euronext Amsterdam). Evitare azioni italiane (Tobin Tax 0,2%) e francesi (TTF ~0,3%).

---

## Fasi del Progetto

| Fase | Account IBKR | Hosting | Costo |
|---|---|---|---|
| **0 — Sviluppo e Test** | Paper (gratuito) | Oracle Cloud Always Free | €0 |
| **1 — Live piccolo** | Live (capitale ridotto) | Oracle Cloud Always Free | €0 |
| **2 — Live scalato** | Live (capitale pieno) | Vultr NJ ~$24/mese | ~$24/mese |

Iniziare sempre dalla Fase 0. L'account IBKR Paper è identico al live per API e funzionalità, ma non esegue ordini reali. Passare alla Fase 1 solo dopo almeno 2 settimane di paper trading con risultati coerenti col backtest.

---

## 1. Architettura Generale

```
┌─────────────────────────────────────────────────────────────────┐
│          Oracle Cloud Always Free VM (ARM, Ubuntu 24.04)        │
│                                                                 │
│  ┌─────────────┐    socket     ┌──────────────────────────────┐ │
│  │ IB Gateway  │◄─────────────►│     Trading Bot (Python)     │ │
│  │ (headless)  │  localhost    │                              │ │
│  │  port 4002  │  :4002        │  ┌──────────┐ ┌──────────┐  │ │
│  └─────────────┘               │  │ Strategy │ │  Order   │  │ │
│         ▲                      │  │ Engine   │ │  Manager │  │ │
│         │ auto-login           │  └──────────┘ └──────────┘  │ │
│  ┌─────────────┐               │  ┌──────────┐ ┌──────────┐  │ │
│  │    IBC      │               │  │   Risk   │ │  Logger  │  │ │
│  │(IB Controller)              │  │  Manager │ │          │  │ │
│  └─────────────┘               │  └──────────┘ └──────────┘  │ │
│                                └──────────────┬───────────────┘ │
│                                               │                  │
│                                ┌──────────────▼───────────────┐ │
│                                │        PostgreSQL DB          │ │
│                                │  (trades, positions, P&L,     │ │
│                                │   signals, errors)            │ │
│                                └──────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
         │                                        │
         ▼                                        ▼
   IBKR Servers                         Telegram Bot (alerts)
   NYSE/NASDAQ + XETRA/Euronext

GitHub → GitHub Actions (CI/CD gratuito) → deploy via SSH → VM
```

**Flusso dati:**
1. IBC avvia e mantiene loggato IB Gateway in modo headless
2. Il Trading Bot si connette a IB Gateway via socket TCP locale
3. Il Bot riceve market data real-time → Strategy Engine genera segnali
4. I segnali passano per Risk Manager → Order Manager invia ordini a IBKR
5. Ogni esecuzione viene loggata su PostgreSQL
6. Alerts critici vengono inviati via Telegram

**Due sessioni di mercato gestite in parallelo:**
- EU (XETRA/Euronext): 09:00–17:30 CET
- US (NYSE/NASDAQ): 15:30–22:00 CET
- Overlap (entrambi aperti): 15:30–17:30 CET

---

## 2. Stack Tecnologico

| Layer | Tecnologia | Versione minima | Note |
|---|---|---|---|
| Broker gateway | IB Gateway | 10.30+ | Headless, nessuna GUI |
| Auto-login | IBC (IB Controller) | 3.19+ | Open source, gestisce login automatico |
| Linguaggio | Python | 3.11+ | |
| API wrapper | `ib_async` | latest | Fork moderno di ib_insync, asyncio-native |
| Database | PostgreSQL | 15+ | Storico trade, P&L, segnali |
| ORM | SQLAlchemy | 2.0+ | Con Alembic per migrations |
| Scheduling | APScheduler | 3.10+ | Task periodici (open/close market) |
| Logging | Loguru | latest | Structured logging su file + stdout |
| Alerting | python-telegram-bot | 20+ | Notifiche critiche |
| Monitoring | Prometheus + Grafana | latest | Metriche sistema e trading |
| Containerizzazione | Docker + Docker Compose | latest | Per IB Gateway + Bot |
| Process manager | systemd | — | Su VPS bare-metal/VM |
| Data analysis | pandas, numpy | latest | Calcolo indicatori |
| Backtesting | backtrader o vectorbt | latest | Test strategie su dati storici |

---

## 3. Infrastruttura — Fase 0/1 (Costo Zero)

### Oracle Cloud Always Free — la scelta per le prime fasi

Oracle Cloud offre gratuitamente, senza scadenza e senza carta di credito attiva:
- **ARM Ampere A1**: fino a 4 vCPU + 24 GB RAM (configurabile come 1 VM singola)
- **Storage**: 200 GB block volume
- **Rete**: 10 TB/mese uscita

È l'unica opzione realmente adatta al bot: le alternative "free" (AWS t2.micro 1GB, Railway 500h/mese, Render che spegne i processi dopo 15 min) non reggono un processo 24/7.

**Nota su ARM**: IB Gateway è Java — Java 17+ ha build native per ARM64 (aarch64). IBC, Xvfb e tutti i pacchetti Python funzionano su ARM Ubuntu. Non ci sono problemi di compatibilità.

### Configurazione VM consigliata su Oracle Cloud
- **Shape**: VM.Standard.A1.Flex (ARM)
- **OCPU**: 4
- **RAM**: 24 GB
- **OS**: Ubuntu 24.04 LTS (ARM64)
- **Region**: `us-ashburn-1` (Virginia — vicino ai server IBKR in NJ) oppure `eu-frankfurt-1` se si privilegiano le azioni EU

### Fase 2 (quando si scala): Vultr NJ
Quando le commissioni generate superano i costi infrastrutturali, passare a Vultr High Frequency New Jersey (~$24/mese, NVMe, 2 vCPU/4GB, latenza ~2-5ms a IBKR).

### Pacchetti di sistema da installare
```bash
# Display virtuale per IB Gateway (obbligatorio anche su ARM)
apt install -y xvfb x11vnc

# Java Runtime ARM64
apt install -y openjdk-17-jre

# Python
apt install -y python3.11 python3.11-venv python3-pip

# PostgreSQL
apt install -y postgresql-15

# Build tools
apt install -y git curl wget unzip build-essential
```

### CI/CD gratuito: GitHub Actions (non Render per il bot)
Render è ottimo per CI/CD ma **non adatto a eseguire il bot** — il free tier spegne i processi dopo 15 minuti di inattività. Usarlo solo come pipeline CI se già si ha l'account.

Il flusso consigliato (tutto gratuito):
```
Push su GitHub → GitHub Actions (test automatici) → SSH deploy su Oracle Cloud VM
```

```yaml
# .github/workflows/deploy.yml
name: Test and Deploy
on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -e ".[dev]"
      - run: pytest tests/unit/ -v

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy via SSH
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.ORACLE_VM_IP }}
          username: trader
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd ~/trading-bot
            git pull origin main
            source .venv/bin/activate
            pip install -e "."
            alembic upgrade head
            systemctl restart trading-bot
```

---

## 4. Setup IB Gateway + IBC

### 4.1 Download e installazione IB Gateway
```bash
# Scaricare IB Gateway installer da:
# https://www.interactivebrokers.com/en/trading/ibgateway-stable.php
# Scegliere versione Linux standalone

chmod +x ibgateway-stable-standalone-linux-x64.sh
./ibgateway-stable-standalone-linux-x64.sh -q   # installazione silenziosa
# Default install path: ~/Jts/ibgateway/
```

### 4.2 Download e configurazione IBC
```bash
# IBC: https://github.com/IbcAlpha/IBC
wget https://github.com/IbcAlpha/IBC/releases/latest/download/IBCLinux-3.19.0.zip
unzip IBCLinux-3.19.0.zip -d ~/ibc

# Configurare ~/ibc/config.ini
```

**File `~/ibc/config.ini` — configurazione chiave:**
```ini
# IBKR credentials — da passare via variabili d'ambiente, NON hardcodare
IbLoginId=
IbPassword=

# LIVE account: usa 'live', PAPER account: usa 'paper'
TradingMode=live

# Accetta automaticamente il login a due fattori (richiede configurazione in IBKR)
AcceptIncomingConnectionRequest=accept

# Riavvio automatico del gateway
ReloginAfterSecondFactorAuthenticationTimeout=yes
SecondFactorAuthenticationTimeout=180

# Porta API (live: 4002, paper: 4001)
OverrideTwsApiPort=4002

# Chiudi automaticamente al logout di sistema
ExistingSessionDetectedAction=secondary
```

### 4.3 Script di avvio con Xvfb
```bash
#!/bin/bash
# /usr/local/bin/start-ibgateway.sh

export DISPLAY=:1
Xvfb :1 -screen 0 1024x768x24 &
sleep 2

cd ~/ibc
./gatewaystart.sh \
  --gateway ~/Jts/ibgateway/1030 \
  --ibc ~/ibc \
  --mode live \
  --user "${IBKR_USERNAME}" \
  --pw "${IBKR_PASSWORD}"
```

### 4.4 Systemd service per IB Gateway
```ini
# /etc/systemd/system/ibgateway.service
[Unit]
Description=Interactive Brokers Gateway
After=network.target

[Service]
Type=forking
User=trader
EnvironmentFile=/etc/trading/credentials.env
ExecStart=/usr/local/bin/start-ibgateway.sh
Restart=on-failure
RestartSec=30
TimeoutStartSec=120

[Install]
WantedBy=multi-user.target
```

```bash
# /etc/trading/credentials.env (permessi 600, owner: trader)
IBKR_USERNAME=tuousername
IBKR_PASSWORD=tuapassword
```

---

## 5. Struttura del Progetto Python

```
trading-bot/
├── pyproject.toml
├── .env.example
├── .env                          # NON committare, in .gitignore
├── docker-compose.yml
├── Dockerfile
│
├── src/
│   └── trading/
│       ├── __init__.py
│       ├── main.py               # Entrypoint principale
│       ├── config.py             # Configurazione da env vars
│       │
│       ├── broker/
│       │   ├── __init__.py
│       │   ├── client.py         # Wrapper ib_async: connessione, riconnessione
│       │   ├── market_data.py    # Subscription dati real-time e storici
│       │   └── orders.py         # Invio, modifica, cancellazione ordini
│       │
│       ├── strategy/
│       │   ├── __init__.py
│       │   ├── base.py           # Classe astratta Strategy
│       │   ├── example_ma.py     # Esempio: Moving Average Crossover
│       │   └── signals.py        # Dataclass Signal
│       │
│       ├── risk/
│       │   ├── __init__.py
│       │   └── manager.py        # Regole di risk management
│       │
│       ├── db/
│       │   ├── __init__.py
│       │   ├── models.py         # SQLAlchemy models
│       │   ├── repository.py     # CRUD operations
│       │   └── migrations/       # Alembic migrations
│       │
│       ├── notifications/
│       │   ├── __init__.py
│       │   └── telegram.py       # Alerting via Telegram
│       │
│       ├── scheduler/
│       │   ├── __init__.py
│       │   └── jobs.py           # Market open/close, EOD tasks
│       │
│       └── reporting/
│           ├── __init__.py
│           └── flex_query.py     # Export IBKR Flex Query per dichiarazione
│
├── tests/
│   ├── unit/
│   └── integration/
│
├── scripts/
│   ├── backtest.py
│   └── export_tax_report.py      # Script annuale per export fiscale
│
└── data/
    └── historical/               # Cache dati storici locali
```

---

## 6. Configurazione (`config.py`)

Tutto il config deve venire da variabili d'ambiente (mai hardcodato nel codice).

```python
# src/trading/config.py
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # IBKR Connection
    IBKR_HOST: str = "127.0.0.1"
    IBKR_PORT: int = 4002          # 4002 live, 4001 paper
    IBKR_CLIENT_ID: int = 1        # Deve essere univoco per ogni connessione
    IBKR_ACCOUNT: str              # Account ID IBKR (es. U1234567)

    # Database
    DATABASE_URL: str              # postgresql://user:pass@localhost:5432/trading

    # Telegram
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_CHAT_ID: str

    # Risk Management
    MAX_POSITION_SIZE_USD: float = 10_000.0
    MAX_DAILY_LOSS_USD: float = 500.0
    MAX_OPEN_POSITIONS: int = 5
    DEFAULT_STOP_LOSS_PCT: float = 0.02   # 2%

    # Strategy
    SYMBOLS: List[str] = ["AAPL", "MSFT", "NVDA"]
    TIMEFRAME: str = "5 mins"

    # Tax Reporting
    IBKR_FLEX_TOKEN: str           # Token per Flex Web Service
    IBKR_FLEX_QUERY_ID: str        # ID della Flex Query configurata su IBKR

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

---

## 7. Broker Client (`broker/client.py`)

```python
# src/trading/broker/client.py
"""
Wrapper attorno a ib_async che gestisce:
- connessione e riconnessione automatica
- gestione client_id unico
- timeout e error handling
"""
import asyncio
from ib_async import IB, util
from loguru import logger
from trading.config import settings

class IBClient:
    def __init__(self):
        self.ib = IB()
        self._connected = False

    async def connect(self):
        """Connessione con retry automatico."""
        max_retries = 5
        for attempt in range(max_retries):
            try:
                await self.ib.connectAsync(
                    host=settings.IBKR_HOST,
                    port=settings.IBKR_PORT,
                    clientId=settings.IBKR_CLIENT_ID,
                    timeout=20
                )
                self._connected = True
                logger.info(f"Connesso a IB Gateway su port {settings.IBKR_PORT}")
                return
            except Exception as e:
                logger.warning(f"Tentativo {attempt+1}/{max_retries} fallito: {e}")
                await asyncio.sleep(10 * (attempt + 1))
        raise ConnectionError("Impossibile connettersi a IB Gateway dopo tutti i tentativi")

    async def disconnect(self):
        self.ib.disconnect()
        self._connected = False

    def on_error(self, reqId, errorCode, errorString, contract):
        """
        Codici di errore IBKR rilevanti:
        1100: connessione persa
        1102: connessione ripristinata (dati risynced)
        2104: market data farm connessa
        2106: HMDS data farm connessa
        200: no security definition (symbol non trovato)
        201: ordine rifiutato
        """
        if errorCode in (1100, 1101, 1102):
            logger.warning(f"Connessione IBKR: {errorCode} - {errorString}")
        elif errorCode == 201:
            logger.error(f"ORDINE RIFIUTATO reqId={reqId}: {errorString}")
        else:
            logger.debug(f"IBKR msg {errorCode} reqId={reqId}: {errorString}")
```

---

## 8. Database Schema (`db/models.py`)

```python
# src/trading/db/models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, Text
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime
import enum

class Base(DeclarativeBase):
    pass

class OrderSide(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"

class Trade(Base):
    """Una singola esecuzione (fill) di ordine — fondamentale per dichiarazione fiscale."""
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True)
    ibkr_order_id = Column(Integer, nullable=False, index=True)
    ibkr_exec_id = Column(String(64), unique=True)   # ID univoco esecuzione IBKR
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(Enum(OrderSide), nullable=False)
    quantity = Column(Float, nullable=False)
    fill_price = Column(Float, nullable=False)
    commission = Column(Float, default=0.0)
    currency = Column(String(3), default="USD")
    exchange = Column(String(20))
    executed_at = Column(DateTime, default=datetime.utcnow, index=True)
    strategy_name = Column(String(64))
    signal_id = Column(Integer)

class Position(Base):
    """Posizioni aperte correnti — sincronizzate con IBKR."""
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, unique=True)
    quantity = Column(Float, nullable=False)
    avg_cost = Column(Float, nullable=False)
    current_price = Column(Float)
    unrealized_pnl = Column(Float)
    updated_at = Column(DateTime, default=datetime.utcnow)

class Signal(Base):
    """Ogni segnale generato dalla strategia, per audit e backtesting."""
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False)
    strategy_name = Column(String(64))
    direction = Column(Enum(OrderSide))
    strength = Column(Float)       # 0.0 a 1.0
    reason = Column(Text)          # Descrizione human-readable del segnale
    acted_upon = Column(String(3), default="NO")  # YES/NO/SKIP (risk block)
    generated_at = Column(DateTime, default=datetime.utcnow)

class DailyPnL(Base):
    """P&L giornaliero aggregato — per monitoraggio e dichiarazione."""
    __tablename__ = "daily_pnl"

    id = Column(Integer, primary_key=True)
    date = Column(String(10), unique=True)    # YYYY-MM-DD
    realized_pnl = Column(Float, default=0.0)
    commissions = Column(Float, default=0.0)
    num_trades = Column(Integer, default=0)
    ending_portfolio_value = Column(Float)
```

---

## 9. Strategy Interface Contract (`strategy/base.py`)

Ogni strategia deve implementare questa interfaccia. È il punto di estensione principale: si aggiungono nuove strategie senza modificare il resto del sistema.

```python
# src/trading/strategy/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from trading.db.models import OrderSide

@dataclass
class Signal:
    symbol: str
    direction: OrderSide
    strength: float          # 0.0 a 1.0
    reason: str
    suggested_quantity: Optional[float] = None    # override position sizing
    stop_loss_price: Optional[float] = None
    take_profit_price: Optional[float] = None
    generated_at: datetime = None

    def __post_init__(self):
        if self.generated_at is None:
            self.generated_at = datetime.utcnow()

class BaseStrategy(ABC):
    """
    Interfaccia che ogni strategia deve implementare.
    
    Il trading bot chiama on_bar() ad ogni nuovo bar di mercato.
    La strategia può restituire uno o più Signal, oppure None.
    """
    name: str = "unnamed"
    symbols: list[str] = []

    @abstractmethod
    async def on_bar(self, symbol: str, bar: dict) -> Optional[Signal]:
        """
        Chiamato ad ogni nuovo bar di dati.
        
        Args:
            symbol: ticker (es. "AAPL")
            bar: dict con keys: open, high, low, close, volume, timestamp
        
        Returns:
            Signal oppure None se nessuna azione
        """
        pass

    async def on_fill(self, symbol: str, side: OrderSide, quantity: float, price: float):
        """Callback opzionale quando un ordine viene eseguito."""
        pass

    async def on_position_update(self, symbol: str, quantity: float, unrealized_pnl: float):
        """Callback opzionale quando la posizione cambia."""
        pass
```

---

## 10. Risk Manager (`risk/manager.py`)

Il Risk Manager è il gate tra Strategy e Order Manager. **Nessun ordine bypassa il risk manager.**

```python
# src/trading/risk/manager.py
"""
Regole di risk management applicate prima di ogni ordine.
Il Risk Manager può:
  - approvare il segnale invariato
  - modificare quantity/stop_loss
  - bloccare completamente il segnale (restituisce None)
"""
from loguru import logger
from trading.strategy.base import Signal
from trading.config import settings
from trading.db.repository import get_daily_pnl, get_open_positions_count

class RiskManager:

    async def validate(self, signal: Signal, current_portfolio_value: float) -> Signal | None:
        """
        Ritorna il Signal (eventualmente modificato) oppure None se bloccato.
        """
        # 1. CHECK: limite massimo posizioni aperte
        open_positions = await get_open_positions_count()
        if open_positions >= settings.MAX_OPEN_POSITIONS:
            logger.warning(f"RISK BLOCK: max posizioni ({settings.MAX_OPEN_POSITIONS}) raggiunto")
            return None

        # 2. CHECK: perdita giornaliera massima
        daily_pnl = await get_daily_pnl()
        if daily_pnl <= -settings.MAX_DAILY_LOSS_USD:
            logger.warning(f"RISK BLOCK: daily loss limit ${settings.MAX_DAILY_LOSS_USD} raggiunto. PnL odierno: ${daily_pnl:.2f}")
            return None

        # 3. POSITION SIZING: calcolo quantità se non specificata dalla strategia
        if signal.suggested_quantity is None:
            signal.suggested_quantity = self._calculate_position_size(
                signal, current_portfolio_value
            )

        # 4. CHECK: dimensione posizione non supera il limite per singolo trade
        # (questo richiederebbe il prezzo corrente — semplificato qui)
        if signal.suggested_quantity <= 0:
            logger.warning(f"RISK BLOCK: quantità calcolata <= 0 per {signal.symbol}")
            return None

        # 5. STOP LOSS: imposta default se la strategia non lo ha specificato
        if signal.stop_loss_price is None and signal.direction.value == "BUY":
            # Stop loss di default: 2% sotto il prezzo entry (approssimativo)
            # Il prezzo reale viene preso al momento dell'ordine
            pass  # gestito in orders.py con stop order separato

        logger.info(f"RISK OK: {signal.symbol} {signal.direction.value} qty={signal.suggested_quantity:.2f}")
        return signal

    def _calculate_position_size(self, signal: Signal, portfolio_value: float) -> float:
        """
        Position sizing: dimensione massima per singola posizione in dollari,
        convertita in numero di azioni basandosi su un prezzo stimato.
        
        NOTA: implementare qui il proprio modello di position sizing
        (fixed fractional, Kelly criterion, volatility-adjusted, ecc.)
        """
        # Esempio base: usa MAX_POSITION_SIZE_USD, il prezzo verrà gestito
        # in orders.py dove si ha accesso al prezzo di mercato reale
        max_usd = min(settings.MAX_POSITION_SIZE_USD, portfolio_value * 0.20)
        return max_usd  # ritorna USD; convertire in shares in orders.py
```

---

## 11. Order Manager (`broker/orders.py`)

```python
# src/trading/broker/orders.py
"""
Traduce Signal → Ordini IBKR effettivi.
Gestisce: Market, Limit, Stop Loss automatico.
"""
from ib_async import Stock, MarketOrder, LimitOrder, StopOrder, OrderCombo
from loguru import logger
from trading.strategy.base import Signal
from trading.db.models import OrderSide
from trading.config import settings

class OrderManager:
    def __init__(self, ib_client):
        self.ib = ib_client.ib

    async def execute_signal(self, signal: Signal) -> bool:
        """
        Esegue un segnale approvato dal Risk Manager.
        Invia ordine principale + stop loss automatico.
        """
        contract = Stock(signal.symbol, "SMART", "USD")

        # Recupera prezzo corrente per calcolare shares
        ticker = await self.ib.reqTickersAsync(contract)
        current_price = ticker[0].last or ticker[0].close
        if not current_price:
            logger.error(f"Nessun prezzo disponibile per {signal.symbol}")
            return False

        # Calcola numero di shares
        shares = int(signal.suggested_quantity / current_price)
        if shares <= 0:
            logger.warning(f"Shares calcolate = 0 per {signal.symbol} @ ${current_price:.2f}")
            return False

        action = "BUY" if signal.direction == OrderSide.BUY else "SELL"

        # Ordine principale: Limit order (evita slippage rispetto a Market)
        # Usa prezzo leggermente aggressivo: ask + 0.01 per BUY, bid - 0.01 per SELL
        limit_price = round(current_price * 1.001, 2) if action == "BUY" else round(current_price * 0.999, 2)
        main_order = LimitOrder(action, shares, limit_price)
        main_order.tif = "DAY"  # Day order — non overnight

        trade = self.ib.placeOrder(contract, main_order)
        logger.info(f"ORDINE INVIATO: {action} {shares} {signal.symbol} @ ${limit_price:.2f}")

        # Stop Loss automatico (se non impostato: default -2%)
        stop_price = signal.stop_loss_price or round(current_price * (1 - settings.DEFAULT_STOP_LOSS_PCT), 2)
        if action == "BUY":
            stop_order = StopOrder("SELL", shares, stop_price)
            stop_order.tif = "GTC"  # Good Till Cancel
            self.ib.placeOrder(contract, stop_order)
            logger.info(f"STOP LOSS: SELL {shares} {signal.symbol} @ ${stop_price:.2f}")

        return True

    async def cancel_all_orders(self, symbol: str = None):
        """Emergency: cancella tutti gli ordini aperti (o per un solo simbolo)."""
        open_orders = await self.ib.reqOpenOrdersAsync()
        for order in open_orders:
            if symbol is None or order.contract.symbol == symbol:
                self.ib.cancelOrder(order.order)
                logger.warning(f"CANCELLATO ordine {order.order.orderId} su {order.contract.symbol}")

    async def flatten_all_positions(self):
        """Emergency: chiude tutte le posizioni aperte a mercato."""
        positions = await self.ib.reqPositionsAsync()
        for pos in positions:
            if pos.position != 0:
                action = "SELL" if pos.position > 0 else "BUY"
                order = MarketOrder(action, abs(pos.position))
                self.ib.placeOrder(pos.contract, order)
                logger.warning(f"FLATTEN: {action} {abs(pos.position)} {pos.contract.symbol}")
```

---

## 12. Scheduler (`scheduler/jobs.py`)

```python
# src/trading/scheduler/jobs.py
"""
Due sessioni di mercato gestite in parallelo:

  EU (XETRA / Euronext Amsterdam):
    Apertura: 09:00 CET  →  chiusura: 17:30 CET
    (XETRA chiude 17:30, Euronext Amsterdam 17:30)

  US (NYSE / NASDAQ):
    Apertura: 09:30 ET   →  chiusura: 16:00 ET
    In CET: 15:30–22:00 CET

  Overlap entrambi aperti: 15:30–17:30 CET

IB Gateway daily restart: 23:45 ET (05:45 CET)
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

ET  = pytz.timezone("America/New_York")
CET = pytz.timezone("Europe/Rome")

def setup_scheduler(bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()

    # ── SESSIONE EU ────────────────────────────────────────────────
    scheduler.add_job(bot.pre_market_eu, CronTrigger(
        day_of_week="mon-fri", hour=8, minute=55, timezone=CET
    ))
    scheduler.add_job(bot.start_trading_eu, CronTrigger(
        day_of_week="mon-fri", hour=9, minute=0, timezone=CET
    ))
    scheduler.add_job(bot.stop_new_entries_eu, CronTrigger(
        day_of_week="mon-fri", hour=17, minute=20, timezone=CET
    ))
    scheduler.add_job(bot.close_intraday_eu, CronTrigger(
        day_of_week="mon-fri", hour=17, minute=28, timezone=CET
    ))

    # ── SESSIONE US ────────────────────────────────────────────────
    scheduler.add_job(bot.pre_market_us, CronTrigger(
        day_of_week="mon-fri", hour=9, minute=25, timezone=ET
    ))
    scheduler.add_job(bot.start_trading_us, CronTrigger(
        day_of_week="mon-fri", hour=9, minute=30, timezone=ET
    ))
    scheduler.add_job(bot.stop_new_entries_us, CronTrigger(
        day_of_week="mon-fri", hour=15, minute=45, timezone=ET
    ))
    scheduler.add_job(bot.close_intraday_us, CronTrigger(
        day_of_week="mon-fri", hour=15, minute=55, timezone=ET
    ))

    # ── EOD (dopo chiusura US) ─────────────────────────────────────
    scheduler.add_job(bot.end_of_day_report, CronTrigger(
        day_of_week="mon-fri", hour=16, minute=5, timezone=ET
    ))

    # ── IB Gateway daily restart 23:45 ET ─────────────────────────
    # Il bot gestisce disconnect/reconnect via evento — questo job
    # è un safety net che forza la riconnessione se il bot non l'ha fatto
    scheduler.add_job(bot.handle_gateway_restart, CronTrigger(
        day_of_week="mon-fri", hour=23, minute=50, timezone=ET
    ))

    return scheduler
```

---

## 13. Tax Reporting Export (`reporting/flex_query.py`)

Questo modulo gestisce l'export annuale dei dati per la dichiarazione dei redditi italiana. Si usa una volta l'anno (o quando serve per controllo).

```python
# src/trading/reporting/flex_query.py
"""
Scarica il Flex Report da IBKR via Flex Web Service API.
Il file XML/CSV risultante è quello da importare in MoneyViz
o da consegnare al commercialista per compilare Quadro RT e RW.

Prerequisiti IBKR (configurazione una-tantum sul portale web IBKR):
1. Account Management → Reports → Flex Queries
2. Creare una nuova Flex Query con questi campi obbligatori:
   - Trades: tutte le colonne (symbol, date, quantity, price, commission, proceeds, cost_basis)
   - Open Positions al 31/12
   - Cash Transactions (dividendi, pagamenti interesse)
3. Nota il Query ID numerico
4. Genera un Token dal menu Flex Web Service
"""
import requests
import time
from loguru import logger
from trading.config import settings
from pathlib import Path

FLEX_BASE_URL = "https://gdcdyn.interactivebrokers.com/Universal/servlet/FlexStatementService"

def download_flex_report(year: int, output_dir: str = "./data/tax") -> Path:
    """
    Scarica il Flex Report annuale.
    
    Args:
        year: Anno fiscale (es. 2025 per dichiarazione 2026)
        output_dir: Cartella dove salvare il file
    
    Returns:
        Path del file XML scaricato
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    output_path = Path(output_dir) / f"ibkr_flex_{year}.xml"

    # Step 1: Richiedi il report (asincrono — IBKR lo genera in background)
    request_url = (
        f"{FLEX_BASE_URL}.SendRequest"
        f"?t={settings.IBKR_FLEX_TOKEN}"
        f"&q={settings.IBKR_FLEX_QUERY_ID}"
        f"&v=3"
    )
    resp = requests.get(request_url, timeout=30)
    resp.raise_for_status()

    # Estrai il reference code dalla risposta XML
    import xml.etree.ElementTree as ET
    root = ET.fromstring(resp.text)
    reference_code = root.find(".//ReferenceCode")
    if reference_code is None:
        raise ValueError(f"Flex request fallita: {resp.text}")
    ref_code = reference_code.text
    logger.info(f"Flex report richiesto. Reference: {ref_code}")

    # Step 2: Poll fino a quando il report è pronto (può richiedere 1-3 minuti)
    statement_url = (
        f"{FLEX_BASE_URL}.GetStatement"
        f"?t={settings.IBKR_FLEX_TOKEN}"
        f"&q={ref_code}"
        f"&v=3"
    )
    for attempt in range(20):
        time.sleep(10)
        stmt_resp = requests.get(statement_url, timeout=30)
        if "FlexStatement" in stmt_resp.text:
            # Report pronto
            output_path.write_text(stmt_resp.text, encoding="utf-8")
            logger.info(f"Flex report scaricato: {output_path}")
            return output_path
        logger.debug(f"Tentativo {attempt+1}/20 — report non ancora pronto")

    raise TimeoutError("Flex report non disponibile dopo 200 secondi")


# Script standalone per uso manuale:
# python scripts/export_tax_report.py --year 2025
```

**Script CLI (`scripts/export_tax_report.py`):**
```python
#!/usr/bin/env python3
"""
Uso: python scripts/export_tax_report.py --year 2025

Scarica il report IBKR per l'anno indicato e lo salva in data/tax/.
Caricare il file risultante su MoneyViz o consegnarlo al commercialista.
"""
import argparse
from trading.reporting.flex_query import download_flex_report

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, required=True, help="Anno fiscale da esportare")
    args = parser.parse_args()

    path = download_flex_report(args.year)
    print(f"\n✅ Report salvato: {path}")
    print("\nProssimi passi:")
    print(f"  1. Caricare {path.name} su https://moneyviz.it (oppure su tassetrading.it)")
    print("  2. Il tool genera automaticamente Quadro RT e Quadro RW precompilati")
    print("  3. Verificare con commercialista e inviare Modello Redditi PF entro 31 ottobre")
    print("  4. Pagare imposte (26% plusvalenze nette + IVAFE 0.2%) entro 30 giugno")
```

---

## 14. Monitoring e Alerting

### Telegram Alerts (`notifications/telegram.py`)
```python
# src/trading/notifications/telegram.py
"""
Invia notifiche critiche su Telegram.
Categorie:
  - INFO: trade eseguiti, report giornaliero
  - WARNING: risk block, connessione instabile
  - CRITICAL: errori fatali, posizioni non chiuse a fine giornata
"""
import telegram
from trading.config import settings

bot = telegram.Bot(token=settings.TELEGRAM_BOT_TOKEN)

async def send(message: str, level: str = "INFO"):
    prefix = {"INFO": "ℹ️", "WARNING": "⚠️", "CRITICAL": "🚨"}.get(level, "📢")
    await bot.send_message(
        chat_id=settings.TELEGRAM_CHAT_ID,
        text=f"{prefix} *TRADING BOT*\n{message}",
        parse_mode="Markdown"
    )

async def send_daily_report(date: str, realized_pnl: float, num_trades: int, portfolio_value: float):
    msg = (
        f"📊 *Report {date}*\n"
        f"P&L realizzato: `${realized_pnl:+.2f}`\n"
        f"Trade eseguiti: `{num_trades}`\n"
        f"Valore portafoglio: `${portfolio_value:,.2f}`"
    )
    await send(msg)
```

### Metriche Prometheus
Esporre le seguenti metriche su `/metrics` (porta 8000):
- `trading_pnl_daily_usd` — P&L giornaliero
- `trading_open_positions_count` — posizioni aperte
- `trading_orders_total{status}` — ordini per status
- `ibkr_connection_status` — 1=connesso, 0=disconnesso
- `trading_daily_loss_usd` — perdita giornaliera (per monitor del limite)

---

## 15. Sicurezza

### Credenziali
- **Mai** nel codice, **mai** in `.env` committato su Git
- Usare un secret manager: AWS Secrets Manager, HashiCorp Vault, o variabili d'ambiente del VPS
- Il file `/etc/trading/credentials.env` deve avere permessi `600` e owner `trader`

### Rete
- IB Gateway espone la porta 4002 **solo su localhost** (`127.0.0.1`, non `0.0.0.0`)
- Firewall (ufw): aprire solo SSH (22), porta metrics Prometheus (8000), nient'altro
- Accesso al VPS solo via SSH con chiave pubblica (no password)

### Account IBKR
- Abilitare autenticazione a due fattori
- Impostare IP whitelist nel portale IBKR (solo l'IP del VPS)
- Usare account paper per sviluppo e test, live solo per produzione
- Impostare in IBKR: "Trusted IPs" → aggiungere l'IP del VPS

### Rotazione credenziali
- Cambiare password IBKR ogni 90 giorni (aggiornare `credentials.env` e riavviare service)

---

## 16. Deploy — Sequenza di Comandi

```bash
# 1. Setup utente dedicato (no root per il bot)
adduser trader
usermod -aG sudo trader

# 2. Clone repository
su - trader
git clone https://github.com/tuoorg/trading-bot.git ~/trading-bot
cd ~/trading-bot

# 3. Virtual environment Python
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 4. Setup PostgreSQL
sudo -u postgres psql -c "CREATE USER trader WITH PASSWORD 'strongpassword';"
sudo -u postgres psql -c "CREATE DATABASE trading OWNER trader;"
alembic upgrade head   # applica migrations

# 5. File credenziali
sudo mkdir /etc/trading
sudo cp .env.example /etc/trading/credentials.env
sudo nano /etc/trading/credentials.env   # compilare
sudo chmod 600 /etc/trading/credentials.env
sudo chown trader:trader /etc/trading/credentials.env

# 6. Install e avvio IB Gateway + IBC (vedi sezione 4)
sudo systemctl enable ibgateway
sudo systemctl start ibgateway
sudo systemctl status ibgateway   # verificare che sia UP

# 7. Avvio Trading Bot
sudo cp deploy/trading-bot.service /etc/systemd/system/
sudo systemctl enable trading-bot
sudo systemctl start trading-bot
sudo systemctl status trading-bot

# 8. Verifica log
journalctl -u trading-bot -f
```

---

## 17. Testing Plan

### Paper Trading (obbligatorio prima del live)
1. Configurare `IBKR_PORT=4001` (porta paper account)
2. Eseguire il bot per almeno **2 settimane** in paper
3. Verificare: ordini eseguiti correttamente, stop loss attivati, P&L coerente col database, report giornalieri Telegram, reconnessione automatica dopo restart IB Gateway delle 18:00

### Checklist pre-live
- [ ] IB Gateway si avvia in automatico dopo reboot VPS
- [ ] Bot si riconnette automaticamente se IB Gateway si disconnette
- [ ] Risk manager blocca correttamente quando si supera daily loss limit
- [ ] Stop loss viene piazzato automaticamente ad ogni BUY
- [ ] `flatten_all_positions()` funziona correttamente (testare in paper)
- [ ] Flex Report export genera file XML valido
- [ ] Telegram alerts funzionanti
- [ ] PostgreSQL salva ogni trade con exec_id univoco

### Unit Tests prioritari
```
tests/unit/test_risk_manager.py    — logica di blocco
tests/unit/test_position_sizing.py — calcolo shares
tests/unit/test_order_manager.py   — costruzione ordini IBKR
tests/integration/test_ibkr_connection.py — connessione paper account
```

---

## 18. Considerazioni Fiscali per il Dichiarativo (Riepilogo Operativo)

| Cosa | Quando | Come |
|---|---|---|
| Scarica Flex Report | Gennaio dell'anno dopo | Script `export_tax_report.py --year XXXX` |
| Importa su MoneyViz o tool equivalente | Febbraio-Aprile | Upload XML su [moneyviz.it](https://moneyviz.it) |
| Compila Quadro RT (plusvalenze 26%) | Aprile-Ottobre | Generato automaticamente dal tool |
| Compila Quadro RW (monitoraggio + IVAFE 0,2%) | Aprile-Ottobre | Generato automaticamente dal tool |
| Paga imposte via F24 | Entro 30 giugno | Con proroga al 30 luglio (+0,4%) |
| Invia Modello Redditi PF | Entro 31 ottobre | Tramite CAF o commercialista |

**Nota IVAFE:** si paga lo 0,2% sul valore del conto IBKR al 31 dicembre. Con trading frequente, tenere il conto con solo il capitale operativo necessario — non lasciare liquidità inattiva che incrementa la base IVAFE senza motivo.

---

## 19. Riferimenti e Link Utili

| Risorsa | URL |
|---|---|
| IB Gateway download | https://www.interactivebrokers.com/en/trading/ibgateway-stable.php |
| IBC (auto-login) | https://github.com/IbcAlpha/IBC |
| ib_async library | https://github.com/ib-api-reloaded/ib_async |
| IBKR TWS API docs | https://ibkrcampus.com/ibkr-api-page/trader-workstation-api/ |
| IBKR Web API (REST) | https://ibkrcampus.com/ibkr-api-page/webapi-doc/ |
| IBKR Flex Web Service | https://www.interactivebrokers.com/en/software/am/am/reports/flex_web_service_version_3.htm |
| IBKR Error Codes | https://ibkrcampus.com/ibkr-api-page/tws-api-doc/#error-codes |
| MoneyViz (dichiarazione) | https://moneyviz.it |
| TasseTrading (commercialista) | https://www.tassetrading.it |

---

*Documento generato per handoff a Claude Code — versione 1.0 — Giugno 2026*
*Regime fiscale: dichiarativo IBKR. Non costituisce consulenza fiscale o finanziaria.*
