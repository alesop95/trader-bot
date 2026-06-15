import asyncio
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from functools import partial
from typing import Any

import pandas as pd
import yfinance as yf
from ib_async import IB, Contract
from loguru import logger

from trading.broker.client import IBClient

# Mapping ticker IBKR → ticker Yahoo Finance per simboli EU
# I ticker EU su IBKR non hanno il suffisso di exchange che Yahoo richiede
YAHOO_MAP: dict[str, str] = {
    "SAP": "SAP.DE",
    "IFX": "IFX.DE",
    "AIXA": "AIXA.DE",
    "SRT3": "SRT3.DE",
    "ASML": "ASML.AS",
    "ADYEN": "ADYEN.AS",
    "BESI": "BESI.AS",
}

_WARMUP_PERIOD = "60d"
_WARMUP_INTERVAL = "5m"
_MAX_BARS_IN_MEMORY = 500


class MarketDataManager:
    """
    Gestisce i dati OHLCV per tutti i simboli monitorati.

    Flusso:
      warmup()         → scarica storico 5-min da yfinance (no pacing limits)
      start_realtime() → sottoscrive bar 5s IBKR per ogni contratto
      _on_realtime_bar → aggrega 5s in 5-min allineati all'orologio
      _notify_callbacks → chiama i listener registrati con il DataFrame aggiornato
    """

    def __init__(self, ib_client: IBClient) -> None:
        self._ib: IB = ib_client.ib
        # symbol → DataFrame con colonne [open, high, low, close, volume], index DatetimeIndex UTC
        self._bars: dict[str, pd.DataFrame] = {}
        # symbol → buffer dei 5s-bar della finestra corrente
        self._buffers: dict[str, list[Any]] = {}
        # symbol → datetime UTC di inizio della finestra 5-min corrente
        self._window_starts: dict[str, datetime] = {}
        # symbol → handle RealTimeBarList (tenuto per cancelRealTimeBars)
        self._rt_subscriptions: dict[str, Any] = {}
        # Callback: (symbol, bars_df) — chiamato a ogni nuovo bar 5-min completato
        self._bar_callbacks: list[Callable[[str, pd.DataFrame], Awaitable[None]]] = []

    # ─── API PUBBLICA ─────────────────────────────────────────────────────────

    def register_bar_callback(
        self, callback: Callable[[str, pd.DataFrame], Awaitable[None]]
    ) -> None:
        self._bar_callbacks.append(callback)

    def get_bars(self, symbol: str) -> pd.DataFrame:
        return self._bars.get(symbol, pd.DataFrame()).copy()

    async def warmup(self, symbols: list[str], n_bars: int = 200) -> None:
        """
        Scarica storico 5-min da yfinance per i simboli indicati.
        Eseguito in un thread pool perché yfinance è sincrono.
        Da chiamare prima di start_realtime().
        """
        loop = asyncio.get_event_loop()
        for symbol in symbols:
            try:
                df = await loop.run_in_executor(
                    None, self._download_yfinance, symbol, n_bars
                )
                self._bars[symbol] = df
                logger.info("Warmup {}: {} bar scaricati da Yahoo Finance", symbol, len(df))
            except Exception as exc:
                logger.error("Warmup fallito per {}: {}", symbol, exc)
                self._bars[symbol] = pd.DataFrame()

    async def start_realtime(self, contracts: dict[str, Contract]) -> None:
        """
        Sottoscrive i bar 5s IBKR per ogni contratto.
        contracts: dict symbol → ib_async.Contract (già qualificato con exchange e currency)
        """
        _epoch = datetime.fromtimestamp(0, tz=UTC)
        for symbol, contract in contracts.items():
            bar_list = self._ib.reqRealTimeBars(
                contract, barSize=5, whatToShow="TRADES", useRTH=True
            )
            self._rt_subscriptions[symbol] = bar_list
            self._buffers[symbol] = []
            self._window_starts[symbol] = _epoch
            bar_list.updateEvent += partial(self._on_realtime_bar, symbol)
            logger.info("Sottoscrizione real-time avviata per {}", symbol)

    async def stop_realtime(self) -> None:
        for symbol, bar_list in self._rt_subscriptions.items():
            self._ib.cancelRealTimeBars(bar_list)
            logger.info("Sottoscrizione real-time cancellata per {}", symbol)
        self._rt_subscriptions.clear()

    # ─── WARMUP INTERNO ───────────────────────────────────────────────────────

    def _download_yfinance(self, symbol: str, n_bars: int) -> pd.DataFrame:
        yahoo_ticker = YAHOO_MAP.get(symbol, symbol)
        raw = yf.download(
            yahoo_ticker,
            period=_WARMUP_PERIOD,
            interval=_WARMUP_INTERVAL,
            auto_adjust=True,
            progress=False,
            multi_level_index=False,
        )
        if raw.empty:
            logger.warning("yfinance non ha restituito dati per {} ({})", symbol, yahoo_ticker)
            return pd.DataFrame()

        raw.columns = [c.lower() for c in raw.columns]

        if raw.index.tz is None:
            raw.index = raw.index.tz_localize("UTC")
        else:
            raw.index = raw.index.tz_convert("UTC")

        return raw[["open", "high", "low", "close", "volume"]].tail(n_bars)

    # ─── AGGREGAZIONE 5s → 5-min ──────────────────────────────────────────────

    def _on_realtime_bar(self, symbol: str, bars: Any, has_new_bar: bool) -> None:
        if not has_new_bar or not bars:
            return

        bar = bars[-1]

        # Normalizza bar.time a datetime UTC (ib_async può fornire datetime o int unix)
        raw_time = bar.time
        if isinstance(raw_time, datetime):
            bar_time = raw_time if raw_time.tzinfo else raw_time.replace(tzinfo=UTC)
        else:
            bar_time = datetime.fromtimestamp(int(raw_time), tz=UTC)

        window_start = _floor_to_5min(bar_time)
        current_window = self._window_starts.get(symbol, datetime.fromtimestamp(0, tz=UTC))

        if window_start > current_window:
            # La finestra 5-min è cambiata: flush del buffer precedente
            if self._buffers.get(symbol):
                aggregated = _aggregate(self._buffers[symbol], current_window)
                if aggregated is not None:
                    self._append_bar(symbol, aggregated)
                    asyncio.ensure_future(self._notify_callbacks(symbol))
            self._buffers[symbol] = []
            self._window_starts[symbol] = window_start

        self._buffers[symbol].append(bar)

    def _append_bar(self, symbol: str, row: dict[str, Any]) -> None:
        ts = pd.Timestamp(row["timestamp"])
        new_row = pd.DataFrame(
            [{"open": row["open"], "high": row["high"], "low": row["low"],
              "close": row["close"], "volume": row["volume"]}],
            index=pd.DatetimeIndex([ts], name="Datetime"),
        )
        existing = self._bars.get(symbol, pd.DataFrame())
        self._bars[symbol] = pd.concat([existing, new_row]).tail(_MAX_BARS_IN_MEMORY)

    async def _notify_callbacks(self, symbol: str) -> None:
        bars = self.get_bars(symbol)
        for callback in self._bar_callbacks:
            try:
                await callback(symbol, bars)
            except Exception as exc:
                logger.error("Errore nel bar callback per {}: {}", symbol, exc)


# ─── FUNZIONI PURE (testabili senza istanza) ──────────────────────────────────

def _floor_to_5min(dt: datetime) -> datetime:
    """Floor di un datetime all'inizio della finestra 5-min più vicina (UTC)."""
    ts = int(dt.timestamp())
    return datetime.fromtimestamp((ts // 300) * 300, tz=UTC)


def _aggregate(buf: list[Any], window_start: datetime) -> dict[str, Any] | None:
    """Costruisce un bar OHLCV 5-min dal buffer di bar 5s."""
    if not buf:
        return None
    return {
        "timestamp": window_start,
        "open": float(buf[0].open_),
        "high": float(max(b.high for b in buf)),
        "low": float(min(b.low for b in buf)),
        "close": float(buf[-1].close),
        "volume": int(sum(b.volume for b in buf)),
    }
