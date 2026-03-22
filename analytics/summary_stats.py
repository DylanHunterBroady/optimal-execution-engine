"""Summary statistics for collections of results."""

from __future__ import annotations

import pandas as pd

from execution_engine.types import SimulationResult


def results_to_frame(results: list[SimulationResult]) -> pd.DataFrame:
    """Turn a list of results into a tabular summary."""
    if not results:
        return pd.DataFrame()
    return pd.DataFrame([result.as_summary_row() for result in results]).sort_values("implementation_shortfall")
