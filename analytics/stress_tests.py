"""Pre-defined stress-test regimes."""

from __future__ import annotations

from dataclasses import replace

import pandas as pd

from execution_engine.config import ExperimentConfig
from execution_engine.simulation.monte_carlo import run_monte_carlo


def run_regime_stress_tests(
    config: ExperimentConfig,
    strategy_names: list[str] | None = None,
    n_paths: int | None = None,
) -> pd.DataFrame:
    """Compare strategies across built-in market regimes."""
    scenarios = {
        "low_vol_high_liquidity": replace(
            config,
            market=replace(config.market, regime_name="low_vol_high_liquidity", annualized_volatility=0.18, spread_bps=4.0),
        ),
        "high_vol_low_liquidity": replace(
            config,
            market=replace(config.market, regime_name="high_vol_low_liquidity", annualized_volatility=0.42, spread_bps=12.0),
        ),
        "event_day": replace(
            config,
            market=replace(config.market, regime_name="event_day", drift_regime="event_day", annualized_volatility=0.5, spread_bps=18.0),
        ),
        "trending_market": replace(
            config,
            market=replace(config.market, regime_name="trending_market", drift_regime="uptrend", annualized_volatility=0.3),
        ),
    }
    rows: list[pd.DataFrame] = []
    for scenario_name, scenario_config in scenarios.items():
        summary = run_monte_carlo(scenario_config, strategy_names=strategy_names, n_paths=n_paths).summary.copy()
        summary["scenario"] = scenario_name
        rows.append(summary)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
