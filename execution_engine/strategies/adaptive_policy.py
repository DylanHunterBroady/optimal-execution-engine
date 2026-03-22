"""Adaptive execution policy."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from execution_engine.strategies.base_strategy import BaseStrategy
from execution_engine.types import StrategyContext, StrategyDecision
from execution_engine.utils import normalize


@dataclass
class AdaptivePolicyStrategy(BaseStrategy):
    """Adjust aggressiveness to realized market conditions and fill deficits."""

    cumulative_weights: np.ndarray = field(init=False, default_factory=lambda: np.array([]))

    @property
    def name(self) -> str:
        return "adaptive_policy"

    def initialize(self, market) -> None:  # type: ignore[override]
        super().initialize(market)
        n = self.config.order.horizon_buckets
        x = np.linspace(0.0, 1.0, n)
        vwap_like = self.market["expected_volume"].to_numpy(dtype=float)
        urgency_like = np.exp(-(0.6 + 2.2 * self.config.order.urgency) * x)
        blended = 0.55 * normalize(vwap_like) + 0.45 * normalize(urgency_like)
        self.cumulative_weights = np.cumsum(normalize(blended))

    def decide(self, context: StrategyContext) -> StrategyDecision:
        target_cumulative = self.config.order.parent_order_size * self.cumulative_weights[context.bucket_index]
        target_remaining = max(self.config.order.parent_order_size - target_cumulative, 0.0)
        fill_deficit = max(context.remaining_quantity - target_remaining, 0.0)
        fill_deficit_ratio = fill_deficit / max(self.config.order.parent_order_size, 1.0)

        recent = context.realized_execution.tail(5)
        recent_slippage = float(recent["signed_slippage_per_share"].mean()) if not recent.empty else 0.0
        slippage_signal = recent_slippage / max(float(context.market_slice["base_mid_price"]), 1e-12)
        spread_ratio = float(context.market_slice["half_spread"] / max(self.average_spread, 1e-12))
        vol_ratio = float(context.market_slice["bucket_sigma"] / max(self.average_sigma, 1e-12))

        base_quantity = max(target_cumulative - context.executed_quantity, 0.0)
        catch_up = fill_deficit / max(self.buckets_left(context.bucket_index), 1)
        raw_quantity = base_quantity * (1.0 + 0.25 * max(vol_ratio - 1.0, 0.0)) + 0.7 * catch_up
        if spread_ratio > 1.4 and fill_deficit_ratio < 0.15:
            raw_quantity *= 0.7

        force_completion = context.bucket_index == context.total_buckets - 1
        quantity = self.constrain_quantity(
            proposed_quantity=raw_quantity,
            remaining_quantity=context.remaining_quantity,
            market_slice=context.market_slice,
            force_completion=force_completion,
        )
        aggression = float(
            np.clip(
                0.45
                + 1.2 * fill_deficit_ratio
                + 0.2 * max(vol_ratio - 1.0, 0.0)
                + 6.0 * max(slippage_signal, 0.0)
                - 0.18 * max(spread_ratio - 1.0, 0.0),
                0.2,
                1.0,
            )
        )
        return StrategyDecision(
            quantity=quantity,
            aggression=aggression,
            rationale="Adaptive schedule reacts to remaining inventory, slippage, volatility, and spread.",
            force_completion=force_completion,
        )
