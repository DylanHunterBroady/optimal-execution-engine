"""Intraday volatility surfaces."""

from __future__ import annotations

import numpy as np

from execution_engine.constants import TRADING_DAYS_PER_YEAR


def regime_volatility_multiplier(regime_name: str) -> float:
    """Bucket-volatility multiplier for named regimes."""
    mapping = {
        "low_vol_high_liquidity": 0.75,
        "high_vol_low_liquidity": 1.55,
        "event_day": 1.35,
        "trending_market": 1.05,
        "mean_reverting_market": 0.9,
        "neutral": 1.0,
    }
    return mapping.get(regime_name, 1.0)


def generate_intraday_volatility_curve(
    n_buckets: int,
    annualized_volatility: float,
    regime_name: str,
    rng: np.random.Generator,
) -> np.ndarray:
    """Generate bucket-by-bucket return volatility."""
    base_daily_vol = annualized_volatility / np.sqrt(TRADING_DAYS_PER_YEAR)
    base_bucket_vol = base_daily_vol / np.sqrt(max(n_buckets, 1))

    x = np.linspace(0.0, 1.0, n_buckets)
    u_shape = 0.9 + 0.5 * np.cos(2.0 * np.pi * x) ** 2
    event_bump = 1.0 + 0.55 * np.exp(-((x - 0.5) / 0.08) ** 2) if regime_name == "event_day" else 1.0
    noise = np.exp(0.06 * rng.normal(size=n_buckets))

    return base_bucket_vol * u_shape * event_bump * regime_volatility_multiplier(regime_name) * noise
