# Automated Trading System — Handoff Part 4: Implementazioni Mancanti

*Questo documento completa i riferimenti non ancora implementati nei Part 1-3.*

---

## 1. `db/repository.py` — Tutte le operazioni DB

Questo modulo è il punto di accesso unico al database. Nessun altro modulo esegue query SQL direttamente.

```python
# src/trading/db/repository.py
"""
Repository pattern: tutte le operazioni DB centralizzate qui.
Nessun altro modulo esegue query SQL direttamente.
"""
from datetime import date, datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select, func, and_
from loguru import logger

from trading.config import settings
from trading.db.models import Base, Trade, Position, Signal, DailyPnL

# ── Engine e Session factory ──────────────────────────────────────────────────

engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    echo=False,
    pool_size=5,
    max_overflow=10,
)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def init_db():
    """Crea le tabelle se non esistono. Chiamato all'avvio del bot."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database inizializzato")


# ── Context manager per le sessioni ──────────────────────────────────────────

class db_session:
    """
    Uso:
        async with db_session() as session:
            session.add(...)
            await session.commit()
    """
    async def __aenter__(self) -> AsyncSession:
        self._session = AsyncSessionLocal()
        return self._session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self._session.rollback()
        else:
            await self._session.commit()
        await self._session.close()


# ── Trade ─────────────────────────────────────────────────────────────────────

async def save_trade(
    ibkr_order_id: int,
    ibkr_exec_id: str,
    symbol: str,
    side: str,
    quantity: float,
    fill_price: float,
    commission: float,
    exchange: str,
    strategy_name: str,
    currency: str = "USD",
) -> Trade:
    """
    Salva un fill. Idempotente: se exec_id già esiste, non duplica.
    exec_id IBKR è globalmente univoco — usarlo come chiave di idempotenza.
    """
    async with db_session() as session:
        # Controlla duplicato
        existing = await session.execute(
            select(Trade).where(Trade.ibkr_exec_id == ibkr_exec_id)
        )
        if existing.scalar_one_or_none():
            logger.debug(f"Trade già salvato: execId={ibkr_exec_id}")
            return

        trade = Trade(
            ibkr_order_id=ibkr_order_id,
            ibkr_exec_id=ibkr_exec_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            fill_price=fill_price,
            commission=commission,
            currency=currency,
            exchange=exchange,
            strategy_name=strategy_name,
            executed_at=datetime.now(timezone.utc),
        )
        session.add(trade)
        logger.info(f"TRADE SAVED: {side} {quantity} {symbol} @ ${fill_price:.2f}")
        return trade


async def get_trades_for_year(year: int) -> list[Trade]:
    """Tutti i trade di un anno — usato per export fiscale."""
    async with db_session() as session:
        result = await session.execute(
            select(Trade).where(
                and_(
                    Trade.executed_at >= datetime(year, 1, 1, tzinfo=timezone.utc),
                    Trade.executed_at < datetime(year + 1, 1, 1, tzinfo=timezone.utc),
                )
            ).order_by(Trade.executed_at)
        )
        return result.scalars().all()


# ── Position ──────────────────────────────────────────────────────────────────

async def upsert_position(
    symbol: str,
    quantity: float,
    avg_cost: float,
    current_price: Optional[float] = None,
    unrealized_pnl: Optional[float] = None,
):
    """Aggiorna o crea la posizione. Chiamato dopo ogni fill e periodicamente."""
    async with db_session() as session:
        result = await session.execute(
            select(Position).where(Position.symbol == symbol)
        )
        pos = result.scalar_one_or_none()

        if pos is None:
            pos = Position(symbol=symbol)
            session.add(pos)

        pos.quantity      = quantity
        pos.avg_cost      = avg_cost
        pos.current_price = current_price
        pos.unrealized_pnl = unrealized_pnl
        pos.updated_at    = datetime.now(timezone.utc)


async def get_open_positions() -> list[Position]:
    """Tutte le posizioni con quantità != 0."""
    async with db_session() as session:
        result = await session.execute(
            select(Position).where(Position.quantity != 0)
        )
        return result.scalars().all()


async def get_open_positions_count() -> int:
    """Conteggio posizioni aperte — usato dal RiskManager."""
    async with db_session() as session:
        result = await session.execute(
            select(func.count()).select_from(Position).where(Position.quantity != 0)
        )
        return result.scalar_one()


async def clear_position(symbol: str):
    """Segna una posizione come chiusa (quantity=0)."""
    async with db_session() as session:
        result = await session.execute(
            select(Position).where(Position.symbol == symbol)
        )
        pos = result.scalar_one_or_none()
        if pos:
            pos.quantity = 0
            pos.unrealized_pnl = 0


# ── Signal ────────────────────────────────────────────────────────────────────

async def save_signal(
    symbol: str,
    strategy_name: str,
    direction: str,
    strength: float,
    reason: str,
    acted_upon: str = "NO",
) -> Signal:
    """Salva ogni segnale generato — per audit e analisi backtest post-live."""
    async with db_session() as session:
        signal = Signal(
            symbol=symbol,
            strategy_name=strategy_name,
            direction=direction,
            strength=strength,
            reason=reason,
            acted_upon=acted_upon,
            generated_at=datetime.now(timezone.utc),
        )
        session.add(signal)
        return signal


# ── Daily P&L ─────────────────────────────────────────────────────────────────

async def get_today_pnl() -> dict:
    """
    Calcola il P&L realizzato di oggi sommando i trade del giorno.
    Usato dal RiskManager (daily loss limit) e dall'EOD report.
    """
    today_start = datetime.combine(date.today(), datetime.min.time()).replace(tzinfo=timezone.utc)

    async with db_session() as session:
        # Somma per BUY e SELL separatamente
        result = await session.execute(
            select(
                Trade.side,
                func.sum(Trade.quantity * Trade.fill_price).label("total_value"),
                func.sum(Trade.commission).label("total_commission"),
                func.count().label("count"),
            )
            .where(Trade.executed_at >= today_start)
            .group_by(Trade.side)
        )
        rows = result.all()

        buy_value  = next((r.total_value for r in rows if r.side == "BUY"), 0) or 0
        sell_value = next((r.total_value for r in rows if r.side == "SELL"), 0) or 0
        commissions = sum(r.total_commission for r in rows if r.total_commission) or 0
        num_trades  = sum(r.count for r in rows)

        # P&L grezzo = incassi SELL - esborsi BUY
        # (approssimazione — il calcolo esatto richiede matching FIFO/LIFO)
        realized_pnl = sell_value - buy_value - commissions

        return {
            "realized": realized_pnl,
            "commissions": commissions,
            "num_trades": num_trades,
        }


async def get_daily_pnl() -> float:
    """Shortcut per RiskManager: solo il float del P&L odierno."""
    data = await get_today_pnl()
    return data["realized"]


async def save_daily_pnl(
    realized_pnl: float,
    commissions: float,
    num_trades: int,
    ending_portfolio_value: float,
):
    """Snapshot giornaliero — chiamato dall'EOD job."""
    today_str = str(date.today())
    async with db_session() as session:
        result = await session.execute(
            select(DailyPnL).where(DailyPnL.date == today_str)
        )
        record = result.scalar_one_or_none()

        if record is None:
            record = DailyPnL(date=today_str)
            session.add(record)

        record.realized_pnl          = realized_pnl
        record.commissions            = commissions
        record.num_trades             = num_trades
        record.ending_portfolio_value = ending_portfolio_value
```

