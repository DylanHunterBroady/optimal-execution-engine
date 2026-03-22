"""Constraint helpers for schedule optimization."""

from __future__ import annotations

import numpy as np


def is_schedule_complete(schedule: np.ndarray, total_quantity: float, tolerance: float = 1e-6) -> bool:
    """Check that a schedule fully executes the parent order."""
    return abs(float(schedule.sum() - total_quantity)) <= tolerance


def max_participation_violations(
    schedule: np.ndarray,
    expected_volume: np.ndarray,
    max_participation_rate: float,
) -> np.ndarray:
    """Per-bucket participation cap violations."""
    return np.clip(schedule - max_participation_rate * expected_volume, 0.0, None)


def project_schedule_to_constraints(
    schedule: np.ndarray,
    total_quantity: float,
    expected_volume: np.ndarray,
    max_participation_rate: float,
    min_child_order_size: float,
) -> np.ndarray:
    """Repair a schedule to satisfy basic positivity and completion constraints."""
    schedule = np.clip(schedule.astype(float), 0.0, None)
    cap = max_participation_rate * np.clip(expected_volume.astype(float), 1.0, None)
    repaired = np.minimum(schedule, cap)

    if min_child_order_size > 0:
        small_nonzero = (repaired > 0.0) & (repaired < min_child_order_size)
        repaired[small_nonzero] = 0.0

    shortfall = total_quantity - repaired.sum()
    if shortfall > 0:
        for bucket in range(len(repaired) - 1, -1, -1):
            available = max(cap[bucket] - repaired[bucket], 0.0)
            take = min(shortfall, available)
            repaired[bucket] += take
            shortfall -= take
            if shortfall <= 1e-9:
                break
    if shortfall > 0:
        repaired[-1] += shortfall

    excess = repaired.sum() - total_quantity
    if excess > 0:
        for bucket in range(len(repaired) - 1, -1, -1):
            removable = repaired[bucket]
            take = min(excess, removable)
            repaired[bucket] -= take
            excess -= take
            if excess <= 1e-9:
                break
    return repaired
