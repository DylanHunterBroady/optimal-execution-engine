from __future__ import annotations

from pathlib import Path

import pandas as pd

from execution_engine.config import load_config
from execution_engine.market.price_process import IntradayMarketSimulator
from execution_engine.simulation.scenario_runner import run_strategy_suite
from execution_engine.simulation.simulator import ExecutionSimulator


def test_inventory_conservation_holds() -> None:
    config = load_config(Path("configs/base.yaml"))
    result = ExecutionSimulator(config).run(strategy="adaptive_policy", seed=2026)
    executions = result.executions

    assert executions["remaining_start"].iloc[0] == config.order.parent_order_size
    assert (executions["remaining_start"] - executions["filled_quantity"] - executions["remaining_end"]).abs().max() < 1e-6
    assert abs(executions["filled_quantity"].sum() - config.order.parent_order_size) < 1e-6
    assert executions["remaining_end"].iloc[-1] == 0.0


def test_simulation_is_reproducible_given_seed() -> None:
    config = load_config(Path("configs/base.yaml"))
    simulator = ExecutionSimulator(config)
    first = simulator.run(strategy="twap", seed=77)
    second = simulator.run(strategy="twap", seed=77)

    pd.testing.assert_frame_equal(first.market, second.market)
    pd.testing.assert_frame_equal(first.executions, second.executions)
    assert first.metrics == second.metrics


def test_strategy_suite_uses_shared_market_path() -> None:
    config = load_config(Path("configs/base.yaml"))
    market = IntradayMarketSimulator(config).simulate(seed=19)
    suite = run_strategy_suite(config=config, seed=19, market=market)

    pd.testing.assert_frame_equal(suite.market, market.reset_index(drop=True))
    for result in suite.results:
        pd.testing.assert_frame_equal(result.market, suite.market)
