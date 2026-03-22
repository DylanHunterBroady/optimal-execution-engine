"""Top-of-book state abstraction."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class LOBState:
    """Stylized top-of-book state for a single bucket."""

    mid_price: float
    half_spread: float
    depth_at_touch: float
    realized_volume: float
    liquidity_multiplier: float
    refill_rate: float
    alpha: float
    bucket_sigma: float
    event_indicator: float

    @classmethod
    def from_market_row(cls, row: pd.Series, adjusted_mid_price: float) -> "LOBState":
        """Build a book state from the market path and current permanent shift."""
        return cls(
            mid_price=float(adjusted_mid_price),
            half_spread=float(row["half_spread"]),
            depth_at_touch=float(row["depth_at_touch"]),
            realized_volume=float(row["realized_volume"]),
            liquidity_multiplier=float(row["liquidity_multiplier"]),
            refill_rate=float(row["refill_rate"]),
            alpha=float(row["alpha"]),
            bucket_sigma=float(row["bucket_sigma"]),
            event_indicator=float(row["event_indicator"]),
        )
