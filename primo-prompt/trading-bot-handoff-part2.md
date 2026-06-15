# Automated Trading System — Handoff Part 2: Completamento
*Da leggere insieme a Part 1. Copre: pattern strategia multi-interfaccia, gotcha IBKR, entrypoint completo, Docker, market data, backtesting, edge cases.*

---

## 1. Pattern Strategia: Decomposizione in Interfacce Multiple

La classe `BaseStrategy` del Part 1 è utile per casi semplici. Per un sistema estensibile e robusto, la strategia va decomposta in **6 interfacce separate e componibili**. Ogni interfaccia ha una responsabilità unica e può essere swappata indipendentemente.

```
Signal → [IUniverseFilter] → [ISignalGenerator] → [IPositionSizer]
       → [IPortfolioAllocator] → [IExecutionAlgo] → [IExitLogic]
```

### 1.1 Le sei interfacce

```python
# src/trading/strategy/interfaces.py
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
from enum import Enum
import pandas as pd

class Direction(str, Enum):
    LONG  = "LONG"
    SHORT = "SHORT"   # richiede margin account abilitato

@dataclass
class RawSignal:
    """Output di ISignalGenerator — ancora non dimensionato né allocato."""
    symbol:    str
    direction: Direction
    strength:  float          # 0.0–1.0 — confidence del segnale
    reason:    str            # spiegazione human-readable per log/audit
    stop_loss_pct:   Optional[float] = None    # es. 0.02 = 2%
    take_profit_pct: Optional[float] = None
    generated_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class AllocatedSignal(RawSignal):
    """RawSignal + sizing deciso dal PositionSizer e Allocator."""
    target_usd:   float = 0.0    # dollari da impegnare
    shares:       int   = 0      # azioni calcolate
    limit_price:  Optional[float] = None

# ─── INTERFACCIA 1 ───────────────────────────────────────────────
class IUniverseFilter(ABC):
    """
    Decide quali simboli considerare in un dato momento.
    Può filtrare per liquidità, volatilità, notizie, settore, ecc.
    Viene chiamata una volta all'apertura del mercato.
    """
    @abstractmethod
    async def filter(self, candidates: List[str]) -> List[str]:
        """Ritorna sottolista di symbols da monitorare oggi."""
        ...

# ─── INTERFACCIA 2 ───────────────────────────────────────────────
class ISignalGenerator(ABC):
    """
    Genera segnali a partire da dati OHLCV e indicatori.
    Viene chiamata a ogni nuovo bar per ogni simbolo filtrato.
    """
    warmup_bars: int = 50    # barre storiche necessarie prima di generare segnali

    @abstractmethod
    async def generate(self, symbol: str, bars: pd.DataFrame) -> Optional[RawSignal]:
        """
        Args:
            symbol: ticker
            bars: DataFrame con colonne [open, high, low, close, volume, timestamp]
                  ordinato cronologicamente, almeno `warmup_bars` righe
        Returns:
            RawSignal oppure None se nessun segnale
        """
        ...

    async def on_fill(self, symbol: str, direction: Direction, shares: int, price: float):
        """Callback opzionale — aggiorna stato interno dopo fill."""
        pass

# ─── INTERFACCIA 3 ───────────────────────────────────────────────
class IPositionSizer(ABC):
    """
    Decide quanti dollari allocare a un singolo segnale.
    Disaccoppiato dalla logica di segnale: si può cambiare il sizing
    senza toccare la strategia.
    """
    @abstractmethod
    def size(
        self,
        signal: RawSignal,
        portfolio_value: float,
        current_positions: dict[str, float],  # symbol → valore posizione in USD
    ) -> float:
        """Ritorna USD da impegnare per questo segnale."""
        ...

# ─── INTERFACCIA 4 ───────────────────────────────────────────────
class IPortfolioAllocator(ABC):
    """
    Gestisce la coesistenza di più segnali simultanei.
    Decide quali eseguire, in che ordine, se ci sono conflitti.
    Viene chiamata con tutti i segnali dimensionati del bar corrente.
    """
    @abstractmethod
    def allocate(
        self,
        signals: List[AllocatedSignal],
        portfolio_value: float,
        available_cash: float,
    ) -> List[AllocatedSignal]:
        """Ritorna la lista filtrata/ordinata di segnali da eseguire."""
        ...

# ─── INTERFACCIA 5 ───────────────────────────────────────────────
class IExecutionAlgo(ABC):
    """
    Traduce un AllocatedSignal in ordini IBKR.
    Implementazioni: MarketExecution, LimitExecution, TWAPExecution, VWAPExecution.
    """
    @abstractmethod
    async def execute(self, signal: AllocatedSignal, ib_client) -> bool:
        """Invia ordine(i) e ritorna True se inviato con successo."""
        ...

# ─── INTERFACCIA 6 ───────────────────────────────────────────────
class IExitLogic(ABC):
    """
    Decide quando chiudere una posizione aperta.
    Viene chiamata a ogni bar per ogni posizione aperta.
    Separata da ISignalGenerator: una strategia può avere entry e
    exit con logiche completamente diverse.
    """
    @abstractmethod
    def should_exit(
        self,
        symbol: str,
        position_shares: float,
        avg_entry_price: float,
        current_bar: dict,         # {open, high, low, close, volume, timestamp}
        bars_held: int,            # quanti bar è aperta la posizione
    ) -> tuple[bool, str]:
        """
        Returns:
            (True, motivo) se bisogna chiudere
            (False, "") se mantenere
        """
        ...
```

### 1.2 Strategy Composer — mette insieme le sei interfacce

```python
# src/trading/strategy/composer.py
"""
StrategyComposer assembla le 6 interfacce in un flusso completo.
Non contiene logica di trading: è solo il collante.
"""
from trading.strategy.interfaces import (
    IUniverseFilter, ISignalGenerator, IPositionSizer,
    IPortfolioAllocator, IExecutionAlgo, IExitLogic,
    RawSignal, AllocatedSignal
)
from typing import List
import pandas as pd
from loguru import logger

class StrategyComposer:
    def __init__(
        self,
        name: str,
        universe_filter:    IUniverseFilter,
        signal_generator:   ISignalGenerator,
        position_sizer:     IPositionSizer,
        portfolio_allocator: IPortfolioAllocator,
        execution_algo:     IExecutionAlgo,
        exit_logic:         IExitLogic,
    ):
        self.name = name
        self._universe  = universe_filter
        self._signal    = signal_generator
        self._sizer     = position_sizer
        self._allocator = portfolio_allocator
        self._executor  = execution_algo
        self._exit      = exit_logic

    async def get_universe(self, candidates: List[str]) -> List[str]:
        return await self._universe.filter(candidates)

    async def process_bar(
        self,
        symbol: str,
        bars: pd.DataFrame,
        portfolio_value: float,
        current_positions: dict,
        available_cash: float,
        ib_client,
    ) -> bool:
        """
        Chiamato a ogni bar per ogni simbolo dell'universo.
        Ritorna True se un ordine è stato inviato.
        """
        # 1. Genera segnale
        signal: RawSignal | None = await self._signal.generate(symbol, bars)
        if signal is None:
            return False

        # 2. Dimensiona
        target_usd = self._sizer.size(signal, portfolio_value, current_positions)
        if target_usd <= 0:
            logger.debug(f"[{self.name}] {symbol}: sizer ha ritornato 0")
            return False

        # 3. Alloca (qui con un solo segnale, ma il composer può riceverne multipli)
        current_price = bars.iloc[-1]["close"]
        shares = int(target_usd / current_price)
        allocated = AllocatedSignal(
            **{k: v for k, v in signal.__dict__.items()},
            target_usd=target_usd,
            shares=shares,
        )
        approved = self._allocator.allocate([allocated], portfolio_value, available_cash)
        if not approved:
            return False

        # 4. Esegui
        return await self._executor.execute(approved[0], ib_client)

    def check_exit(
        self, symbol: str, shares: float, avg_price: float,
        current_bar: dict, bars_held: int
    ) -> tuple[bool, str]:
        return self._exit.should_exit(symbol, shares, avg_price, current_bar, bars_held)
```

