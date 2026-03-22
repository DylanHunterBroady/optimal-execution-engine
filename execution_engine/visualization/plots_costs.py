"""Cost decomposition and strategy comparison plots."""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd

from execution_engine.types import SimulationResult


def _pretty_strategy_name(name: str) -> str:
    mapping = {
        "twap": "TWAP",
        "vwap": "VWAP",
        "pov": "POV",
        "almgren_chriss": "Almgren-Chriss",
        "implementation_shortfall": "Implementation Shortfall",
        "adaptive_policy": "Adaptive Policy",
    }
    return mapping.get(name, name.replace("_", " ").title())


def _pretty_metric_name(metric: str) -> str:
    mapping = {
        "implementation_shortfall": "Implementation Shortfall (USD)",
        "implementation_shortfall_bps": "Implementation Shortfall (bps)",
        "arrival_slippage_bps": "Arrival Slippage (bps)",
        "vwap_slippage_bps": "VWAP Slippage (bps)",
        "average_participation": "Average Participation Rate",
        "completion_rate": "Completion Rate",
        "mean_implementation_shortfall": "Mean Implementation Shortfall (USD)",
        "std_implementation_shortfall": "Standard Deviation of Cost (USD)",
    }
    return mapping.get(metric, metric.replace("_", " ").title())


def plot_cost_breakdown(result: SimulationResult, ax: plt.Axes | None = None) -> plt.Axes:
    """Bar chart of cost decomposition for one strategy."""
    ax = ax or plt.subplots(figsize=(10, 4))[1]
    ordered_items = [
        ("market_drift", result.cost_breakdown["market_drift"]),
        ("permanent_impact", result.cost_breakdown["permanent_impact"]),
        ("spread_paid", result.cost_breakdown["spread_paid"]),
        ("spread_capture", -result.cost_breakdown["spread_capture"]),
        ("temporary_impact", result.cost_breakdown["temporary_impact"]),
        ("transient_impact", result.cost_breakdown["transient_impact"]),
        ("queue_penalty", result.cost_breakdown["queue_penalty"]),
        ("adverse_selection", result.cost_breakdown["adverse_selection"]),
        ("latency_penalty", result.cost_breakdown["latency_penalty"]),
        ("residual_liquidation", result.cost_breakdown["residual_liquidation"]),
        ("opportunity_cost", result.cost_breakdown["opportunity_cost"]),
    ]
    labels = [item[0].replace("_", " ").title() for item in ordered_items]
    values = [item[1] for item in ordered_items]
    colors = ["#33658a" if value >= 0 else "#2a9d8f" for value in values]
    ax.bar(labels, values, color=colors)
    ax.axhline(0.0, color="#444444", linewidth=1.0)
    ax.set_title(f"{_pretty_strategy_name(result.strategy_name)} Cost Decomposition")
    ax.set_ylabel("Signed Cost Contribution (USD)")
    ax.tick_params(axis="x", rotation=45)
    ax.grid(axis="y", linestyle="--", alpha=0.25)
    return ax


def plot_strategy_comparison(summary: pd.DataFrame, metric: str = "implementation_shortfall", ax: plt.Axes | None = None) -> plt.Axes:
    """Compare strategies on a selected metric."""
    ax = ax or plt.subplots(figsize=(10, 4))[1]
    ordered = summary.sort_values(metric)
    labels = [_pretty_strategy_name(name) for name in ordered["strategy"]]
    ax.bar(labels, ordered[metric], color="#1d3557")
    ax.set_title(f"Cross-Strategy Comparison: {_pretty_metric_name(metric)}")
    ax.set_ylabel(_pretty_metric_name(metric))
    ax.tick_params(axis="x", rotation=30)
    ax.grid(axis="y", linestyle="--", alpha=0.25)
    return ax


def plot_sensitivity_heatmap(
    sensitivity_frame: pd.DataFrame,
    metric: str = "mean_implementation_shortfall",
    ax: plt.Axes | None = None,
) -> plt.Axes:
    """Heatmap of sensitivity results for one metric."""
    ax = ax or plt.subplots(figsize=(10, 5))[1]
    pivot = sensitivity_frame.pivot_table(index="strategy", columns="value", values=metric)
    image = ax.imshow(pivot.to_numpy(), aspect="auto", cmap="viridis")
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels([str(value) for value in pivot.columns], rotation=45)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels([_pretty_strategy_name(name) for name in pivot.index])
    ax.set_title(f"Sensitivity of {_pretty_metric_name(metric)}")
    ax.set_xlabel("Parameter Value")
    ax.set_ylabel("Strategy")
    plt.colorbar(image, ax=ax, label=_pretty_metric_name(metric))
    return ax
