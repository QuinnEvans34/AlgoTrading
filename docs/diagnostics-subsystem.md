# Diagnostics Subsystem (Performance Analytics Layer)

## Purpose
The diagnostics subsystem computes structured performance analytics from backtesting outputs. It is backend-first, deterministic, and designed to feed later visualization and run-comparison workflows.

## Architecture
- `src/diagnostics/contracts.py`
  - Canonical typed models for diagnostics input, configuration, KPI sections, drawdown episodes, chart-ready series, and final report output.
- `src/diagnostics/adapters.py`
  - Adapter from `backtesting.BacktestResult` into diagnostics-native contracts.
  - Isolates diagnostics logic from simulator implementation details.
- `src/diagnostics/performance.py`
  - Run-level return/PnL and annualization logic.
- `src/diagnostics/trade_analysis.py`
  - Trade distributions, expectancy, side breakdowns, streaks, and top winners/losers.
- `src/diagnostics/risk.py`
  - Return-series risk metrics, drawdown series, and drawdown-episode extraction.
- `src/diagnostics/report.py`
  - Orchestrates full report generation from input contracts.

## Integration Boundary
- Diagnostics consumes structured results only.
- Primary integration path:
  - `build_report_from_backtest(backtest_result, ...)`
  - `BacktestResult -> DiagnosticsInput -> DiagnosticsReport`
- No dependency on providers, brokers, live execution, CSV parsing, or log scraping.

## Metrics Included In This Phase
- Performance:
  - final equity, gross/net PnL, total commissions, total return %, annualized return % (guarded), exposure proxy.
- Trade analytics:
  - trade count, win/loss/flat counts, win rate, expectancy, average/median outcomes, largest win/loss, profit factor, payoff ratio, average/median duration, streaks, long/short splits.
- Risk analytics:
  - max drawdown %, max drawdown duration (bars), volatility %, downside volatility %, Sharpe, Sortino, Calmar.
- Series artifacts:
  - equity, return series, drawdown series, trade-return and trade-PnL arrays for charting.
- Drawdown episodes:
  - peak/trough/recovery timestamps, depth %, duration, recovery bars.

## Explicit Assumptions
- Return basis: arithmetic bar-over-bar returns from equity points.
- Annualization: interval-specific bars/year map with minimum sample guards.
  - Default guard requires at least ~1 month of bars (`min_years_for_annualization = 1/12`).
- Risk-free handling: annual rate converted to per-bar rate for Sharpe/Sortino.
- Cost handling: commissions explicit; spread/slippage embedded implicitly in net trade outcomes.
- Zero-trade runs: counts remain valid, but trade-quality metrics return `None`.
- Sparse samples: unstable risk/annualization outputs return `None`.
- Drawdown is recomputed from equity series for consistency.

## Conceptual Reuse From Donor
Reused conceptually:
- summary reporting mindset
- drawdown/risk framing
- robustness-oriented metric checks

Intentionally not reused:
- monolithic orchestration
- forex/pip assumptions
- CSV/log-report patterns
- provider-specific coupling

## Deferred To Later Phases
- Benchmark-relative metrics (alpha/beta/information ratio)
- VaR/CVaR and regime attribution
- portfolio-level diagnostics
- experiment tracking and persistent comparison store
- explicit spread/slippage attribution fields (requires richer execution telemetry)
