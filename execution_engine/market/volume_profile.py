"""Intraday market volume curves."""

from __future__ import annotations

import numpy as np

from execution_engine.utils import normalize


def u_shaped_volume_profile(n_buckets: int, shape: str = "u_shaped") -> np.ndarray:
    """Return a normalized intraday volume curve."""
    x = np.linspace(0.0, 1.0, n_buckets)

    profile = (
        0.7
        + 1.25 * np.exp(-((x - 0.04) / 0.14) ** 2)
        + 1.15 * np.exp(-((x - 0.96) / 0.16) ** 2)
    )

    if shape == "front_loaded":
        profile += 0.45 * (1.0 - x)
    elif shape == "back_loaded":
        profile += 0.45 * x
    elif shape == "event_day":
        profile += 0.35 * np.exp(-((x - 0.5) / 0.09) ** 2)
    elif shape == "lunch_lull":
        profile -= 0.25 * np.exp(-((x - 0.5) / 0.18) ** 2)

    return normalize(profile)
