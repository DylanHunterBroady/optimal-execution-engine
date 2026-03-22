"""Scenario runner for multi-strategy comparison."""

from __future__ import annotations

import pandas as pd

from execution_engine.config import ExperimentConfig
from execution_engine.simulation.simulator import ExecutionSimulator
from execution_engine.types import StrategySuiteResult


def run_strategy_suite(
    config: ExperimentConfig,
    strategy_names: list[str] | None = None,
    seed: int | None = None,
    market: pd.DataFrame | None = None,
) -> StrategySuiteResult:
    """Run a set of strategies on a common market path."""
    simulator = ExecutionSimulator(config)
    strategy_names = strategy_names or list(config.strategies)
    shared_market = market.copy().reset_index(drop=True) if market is not None else None

    results = []
    for name in strategy_names:
        run_market = shared_market.copy() if shared_market is not None else None
        result = simulator.run(strategy=name, seed=seed, market=run_market)
        results.append(result)

    summary = pd.DataFrame([result.as_summary_row() for result in results]).sort_values("implementation_shortfall")
    summary.insert(0, "rank", range(1, len(summary) + 1))
    common_market = results[0].market.copy() if results else pd.DataFrame()
    return StrategySuiteResult(market=common_market, results=results, summary=summary.reset_index(drop=True))
