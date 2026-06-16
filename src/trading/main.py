"""
TradingBot: punto di ingresso e cablaggio di tutti i componenti.
Assembla IBClient, MarketDataManager, StrategyRegistry, RiskManager,
TradingScheduler, TelegramNotifier, HealthCheck e Repository
in un unico ciclo di vita asyncio.
"""

import asyncio
import signal
import sys
from datetime import UTC, datetime
from decimal import Decimal

import pandas as pd
from ib_async import Fill
from loguru import logger

from trading.broker.client import IBClient
from trading.broker.market_data import MarketDataManager
from trading.broker.orders import UNIVERSE, OrderManager, get_contract
from trading.config import settings
from trading.db.repository import get_repository
from trading.monitoring.healthcheck import DAILY_PNL_USD, SIGNALS_TOTAL, TRADES_TOTAL, HealthCheck
from trading.notifications.telegram import build_notifier
from trading.reporting.flex_query import build_flex_client
from trading.risk.circuit_breaker import CircuitBreaker
from trading.risk.manager import build_risk_manager
from trading.scheduler.jobs import (
    TradingScheduler,
    is_any_session_open,
    is_eu_session,
    is_us_session,
)
from trading.strategy.implementations.ma_crossover import build_ma_crossover_composer
from trading.strategy.interfaces import AllocatedSignal, Direction
from trading.strategy.registry import StrategyRegistry

# Suddivisione dell'universo per sessione
_EU_EXCHANGES = frozenset({"IBIS", "AEB"})
_EU_CANDIDATES: list[str] = [s for s, (ex, _) in UNIVERSE.items() if ex in _EU_EXCHANGES]
_US_CANDIDATES: list[str] = [s for s, (ex, _) in UNIVERSE.items() if ex == "SMART"]
_ALL_CANDIDATES: list[str] = list(UNIVERSE.keys())

# Sentinella IBKR per "PnL non ancora disponibile" — sys.float_info.max
_IBKR_NO_PNL = 1.7976931348623157e308


