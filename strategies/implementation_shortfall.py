"""Implementation shortfall style urgency strategy."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from execution_engine.strategies.base_strategy import BaseStrategy
from execution_engine.types import StrategyContext, StrategyDecision
from execution_engine.utils import normalize


@dataclass
class ImplementationShortfallStrategy(BaseStrategy):
    """Front-loaded urgency strategy."""

    cumulative_weights: np.ndarray = field(init=False, default_factory=lambda: np.array([]))

    @property
    def name(self) -> str:
        return "implementation_shortfall"

    def initialize(self, market) -> None:  # type: ignore[override]
        super().initialize(market)
        n = self.config.order.horizon_buckets
        x = np.linspace(0.0, 1.0, n)
        front_load = np.exp(-(0.4 + 3.0 * self.config.order.urgency) * x)
        weights = normalize(front_load)
        self.cumulative_weights = np.cumsum(weights)

    def decide(self, context: StrategyContext) -> StrategyDecision:
        target_cumulative = self.config.order.parent_order_size * self.cumulative_weights[context.bucket_index]
        base_quantity = max(target_cumulative - context.executed_quantity, 0.0)
        time_pressure = context.remaining_quantity / max(self.buckets_left(context.bucket_index), 1)
        raw_quantity = max(base_quantity, time_pressure * (0.7 + 0.6 * self.config.order.urgency))
        force_completion = context.bucket_index == context.total_buckets - 1
        quantity = self.constrain_quantity(
            proposed_quantity=raw_quantity,
            remaining_quantity=context.remaining_quantity,
            market_slice=context.market_slice,
            force_completion=force_completion,
        )
        deficit_ratio = max(
            target_cumulative - context.executed_quantity,
            0.0,
        ) / max(self.config.order.parent_order_size, 1.0)
        aggression = float(np.clip(0.6 + 0.3 * self.config.order.urgency + 1.2 * deficit_ratio, 0.35, 1.0))
        return StrategyDecision(
            quantity=quantity,
            aggression=aggression,
            rationale="Front-loaded implementation shortfall schedule with urgency control.",
            force_completion=force_completion,
        )
