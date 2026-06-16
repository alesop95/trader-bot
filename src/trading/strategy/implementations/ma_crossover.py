"""
Strategia MA Crossover completa.
Ogni classe implementa una delle 6 interfacce di strategy/interfaces.py.
La funzione build_ma_crossover_composer() assembla il composer pronto all'uso.
"""

import asyncio
from collections.abc import Callable
from datetime import UTC, datetime

import pandas as pd
import yfinance as yf
from loguru import logger

from trading.broker.market_data import YAHOO_MAP
from trading.broker.orders import OrderManager
from trading.strategy.composer import RiskValidator, StrategyComposer
from trading.strategy.interfaces import (
    AllocatedSignal,
    Direction,
    IExecutionAlgo,
    IExitLogic,
    IPortfolioAllocator,
    IPositionSizer,
    ISignalGenerator,
    IUniverseFilter,
    RawSignal,
)

# ─── 1. UNIVERSE FILTER ──────────────────────────────────────────────────────


class DividendFreeFilter(IUniverseFilter):
    """
    Esclude i simboli con ex-dividend date entro `lookforward_days` giorni di calendario.
    Un'azione che stacca dividendo scende sistematicamente del valore del dividendo il
    giorno ex-div — il filtro evita di entrare a ridosso di quell'evento.

    La chiamata a yfinance.Ticker.info è sincrona e wrappata in run_in_executor.
    I simboli EU vengono tradotti con YAHOO_MAP prima della query.
    In caso di errore sul singolo simbolo il filtro è permissivo: il simbolo viene incluso.
    """

    def __init__(self, lookforward_days: int = 5) -> None:
        self._lookforward_days = lookforward_days

    async def filter(self, candidates: list[str]) -> list[str]:
        loop = asyncio.get_event_loop()

        async def _check(symbol: str) -> str | None:
            yahoo_sym = YAHOO_MAP.get(symbol, symbol)
            try:
                info: dict = await loop.run_in_executor(
                    None, lambda s=yahoo_sym: yf.Ticker(s).info
                )
                ex_div_ts = info.get("exDividendDate")
                if ex_div_ts is None:
                    return symbol
                ex_div_dt = datetime.fromtimestamp(ex_div_ts, tz=UTC)
                days_to_ex = (ex_div_dt - datetime.now(UTC)).days
                if 0 <= days_to_ex <= self._lookforward_days:
                    logger.info(
                        "DividendFreeFilter: escluso {} — ex-div in {} giorni",
                        symbol, days_to_ex,
                    )
                    return None
                return symbol
            except Exception as exc:
                logger.warning(
                    "DividendFreeFilter: errore su {}, incluso per default ({})",
                    symbol, exc,
                )
                return symbol

        results = await asyncio.gather(*(_check(s) for s in candidates))
        return [s for s in results if s is not None]


# ─── 2. SIGNAL GENERATOR ─────────────────────────────────────────────────────


class MACrossoverSignalGenerator(ISignalGenerator):
    """
    Segnale LONG quando EMA_9 attraversa al rialzo EMA_21 sul bar corrente.
    Conferme richieste: RSI_14 < rsi_max (no overbought), MACDh_12_26_9 > 0 (momentum positivo).
    Ignora i simboli già in posizione (stato tracciato via on_fill).

    strength: combinazione di ampiezza del crossover e RSI normalizzato, clampato in [0.01, 1.0].
    stop_loss_pct: 2 × ATRr_14 (due ATR sotto il prezzo di entrata stimato).
    """

    warmup_bars: int = 50

    def __init__(self, rsi_max: float = 70.0) -> None:
        self._rsi_max = rsi_max
        self._in_position: set[str] = set()

    async def generate(self, symbol: str, bars: pd.DataFrame) -> RawSignal | None:
        if symbol in self._in_position:
            return None

        last = bars.iloc[-1]
        prev = bars.iloc[-2]

        # Salta se i valori chiave sono NaN (copertura difensiva)
        ema_cols_valid = not (
            pd.isna(last["EMA_9"]) or pd.isna(last["EMA_21"])
            or pd.isna(prev["EMA_9"]) or pd.isna(prev["EMA_21"])
        )
        if not ema_cols_valid:
            return None
        if pd.isna(last["RSI_14"]) or pd.isna(last["MACDh_12_26_9"]):
            return None

        # Bullish crossover: il bar precedente era EMA_9 <= EMA_21, ora è invertito
        crossed_up = prev["EMA_9"] <= prev["EMA_21"] and last["EMA_9"] > last["EMA_21"]
        if not crossed_up:
            return None

        if last["RSI_14"] >= self._rsi_max:
            return None
        if last["MACDh_12_26_9"] <= 0:
            return None

        # Strength: spread relativo EMA × (100 - RSI) normalizzato — più grande è il gap
        # e più basso è l'RSI, più forte è il segnale
        ema_spread = (last["EMA_9"] - last["EMA_21"]) / last["EMA_21"]
        raw_strength = ema_spread * 20 * (1.0 - last["RSI_14"] / 100.0)
        strength = float(max(0.01, min(1.0, raw_strength)))

        stop_loss_pct = float(last["ATRr_14"]) * 2.0 if pd.notna(last["ATRr_14"]) else None

        return RawSignal(
            symbol=symbol,
            direction=Direction.LONG,
            strength=strength,
            reason=(
                f"EMA9/EMA21 cross | RSI={last['RSI_14']:.1f}"
                f" | MACDh={last['MACDh_12_26_9']:.5f}"
            ),
            stop_loss_pct=stop_loss_pct,
        )

    async def on_fill(
        self,
        symbol: str,
        direction: Direction,
        shares: int,
        price: float,
    ) -> None:
        if direction == Direction.LONG and shares > 0:
            self._in_position.add(symbol)
        else:
            # SELL (chiusura) — rimuove dalla lista posizioni aperte
            self._in_position.discard(symbol)


