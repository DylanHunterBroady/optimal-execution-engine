"""Shared typed objects for the execution engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import pandas as pd


class Side(str, Enum):
    """Order side."""

    BUY = "buy"
    SELL = "sell"

    @property
    def sign(self) -> int:
        """Signed direction for costs and price displacements."""
        return 1 if self is Side.BUY else -1


@dataclass(frozen=True)
class StrategyDecision:
    """Requested trading action for a bucket."""

    quantity: float
    aggression: float
    rationale: str = ""
    force_completion: bool = False


@dataclass(frozen=True)
class FillOutcome:
    """Executed child-order details."""

    requested_quantity: float
    filled_quantity: float
    marketable_quantity: float
    passive_quantity: float
    unfilled_quantity: float
    average_execution_price: float
    half_spread: float
    temporary_impact: float
    transient_impact: float
    queue_penalty: float
    adverse_selection: float
    latency_penalty: float
    passive_capture: float
    fill_rate: float


@dataclass(frozen=True)
class StrategyContext:
    """State visible to strategies in each bucket."""

    bucket_index: int
    total_buckets: int
    remaining_quantity: float
    executed_quantity: float
    realized_cost: float
    market_slice: pd.Series
    realized_execution: pd.DataFrame


@dataclass(frozen=True)
class FrontierPoint:
    """Risk-return point for efficient frontier output."""

    risk_aversion: float
    expected_cost: float
    cost_std: float
    completion_rate: float
    average_participation: float
    schedule: list[float] = field(default_factory=list)


@dataclass
class SimulationResult:
    """Container for a single strategy simulation run."""

    strategy_name: str
    market: pd.DataFrame
    executions: pd.DataFrame
    cost_breakdown: dict[str, float]
    metrics: dict[str, float]
    diagnostics: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_summary_row(self) -> dict[str, Any]:
        """Flatten the result into a summary record."""
        row: dict[str, Any] = {"strategy": self.strategy_name}
        row.update(self.metrics)
        row.update({f"cost_{k}": v for k, v in self.cost_breakdown.items()})
        return row


@dataclass
class StrategySuiteResult:
    """Common-market comparison across multiple strategies."""

    market: pd.DataFrame
    results: list[SimulationResult]
    summary: pd.DataFrame

    def __getitem__(self, key: str) -> Any:
        """Backward-compatible dictionary-style access."""
        return getattr(self, key)

    def get_result(self, strategy_name: str) -> SimulationResult:
        """Fetch a named strategy result."""
        for result in self.results:
            if result.strategy_name == strategy_name:
                return result
        raise KeyError(strategy_name)

    @property
    def best_result(self) -> SimulationResult:
        """Lowest-implementation-shortfall result."""
        return min(self.results, key=lambda result: result.metrics["implementation_shortfall"])


@dataclass
class MonteCarloResult:
    """Monte Carlo outputs for a family of strategies."""

    raw: pd.DataFrame
    summary: pd.DataFrame

    def __getitem__(self, key: str) -> Any:
        """Backward-compatible dictionary-style access."""
        return getattr(self, key)
