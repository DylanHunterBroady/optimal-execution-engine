"""VWAP execution strategy."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from execution_engine.strategies.base_strategy import BaseStrategy
from execution_engine.types import StrategyContext, StrategyDecision


@dataclass
class VWAPStrategy(BaseStrategy):
    """Execute proportionally to expected market volume."""

    catch_up_strength: float = 0.35
    cumulative_weights: np.ndarray = field(init=False, default_factory=lambda: np.array([]))

    @property
    def name(self) -> str:
        return "vwap"

    def initialize(self, market) -> None:  # type: ignore[override]
        super().initialize(market)
        expected_weights = self.market["expected_volume"].to_numpy(dtype=float)
        expected_weights = expected_weights / expected_weights.sum()
        self.cumulative_weights = np.cumsum(expected_weights)

    def decide(self, context: StrategyContext) -> StrategyDecision:
        target_cumulative = self.config.order.parent_order_size * self.cumulative_weights[context.bucket_index]
        schedule_deficit = max(target_cumulative - context.executed_quantity, 0.0)
        catch_up = self.catch_up_strength * max(
            context.remaining_quantity - (self.config.order.parent_order_size - target_cumulative),
            0.0,
        ) / max(self.buckets_left(context.bucket_index), 1)
        raw_quantity = schedule_deficit + catch_up
        force_completion = context.bucket_index == context.total_buckets - 1
        quantity = self.constrain_quantity(
            proposed_quantity=raw_quantity,
            remaining_quantity=context.remaining_quantity,
            market_slice=context.market_slice,
            force_completion=force_completion,
        )
        spread_ratio = float(context.market_slice["half_spread"] / max(self.average_spread, 1e-12))
        aggression = float(np.clip(0.5 + 0.2 * max(schedule_deficit > 0, 0) - 0.1 * (spread_ratio - 1.0), 0.25, 0.9))
        return StrategyDecision(
            quantity=quantity,
            aggression=aggression,
            rationale="Track cumulative expected volume with catch-up logic.",
            force_completion=force_completion,
        )
