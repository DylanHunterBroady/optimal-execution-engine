"""Cost decomposition and reconciliation."""

from __future__ import annotations

import pandas as pd

from execution_engine.cost.transaction_costs import summarize_execution_costs


def build_cost_decomposition(executions: pd.DataFrame) -> dict[str, float]:
    """Create a complete execution cost decomposition."""
    if executions.empty:
        return {
            "implementation_shortfall": 0.0,
            "market_drift": 0.0,
            "permanent_impact": 0.0,
            "spread_paid": 0.0,
            "spread_capture": 0.0,
            "temporary_impact": 0.0,
            "transient_impact": 0.0,
            "queue_penalty": 0.0,
            "adverse_selection": 0.0,
            "latency_penalty": 0.0,
            "residual_liquidation": 0.0,
            "opportunity_cost": 0.0,
            "reconciliation_error": 0.0,
        }

    regular_executions = executions.loc[~executions["is_residual_liquidation"]].copy()
    cleanup_executions = executions.loc[executions["is_residual_liquidation"]].copy()

    explicit = summarize_execution_costs(regular_executions)
    residual_liquidation = float(
        (
            cleanup_executions["implementation_shortfall_dollars"]
            - cleanup_executions["market_drift_cost"]
            - cleanup_executions["permanent_impact_cost"]
        ).sum()
    )
    decomposition_total = (
        float(executions["market_drift_cost"].sum())
        + float(executions["permanent_impact_cost"].sum())
        + explicit["spread_paid"]
        - explicit["spread_capture"]
        + explicit["temporary_impact"]
        + explicit["transient_impact"]
        + explicit["queue_penalty"]
        + explicit["adverse_selection"]
        + explicit["latency_penalty"]
        + residual_liquidation
        + float(executions["opportunity_cost"].sum())
    )
    implementation_shortfall = float(executions["implementation_shortfall_dollars"].sum())
    error = implementation_shortfall - decomposition_total
    return {
        "implementation_shortfall": implementation_shortfall,
        "market_drift": float(executions["market_drift_cost"].sum()),
        "permanent_impact": float(executions["permanent_impact_cost"].sum()),
        "spread_paid": explicit["spread_paid"],
        "spread_capture": explicit["spread_capture"],
        "temporary_impact": explicit["temporary_impact"],
        "transient_impact": explicit["transient_impact"],
        "queue_penalty": explicit["queue_penalty"],
        "adverse_selection": explicit["adverse_selection"],
        "latency_penalty": explicit["latency_penalty"],
        "residual_liquidation": residual_liquidation,
        "opportunity_cost": float(executions["opportunity_cost"].sum()),
        "reconciliation_error": error,
    }


def reconciliation_error(executions: pd.DataFrame) -> float:
    """Return the cost decomposition reconciliation gap."""
    return float(build_cost_decomposition(executions)["reconciliation_error"])
