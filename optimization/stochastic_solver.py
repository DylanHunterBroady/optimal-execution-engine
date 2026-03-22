"""Stochastic evaluation helpers for optimized schedules."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from execution_engine.config import ExperimentConfig
from execution_engine.market.price_process import IntradayMarketSimulator
from execution_engine.optimization.deterministic_solver import DeterministicSolverResult
from execution_engine.simulation.simulator import ExecutionSimulator
from execution_engine.strategies.almgren_chriss import AlmgrenChrissStrategy


@dataclass(frozen=True)
class StochasticEvaluation:
    """Monte Carlo summary for a family of schedules."""

    summary: pd.DataFrame
    raw_costs: dict[float, np.ndarray]
    raw: pd.DataFrame


def summarize_schedule_outcomes(outcomes: dict[float, list[float]]) -> StochasticEvaluation:
    """Convert risk-aversion keyed costs into a summary table."""
    rows: list[dict[str, float]] = []
    raw_rows: list[dict[str, float]] = []
    raw_costs: dict[float, np.ndarray] = {}
    for risk_aversion, costs in outcomes.items():
        cost_array = np.asarray(costs, dtype=float)
        raw_costs[risk_aversion] = cost_array
        raw_rows.extend(
            {"risk_aversion": risk_aversion, "implementation_shortfall": float(cost)}
            for cost in cost_array
        )
        rows.append(
            {
                "risk_aversion": risk_aversion,
                "expected_cost": float(cost_array.mean()),
                "cost_std": float(cost_array.std(ddof=1)) if len(cost_array) > 1 else 0.0,
                "p95_cost": float(np.quantile(cost_array, 0.95)),
            }
        )
    summary = pd.DataFrame(rows).sort_values("risk_aversion").reset_index(drop=True)
    return StochasticEvaluation(summary=summary, raw_costs=raw_costs, raw=pd.DataFrame(raw_rows))


def deterministic_results_to_frame(results: dict[float, DeterministicSolverResult]) -> pd.DataFrame:
    """Summarize deterministic solver outputs across risk aversion values."""
    rows = []
    for risk_aversion, result in results.items():
        rows.append(
            {
                "risk_aversion": risk_aversion,
                "success": result.success,
                "objective_value": result.terms.expected_cost
                + result.terms.smoothness_penalty
                + result.terms.participation_penalty
                + result.terms.completion_penalty,
                "expected_cost": result.terms.expected_cost,
                "risk_cost": result.terms.risk_cost,
                "temporary_cost": result.terms.temporary_cost,
                "spread_cost": result.terms.spread_cost,
                "permanent_cost": result.terms.permanent_cost,
            }
        )
    return pd.DataFrame(rows).sort_values("risk_aversion")


def evaluate_almgren_chriss_stochastic_frontier(
    config: ExperimentConfig,
    n_paths: int | None = None,
) -> StochasticEvaluation:
    """Evaluate Almgren-Chriss schedules across the risk-aversion grid on Monte Carlo paths."""
    path_count = n_paths or config.optimization.monte_carlo_paths
    market_simulator = IntradayMarketSimulator(config)
    simulator = ExecutionSimulator(config)

    rows: list[dict[str, float]] = []
    outcomes: dict[float, list[float]] = {risk_aversion: [] for risk_aversion in config.optimization.risk_aversion_grid}

    for path_index in range(path_count):
        seed = config.optimization.scenario_seed + path_index
        market = market_simulator.simulate(seed=seed)
        for risk_aversion in config.optimization.risk_aversion_grid:
            strategy = AlmgrenChrissStrategy(config=config, risk_aversion=risk_aversion)
            result = simulator.run(strategy=strategy, seed=seed, market=market)
            cost = float(result.metrics["implementation_shortfall"])
            outcomes[risk_aversion].append(cost)
            rows.append(
                {
                    "path": float(path_index),
                    "seed": float(seed),
                    "risk_aversion": risk_aversion,
                    "implementation_shortfall": cost,
                    "implementation_shortfall_bps": float(result.metrics["implementation_shortfall_bps"]),
                    "completion_rate": float(result.metrics["completion_rate"]),
                    "average_participation": float(result.metrics["average_participation"]),
                }
            )

    evaluation = summarize_schedule_outcomes(outcomes)
    empirical = (
        pd.DataFrame(rows)
        .groupby("risk_aversion")
        .agg(
            mean_implementation_shortfall_bps=("implementation_shortfall_bps", "mean"),
            mean_completion_rate=("completion_rate", "mean"),
            mean_average_participation=("average_participation", "mean"),
        )
        .reset_index()
    )
    summary = evaluation.summary.merge(empirical, on="risk_aversion", how="left").sort_values("risk_aversion")
    summary.insert(0, "rank", range(1, len(summary) + 1))
    return StochasticEvaluation(
        summary=summary.reset_index(drop=True),
        raw_costs=evaluation.raw_costs,
        raw=pd.DataFrame(rows),
    )
