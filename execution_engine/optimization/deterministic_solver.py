"""Deterministic schedule optimization."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import LinearConstraint, minimize

from execution_engine.config import ExperimentConfig
from execution_engine.optimization.constraints import project_schedule_to_constraints
from execution_engine.optimization.objective import ObjectiveTerms, evaluate_objective_terms, scalar_objective


@dataclass(frozen=True)
class DeterministicSolverResult:
    """Container for deterministic schedule optimization output."""

    schedule: np.ndarray
    terms: ObjectiveTerms
    success: bool
    message: str


def solve_deterministic_schedule(
    config: ExperimentConfig,
    expected_volume: np.ndarray,
    bucket_sigma: np.ndarray,
    half_spread: np.ndarray,
    risk_aversion: float,
    price: float | None = None,
) -> DeterministicSolverResult:
    """Solve for a deterministic execution schedule under stylized AC assumptions."""
    order_cfg = config.order
    market_cfg = config.market
    impact_cfg = config.impact
    opt_cfg = config.optimization
    price = market_cfg.initial_price if price is None else price

    expected_volume = expected_volume.astype(float)
    bucket_sigma = bucket_sigma.astype(float)
    half_spread = half_spread.astype(float)
    total_quantity = float(order_cfg.parent_order_size)
    n_buckets = len(expected_volume)

    weighted_guess = total_quantity * expected_volume / expected_volume.sum()
    uniform_guess = np.full(n_buckets, total_quantity / n_buckets)
    initial_guess = 0.5 * weighted_guess + 0.5 * uniform_guess
    initial_guess = project_schedule_to_constraints(
        schedule=initial_guess,
        total_quantity=total_quantity,
        expected_volume=expected_volume,
        max_participation_rate=order_cfg.max_participation_rate,
        min_child_order_size=order_cfg.min_child_order_size,
    )

    linear_constraint = LinearConstraint(np.ones((1, n_buckets)), [total_quantity], [total_quantity])
    bounds = [(0.0, max(total_quantity, order_cfg.max_participation_rate * volume)) for volume in expected_volume]

    result = minimize(
        fun=lambda q: scalar_objective(
            schedule=q,
            total_quantity=total_quantity,
            expected_volume=expected_volume,
            bucket_sigma=bucket_sigma,
            price=price,
            adv=market_cfg.adv,
            half_spread=half_spread,
            temporary_impact_coefficient=impact_cfg.temporary_impact_coefficient,
            permanent_impact_coefficient=impact_cfg.permanent_impact_coefficient,
            impact_exponent=impact_cfg.impact_exponent,
            risk_aversion=risk_aversion,
            max_participation_rate=order_cfg.max_participation_rate,
            penalty_weights=opt_cfg.penalty_weights,
        ),
        x0=initial_guess,
        bounds=bounds,
        constraints=[linear_constraint],
        method="SLSQP",
        options={"ftol": opt_cfg.solver_tolerance, "maxiter": 500},
    )

    schedule = project_schedule_to_constraints(
        schedule=np.asarray(result.x, dtype=float),
        total_quantity=total_quantity,
        expected_volume=expected_volume,
        max_participation_rate=order_cfg.max_participation_rate,
        min_child_order_size=order_cfg.min_child_order_size,
    )
    terms = evaluate_objective_terms(
        schedule=schedule,
        total_quantity=total_quantity,
        expected_volume=expected_volume,
        bucket_sigma=bucket_sigma,
        price=price,
        adv=market_cfg.adv,
        half_spread=half_spread,
        temporary_impact_coefficient=impact_cfg.temporary_impact_coefficient,
        permanent_impact_coefficient=impact_cfg.permanent_impact_coefficient,
        impact_exponent=impact_cfg.impact_exponent,
        risk_aversion=risk_aversion,
        max_participation_rate=order_cfg.max_participation_rate,
        penalty_weights=opt_cfg.penalty_weights,
    )
    return DeterministicSolverResult(
        schedule=schedule,
        terms=terms,
        success=bool(result.success),
        message=str(result.message),
    )
