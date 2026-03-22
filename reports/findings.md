# Findings

This file is intentionally structured as a reporting template for empirical results generated from the notebooks, CLI, and Monte Carlo workflows in this repository.

## Executive summary

Use this section for 3-5 headline observations once experiments are run.

Suggested prompts:

- Which strategy minimized mean implementation shortfall in the base regime?
- Which strategy minimized tail cost?
- Which strategy was most sensitive to spread widening?
- How did the frontier move as risk aversion changed?

## Base scenario results

Document:

- config file used
- seed or Monte Carlo path count
- ranking by mean implementation shortfall
- ranking by cost volatility
- completion behavior

Suggested table:

| Strategy | Mean IS | Std IS | P95 IS | Completion | Avg participation |
|---|---:|---:|---:|---:|---:|
| TWAP | TODO | TODO | TODO | TODO | TODO |
| VWAP | TODO | TODO | TODO | TODO | TODO |
| POV | TODO | TODO | TODO | TODO | TODO |
| Implementation Shortfall | TODO | TODO | TODO | TODO | TODO |
| Almgren-Chriss | TODO | TODO | TODO | TODO | TODO |
| Adaptive | TODO | TODO | TODO | TODO | TODO |

## Regime comparison

Summarize behavior across:

- low vol / high liquidity
- high vol / low liquidity
- event day
- trending market
- mean-reverting market

Suggested discussion questions:

- Which strategies degrade most under high spreads and thin depth?
- Does urgency help or hurt on event days?
- Does trending drift favor front-loaded or volume-following schedules?

## Sensitivity analysis

Record how rankings changed with:

- order size as % ADV
- annualized volatility
- spread regime
- impact exponent
- participation cap
- time horizon

Suggested narrative:

> As order size rises relative to ADV, schedule quality becomes increasingly constrained by participation and residual cleanup risk. In this regime, strategies that rely on patient passive fills may lose relative performance if they accumulate a meaningful fill deficit.

## Frontier analysis

Capture:

- risk-aversion grid
- expected-cost / risk points
- schedule participation levels
- qualitative shape of the frontier

Suggested prompts:

- At what `lambda` does the schedule become materially front-loaded?
- Does the frontier flatten or remain steep over the chosen grid?
- Is the deterministic frontier consistent with Monte Carlo realized rankings?

## Cost decomposition

Recommended breakdown to report:

- market drift
- permanent impact
- spread paid
- spread capture
- temporary impact
- transient impact
- queue penalty
- adverse selection
- latency penalty
- residual liquidation

## Robustness checks

Examples:

- rerun with different seeds
- compare linear vs square-root temporary impact
- tighten and relax participation caps
- vary passive fill probability and queue penalty
- stress jump probability and event-day spread widening

## Caveats

Every findings section should restate the scope:

- synthetic market generation
- stylized passive fills
- no historical L2/L3 calibration
- no venue routing
- no claim of production realism

## Example starter note

Illustrative single-path result from the current base configuration:

> On one shared synthetic path (`configs/base.yaml`, seed `11`), `POV` produced the lowest implementation shortfall among the implemented strategies, while all strategies completed the order after residual cleanup logic. This is not a robust conclusion until Monte Carlo analysis is used to separate path luck from structural behavior.
