"""Implementation shortfall utilities."""

from __future__ import annotations

from execution_engine.constants import BPS
from execution_engine.types import Side


def implementation_shortfall_dollars(
    side: Side,
    quantity: float,
    execution_price: float,
    benchmark_price: float,
) -> float:
    """Return signed implementation shortfall as a positive cost."""
    return float(side.sign * quantity * (execution_price - benchmark_price))


def implementation_shortfall_bps(
    cost_dollars: float,
    quantity: float,
    benchmark_price: float,
) -> float:
    """Express implementation shortfall in basis points."""
    if quantity <= 0 or benchmark_price <= 0:
        return 0.0
    notional = quantity * benchmark_price
    return float(cost_dollars / notional / BPS)
