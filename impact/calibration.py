"""Heuristic calibration helpers for stylized impact models."""

from __future__ import annotations

from execution_engine.constants import BPS


def calibrate_temporary_coefficient(
    reference_participation: float,
    reference_impact_bps: float,
    exponent: float,
) -> float:
    """Infer a coefficient from a target participation/impact pair."""
    if reference_participation <= 0:
        raise ValueError("reference_participation must be positive")
    return reference_impact_bps * BPS / reference_participation ** exponent


def calibrate_permanent_coefficient(
    order_fraction_of_adv: float,
    permanent_shift_bps: float,
) -> float:
    """Infer a permanent impact coefficient from an ADV-scaled order."""
    if order_fraction_of_adv <= 0:
        raise ValueError("order_fraction_of_adv must be positive")
    return permanent_shift_bps * BPS / order_fraction_of_adv
