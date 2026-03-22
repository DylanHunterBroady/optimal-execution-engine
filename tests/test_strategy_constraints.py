from __future__ import annotations

from pathlib import Path

import pytest

from execution_engine.config import load_config
from execution_engine.market.price_process import IntradayMarketSimulator
from execution_engine.simulation.scenario_runner import run_strategy_suite
from execution_engine.simulation.simulator import ExecutionSimulator


@pytest.mark.parametrize(
    "strategy_name",
    ["twap", "vwap", "pov", "implementation_shortfall", "almgren_chriss", "adaptive_policy"],
)
def test_strategy_decisions_respect_basic_constraints(strategy_name: str) -> None:
    config = load_config(Path("configs/base.yaml"))
    result = ExecutionSimulator(config).run(strategy=strategy_name, seed=321)
    executions = result.executions
    cap = config.order.max_participation_rate

    assert (executions["decision_quantity"] >= 0.0).all()
    assert (executions["filled_quantity"] >= 0.0).all()
    assert (executions["filled_quantity"] <= executions["remaining_start"] + 1e-9).all()

    regular = executions.loc[~executions["is_residual_liquidation"]]
    assert ((regular["decision_quantity"] - cap * regular["realized_volume"]) <= 1e-6).all()


@pytest.mark.parametrize("strategy_name", ["twap", "vwap", "implementation_shortfall", "almgren_chriss"])
def test_completion_behavior_finishes_parent_order(strategy_name: str) -> None:
    config = load_config(Path("configs/base.yaml"))
    result = ExecutionSimulator(config).run(strategy=strategy_name, seed=111)
    assert abs(result.executions["filled_quantity"].sum() - config.order.parent_order_size) < 1e-6
    assert result.metrics["completion_rate"] == pytest.approx(1.0)


@pytest.mark.parametrize(
    "config_name",
    [
        "base.yaml",
        "low_vol_high_liquidity.yaml",
        "high_vol_low_liquidity.yaml",
        "event_day.yaml",
        "trending_market.yaml",
    ],
)
def test_all_configs_run_all_registered_strategies(config_name: str) -> None:
    config = load_config(Path("configs") / config_name)
    market = IntradayMarketSimulator(config).simulate(seed=config.optimization.scenario_seed)
    suite = run_strategy_suite(config=config, seed=config.optimization.scenario_seed, market=market)

    assert len(suite.results) == len(config.strategies)
    assert set(suite.summary["strategy"]) == set(config.strategies)
    assert not suite.summary.isnull().any().any()
    assert suite.summary["completion_rate"].min() > 0.99