---

## 2. Alembic — Setup e Prima Migration

### 2.1 Inizializzazione

```bash
cd /home/trader/trading-bot
source .venv/bin/activate

# Inizializza alembic
alembic init src/trading/db/migrations

# Questo crea:
# alembic.ini           → file configurazione principale
# src/trading/db/migrations/
#   env.py              → script di migrazione (da modificare)
#   versions/           → directory dove vanno le migration
```

### 2.2 Configurazione `alembic.ini`

```ini
# alembic.ini — modifica queste righe:
[alembic]
script_location = src/trading/db/migrations

# Non mettere la URL qui (viene da env var in env.py)
sqlalchemy.url =
```

### 2.3 Configurazione `src/trading/db/migrations/env.py`

```python
# src/trading/db/migrations/env.py
import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

# Importa i modelli per autodetect
from trading.db.models import Base
from trading.config import settings

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Imposta la URL dal settings
config.set_main_option(
    "sqlalchemy.url",
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
)

target_metadata = Base.metadata


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations():
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online():
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### 2.4 Comandi Alembic

```bash
# Genera la prima migration (autodetect dai modelli)
alembic revision --autogenerate -m "initial_schema"

# Applica la migration al DB
alembic upgrade head

# Verifica stato
alembic current

# Rollback di una migration
alembic downgrade -1

