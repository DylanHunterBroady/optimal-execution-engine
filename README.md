****# Optimal Execution and Market Impact Simulation Engine

Optimal execution and market impact simulator for large equity parent orders. The repo is built as an execution research environment: discrete-time microstructure-aware market simulation, configurable impact and fill models, cross-strategy comparison, implementation-shortfall analytics, and deterministic/stochastic frontier analysis.

## Research question

How should a large equity parent order be executed over a finite horizon when temporary impact, permanent impact, spread costs, vol risk, liquidity constraints, and fill uncertainty are jointly considered?

## Key Research Questions

How does the optimal execution schedule shift as vol risk and risk aversion increase?
When do passive fill uncertainty and queue frictions offset the apparent benefit of spread capture?
How sensitive are strategy rankings to order size as a fraction of ADV, spread regime, and liquidity state?
Under what assumptions does a deterministic Almgren-Chriss schedule remain competitive against simpler participation-based policies?
How much of realized implementation shortfall is attributable to market drift, spread, impact, and cleanup costs?

## What this repo is

A discrete-time execution research framework for synthetic intraday equity markets.
A common simulation runner for TWAP, VWAP, POV, urgency-based implementation shortfall, Almgren-Chriss, and an adaptive policy.
A cost and benchmark layer centered on implementation shortfall, with explicit decomposition into market drift, spread, impact, queue friction, and adverse selection.
A deterministic and stochastic optimization environment for risk-aversion sweeps and frontier analysis.
A research workflow that runs from YAML scenario config to simulation outputs, analytics tables, and saved plot artifacts.

## What this repository is not

Not a claim of L2/L3 realism.
Not an exchange simulator or smart order router.
Not a production trading stack.
Not a source of historical alpha.

## Math

Inventory dynamics:

X_{t+1} = X_t - q_t
X_0 = Q
X_T = 0

Participation-style constraint:

0 <= q_t <= rho_max * V_t

Midprice dynamics:

S_{t+1} = S_t + sigma_t * epsilon_{t+1} + alpha_t + permanent_impact(q_t)

Execution price:

P_exec,t = S_t
         + side * [half_spread
                   + temporary_impact(q_t, V_t, L_t)
                   + transient_impact_t
                   + queue_penalty
                   + adverse_selection
                   + latency_penalty
                   - passive_capture]


Execution objective: min_q E[cost(q)] + lambda * Risk(cost(q))

The deterministic optimizer implements a constrained Almgren-Chriss style schedule with temporary impact, permanent impact, spread cost, smoothness penalties, participation penalties, and volatility-linked inventory risk.

## Architecture

optimal-execution-engine/
configs/                       Scenario YAMLs
examples/                      Runnable example
notebooks/                     Research notebooks
reports/                       Methodology / assumptions / findings
src/execution_engine/

  market/                    Intraday price, spread, volume, liquidity regimes
  impact/                    Linear, square-root, permanent, transient impact
  book/                      Stylized top-of-book and fill logic
  strategies/                Execution policies on a shared interface
  cost/                      Benchmarks and cost decomposition
  optimization/              Deterministic and stochastic frontier tools
  simulation/                Common simulator, suite runner, Monte Carlo
  analytics/                 Sensitivity and stress-test analysis
  visualization/             matplotlib plots
  config.py                  Typed dataclass config schema and validation
  example_runner.py          Full config > simulation > analytics > plots workflow
    __main__.py                CLI entry point
  tests/                         Economic and integration tests

## Market and execution model

### Market simulation

Intraday price path generation with stochastic volatility, drift regimes, and jump risk.
U-shaped expected volume curve with realized-volume noise.
Dynamic spread widening under volatility, event, and liquidity stress.
Liquidity regimes including low-vol/high-liquidity, high-vol/low-liquidity, event day, and trending market.

### Impact layer

Linear temporary impact.
Square-root temporary impact.
Linear permanent impact.
Transient impact with resilience decay.

### Book and fill layer

Stylized touch depth and refill process.
Marketable versus passive child-order split.
Passive fill uncertainty driven by queue load, cancellations, and liquidity state.
Adverse selection and latency penalties.
Explicit residual cleanup handling.

### Strategy layer

`twap`
`vwap`
`pov`
`implementation_shortfall`
`almgren_chriss`
`adaptive_policy`

All strategies run through the same `ExecutionSimulator` and the same `run_strategy_suite(...)` multi-strategy runner.

## Main entry points

Library API:

