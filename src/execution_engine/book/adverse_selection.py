"""Adverse selection penalty approximation."""

from __future__ import annotations

from execution_engine.types import Side


def adverse_selection_penalty(
    side: Side,
    price: float,
    alpha: float,
    bucket_sigma: float,
    coefficient: float,
    aggression: float,
    event_indicator: float,
) -> float:
    """Expected per-share cost from trading ahead of informed flow."""
    directional_move = max(side.sign * alpha, 0.0)
    volatility_component = 0.35 * bucket_sigma * aggression
    event_component = 0.15 * bucket_sigma * event_indicator
    return price * coefficient * (directional_move + volatility_component + event_component)
