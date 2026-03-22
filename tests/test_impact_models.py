from __future__ import annotations

from execution_engine.config import ExperimentConfig
from execution_engine.impact.linear_impact import linear_temporary_impact
from execution_engine.impact.permanent_impact import linear_permanent_impact
from execution_engine.impact.square_root_impact import square_root_temporary_impact
from execution_engine.impact.transient_impact import TransientImpactModel


def test_temporary_impact_is_monotonic_in_quantity() -> None:
    price = 100.0
    bucket_volume = 1_000_000.0
    coefficient = 0.0015

    small = linear_temporary_impact(10_000.0, bucket_volume, price, coefficient)
    large = linear_temporary_impact(50_000.0, bucket_volume, price, coefficient)
    assert large > small > 0.0

    small_sqrt = square_root_temporary_impact(10_000.0, bucket_volume, price, coefficient, exponent=0.5)
    large_sqrt = square_root_temporary_impact(50_000.0, bucket_volume, price, coefficient, exponent=0.5)
    assert large_sqrt > small_sqrt > 0.0


def test_permanent_impact_is_monotonic_in_order_fraction() -> None:
    price = 100.0
    adv = 10_000_000.0
    coefficient = 0.0004
    assert linear_permanent_impact(50_000.0, adv, price, coefficient) > linear_permanent_impact(10_000.0, adv, price, coefficient)


def test_transient_impact_state_accumulates_and_decays() -> None:
    model = TransientImpactModel(coefficient=0.0005, exponent=0.5, decay=0.5)
    first = model.evaluate(quantity=20_000.0, bucket_volume=1_000_000.0, price=100.0)
    second = model.evaluate(quantity=20_000.0, bucket_volume=1_000_000.0, price=100.0)
    third = model.evaluate(quantity=0.0, bucket_volume=1_000_000.0, price=100.0)

    assert second > first
    assert third < second


def test_default_config_impact_parameters_are_reasonable() -> None:
    config = ExperimentConfig()
    assert 0.0 < config.impact.temporary_impact_coefficient < 0.01
    assert 0.0 < config.impact.permanent_impact_coefficient < 0.01
