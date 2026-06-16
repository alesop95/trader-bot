from collections.abc import Callable

import pandas as pd
from loguru import logger

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

# RiskValidator: riceve un AllocatedSignal, ritorna il segnale (eventualmente modificato)
# oppure None se deve essere bloccato. Corrisponde a RiskManager.validate().
RiskValidator = Callable[[AllocatedSignal], AllocatedSignal | None]


class StrategyComposer:
    """
    Collante delle 6 interfacce per una singola strategia. Non contiene logica di trading.

    Flusso on_bar:
      IUniverseFilter → ISignalGenerator → IPositionSizer → [risk_validator] →
      IPortfolioAllocator → IExecutionAlgo

    IExitLogic gira separatamente via check_exits(), ogni 30 secondi.
    Il risk_validator (RiskManager.validate) è iniettato come callable: questo
    mantiene strategy/ disaccoppiato da risk/ a livello di import.
    """

    def __init__(
        self,
        name: str,
        universe_filter: IUniverseFilter,
        signal_generator: ISignalGenerator,
        position_sizer: IPositionSizer,
        portfolio_allocator: IPortfolioAllocator,
        execution_algo: IExecutionAlgo,
        exit_logic: IExitLogic,
        risk_validator: RiskValidator | None = None,
    ) -> None:
        self.name = name
        self._filter = universe_filter
        self._generator = signal_generator
        self._sizer = position_sizer
        self._allocator = portfolio_allocator
        self._executor = execution_algo
        self._exit_logic = exit_logic
        self._risk_validator = risk_validator

    async def on_bar(
        self,
        candidates: list[str],
        bars_by_symbol: dict[str, pd.DataFrame],
        portfolio_value: float,
        current_positions: dict[str, float],
    ) -> list[AllocatedSignal]:
        """
        Esegue il ciclo completo per un bar 5-min.
        portfolio_value: capitale assegnato a questa strategia (già scalato dalla StrategyRegistry).
        Ritorna i segnali effettivamente eseguiti.
        """
        # 1 — Filtra l'universo
        filtered = await self._filter.filter(candidates)
        if not filtered:
            return []

        # 2 — Genera segnali
        raw_signals: list[RawSignal] = []
        for symbol in filtered:
            bars = bars_by_symbol.get(symbol)
            if bars is None or len(bars) < self._generator.warmup_bars:
                continue
            signal = await self._generator.generate(symbol, bars)
            if signal is not None:
                raw_signals.append(signal)

        if not raw_signals:
            return []

        # 3 — Sizing (sincrono, puro calcolo)
        sized_usds = [
            self._sizer.size(sig, portfolio_value, current_positions)
            for sig in raw_signals
        ]

        # 4 — Allocazione (decide quali segnali eseguire date le posizioni correnti)
        allocated = self._allocator.allocate(raw_signals, sized_usds, current_positions)

        # 5 — Validazione risk + esecuzione
        executed: list[AllocatedSignal] = []
        for signal in allocated:
            validated = (
                self._risk_validator(signal)
                if self._risk_validator is not None
                else signal
            )
            if validated is None:
                logger.info(
                    "[{}] segnale {} {} bloccato dal risk validator",
                    self.name, signal.direction, signal.symbol,
                )
                continue
            await self._executor.execute(validated)
            executed.append(validated)

        return executed

    async def check_exits(
        self,
        current_positions: dict[str, float],
        bars_by_symbol: dict[str, pd.DataFrame],
    ) -> list[str]:
        """
        Controlla le posizioni aperte con IExitLogic.
        Ritorna i simboli per cui è stata richiesta l'uscita immediata.
        """
        to_exit: list[str] = []
        for symbol, position_value in current_positions.items():
            if position_value == 0:
                continue
            bars = bars_by_symbol.get(symbol)
            if bars is None or bars.empty:
                continue
            try:
                if await self._exit_logic.should_exit(symbol, position_value, bars):
                    to_exit.append(symbol)
            except Exception as exc:
                logger.error("[{}] errore in should_exit per {}: {}", self.name, symbol, exc)
        return to_exit

    async def on_fill(
        self,
        symbol: str,
        direction: Direction,
        shares: int,
        price: float,
    ) -> None:
        """Propaga il fill al signal generator per aggiornare lo stato interno."""
        await self._generator.on_fill(symbol, direction, shares, price)
