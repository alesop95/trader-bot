from collections.abc import Callable

from loguru import logger

from trading.risk.circuit_breaker import CircuitBreaker
from trading.strategy.interfaces import AllocatedSignal


class RiskManager:
    """
    Gate obbligatorio tra IPortfolioAllocator e IExecutionAlgo.

    validate() implementa il tipo RiskValidator definito in strategy/composer.py:
      Callable[[AllocatedSignal], AllocatedSignal | None]
    Restituisce None per bloccare il segnale, oppure l'AllocatedSignal
    (eventualmente con target_usd ridotto) per approvarlo.

    Controlli in ordine:
      1. Circuit breaker aperto → blocca tutto
      2. Perdita giornaliera >= max_daily_loss_usd → blocca nuovi ingressi
      3. Numero posizioni aperte >= max_open_positions → blocca
      4. target_usd > max_position_usd → riduce al cap (non blocca)

    Le soglie vengono lette da config.py tramite build_risk_manager(),
    che è il punto di cablaggio consigliato da main.py.
    """

    def __init__(
        self,
        circuit_breaker: CircuitBreaker,
        positions_getter: Callable[[], dict[str, float]],
        daily_pnl_getter: Callable[[], float],
        *,
        max_position_usd: float,
        max_daily_loss_usd: float,
        max_open_positions: int,
    ) -> None:
        self._cb = circuit_breaker
        self._positions_getter = positions_getter
        self._daily_pnl_getter = daily_pnl_getter
        self._max_position_usd = max_position_usd
        self._max_daily_loss_usd = max_daily_loss_usd
        self._max_open_positions = max_open_positions

    def validate(self, signal: AllocatedSignal) -> AllocatedSignal | None:
        """Chiamato da StrategyComposer come risk_validator(signal)."""

        # 1 — Circuit breaker
        if self._cb.is_open():
            logger.warning(
                "RiskManager: blocca {} — circuit breaker {} aperto",
                signal.symbol, self._cb.state,
            )
            return None

        # 2 — Perdita giornaliera
        daily_pnl = self._daily_pnl_getter()
        if daily_pnl <= -self._max_daily_loss_usd:
            logger.warning(
                "RiskManager: blocca {} — perdita giornaliera {:.0f} USD >= soglia {:.0f} USD",
                signal.symbol, abs(daily_pnl), self._max_daily_loss_usd,
            )
            return None

        # 3 — Numero posizioni aperte
        positions = self._positions_getter()
        open_count = sum(1 for v in positions.values() if v > 0)
        if open_count >= self._max_open_positions:
            logger.info(
                "RiskManager: blocca {} — {} posizioni aperte su {} consentite",
                signal.symbol, open_count, self._max_open_positions,
            )
            return None

        # 4 — Cap per singola posizione (modifica, non blocca)
        if signal.target_usd > self._max_position_usd:
            logger.info(
                "RiskManager: {} target_usd ridotto da {:.0f} a {:.0f} (cap per posizione)",
                signal.symbol, signal.target_usd, self._max_position_usd,
            )
            signal.target_usd = self._max_position_usd

        return signal


# ─── FACTORY ─────────────────────────────────────────────────────────────────


def build_risk_manager(
    circuit_breaker: CircuitBreaker,
    positions_getter: Callable[[], dict[str, float]],
    daily_pnl_getter: Callable[[], float],
) -> RiskManager:
    """
    Costruisce RiskManager leggendo i limiti da settings.
    main.py chiama questa funzione passando i getter collegati allo stato live:
      positions_getter  → lambda: market_data_manager.current_positions()
      daily_pnl_getter  → lambda: repository.get_today_pnl()
    """
    from trading.config import settings

    return RiskManager(
        circuit_breaker=circuit_breaker,
        positions_getter=positions_getter,
        daily_pnl_getter=daily_pnl_getter,
        max_position_usd=settings.max_position_size_usd,
        max_daily_loss_usd=settings.max_daily_loss_usd,
        max_open_positions=settings.max_open_positions,
    )