# ─── 3. POSITION SIZER ───────────────────────────────────────────────────────


class FixedFractionSizer(IPositionSizer):
    """
    Alloca una fraction fissa del capitale strategia per ogni segnale.
    Se esiste già una posizione parziale sullo stesso simbolo, riduce la size
    dello spazio già occupato (non aggiunge oltre il cap per simbolo).
    """

    def __init__(self, fraction: float = 0.05) -> None:
        if not 0 < fraction <= 1:
            raise ValueError(f"fraction deve essere (0, 1], ricevuto {fraction}")
        self._fraction = fraction

    def size(
        self,
        signal: RawSignal,
        portfolio_value: float,
        current_positions: dict[str, float],
    ) -> float:
        cap = portfolio_value * self._fraction
        existing = current_positions.get(signal.symbol, 0.0)
        return max(0.0, cap - existing)


# ─── 4. PORTFOLIO ALLOCATOR ──────────────────────────────────────────────────


class SimplePortfolioAllocator(IPortfolioAllocator):
    """
    Accetta al massimo (max_positions - posizioni_aperte) segnali per bar,
    scegliendo quelli con strength maggiore. Scarta i segnali il cui sized_usd
    è inferiore a min_trade_usd — troppo piccoli per coprire commissioni e slippage.
    """

    def __init__(self, max_positions: int = 10, min_trade_usd: float = 200.0) -> None:
        self._max_positions = max_positions
        self._min_trade_usd = min_trade_usd

    def allocate(
        self,
        signals: list[RawSignal],
        sized_usds: list[float],
        current_positions: dict[str, float],
    ) -> list[AllocatedSignal]:
        open_count = sum(1 for v in current_positions.values() if v > 0)
        slots = max(0, self._max_positions - open_count)
        if slots == 0:
            return []

        # Filtra per size minima, poi ordina per strength decrescente
        candidates = sorted(
            [
                (sig, usd)
                for sig, usd in zip(signals, sized_usds, strict=True)
                if usd >= self._min_trade_usd
            ],
            key=lambda x: x[0].strength,
            reverse=True,
        )

        allocated: list[AllocatedSignal] = []
        for sig, usd in candidates[:slots]:
            allocated.append(
                AllocatedSignal(
                    symbol=sig.symbol,
                    direction=sig.direction,
                    strength=sig.strength,
                    reason=sig.reason,
                    stop_loss_pct=sig.stop_loss_pct,
                    take_profit_pct=sig.take_profit_pct,
                    generated_at=sig.generated_at,
                    target_usd=usd,
                )
            )
        return allocated


# ─── 5. EXECUTION ALGO ───────────────────────────────────────────────────────


