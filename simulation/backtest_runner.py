"""Batch synthetic scenario runner."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from execution_engine.config import load_config
from execution_engine.simulation.monte_carlo import run_monte_carlo


def run_config_directory(config_dir: str | Path) -> dict[str, pd.DataFrame]:
    """Execute Monte Carlo analysis for every YAML config in a directory."""
    summaries: list[pd.DataFrame] = []
    raw_rows: list[pd.DataFrame] = []
    for path in sorted(Path(config_dir).glob("*.yaml")):
        config = load_config(path)
        result = run_monte_carlo(config)
        scenario_summary = result.summary.copy()
        scenario_summary["scenario"] = path.stem
        summaries.append(scenario_summary)

        scenario_raw = result.raw.copy()
        scenario_raw["scenario"] = path.stem
        raw_rows.append(scenario_raw)

    return {
        "summary": pd.concat(summaries, ignore_index=True) if summaries else pd.DataFrame(),
        "raw": pd.concat(raw_rows, ignore_index=True) if raw_rows else pd.DataFrame(),
    }
