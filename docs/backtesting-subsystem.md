# Backtesting Subsystem (Research Simulation Kernel)

## Purpose
The backtesting subsystem is a deterministic, single-asset, bar-based simulation kernel for research workflows. It consumes normalized candles from `market_data` and strategy outputs from `strategy_engine`, then produces structured trade/equity/summary outputs for downstream diagnostics.

## Architecture

### Contracts and assumptions
- `src/backtesting/contracts.py`
- Canonical models:
  - input/config: `BacktestInput`, `BacktestConfig`, `RiskExitConfig`
  - runtime: `SignalEvent`, `Position`, `Trade`
  - outputs: `EquityPoint`, `BacktestSummary`, `BacktestResult`
- Explicit execution assumptions are encoded in enums:
  - `ExecutionTiming` (`NEXT_BAR_OPEN`)
  - `SizingMode` (`FIXED_EQUITY_FRACTION`)
  - `IntrabarExitPolicy` (`ADVERSE_FIRST`)
  - `ExitReason`

### Cost/fill layer
- `src/backtesting/costs.py`
- Strict abstractions: `SpreadModel`, `SlippageModel`, `CommissionModel`, `FillModel`
- Default research models: fixed-bps spread/slippage + fixed/composite commission.

### Execution-rule helpers
- `src/backtesting/execution.py`
- Pure logic helpers:
  - signal direction mapping
  - signal collision handling (ignore vs flip)
  - protective stop/take level calculation
  - intrabar stop-loss / take-profit trigger resolution (including conservative same-bar ambiguity policy)

### Core simulator
- `src/backtesting/engine.py`
- `BacktestSimulator` responsibilities:
  - strategy evaluation on rolling windows
  - next-bar-open signal execution
  - optional stop/take intrabar exits
  - timed exits and end-of-series closure
  - cost-aware fill and PnL accounting
  - trade ledger + drawdown-ready equity curve

### Metrics and scaffolding
- `src/backtesting/metrics.py`: summary metrics (return, drawdown, win rate, profit factor, Sharpe, fee totals)
- `src/backtesting/walk_forward.py`: rolling out-of-sample scaffold (no optimizer yet)
- `src/backtesting/monte_carlo.py`: optional trade-sequence bootstrap robustness helper

## Deterministic Simulation Rules
- Signal observed on bar `t` close.
- Signal-driven entry/flip exits occur at bar `t+1` open.
- Stop-loss/take-profit are evaluated on current bar OHLC after entry.
- If stop and take are both hit in the same bar, adverse outcome is chosen first (`ADVERSE_FIRST`).
- Gap-through stop/take fills at bar open, then fill model friction is applied.
- Single-position model: no portfolio or multi-position orchestration in this phase.

## Donor Concepts Reused vs Removed

### Reused conceptually
- Evaluation loop and experiment framing from donor backtesting
- Walk-forward scaffolding concept
- Monte Carlo trade-sequence robustness concept
- Summary-reporting mindset

### Intentionally not reused
- Forex-specific pip assumptions
- Provider/broker coupling (including OANDA assumptions)
- Donor monolithic structure
- Live execution runtime concerns
- CSV/log persistence patterns

## Integration Points
- Input candles: `market_data.contracts.Candle`
- Strategy output: `strategy_engine.Strategy.evaluate(...)`
- Output artifact: `BacktestResult` for later diagnostics/visualization layers

## Minimal Demo
- `examples/backtest_demo.py`
- Demonstrates normalized candles -> strategy -> simulator -> structured summary and trade output.
