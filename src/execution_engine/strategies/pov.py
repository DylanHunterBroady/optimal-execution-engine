"""Participation-of-volume execution strategy."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from execution_engine.strategies.base_strategy import BaseStrategy
from execution_engine.types import StrategyContext, StrategyDecision


@dataclass
class POVStrategy(BaseStrategy):
    """Trade a fixed fraction of realized market volume."""

    @property
    def name(self) -> str:
        return "pov"

    def decide(self, context: StrategyContext) -> StrategyDecision:
        target_participation = min(
            self.config.order.max_participation_rate,
            0.06 + 0.12 * self.config.order.urgency,
        )
        spread_ratio = float(context.market_slice["half_spread"] / max(self.average_spread, 1e-12))
        spread_slowdown = 0.6 if spread_ratio > 1.35 else 1.0
        raw_quantity = target_participation * float(context.market_slice["realized_volume"]) * spread_slowdown
        force_completion = context.bucket_index == context.total_buckets - 1 and context.remaining_quantity <= 2.0 * self.config.order.min_child_order_size
        quantity = self.constrain_quantity(
            proposed_quantity=raw_quantity,
            remaining_quantity=context.remaining_quantity,
            market_slice=context.market_slice,
            force_completion=force_completion,
        )
        aggression = float(np.clip(0.45 + 0.25 * self.config.order.urgency + 0.15 * (spread_ratio > 1.35), 0.2, 0.85))
        return StrategyDecision(
            quantity=quantity,
            aggression=aggression,
            rationale="Trade a stable participation rate of realized volume.",
            force_completion=force_completion,
        )