### 1.3 Strategy Registry — gestisce multiple strategie in parallelo

```python
# src/trading/strategy/registry.py
"""
Permette di registrare più strategie e di eseguirle in parallelo.
Ogni strategia può avere il proprio universo, timeframe e allocation.
"""
from typing import Dict
from trading.strategy.composer import StrategyComposer

class StrategyRegistry:
    def __init__(self):
        self._strategies: Dict[str, StrategyComposer] = {}
        self._strategy_capital: Dict[str, float] = {}  # nome → % capitale allocato

    def register(self, composer: StrategyComposer, capital_pct: float):
        """
        Args:
            composer: la strategia composta
            capital_pct: percentuale del portafoglio assegnata (es. 0.4 = 40%)
        """
        assert 0 < capital_pct <= 1.0
        total_allocated = sum(self._strategy_capital.values()) + capital_pct
        assert total_allocated <= 1.0, f"Allocazione totale supera 100%: {total_allocated:.0%}"

        self._strategies[composer.name] = composer
        self._strategy_capital[composer.name] = capital_pct

    def get_all(self) -> Dict[str, StrategyComposer]:
        return self._strategies

    def get_capital_for(self, name: str, total_portfolio: float) -> float:
        return total_portfolio * self._strategy_capital.get(name, 0.0)
```

### 1.4 Esempio concreto: MA Crossover con le 6 interfacce

```python
# src/trading/strategy/implementations/ma_crossover.py
"""
Moving Average Crossover — esempio completo che implementa tutte le interfacce.
Segnale: BUY quando EMA_fast > EMA_slow; EXIT quando cross inverso o stop.
"""
import pandas as pd
import numpy as np
from trading.strategy.interfaces import *
from typing import List, Optional

# ── Universe Filter: no dividendi + liquidità + EU/US ────────────────────────
class DividendFreeFilter(IUniverseFilter):
    """
    Filtra l'universo per:
    1. Zero (o quasi zero) dividend yield — obiettivo: solo azioni growth
    2. Liquidità minima (ADV > soglia)
    3. Exchange ammessi (evita IT e FR per transaction tax)

    Exchange IBKR ammessi (no transaction tax locale):
      SMART / ISLAND / ARCA  → US (NYSE, NASDAQ)
      IBIS                   → XETRA (Germania) — nessuna transaction tax
      AEB                    → Euronext Amsterdam (Olanda) — nessuna transaction tax
    Exchange da evitare:
      BVME / MTAA            → Borsa Italiana (Tobin Tax 0,2%)
      SBF / EPA              → Euronext Paris (TTF ~0,3% su cap >1B€)
    """

    ALLOWED_EXCHANGES = {"SMART", "ISLAND", "ARCA", "IBIS", "AEB"}

    # Lista curata di azioni growth senza dividendi — da aggiornare periodicamente
    # US: big tech, AI, growth
    US_UNIVERSE = [
        "NVDA", "META", "GOOGL", "AMZN", "TSLA",
        "AMD",  "CRM",  "SNOW",  "PLTR", "NET",
        "DDOG", "MDB",  "CRWD",  "PANW", "COIN",
    ]
    # EU: XETRA (Germania) + Euronext Amsterdam — growth, no dividendi significativi
    EU_UNIVERSE = [
        # XETRA (Exchange: IBIS, Currency: EUR)
        "SAP",   # SAP SE — software enterprise
        "IFX",   # Infineon — semiconduttori
        "AIXA",  # Aixtron — semiconduttori
        "SRT3",  # Sartorius — biotech equipment
        # Euronext Amsterdam (Exchange: AEB, Currency: EUR)
        "ASML",  # ASML — litografia chip (no dividendo significativo per il prezzo)
        "ADYEN", # Adyen — pagamenti digitali
        "BESI",  # BE Semiconductor — semiconduttori
    ]

    def __init__(self, include_eu: bool = True, min_adv_usd: float = 10_000_000):
        self.include_eu  = include_eu
        self.min_adv     = min_adv_usd
        self._universe   = self.US_UNIVERSE + (self.EU_UNIVERSE if include_eu else [])

    async def filter(self, candidates: list[str]) -> list[str]:
        """
        Ritorna solo i simboli della lista curata.
        In produzione: aggiungere check dinamico su dividend yield via
        reqFundamentalData o provider dati (es. yfinance per screening offline).
        """
        allowed = set(self._universe)
        return [s for s in candidates if s in allowed]


def get_contract(symbol: str):
    """
    Ritorna il contratto IBKR corretto in base al simbolo.
    I simboli EU usano exchange e valuta specifici.
    """
    from ib_async import Stock

    EU_XETRA      = {"SAP", "IFX", "AIXA", "SRT3"}
    EU_EURONEXT_AMS = {"ASML", "ADYEN", "BESI"}

    if symbol in EU_XETRA:
        return Stock(symbol, "IBIS", "EUR")
    elif symbol in EU_EURONEXT_AMS:
        return Stock(symbol, "AEB", "EUR")
    else:
        return Stock(symbol, "SMART", "USD")

# ── Signal Generator: EMA crossover ─────────────────────────────────────────
class EMACrossoverSignal(ISignalGenerator):
    warmup_bars = 60  # minimo per calcolare EMA lenta

    def __init__(self, fast: int = 10, slow: int = 50):
        self.fast = fast
        self.slow = slow
        self._prev_cross: dict[str, str] = {}  # symbol → "above" | "below"

    async def generate(self, symbol: str, bars: pd.DataFrame) -> Optional[RawSignal]:
        if len(bars) < self.slow:
            return None

        close = bars["close"]
        ema_fast = close.ewm(span=self.fast, adjust=False).mean()
        ema_slow = close.ewm(span=self.slow, adjust=False).mean()

        curr_fast, curr_slow = ema_fast.iloc[-1], ema_slow.iloc[-1]
        prev_fast, prev_slow = ema_fast.iloc[-2], ema_slow.iloc[-2]

        current_cross = "above" if curr_fast > curr_slow else "below"
        prev_cross    = "above" if prev_fast > prev_slow else "below"

        if prev_cross == "below" and current_cross == "above":
            self._prev_cross[symbol] = current_cross
            return RawSignal(
                symbol=symbol,
                direction=Direction.LONG,
                strength=min(abs(curr_fast - curr_slow) / curr_slow * 100, 1.0),
                reason=f"EMA{self.fast} crossed above EMA{self.slow}",
                stop_loss_pct=0.025,
                take_profit_pct=0.05,
            )
        # (aggiungere segnale SHORT per cross inverso se si vuole short selling)
        self._prev_cross[symbol] = current_cross
        return None

# ── Position Sizer: Fixed Fractional (rischia max 1% del portafoglio) ────────
class FixedFractionalSizer(IPositionSizer):
    def __init__(self, risk_per_trade_pct: float = 0.01):
        self.risk_pct = risk_per_trade_pct

    def size(self, signal: RawSignal, portfolio_value: float, positions: dict) -> float:
        if signal.stop_loss_pct is None:
            return portfolio_value * 0.05   # fallback: 5% del portafoglio
        # Dollari a rischio = portfolio × risk_pct
        # Posizione = dollari_a_rischio / stop_loss_pct
        risk_usd = portfolio_value * self.risk_pct
        position_usd = risk_usd / signal.stop_loss_pct
        return min(position_usd, portfolio_value * 0.20)   # max 20% per posizione

# ── Portfolio Allocator: max N posizioni simultanee ──────────────────────────
class MaxPositionsAllocator(IPortfolioAllocator):
    def __init__(self, max_positions: int = 5):
        self.max_pos = max_positions

    def allocate(
        self,
        signals: List[AllocatedSignal],
        portfolio_value: float,
        available_cash: float,
    ) -> List[AllocatedSignal]:
        # Ordina per strength decrescente, prendi i migliori fino al limite
        sorted_signals = sorted(signals, key=lambda s: s.strength, reverse=True)
        result = []
        for s in sorted_signals:
            if len(result) >= self.max_pos:
                break
            if s.target_usd <= available_cash:
                result.append(s)
                available_cash -= s.target_usd
        return result

# ── Execution Algo: Limit order aggressivo (+0.1% rispetto al last) ──────────
class AggressiveLimitExecution(IExecutionAlgo):
    async def execute(self, signal: AllocatedSignal, ib_client) -> bool:
        from ib_async import Stock, LimitOrder, StopOrder
        contract = Stock(signal.symbol, "SMART", "USD")
        ticker = await ib_client.ib.reqTickersAsync(contract)
        last_price = ticker[0].last or ticker[0].close
        if not last_price:
            return False

        limit_price = round(last_price * 1.001, 2)
        shares = int(signal.target_usd / last_price)
        if shares <= 0:
            return False

        order = LimitOrder("BUY", shares, limit_price)
        order.tif = "DAY"
        ib_client.ib.placeOrder(contract, order)

        # Stop loss automatico
        if signal.stop_loss_pct:
            stop_price = round(last_price * (1 - signal.stop_loss_pct), 2)
            stop = StopOrder("SELL", shares, stop_price)
            stop.tif = "GTC"
            ib_client.ib.placeOrder(contract, stop)

        return True

# ── Exit Logic: tempo massimo + trailing stop ─────────────────────────────────
class TimeAndTrailingExit(IExitLogic):
    def __init__(self, max_bars_held: int = 20, trailing_stop_pct: float = 0.03):
        self.max_bars = max_bars_held
        self.trailing_pct = trailing_stop_pct
        self._high_watermark: dict[str, float] = {}

    def should_exit(self, symbol, shares, avg_price, bar, bars_held) -> tuple[bool, str]:
        close = bar["close"]

        # Aggiorna high watermark
        hw = self._high_watermark.get(symbol, avg_price)
        self._high_watermark[symbol] = max(hw, close)

        # Trailing stop
        trailing_stop = self._high_watermark[symbol] * (1 - self.trailing_pct)
        if close < trailing_stop:
            return True, f"Trailing stop: {close:.2f} < {trailing_stop:.2f}"

        # Tempo massimo
        if bars_held >= self.max_bars:
            return True, f"Max bars held ({self.max_bars}) raggiunto"

        return False, ""


# ── Factory: assembla tutto in un StrategyComposer ───────────────────────────
def create_ma_crossover_strategy() -> "StrategyComposer":
    from trading.strategy.composer import StrategyComposer
    return StrategyComposer(
        name="MA_Crossover_v1",
        universe_filter=    DividendFreeFilter(include_eu=True, min_adv_usd=10_000_000),
        signal_generator=   EMACrossoverSignal(fast=10, slow=50),
        position_sizer=     FixedFractionalSizer(risk_per_trade_pct=0.01),
        portfolio_allocator=MaxPositionsAllocator(max_positions=5),
        execution_algo=     AggressiveLimitExecution(),
        exit_logic=         TimeAndTrailingExit(max_bars_held=20, trailing_stop_pct=0.03),
    )
```

