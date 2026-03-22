"""Queue-position penalties."""

from __future__ import annotations

from execution_engine.constants import EPSILON


def queue_penalty_cost(
    requested_quantity: float,
    depth_at_touch: float,
    base_penalty: float,
    price: float,
    liquidity_multiplier: float,
) -> float:
    """Return a per-share queue friction penalty."""
    queue_ratio = requested_quantity / max(depth_at_touch, EPSILON)
    liquidity_scale = max(liquidity_multiplier, EPSILON)
    return price * base_penalty * queue_ratio / liquidity_scale


def queue_fill_decay(
    requested_quantity: float,
    depth_at_touch: float,
    base_penalty: float,
) -> float:
    """Map queue load into a passive fill-rate discount."""
    queue_ratio = requested_quantity / max(depth_at_touch, EPSILON)
    return 1.0 / (1.0 + base_penalty * queue_ratio)
