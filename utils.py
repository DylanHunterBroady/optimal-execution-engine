"""Small utility helpers."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any

import numpy as np

from execution_engine.constants import EPSILON, TRADING_MINUTES_PER_DAY
from execution_engine.types import Side


def to_serializable(value: Any) -> Any:
    """Convert dataclasses and numpy values into JSON-friendly objects."""
    if is_dataclass(value):
        return {k: to_serializable(v) for k, v in asdict(value).items()}
    if isinstance(value, dict):
        return {str(k): to_serializable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_serializable(v) for v in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    return value


def get_rng(seed: int | None) -> np.random.Generator:
    """Return a local generator for reproducible simulations."""
    return np.random.default_rng(seed)


def normalize(values: np.ndarray) -> np.ndarray:
    """Return a normalized positive vector."""
    clipped = np.clip(values.astype(float), EPSILON, None)
    return clipped / clipped.sum()


def clip_non_negative(values: np.ndarray | float) -> np.ndarray | float:
    """Clip a scalar or vector at zero."""
    return np.clip(values, 0.0, None)


def side_sign(side: Side | str) -> int:
    """Return the sign of an order side."""
    return Side(side).sign


def participation_rate(quantity: float, bucket_volume: float) -> float:
    """Shares executed as a fraction of market volume."""
    return float(quantity / max(bucket_volume, EPSILON))


def annualized_vol_to_bucket_sigma(annualized_volatility: float, horizon_buckets: int) -> float:
    """Convert annualized volatility to a single bucket standard deviation."""
    return annualized_volatility / np.sqrt(252.0 * max(horizon_buckets, 1))


def parse_time_to_minutes(clock_time: str) -> int:
    """Convert a HH:MM string into minutes since midnight."""
    hour_text, minute_text = clock_time.split(":")
    return int(hour_text) * 60 + int(minute_text)


def horizon_fraction(start_time: str, end_time: str) -> float:
    """Portion of the trading day covered by the execution window."""
    total_minutes = max(parse_time_to_minutes(end_time) - parse_time_to_minutes(start_time), 1)
    return total_minutes / TRADING_MINUTES_PER_DAY


def evenly_spaced_minutes(start_time: str, end_time: str, buckets: int) -> np.ndarray:
    """Create evenly spaced bucket start times in minutes."""
    start = parse_time_to_minutes(start_time)
    end = parse_time_to_minutes(end_time)
    return np.linspace(start, end, num=buckets, endpoint=False)
