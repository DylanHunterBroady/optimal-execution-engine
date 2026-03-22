"""Transient impact with resilience decay."""

from __future__ import annotations

from dataclasses import dataclass
from math import exp

from execution_engine.constants import EPSILON


@dataclass
class TransientImpactModel:
    """Track residual temporary impact that decays over time."""

    coefficient: float
    exponent: float
    decay: float
    state: float = 0.0

    def reset(self) -> None:
        """Reset accumulated transient impact."""
        self.state = 0.0

    def evaluate(
        self,
        quantity: float,
        bucket_volume: float,
        price: float,
        liquidity_multiplier: float = 1.0,
    ) -> float:
        """Return the transient component to charge in the current bucket."""
        participation = quantity / max(bucket_volume, EPSILON)
        decayed_state = self.state * exp(-self.decay)
        increment = price * self.coefficient * participation ** self.exponent / max(liquidity_multiplier, EPSILON)
        current_impact = decayed_state + 0.5 * increment
        self.state = decayed_state + increment
        return current_impact