---

## 2. Entrypoint Completo (`main.py`)

```python
# src/trading/main.py
"""
Entrypoint del bot. Sequenza di avvio:
1. Init DB e validazione config
2. Connessione IB Gateway (con retry)
3. Registra strategie
4. Avvia scheduler (market open/close)
5. Event loop asyncio — gira finché non viene fermato (SIGTERM/SIGINT)
"""
import asyncio
import signal
from loguru import logger
from trading.config import settings
from trading.broker.client import IBClient
from trading.db.models import Base
from trading.db.repository import init_db
from trading.scheduler.jobs import setup_scheduler
from trading.strategy.registry import StrategyRegistry
from trading.strategy.implementations.ma_crossover import create_ma_crossover_strategy
from trading.notifications.telegram import send
from trading.risk.manager import RiskManager

class TradingBot:
    def __init__(self):
        self.ib = IBClient()
        self.registry = StrategyRegistry()
        self.risk = RiskManager()
        self.scheduler = None
        self._running = False
        self._bar_subscriptions: dict = {}

    async def startup(self):
        logger.info("=== TRADING BOT AVVIO ===")

        # 1. DB
        await init_db()
        logger.info("Database OK")

        # 2. Connessione IBKR
        await self.ib.connect()
        self.ib.ib.errorEvent += self.ib.on_error

        # 3. Verifica account
        account_summary = await self.ib.ib.reqAccountSummaryAsync()
        net_liq = next(
            (float(v.value) for v in account_summary
             if v.tag == "NetLiquidation" and v.currency == "USD"), 0
        )
        logger.info(f"Account: {settings.IBKR_ACCOUNT} | Net Liquidation: ${net_liq:,.2f}")
        await send(f"Bot avviato. Portafoglio: ${net_liq:,.2f}", level="INFO")

        # 4. Registra strategie
        self.registry.register(create_ma_crossover_strategy(), capital_pct=0.80)
        # self.registry.register(create_mean_reversion_strategy(), capital_pct=0.20)
        logger.info(f"Strategie registrate: {list(self.registry.get_all().keys())}")

        # 5. Scheduler
        self.scheduler = setup_scheduler(self)
        self.scheduler.start()

        self._running = True
        logger.info("Bot pronto. Attendo apertura mercato...")

    async def shutdown(self):
        logger.info("=== SHUTDOWN ===")
        self._running = False
        if self.scheduler:
            self.scheduler.shutdown(wait=False)
        await self.ib.disconnect()
        await send("Bot fermato.", level="WARNING")

    # ── Callback scheduler ──────────────────────────────────────────────────
    async def pre_market_check(self):
        """09:25 ET — controlla posizioni residue da sessione precedente."""
        positions = await self.ib.ib.reqPositionsAsync()
        if positions:
            logger.warning(f"Posizioni residue rilevate: {[p.contract.symbol for p in positions]}")
            await send(f"⚠️ Posizioni residue: {len(positions)} simboli", level="WARNING")

    async def start_trading(self):
        """09:30 ET — avvia sottoscrizioni dati real-time e loop barre."""
        logger.info("MERCATO APERTO — avvio trading")
        for name, strategy in self.registry.get_all().items():
            universe = await strategy.get_universe(settings.SYMBOLS)
            logger.info(f"[{name}] Universo: {universe}")
            for symbol in universe:
                await self._subscribe_bars(symbol, strategy)

    async def stop_new_entries(self):
        """15:45 ET — blocca nuovi ingressi, mantieni posizioni esistenti."""
        logger.info("15:45 ET — stop nuovi ingressi")
        self._running = False   # il loop check_exits continua, ma no nuovi segnali

    async def close_intraday_positions(self):
        """15:55 ET — chiudi tutte le posizioni intraday."""
        await self.ib.orders.flatten_all_positions()
        logger.info("Posizioni intraday chiuse")

    async def end_of_day_report(self):
        """16:05 ET — salva P&L e invia report Telegram."""
        from trading.db.repository import get_today_pnl, save_daily_pnl
        pnl = await get_today_pnl()
        account = await self.ib.ib.reqAccountSummaryAsync()
        portfolio_value = next(
            (float(v.value) for v in account if v.tag == "NetLiquidation"), 0
        )
        await save_daily_pnl(pnl["realized"], pnl["commissions"], pnl["num_trades"], portfolio_value)
        from trading.notifications.telegram import send_daily_report
        from datetime import date
        await send_daily_report(str(date.today()), pnl["realized"], pnl["num_trades"], portfolio_value)

    async def handle_gateway_restart(self):
        """18:10 ET — IB Gateway si riavvia automaticamente. Riconnetti."""
        logger.warning("Riconnessione post-restart IB Gateway...")
        await asyncio.sleep(60)   # attendi restart completo
        await self.ib.connect()
        self._running = True
        self.scheduler.start()

    async def _subscribe_bars(self, symbol: str, strategy):
        """Sottoscrivi barre real-time e collega il processing loop."""
        from ib_async import Stock, BarData
        contract = Stock(symbol, "SMART", "USD")
        bars = self.ib.ib.reqRealTimeBars(contract, 5, "TRADES", False)
        # ib_async emette eventi: bars.updateEvent += handler
        # Implementazione completa in broker/market_data.py


async def main():
    bot = TradingBot()

    # Gestione SIGTERM / SIGINT per shutdown pulito
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(bot.shutdown()))

    await bot.startup()

    # Mantieni il processo vivo
    while bot._running or bot.scheduler and bot.scheduler.running:
        await asyncio.sleep(1)

if __name__ == "__main__":
    # Configurazione logging
    logger.add(
        "logs/trading_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="90 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {message}",
    )
    asyncio.run(main())
```