class TradingBot:
    """
    Assembla e coordina tutti i componenti del bot.
    Unica istanza: main() crea TradingBot e chiama asyncio.run(bot.run()).
    """

    def __init__(self) -> None:
        # ─── INFRASTRUTTURA ──────────────────────────────────────────────────
        self._ib = IBClient()
        self._market_data = MarketDataManager(self._ib)
        self._order_manager = OrderManager(self._ib)

        # ─── RISK ─────────────────────────────────────────────────────────────
        self._cb = CircuitBreaker()
        self._risk_manager = build_risk_manager(
            circuit_breaker=self._cb,
            positions_getter=lambda: self._positions,
            daily_pnl_getter=lambda: self._daily_pnl,
        )

        # ─── STRATEGIA ────────────────────────────────────────────────────────
        self._registry = StrategyRegistry()
        self._registry.register(
            build_ma_crossover_composer(
                order_manager=self._order_manager,
                price_getter=self._get_last_price,
                risk_validator=self._risk_manager.validate,
            ),
            capital_fraction=1.0,
        )

        # ─── SERVIZI DI SUPPORTO ──────────────────────────────────────────────
        self._notifier = build_notifier()
        self._flex_client = build_flex_client()

        self._scheduler = TradingScheduler()
        self._scheduler.setup(
            on_bar=self._on_bar,
            on_exit_check=self._on_exit_check,
            on_eu_open=self._on_eu_open,
            on_us_open=self._on_us_open,
            on_eu_close=self._on_eu_close,
            on_us_close=self._on_us_close,
        )

        self._health = HealthCheck(
            circuit_breaker=self._cb,
            scheduler=self._scheduler,
            ib_connected_getter=lambda: self._ib.is_connected,
            daily_pnl_getter=lambda: self._daily_pnl,
        )

        # ─── STATO IN MEMORIA ─────────────────────────────────────────────────
        self._positions: dict[str, float] = {}   # symbol → valore USD corrente
        self._daily_pnl: float = 0.0             # PnL realizzato della sessione
        self._portfolio_value: float = 0.0       # NetLiquidation USD
        self._stop_event = asyncio.Event()

        # Fill callback
        self._ib.register_fill_callback(self._on_fill)

    # ─── CICLO DI VITA ────────────────────────────────────────────────────────

    async def run(self) -> None:
        """Entry point asincrono. Avvia il bot e aspetta lo shutdown."""
        loop = asyncio.get_running_loop()
        self._setup_signal_handlers(loop)
        try:
            await self._start()
            await self._stop_event.wait()
        finally:
            await self._stop()

    async def _start(self) -> None:
        logger.info("TradingBot: avvio in modalità {}", settings.trading_mode)

        await self._ib.connect()

        # Quando IBKR conferma la connessione, chiude il circuit breaker
        self._ib.ib.connectedEvent += lambda: self._cb.record_success()

        # Warmup dati storici + sottoscrizione real-time
        await self._market_data.warmup(_ALL_CANDIDATES)
        contracts = {s: get_contract(s) for s in _ALL_CANDIDATES}
        await self._market_data.start_realtime(contracts)

        # Sincronizza portafoglio da IBKR
        await self._sync_portfolio()

        # Avvia servizi
        await self._notifier.start()
        await self._health.start()
        self._scheduler.start()

        await self._notifier.notify_bot_started(mode=settings.trading_mode)
        logger.info(
            "TradingBot: pronto — {} EU, {} US candidati",
            len(_EU_CANDIDATES), len(_US_CANDIDATES),
        )

    async def _stop(self) -> None:
        logger.info("TradingBot: shutdown in corso...")
        self._scheduler.shutdown()
        await self._market_data.stop_realtime()
        await self._health.stop()
        await self._notifier.notify_bot_stopped()
        await self._notifier.stop()
        await self._ib.disconnect()
        logger.info("TradingBot: fermato")

    def _setup_signal_handlers(self, loop: asyncio.AbstractEventLoop) -> None:
        def _request_shutdown() -> None:
            logger.info("TradingBot: segnale di shutdown ricevuto")
            self._stop_event.set()

        try:
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(sig, _request_shutdown)
        except (NotImplementedError, OSError):
            # Windows: add_signal_handler non disponibile — SIGINT è gestito da asyncio
            logger.debug("Signal handlers Unix non disponibili (Windows dev?)")

    # ─── SINCRONIZZAZIONE PORTAFOGLIO ─────────────────────────────────────────

    async def _sync_portfolio(self) -> None:
        """
        Aggiorna posizioni e NetLiquidation dai dati in cache di ib_async.
        ib_async mantiene questi valori sincronizzati automaticamente dopo connect().
        """
        portfolio_items = self._ib.ib.portfolio()
        self._positions = {
            item.contract.symbol: float(item.marketValue)
            for item in portfolio_items
            if float(item.marketValue) != 0
        }

        for av in self._ib.ib.accountValues():
            if av.tag == "NetLiquidation" and av.currency == "USD":
                self._portfolio_value = float(av.value)
                break

        logger.debug(
            "Portfolio sync: {:.0f} USD netti, {} posizioni",
            self._portfolio_value,
            sum(1 for v in self._positions.values() if v > 0),
        )

    def _get_last_price(self, symbol: str) -> float | None:
        """Close dell'ultimo bar 5-min — usato da LimitOrderExecutionAlgo per il limite."""
        bars = self._market_data.get_bars(symbol)
        if bars.empty or "close" not in bars.columns:
            return None
        last = bars["close"].iloc[-1]
        return float(last) if pd.notna(last) else None

    # ─── FILL HANDLER ─────────────────────────────────────────────────────────

    async def _on_fill(self, fill: Fill) -> None:
        """
        Chiamato da IBClient._dispatch_fill() a ogni fill IBKR.
        Responsabilità: stop GTC, DB, Telegram, metriche, registry.on_fill().
        """
        symbol = fill.contract.symbol
        side = fill.execution.side.upper()         # "BOT" o "SLD"
        shares = int(fill.execution.shares)
        price = float(fill.execution.price)
        exec_id = fill.execution.execId
        fill_time = fill.execution.time
        if fill_time.tzinfo is None:
            fill_time = fill_time.replace(tzinfo=UTC)

        cr = fill.commissionReport
        commission = float(cr.commission) if cr else 0.0
        raw_pnl = float(cr.realizedPNL) if cr else 0.0
        pnl_usd = raw_pnl if abs(raw_pnl) < _IBKR_NO_PNL * 0.9 else 0.0

        direction = Direction.LONG if side == "BOT" else Direction.SHORT
        exchange, currency = UNIVERSE.get(symbol, ("UNKNOWN", "USD"))

        # 1 — Propaga al registry
        await self._registry.on_fill(symbol, direction, shares, price)

        # 2 — GTC stop immediatamente dopo un BUY fill
        if side == "BOT":
            stop_price = round(price * (1 - settings.default_stop_loss_pct), 4)
            self._order_manager.place_stop_order(symbol, "SELL", shares, stop_price)

        # 3 — Aggiorna PnL e metriche
        if side == "SLD":
            self._daily_pnl += pnl_usd
            await self._notifier.notify_exit(symbol, pnl_usd)
        else:
            sig = AllocatedSignal(
                symbol=symbol, direction=Direction.LONG, strength=0.0,
                reason="fill", target_usd=shares * price,
                shares=shares, limit_price=price,
                generated_at=datetime.now(UTC),
            )
            await self._notifier.notify_entry(sig)

        TRADES_TOTAL.inc()
        DAILY_PNL_USD.set(self._daily_pnl)

        # 4 — Persisti nel DB
        async with get_repository() as repo:
            await repo.save_trade(
                ibkr_exec_id=exec_id,
                symbol=symbol,
                exchange=exchange,
                currency=currency,
                direction="BUY" if side == "BOT" else "SELL",
                quantity=shares,
                fill_price=Decimal(str(price)),
                commission=Decimal(str(abs(commission))),
                fill_time=fill_time,
                strategy_name=self._registry.names[0] if self._registry.names else "unknown",
                pnl_usd=Decimal(str(round(pnl_usd, 4))) if pnl_usd else None,
            )

        # 5 — Risincronizza portafoglio
        await self._sync_portfolio()

    # ─── SCHEDULER CALLBACKS ──────────────────────────────────────────────────

    async def _on_bar(self) -> None:
        """Chiamato ogni 5 minuti dal TradingScheduler. Esegue il ciclo strategia."""
        if not is_any_session_open():
            return

        now = datetime.now(UTC)
        candidates: list[str] = []
        if is_eu_session(now):
            candidates.extend(_EU_CANDIDATES)
        if is_us_session(now):
            candidates.extend(_US_CANDIDATES)
        if not candidates:
            return

        bars_by_symbol = {s: self._market_data.get_bars(s) for s in candidates}
        await self._sync_portfolio()

        try:
            executed = await self._registry.run_bar(
                candidates=candidates,
                bars_by_symbol=bars_by_symbol,
                total_portfolio_value=self._portfolio_value,
                current_positions=self._positions,
            )
        except Exception as exc:
            logger.error("_on_bar: errore nel registry.run_bar: {}", exc)
            self._cb.record_failure(f"run_bar error: {exc}")
            return

        if executed:
            SIGNALS_TOTAL.inc(len(executed))
            logger.info("Bar: {} segnali eseguiti", len(executed))

    async def _on_exit_check(self) -> None:
        """Chiamato ogni 30 secondi. Verifica le uscite su tutte le posizioni aperte."""
        if not is_any_session_open():
            return
        if not self._positions:
            return

        bars_by_symbol = {s: self._market_data.get_bars(s) for s in _ALL_CANDIDATES}

        try:
            exits_by_strategy = await self._registry.run_exit_check(
                current_positions=self._positions,
                bars_by_symbol=bars_by_symbol,
            )
        except Exception as exc:
            logger.error("_on_exit_check: errore: {}", exc)
            return

        for strategy_name, symbols in exits_by_strategy.items():
            for symbol in symbols:
                last_price = self._get_last_price(symbol)
                if not last_price or last_price <= 0:
                    logger.warning("Exit {}: prezzo non disponibile, skip", symbol)
                    continue
                position_value = self._positions.get(symbol, 0.0)
                exit_shares = int(position_value / last_price)
                if exit_shares <= 0:
                    continue
                limit_price = round(last_price * 0.999, 4)
                self._order_manager.place_limit_order(symbol, "SELL", exit_shares, limit_price)
                logger.info(
                    "Exit {}: SELL {} @ {:.4f} (richiesta da '{}')",
                    symbol, exit_shares, limit_price, strategy_name,
                )

    async def _on_eu_open(self) -> None:
        logger.info("Sessione EU aperta (XETRA 09:00 CET)")
        await self._notifier.send("[MARKET] Sessione EU aperta (XETRA)")

    async def _on_us_open(self) -> None:
        logger.info("Sessione US aperta (NYSE/NASDAQ 09:30 ET)")
        await self._notifier.send("[MARKET] Sessione US aperta (NYSE/NASDAQ)")

    async def _on_eu_close(self) -> None:
        logger.info("Chiusura EU imminente (17:30 CET)")
        eu_open = sorted(
            s for s in _EU_CANDIDATES if self._positions.get(s, 0) > 0
        )
        if eu_open:
            await self._notifier.send(
                f"[MARKET] Chiusura EU. Posizioni aperte: {', '.join(eu_open)}"
            )

    async def _on_us_close(self) -> None:
        logger.info("Chiusura US imminente (16:00 ET)")
        us_open = sorted(
            s for s in _US_CANDIDATES if self._positions.get(s, 0) > 0
        )
        if us_open:
            await self._notifier.send(
                f"[MARKET] Chiusura US. Posizioni aperte: {', '.join(us_open)}"
            )
        await self._notifier.notify_daily_summary(
            pnl_usd=self._daily_pnl,
            trades=0,   # aggiornato in una versione futura leggendo il DB
        )
        self._daily_pnl = 0.0   # reset per la sessione successiva


# ─── ENTRY POINT ──────────────────────────────────────────────────────────────


def main() -> None:
    """
    Entry point del bot — `trader-bot` CLI command (pyproject.toml scripts).
    Configura loguru e avvia il ciclo asyncio.
    """
    logger.remove()
    logger.add(
        sys.stderr,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {name}:{line} — {message}",
        level="INFO",
    )
    logger.add(
        "logs/trader-bot.log",
        rotation="1 day",
        retention="30 days",
        compression="gz",
        level="DEBUG",
    )

    try:
        asyncio.run(TradingBot().run())
    except KeyboardInterrupt:
        logger.info("Interruzione manuale ricevuta — bot fermato")
