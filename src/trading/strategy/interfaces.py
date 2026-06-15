from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

import pandas as pd


class Direction(StrEnum):
    """Direzione di una posizione. SHORT richiede margin account abilitato su IBKR."""

    LONG = "LONG"
    SHORT = "SHORT"


# ─── DATACLASS DEI SEGNALI ────────────────────────────────────────────────────


@dataclass
class RawSignal:
    """
    Output di ISignalGenerator — segnale grezzo, non ancora dimensionato né allocato.
    Contiene la logica di mercato (direzione, forza, motivo) ma nessuna info di sizing.
    """

    symbol: str
    direction: Direction
    strength: float                         # 0.0–1.0: confidenza del segnale
    reason: str                             # descrizione human-readable per log e audit
    stop_loss_pct: float | None = None      # es. 0.02 = stop a -2% dall'entrata
    take_profit_pct: float | None = None
    generated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class AllocatedSignal(RawSignal):
    """
    RawSignal + sizing deciso da IPositionSizer e IPortfolioAllocator.
    target_usd e shares vengono popolati prima di passare a IExecutionAlgo.
    limit_price viene popolato da IExecutionAlgo al momento del piazzamento.
    """

    target_usd: float = 0.0         # dollari da impegnare
    shares: int = 0                 # azioni da comprare/vendere (calcolate da exec algo)
    limit_price: float | None = None


# ─── INTERFACCIA 1: UNIVERSE FILTER ──────────────────────────────────────────


class IUniverseFilter(ABC):
    """
    Filtra i simboli candidati all'inizio della sessione.
    Può escludere titoli per liquidità, volatilità implicita, notizie, settore, ecc.
    Chiamata una volta all'apertura del mercato, non a ogni bar.
    """

    @abstractmethod
    async def filter(self, candidates: list[str]) -> list[str]:
        """
        Args:
            candidates: simboli dell'universo configurato
        Returns:
            sottoinsieme dei candidati da monitorare oggi
        """
        ...


# ─── INTERFACCIA 2: SIGNAL GENERATOR ─────────────────────────────────────────


class ISignalGenerator(ABC):
    """
    Genera segnali a partire dai bar OHLCV + indicatori già calcolati.
    Chiamata a ogni nuovo bar 5-min per ogni simbolo filtrato.
    """

    warmup_bars: int = 50   # barre minime prima che il generatore produca segnali

    @abstractmethod
    async def generate(self, symbol: str, bars: pd.DataFrame) -> RawSignal | None:
        """
        Args:
            symbol: ticker IBKR
            bars:   DataFrame con colonne OHLCV + feature di pipeline.py,
                    index DatetimeIndex UTC, almeno `warmup_bars` righe
        Returns:
            RawSignal oppure None se nessun segnale
        """
        ...

    async def on_fill(
        self,
        symbol: str,
        direction: Direction,
        shares: int,
        price: float,
    ) -> None:
        """
        Callback opzionale — chiamato dopo ogni fill.
        Permette al generatore di aggiornare stato interno (es. flag "già in posizione").
        """


# ─── INTERFACCIA 3: POSITION SIZER ───────────────────────────────────────────


class IPositionSizer(ABC):
    """
    Calcola quanti dollari allocare a un singolo segnale.
    Operazione sincrona: nessun I/O, solo calcolo sul portafoglio corrente.
    """

    @abstractmethod
    def size(
        self,
        signal: RawSignal,
        portfolio_value: float,
        current_positions: dict[str, float],    # symbol → valore posizione in USD
    ) -> float:
        """Ritorna i dollari USD da impegnare per questo segnale."""
        ...


# ─── INTERFACCIA 4: PORTFOLIO ALLOCATOR ──────────────────────────────────────


class IPortfolioAllocator(ABC):
    """
    Gestisce segnali multipli simultanei e decide quali eseguire.
    Tiene conto del numero massimo di posizioni aperte, della correlazione
    e del capitale disponibile complessivo.
    Operazione sincrona: decide prima, ordina poi.
    """

    @abstractmethod
    def allocate(
        self,
        signals: list[RawSignal],
        sized_usds: list[float],                 # USD calcolati da IPositionSizer per ogni segnale
        current_positions: dict[str, float],     # symbol → valore posizione corrente in USD
    ) -> list[AllocatedSignal]:
        """
        Ritorna la lista di AllocatedSignal da eseguire (potenzialmente un sottoinsieme).
        Gli AllocatedSignal hanno target_usd impostato; shares e limit_price vengono
        completati da IExecutionAlgo.
        """
        ...


# ─── INTERFACCIA 5: EXECUTION ALGO ───────────────────────────────────────────


class IExecutionAlgo(ABC):
    """
    Traduce un AllocatedSignal in ordini IBKR concreti.
    Responsabilità:
    - calcolare il prezzo limite aggressivo (last ± 0.1%)
    - piazzare il LimitOrder
    - dopo il fill: piazzare il GTC StopOrder
    Operazione asincrona: interagisce con IBKR via IBClient/OrderManager.
    """

    @abstractmethod
    async def execute(self, signal: AllocatedSignal) -> None:
        """Piazza gli ordini. Non solleva eccezioni se il segnale viene ignorato per sicurezza."""
        ...


# ─── INTERFACCIA 6: EXIT LOGIC ────────────────────────────────────────────────


class IExitLogic(ABC):
    """
    Decide se uscire da una posizione aperta.
    Eseguita ogni 30 secondi su tutte le posizioni aperte, in parallelo
    rispetto al flusso di entrata (non blocca la generazione di nuovi segnali).
    """

    @abstractmethod
    async def should_exit(
        self,
        symbol: str,
        position_value: float,      # valore corrente della posizione in USD
        bars: pd.DataFrame,         # DataFrame aggiornato con feature
    ) -> bool:
        """True se la posizione va chiusa immediatamente."""
        ...
