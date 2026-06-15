import pandas as pd
import pandas_ta_classic as ta

# Barre minime necessarie prima che gli indicatori siano affidabili.
# Determinato dal lookback più lungo: MACD slow=26, EMA_50=50.
MIN_BARS: int = 50

# Strategia pandas-ta-classic calcolata una volta a livello modulo.
# Colonne aggiunte (verificato su pandas-ta-classic 0.6.20):
#   EMA_9, EMA_21, EMA_50
#   RSI_14
#   ATRr_14         (ATR normalizzato su close — per stop loss assoluto moltiplicare × close)
#   BBL_20_2.0, BBM_20_2.0, BBU_20_2.0, BBB_20_2.0, BBP_20_2.0
#   MACD_12_26_9, MACDh_12_26_9, MACDs_12_26_9
_STRATEGY = ta.Strategy(
    name="trading_bot",
    description="Indicatori core per MA crossover e strategie future",
    ta=[
        {"kind": "ema", "length": 9},
        {"kind": "ema", "length": 21},
        {"kind": "ema", "length": 50},
        {"kind": "rsi", "length": 14},
        {"kind": "atr", "length": 14},
        {"kind": "bbands", "length": 20},
        {"kind": "macd"},
    ],
)


def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggiunge colonne di indicatori tecnici e feature custom al DataFrame OHLCV.

    Input:  df con colonne [open, high, low, close, volume], index DatetimeIndex UTC.
            Richiede almeno 2 righe; le prime MIN_BARS-1 righe avranno NaN sugli indicatori.
    Output: copia del DataFrame con le colonne aggiuntive.
    """
    if len(df) < 2:
        return df.copy()

    out = df.copy()

    # Indicatori tecnici via pandas-ta-classic
    out.ta.strategy(_STRATEGY)

    # vol_ratio: volume corrente / media 20-bar — individua bar ad alta partecipazione
    vol_ma20 = out["volume"].rolling(20).mean()
    out["vol_ratio"] = out["volume"] / vol_ma20.where(vol_ma20 > 0)

    # gap_pct: (open - close_precedente) / close_precedente — gap overnight
    out["gap_pct"] = (out["open"] - out["close"].shift(1)) / out["close"].shift(1)

    return out


def has_enough_bars(df: pd.DataFrame, required: int = MIN_BARS) -> bool:
    """True se il DataFrame ha almeno `required` righe con close non-NaN."""
    return int(df["close"].notna().sum()) >= required if "close" in df.columns else False
