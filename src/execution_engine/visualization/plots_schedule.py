"""Schedule and inventory trajectory plots."""

from __future__ import annotations

import matplotlib.pyplot as plt

from execution_engine.types import SimulationResult
from execution_engine.visualization.plots_costs import _pretty_strategy_name


def plot_execution_schedule(result: SimulationResult, ax: plt.Axes | None = None) -> plt.Axes:
    """Plot requested and filled child-order quantities over time."""
    ax = ax or plt.subplots(figsize=(10, 4))[1]
    executions = result.executions
    ax.bar(executions["bucket"], executions["decision_quantity"], alpha=0.4, label="Requested Child Order")
    ax.plot(executions["bucket"], executions["filled_quantity"], marker="o", label="Realized Fill", color="#0b6e4f")
    ax.set_title(f"{_pretty_strategy_name(result.strategy_name)} Schedule: Requested vs. Realized Fills")
    ax.set_xlabel("Intraday Bucket")
    ax.set_ylabel("Child Order Size (shares)")
    ax.grid(axis="y", linestyle="--", alpha=0.25)
    ax.legend()
    return ax


def plot_inventory_trajectory(result: SimulationResult, ax: plt.Axes | None = None) -> plt.Axes:
    """Plot remaining inventory through the execution horizon."""
    ax = ax or plt.subplots(figsize=(10, 4))[1]
    executions = result.executions
    ax.step(executions["bucket"], executions["remaining_start"], where="post", label="Inventory Before Bucket", color="#9a031e")
    ax.step(executions["bucket"], executions["remaining_end"], where="post", linestyle="--", label="Inventory After Bucket", color="#5f0f40")
    ax.set_title(f"{_pretty_strategy_name(result.strategy_name)} Inventory Trajectory")
    ax.set_xlabel("Intraday Bucket")
    ax.set_ylabel("Remaining Inventory (shares)")
    ax.grid(axis="y", linestyle="--", alpha=0.25)
    ax.legend()
    return ax
