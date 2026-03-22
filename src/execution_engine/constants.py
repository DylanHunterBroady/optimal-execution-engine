"""Project-wide constants."""

from __future__ import annotations

TRADING_DAYS_PER_YEAR = 252
TRADING_MINUTES_PER_DAY = 390
BPS = 1e-4
EPSILON = 1e-12

DEFAULT_STRATEGIES = [
    "twap",
    "vwap",
    "pov",
    "implementation_shortfall",
    "almgren_chriss",
    "adaptive_policy",
]

SUPPORTED_REGIMES = {
    "low_vol_high_liquidity",
    "high_vol_low_liquidity",
    "event_day",
    "trending_market",
    "mean_reverting_market",
    "neutral",
}
