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
```

with optional participation constraints:

```text
0 <= q_t <= rho_max * V_t
```

Midprice evolves as a stochastic process with drift, volatility, and permanent impact:

```text
S_{t+1} = S_t + sigma_t * epsilon_{t+1} + alpha_t + permanent_impact(q_t)
```

Execution price includes spread, temporary impact, transient impact, queue friction, adverse selection, latency penalty, and passive capture effects.

The main objective is to minimize expected execution cost plus a risk penalty:

```text
min_q E[cost(q)] + lambda * Risk(cost(q))
```

The deterministic optimizer uses an Almgren-Chriss style schedule with temporary impact, permanent impact, spread cost, smoothness penalties, participation penalties, and volatility-linked inventory risk.

## Strategies included

- `twap`
- `vwap`
- `pov`
- `implementation_shortfall`
- `almgren_chriss`
- `adaptive_policy`

All strategies run through the same simulator so the outputs are directly comparable.

## Repo structure

```text
optimal-execution-engine/
├── configs/                    # scenario YAMLs
├── examples/                   # runnable example scripts
├── notebooks/                  # research notebooks
├── reports/                    # methodology, assumptions, findings
├── src/
│   └── execution_engine/
│       ├── market/             # price, spread, volume, liquidity regimes
│       ├── impact/             # linear, square-root, permanent, transient impact
│       ├── book/               # stylized top-of-book and fill logic
│       ├── strategies/         # execution policies
│       ├── cost/               # benchmarks and cost decomposition
│       ├── optimization/       # deterministic and stochastic frontier tools
│       ├── simulation/         # simulator, suite runner, Monte Carlo
│       ├── analytics/          # sensitivity and stress-test analysis
│       ├── visualization/      # matplotlib plots
│       ├── config.py
│       ├── example_runner.py
│       └── __main__.py
├── tests/
├── README.md
├── pyproject.toml
└── requirements.txt
```

## Market and execution model

### Market simulation

- intraday price path generation with stochastic volatility, drift regimes, and jump risk
- U-shaped expected volume curve with realized-volume noise
- dynamic spread widening under volatility, event, and liquidity stress
- liquidity regimes including low-vol/high-liquidity, high-vol/low-liquidity, event day, and trending market

### Impact layer

- linear temporary impact
- square-root temporary impact
- linear permanent impact
- transient impact with resilience decay

### Book and fill layer

- stylized touch depth and refill process
- marketable versus passive child-order split
- passive fill uncertainty driven by queue load, cancellations, and liquidity state
- adverse selection and latency penalties
- explicit residual cleanup handling

### Strategy layer

- TWAP
- VWAP
- POV
- implementation shortfall
- Almgren-Chriss
- adaptive policy

## Main entry points

Library API:

- `execution_engine.load_config(...)`
- `execution_engine.ExecutionSimulator`
- `execution_engine.run_strategy_suite(...)`
- `execution_engine.run_monte_carlo(...)`
- `execution_engine.optimization.generate_efficient_frontier(...)`
- `execution_engine.optimization.stochastic_solver.evaluate_almgren_chriss_stochastic_frontier(...)`
- `execution_engine.example_runner.run_end_to_end_example(...)`

CLI:

- `optimal-execution`
- `optimal-execution-example`

Example script:

- `examples/run_end_to_end_example.py`

## Installation

Install dependencies:

```bash
python3 -m pip install -r requirements.txt
python3 -m pip install --no-build-isolation -e .
```

Or run directly from source:

```bash
python3 -m pip install -r requirements.txt
PYTHONPATH=src python3 -m pytest
```

## Commands

Run a single strategy:

```bash
optimal-execution --config configs/base.yaml --mode single --strategy almgren_chriss --seed 11
```

Run the full strategy suite on a shared market path:

```bash
optimal-execution --config configs/base.yaml --mode suite --seed 11
```

Run Monte Carlo comparison:

```bash
optimal-execution --config configs/base.yaml --mode monte_carlo --paths 100
```

Run deterministic frontier analysis:

```bash
optimal-execution --config configs/base.yaml --mode frontier --seed 19
```

Run stochastic frontier analysis for the Almgren-Chriss risk-aversion grid:

```bash
optimal-execution --config configs/base.yaml --mode stochastic_frontier --paths 25
```

Run the full example workflow and save figures plus CSV outputs:

```bash
optimal-execution --config configs/base.yaml --mode example --output-dir artifacts/base_case --paths 25
```

Or directly:

```bash
PYTHONPATH=src python3 examples/run_end_to_end_example.py --config configs/base.yaml --output-dir artifacts/base_case --paths 25
```

Run tests:

```bash
PYTHONPATH=src python3 -m pytest
```

## Example workflow

A typical run does the following:

1. loads a YAML scenario config
2. simulates one market path
3. runs all configured strategies through the same simulator
4. computes suite summaries, diagnostics, and Monte Carlo comparison tables
5. generates frontier outputs
6. saves strategy comparison, schedule, inventory, cost-breakdown, and frontier plots

Saved artifacts include:

- `strategy_suite_summary.csv`
- `monte_carlo_summary.csv`
- `efficient_frontier.csv`
- `best_strategy_execution.csv`
- `best_strategy_diagnostics.csv`
- `strategy_comparison.png`
- `best_strategy_schedule.png`
- `best_strategy_cost_breakdown.png`
- `efficient_frontier.png`
- `best_strategy_inventory.png`

## Configurations

Included scenario configs:

- `configs/base.yaml`
- `configs/low_vol_high_liquidity.yaml`
- `configs/high_vol_low_liquidity.yaml`
- `configs/event_day.yaml`
- `configs/trending_market.yaml`

The config schema validates:

- order timing and side
- benchmark selection
- impact model selection
- strategy names
- Monte Carlo and risk-aversion settings

## Notebooks

- `notebooks/01_market_impact_model_exploration.ipynb` — impact scaling and calibration
- `notebooks/02_execution_strategy_comparison.ipynb` — cross-strategy comparison on a shared path
- `notebooks/03_sensitivity_analysis.ipynb` — sensitivity to volatility, spread, ADV, and order size
- `notebooks/04_frontier_visualization.ipynb` — Almgren-Chriss frontier and risk-aversion tradeoff

The notebooks reuse the package API rather than carrying separate notebook-only logic.

## Outputs

Typical outputs include:

- execution schedules by time bucket
- implementation shortfall and slippage metrics
- cost decomposition across spread, impact, and cleanup
- Monte Carlo strategy comparison tables
- efficient frontier analysis across risk aversion levels
- saved plots for schedules, inventories, cost breakdown, and frontier results

## Why I built it

I wanted a structured way to study how large equity orders should be worked under different market conditions. A lot of execution discussion stays qualitative. This project turns those tradeoffs into something you can simulate, compare, and stress test.

## Limits

The repo uses synthetic market data and a stylized fill model. It is meant for execution research, not for claiming full market realism. More realistic extensions would require historical intraday calibration, deeper order book data, and venue-specific routing assumptions.

## Possible extensions

- multi-venue routing
- dark pool execution logic
- cross-impact for baskets
- queue-reactive order book models
- reinforcement learning execution policies
- calibration against historical intraday data
