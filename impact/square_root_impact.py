"""Square-root temporary impact model."""

from __future__ import annotations

from execution_engine.constants import EPSILON


def square_root_temporary_impact(
    quantity: float,
    bucket_volume: float,
    price: float,
    coefficient: float,
    exponent: float = 0.5,
    liquidity_multiplier: float = 1.0,
) -> float:
    """Square-root style participation impact."""
    participation = quantity / max(bucket_volume, EPSILON)
    liquidity_scale = max(liquidity_multiplier, EPSILON)
    return price * coefficient * participation ** exponent / liquidity_scale
