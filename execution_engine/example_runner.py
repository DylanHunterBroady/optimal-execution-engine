"""Runnable end-to-end research example."""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
import argparse

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "optimal_execution_mplconfig"))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

from execution_engine.analytics.diagnostics import bucket_level_diagnostics, result_diagnostics
from execution_engine.config import load_config
from execution_engine.market.price_process import IntradayMarketSimulator
from execution_engine.optimization.frontier import generate_efficient_frontier
from execution_engine.simulation.monte_carlo import run_monte_carlo
from execution_engine.simulation.scenario_runner import run_strategy_suite
from execution_engine.visualization.dashboard_data import comparison_dashboard
from execution_engine.visualization.plots_costs import plot_cost_breakdown, plot_strategy_comparison
from execution_engine.visualization.plots_frontier import plot_efficient_frontier
from execution_engine.visualization.plots_schedule import plot_execution_schedule, plot_inventory_trajectory


@dataclass(frozen=True)
class ExampleArtifacts:
    """Artifacts emitted by the end-to-end example workflow."""

    output_dir: Path
    summary: pd.DataFrame
    suite_summary_csv: Path
    monte_carlo_summary_csv: Path
    frontier_csv: Path
    best_strategy_execution_csv: Path
    best_strategy_diagnostics_csv: Path
    strategy_comparison_png: Path
    best_schedule_png: Path
    best_cost_breakdown_png: Path
    frontier_png: Path
    inventory_png: Path


def run_end_to_end_example(
    config_path: str | Path,
    output_dir: str | Path = "artifacts/example_run",
    seed: int | None = None,
    monte_carlo_paths: int | None = 25,
) -> ExampleArtifacts:
    """Run a full example from config load through plot generation."""
    config = load_config(config_path)
    run_seed = config.optimization.scenario_seed if seed is None else seed
    artifact_dir = Path(output_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)

    market = IntradayMarketSimulator(config).simulate(seed=run_seed)
    suite = run_strategy_suite(config=config, seed=run_seed, market=market)
    monte_carlo = run_monte_carlo(config=config, n_paths=monte_carlo_paths)
    frontier = generate_efficient_frontier(config, market)
    dashboard = comparison_dashboard(suite.results)

    best_result = suite.best_result
    best_execution = bucket_level_diagnostics(best_result)
    best_summary = pd.DataFrame([result_diagnostics(best_result)])
    dashboard["summary"].to_csv(artifact_dir / "dashboard_summary.csv", index=False)
    dashboard["diagnostics"].to_csv(artifact_dir / "dashboard_diagnostics.csv", index=False)

    suite_summary_csv = artifact_dir / "strategy_suite_summary.csv"
    monte_carlo_summary_csv = artifact_dir / "monte_carlo_summary.csv"
    frontier_csv = artifact_dir / "efficient_frontier.csv"
    best_strategy_execution_csv = artifact_dir / "best_strategy_execution.csv"
    best_strategy_diagnostics_csv = artifact_dir / "best_strategy_diagnostics.csv"

    suite.summary.to_csv(suite_summary_csv, index=False)
    monte_carlo.summary.to_csv(monte_carlo_summary_csv, index=False)
    frontier.to_csv(frontier_csv, index=False)
    best_execution.to_csv(best_strategy_execution_csv, index=False)
    best_summary.to_csv(best_strategy_diagnostics_csv, index=False)

    strategy_comparison_png = artifact_dir / "strategy_comparison.png"
    best_schedule_png = artifact_dir / "best_strategy_schedule.png"
    best_cost_breakdown_png = artifact_dir / "best_strategy_cost_breakdown.png"
    frontier_png = artifact_dir / "efficient_frontier.png"
    inventory_png = artifact_dir / "best_strategy_inventory.png"

    fig, ax = plt.subplots(figsize=(10, 4))
    plot_strategy_comparison(suite.summary, metric="implementation_shortfall_bps", ax=ax)
    fig.tight_layout()
    fig.savefig(strategy_comparison_png, dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 4))
    plot_execution_schedule(best_result, ax=ax)
    fig.tight_layout()
    fig.savefig(best_schedule_png, dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 4))
    plot_cost_breakdown(best_result, ax=ax)
    fig.tight_layout()
    fig.savefig(best_cost_breakdown_png, dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    plot_efficient_frontier(frontier, ax=ax)
    fig.tight_layout()
    fig.savefig(frontier_png, dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 4))
    plot_inventory_trajectory(best_result, ax=ax)
    fig.tight_layout()
    fig.savefig(inventory_png, dpi=180)
    plt.close(fig)

    return ExampleArtifacts(
        output_dir=artifact_dir,
        summary=suite.summary,
        suite_summary_csv=suite_summary_csv,
        monte_carlo_summary_csv=monte_carlo_summary_csv,
        frontier_csv=frontier_csv,
        best_strategy_execution_csv=best_strategy_execution_csv,
        best_strategy_diagnostics_csv=best_strategy_diagnostics_csv,
        strategy_comparison_png=strategy_comparison_png,
        best_schedule_png=best_schedule_png,
        best_cost_breakdown_png=best_cost_breakdown_png,
        frontier_png=frontier_png,
        inventory_png=inventory_png,
    )


def cli_main() -> None:
    """CLI wrapper for the end-to-end example workflow."""
    parser = argparse.ArgumentParser(description="Run the optimal execution example workflow")
    parser.add_argument("--config", required=True, help="Path to a YAML scenario config")
    parser.add_argument("--output-dir", default="artifacts/example_run", help="Directory for output artifacts")
    parser.add_argument("--seed", type=int, default=None, help="Optional scenario seed override")
    parser.add_argument("--paths", type=int, default=25, help="Monte Carlo path count for the example summary")
    args = parser.parse_args()

    artifacts = run_end_to_end_example(
        config_path=args.config,
        output_dir=args.output_dir,
        seed=args.seed,
        monte_carlo_paths=args.paths,
    )
    print(artifacts.summary.to_string(index=False))
    print(f"\nArtifacts written to: {artifacts.output_dir}")
