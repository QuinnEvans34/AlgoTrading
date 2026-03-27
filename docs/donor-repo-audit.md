# Donor Repo Audit: `forex_signal_scanner`

## Scope
- Donor repo path: `legacy_reference/forex_signal_scanner`
- Pinned commit audited: `bc365a92453b55d7ea34971d96e3af949ea727c7`
- Audit date: `2026-03-24`
- New project context: clean multi-asset platform (stocks + forex), not built on donor structure

## Repo-Wide Architecture Summary
The donor repo is a prototype-style Python trading bot centered on `main.py` with OANDA-only execution. Most core behavior is in one runtime loop with mixed concerns: data fetch, signal generation, risk sizing, order execution, trade lifecycle management, logging, and notifications.

Subsystems exist (`backtest/`, `signal_detection/`, `indicators/`, `data_fetcher/`, `risk/`, `macroeconomics/`, `notifications/`), but orchestration is still monolithic. There is no database layer, no service boundaries, no formal test suite, and secrets are stored directly in `config/config.yaml`.

## Subsystem Audit Matrix

| Category | What Exists | How It Works (High Level) | Forex-Only Constraints | Classification | Why | Suggested Destination in New Repo |
|---|---|---|---|---|---|---|
| Backtesting engine and simulation flow | `backtest/backtest.py`, `run_backtest.py` | Fetches historical candles in chunks, applies signal detector, session/volatility filters, H1 confirmation, ATR SL/TP, close-price-based trade simulation, then summary stats; includes walk-forward and Monte Carlo helpers. | Hard-coded pip math (`0.0001`, `*10000`), EUR/USD-oriented assumptions, OANDA data source dependency. | Reuse with refactor | Good reusable scaffolding for experiment loops and evaluation helpers, but fill model and instrument assumptions are too narrow for multi-asset. | `research/backtesting/engine.py`, `research/backtesting/cost_models.py`, `research/evaluation/walk_forward.py` |
| Live execution / broker integration | `main.py`, `scripts/debug_oanda_check.py`, `test_signal.py` | Async loop fetches account + candles, runs scanner, sizes positions, places OANDA market orders, monitors/adjusts open trade state, sends Telegram updates. | OANDA endpoint contracts, forex units/pips, fixed leverage assumptions, fixed trading-hour assumptions. | Reference only | Useful for behavior requirements, but code is monolithic and tightly coupled; not suitable to transplant directly. | `execution/orchestrator.py`, `execution/order_manager.py`, `execution/brokers/oanda_adapter.py` |
| Signal generation logic | `signal_detection/signal_detector.py`, `scanner/scanner.py` | Rule-based signal generation from RSI z-score, MACD, stochastic, ADX, Bollinger position, and FVG checks; returns `Signal` dataclass. | FVG threshold uses forex pip-scale defaults, thresholds tuned around M1 EUR/USD behavior. | Reuse with refactor | Logic is relatively modular and strategy-like, but thresholds and unit assumptions need instrument-aware configuration. | `strategy_engine/strategies/technical_rule_set.py`, `strategy_engine/contracts/signal.py` |
| Data ingestion / adapters / market data handling | `data_fetcher/data_fetcher.py` | OANDA candles fetcher with retry/backoff and fallbacks (`count` fallback and widened time windows), returns pandas DataFrames. | OANDA-only URLs/instrument format and forex naming assumptions. | Reuse with refactor | Retry/fallback logic is valuable, but provider abstraction is missing and schema normalization should be explicit. | `research/data/providers/base.py`, `research/data/providers/oanda.py`, `research/data/schemas/ohlcv.py` |
| Risk management and position sizing | `risk/risk_model.py`, duplicated sizing logic in `main.py` and `test_signal.py` | Fixed-percent risk sizing with ATR-derived SL/TP and margin checks. | Pip-specific math and forex lot/unit logic; duplicated rules across files. | Reference only | Captures useful intent, but implementation is simplistic, duplicated, and not portfolio- or asset-class-aware. | `strategy_engine/risk/position_sizer.py`, `strategy_engine/risk/limits.py` |
| Model training helpers / ML utilities | No meaningful ML module found | No training pipeline, feature store, model registry, or evaluation harness beyond technical-rule backtesting. | N/A | Discard | Nothing substantive to migrate from this category. | Build fresh under `research/ml/` when needed |
| Performance metrics / analytics / reporting | Metrics in `backtest/backtest.py`, CSV logs in runtime scripts | Computes win rate, avg win/loss, total PnL, simple Sharpe, bootstrap Monte Carlo of PnL/drawdown; runtime logs to CSV/text files. | PnL representation assumes forex pip conversions in parts of stack; reporting is file-based only. | Reuse with refactor | Metric set is a decent starter baseline; output and storage patterns are too ad hoc for the new platform. | `research/analytics/metrics.py`, `research/analytics/bootstrap.py`, `visualization/contracts/performance_views.py` |
| Config / environment / secrets handling | `config/config.yaml` loaded directly from scripts | YAML is loaded directly in multiple entry points; credentials/tokens stored in plaintext. | OANDA/FRED/Telegram settings embedded with forex defaults. | Discard | Security and maintainability risk: committed secrets, no validation layer, no environment profile separation. | `core/config/schema.py`, `.env` + secret provider integration |
| Scheduling / automation / logging / diagnostics | `scripts/start_main.sh`, `scripts/stop_main.sh`, `scripts/start_scheduler.sh`, `scripts/schedule_next_6am.py`, `utils/helpers.py` | Process-control shell scripts and a scheduler launch `main.py`; helper sets rotating log handlers. | Linux tooling (`pgrep`, `pkill`, `nohup`, `python3`) and forex session timing assumptions. | Reference only | Good operational intent, but implementation is environment-specific and not production-grade orchestration. | `ops/jobs/`, `ops/cli/`, `core/logging/setup.py` |
| Database/storage patterns | `trades.csv`, `test_trades.csv`, many `*.log` artifacts | Uses CSV/text files as persistence and diagnostics. No DB, no query model, no schema migration path. | Runtime and report formats are forex-session oriented. | Discard | Not suitable for multi-asset research + paper/live workflows requiring durable, queryable storage. | `storage/research/duckdb_or_parquet.py`, `storage/runtime/postgres.py` |
| Shared utility modules | `utils/helpers.py`, portions of `indicators/indicator_calculator.py` | Logging helper, simple pip conversion helper, and indicator math wrappers. | `convert_to_pips` is explicitly EUR/USD-specific. | Reuse with refactor | Indicator utilities are reusable with minimal cleanup; generic helpers need asset-agnostic unit handling. | `core/logging/`, `research/indicators/`, `market/units.py` |
| Frontend structure and reusable UI | No frontend module found | No web UI/app structure in donor repo. | N/A | Discard | Nothing to migrate for visualization UI. | Build visualization layer fresh in new repo |
| Anything else materially reusable | `macroeconomics/macro_analysis.py`, `notifications/notification_manager.py` | FRED macro pull + Telegram notifier integrations exist as concept modules. | Currency-pair macro mapping and forex workflow assumptions. | Reference only | Integration ideas are useful, but current implementation has coupling/quality issues (see risks below). | `integrations/macro/fred_provider.py`, `integrations/alerts/telegram.py` |

