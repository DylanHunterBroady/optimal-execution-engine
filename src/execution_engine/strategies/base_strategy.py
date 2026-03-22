"""Base interface for execution strategies."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from execution_engine.config import ExperimentConfig
from execution_engine.types import StrategyContext, StrategyDecision


@dataclass
class BaseStrategy(ABC):
    """Abstract strategy interface."""

    config: ExperimentConfig
    market: pd.DataFrame | None = field(init=False, default=None)
    average_spread: float = field(init=False, default=0.0)
    average_sigma: float = field(init=False, default=0.0)

    @property
    @abstractmethod
    def name(self) -> str:
        """Readable strategy name."""

    def initialize(self, market: pd.DataFrame) -> None:
        """Prepare strategy state before simulation starts."""
        self.market = market.reset_index(drop=True)
        self.average_spread = float(self.market["half_spread"].mean())
        self.average_sigma = float(self.market["bucket_sigma"].mean())

    @abstractmethod
    def decide(self, context: StrategyContext) -> StrategyDecision:
        """Choose the order size and aggression for the current bucket."""

    def constrain_quantity(
        self,
        proposed_quantity: float,
        remaining_quantity: float,
        market_slice: pd.Series,
        force_completion: bool = False,
    ) -> float:
        """Apply non-negativity, participation, and minimum-size constraints."""
        order_cfg = self.config.order
        max_by_participation = float(order_cfg.max_participation_rate * market_slice["realized_volume"])
        quantity = max(proposed_quantity, 0.0)

        if force_completion:
            quantity = remaining_quantity
        else:
            quantity = min(quantity, remaining_quantity, max_by_participation)
            if 0.0 < quantity < order_cfg.min_child_order_size and remaining_quantity > order_cfg.min_child_order_size:
                quantity = 0.0
        return float(min(quantity, remaining_quantity))

    def cumulative_target_quantity(self, bucket_index: int, weights: np.ndarray) -> float:
        """Total shares that should be completed by the end of the current bucket."""
        total_quantity = self.config.order.parent_order_size
        return float(total_quantity * np.clip(weights[: bucket_index + 1].sum(), 0.0, 1.0))

    def buckets_left(self, bucket_index: int) -> int:
        """Number of buckets remaining including the current one."""
        return self.config.order.horizon_buckets - bucket_index
