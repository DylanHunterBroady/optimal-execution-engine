from __future__ import annotations

from pathlib import Path

from execution_engine.config import load_config
from execution_engine.market.price_process import IntradayMarketSimulator
from execution_engine.optimization.constraints import max_participation_violations
from execution_engine.optimization.deterministic_solver import solve_deterministic_schedule
from execution_engine.optimization.frontier import generate_efficient_frontier
from execution_engine.optimization.stochastic_solver import evaluate_almgren_chriss_stochastic_frontier


def test_deterministic_solver_satisfies_completion_constraint() -> None:
    config = load_config(Path("configs/base.yaml"))
    market = IntradayMarketSimulator(config).simulate(seed=5)
    result = solve_deterministic_schedule(
        config=config,
        expected_volume=market["expected_volume"].to_numpy(),
        bucket_sigma=market["bucket_sigma"].to_numpy(),
        half_spread=market["half_spread"].to_numpy(),
        risk_aversion=config.optimization.risk_aversion_grid[2],
        price=float(market["base_mid_price"].iloc[0]),
    )
    assert abs(result.schedule.sum() - config.order.parent_order_size) < 1e-6
    assert (result.schedule >= 0.0).all()


def test_participation_constraint_is_respected_when_feasible() -> None:
    config = load_config(Path("configs/base.yaml"))
    market = IntradayMarketSimulator(config).simulate(seed=5)
    result = solve_deterministic_schedule(
        config=config,
        expected_volume=market["expected_volume"].to_numpy(),
        bucket_sigma=market["bucket_sigma"].to_numpy(),
        half_spread=market["half_spread"].to_numpy(),
        risk_aversion=config.optimization.risk_aversion_grid[2],
        price=float(market["base_mid_price"].iloc[0]),
    )
    violations = max_participation_violations(
        result.schedule,
        market["expected_volume"].to_numpy(),
        config.order.max_participation_rate,
    )
    assert violations.max() < 1e-6


def test_efficient_frontier_returns_all_risk_aversion_points() -> None:
    config = load_config(Path("configs/base.yaml"))
    market = IntradayMarketSimulator(config).simulate(seed=5)
    frontier = generate_efficient_frontier(config, market)
    assert len(frontier) == len(config.optimization.risk_aversion_grid)
    assert set(frontier["risk_aversion"]) == set(config.optimization.risk_aversion_grid)


def test_higher_risk_aversion_front_loads_the_schedule() -> None:
    config = load_config(Path("configs/base.yaml"))
    market = IntradayMarketSimulator(config).simulate(seed=7)
    expected_volume = market["expected_volume"].to_numpy()
    bucket_sigma = market["bucket_sigma"].to_numpy()
    half_spread = market["half_spread"].to_numpy()
    low_lambda = min(config.optimization.risk_aversion_grid)
    high_lambda = max(config.optimization.risk_aversion_grid)

    low_risk = solve_deterministic_schedule(config, expected_volume, bucket_sigma, half_spread, low_lambda)
    high_risk = solve_deterministic_schedule(config, expected_volume, bucket_sigma, half_spread, high_lambda)

    bucket_index = range(len(low_risk.schedule))
    low_center = sum(i * q for i, q in zip(bucket_index, low_risk.schedule)) / low_risk.schedule.sum()
    high_center = sum(i * q for i, q in zip(bucket_index, high_risk.schedule)) / high_risk.schedule.sum()
    assert high_center < low_center


def test_stochastic_frontier_evaluation_covers_all_risk_points() -> None:
    config = load_config(Path("configs/base.yaml"))
    evaluation = evaluate_almgren_chriss_stochastic_frontier(config, n_paths=3)
    assert len(evaluation.summary) == len(config.optimization.risk_aversion_grid)
    assert set(evaluation.summary["risk_aversion"]) == set(config.optimization.risk_aversion_grid)
    assert (evaluation.summary["mean_completion_rate"] > 0.99).all()
