# Assumptions

This document lists the main simplifying assumptions in the current framework and what would be required to relax them with richer market data.

## Core simplifying assumptions

### 1. Synthetic market data

Assumption:

- Intraday price, volume, spread, and liquidity are generated synthetically from stylized processes.

Why it matters:

- This supports controlled experiments and clean reproducibility.
- It does not capture stock-specific seasonality, auction mechanics, fragmented liquidity, or corporate-event structure.

What is needed for greater realism:

- historical TAQ or venue-level data
- stock-specific intraday volume curves
- empirical spread and depth calibration
- event-conditioned parameter estimation

### 2. Top-of-book approximation

Assumption:

- The engine models a stylized touch depth and passive fill probability rather than a full depth ladder.

Why it matters:

- True queue position, book resiliency, and depth consumption depend on deeper levels and venue microstructure.

What is needed for greater realism:

- L2 snapshots or order-book reconstruction
- queue priority estimates
- level-by-level refill dynamics
- venue-specific fee/rebate schedules

### 3. Simplified passive fills

Assumption:

- Passive fills are probabilistic and summarized by a fill-rate model.

Why it matters:

- Real passive fills depend on queue rank, cancellations ahead, opposing market orders, hidden size, and venue routing choices.

What is needed for greater realism:

- L3 order event feeds
- queue-position tracking
- cancellation and modification event modeling
- per-venue passive execution simulation

### 4. Simple impact forms

Assumption:

- Temporary impact is linear or square-root in participation.
- Permanent impact is linear in order fraction of ADV.
- Transient impact uses exponential decay.

Why it matters:

- Real impact depends on liquidity state, information content, volatility regime, venue mix, and order slicing logic.

What is needed for greater realism:

- calibration on historical parent/child execution data
- stock- and regime-specific impact surfaces
- interaction terms between spread, depth, and impact
- transient-impact estimation from post-trade recovery paths

### 5. Single-asset execution

Assumption:

- Only one equity order is executed at a time.

Why it matters:

- Real portfolios may optimize execution jointly across correlated names, baskets, or cross-venue liquidity pools.

What is needed for greater realism:

- multi-asset inventory and covariance model
- basket-level liquidity constraints
- cross-impact estimation

### 6. Deterministic schedule optimizer

Assumption:

- The Almgren-Chriss style optimizer uses the expected market path, not a full stochastic dynamic program.

Why it matters:

- A deterministic plan is transparent and interview-friendly, but it cannot fully anticipate path-dependent fill surprises or state transitions.

What is needed for greater realism:

- dynamic programming or model predictive control
- scenario-tree or stochastic optimization
- policy optimization over observable state variables

### 7. Residual liquidation simplification

Assumption:

- Unfilled residual inventory is force-cleaned at the close with an explicit penalty.

Why it matters:

- Real execution desks may roll inventory, switch venues, alter urgency, or hand off residuals to closing-auction logic.

What is needed for greater realism:

- explicit closing-auction model
- rolling residual decision rules
- after-hours or next-session carry logic

## What L2/L3 data would enable

With L2/L3 data, the engine could be extended to:

- reconstruct queue rank for passive orders
- simulate priority loss from cancellations/replacements
- model depth depletion and refill level by level
- estimate adverse selection from post-fill price response
- calibrate spread capture versus information leakage more realistically
- compare routing choices across venues and order types
- fit resilience and impact parameters from empirical recovery patterns

## What this framework is best used for today

The current framework is best suited for:

- execution research prototypes
- strategy comparison under controlled assumptions
- interview or recruiting portfolios for quant execution roles
- teaching / explaining microstructure-aware scheduling trade-offs
- building a bridge from stylized theory to richer historical calibration

It should not be used as a production trading engine or as evidence of live execution performance without substantial empirical extension.
