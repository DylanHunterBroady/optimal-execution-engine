"""Single-path execution simulator."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from execution_engine.book.fill_model import FillModel
from execution_engine.book.lob_state import LOBState
from execution_engine.config import ExperimentConfig
from execution_engine.cost.benchmark_metrics import compute_benchmark_metrics
from execution_engine.cost.decomposition import build_cost_decomposition
from execution_engine.cost.implementation_shortfall import implementation_shortfall_dollars
from execution_engine.impact.linear_impact import linear_temporary_impact
from execution_engine.impact.permanent_impact import linear_permanent_impact
from execution_engine.impact.square_root_impact import square_root_temporary_impact
from execution_engine.impact.transient_impact import TransientImpactModel
from execution_engine.market.price_process import IntradayMarketSimulator
from execution_engine.strategies import build_strategy
from execution_engine.strategies.base_strategy import BaseStrategy
from execution_engine.types import Side, SimulationResult, StrategyContext, StrategyDecision
from execution_engine.utils import get_rng, participation_rate


@dataclass
class ExecutionSimulator:
    """Simulate one execution path for one strategy."""

    config: ExperimentConfig

    def run(
        self,
        strategy: str | BaseStrategy,
        seed: int | None = None,
        market: pd.DataFrame | None = None,
    ) -> SimulationResult:
        """Run a full execution simulation."""
        rng = get_rng(seed if seed is not None else self.config.optimization.scenario_seed)
        market_frame = (
            market.copy().reset_index(drop=True)
            if market is not None
            else IntradayMarketSimulator(self.config).simulate(seed=seed)
        )
        strategy_obj = build_strategy(strategy, config=self.config) if isinstance(strategy, str) else strategy
        strategy_obj.initialize(market_frame)

        fill_model = FillModel(self.config)
        transient_model = TransientImpactModel(
            coefficient=self.config.impact.temporary_impact_coefficient * self.config.impact.information_leakage_coefficient,
            exponent=max(self.config.impact.impact_exponent, 0.5),
            decay=self.config.impact.resilience_decay,
        )

        side = self.config.order.side
        arrival_price = float(market_frame["base_mid_price"].iloc[0])
        remaining_quantity = float(self.config.order.parent_order_size)
        executed_quantity = 0.0
        realized_cost = 0.0
        signed_permanent_shift = 0.0
        execution_rows: list[dict[str, float | int | str | bool]] = []

        for bucket_index, row in market_frame.iterrows():
            adjusted_mid_pre = float(row["base_mid_price"] + signed_permanent_shift)
            market_slice = row.copy()
            market_slice["adjusted_mid_price"] = adjusted_mid_pre

            context = StrategyContext(
                bucket_index=bucket_index,
                total_buckets=self.config.order.horizon_buckets,
                remaining_quantity=remaining_quantity,
                executed_quantity=executed_quantity,
                realized_cost=realized_cost,
                market_slice=market_slice,
                realized_execution=pd.DataFrame(execution_rows),
            )
            decision = strategy_obj.decide(context)
            requested_quantity = min(max(decision.quantity, 0.0), remaining_quantity)

            temporary_impact = self._temporary_impact(
                quantity=requested_quantity,
                bucket_volume=float(row["realized_volume"]),
                price=adjusted_mid_pre,
                liquidity_multiplier=float(row["liquidity_multiplier"]),
            )
            transient_impact = transient_model.evaluate(
                quantity=requested_quantity,
                bucket_volume=float(row["realized_volume"]),
                price=adjusted_mid_pre,
                liquidity_multiplier=float(row["liquidity_multiplier"]),
            )
            state = LOBState.from_market_row(row, adjusted_mid_pre)
            fill = fill_model.simulate_fill(
                side=side,
                decision=StrategyDecision(
                    quantity=requested_quantity,
                    aggression=decision.aggression,
                    rationale=decision.rationale,
                    force_completion=decision.force_completion,
                ),
                state=state,
                temporary_impact=temporary_impact,
                transient_impact=transient_impact,
                rng=rng,
            )

            filled_quantity = min(fill.filled_quantity, remaining_quantity)
            remaining_start = remaining_quantity
            permanent_cost_before = side.sign * filled_quantity * signed_permanent_shift
            implementation_cost = implementation_shortfall_dollars(
                side=side,
                quantity=filled_quantity,
                execution_price=fill.average_execution_price,
                benchmark_price=arrival_price,
            )
            market_drift_cost = side.sign * filled_quantity * (float(row["base_mid_price"]) - arrival_price)
            spread_paid_cost = fill.marketable_quantity * fill.half_spread
            spread_capture_cost = filled_quantity * fill.passive_capture
            temporary_impact_cost = filled_quantity * fill.temporary_impact
            transient_impact_cost = filled_quantity * fill.transient_impact
            queue_penalty_cost = filled_quantity * fill.queue_penalty
            adverse_selection_cost = filled_quantity * fill.adverse_selection
            latency_penalty_cost = fill.marketable_quantity * fill.latency_penalty

            permanent_increment = side.sign * linear_permanent_impact(
                quantity=filled_quantity,
                adv=self.config.market.adv,
                price=adjusted_mid_pre,
                coefficient=self.config.impact.permanent_impact_coefficient,
            )
            signed_permanent_shift += permanent_increment
            adjusted_mid_post = float(row["base_mid_price"] + signed_permanent_shift)

            remaining_quantity = max(remaining_quantity - filled_quantity, 0.0)
            executed_quantity += filled_quantity
            realized_cost += implementation_cost

            execution_rows.append(
                {
                    "bucket": int(bucket_index),
                    "clock_time": str(row["clock_time"]),
                    "decision_quantity": requested_quantity,
                    "aggression": decision.aggression,
                    "filled_quantity": filled_quantity,
                    "marketable_quantity": fill.marketable_quantity,
                    "passive_quantity": fill.passive_quantity,
                    "unfilled_quantity": fill.unfilled_quantity,
                    "remaining_start": remaining_start,
                    "remaining_end": remaining_quantity,
                    "realized_volume": float(row["realized_volume"]),
                    "base_mid_price": float(row["base_mid_price"]),
                    "adjusted_mid_pre": adjusted_mid_pre,
                    "adjusted_mid_post": adjusted_mid_post,
                    "average_execution_price": fill.average_execution_price,
                    "half_spread": fill.half_spread,
                    "temporary_impact_per_share": fill.temporary_impact,
                    "transient_impact_per_share": fill.transient_impact,
                    "queue_penalty_per_share": fill.queue_penalty,
                    "adverse_selection_per_share": fill.adverse_selection,
                    "latency_penalty_per_share": fill.latency_penalty,
                    "passive_capture_per_share": fill.passive_capture,
                    "market_drift_cost": market_drift_cost,
                    "permanent_impact_cost": permanent_cost_before,
                    "spread_paid_cost": spread_paid_cost,
                    "spread_capture_cost": spread_capture_cost,
                    "temporary_impact_cost": temporary_impact_cost,
                    "transient_impact_cost": transient_impact_cost,
                    "queue_penalty_cost": queue_penalty_cost,
                    "adverse_selection_cost": adverse_selection_cost,
                    "latency_penalty_cost": latency_penalty_cost,
                    "residual_liquidation_cost": 0.0,
                    "opportunity_cost": 0.0,
                    "signed_slippage_per_share": side.sign * (fill.average_execution_price - float(row["base_mid_price"])),
                    "implementation_shortfall_dollars": implementation_cost,
                    "participation_rate": participation_rate(filled_quantity, float(row["realized_volume"])),
                    "fill_rate": fill.fill_rate,
                    "is_residual_liquidation": False,
                }
            )

        if remaining_quantity > 1e-9:
            cleanup_row = self._residual_liquidation_row(
                side=side,
                remaining_quantity=remaining_quantity,
                arrival_price=arrival_price,
                signed_permanent_shift=signed_permanent_shift,
                last_market_row=market_frame.iloc[-1],
                transient_model=transient_model,
            )
            execution_rows.append(cleanup_row)
            executed_quantity += float(cleanup_row["filled_quantity"])
            realized_cost += float(cleanup_row["implementation_shortfall_dollars"])
            remaining_quantity = float(cleanup_row["remaining_end"])

        executions = pd.DataFrame(execution_rows)
        cost_breakdown = build_cost_decomposition(executions)
        metrics = compute_benchmark_metrics(
            executions=executions,
            market=market_frame,
            order_size=self.config.order.parent_order_size,
            arrival_price=arrival_price,
            side=side,
            benchmark_type=self.config.order.benchmark_type,
        )
        diagnostics = {
            "residual_quantity": remaining_quantity,
            "max_bucket_participation": float(executions["participation_rate"].max()) if not executions.empty else 0.0,
            "mean_fill_rate": float(executions["fill_rate"].mean()) if not executions.empty else 0.0,
        }
        return SimulationResult(
            strategy_name=strategy_obj.name,
            market=market_frame,
            executions=executions,
            cost_breakdown=cost_breakdown,
            metrics=metrics,
            diagnostics=diagnostics,
            metadata={
                "seed": seed,
                "arrival_price": arrival_price,
                "benchmark_type": self.config.order.benchmark_type,
                "residual_liquidation_rule": self.config.order.residual_liquidation_rule,
            },
        )

    def _temporary_impact(
        self,
        quantity: float,
        bucket_volume: float,
        price: float,
        liquidity_multiplier: float,
    ) -> float:
        if self.config.impact.impact_model == "linear":
            return linear_temporary_impact(
                quantity=quantity,
                bucket_volume=bucket_volume,
                price=price,
                coefficient=self.config.impact.temporary_impact_coefficient,
                liquidity_multiplier=liquidity_multiplier,
            )
        return square_root_temporary_impact(
            quantity=quantity,
            bucket_volume=bucket_volume,
            price=price,
            coefficient=self.config.impact.temporary_impact_coefficient,
            exponent=self.config.impact.impact_exponent,
            liquidity_multiplier=liquidity_multiplier,
        )

    def _residual_liquidation_row(
        self,
        side: Side,
        remaining_quantity: float,
        arrival_price: float,
        signed_permanent_shift: float,
        last_market_row: pd.Series,
        transient_model: TransientImpactModel,
    ) -> dict[str, float | int | str | bool]:
        """Force-liquidate any residual quantity at the close."""
        adjusted_mid_pre = float(last_market_row["base_mid_price"] + signed_permanent_shift)
        temporary_impact = self._temporary_impact(
            quantity=remaining_quantity,
            bucket_volume=max(float(last_market_row["realized_volume"]), remaining_quantity),
            price=adjusted_mid_pre,
            liquidity_multiplier=float(last_market_row["liquidity_multiplier"]),
        )
        transient_impact = transient_model.evaluate(
            quantity=remaining_quantity,
            bucket_volume=max(float(last_market_row["realized_volume"]), remaining_quantity),
            price=adjusted_mid_pre,
            liquidity_multiplier=float(last_market_row["liquidity_multiplier"]),
        )
        cleanup_half_spread = 1.2 * float(last_market_row["half_spread"])
        cleanup_price = adjusted_mid_pre + side.sign * (cleanup_half_spread + temporary_impact + transient_impact)
        implementation_cost = implementation_shortfall_dollars(
            side=side,
            quantity=remaining_quantity,
            execution_price=cleanup_price,
            benchmark_price=arrival_price,
        )
        market_drift_cost = side.sign * remaining_quantity * (float(last_market_row["base_mid_price"]) - arrival_price)
        permanent_cost = side.sign * remaining_quantity * signed_permanent_shift
        spread_paid_cost = remaining_quantity * cleanup_half_spread
        temporary_impact_cost = remaining_quantity * temporary_impact
        transient_impact_cost = remaining_quantity * transient_impact
        residual_cost = spread_paid_cost + temporary_impact_cost + transient_impact_cost
        return {
            "bucket": int(last_market_row["bucket"]) + 1,
            "clock_time": "CLOSE_CLEANUP",
            "decision_quantity": remaining_quantity,
            "aggression": 1.0,
            "filled_quantity": remaining_quantity,
            "marketable_quantity": remaining_quantity,
            "passive_quantity": 0.0,
            "unfilled_quantity": 0.0,
            "remaining_start": remaining_quantity,
            "remaining_end": 0.0,
            "realized_volume": float(last_market_row["realized_volume"]),
            "base_mid_price": float(last_market_row["base_mid_price"]),
            "adjusted_mid_pre": adjusted_mid_pre,
            "adjusted_mid_post": adjusted_mid_pre,
            "average_execution_price": cleanup_price,
            "half_spread": cleanup_half_spread,
            "temporary_impact_per_share": temporary_impact,
            "transient_impact_per_share": transient_impact,
            "queue_penalty_per_share": 0.0,
            "adverse_selection_per_share": 0.0,
            "latency_penalty_per_share": 0.0,
            "passive_capture_per_share": 0.0,
            "market_drift_cost": market_drift_cost,
            "permanent_impact_cost": permanent_cost,
            "spread_paid_cost": spread_paid_cost,
            "spread_capture_cost": 0.0,
            "temporary_impact_cost": temporary_impact_cost,
            "transient_impact_cost": transient_impact_cost,
            "queue_penalty_cost": 0.0,
            "adverse_selection_cost": 0.0,
            "latency_penalty_cost": 0.0,
            "residual_liquidation_cost": residual_cost,
            "opportunity_cost": 0.0,
            "signed_slippage_per_share": side.sign * (cleanup_price - float(last_market_row["base_mid_price"])),
            "implementation_shortfall_dollars": implementation_cost,
            "participation_rate": participation_rate(remaining_quantity, max(float(last_market_row["realized_volume"]), remaining_quantity)),
            "fill_rate": 1.0,
            "is_residual_liquidation": True,
        }
