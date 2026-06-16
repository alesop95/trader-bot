"""
Test unitari per CircuitBreaker e RiskManager.
Nessun I/O, nessun DB, nessun IBKR: i getter di stato sono lambda in linea.
"""

from datetime import UTC, datetime

import pytest

from trading.risk.circuit_breaker import CircuitBreaker, CircuitState
from trading.risk.manager import RiskManager
from trading.strategy.interfaces import AllocatedSignal, Direction

# ─── FIXTURE HELPERS ─────────────────────────────────────────────────────────


def _signal(symbol: str = "AAPL", target_usd: float = 1000.0) -> AllocatedSignal:
    return AllocatedSignal(
        symbol=symbol,
        direction=Direction.LONG,
        strength=0.5,
        reason="test",
        target_usd=target_usd,
    )


def _manager(
    cb: CircuitBreaker | None = None,
    positions: dict[str, float] | None = None,
    daily_pnl: float = 0.0,
    max_position_usd: float = 5000.0,
    max_daily_loss_usd: float = 1000.0,
    max_open_positions: int = 5,
) -> RiskManager:
    return RiskManager(
        circuit_breaker=cb or CircuitBreaker(),
        positions_getter=lambda: positions if positions is not None else {},
        daily_pnl_getter=lambda: daily_pnl,
        max_position_usd=max_position_usd,
        max_daily_loss_usd=max_daily_loss_usd,
        max_open_positions=max_open_positions,
    )


# ─── CIRCUIT BREAKER ─────────────────────────────────────────────────────────


def test_circuit_breaker_initial_state_is_closed():
    cb = CircuitBreaker()
    assert cb.state == CircuitState.CLOSED
    assert not cb.is_open()


def test_circuit_breaker_opens_at_threshold():
    cb = CircuitBreaker(failure_threshold=3)
    cb.record_failure("e1")
    cb.record_failure("e2")
    assert cb.state == CircuitState.CLOSED   # sotto soglia
    cb.record_failure("e3")
    assert cb.state == CircuitState.OPEN
    assert cb.is_open()


def test_circuit_breaker_under_threshold_stays_closed():
    cb = CircuitBreaker(failure_threshold=5)
    for _ in range(4):
        cb.record_failure("err")
    assert cb.state == CircuitState.CLOSED


def test_circuit_breaker_open_to_half_open_after_recovery():
    cb = CircuitBreaker(failure_threshold=1, recovery_seconds=60.0)
    cb.record_failure("err")
    assert cb._state == CircuitState.OPEN
    # Simula il passaggio del tempo modificando _opened_at
    cb._opened_at = datetime(2000, 1, 1, tzinfo=UTC)
    assert cb.state == CircuitState.HALF_OPEN
    assert cb.is_open()   # HALF_OPEN blocca ancora


def test_circuit_breaker_half_open_success_closes():
    cb = CircuitBreaker(failure_threshold=1, recovery_seconds=60.0)
    cb.record_failure("err")
    cb._opened_at = datetime(2000, 1, 1, tzinfo=UTC)
    _ = cb.state   # avanza a HALF_OPEN
    cb.record_success()
    assert cb.state == CircuitState.CLOSED
    assert not cb.is_open()


def test_circuit_breaker_half_open_failure_reopens():
    cb = CircuitBreaker(failure_threshold=1, recovery_seconds=60.0)
    cb.record_failure("err")
    cb._opened_at = datetime(2000, 1, 1, tzinfo=UTC)
    _ = cb.state   # avanza a HALF_OPEN
    cb.record_failure("ripetuto")
    assert cb.state == CircuitState.OPEN


def test_circuit_breaker_success_in_closed_is_noop():
    cb = CircuitBreaker()
    cb.record_success()   # non deve sollevare e non deve cambiare stato
    assert cb.state == CircuitState.CLOSED


def test_circuit_breaker_reset_from_open():
    cb = CircuitBreaker(failure_threshold=1)
    cb.record_failure("err")
    assert cb.is_open()
    cb.reset()
    assert cb.state == CircuitState.CLOSED
    assert not cb.is_open()


# ─── RISK MANAGER ────────────────────────────────────────────────────────────


def test_risk_manager_passes_clean_signal():
    rm = _manager()
    sig = _signal(target_usd=1000.0)
    result = rm.validate(sig)
    assert result is sig


def test_risk_manager_blocks_when_circuit_breaker_open():
    cb = CircuitBreaker(failure_threshold=1)
    cb.record_failure("err")
    rm = _manager(cb=cb)
    assert rm.validate(_signal()) is None


def test_risk_manager_blocks_on_max_daily_loss():
    rm = _manager(daily_pnl=-1000.0, max_daily_loss_usd=1000.0)
    assert rm.validate(_signal()) is None


def test_risk_manager_blocks_just_above_daily_loss():
    rm = _manager(daily_pnl=-1001.0, max_daily_loss_usd=1000.0)
    assert rm.validate(_signal()) is None


def test_risk_manager_passes_just_below_daily_loss():
    rm = _manager(daily_pnl=-999.0, max_daily_loss_usd=1000.0)
    assert rm.validate(_signal()) is not None


def test_risk_manager_blocks_when_max_positions_reached():
    positions = {"AAPL": 1000.0, "MSFT": 1000.0, "NVDA": 1000.0}
    rm = _manager(positions=positions, max_open_positions=3)
    assert rm.validate(_signal("GOOGL")) is None


def test_risk_manager_passes_when_below_max_positions():
    positions = {"AAPL": 1000.0, "MSFT": 1000.0}
    rm = _manager(positions=positions, max_open_positions=3)
    assert rm.validate(_signal("NVDA")) is not None


def test_risk_manager_clamps_target_usd_to_cap():
    rm = _manager(max_position_usd=2000.0)
    sig = _signal(target_usd=5000.0)
    result = rm.validate(sig)
    assert result is not None
    assert result.target_usd == pytest.approx(2000.0)


def test_risk_manager_does_not_clamp_when_within_cap():
    rm = _manager(max_position_usd=5000.0)
    sig = _signal(target_usd=1000.0)
    result = rm.validate(sig)
    assert result is not None
    assert result.target_usd == pytest.approx(1000.0)


def test_risk_manager_zero_positions_are_not_counted():
    # Posizione con valore 0 (chiusa) non deve occupare uno slot
    positions = {"AAPL": 0.0, "MSFT": 0.0}
    rm = _manager(positions=positions, max_open_positions=1)
    assert rm.validate(_signal("NVDA")) is not None
