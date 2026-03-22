"""Synthetic intraday market path generation."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from execution_engine.config import ExperimentConfig
from execution_engine.market.liquidity_regime import generate_liquidity_state
from execution_engine.market.spread_model import dynamic_spread_series
from execution_engine.market.volatility_model import generate_intraday_volatility_curve
from execution_engine.market.volume_profile import u_shaped_volume_profile
from execution_engine.utils import evenly_spaced_minutes, get_rng, horizon_fraction


@dataclass
class IntradayMarketSimulator:
    """Generate stylized intraday market paths with microstructure state."""

    config: ExperimentConfig

    def simulate(self, seed: int | None = None) -> pd.DataFrame:
        """Create a synthetic intraday market scenario."""
        rng = get_rng(seed if seed is not None else self.config.optimization.scenario_seed)
        market_cfg = self.config.market
        order_cfg = self.config.order
        n_buckets = order_cfg.horizon_buckets

        volume_weights = u_shaped_volume_profile(n_buckets, market_cfg.intraday_volume_curve_shape)
        regime_state = generate_liquidity_state(
            n_buckets=n_buckets,
            regime_name=market_cfg.regime_name,
            drift_regime=market_cfg.drift_regime,
            mean_reversion_strength=market_cfg.mean_reversion_strength,
            rng=rng,
        )
        bucket_sigma = generate_intraday_volatility_curve(
            n_buckets=n_buckets,
            annualized_volatility=market_cfg.annualized_volatility,
            regime_name=market_cfg.regime_name,
            rng=rng,
        )

        time_fraction = np.linspace(0.0, 1.0, n_buckets, endpoint=False)
        minutes = evenly_spaced_minutes(order_cfg.start_time, order_cfg.end_time, n_buckets)
        horizon_share = horizon_fraction(order_cfg.start_time, order_cfg.end_time)
        daily_volume = market_cfg.adv * horizon_share
        realized_volume_noise = np.exp(0.18 * rng.normal(size=n_buckets))

        expected_volume = daily_volume * volume_weights
        realized_volume = (
            expected_volume
            * regime_state["liquidity_multiplier"]
            * realized_volume_noise
        )
        realized_volume = np.clip(realized_volume, 0.05 * expected_volume, None)

        base_mid = np.empty(n_buckets)
        returns = np.zeros(n_buckets)
        shocks = rng.normal(size=n_buckets)

        base_mid[0] = market_cfg.initial_price
        for bucket in range(1, n_buckets):
            jump = 0.0
            if rng.uniform() < market_cfg.jump_probability:
                jump = rng.normal(scale=market_cfg.jump_scale)

            mean_reversion = 0.0
            if market_cfg.drift_regime in {"mean_revert", "mean_reverting"}:
                mean_reversion = -market_cfg.mean_reversion_strength * (
                    (base_mid[bucket - 1] / market_cfg.initial_price) - 1.0
                ) / n_buckets

            bucket_return = (
                regime_state["alpha"][bucket]
                + bucket_sigma[bucket] * shocks[bucket]
                + jump
                + mean_reversion
            )
            returns[bucket] = bucket_return
            base_mid[bucket] = max(0.01, base_mid[bucket - 1] * (1.0 + bucket_return))

        spread = dynamic_spread_series(
            mid_prices=base_mid,
            base_spread_bps=market_cfg.spread_bps,
            volatility_curve=bucket_sigma,
            liquidity_multiplier=regime_state["liquidity_multiplier"],
            event_indicator=regime_state["event_indicator"],
        )

        frame = pd.DataFrame(
            {
                "bucket": np.arange(n_buckets, dtype=int),
                "time_fraction": time_fraction,
                "clock_minute": minutes,
                "clock_time": [f"{int(m // 60):02d}:{int(m % 60):02d}" for m in minutes],
                "expected_volume_weight": volume_weights,
                "expected_volume": expected_volume,
                "realized_volume": realized_volume,
                "bucket_sigma": bucket_sigma,
                "alpha": regime_state["alpha"],
                "epsilon": shocks,
                "bucket_return": returns,
                "base_mid_price": base_mid,
                "spread": spread,
                "half_spread": 0.5 * spread,
                "liquidity_multiplier": regime_state["liquidity_multiplier"],
                "depth_at_touch": market_cfg.depth_at_touch * regime_state["depth_multiplier"],
                "refill_rate": market_cfg.refill_rate * regime_state["liquidity_multiplier"],
                "event_indicator": regime_state["event_indicator"],
            }
        )
        return frame