## Strongest Reusable Assets
- `data_fetcher/data_fetcher.py`: robust retry/fallback patterns for external market-data APIs.
- `signal_detection/signal_detector.py`: clear rule-based strategy logic that can seed the new strategy engine.
- `indicators/indicator_calculator.py`: straightforward indicator implementations that can be modularized quickly.
- `backtest/backtest.py` walk-forward and Monte Carlo helpers: useful research workflow primitives.
- Trade lifecycle requirement ideas from `main.py` (`breakeven`, `trailing`, `idle close`, `daily trade limit`), but as design references only.

## Most Dangerous Legacy Assumptions to Avoid Importing
- Secrets committed in repo (`config/config.yaml` contains API keys/tokens/account IDs).
- Forex hard-coding throughout runtime and risk math (`0.0001` pip math, `EUR_USD` defaults).
- Monolithic orchestration in one script (`main.py`) mixing domain logic, I/O, risk, execution, and alerts.
- Async functions using blocking I/O (`requests.post` inside `async def send_telegram`).
- Unsafe fallback behavior (`scanner/scanner.py` attempts `verify=False`; macro call signature mismatch exists).
- Operational scripts assume Linux tools (`pgrep`, `pkill`, `nohup`) and direct process control.
- Logs/artifacts and process files living beside source as first-class workflow.

## Notable Quality Findings
- `scanner/scanner.py` calls `fetch_macro_data(pair, verify=False)`, but `MacroAnalysis.fetch_macro_data` only accepts `pair`; fallback call is invalid and always error-prone.
- `Signal` dataclass has no `macro_data` field, while runtime code logs `getattr(signal, "macro_data", {})`; macro context is not actually propagated through signal objects.
- `scripts/diagnostics/debug_oanda_check.py` is currently a placeholder stub, not a working diagnostic script.
- Core risk logic is duplicated across `main.py` and `test_signal.py`, increasing drift risk.

## Recommended Migration Order (Audit-Driven)
1. Build a provider-agnostic market-data interface and port OANDA fetch logic with strict schema normalization.
2. Extract indicator + signal logic into a strategy-engine module with instrument metadata and parameterized thresholds.
3. Port backtest orchestration primitives (walk-forward/Monte Carlo) into a research layer with a new execution/fill abstraction.
4. Rebuild analytics/reporting outputs on top of structured storage contracts.
5. Re-implement execution as adapter-based broker integrations (paper first, then live), using donor `main.py` only as behavior reference.
6. Introduce secure config/secrets and production-safe ops tooling before live-trading paths.

## Do Not Import These Patterns
- Committed plaintext credentials or token fallbacks in source.
- Hard-coded forex pip conversions in shared logic.
- Single-file runtime orchestrators with mixed responsibilities.
- Blocking network calls inside async paths.
- Provider-specific assumptions in core domain types.
- CSV/log-file persistence as the primary system of record.

## Bottom Line
This donor repo is a useful reference prototype with recoverable strategy/research components, but it is not an architectural base. The best reuse comes from selective extraction of data-fetch, indicator/signal logic, and research evaluation utilities after refactoring into clean multi-asset interfaces.