---

## 3. Market Data — Dettagli e Gestione Pacing

### 3.1 Tipi di dati IBKR (scegliere quello giusto)

| Tipo | API call | Uso | Latenza | Costo |
|---|---|---|---|---|
| Real-time bars (5s) | `reqRealTimeBars` | Trading intraday | ~5 sec | Subscription mercato |
| Tick by tick | `reqTickByTick` | HFT / microstructure | < 1 sec | Subscription mercato |
| Market data (L1) | `reqMktData` | Monitor prezzi | Real-time | Subscription mercato |
| Historical bars | `reqHistoricalData` | Warmup, backfill | Batch | Incluso |
| Historical ticks | `reqHistoricalTicks` | Analisi dettagliata | Batch | Incluso |

Per trading algoritmico su timeframe ≥ 5 minuti: usare `reqRealTimeBars` (5 secondi) e aggregare in pandas.

### 3.2 Regole di pacing IBKR (critiche per evitare errori 162)

**Errore 162 = "Historical Market Data Service error message: Historical data request pacing violation"**

Il numero massimo di richieste storiche simultanee è 50. Limiti aggiuntivi da rispettare:

- Max **60 richieste in 10 minuti** per account
- Minimo **10 secondi tra richieste successive** per lo stesso contratto
- Dati intraday (< 1 giorno) disponibili max negli ultimi 6 mesi
- Dati tick disponibili max negli ultimi 90 giorni

```python
# src/trading/broker/market_data.py
"""
Gestisce la cache locale dei dati storici e il pacing IBKR.
Strategia: scarica bulk al pre-market, poi usa solo real-time durante il giorno.
"""
import asyncio
import pandas as pd
from datetime import datetime, timedelta
from loguru import logger
from pathlib import Path

CACHE_DIR = Path("data/historical")

class MarketDataManager:
    def __init__(self, ib_client):
        self.ib = ib_client.ib
        self._request_times: list[datetime] = []  # sliding window pacing
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

    async def _enforce_pacing(self):
        """Rispetta il limite di 60 richieste in 10 minuti."""
        now = datetime.utcnow()
        window = now - timedelta(minutes=10)
        self._request_times = [t for t in self._request_times if t > window]

        if len(self._request_times) >= 55:  # buffer di sicurezza
            wait_time = 10 - (now - self._request_times[0]).total_seconds()
            if wait_time > 0:
                logger.warning(f"Pacing: attendo {wait_time:.1f}s")
                await asyncio.sleep(wait_time)

        self._request_times.append(datetime.utcnow())
        await asyncio.sleep(11)  # 11s tra richieste consecutive (> 10 richiesto)

    async def get_historical_bars(
        self,
        symbol: str,
        bar_size: str = "5 mins",
        duration: str = "5 D",
        use_cache: bool = True,
    ) -> pd.DataFrame:
        """
        Scarica dati storici con pacing automatico e cache su disco.
        
        Bar sizes valide: '1 secs', '5 secs', '10 secs', '15 secs', '30 secs',
                          '1 min', '2 mins', '3 mins', '5 mins', '10 mins',
                          '15 mins', '20 mins', '30 mins', '1 hour', '1 day'
        Duration examples: '1 D', '5 D', '1 W', '1 M', '1 Y'
        """
        cache_key = f"{symbol}_{bar_size.replace(' ', '')}_{duration.replace(' ', '')}"
        cache_file = CACHE_DIR / f"{cache_key}.parquet"

        # Usa cache se aggiornata nelle ultime 4 ore
        if use_cache and cache_file.exists():
            age = datetime.utcnow().timestamp() - cache_file.stat().st_mtime
            if age < 4 * 3600:
                return pd.read_parquet(cache_file)

        from ib_async import Stock
        contract = Stock(symbol, "SMART", "USD")

        await self._enforce_pacing()
        bars = await self.ib.reqHistoricalDataAsync(
            contract,
            endDateTime="",       # vuoto = adesso
            durationStr=duration,
            barSizeSetting=bar_size,
            whatToShow="TRADES",
            useRTH=True,          # solo Regular Trading Hours (09:30-16:00 ET)
            formatDate=2,         # timestamp Unix
        )

        if not bars:
            logger.error(f"Nessun dato storico per {symbol}")
            return pd.DataFrame()

        df = pd.DataFrame([{
            "timestamp": b.date,
            "open":   b.open,
            "high":   b.high,
            "low":    b.low,
            "close":  b.close,
            "volume": b.volume,
        } for b in bars])
        df.set_index("timestamp", inplace=True)
        df.to_parquet(cache_file)
        return df
```

### 3.3 Subscriptions market data IBKR (costo)

⚠️ **Senza subscription attiva, i prezzi real-time sono ritardati di 15 minuti.** Configurare sul portale IBKR:

| Subscription | Costo approx | Necessaria per |
|---|---|---|
| NYSE + AMEX (US Network B+C) | ~$4.50/mese | Azioni NYSE |
| NASDAQ (US Network A) | ~$4.50/mese | Azioni NASDAQ |
| US Equity Snapshot | gratuita | Solo prezzi delayed/snapshot |

Le subscription si compensano automaticamente se le commissioni generate superano una soglia mensile (~$30 su IBKR Pro). Per un bot attivo, spesso le subscription sono effettivamente gratuite.

**Nota IBKR Pro vs IBKR Lite**: usare sempre **IBKR Pro** (commissioni a consumo). IBKR Lite ha zero commissioni ma vende l'order flow (PFOF) e non ha accesso a smart routing. Per trading algoritmico è inaccettabile.

---

## 4. IBKR Gotcha — Lista Completa

### 4.1 nextValidId — obbligatorio per gli ordini

```python
# IBKR richiede che ogni ordine abbia un ID univoco e incrementale.
# ib_async gestisce questo automaticamente, ma da sapere:
# - alla connessione IBKR invia nextValidId via callback
# - NON usare mai lo stesso orderId due volte in una sessione
# - dopo reconnessione, richiedere nuovo nextValidId
next_order_id = self.ib.client.getReqId()  # ib_async gestisce internamente
```

### 4.2 IB Gateway restart giornaliero

**IB Gateway si riavvia automaticamente ogni giorno alle 23:45 ET (05:45 CET).**
Durante il restart (dura ~2-3 minuti) la connessione socket si interrompe.
Il bot DEVE gestire la disconnessione e riconnessione.

```python
# ib_async espone disconnectedEvent
self.ib.disconnectedEvent += self._on_disconnected

async def _on_disconnected(self):
    logger.warning("IB Gateway disconnesso — tentativo riconnessione tra 30s")
    await asyncio.sleep(30)
    await self.ib.connect()   # con retry interno
```

### 4.3 Partial fills

Un ordine può essere eseguito parzialmente (es. BUY 100 AAPL → fill di 60, poi 40).

```python
# ib_async emette fillEvent per ogni fill parziale o totale
self.ib.fillEvent += self._on_fill

def _on_fill(self, trade, fill):
    logger.info(
        f"FILL: {fill.contract.symbol} "
        f"{fill.execution.side} {fill.execution.shares} @ ${fill.execution.price:.2f} "
        f"(cumQty: {fill.execution.cumQty})"
    )
    # Salva ogni fill separatamente nel DB con l'execId univoco
    # execId è il campo `fill.execution.execId` — SEMPRE univoco per IBKR
```

### 4.4 Ordini "ghost" dopo reconnessione

Dopo una reconnessione, IBKR può inviare update di ordini già chiusi.
Sempre verificare lo stato prima di agire:

```python
open_orders = await self.ib.reqOpenOrdersAsync()   # solo ordini realmente aperti
all_trades  = self.ib.trades()   # include storici della sessione
```

### 4.5 reqContractDetails prima del trading

**Verificare sempre che il contratto esista prima di piazzare ordini:**

```python
from ib_async import Stock
contract = Stock("AAPL", "SMART", "USD")
details = await self.ib.reqContractDetailsAsync(contract)
if not details:
    raise ValueError(f"Contratto non trovato: {symbol}")
# details[0].contract contiene il contratto qualificato con conId
# details[0].liquidHours contiene gli orari di trading
```

### 4.6 Market order vs Limit order

⚠️ **Evitare Market Order su azioni con spread ampio o bassa liquidità.**
In paper trading il fill è immediato al last price.
In live trading, uno slippage del 0.5% su ogni trade uccide la profittabilità.
Usare sempre **Limit Order con prezzo aggressivo** (last ± 0.1%).

### 4.7 useRTH=True obbligatorio

Impostare sempre `useRTH=True` (Regular Trading Hours) per:
- `reqHistoricalData`: evita barre pre/post market nel calcolo indicatori
- Ordini: aggiungere `order.outsideRth = False` per non eseguire pre/after-hours

### 4.8 Il contratto SMART per azioni USA

```python
# CORRETTO per azioni USA
Stock("AAPL", "SMART", "USD")    # SMART routing = IBKR sceglie il miglior exchange

# SBAGLIATO (troppo specifico, può fallire se non hai subscription exchange)
Stock("AAPL", "NASDAQ", "USD")
```

### 4.9 Gestione errore 200 (No security definition)

Codice errore 200 = symbol non trovato o non tradeable con questo account.
Può succedere con:
- Ticker non quotato sul mercato richiesto
- Azioni con simbolo cambiato dopo M&A
- Azioni in OTC/Pink Sheets (richiedono configurazione speciale)

### 4.10 Timeout e deadlock

`reqTickersAsync`, `reqHistoricalDataAsync` ecc. possono non rispondere mai se IB Gateway è overloaded o disconnesso. Usare sempre timeout:

```python
try:
    ticker = await asyncio.wait_for(
        self.ib.reqTickersAsync(contract),
        timeout=10.0
    )
except asyncio.TimeoutError:
    logger.error(f"Timeout su reqTickers per {symbol}")
```

### 4.11 Thread safety

`ib_async` è single-threaded (asyncio). **Non chiamare metodi ib da thread diversi.** Se si usa APScheduler o threading, sempre via `asyncio.run_coroutine_threadsafe()`.

### 4.12 Paper Trading vs Live — differenze

| Aspetto | Paper | Live |
|---|---|---|
| Fill price | Al last price, immediato | Dipende da liquidità e spread |
| Commissions | Simulate | Reali |
| Market data | Può essere delayed | Real-time (con subscription) |
| Short selling | Sempre disponibile | Dipende da disponibilità titolo |
| Pattern Day Trader | Non applicato | Non più applicato (regola eliminata giugno 2026) |
| Order rejection | Raro | Può succedere per margin, restrizioni |

---

## 5. PDT Rule — Chiarita (Aggiornamento Giugno 2026)

Il 14 aprile 2026, la SEC ha approvato il piano di FINRA per eliminare la Pattern Day Trader rule, con effetto dal 4 giugno 2026. Il requisito di $25.000 di patrimonio minimo e la soglia dei quattro day trade sono stati rimossi. Un nuovo framework di margin intraday in real-time li sostituisce.

Per i clienti IBKR europei (account IBKR Ireland/Central Europe), la regola PDT non era mai stata applicata. Per i clienti italiani con account IBKR Ireland, **non c'è e non c'è mai stato alcun limite al numero di day trade intraday.**

---

## 6. Gestione Valuta — Investitore EUR che opera in USD

### Il problema
Il conto IBKR di un investitore italiano ha base EUR. Le azioni USA vengono comprate in USD. IBKR gestisce automaticamente il forex, ma bisogna capire il meccanismo.

### Modalità IBKR (scegliere esplicitamente)

**Opzione A — Auto FX Conversion (default)**
IBKR converte automaticamente EUR → USD al momento dell'acquisto.
Ogni conversione ha un piccolo spread (commissione forex implicita ~0.002%).
Semplice ma meno controllato.

**Opzione B — Manuale: tenere saldo USD nel conto**
Comprare USD prima manualmente (`reqContractDetails` per `Cash` contract).
Più controllo ma richiede gestione attiva del saldo valutario.

**Raccomandazione per il bot**: usare **IDA (Integrated Data Access)** di IBKR — impostare il conto in modalità "multi-currency" e lasciare che IBKR gestisca le conversioni automaticamente. Per semplificare la reportistica fiscale, il bot deve registrare il tasso di cambio EUR/USD al momento di ogni trade (campo `execution.exchange` in fill).

```python
# Aggiunta al Trade model per tracking valuta
class Trade(Base):
    # ... campi esistenti ...
    eur_usd_rate = Column(Float)      # tasso al momento dell'esecuzione
    pnl_eur = Column(Float)           # P&L convertito in EUR per dichiarazione
```

### IVAFE e valuta

L'IVAFE si calcola sul valore del conto al 31 dicembre convertito in EUR al tasso di cambio BCE del 31 dicembre. Il bot deve registrare il valore del portafoglio in USD e il tasso EUR/USD ogni fine anno (o meglio ogni fine giornata).

---

## 7. Docker Compose — Configurazione Completa

### Nota architetturale: ARM vs x86

`gnzsnz/ib-gateway-docker` (⭐838, vedi Sezione GitHub Repos) include IB Gateway + IBC + Xvfb in un'unica immagine Docker mantenuta. **Sostituisce completamente la configurazione manuale di IBC e Xvfb** descritta nel Part 1.

| Piattaforma | Approccio |
|---|---|
| **Oracle Cloud ARM (Fase 0/1)** | IB Gateway via Docker con emulazione x86 (`platform: linux/amd64`) oppure installazione manuale come da Part 1. L'emulazione aggiunge ~30% overhead CPU, accettabile per trading non-HFT. |
| **Vultr NJ x86 (Fase 2)** | `gnzsnz/ib-gateway-docker` nativo, zero overhead. |

### `docker-compose.yml`
```yaml
services:
  # ── IB Gateway (sostituisce setup manuale IBC + Xvfb) ──────────────────────
  # Repo: github.com/gnzsnz/ib-gateway-docker (⭐838, multi-arch)
  ib-gateway:
    image: ghcr.io/gnzsnz/ib-gateway:stable
    restart: unless-stopped
    # Su Oracle Cloud ARM: decommentare la riga sotto per emulazione x86
    # platform: linux/amd64
    environment:
      TWS_USERID: ${IBKR_USERNAME}
      TWS_PASSWORD: ${IBKR_PASSWORD}
      TRADING_MODE: ${TRADING_MODE:-paper}   # paper | live
      READ_ONLY_API: "no"
      VNC_SERVER_PASSWORD: ${VNC_PASSWORD}   # per debug remoto via VNC
      RELOGIN_AFTER_SECOND_FACTOR_AUTHENTICATION: "yes"
      # Restart giornaliero alle 23:45 ET (default IBC)
      AUTO_RESTART_TIME: "11:45 PM"
      TWS_SETTINGS_PATH: /home/ibgateway/Jts
    ports:
      - "127.0.0.1:4001:4001"   # API paper
      - "127.0.0.1:4002:4002"   # API live
      - "127.0.0.1:5900:5900"   # VNC (solo localhost, accedi via SSH tunnel)
    volumes:
      - ib_gateway_settings:/home/ibgateway/Jts
    healthcheck:
      test: ["CMD-SHELL", "nc -z localhost 4002 || nc -z localhost 4001"]
      interval: 30s
      timeout: 10s
      retries: 10
      start_period: 60s    # IB Gateway impiega ~60s per avviarsi

  # ── PostgreSQL ──────────────────────────────────────────────────────────────
  postgres:
    image: postgres:15-alpine
    restart: unless-stopped
    environment:
      POSTGRES_DB: trading
      POSTGRES_USER: trader
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "127.0.0.1:5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U trader"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ── Trading Bot ─────────────────────────────────────────────────────────────
  trading-bot:
    build: .
    restart: unless-stopped
    depends_on:
      postgres:
        condition: service_healthy
      ib-gateway:
        condition: service_healthy
    environment:
      IBKR_HOST: ib-gateway          # nome del servizio Docker (no localhost)
      IBKR_PORT: ${IBKR_PORT:-4002}
      IBKR_CLIENT_ID: 1
      IBKR_ACCOUNT: ${IBKR_ACCOUNT}
      DATABASE_URL: postgresql://trader:${POSTGRES_PASSWORD}@postgres:5432/trading
      TELEGRAM_BOT_TOKEN: ${TELEGRAM_BOT_TOKEN}
      TELEGRAM_CHAT_ID: ${TELEGRAM_CHAT_ID}
      IBKR_FLEX_TOKEN: ${IBKR_FLEX_TOKEN}
      IBKR_FLEX_QUERY_ID: ${IBKR_FLEX_QUERY_ID}
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    command: python -m trading.main

  # ── Prometheus + Grafana ────────────────────────────────────────────────────
  prometheus:
    image: prom/prometheus:latest
    restart: unless-stopped
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "127.0.0.1:9090:9090"

  grafana:
    image: grafana/grafana:latest
    restart: unless-stopped
    depends_on: [prometheus]
    ports:
      - "127.0.0.1:3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}

volumes:
  postgres_data:
  grafana_data:
  ib_gateway_settings:    # persistenza settings IB Gateway tra restart
```

