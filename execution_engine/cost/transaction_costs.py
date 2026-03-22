"""Aggregate transaction cost helpers."""

from __future__ import annotations

import pandas as pd


def summarize_execution_costs(executions: pd.DataFrame) -> dict[str, float]:
    """Aggregate explicit cost components from an execution log."""
    if executions.empty:
        return {
            "spread_paid": 0.0,
            "spread_capture": 0.0,
            "temporary_impact": 0.0,
            "transient_impact": 0.0,
            "queue_penalty": 0.0,
            "adverse_selection": 0.0,
            "latency_penalty": 0.0,
            "residual_liquidation": 0.0,
        }
    return {
        "spread_paid": float(executions["spread_paid_cost"].sum()),
        "spread_capture": float(executions["spread_capture_cost"].sum()),
        "temporary_impact": float(executions["temporary_impact_cost"].sum()),
        "transient_impact": float(executions["transient_impact_cost"].sum()),
        "queue_penalty": float(executions["queue_penalty_cost"].sum()),
        "adverse_selection": float(executions["adverse_selection_cost"].sum()),
        "latency_penalty": float(executions["latency_penalty_cost"].sum()),
        "residual_liquidation": float(executions["residual_liquidation_cost"].sum()),
    }
