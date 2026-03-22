# Optimal Execution and Market Impact Simulation Engine

This repo is a Python research project for studying how large equity orders should be executed under different market conditions. It simulates intraday price, volume, spread, and liquidity dynamics, applies temporary and permanent market impact, and compares several execution strategies under a common framework.

The goal is to study the tradeoff between execution cost and execution risk when working a large parent order over a fixed horizon.

## Research question

How should a large equity parent order be executed when market impact, spread costs, volatility, liquidity constraints, and fill uncertainty all matter at the same time?

## What this repo does

- simulates synthetic intraday equity market paths
- models temporary, permanent, and transient market impact
- approximates passive fills, queue friction, and cleanup costs
- compares TWAP, VWAP, POV, implementation shortfall, Almgren-Chriss, and an adaptive policy
- measures implementation shortfall and related execution metrics
- runs Monte Carlo analysis, sensitivity studies, and frontier analysis across different market regimes

## What it is not

This is not a production trading system, exchange simulator, or full L2/L3 market replay engine. It is a stylized but microstructure-aware execution research framework built to study execution behavior under controlled assumptions.

## Key questions

- How does the execution schedule change as volatility and risk aversion increase?
- When do passive fill uncertainty and queue frictions offset the benefit of spread capture?
- How sensitive are strategy rankings to order size as a fraction of ADV, spread regime, and liquidity state?
- When does a deterministic Almgren-Chriss schedule outperform simpler participation-based policies?
- How much of realized implementation shortfall comes from drift, spread, impact, and cleanup costs?

## Core setup

The engine uses a discrete-time execution framework.

Inventory evolves as:

```text
X_{t+1} = X_t - q_t
X_0 = Q
X_T = 0