`execution_engine.load_config(...)`
`execution_engine.ExecutionSimulator`
`execution_engine.run_strategy_suite(...)`
`execution_engine.run_monte_carlo(...)`
`execution_engine.optimization.generate_efficient_frontier(...)`
`execution_engine.optimization.stochastic_solver.evaluate_almgren_chriss_stochastic_frontier(...)`
`execution_engine.example_runner.run_end_to_end_example(...)`

CLI:

`optimal-execution`
`optimal-execution-example`

Example script:

`examples/run_end_to_end_example.py`

## Installation

Editable install with development tools:

```bash
python3 -m pip install -r requirements.txt
python3 -m pip install --no-build-isolation -e .
```

Or use the package directly from source:

```bash
python3 -m pip install -r requirements.txt
PYTHONPATH=src python3 -m pytest
```

## Commands to run

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

## Example end-to-end workflow

The example runner performs a real workflow:

1. Load a YAML scenario config.
2. Simulate one market path.
3. Run all configured strategies through the common simulator.
4. Compute suite summaries, diagnostics, and Monte Carlo comparison tables.
5. Generate efficient-frontier outputs.
6. Save strategy comparison, schedule, inventory, cost-breakdown, and frontier plots.

Saved artifacts include:

`strategy_suite_summary.csv`
`monte_carlo_summary.csv`
`efficient_frontier.csv`
`best_strategy_execution.csv`
`best_strategy_diagnostics.csv`
`strategy_comparison.png`
`best_strategy_schedule.png`
`best_strategy_cost_breakdown.png`
`efficient_frontier.png`
`best_strategy_inventory.png`

## Configurations

Included scenario configs:

`configs/base.yaml`
`configs/low_vol_high_liquidity.yaml`
`configs/high_vol_low_liquidity.yaml`
`configs/event_day.yaml`
`configs/trending_market.yaml`

The config schema validates:

order timing and side
benchmark selection
impact model selection
strategy names
Monte Carlo and risk-aversion settings

All shipped configs are covered by integration tests.

## Notebooks

`notebooks/01_market_impact_model_exploration.ipynb` — market impact scaling and calibration
`notebooks/02_execution_strategy_comparison.ipynb` — cross strat comparison on a shared path
`notebooks/03_sensitivity_analysis.ipynb` — sensitivity to vol, spread, ADV, and order size
`notebooks/04_frontier_visualization.ipynb` — Almgren-Chriss frontier and risk-aversion trade-off

These notebooks reuse the package API rather than carrying notebook-only logic.

## Testing

The test suite checks actual execution logic rather than import smoke tests:

inventory conservation
simulation reproducibility
impact-model monotonicity
common-runner coverage across all configs and strategies
benchmark sign consistency for buy and sell logic
cost-decomposition reconciliation
optimizer completion and participation constraints
risk-aversion front-loading behavior
stochastic frontier coverage
artifact generation

Current local verification:
32 passed in 4.26s

## Sample observations from the current engine

Illustrative single-path suite output from `configs/base.yaml`:

all six strategies complete the order under the default cleanup rule
strategy rankings differ materially across seeds and regimes
deterministic Almgren-Chriss frontier outputs are monotone in risk aversion
execution-cost decomposition reconciles back to implementation shortfall

The project is built so those claims are reproducible from code, not just described in prose.

## Modeling Assumptions and Limitations

Synthetic market data only; no historical TAQ calibration in the current repo.
Stylized touch-depth and passive-fill logic rather than full L2/L3 book replay.
Permanent impact is linear and stylized.
Temporary impact is linear or square-root in participation.
Residual cleanup is implemented as a market-style close-out rule in shipped configs.
Single-asset execution only.
No venue-routing logic, auction model, hidden-liquidity model, or maker/taker economics.

See:

[`reports/methodology.md`](reports/methodology.md)
[`reports/assumptions.md`](reports/assumptions.md)
[`reports/findings.md`](reports/findings.md)

## Potential Extensions

historical calibration against intraday data
multi-venue routing with venue-specific spread, fee, and queue assumptions
dark pool execution and midpoint-cross logic
stochastic control / MPC execution policies
multi-asset and basket execution
cross-impact for baskets and correlated execution programs
queue-reactive order book models with state-dependent refill and cancellation
reinforcement learning execution policies trained on the simulator state space
explicit closing-auction modeling
empirical resilience and impact-surface calibration

## Bottom line

This repo is intended to be a serious execution research environment: one simulator, one strategy interface, explicit market-impact assumptions, reproducible scenario analysis, consistent metrics, and engineering discipline
****
