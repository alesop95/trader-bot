"""
Test unitari per FixedFractionSizer.
Verifica il calcolo della size e l'interazione con le posizioni esistenti.
"""

import pytest

from trading.strategy.implementations.ma_crossover import FixedFractionSizer
from trading.strategy.interfaces import Direction, RawSignal


def _raw(symbol: str = "AAPL") -> RawSignal:
    return RawSignal(symbol=symbol, direction=Direction.LONG, strength=0.5, reason="test")


def test_basic_size_no_existing_position():
    sizer = FixedFractionSizer(fraction=0.05)
    result = sizer.size(_raw(), portfolio_value=10_000.0, current_positions={})
    assert result == pytest.approx(500.0)


def test_existing_position_reduces_available_size():
    sizer = FixedFractionSizer(fraction=0.05)
    result = sizer.size(
        _raw("AAPL"),
        portfolio_value=10_000.0,
        current_positions={"AAPL": 200.0},
    )
    assert result == pytest.approx(300.0)


def test_existing_position_at_cap_returns_zero():
    sizer = FixedFractionSizer(fraction=0.05)
    result = sizer.size(
        _raw("AAPL"),
        portfolio_value=10_000.0,
        current_positions={"AAPL": 500.0},
    )
    assert result == pytest.approx(0.0)


def test_existing_position_above_cap_returns_zero():
    # Posizione già oltre il cap (es. apprezzamento) — non aggiunge
    sizer = FixedFractionSizer(fraction=0.05)
    result = sizer.size(
        _raw("AAPL"),
        portfolio_value=10_000.0,
        current_positions={"AAPL": 700.0},
    )
    assert result == pytest.approx(0.0)


def test_other_symbol_positions_do_not_affect_size():
    sizer = FixedFractionSizer(fraction=0.05)
    result = sizer.size(
        _raw("MSFT"),
        portfolio_value=10_000.0,
        current_positions={"AAPL": 500.0},   # simbolo diverso
    )
    assert result == pytest.approx(500.0)


def test_different_portfolio_values():
    sizer = FixedFractionSizer(fraction=0.10)
    result_50k = sizer.size(_raw(), portfolio_value=50_000.0, current_positions={})
    result_1k = sizer.size(_raw(), portfolio_value=1_000.0, current_positions={})
    assert result_50k == pytest.approx(5000.0)
    assert result_1k == pytest.approx(100.0)


def test_fraction_at_boundary_one():
    sizer = FixedFractionSizer(fraction=1.0)
    result = sizer.size(_raw(), portfolio_value=10_000.0, current_positions={})
    assert result == pytest.approx(10_000.0)


def test_invalid_fraction_zero_raises():
    with pytest.raises(ValueError):
        FixedFractionSizer(fraction=0.0)


def test_invalid_fraction_negative_raises():
    with pytest.raises(ValueError):
        FixedFractionSizer(fraction=-0.1)


def test_invalid_fraction_above_one_raises():
    with pytest.raises(ValueError):
        FixedFractionSizer(fraction=1.01)
