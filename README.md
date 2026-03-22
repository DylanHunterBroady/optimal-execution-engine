# Optimal Execution and Market Impact Simulation Engine

This repo is a Python execution research project for large equity parent orders. It simulates intraday market conditions, models temporary and permanent market impact, and compares different execution approaches under varying volatility, spread, and liquidity regimes.

The main goal is to study the tradeoff between execution cost and execution risk when working large orders over a fixed horizon.

## Research question

How should a large equity parent order be executed when market impact, spread costs, volatility, liquidity constraints, and fill uncertainty all matter at the same time?

## What this repo does

- simulates synthetic intraday equity market paths
- models temporary, permanent, and transient market impact
- approximates passive fills, queue friction, and cleanup costs
- compares TWAP, VWAP, POV, implementation shortfall, Almgren-Chriss, and an adaptive policy
- measures implementation shortfall and related execution metrics
- runs Monte Carlo and frontier analysis across different market regimes

## What it is not

This is not a production trading system, exchange simulator, or full L2/L3 market replay engine. It is a stylized but microstructure-aware execution research framework built to study execution behavior under controlled assumptions.

## Core setup

The engine uses a discrete-time execution framework.

Inventory evolves as:

X_{t+1} = X_t - q_t

with:

X_0 = Q  
X_T = 0

and optional participation constraints of the form:

0 <= q_t <= rho_max * V_t

Midprice evolves as a stochastic process with drift, volatility, and permanent impact:

S_{t+1} = S_t + sigma_t * epsilon_{t+1} + alpha_t + permanent_impact(q_t)

Execution price includes spread, temporary impact, transient impact, queue friction, adverse selection, latency penalty, and passive capture effects.

The main execution objective is to minimize expected cost plus a risk penalty:

min E[cost(q)] + lambda * Risk(cost(q))

## Strategies included

- `twap`
- `vwap`
- `pov`
- `implementation_shortfall`
- `almgren_chriss`
- `adaptive_policy`

All strategies run through the same simulation framework so the results are directly comparable.

## Repo structure

```text
optimal-execution-engine/
├── configs/        # scenario YAMLs
├── examples/       # runnable examples
├── notebooks/      # research notebooks
├── reports/        # methodology, assumptions, findings
├── src/            # package source code
├── tests/          # unit and integration tests
├── README.md
├── pyproject.toml
└── requirements.txt