> **⚠️ Differenza chiave rispetto al Part 1**: con `gnzsnz/ib-gateway-docker`, il bot si connette a `IBKR_HOST: ib-gateway` (nome del servizio Docker) e non più a `127.0.0.1`. Aggiornare `config.py` di conseguenza.

### `Dockerfile`
```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --no-cache-dir -e "."

COPY src/ ./src/

RUN useradd -m trader && chown -R trader:trader /app
USER trader

CMD ["python", "-m", "trading.main"]
```

---

## 8. `pyproject.toml` — Stack Moderno (Python 3.12 + uv)

uv è il package manager Python standard per il 2026: 10-100x più veloce di pip, drop-in compatible, gestisce Python version management + virtual environments + lockfile in un solo tool.

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "trading-bot"
version = "0.1.0"
requires-python = ">=3.12"        # 3.12 = +15% performance vs 3.11
dependencies = [
    # ── IBKR ──────────────────────────────────────────────────────
    "ib-async>=1.0",               # wrapper IBKR (ib-api-reloaded/ib_async)

    # ── Database ───────────────────────────────────────────────────
    "sqlalchemy>=2.0",
    "alembic>=1.13",
    "asyncpg>=0.29",               # driver PostgreSQL async
    "duckdb>=1.0",                 # analytics veloci su parquet per backtesting

    # ── Config ────────────────────────────────────────────────────
    "pydantic-settings>=2.0",

    # ── Scheduling ────────────────────────────────────────────────
    "apscheduler>=3.10",
    "exchange-calendars>=4.5",     # calendari NYSE, XETRA, Euronext

    # ── Logging ───────────────────────────────────────────────────
    "loguru>=0.7",
    "rich>=13",                    # output terminale colorato per dev

    # ── API / Web ─────────────────────────────────────────────────
    "fastapi>=0.115",              # health check endpoint (sostituisce aiohttp)
    "uvicorn[standard]>=0.30",     # ASGI server per FastAPI
    "httpx>=0.26",                 # HTTP async per Flex Query

    # ── Alerting ──────────────────────────────────────────────────
    "python-telegram-bot>=20",

    # ── Data ──────────────────────────────────────────────────────
    "pandas>=2.1",
    "pandas-ta-classic>=0.3",    # 252 indicatori (RSI, ATR, VWAP, MACD...). Uso: df.ta.rsi()
    "yfinance>=0.2",             # warmup storico senza pacing IBKR
    "numpy>=1.26",
    "pyarrow>=14",                 # parquet per cache dati storici
    "pytz>=2024.1",

    # ── Monitoring ────────────────────────────────────────────────
    "prometheus-client>=0.19",

    # ── CLI ───────────────────────────────────────────────────────
    "typer>=0.12",                 # CLI moderna per script (export fiscale, ecc.)
]

[tool.uv]
dev-dependencies = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pytest-mock>=3.12",
    "ruff>=0.5",
    "mypy>=1.10",
    "vectorbt>=0.26",              # backtesting vectorizzato
    "jupyter>=1.0",
    "matplotlib>=3.8",
    "ipython>=8.0",
]

[tool.hatch.build.targets.wheel]
packages = ["src/trading"]

# ── Tool config ───────────────────────────────────────────────────────────────

[tool.ruff]
line-length = 100
target-version = "py312"
select = ["E", "F", "I", "UP", "B", "SIM"]

[tool.ruff.format]
quote-style = "double"

[tool.mypy]
python_version = "3.12"
strict = false
ignore_missing_imports = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

### Comandi uv (sostituiscono pip ovunque)

```bash
# Setup iniziale (una volta sola)
curl -LsSf https://astral.sh/uv/install.sh | sh   # installa uv
uv sync --all-extras                               # installa tutto (prod + dev)

# Aggiornamento dipendenze
uv add ib-async                    # aggiunge una dipendenza
uv add --dev pytest-cov            # aggiunge una dev dependency
uv sync                            # aggiorna l'ambiente al lockfile

# Esecuzione
uv run python -m trading.main      # avvia il bot
uv run pytest tests/               # test
uv run alembic upgrade head        # migration DB
uv run python scripts/export_tax_report.py --year 2025

# Python version management (no pyenv necessario)
uv python install 3.12
uv python pin 3.12                 # scrive .python-version
```

### Dockerfile con uv

```dockerfile
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# Installa dipendenze con uv (cache layer separato)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Codice sorgente
COPY src/ ./src/

RUN useradd -m trader && chown -R trader:trader /app
USER trader

CMD ["uv", "run", "python", "-m", "trading.main"]
```

### Rimpiazzo `features/pipeline.py` con pandas-ta

```python
# src/trading/features/pipeline.py — versione moderna con pandas-ta
import pandas as pd
import pandas_ta as ta

def compute_features(bars: pd.DataFrame) -> pd.DataFrame:
    """
    Calcola 130+ indicatori con una sola chiamata a pandas-ta.
    Molto più robusto e testato della pipeline manuale.
    """
    df = bars.copy()

    # Strategia: usa ta.Strategy per calcolare solo gli indicatori necessari
    strategy = ta.Strategy(
        name="trading_bot",
        ta=[
            {"kind": "ema",  "length": 9},
            {"kind": "ema",  "length": 21},
            {"kind": "ema",  "length": 50},
            {"kind": "sma",  "length": 200},
            {"kind": "rsi",  "length": 14},
            {"kind": "rsi",  "length": 7},
            {"kind": "atr",  "length": 14},
            {"kind": "bbands", "length": 20, "std": 2},
            {"kind": "vwap"},
            {"kind": "macd", "fast": 12, "slow": 26, "signal": 9},
            {"kind": "stoch", "k": 14, "d": 3},
        ]
    )
    df.ta.strategy(strategy)

    # Pulizia nomi colonne (pandas-ta usa nomi tipo EMA_9, RSI_14)
    df.columns = [c.lower() for c in df.columns]

    # Aggiungi feature custom non disponibili in pandas-ta
    df["vol_ratio"]   = df["volume"] / df["volume"].rolling(20).mean()
    df["gap_pct"]     = (df["open"] - df["close"].shift(1)) / df["close"].shift(1)

    return df
```

---

## 9. Market Holidays e Calendario Borse

**IBKR rifiuta gli ordini nei giorni di chiusura.** Il bot deve sapere se il mercato è aperto prima di connettersi e iniziare.

