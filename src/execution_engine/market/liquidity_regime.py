"""Liquidity and drift regime generation."""

from __future__ import annotations

import numpy as np


def generate_liquidity_state(
    n_buckets: int,
    regime_name: str,
    drift_regime: str,
    mean_reversion_strength: float,
    rng: np.random.Generator,
) -> dict[str, np.ndarray]:
    """Generate liquidity multipliers, drift terms, and event indicators."""
    x = np.linspace(0.0, 1.0, n_buckets)
    event_indicator = np.exp(-((x - 0.5) / 0.08) ** 2) if regime_name == "event_day" else np.zeros(n_buckets)

    liquidity_base = np.ones(n_buckets)
    depth_base = np.ones(n_buckets)

    if regime_name == "low_vol_high_liquidity":
        liquidity_base *= 1.35
        depth_base *= 1.4
    elif regime_name == "high_vol_low_liquidity":
        liquidity_base *= 0.7
        depth_base *= 0.75
    elif regime_name == "event_day":
        liquidity_base *= 0.95 - 0.35 * event_indicator
        depth_base *= 0.9 - 0.4 * event_indicator
    elif regime_name == "trending_market":
        liquidity_base *= 1.0 + 0.12 * x
    elif regime_name == "mean_reverting_market":
        liquidity_base *= 0.95 + 0.08 * np.sin(4.0 * np.pi * x)

    liquidity_multiplier = np.clip(liquidity_base * np.exp(0.08 * rng.normal(size=n_buckets)), 0.35, 2.5)
    depth_multiplier = np.clip(depth_base * np.exp(0.06 * rng.normal(size=n_buckets)), 0.35, 2.5)

    if drift_regime in {"uptrend", "trending_up"}:
        alpha = np.full(n_buckets, 0.12 / (252.0 * n_buckets))
    elif drift_regime in {"downtrend", "trending_down"}:
        alpha = np.full(n_buckets, -0.12 / (252.0 * n_buckets))
    elif drift_regime in {"event", "event_day"}:
        alpha = 0.3 / (252.0 * n_buckets) * event_indicator
    elif drift_regime in {"mean_revert", "mean_reverting"}:
        alpha = -mean_reversion_strength * np.sin(2.0 * np.pi * x) / (252.0 * n_buckets)
    else:
        alpha = np.zeros(n_buckets)

    return {
        "liquidity_multiplier": liquidity_multiplier,
        "depth_multiplier": depth_multiplier,
        "alpha": alpha,
        "event_indicator": event_indicator,
    }
