"""Stylized child-order fill model."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from execution_engine.book.adverse_selection import adverse_selection_penalty
from execution_engine.book.lob_state import LOBState
from execution_engine.book.queue_model import queue_fill_decay, queue_penalty_cost
from execution_engine.config import ExperimentConfig
from execution_engine.types import FillOutcome, Side, StrategyDecision


@dataclass
class FillModel:
    """Approximate aggressive and passive fills against a stylized book."""

    config: ExperimentConfig

    def simulate_fill(
        self,
        side: Side,
        decision: StrategyDecision,
        state: LOBState,
        temporary_impact: float,
        transient_impact: float,
        rng: np.random.Generator,
    ) -> FillOutcome:
        """Simulate a child-order fill for a single bucket."""
        fill_cfg = self.config.fill
        impact_cfg = self.config.impact

        requested_quantity = max(decision.quantity, 0.0)
        if requested_quantity == 0:
            return FillOutcome(
                requested_quantity=0.0,
                filled_quantity=0.0,
                marketable_quantity=0.0,
                passive_quantity=0.0,
                unfilled_quantity=0.0,
                average_execution_price=state.mid_price,
                half_spread=state.half_spread,
                temporary_impact=0.0,
                transient_impact=0.0,
                queue_penalty=0.0,
                adverse_selection=0.0,
                latency_penalty=0.0,
                passive_capture=0.0,
                fill_rate=0.0,
            )

        marketable_fraction = np.clip(
            fill_cfg.marketable_fraction + 0.25 * (decision.aggression - 0.5),
            0.1,
            1.0,
        )
        marketable_target = requested_quantity * marketable_fraction
        passive_target = requested_quantity - marketable_target

        available_touch_liquidity = state.depth_at_touch * (0.7 + 0.6 * decision.aggression) * state.refill_rate
        marketable_filled = min(marketable_target, available_touch_liquidity)

        queue_decay = queue_fill_decay(requested_quantity, state.depth_at_touch, fill_cfg.queue_penalty)
        passive_fill_mean = (
            fill_cfg.passive_fill_probability
            * queue_decay
            * state.liquidity_multiplier
            * (1.0 - 0.5 * fill_cfg.cancellation_rate)
        )
        passive_fill_mean = np.clip(passive_fill_mean, 0.05, 1.0)
        passive_fill_noise = np.clip(rng.normal(loc=1.0, scale=0.12), 0.5, 1.5)
        passive_filled = min(passive_target, passive_target * passive_fill_mean * passive_fill_noise)

        filled_quantity = marketable_filled + passive_filled
        unfilled_quantity = max(requested_quantity - filled_quantity, 0.0)

        queue_penalty = queue_penalty_cost(
            requested_quantity=requested_quantity,
            depth_at_touch=state.depth_at_touch,
            base_penalty=fill_cfg.queue_penalty,
            price=state.mid_price,
            liquidity_multiplier=state.liquidity_multiplier,
        )
        adverse = adverse_selection_penalty(
            side=side,
            price=state.mid_price,
            alpha=state.alpha,
            bucket_sigma=state.bucket_sigma,
            coefficient=impact_cfg.adverse_selection_coefficient,
            aggression=decision.aggression,
            event_indicator=state.event_indicator,
        )
        passive_capture = state.half_spread * np.clip(0.55 + 0.2 * (1.0 - decision.aggression), 0.2, 0.85)
        latency_cost = state.mid_price * fill_cfg.latency_penalty * state.bucket_sigma * decision.aggression

        aggressive_price = state.mid_price + side.sign * (
            state.half_spread + temporary_impact + transient_impact + queue_penalty + adverse + latency_cost
        )
        passive_price = state.mid_price + side.sign * (
            -passive_capture + 0.35 * temporary_impact + 0.7 * transient_impact + queue_penalty + adverse
        )

        if filled_quantity > 0:
            average_execution_price = (
                marketable_filled * aggressive_price + passive_filled * passive_price
            ) / filled_quantity
            effective_temp = (
                marketable_filled * temporary_impact + passive_filled * 0.35 * temporary_impact
            ) / filled_quantity
            effective_transient = (
                marketable_filled * transient_impact + passive_filled * 0.7 * transient_impact
            ) / filled_quantity
            effective_capture = passive_capture * passive_filled / filled_quantity
        else:
            average_execution_price = state.mid_price
            effective_temp = 0.0
            effective_transient = 0.0
            effective_capture = 0.0

        return FillOutcome(
            requested_quantity=requested_quantity,
            filled_quantity=filled_quantity,
            marketable_quantity=marketable_filled,
            passive_quantity=passive_filled,
            unfilled_quantity=unfilled_quantity,
            average_execution_price=average_execution_price,
            half_spread=state.half_spread,
            temporary_impact=effective_temp,
            transient_impact=effective_transient,
            queue_penalty=queue_penalty,
            adverse_selection=adverse,
            latency_penalty=latency_cost,
            passive_capture=effective_capture,
            fill_rate=filled_quantity / requested_quantity,
        )