```python
# pip install exchange-calendars
# src/trading/utils/calendar.py
import exchange_calendars as xcals
from datetime import date, datetime
import pytz

NYSE = xcals.get_calendar("XNYS")   # NYSE calendar
ET = pytz.timezone("America/New_York")

def is_market_open_today() -> bool:
    """True se oggi NYSE è aperto."""
    today = date.today()
    return NYSE.is_session(str(today))

def get_next_open() -> datetime:
    """Restituisce il prossimo open del NYSE in UTC."""
    sessions = NYSE.sessions_in_range(str(date.today()), str(date.today().replace(year=date.today().year + 1)))
    next_session = sessions[0] if sessions else None
    if next_session is None:
        raise RuntimeError("Nessuna sessione trovata")
    open_time = NYSE.session_open(next_session)
    return open_time.to_pydatetime()

def minutes_to_close() -> float:
    """Minuti mancanti alla chiusura del mercato (16:00 ET)."""
    now_et = datetime.now(ET)
    close_et = now_et.replace(hour=16, minute=0, second=0, microsecond=0)
    delta = (close_et - now_et).total_seconds() / 60
    return max(0, delta)

# Nel main.py, prima di startup:
if not is_market_open_today():
    logger.info("Oggi il mercato è chiuso. Bot in standby.")
    # Schedulare avvio per il prossimo giorno di mercato
```

---

## 10. Backtesting — Integrazione con vectorbt

Per testare una strategia prima del live, il workflow consigliato è:

**Step 1: Scarica dati storici da IBKR** (paper account, fuori orario mercato)
```python
# scripts/download_historical.py
# Usa MarketDataManager.get_historical_bars() per ogni symbol
# Salva tutto in data/historical/ come Parquet
```

**Step 2: Adatta ISignalGenerator per backtesting**

```python
# src/trading/backtesting/runner.py
"""
Esegue un ISignalGenerator su dati storici senza toccare IBKR.
Compatibile con vectorbt per metriche avanzate.
"""
import pandas as pd
import vectorbt as vbt
from trading.strategy.interfaces import ISignalGenerator, Direction

async def backtest_signal_generator(
    generator: ISignalGenerator,
    bars: pd.DataFrame,
    initial_capital: float = 10_000,
) -> dict:
    """
    Simula il generatore di segnali su dati storici.
    Ritorna statistiche: total_return, sharpe, max_drawdown, win_rate.
    """
    entries = []
    exits   = []
    warmup = generator.warmup_bars

    for i in range(warmup, len(bars)):
        window = bars.iloc[:i+1]
        signal = await generator.generate("BACKTEST", window)
        if signal and signal.direction == Direction.LONG:
            entries.append(True)
            exits.append(False)
        else:
            entries.append(False)
            exits.append(False)  # exit logic separata — implementare da IExitLogic

    entries_series = pd.Series(entries, index=bars.index[warmup:])
    price_series   = bars["close"].iloc[warmup:]

    # Usa vectorbt per calcolo metriche
    pf = vbt.Portfolio.from_signals(
        price_series,
        entries=entries_series,
        exits=pd.Series(exits, index=bars.index[warmup:]),
        init_cash=initial_capital,
        fees=0.001,   # 0.1% commissione simulate
    )

    return {
        "total_return_pct": pf.total_return() * 100,
        "sharpe_ratio":     pf.sharpe_ratio(),
        "max_drawdown_pct": pf.max_drawdown() * 100,
        "num_trades":       pf.trades.count(),
        "win_rate_pct":     pf.trades.win_rate() * 100 if pf.trades.count() > 0 else 0,
    }
```

**Workflow raccomandato prima del live:**
1. Backtest su dati 2022–2024 (in-sample)
2. Walk-forward validation su 2024–2025 (out-of-sample)
3. Paper trading per almeno 2 settimane
4. Live con capitale ridotto (10-20% del target) per 4 settimane
5. Scala al capitale pieno solo se paper + small-live sono coerenti col backtest

---

## 11. Circuit Breaker e Watchdog

### Circuit Breaker — ferma il bot automaticamente in caso di anomalie

```python
# src/trading/risk/circuit_breaker.py
"""
Il Circuit Breaker ferma il bot se vengono rilevate condizioni anomale.
È un layer di sicurezza aggiuntivo rispetto al RiskManager per trade.
"""
from loguru import logger
from trading.notifications.telegram import send

class CircuitBreaker:
    def __init__(self, bot):
        self.bot = bot
        self._triggered = False

    async def check(self, portfolio_value: float, daily_pnl: float):
        if self._triggered:
            return

        triggers = []

        # 1. Perdita giornaliera > 5% del portafoglio
        if portfolio_value > 0 and (daily_pnl / portfolio_value) < -0.05:
            triggers.append(f"Daily loss {daily_pnl/portfolio_value:.1%} supera -5%")

        # 2. Più di 20 ordini rifiutati oggi
        # (implementare contatore rejections nel DB)

        # 3. IB Gateway non risponde (ping test)
        try:
            await self.bot.ib.ib.reqCurrentTimeAsync()
        except Exception:
            triggers.append("IB Gateway non risponde")

        if triggers:
            self._triggered = True
            reason = " | ".join(triggers)
            logger.critical(f"CIRCUIT BREAKER ATTIVATO: {reason}")
            await send(f"🚨 CIRCUIT BREAKER: {reason}\nBot fermato, posizioni chiuse.", level="CRITICAL")
            await self.bot.ib.orders.cancel_all_orders()
            await self.bot.ib.orders.flatten_all_positions()
            await self.bot.shutdown()
```

### Watchdog — rileva blocchi del bot

```bash
# cron job ogni 5 minuti durante ore di mercato:
# /etc/cron.d/trading-bot-watchdog
*/5 9-16 * * 1-5 trader /usr/local/bin/check-bot.sh

# check-bot.sh:
#!/bin/bash
if ! systemctl is-active --quiet trading-bot; then
    echo "Bot down — restart" | logger
    systemctl restart trading-bot
    curl -s "https://api.telegram.org/bot$TOKEN/sendMessage?chat_id=$CHAT_ID&text=⚠️+Bot+riavviato+da+watchdog"
fi
```

---

## 12. Feature Pipeline — Calcolo Indicatori

Separare il calcolo delle feature dalla logica di segnale evita duplicazione quando più strategie usano gli stessi indicatori (es. RSI, ATR, VWAP).

```python
# src/trading/features/pipeline.py
"""
Calcola e memorizza feature/indicatori tecnici su ogni bar.
Le strategie ricevono un DataFrame già arricchito, non le barre grezze.
"""
import pandas as pd
import numpy as np

def compute_features(bars: pd.DataFrame) -> pd.DataFrame:
    """
    Aggiunge colonne di feature al DataFrame barre.
    Input: OHLCV. Output: OHLCV + indicatori.
    """
    df = bars.copy()

    # Momentum
    df["rsi_14"]     = _rsi(df["close"], 14)
    df["rsi_7"]      = _rsi(df["close"], 7)

    # Trend
    df["ema_9"]      = df["close"].ewm(span=9, adjust=False).mean()
    df["ema_21"]     = df["close"].ewm(span=21, adjust=False).mean()
    df["ema_50"]     = df["close"].ewm(span=50, adjust=False).mean()
    df["sma_200"]    = df["close"].rolling(200).mean()

    # Volatilità
    df["atr_14"]     = _atr(df, 14)
    df["bb_upper"], df["bb_lower"] = _bollinger(df["close"], 20, 2)

    # Volume
    df["vwap"]       = _vwap(df)
    df["vol_ratio"]  = df["volume"] / df["volume"].rolling(20).mean()

    # Prezzo
    df["daily_range_pct"] = (df["high"] - df["low"]) / df["close"]
    df["gap_pct"]         = (df["open"] - df["close"].shift(1)) / df["close"].shift(1)

    return df

def _rsi(series: pd.Series, period: int) -> pd.Series:
    delta = series.diff()
    gain  = delta.clip(lower=0).rolling(period).mean()
    loss  = (-delta.clip(upper=0)).rolling(period).mean()
    rs    = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def _atr(df: pd.DataFrame, period: int) -> pd.Series:
    hl  = df["high"] - df["low"]
    hc  = (df["high"] - df["close"].shift()).abs()
    lc  = (df["low"]  - df["close"].shift()).abs()
    tr  = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    return tr.rolling(period).mean()

def _bollinger(series: pd.Series, period: int, std_dev: float):
    sma   = series.rolling(period).mean()
    std   = series.rolling(period).std()
    return sma + std_dev * std, sma - std_dev * std

def _vwap(df: pd.DataFrame) -> pd.Series:
    tp = (df["high"] + df["low"] + df["close"]) / 3
    return (tp * df["volume"]).cumsum() / df["volume"].cumsum()
```

