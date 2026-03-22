"""Execution strategy implementations."""

from execution_engine.strategies.adaptive_policy import AdaptivePolicyStrategy
from execution_engine.strategies.almgren_chriss import AlmgrenChrissStrategy
from execution_engine.strategies.base_strategy import BaseStrategy
from execution_engine.strategies.implementation_shortfall import ImplementationShortfallStrategy
from execution_engine.strategies.pov import POVStrategy
from execution_engine.strategies.twap import TWAPStrategy
from execution_engine.strategies.vwap import VWAPStrategy

STRATEGY_REGISTRY = {
    "twap": TWAPStrategy,
    "vwap": VWAPStrategy,
    "pov": POVStrategy,
    "implementation_shortfall": ImplementationShortfallStrategy,
    "almgren_chriss": AlmgrenChrissStrategy,
    "adaptive_policy": AdaptivePolicyStrategy,
}


def build_strategy(name: str, *args: object, **kwargs: object) -> BaseStrategy:
    """Instantiate a strategy by name."""
    try:
        strategy_cls = STRATEGY_REGISTRY[name]
    except KeyError as exc:
        raise ValueError(f"Unknown strategy: {name}") from exc
    return strategy_cls(*args, **kwargs)


__all__ = [
    "AdaptivePolicyStrategy",
    "AlmgrenChrissStrategy",
    "BaseStrategy",
    "ImplementationShortfallStrategy",
    "POVStrategy",
    "STRATEGY_REGISTRY",
    "TWAPStrategy",
    "VWAPStrategy",
    "build_strategy",
]
