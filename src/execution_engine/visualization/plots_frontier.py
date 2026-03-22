"""Efficient frontier plots."""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd


def plot_efficient_frontier(frontier: pd.DataFrame, ax: plt.Axes | None = None) -> plt.Axes:
    """Plot expected cost versus risk for an efficient frontier."""
    ax = ax or plt.subplots(figsize=(8, 5))[1]
    ax.plot(frontier["risk_cost"], frontier["expected_cost"], marker="o", color="#e76f51")
    for _, row in frontier.iterrows():
        ax.annotate(f"$\\lambda$={row['risk_aversion']:.1e}", (row["risk_cost"], row["expected_cost"]))
    ax.set_title("Deterministic Cost-Risk Frontier")
    ax.set_xlabel("Volatility Risk Penalty (USD)")
    ax.set_ylabel("Expected Execution Cost (USD)")
    ax.grid(linestyle="--", alpha=0.25)
    return ax
