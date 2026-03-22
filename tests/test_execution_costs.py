from __future__ import annotations

from pathlib import Path

import pandas as pd

from execution_engine.config import load_config
from execution_engine.cost.benchmark_metrics import compute_benchmark_metrics
from execution_engine.cost.decomposition import reconciliation_error
from execution_engine.simulation.simulator import ExecutionSimulator
from execution_engine.types import Side


def test_cost_decomposition_reconciles_to_implementation_shortfall() -> None:
    config = load_config(Path("configs/base.yaml"))
    result = ExecutionSimulator(config).run(strategy="twap", seed=123)
    assert abs(reconciliation_error(result.executions)) < 1e-6


def test_cost_components_are_non_negative_except_spread_capture() -> None:
    config = load_config(Path("configs/base.yaml"))
    result = ExecutionSimulator(config).run(strategy="vwap", seed=123)
    breakdown = result.cost_breakdown

    assert breakdown["spread_capture"] >= 0.0
    for key in [
        "spread_paid",
        "temporary_impact",
        "transient_impact",
        "queue_penalty",
        "adverse_selection",
        "latency_penalty",
    ]:
        assert breakdown[key] >= 0.0


def test_benchmark_slippage_is_sign_consistent_for_sell_programs() -> None:
    market = pd.DataFrame({"base_mid_price": [100.0, 101.0], "realized_volume": [1_000.0, 1_000.0]})
    executions = pd.DataFrame(
        {
            "filled_quantity": [1_000.0],
            "average_execution_price": [99.0],
            "implementation_shortfall_dollars": [1_000.0],
            "participation_rate": [0.1],
        }
    )
    metrics = compute_benchmark_metrics(
        executions=executions,
        market=market,
        order_size=1_000.0,
        arrival_price=100.0,
        side=Side.SELL,
        benchmark_type="arrival_price",
    )
    assert metrics["arrival_slippage_bps"] == 100.0
    assert metrics["implementation_shortfall_bps"] == 100.0


def test_primary_benchmark_switches_with_configured_benchmark_type() -> None:
    market = pd.DataFrame({"base_mid_price": [100.0, 102.0], "realized_volume": [1_000.0, 3_000.0]})
    executions = pd.DataFrame(
        {
            "filled_quantity": [1_000.0],
            "average_execution_price": [101.0],
            "implementation_shortfall_dollars": [1_000.0],
            "participation_rate": [0.1],
        }
    )
    metrics = compute_benchmark_metrics(
        executions=executions,
        market=market,
        order_size=1_000.0,
        arrival_price=100.0,
        side=Side.BUY,
        benchmark_type="vwap",
    )
    assert metrics["primary_benchmark_is_vwap"] == 1.0
    assert metrics["primary_benchmark_price"] > 100.0