---

## 13. W-8BEN e Ritenuta Dividendi USA

Se il portafoglio include azioni che staccano dividendi USA:

**Compilare il modulo W-8BEN** su IBKR (Account Management → Tax Forms).
Il W-8BEN attesta di essere un non-residente USA e consente di applicare il **trattato fiscale Italia-USA**:
- Ritenuta standard USA sui dividendi: 30%
- Con W-8BEN + trattato Italia-USA: ridotta al **15%**
- La ritenuta residua del 15% è credito d'imposta recuperabile nel Quadro RM della dichiarazione italiana (credito d'imposta estero)

Il W-8BEN va rinnovato ogni 3 anni. IBKR invia reminder automatici.

---

## 14. Gestione Errori — Catalogo Codici IBKR Rilevanti

```python
# src/trading/broker/error_catalog.py
IBKR_ERROR_CATALOG = {
    # Connessione
    1100: ("CONN_LOST",     "Connessione a IB Gateway persa"),
    1101: ("CONN_RESTORE",  "Connessione ripristinata, dati non re-sincronizzati"),
    1102: ("CONN_RESTORE",  "Connessione ripristinata, dati re-sincronizzati"),
    # Market Data
    2104: ("MKT_DATA_OK",   "Market data farm connessa"),
    2106: ("HMDS_OK",       "HMDS data farm connessa"),
    2119: ("MARKET_CLOSED", "Market Data Farm disconnessa — mercato chiuso"),
    # Ordini
    201:  ("ORDER_REJECT",  "Ordine rifiutato — verificare margin/restrizioni"),
    202:  ("ORDER_CANCEL",  "Ordine cancellato"),
    # Contratti
    200:  ("NO_CONTRACT",   "Nessun security definition trovato"),
    # Dati storici
    162:  ("PACING_VIOL",   "Historical data pacing violation — rallentare richieste"),
    165:  ("HIST_DATA_END", "Historical data completato"),
    # Margin
    2137: ("MARGIN_WARN",   "Margin cushion sotto la soglia"),
}

def classify_error(code: int) -> tuple[str, str]:
    return IBKR_ERROR_CATALOG.get(code, ("UNKNOWN", f"Codice errore sconosciuto: {code}"))

def is_critical_error(code: int) -> bool:
    """True se l'errore richiede attenzione immediata (alert Telegram)."""
    critical = {201, 2137, 1100}   # order reject, margin, disconnessione
    return code in critical
```

---

## 15. Checklist Finale Prima del Live

### Infrastruttura
- [ ] VPS operativo, SSH key-only, ufw configurato
- [ ] IB Gateway si avvia automaticamente al reboot
- [ ] Bot si riconnette dopo disconnect (testare `systemctl restart ibgateway`)
- [ ] Telegram alerts funzionanti (test manuale)
- [ ] Grafana/Prometheus raccolgono metriche

### Account IBKR
- [ ] Conto live attivato (non paper)
- [ ] W-8BEN compilato e accettato
- [ ] Market data subscriptions attive (NYSE + NASDAQ)
- [ ] Margin account abilitato se necessario per short selling
- [ ] IP whitelist configurato (solo IP del VPS)
- [ ] Flex Query configurata e Token generato

### Bot
- [ ] `.env` con credenziali live, non paper
- [ ] `IBKR_PORT=4002` (live), non 4001 (paper)
- [ ] `IBKR_ACCOUNT` corretto (formato U1234567)
- [ ] Risk limits configurati per il capitale reale (non quelli di test)
- [ ] Circuit breaker soglia impostata
- [ ] Database con migrations applicate
- [ ] Logs scrivono su file (non solo stdout)
- [ ] Backtest completato con out-of-sample positivo
- [ ] 2+ settimane paper trading con risultati coerenti col backtest

### Fiscale
- [ ] Flex Query configurata e testata (export di prova con anno corrente)
- [ ] Scadenze aggiunte in calendario: 30 giugno (pagamento) e 31 ottobre (invio modello)
- [ ] Commercialista o MoneyViz account ready

---

## 16. GitHub Repos Ecosystem — Cosa Usare e Cosa Ignorare

### Repos da integrare direttamente nel progetto

| Repo | Stars | Ruolo nel progetto | Come usarlo |
|---|---|---|---|
| `ib-api-reloaded/ib_async` | ⭐1.4k | **Dipendenza core** — wrapper IBKR | `pip install ib-async` |
| `gnzsnz/ib-gateway-docker` | ⭐838 | **Sostituisce setup manuale IBC + Xvfb** | Immagine nel `docker-compose.yml` |
| `polakowo/vectorbt` | ⭐OSS | **Backtesting** — migliaia di config in secondi | `pip install vectorbt` |
| `IbcAlpha/IBC` | — | **Auto-login IB Gateway** — incluso in gnzsnz | Già bundled nell'immagine Docker |
| `exchange-calendars` | — | **Calendari di mercato NYSE + XETRA** | `pip install exchange-calendars` |

### Repos utili come riferimento architetturale

**`9600dev/mmr`** — Python trading platform costruita su `ib_async`, molto simile alla nostra architettura. MMR è progettata per essere operata da LLM: ogni operazione è un comando CLI che ritorna JSON, con un pipeline Propose → Review → Approve dove l'LLM non piazza mai ordini direttamente. Vale la pena leggere il codice per pattern di gestione connessione e position sizing.

**`wangzhe3224/awesome-systematic-trading`** — Lista curata di librerie per systematic trading. Utile per scegliere librerie di analisi aggiuntive quando si sviluppano nuove strategie.

### Repos con lo stesso nome ma inutili per questo progetto

Ci sono tre repository distinte con varianti del nome "Vibe-Trading" — è importante distinguerle:

**`HKUDS/Vibe-Trading`** (⭐11.7k) — Vibe-Trading è un workspace di ricerca AI che trasforma prompt in linguaggio naturale in strategie analizzabili, motori di backtest e report. **Non esegue trade live** e non ha integrazione IBKR. Utile solo per fase di ricerca strategica offline.

**`VibeTradingLabs/vibetrading`** — Usa Claude API per generare codice strategia da descrizioni in linguaggio naturale, con backtest integrato e position sizing (Kelly, fixed fraction). Interessante per generare rapidamente codice per nuove `ISignalGenerator` da testare, ma orientato a crypto/Hyperliquid, non IBKR.

**`vibetrade-ai/vibe-trade`** — Mercato indiano (NSE/BSE), broker locale. Non applicabile.

**`brndnmtthws/thetagang`** — Bot IBKR per "The Wheel" su opzioni. Non rilevante per stock puro.

### Come usare VibeTradingLabs per generare strategie

L'unico uso pratico di questi repo nel nostro contesto è usare `vibetrading` come **generatore di bozze di `ISignalGenerator`** durante la fase di ricerca:

```python
# Esempio: genera una bozza di strategia da linguaggio naturale
import vibetrading.strategy

code = vibetrading.strategy.generate(
    "Momentum strategy on EU growth stocks: "
    "RSI(14) < 30 oversold entry, EMA50 above EMA200 trend filter, "
    "2% stop loss, 4% take profit, hold max 5 days",
    model="claude-sonnet-4-6",
)
# Il codice generato va adattato all'interfaccia ISignalGenerator del nostro progetto
# NON usare direttamente in produzione — sempre validare e backtestare
```

---

*Part 2 — Versione 1.1 — Giugno 2026*
*Leggere insieme a Part 1. Insieme i due documenti costituiscono il handoff completo.*
