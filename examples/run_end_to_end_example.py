"""Run a complete example research workflow and save artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from execution_engine.example_runner import run_end_to_end_example


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the optimal execution example workflow")
    parser.add_argument("--config", default="configs/base.yaml", help="Path to a YAML scenario config")
    parser.add_argument("--output-dir", default="artifacts/example_run", help="Directory for output artifacts")
    parser.add_argument("--seed", type=int, default=None, help="Optional scenario seed override")
    parser.add_argument("--paths", type=int, default=25, help="Monte Carlo path count for the example summary")
    args = parser.parse_args()

    artifacts = run_end_to_end_example(
        config_path=PROJECT_ROOT / args.config,
        output_dir=PROJECT_ROOT / args.output_dir,
        seed=args.seed,
        monte_carlo_paths=args.paths,
    )
    print("Example workflow completed.")
    print(f"Artifacts: {artifacts.output_dir}")
    print(artifacts.summary.to_string(index=False))


if __name__ == "__main__":
    main()
