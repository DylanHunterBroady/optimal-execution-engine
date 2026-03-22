"""Expected execution cost and risk objective."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from execution_engine.constants import EPSILON


def inventory_path(total_quantity: float, schedule: np.ndarray) -> np.ndarray:
    """Remaining inventory after each bucket."""
    return total_quantity - np.cumsum(schedule)


@dataclass(frozen=True)
class ObjectiveTerms:
    """Decomposed deterministic objective terms."""

    expected_cost: float
    temporary_cost: float
    spread_cost: float
    permanent_cost: float
    risk_cost: float
    smoothness_penalty: float
    participation_penalty: float
    completion_penalty: float


def evaluate_objective_terms(
    schedule: np.ndarray,
    total_quantity: float,
    expected_volume: np.ndarray,
    bucket_sigma: np.ndarray,
    price: float,
    adv: float,
    half_spread: np.ndarray,
    temporary_impact_coefficient: float,
    permanent_impact_coefficient: float,
    impact_exponent: float,
    risk_aversion: float,
    max_participation_rate: float,
    penalty_weights: dict[str, float],
) -> ObjectiveTerms:
    """Evaluate expected cost plus penalties for a deterministic schedule."""
    safe_volume = np.clip(expected_volume.astype(float), EPSILON, None)
    schedule = np.clip(schedule.astype(float), 0.0, None)
    participation = schedule / safe_volume
    after_inventory = inventory_path(total_quantity, schedule)

    temporary_cost = float(np.sum(schedule * price * temporary_impact_coefficient * participation ** impact_exponent))
    spread_cost = float(np.sum(schedule * half_spread))
    permanent_cost = float(
        np.sum(np.clip(after_inventory, 0.0, None) * price * permanent_impact_coefficient * schedule / max(adv, EPSILON))
    )
    risk_cost = float(np.sum((after_inventory ** 2) * (price * bucket_sigma) ** 2) * risk_aversion)

    smoothness_penalty = float(
        penalty_weights.get("smoothness", 0.0) * np.sum(np.diff(schedule, prepend=schedule[0]) ** 2)
    )
    participation_violations = np.clip(schedule - max_participation_rate * safe_volume, 0.0, None)
    participation_penalty = float(
        penalty_weights.get("participation", 0.0) * np.sum(participation_violations ** 2)
    )
    completion_penalty = float(
        penalty_weights.get("completion", 0.0) * (schedule.sum() - total_quantity) ** 2
    )
    expected_cost = temporary_cost + spread_cost + permanent_cost + risk_cost

    return ObjectiveTerms(
        expected_cost=expected_cost,
        temporary_cost=temporary_cost,
        spread_cost=spread_cost,
        permanent_cost=permanent_cost,
        risk_cost=risk_cost,
        smoothness_penalty=smoothness_penalty,
        participation_penalty=participation_penalty,
        completion_penalty=completion_penalty,
    )


def scalar_objective(*args: object, **kwargs: object) -> float:
    """Return the scalar objective minimized by deterministic solvers."""
    terms = evaluate_objective_terms(*args, **kwargs)
    return (
        terms.expected_cost
        + terms.smoothness_penalty
        + terms.participation_penalty
        + terms.completion_penalty
    )
