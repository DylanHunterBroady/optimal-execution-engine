"""Optimal Execution and Market Impact Simulation Engine."""

from execution_engine.config import ExperimentConfig, load_config
from execution_engine.simulation.monte_carlo import run_monte_carlo
from execution_engine.simulation.scenario_runner import run_strategy_suite
from execution_engine.simulation.simulator import ExecutionSimulator

__all__ = [
    "ExperimentConfig",
    "ExecutionSimulator",
    "load_config",
    "run_monte_carlo",
    "run_strategy_suite",
]

__version__ = "0.1.0"