# Workflow normale dopo modifiche ai modelli:
# 1. Modifica models.py
# 2. alembic revision --autogenerate -m "descrizione_cambio"
# 3. Controlla il file generato in migrations/versions/
# 4. alembic upgrade head
```

---

## 3. `broker/market_data.py` — Loop Real-Time Completo

```python
# src/trading/broker/market_data.py
"""
Gestisce l'intero ciclo di vita dei dati di mercato:
- Warmup: dati storici all'apertura del mercato
- Real-time: stream di barre 5-second durante il trading
- Aggregazione: accumulo in DataFrame pandas con features calcolate
- Distribuzione: notifica le strategie ad ogni nuovo bar completato
"""
import asyncio
import pandas as pd
from datetime import datetime, timezone
from typing import Callable, Awaitable
from ib_async import Stock, RealTimeBar
from loguru import logger

from trading.broker.client import IBClient
from trading.features.pipeline import compute_features
from trading.config import settings


# Tipo del callback che le strategie registrano per ricevere i bar
BarCallback = Callable[[str, pd.DataFrame], Awaitable[None]]


class MarketDataManager:
    def __init__(self, ib_client: IBClient):
        self.ib = ib_client.ib
        self._bars_5s:  dict[str, list[dict]] = {}    # buffer barre 5s raw
        self._bars_agg: dict[str, pd.DataFrame] = {}  # barre aggregate su timeframe
        self._callbacks: list[BarCallback] = []
        self._subscriptions: dict[str, object] = {}    # symbol → subscription handle
        self._target_bar_seconds = 300                 # 5 minuti = 300 secondi

    def register_callback(self, callback: BarCallback):
        """Le strategie chiamano questo per ricevere ogni nuovo bar completato."""
        self._callbacks.append(callback)

    async def warmup(self, symbol: str, n_bars: int = 100):
        """
        Scarica n_bars barre storiche di 5 minuti prima di avviare il real-time.
        Deve essere chiamato prima di subscribe() per ogni simbolo.
        """
        from trading.broker.market_data import MarketDataManager
        from ib_async import Stock

        logger.info(f"Warmup {symbol}: scarico {n_bars} barre storiche...")
        contract = Stock(symbol, "SMART", "USD")

        # Calcola duration necessaria
        days_needed = max(1, (n_bars * 5) // 390 + 1)   # 390 minuti per sessione
        duration = f"{days_needed} D"

        bars = await self.ib.reqHistoricalDataAsync(
            contract,
            endDateTime="",
            durationStr=duration,
            barSizeSetting="5 mins",
            whatToShow="TRADES",
            useRTH=True,
        )

        if not bars:
            logger.error(f"Warmup fallito per {symbol}: nessun dato")
            return

        df = pd.DataFrame([{
            "timestamp": b.date,
            "open":   b.open,
            "high":   b.high,
            "low":    b.low,
            "close":  b.close,
            "volume": b.volume,
        } for b in bars[-n_bars:]])  # prendi solo gli ultimi n_bars
        df.set_index("timestamp", inplace=True)

        # Calcola features sull'intero storico di warmup
        self._bars_agg[symbol] = compute_features(df)
        self._bars_5s[symbol] = []

        logger.info(f"Warmup {symbol} completato: {len(df)} barre disponibili")

    async def subscribe(self, symbol: str):
        """
        Avvia lo stream di barre real-time a 5 secondi per un simbolo.
        Aggrega le barre 5s in barre da 5 minuti.
        Chiama i callback registrati ad ogni bar 5-min completato.
        """
        if symbol in self._subscriptions:
            logger.warning(f"Già sottoscritto a {symbol}")
            return

        contract = Stock(symbol, "SMART", "USD")

        # reqRealTimeBars ritorna un BarList con updateEvent
        bar_list = self.ib.reqRealTimeBars(contract, 5, "TRADES", False)
        bar_list.updateEvent += lambda bars, has_new: asyncio.ensure_future(
            self._on_realtime_bar(symbol, bars[-1] if bars else None)
        )

        self._subscriptions[symbol] = bar_list
        logger.info(f"Sottoscritto a real-time bars: {symbol}")

    async def _on_realtime_bar(self, symbol: str, bar: RealTimeBar):
        """
        Callback interno per ogni barra da 5 secondi.
        Accumuliamo 60 barre (60 × 5s = 300s = 5min) e poi
        emettiamo una barra aggregata da 5 minuti ai callback.
        """
        if bar is None:
            return

        buf = self._bars_5s.setdefault(symbol, [])
        buf.append({
            "open":   bar.open,
            "high":   bar.high,
            "low":    bar.low,
            "close":  bar.close,
            "volume": bar.volume,
            "ts":     bar.time,
        })

        # Ogni 60 barre da 5 secondi = 1 bar da 5 minuti
        bars_per_period = self._target_bar_seconds // 5
        if len(buf) < bars_per_period:
            return

        # Aggrega le 60 barre in una da 5 minuti
        period = buf[-bars_per_period:]
        aggregated = {
            "timestamp": period[0]["ts"],
            "open":   period[0]["open"],
            "high":   max(b["high"] for b in period),
            "low":    min(b["low"]  for b in period),
            "close":  period[-1]["close"],
            "volume": sum(b["volume"] for b in period),
        }

        # Svuota il buffer (rolling: mantieni overlap se necessario)
        self._bars_5s[symbol] = []

        # Aggiorna il DataFrame storico
        if symbol not in self._bars_agg:
            logger.warning(f"Nessun warmup per {symbol} — skip bar")
            return

        new_row = pd.DataFrame([aggregated]).set_index("timestamp")
        self._bars_agg[symbol] = pd.concat([self._bars_agg[symbol], new_row]).tail(500)

        # Ricalcola le feature sull'intero DataFrame aggiornato
        df_with_features = compute_features(self._bars_agg[symbol])

        # Notifica tutte le strategie registrate
        for callback in self._callbacks:
            try:
                await callback(symbol, df_with_features)
            except Exception as e:
                logger.error(f"Errore nel callback per {symbol}: {e}")

    async def unsubscribe(self, symbol: str):
        """Cancella la sottoscrizione real-time per un simbolo."""
        if symbol in self._subscriptions:
            self.ib.cancelRealTimeBars(self._subscriptions[symbol])
            del self._subscriptions[symbol]
            logger.info(f"Disiscritto da {symbol}")

    async def unsubscribe_all(self):
        """Chiudi tutte le sottoscrizioni — chiamato a fine giornata."""
        for symbol in list(self._subscriptions.keys()):
            await self.unsubscribe(symbol)

    def get_latest_bar(self, symbol: str) -> dict | None:
        """Ritorna l'ultimo bar aggregato per un simbolo (per exit logic check)."""
        if symbol not in self._bars_agg or self._bars_agg[symbol].empty:
            return None
        row = self._bars_agg[symbol].iloc[-1]
        return row.to_dict()
```

---

## 4. `main.py` — Integrazione Completa con Market Data

Il `main.py` del Part 2 va aggiornato per usare `MarketDataManager` e `repository`:

```python
# Aggiornamenti chiave al TradingBot.start_trading() in main.py

async def start_trading(self):
    """09:30 ET — warmup, subscribe, avvia loop exit check."""
    logger.info("MERCATO APERTO")
    self.market_data = MarketDataManager(self.ib)

    # Registra il callback che processa i bar per tutte le strategie
    self.market_data.register_callback(self._on_new_bar)

    for name, strategy in self.registry.get_all().items():
        universe = await strategy.get_universe(settings.SYMBOLS)
        for symbol in universe:
            # 1. Warmup storico
            await self.market_data.warmup(symbol, n_bars=100)
            await asyncio.sleep(11)  # rispetta pacing IBKR tra richieste
            # 2. Avvia stream real-time
            await self.market_data.subscribe(symbol)

        logger.info(f"[{name}] {len(universe)} simboli attivi")

    # Avvia loop parallelo per exit check delle posizioni aperte
    asyncio.create_task(self._exit_check_loop())

    self._running = True

async def _on_new_bar(self, symbol: str, bars: pd.DataFrame):
    """Callback: nuovo bar 5min disponibile — processa tutte le strategie."""
    if not self._running:
        return

    account = await self.ib.ib.reqAccountSummaryAsync()
    portfolio_value = next(
        (float(v.value) for v in account if v.tag == "NetLiquidation"), 0
    )
    available_cash = next(
        (float(v.value) for v in account if v.tag == "AvailableFunds"), 0
    )
    open_positions = {
        p.contract.symbol: p.position * p.marketPrice
        for p in await self.ib.ib.reqPositionsAsync()
    }

    for name, strategy in self.registry.get_all().items():
        strategy_capital = self.registry.get_capital_for(name, portfolio_value)
        signal = await strategy._signal.generate(symbol, bars)

        if signal:
            await save_signal(symbol, name, signal.direction.value,
                              signal.strength, signal.reason, acted_upon="PENDING")
            approved = await self.risk.validate(signal, strategy_capital)
            if approved:
                success = await strategy.process_bar(
                    symbol, bars, strategy_capital,
                    open_positions, available_cash, self.ib
                )
                acted = "YES" if success else "SKIP"
                await save_signal(symbol, name, signal.direction.value,
                                  signal.strength, signal.reason, acted_upon=acted)

async def _exit_check_loop(self):
    """
    Ogni 30 secondi controlla se le posizioni aperte devono essere chiuse.
    Separato dal loop di entry per non bloccare i nuovi segnali.
    """
    while self._running:
        positions = await get_open_positions()
        for pos in positions:
            bar = self.market_data.get_latest_bar(pos.symbol)
            if bar is None:
                continue

            for name, strategy in self.registry.get_all().items():
                # Calcola bars_held dal DB (semplificato: usa updated_at)
                bars_held = int(
                    (datetime.now(timezone.utc) - pos.updated_at).total_seconds() / 300
                )
                should_exit, reason = strategy.check_exit(
                    pos.symbol, pos.quantity, pos.avg_cost, bar, bars_held
                )
                if should_exit:
                    logger.info(f"EXIT {pos.symbol}: {reason}")
                    from ib_async import Stock, MarketOrder
                    contract = Stock(pos.symbol, "SMART", "USD")
                    action = "SELL" if pos.quantity > 0 else "BUY"
                    order = MarketOrder(action, abs(pos.quantity))
                    self.ib.ib.placeOrder(contract, order)
                    await clear_position(pos.symbol)
                    break  # evita exit multipli dalla stessa posizione

        await asyncio.sleep(30)
```

---

## 5. Fill Handler — Salvataggio Automatico dei Trade

```python
# Da aggiungere in broker/client.py — setup nel startup del bot

def setup_fill_handler(self, on_fill_callback):
    """
    Registra il handler per i fill IBKR.
    Ogni esecuzione (anche parziale) viene intercettata qui.
    """
    self.ib.fillEvent += lambda trade, fill: asyncio.ensure_future(
        self._on_fill(trade, fill, on_fill_callback)
    )

async def _on_fill(self, trade, fill, callback):
    from trading.db.repository import save_trade

    await save_trade(
        ibkr_order_id=fill.execution.orderId,
        ibkr_exec_id=fill.execution.execId,
        symbol=fill.contract.symbol,
        side=fill.execution.side,
        quantity=fill.execution.shares,
        fill_price=fill.execution.price,
        commission=fill.commissionReport.commission if fill.commissionReport else 0.0,
        exchange=fill.execution.exchange,
        strategy_name=getattr(trade.order, "orderRef", "unknown"),
    )

    if callback:
        await callback(fill.contract.symbol, fill.execution.side,
                       fill.execution.shares, fill.execution.price)
```

---

## 6. `.env.example` — Completo

```bash
# .env.example — copiare in .env e compilare

# ── IBKR ──────────────────────────────────────────────────────
IBKR_HOST=127.0.0.1
IBKR_PORT=4002                    # 4002 = live, 4001 = paper
IBKR_CLIENT_ID=1
IBKR_ACCOUNT=U1234567             # Il tuo account ID IBKR

# ── Database ───────────────────────────────────────────────────
DATABASE_URL=postgresql://trader:CAMBIA_QUESTA_PASSWORD@localhost:5432/trading
POSTGRES_PASSWORD=CAMBIA_QUESTA_PASSWORD

# ── Telegram ───────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN=123456789:AAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TELEGRAM_CHAT_ID=987654321

# ── Tax Reporting ──────────────────────────────────────────────
IBKR_FLEX_TOKEN=000000000000      # Da IBKR Account Management → Flex Web Service
IBKR_FLEX_QUERY_ID=000000         # Da IBKR Account Management → Flex Queries

# ── Risk Management ────────────────────────────────────────────
MAX_POSITION_SIZE_USD=10000.0
MAX_DAILY_LOSS_USD=500.0
MAX_OPEN_POSITIONS=5
DEFAULT_STOP_LOSS_PCT=0.02

# ── Strategia ──────────────────────────────────────────────────
# Lista simboli separati da virgola
SYMBOLS=AAPL,MSFT,NVDA,AMZN,GOOGL

# ── Monitoring ─────────────────────────────────────────────────
GRAFANA_PASSWORD=CAMBIA_QUESTA_PASSWORD
```

---

## 7. Struttura File Finale — Riepilogo

```
trading-bot/
├── pyproject.toml
├── alembic.ini
├── .env.example
├── .env                              ← NON in git
├── docker-compose.yml
├── Dockerfile
│
├── src/trading/
│   ├── main.py                       ✅ Part 2 + aggiornamenti Part 4
│   ├── config.py                     ✅ Part 2
│   │
│   ├── broker/
│   │   ├── client.py                 ✅ Part 1 + fill handler Part 4
│   │   ├── market_data.py            ✅ Part 4 (completo)
│   │   └── orders.py                 ✅ Part 1
│   │
│   ├── strategy/
│   │   ├── interfaces.py             ✅ Part 2 (6 interfacce)
│   │   ├── composer.py               ✅ Part 2
│   │   ├── registry.py               ✅ Part 2
│   │   └── implementations/
│   │       └── ma_crossover.py       ✅ Part 2 (esempio completo)
│   │
│   ├── risk/
│   │   ├── manager.py                ✅ Part 1
│   │   └── circuit_breaker.py        ✅ Part 2
│   │
│   ├── db/
│   │   ├── models.py                 ✅ Part 1
│   │   ├── repository.py             ✅ Part 4 (nuovo)
│   │   └── migrations/               ✅ Part 4 (alembic)
│   │       ├── env.py
│   │       └── versions/
│   │
│   ├── features/
│   │   └── pipeline.py               ✅ Part 2
│   │
│   ├── scheduler/
│   │   └── jobs.py                   ✅ Part 1
│   │
│   ├── notifications/
│   │   └── telegram.py               ✅ Part 1
│   │
│   ├── monitoring/
│   │   └── healthcheck.py            ✅ Part 3
│   │
│   └── reporting/
│       └── flex_query.py             ✅ Part 1
│
├── tests/
│   ├── unit/
│   │   ├── test_risk_manager.py
│   │   ├── test_position_sizer.py
│   │   └── test_signal_generator.py
│   └── integration/
│       └── test_ibkr_paper.py
│
├── scripts/
│   ├── export_tax_report.py          ✅ Part 1
│   ├── emergency_flatten.py
│   └── check_positions.py
│
└── data/
    └── historical/                   ← cache parquet (in .gitignore)
```

---

## 8. Prompt per Claude Code

Questo è il prompt da usare per avviare Claude Code con l'intero handoff:

```
Sei incaricato di implementare un sistema di trading algoritmico automatizzato 
su Interactive Brokers per un investitore italiano in regime dichiarativo.

VINCOLI DI BUSINESS:
- Universo: azioni growth senza dividendi — US (NYSE/NASDAQ) + EU (XETRA/Euronext AMS)
- Evitare azioni italiane (Tobin Tax 0,2%) e francesi (TTF ~0,3%)
- Fase 0: account IBKR Paper gratuito, hosting Oracle Cloud Always Free (ARM)
- Fase 2: Vultr NJ x86 con gnzsnz/ib-gateway-docker

Il progetto è completamente specificato in 4 documenti di handoff:
- Part 1: Architettura, stack, IB Gateway, struttura progetto, DB schema, 
          risk manager, order manager, scheduler DUAL SESSION (EU + US),
          tax reporting, costi zero fase iniziale
- Part 2: Pattern strategia multi-interfaccia (6 interfacce), DividendFreeFilter
          con universo EU+US, docker-compose con gnzsnz/ib-gateway-docker,
          IBKR gotcha, backtesting, feature pipeline, repo ecosystem
- Part 3: Hosting Oracle Cloud Always Free ARM, GitHub Actions CI/CD,
          health check, backup PostgreSQL, gestione restart IB Gateway
- Part 4: repository.py completo, setup Alembic, market_data.py loop 
          real-time, fill handler, struttura file finale

[ALLEGA I 4 FILE MD]

REPOS DA USARE:
- ib_async (pip install ib-async) — wrapper IBKR
- gnzsnz/ib-gateway-docker (ghcr.io/gnzsnz/ib-gateway:stable) — IB Gateway dockerizzato
- vectorbt (pip install vectorbt) — backtesting
- exchange-calendars — calendari NYSE + XETRA

Implementa il progetto seguendo ESATTAMENTE le specifiche dei documenti.

Ordine di implementazione:
1. Setup pyproject.toml e struttura directory
2. config.py e models.py
3. db/repository.py e Alembic migrations
4. broker/client.py e broker/market_data.py
5. strategy/interfaces.py, composer.py, registry.py
6. strategy/implementations/ma_crossover.py con DividendFreeFilter
7. features/pipeline.py
8. risk/manager.py e risk/circuit_breaker.py
9. broker/orders.py con get_contract() per EU/US
10. scheduler/jobs.py con dual session EU + US
11. notifications/telegram.py e monitoring/healthcheck.py
12. reporting/flex_query.py
13. main.py con dual session callbacks
14. docker-compose.yml con gnzsnz/ib-gateway-docker + Dockerfile
15. .github/workflows/deploy.yml (GitHub Actions CI/CD)
16. tests/ (unit test per risk manager e signal generator)

Per ogni file: scrivi il codice completo, non placeholder.
Se hai dubbi su un'implementazione, scegli l'opzione più conservativa.
```

---

*Part 4 — Versione 1.0 — Giugno 2026*
*Questo documento completa il handoff. Part 1 + 2 + 3 + 4 = implementazione completa.*
