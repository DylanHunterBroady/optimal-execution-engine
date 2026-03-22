"""Permanent impact model."""

from __future__ import annotations

from execution_engine.constants import EPSILON


def linear_permanent_impact(
    quantity: float,
    adv: float,
    price: float,
    coefficient: float,
) -> float:
    """Linear permanent impact as a fraction of ADV."""
    return price * coefficient * quantity / max(adv, EPSILON)
