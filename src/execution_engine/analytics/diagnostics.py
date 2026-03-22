"""Diagnostic views of execution output."""

from __future__ import annotations

import pandas as pd

from execution_engine.types import SimulationResult


def result_diagnostics(result: SimulationResult) -> dict[str, float]:
    """High-level diagnostics for one simulation result."""
    executions = result.executions
    return {
        "completion_rate": float(result.metrics["completion_rate"]),
        "implementation_shortfall": float(result.metrics["implementation_shortfall"]),
        "max_bucket_participation": float(executions["participation_rate"].max()) if not executions.empty else 0.0,
        "active_bucket_count": float((executions["filled_quantity"] > 0).sum()) if not executions.empty else 0.0,
        "residual_cleanup_used": float(executions["is_residual_liquidation"].any()) if not executions.empty else 0.0,
        "mean_fill_rate": float(executions["fill_rate"].mean()) if not executions.empty else 0.0,
    }


def bucket_level_diagnostics(result: SimulationResult) -> pd.DataFrame:
    """Bucket-level view of schedule and realized slippage."""
    executions = result.executions.copy()
    if executions.empty:
        return executions
    executions["inventory_completion"] = 1.0 - executions["remaining_end"] / max(executions["remaining_start"].max(), 1.0)
    executions["cost_per_share"] = executions["implementation_shortfall_dollars"] / executions["filled_quantity"].clip(lower=1.0)
    return executions[
        [
            "bucket",
            "clock_time",
            "decision_quantity",
            "filled_quantity",
            "remaining_end",
            "participation_rate",
            "fill_rate",
            "signed_slippage_per_share",
            "cost_per_share",
            "is_residual_liquidation",
        ]
    ]
