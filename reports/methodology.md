# Methodology

## Scope

The engine studies single-asset execution for a large equity parent order over a finite intraday horizon. The framework is synthetic and stylized, but aims to preserve the main execution trade-offs that matter in practice:

- impact versus urgency
- spread cost versus passive fill uncertainty
- participation control versus completion risk
- expected cost versus volatility-linked inventory risk

## Price process

The market layer produces a synthetic intraday path with:

- an initial reference midprice
- bucket-level return volatility
- optional drift regime
- jump risk
- liquidity and depth multipliers
- dynamic spread
- realized market volume

The base midprice evolves bucket by bucket as:

```text
S_{t+1}^{base} = S_t^{base} (1 + alpha_t + sigma_t * epsilon_t + jump_t + mean_reversion_t)
```

where:

- `alpha_t` is regime drift
- `sigma_t` is bucket volatility
- `epsilon_t` is a Gaussian innovation
- `jump_t` is an event jump when triggered
- `mean_reversion_t` is optional pull toward the opening price

Execution-generated permanent impact is added separately inside the simulator so the same fundamental market path can be shared across strategies.

## Intraday volume and spread

Volume is modeled using a normalized U-shaped profile, optionally modified for event days or front-loaded/back-loaded conditions. Realized volume is the product of:

- ADV scaled by the execution-window fraction
- expected bucket weight
- liquidity regime multiplier
- multiplicative noise

Spread is dynamic rather than constant. The spread widens when:

- volatility rises
- liquidity deteriorates
- an event indicator is active

This keeps spread-sensitive strategies, especially `POV` and the adaptive policy, from behaving unrealistically in stressed buckets.

## Impact forms

### Temporary impact

Two temporary impact variants are implemented:

1. Linear impact:

```text
temp(q_t) = price_t * eta * (q_t / V_t)
```

2. Square-root impact:

```text
temp(q_t) = price_t * eta * (q_t / V_t)^delta
```

with `delta` typically near `0.5`.

### Permanent impact

Permanent impact is linear in order fraction of ADV:

```text
perm(q_t) = price_t * gamma * (q_t / ADV)
```

The simulator applies permanent impact as a persistent signed shift to future midprices seen by the strategy.

### Transient impact

Transient impact models residual footprint that decays over time:

```text
state_{t+1} = exp(-kappa) * state_t + c * (q_t / V_t)^delta
```

The execution price pays the decayed residual plus half of the current increment. This creates a resilience mechanism without pretending to simulate a full LOB recovery process.

## Fill model

Child orders are split into:

- marketable quantity
- passive quantity

The passive component is subject to:

- a fill-probability baseline
- queue-position decay
- cancellation-rate adjustment
- liquidity multiplier
- random noise

Aggressive flow pays more spread and latency cost. Passive flow can capture spread, but is exposed to adverse selection and incomplete fills.

## Execution objective

The economic reporting benchmark is implementation shortfall versus arrival price.

The deterministic optimizer minimizes:

```text
Expected cost
+ risk_aversion * inventory_risk
+ participation penalties
+ smoothness penalties
+ completion penalty
```

where inventory risk is proportional to bucket volatility and remaining inventory squared.

## Strategy design

### TWAP

Equal bucket sizing over remaining time, subject to participation and minimum-child constraints.

### VWAP

Tracks expected market volume and adds catch-up behavior when behind schedule.

### POV

Trades a constant fraction of realized market volume, slowing when spread widens.

### Implementation Shortfall

Uses a front-loaded exponential weight profile controlled by urgency.

### Almgren-Chriss

Uses the deterministic optimizer over the expected volume and volatility path.

### Adaptive Policy

Blends schedule following with reactive changes driven by:

- fill deficit
- recent slippage
- spread widening
- realized volatility
- remaining inventory

## Regime design

Built-in regimes include:

- low vol / high liquidity
- high vol / low liquidity
- event day
- trending market
- mean-reverting market
- neutral base case

Regimes alter some combination of:

- volatility level
- depth and liquidity multipliers
- spread state
- event indicator
- drift behavior

## Cost decomposition

The execution log explicitly tracks:

- market drift
- permanent impact carried into later fills
- spread paid
- spread capture
- temporary impact
- transient impact
- queue penalty
- adverse selection
- latency penalty
- residual liquidation cost

The tests verify that the decomposition reconciles to total implementation shortfall up to numerical tolerance.

## Limitations

- No exchange-specific matching logic
- No hidden liquidity or dark routing
- No explicit order-cancellation policy optimization
- No queue-priority dynamics from real L2/L3 feeds
- No multi-asset cross-impact
- Synthetic calibration only unless extended with historical data

These limits are intentional: the framework aims for research clarity and extensibility, not over-claimed realism.
