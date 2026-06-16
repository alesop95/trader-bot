from dataclasses import dataclass

from loguru import logger

from trading.strategy.composer import StrategyComposer
from trading.strategy.interfaces import AllocatedSignal, Direction


@dataclass
class _StrategyEntry:
    composer: StrategyComposer
    capital_fraction: float     # quota del portafoglio totale assegnata a questa strategia


class StrategyRegistry:
    """
    Gestisce più StrategyComposer in parallelo, ognuno con una quota di capitale.
    Non contiene logica di trading: orchestra il lancio di ogni composer e aggrega i risultati.

    Utilizzo tipico:
        registry = StrategyRegistry()
        registry.register(ma_composer, capital_fraction=0.7)
        registry.register(mr_composer, capital_fraction=0.3)

        # a ogni bar:
        executed = await registry.run_bar(candidates, bars, total_portfolio, positions)

        # ogni 30 secondi:
        exits = await registry.run_exit_check(positions, bars)
    """

    def __init__(self) -> None:
        self._entries: list[_StrategyEntry] = []

    def register(self, composer: StrategyComposer, capital_fraction: float) -> None:
        """
        Aggiunge una strategia al registro.
        capital_fraction deve essere > 0 e la somma totale non può superare 1.0.
        La chiamata solleva ValueError se il vincolo non è soddisfatto.
        """
        if capital_fraction <= 0 or capital_fraction > 1:
            raise ValueError(
                f"capital_fraction deve essere (0, 1], ricevuto {capital_fraction}"
            )
        current_total = sum(e.capital_fraction for e in self._entries)
        if current_total + capital_fraction > 1.0 + 1e-9:
            raise ValueError(
                f"La somma delle capital_fraction supererebbe 1.0: "
                f"attuale {current_total:.2f} + nuova {capital_fraction:.2f}"
            )
        self._entries.append(_StrategyEntry(composer=composer, capital_fraction=capital_fraction))
        logger.info(
            "Strategia '{}' registrata (capital_fraction={:.0%})",
            composer.name, capital_fraction,
        )

    @property
    def names(self) -> list[str]:
        """Nomi delle strategie registrate, in ordine di registrazione."""
        return [e.composer.name for e in self._entries]

    async def run_bar(
        self,
        candidates: list[str],
        bars_by_symbol: dict,
        total_portfolio_value: float,
        current_positions: dict[str, float],
    ) -> list[AllocatedSignal]:
        """
        Lancia on_bar su ogni composer con il capitale scalato dalla rispettiva fraction.
        Le strategie girano in sequenza: ognuna vede le posizioni correnti al momento
        della sua chiamata. Per parallelismo futuro si può passare a asyncio.gather,
        ma la semantica sequenziale è più semplice da ragionare durante lo sviluppo.
        Ritorna tutti i segnali eseguiti aggregati.
        """
        all_executed: list[AllocatedSignal] = []
        for entry in self._entries:
            strategy_capital = total_portfolio_value * entry.capital_fraction
            try:
                executed = await entry.composer.on_bar(
                    candidates,
                    bars_by_symbol,
                    strategy_capital,
                    current_positions,
                )
                all_executed.extend(executed)
            except Exception as exc:
                logger.error(
                    "Errore in on_bar della strategia '{}': {}",
                    entry.composer.name, exc,
                )
        return all_executed

    async def run_exit_check(
        self,
        current_positions: dict[str, float],
        bars_by_symbol: dict,
    ) -> dict[str, list[str]]:
        """
        Esegue check_exits su ogni composer.
        Ritorna {strategy_name: [simboli da uscire]} — solo le strategie con almeno un simbolo.
        """
        result: dict[str, list[str]] = {}
        for entry in self._entries:
            try:
                to_exit = await entry.composer.check_exits(
                    current_positions, bars_by_symbol
                )
                if to_exit:
                    result[entry.composer.name] = to_exit
            except Exception as exc:
                logger.error(
                    "Errore in check_exits della strategia '{}': {}",
                    entry.composer.name, exc,
                )
        return result

    async def on_fill(
        self,
        symbol: str,
        direction: Direction,
        shares: int,
        price: float,
    ) -> None:
        """Propaga il fill a ogni composer registrato."""
        for entry in self._entries:
            try:
                await entry.composer.on_fill(symbol, direction, shares, price)
            except Exception as exc:
                logger.error(
                    "Errore in on_fill della strategia '{}': {}",
                    entry.composer.name, exc,
                )
