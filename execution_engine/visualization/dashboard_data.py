"""Prepare compact dashboard-friendly tables."""

from __future__ import annotations

import pandas as pd

from execution_engine.types import SimulationResult


def comparison_dashboard(results: list[SimulationResult]) -> dict[str, pd.DataFrame]:
    """Create tables used by notebooks or downstream dashboards."""
    summary = pd.DataFrame([result.as_summary_row() for result in results]).sort_values("implementation_shortfall")
    diagnostics = pd.DataFrame(
        [
            {
                "strategy": result.strategy_name,
                "completion_rate": result.metrics["completion_rate"],
                "mean_fill_rate": result.diagnostics["mean_fill_rate"],
                "max_bucket_participation": result.diagnostics["max_bucket_participation"],
            }
            for result in results
        ]
    )
    return {"summary": summary, "diagnostics": diagnostics}
