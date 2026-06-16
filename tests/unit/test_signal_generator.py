"""
Test unitari per MACrossoverSignalGenerator.
Il DataFrame viene costruito in linea senza dati di mercato reali.
asyncio_mode = 'auto' in pyproject.toml — nessun decorator necessario.
"""

import pandas as pd
import pytest

from trading.strategy.implementations.ma_crossover import MACrossoverSignalGenerator
from trading.strategy.interfaces import Direction, RawSignal

# ─── HELPER ──────────────────────────────────────────────────────────────────


def _bars(
    *,
    ema9_prev: float,
    ema21_prev: float,
    ema9_last: float,
    ema21_last: float,
    rsi: float = 60.0,
    macdh: float = 0.1,
    atr: float = 0.02,
    n_rows: int = 55,
) -> pd.DataFrame:
    """
    Costruisce un DataFrame con n_rows righe.
    Le ultime due righe usano i valori passati; le precedenti sono neutre
    (EMA9 == EMA21 — nessun crossover, no segnali spurii).
    """
    neutral = {
        "EMA_9": 10.0, "EMA_21": 10.0,
        "RSI_14": 50.0, "MACDh_12_26_9": 0.1, "ATRr_14": 0.02,
    }
    rows = [neutral.copy() for _ in range(n_rows - 2)]
    rows.append({
        "EMA_9": ema9_prev, "EMA_21": ema21_prev,
        "RSI_14": rsi, "MACDh_12_26_9": macdh, "ATRr_14": atr,
    })
    rows.append({
        "EMA_9": ema9_last, "EMA_21": ema21_last,
        "RSI_14": rsi, "MACDh_12_26_9": macdh, "ATRr_14": atr,
    })
    return pd.DataFrame(rows)


def _crossover_bars(**kwargs) -> pd.DataFrame:
    """Bar con bullish crossover canonico: EMA9 passa da sotto a sopra EMA21."""
    return _bars(
        ema9_prev=9.0, ema21_prev=10.0,   # EMA9 < EMA21
        ema9_last=11.0, ema21_last=10.0,  # EMA9 > EMA21 — crossover
        **kwargs,
    )


# ─── TEST ────────────────────────────────────────────────────────────────────


async def test_generates_signal_on_bullish_crossover():
    gen = MACrossoverSignalGenerator(rsi_max=70.0)
    signal = await gen.generate("AAPL", _crossover_bars())
    assert signal is not None
    assert isinstance(signal, RawSignal)
    assert signal.symbol == "AAPL"
    assert signal.direction == Direction.LONG


async def test_no_signal_when_already_in_position():
    gen = MACrossoverSignalGenerator()
    await gen.on_fill("AAPL", Direction.LONG, 10, 150.0)
    signal = await gen.generate("AAPL", _crossover_bars())
    assert signal is None


async def test_signal_resumes_after_exit_fill():
    gen = MACrossoverSignalGenerator()
    await gen.on_fill("AAPL", Direction.LONG, 10, 150.0)   # entrata
    await gen.on_fill("AAPL", Direction.SHORT, 10, 155.0)  # uscita (SELL)
    signal = await gen.generate("AAPL", _crossover_bars())
    assert signal is not None


async def test_no_signal_rsi_at_max():
    gen = MACrossoverSignalGenerator(rsi_max=70.0)
    signal = await gen.generate("AAPL", _crossover_bars(rsi=70.0))
    assert signal is None


async def test_no_signal_rsi_above_max():
    gen = MACrossoverSignalGenerator(rsi_max=70.0)
    signal = await gen.generate("AAPL", _crossover_bars(rsi=75.0))
    assert signal is None


async def test_no_signal_macdh_zero():
    gen = MACrossoverSignalGenerator()
    signal = await gen.generate("AAPL", _crossover_bars(macdh=0.0))
    assert signal is None


async def test_no_signal_macdh_negative():
    gen = MACrossoverSignalGenerator()
    signal = await gen.generate("AAPL", _crossover_bars(macdh=-0.1))
    assert signal is None


async def test_no_signal_when_no_crossover_already_above():
    # EMA9 era già sopra EMA21 nel bar precedente — non è un crossover fresco
    gen = MACrossoverSignalGenerator()
    bars = _bars(
        ema9_prev=11.0, ema21_prev=10.0,   # già sopra
        ema9_last=12.0, ema21_last=10.0,   # ancora sopra
    )
    signal = await gen.generate("AAPL", bars)
    assert signal is None


async def test_no_signal_when_ema9_still_below():
    # Nessun crossover: EMA9 rimane sotto EMA21
    gen = MACrossoverSignalGenerator()
    bars = _bars(
        ema9_prev=9.0, ema21_prev=10.0,
        ema9_last=9.5, ema21_last=10.0,
    )
    signal = await gen.generate("AAPL", bars)
    assert signal is None


async def test_strength_is_within_bounds():
    gen = MACrossoverSignalGenerator()
    signal = await gen.generate("AAPL", _crossover_bars())
    assert signal is not None
    assert 0.01 <= signal.strength <= 1.0


async def test_stop_loss_pct_set_from_atr():
    gen = MACrossoverSignalGenerator()
    signal = await gen.generate("AAPL", _crossover_bars(atr=0.02))
    assert signal is not None
    assert signal.stop_loss_pct == pytest.approx(0.04)   # atr * 2.0


async def test_multiple_symbols_tracked_independently():
    gen = MACrossoverSignalGenerator()
    await gen.on_fill("AAPL", Direction.LONG, 10, 150.0)
    # AAPL in posizione — nessun segnale
    assert await gen.generate("AAPL", _crossover_bars()) is None
    # MSFT non in posizione — segnale atteso
    assert await gen.generate("MSFT", _crossover_bars()) is not None
