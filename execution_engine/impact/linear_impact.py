"""Linear temporary impact model."""

from __future__ import annotations

from execution_engine.constants import EPSILON


def linear_temporary_impact(
    quantity: float,
    bucket_volume: float,
    price: float,
    coefficient: float,
    liquidity_multiplier: float = 1.0,
) -> float:
    """Temporary impact proportional to participation."""
    participation = quantity / max(bucket_volume, EPSILON)
    liquidity_scale = max(liquidity_multiplier, EPSILON)
    return price * coefficient * participation / liquidity_scale
