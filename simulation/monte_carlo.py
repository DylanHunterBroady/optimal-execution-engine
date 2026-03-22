"""Monte Carlo scenario analysis."""

from __future__ import annotations

import numpy as np
import pandas as pd

from execution_engine.config import ExperimentConfig
from execution_engine.market.price_process import IntradayMarketSimulator
from execution_engine.simulation.scenario_runner import run_strategy_suite
from execution_engine.types import MonteCarloResult


def run_monte_carlo(
    config: ExperimentConfig,
    strategy_names: list[str] | None = None,
    n_paths: int | None = None,
) -> MonteCarloResult:
    """Run Monte Carlo simulations for a family of strategies."""
    path_count = n_paths or config.optimization.monte_carlo_paths
    strategy_names = strategy_names or list(config.strategies)
    market_simulator = IntradayMarketSimulator(config)

    rows: list[dict[str, float | int | str]] = []
    for path_index in range(path_count):
        seed = config.optimization.scenario_seed + path_index
        market = market_simulator.simulate(seed=seed)
        suite = run_strategy_suite(config=config, strategy_names=strategy_names, seed=seed, market=market)
        for result in suite.results:
            rows.append(
                {
                    "path": path_index,
                    "seed": seed,
                    "strategy": result.strategy_name,
                    "implementation_shortfall": result.metrics["implementation_shortfall"],
                    "implementation_shortfall_bps": result.metrics["implementation_shortfall_bps"],
                    "completion_rate": result.metrics["completion_rate"],
                    "average_execution_price": result.metrics["average_execution_price"],
                    "average_participation": result.metrics["average_participation"],
                    "primary_benchmark_slippage_bps": result.metrics["primary_benchmark_slippage_bps"],
                }
            )

    raw = pd.DataFrame(rows)
    summary = (
        raw.groupby("strategy")
        .agg(
            mean_implementation_shortfall=("implementation_shortfall", "mean"),
            std_implementation_shortfall=("implementation_shortfall", "std"),
            mean_implementation_shortfall_bps=("implementation_shortfall_bps", "mean"),
            p95_implementation_shortfall=("implementation_shortfall", lambda s: float(np.quantile(s, 0.95))),
            p99_implementation_shortfall=("implementation_shortfall", lambda s: float(np.quantile(s, 0.99))),
            mean_completion_rate=("completion_rate", "mean"),
            mean_participation=("average_participation", "mean"),
            mean_primary_benchmark_slippage_bps=("primary_benchmark_slippage_bps", "mean"),
        )
        .reset_index()
        .sort_values("mean_implementation_shortfall")
    )
    summary.insert(0, "rank", range(1, len(summary) + 1))
    return MonteCarloResult(raw=raw, summary=summary.reset_index(drop=True))
