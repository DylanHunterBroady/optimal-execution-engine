"""Command-line entry point for the execution engine."""

from __future__ import annotations

import argparse
from pathlib import Path

from execution_engine.config import load_config
from execution_engine.example_runner import run_end_to_end_example
from execution_engine.market.price_process import IntradayMarketSimulator
from execution_engine.optimization.frontier import generate_efficient_frontier
from execution_engine.optimization.stochastic_solver import evaluate_almgren_chriss_stochastic_frontier
from execution_engine.simulation.monte_carlo import run_monte_carlo
from execution_engine.simulation.scenario_runner import run_strategy_suite
from execution_engine.simulation.simulator import ExecutionSimulator


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line parser."""
    parser = argparse.ArgumentParser(description="Optimal execution research engine")
    parser.add_argument("--config", required=True, help="Path to a YAML config file")
    parser.add_argument(
        "--mode",
        choices=["single", "suite", "monte_carlo", "frontier", "stochastic_frontier", "example"],
        default="suite",
        help="Experiment mode to run",
    )
    parser.add_argument("--strategy", default="almgren_chriss", help="Strategy for single-run mode")
    parser.add_argument("--paths", type=int, default=None, help="Override Monte Carlo path count")
    parser.add_argument("--seed", type=int, default=None, help="Override scenario seed")
    parser.add_argument("--output", default=None, help="Optional CSV output path")
    parser.add_argument("--output-dir", default="artifacts/example_run", help="Directory for example-mode outputs")
    return parser


def main() -> None:
    """Run the selected experiment mode."""
    args = build_parser().parse_args()
    config = load_config(args.config)

    if args.mode == "single":
        result = ExecutionSimulator(config).run(strategy=args.strategy, seed=args.seed)
        summary = result.executions
        print(result.metrics)
    elif args.mode == "suite":
        market = IntradayMarketSimulator(config).simulate(seed=args.seed)
        suite = run_strategy_suite(config=config, seed=args.seed, market=market)
        summary = suite.summary
        print(summary.to_string(index=False))
    elif args.mode == "monte_carlo":
        summary = run_monte_carlo(config=config, n_paths=args.paths).summary
        print(summary.to_string(index=False))
    elif args.mode == "stochastic_frontier":
        summary = evaluate_almgren_chriss_stochastic_frontier(config=config, n_paths=args.paths).summary
        print(summary.to_string(index=False))
    elif args.mode == "example":
        artifacts = run_end_to_end_example(
            config_path=args.config,
            output_dir=args.output_dir,
            seed=args.seed,
            monte_carlo_paths=args.paths,
        )
        summary = artifacts.summary
        print(summary.to_string(index=False))
        print(f"\nArtifacts written to: {artifacts.output_dir}")
    else:
        market = IntradayMarketSimulator(config).simulate(seed=args.seed)
        summary = generate_efficient_frontier(config, market)
        print(summary.to_string(index=False))

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        summary.to_csv(output_path, index=False)


if __name__ == "__main__":
    main()
