"""Efficient frontier generation."""

from __future__ import annotations

import pandas as pd

from execution_engine.config import ExperimentConfig
from execution_engine.optimization.deterministic_solver import solve_deterministic_schedule


def generate_efficient_frontier(
    config: ExperimentConfig,
    market_frame: pd.DataFrame,
) -> pd.DataFrame:
    """Generate a cost-risk frontier by sweeping risk aversion."""
    rows: list[dict[str, float]] = []
    for risk_aversion in config.optimization.risk_aversion_grid:
        result = solve_deterministic_schedule(
            config=config,
            expected_volume=market_frame["expected_volume"].to_numpy(),
            bucket_sigma=market_frame["bucket_sigma"].to_numpy(),
            half_spread=market_frame["half_spread"].to_numpy(),
            risk_aversion=risk_aversion,
            price=float(market_frame["base_mid_price"].iloc[0]),
        )
        rows.append(
            {
                "risk_aversion": risk_aversion,
                "expected_cost": result.terms.expected_cost,
                "risk_cost": result.terms.risk_cost,
                "temporary_cost": result.terms.temporary_cost,
                "spread_cost": result.terms.spread_cost,
                "permanent_cost": result.terms.permanent_cost,
                "schedule_max_participation": float(
                    (result.schedule / market_frame["expected_volume"].to_numpy()).max()
                ),
                "success": float(result.success),
            }
        )
    return pd.DataFrame(rows).sort_values("risk_aversion")
