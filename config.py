"""Typed configuration objects and YAML loading."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from execution_engine.constants import DEFAULT_STRATEGIES
from execution_engine.types import Side
from execution_engine.utils import parse_time_to_minutes


@dataclass(frozen=True)
class OrderConfig:
    """Parent-order settings."""

    parent_order_size: float = 250_000.0
    side: Side = Side.BUY
    start_time: str = "09:30"
    end_time: str = "16:00"
    horizon_buckets: int = 39
    urgency: float = 0.5
    benchmark_type: str = "implementation_shortfall"
    max_participation_rate: float = 0.15
    min_child_order_size: float = 500.0
    residual_liquidation_rule: str = "market"


@dataclass(frozen=True)
class MarketConfig:
    """Synthetic market process settings."""

    initial_price: float = 100.0
    annualized_volatility: float = 0.28
    adv: float = 12_000_000.0
    intraday_volume_curve_shape: str = "u_shaped"
    spread_bps: float = 7.5
    depth_at_touch: float = 35_000.0
    refill_rate: float = 0.8
    drift_regime: str = "neutral"
    jump_probability: float = 0.01
    jump_scale: float = 0.012
    mean_reversion_strength: float = 0.15
    regime_name: str = "neutral"


@dataclass(frozen=True)
class ImpactConfig:
    """Temporary, permanent, and transient impact parameters."""

    temporary_impact_coefficient: float = 0.0018
    permanent_impact_coefficient: float = 0.0004
    impact_exponent: float = 0.5
    resilience_decay: float = 0.45
    information_leakage_coefficient: float = 0.25
    adverse_selection_coefficient: float = 0.12
    impact_model: str = "square_root"


@dataclass(frozen=True)
class FillConfig:
    """Passive fill and microstructure approximation parameters."""

    passive_fill_probability: float = 0.55
    queue_penalty: float = 0.0002
    cancellation_rate: float = 0.08
    marketable_fraction: float = 0.65
    latency_penalty: float = 0.03


@dataclass(frozen=True)
class OptimizationConfig:
    """Optimizer and experiment settings."""

    risk_aversion_grid: list[float] = field(
        default_factory=lambda: [1e-7, 3e-7, 1e-6, 3e-6, 1e-5]
    )
    monte_carlo_paths: int = 100
    solver_tolerance: float = 1e-8
    penalty_weights: dict[str, float] = field(
        default_factory=lambda: {
            "completion": 1e6,
            "participation": 5e3,
            "smoothness": 50.0,
        }
    )
    scenario_seed: int = 7


@dataclass(frozen=True)
class ExperimentConfig:
    """Top-level experiment configuration."""

    order: OrderConfig = field(default_factory=OrderConfig)
    market: MarketConfig = field(default_factory=MarketConfig)
    impact: ImpactConfig = field(default_factory=ImpactConfig)
    fill: FillConfig = field(default_factory=FillConfig)
    optimization: OptimizationConfig = field(default_factory=OptimizationConfig)
    strategies: list[str] = field(default_factory=lambda: DEFAULT_STRATEGIES.copy())
    notes: str = ""

    def replace(self, **overrides: Any) -> "ExperimentConfig":
        """Return a new config with top-level dataclass replacements."""
        data = {
            "order": overrides.get("order", self.order),
            "market": overrides.get("market", self.market),
            "impact": overrides.get("impact", self.impact),
            "fill": overrides.get("fill", self.fill),
            "optimization": overrides.get("optimization", self.optimization),
            "strategies": overrides.get("strategies", self.strategies),
            "notes": overrides.get("notes", self.notes),
        }
        return ExperimentConfig(**data)


def _decode_side(raw: str | Side | None) -> Side:
    return raw if isinstance(raw, Side) else Side(raw or Side.BUY.value)


def _load_section(section_type: type[Any], raw: dict[str, Any] | None) -> Any:
    raw = dict(raw or {})
    if section_type is OrderConfig and "side" in raw:
        raw["side"] = _decode_side(raw["side"])
    return section_type(**raw)


def load_config(path: str | Path) -> ExperimentConfig:
    """Load an experiment configuration from YAML."""
    with Path(path).open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}

    config = ExperimentConfig(
        order=_load_section(OrderConfig, raw.get("order")),
        market=_load_section(MarketConfig, raw.get("market")),
        impact=_load_section(ImpactConfig, raw.get("impact")),
        fill=_load_section(FillConfig, raw.get("fill")),
        optimization=_load_section(OptimizationConfig, raw.get("optimization")),
        strategies=list(raw.get("strategies", DEFAULT_STRATEGIES)),
        notes=str(raw.get("notes", "")),
    )
    _validate_config(config)
    return config


def _validate_config(config: ExperimentConfig) -> None:
    order = config.order
    if order.parent_order_size <= 0:
        raise ValueError("parent_order_size must be positive")
    if order.horizon_buckets <= 0:
        raise ValueError("horizon_buckets must be positive")
    if not 0 < order.max_participation_rate <= 1:
        raise ValueError("max_participation_rate must be in (0, 1]")
    if not 0 <= order.urgency <= 1:
        raise ValueError("urgency must be in [0, 1]")
    if parse_time_to_minutes(order.start_time) >= parse_time_to_minutes(order.end_time):
        raise ValueError("start_time must be earlier than end_time")
    if order.benchmark_type not in {"implementation_shortfall", "arrival_price", "vwap"}:
        raise ValueError("benchmark_type must be one of: implementation_shortfall, arrival_price, vwap")
    if order.residual_liquidation_rule not in {"market"}:
        raise ValueError("residual_liquidation_rule currently supports only 'market'")

    market = config.market
    if market.initial_price <= 0:
        raise ValueError("initial_price must be positive")
    if market.annualized_volatility <= 0:
        raise ValueError("annualized_volatility must be positive")
    if market.adv <= 0:
        raise ValueError("adv must be positive")
    if market.depth_at_touch <= 0:
        raise ValueError("depth_at_touch must be positive")

    impact = config.impact
    if impact.temporary_impact_coefficient < 0 or impact.permanent_impact_coefficient < 0:
        raise ValueError("impact coefficients must be non-negative")
    if impact.impact_model not in {"linear", "square_root"}:
        raise ValueError("impact_model must be 'linear' or 'square_root'")
    if impact.impact_exponent <= 0:
        raise ValueError("impact_exponent must be positive")
    if impact.resilience_decay < 0:
        raise ValueError("resilience_decay must be non-negative")

    fill = config.fill
    if not 0 <= fill.passive_fill_probability <= 1:
        raise ValueError("passive_fill_probability must be in [0, 1]")
    if not 0 <= fill.marketable_fraction <= 1:
        raise ValueError("marketable_fraction must be in [0, 1]")
    if fill.queue_penalty < 0 or fill.cancellation_rate < 0 or fill.latency_penalty < 0:
        raise ValueError("fill penalties and cancellation rate must be non-negative")

    optimization = config.optimization
    if optimization.monte_carlo_paths <= 0:
        raise ValueError("monte_carlo_paths must be positive")
    if not optimization.risk_aversion_grid:
        raise ValueError("risk_aversion_grid must not be empty")
    if any(value < 0 for value in optimization.risk_aversion_grid):
        raise ValueError("risk_aversion_grid values must be non-negative")

    from execution_engine.strategies import STRATEGY_REGISTRY

    unknown_strategies = sorted(set(config.strategies) - set(STRATEGY_REGISTRY))
    if unknown_strategies:
        raise ValueError(f"Unknown strategies in config: {unknown_strategies}")
