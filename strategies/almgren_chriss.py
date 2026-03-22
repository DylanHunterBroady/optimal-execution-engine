"""Deterministic Almgren-Chriss style strategy."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from execution_engine.optimization.deterministic_solver import solve_deterministic_schedule
from execution_engine.strategies.base_strategy import BaseStrategy
from execution_engine.types import StrategyContext, StrategyDecision


@dataclass
class AlmgrenChrissStrategy(BaseStrategy):
    """Use the deterministic solver to construct a schedule."""

    cumulative_schedule: np.ndarray = field(init=False, default_factory=lambda: np.array([]))
    risk_aversion: float | None = None

    @property
    def name(self) -> str:
        return "almgren_chriss"

    def initialize(self, market) -> None:  # type: ignore[override]
        super().initialize(market)
        grid = sorted(self.config.optimization.risk_aversion_grid)
        chosen_risk_aversion = self.risk_aversion if self.risk_aversion is not None else grid[len(grid) // 2]
        result = solve_deterministic_schedule(
            config=self.config,
            expected_volume=self.market["expected_volume"].to_numpy(),
            bucket_sigma=self.market["bucket_sigma"].to_numpy(),
            half_spread=self.market["half_spread"].to_numpy(),
            risk_aversion=chosen_risk_aversion,
            price=float(self.market["base_mid_price"].iloc[0]),
        )
        self.cumulative_schedule = np.cumsum(result.schedule)

    def decide(self, context: StrategyContext) -> StrategyDecision:
        target_cumulative = self.cumulative_schedule[context.bucket_index]
        raw_quantity = max(target_cumulative - context.executed_quantity, 0.0)
        force_completion = context.bucket_index == context.total_buckets - 1
        quantity = self.constrain_quantity(
            proposed_quantity=raw_quantity,
            remaining_quantity=context.remaining_quantity,
            market_slice=context.market_slice,
            force_completion=force_completion,
        )
        aggression = 0.7 if context.bucket_index < context.total_buckets - 1 else 1.0
        return StrategyDecision(
            quantity=quantity,
            aggression=aggression,
            rationale="Deterministic Almgren-Chriss schedule from constrained optimizer.",
            force_completion=force_completion,
        )