class LimitOrderExecutionAlgo(IExecutionAlgo):
    """
    Piazza un LimitOrder aggressivo a last_price × (1 ± _SLIPPAGE_PCT).
    Usa price_getter per recuperare l'ultimo prezzo del bar corrente.
    shares = floor(target_usd / limit_price): niente frazionari.

    Il GTC stop loss viene piazzato dall'IBClient fill handler (non qui):
    questo esecutore conosce solo la fase di entrata.
    """

    _SLIPPAGE_PCT: float = 0.001  # 0.1% — aggressivo ma non market order

    def __init__(
        self,
        order_manager: OrderManager,
        price_getter: Callable[[str], float | None],
    ) -> None:
        self._om = order_manager
        self._price_getter = price_getter

    async def execute(self, signal: AllocatedSignal) -> None:
        last_price = self._price_getter(signal.symbol)
        if last_price is None or last_price <= 0:
            logger.warning(
                "LimitOrderExec: prezzo non disponibile per {}, segnale ignorato",
                signal.symbol,
            )
            return

        if signal.direction == Direction.LONG:
            limit_price = round(last_price * (1.0 + self._SLIPPAGE_PCT), 4)
            action = "BUY"
        else:
            limit_price = round(last_price * (1.0 - self._SLIPPAGE_PCT), 4)
            action = "SELL"

        shares = int(signal.target_usd / limit_price)
        if shares <= 0:
            logger.warning(
                "LimitOrderExec: shares=0 per {} (target_usd={:.0f}, price={:.4f}), ignorato",
                signal.symbol, signal.target_usd, limit_price,
            )
            return

        signal.limit_price = limit_price
        signal.shares = shares

        self._om.place_limit_order(signal.symbol, action, shares, limit_price)


# ─── 6. EXIT LOGIC ───────────────────────────────────────────────────────────


class EMACrossoverExitLogic(IExitLogic):
    """
    Esce dalla posizione in due casi:
    - EMA_9 attraversa al ribasso EMA_21 (segnale inverso all'entrata)
    - Il valore della posizione è sceso di max_drawdown_pct dal picco di sessione

    Il picco viene resettato a ogni uscita, così la logica funziona correttamente
    se lo stesso simbolo viene rientersato nella stessa sessione.
    """

    def __init__(self, max_drawdown_pct: float = 0.15) -> None:
        self._max_drawdown_pct = max_drawdown_pct
        self._peak_value: dict[str, float] = {}

    async def should_exit(
        self,
        symbol: str,
        position_value: float,
        bars: pd.DataFrame,
    ) -> bool:
        # Aggiorna picco di sessione
        self._peak_value[symbol] = max(self._peak_value.get(symbol, position_value), position_value)

        # Drawdown dal picco
        peak = self._peak_value[symbol]
        if peak > 0:
            drawdown = (peak - position_value) / peak
            if drawdown >= self._max_drawdown_pct:
                logger.info(
                    "Exit {}: drawdown {:.1%} >= soglia {:.1%}",
                    symbol, drawdown, self._max_drawdown_pct,
                )
                self._peak_value.pop(symbol, None)
                return True

        # EMA bearish crossover
        if len(bars) < 2:
            return False

        last = bars.iloc[-1]
        prev = bars.iloc[-2]

        ema_valid = not (
            pd.isna(last["EMA_9"]) or pd.isna(last["EMA_21"])
            or pd.isna(prev["EMA_9"]) or pd.isna(prev["EMA_21"])
        )
        if not ema_valid:
            return False

        crossed_down = prev["EMA_9"] >= prev["EMA_21"] and last["EMA_9"] < last["EMA_21"]
        if crossed_down:
            logger.info("Exit {}: EMA9 attraversa al ribasso EMA21", symbol)
            self._peak_value.pop(symbol, None)
            return True

        return False


# ─── FACTORY ─────────────────────────────────────────────────────────────────


def build_ma_crossover_composer(
    order_manager: OrderManager,
    price_getter: Callable[[str], float | None],
    risk_validator: RiskValidator | None = None,
    *,
    name: str = "ma_crossover",
    max_positions: int = 10,
    position_fraction: float = 0.05,
    rsi_max: float = 70.0,
    max_drawdown_pct: float = 0.15,
    dividend_lookforward_days: int = 5,
    min_trade_usd: float = 200.0,
) -> StrategyComposer:
    """
    Costruisce un StrategyComposer MA Crossover con i parametri specificati.
    Unico punto di cablaggio: main.py chiama questa funzione passando
    order_manager e price_getter; non ha bisogno di conoscere i 6 componenti.
    """
    return StrategyComposer(
        name=name,
        universe_filter=DividendFreeFilter(lookforward_days=dividend_lookforward_days),
        signal_generator=MACrossoverSignalGenerator(rsi_max=rsi_max),
        position_sizer=FixedFractionSizer(fraction=position_fraction),
        portfolio_allocator=SimplePortfolioAllocator(
            max_positions=max_positions,
            min_trade_usd=min_trade_usd,
        ),
        execution_algo=LimitOrderExecutionAlgo(order_manager, price_getter),
        exit_logic=EMACrossoverExitLogic(max_drawdown_pct=max_drawdown_pct),
        risk_validator=risk_validator,
    )
