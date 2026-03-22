"""TWAP execution strategy."""

from __future__ import annotations

from dataclasses import dataclass

from execution_engine.strategies.base_strategy import BaseStrategy
from execution_engine.types import StrategyContext, StrategyDecision


@dataclass
class TWAPStrategy(BaseStrategy):
    """Evenly distribute the parent order across buckets."""

    cleanup: bool = True
    aggression_multiplier: float = 1.0

    @property
    def name(self) -> str:
        return "twap"

    def decide(self, context: StrategyContext) -> StrategyDecision:
        buckets_left = self.buckets_left(context.bucket_index)
        raw_quantity = context.remaining_quantity / max(buckets_left, 1) * self.aggression_multiplier
        force_completion = self.cleanup and context.bucket_index == context.total_buckets - 1
        quantity = self.constrain_quantity(
            proposed_quantity=raw_quantity,
            remaining_quantity=context.remaining_quantity,
            market_slice=context.market_slice,
            force_completion=force_completion,
        )
        aggression = min(0.55 * self.aggression_multiplier, 1.0)
        return StrategyDecision(
            quantity=quantity,
            aggression=aggression,
            rationale="Equal-sized schedule over remaining time.",
            force_completion=force_completion,
        )
