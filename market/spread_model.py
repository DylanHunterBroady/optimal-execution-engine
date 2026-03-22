"""Dynamic spread process."""

from __future__ import annotations

import numpy as np

from execution_engine.constants import BPS


def dynamic_spread_series(
    mid_prices: np.ndarray,
    base_spread_bps: float,
    volatility_curve: np.ndarray,
    liquidity_multiplier: np.ndarray,
    event_indicator: np.ndarray,
) -> np.ndarray:
    """Return a bucket-by-bucket full spread in price units."""
    normalized_vol = volatility_curve / max(volatility_curve.mean(), 1e-12)
    liquidity_penalty = np.maximum(1.0 / np.maximum(liquidity_multiplier, 1e-6) - 1.0, 0.0)
    spread_multiplier = 1.0 + 0.45 * (normalized_vol - 1.0) + 0.6 * liquidity_penalty + 0.5 * event_indicator
    spread_bps = np.clip(base_spread_bps * spread_multiplier, 0.5, None)
    return mid_prices * spread_bps * BPS
