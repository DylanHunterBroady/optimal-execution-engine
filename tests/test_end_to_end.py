from __future__ import annotations

from pathlib import Path

from execution_engine.example_runner import run_end_to_end_example


def test_end_to_end_example_writes_expected_artifacts(tmp_path: Path) -> None:
    artifacts = run_end_to_end_example(
        config_path=Path("configs/base.yaml"),
        output_dir=tmp_path / "example",
        seed=13,
        monte_carlo_paths=3,
    )
    expected_paths = [
        artifacts.suite_summary_csv,
        artifacts.monte_carlo_summary_csv,
        artifacts.frontier_csv,
        artifacts.best_strategy_execution_csv,
        artifacts.best_strategy_diagnostics_csv,
        artifacts.strategy_comparison_png,
        artifacts.best_schedule_png,
        artifacts.best_cost_breakdown_png,
        artifacts.frontier_png,
        artifacts.inventory_png,
    ]
    for path in expected_paths:
        assert path.exists()
        assert path.stat().st_size > 0
