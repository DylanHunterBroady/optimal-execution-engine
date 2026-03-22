"""Sensitivity analysis utilities."""

from __future__ import annotations

from dataclasses import replace

import pandas as pd

from execution_engine.config import ExperimentConfig
from execution_engine.simulation.monte_carlo import run_monte_carlo


def _override_config(config: ExperimentConfig, parameter_path: str, value: float | str) -> ExperimentConfig:
    section_name, field_name = parameter_path.split(".", maxsplit=1)
    section = getattr(config, section_name)
    new_section = replace(section, **{field_name: value})
    return replace(config, **{section_name: new_section})


def run_sensitivity_analysis(
    config: ExperimentConfig,
    parameter_grid: dict[str, list[float | str]],
    strategy_names: list[str] | None = None,
    n_paths: int | None = None,
) -> pd.DataFrame:
    """Run Monte Carlo sensitivity sweeps over config parameters."""
    rows: list[pd.DataFrame] = []
    for parameter_path, values in parameter_grid.items():
        for value in values:
            scenario_config = _override_config(config, parameter_path, value)
            summary = run_monte_carlo(
                scenario_config,
                strategy_names=strategy_names,
                n_paths=n_paths,
            ).summary.copy()
            summary["parameter"] = parameter_path
            summary["value"] = value
            rows.append(summary)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
