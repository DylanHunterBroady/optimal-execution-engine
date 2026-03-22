"""Benchmarks and execution quality metrics."""

from __future__ import annotations

import pandas as pd

from execution_engine.constants import BPS
from execution_engine.cost.implementation_shortfall import implementation_shortfall_bps
from execution_engine.types import Side


def market_vwap(market: pd.DataFrame) -> float:
    """Volume-weighted midprice benchmark for the execution window."""
    if market.empty:
        return 0.0
    return float((market["base_mid_price"] * market["realized_volume"]).sum() / market["realized_volume"].sum())


def signed_benchmark_slippage_bps(
    side: Side,
    execution_price: float,
    benchmark_price: float,
) -> float:
    """Signed benchmark slippage where positive means higher cost."""
    if benchmark_price <= 0:
        return 0.0
    return float(side.sign * (execution_price - benchmark_price) / benchmark_price / BPS)


def compute_benchmark_metrics(
    executions: pd.DataFrame,
    market: pd.DataFrame,
    order_size: float,
    arrival_price: float,
    side: Side,
    benchmark_type: str = "implementation_shortfall",
) -> dict[str, float]:
    """Compute key execution metrics for a completed run."""
    executed_quantity = float(executions["filled_quantity"].sum()) if not executions.empty else 0.0
    average_execution_price = (
        float((executions["average_execution_price"] * executions["filled_quantity"]).sum() / executed_quantity)
        if executed_quantity > 0
        else arrival_price
    )
    total_cost = float(executions["implementation_shortfall_dollars"].sum()) if not executions.empty else 0.0
    vwap_benchmark = market_vwap(market)
    vwap_slippage_bps = (
        signed_benchmark_slippage_bps(side, average_execution_price, vwap_benchmark)
        if executed_quantity > 0
        else 0.0
    )
    arrival_slippage_bps = signed_benchmark_slippage_bps(side, average_execution_price, arrival_price)

    if benchmark_type in {"implementation_shortfall", "arrival_price"}:
        primary_benchmark_name = "arrival_price"
        primary_benchmark_price = arrival_price
        primary_slippage_bps = arrival_slippage_bps
    else:
        primary_benchmark_name = "vwap"
        primary_benchmark_price = vwap_benchmark
        primary_slippage_bps = vwap_slippage_bps

    realized_participation = (
        float(executed_quantity / market["realized_volume"].sum())
        if not market.empty and market["realized_volume"].sum() > 0
        else 0.0
    )
    active_buckets = executions.loc[executions["filled_quantity"] > 0, "participation_rate"]
    mean_active_participation = float(active_buckets.mean()) if not active_buckets.empty else 0.0

    return {
        "executed_quantity": executed_quantity,
        "completion_rate": executed_quantity / max(order_size, 1.0),
        "average_execution_price": average_execution_price,
        "implementation_shortfall": total_cost,
        "implementation_shortfall_bps": implementation_shortfall_bps(total_cost, max(executed_quantity, 1.0), arrival_price),
        "arrival_slippage_bps": arrival_slippage_bps,
        "vwap_slippage_bps": vwap_slippage_bps,
        "primary_benchmark_price": primary_benchmark_price,
        "primary_benchmark_slippage_bps": primary_slippage_bps,
        "primary_benchmark_is_vwap": float(primary_benchmark_name == "vwap"),
        "average_participation": realized_participation,
        "active_bucket_participation": mean_active_participation,
    }
