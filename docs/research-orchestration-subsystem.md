# Research Orchestration Subsystem (Experiment Runner)

## Purpose
The research subsystem coordinates existing backend layers into reproducible research runs from one typed request.
It does not reimplement strategy, backtesting, diagnostics, ML dataset, or modeling logic.

## Architecture
- `src/research/contracts.py`
  - Workflow contracts, candle source contracts, branch specs, run config, and step status contracts.
- `src/research/config.py`
  - Run ID generation, default run config resolution, and summary output-path resolution.
- `src/research/validation.py`
  - Request validation for workflow compatibility, supported strategy IDs, and ML target/task compatibility.
- `src/research/workflows.py`
  - Pure composition helpers that call existing subsystem APIs.
- `src/research/artifacts.py`
  - Structured run outputs, branch summaries, and summary serialization shape.
- `src/research/runner.py`
  - `ResearchRunner` orchestration entrypoint with step-level status tracking and optional summary persistence.
- `src/research/storage.py`
  - Local artifact storage helpers for `manifest.json` + `index.json` persistence and rebuild behavior.
- `src/research/history.py`
  - History list/read services over persisted artifacts with filtering/sorting/pagination support.
- `src/research/compare.py`
  - Strategy/ML compare assembly and compatibility validation for selected run IDs.

## Workflow Types (Current Phase)
- `strategy_research`
  - candles -> strategy backtest -> diagnostics report
- `ml_research`
  - candles -> ML dataset build -> model training/evaluation
- `hybrid_research`
  - executes both branches over the same candle set and packages both outputs

Hybrid in this phase is packaging only. It does not feed model predictions into strategy execution.

## Candle Source Modes
- `inline_candles`
  - deterministic tests/demos and local offline research
- `market_data_fetch`
  - provider + historical range fetch through injected `MarketDataService`

The orchestration layer stays provider-agnostic and broker-agnostic.

## Failure Semantics
- Default policy: fail-fast (`strict_failures=True`)
  - first failed step ends run with `RunStatus.FAILED`.
- Non-strict mode (`strict_failures=False`)
  - failed steps are captured in timeline and safe downstream steps continue.
  - final status is `PARTIAL_FAILURE` when at least one branch still succeeds.

Each step records:
- status (`success|failed|skipped`)
- start/end timestamps
- duration
- optional error type/message

## Reproducibility Metadata
Run artifact metadata includes:
- run ID / run name
- random seed used for downstream modeling config
- candle source details
- strict-failure policy
- optional persisted summary path

Branch artifacts preserve subsystem-native metadata:
- strategy branch includes full `BacktestResult` and `DiagnosticsReport`
- ML branch includes `MLDatasetArtifact` and `TrainingRunArtifact`

## Persistence
Summary persistence is optional (`persist_summary` in run config).
When enabled, the runner writes:
- `<output_dir>/<run_id>/summary.json`
- `<output_dir>/<run_id>/detail.json`
- `<output_dir>/<run_id>/manifest.json`
- `<output_dir>/index.json`

Default output directory when persistence is enabled and unset:
- `artifacts/research_runs/`

## Intentionally Deferred
- distributed orchestration / job queues
- experiment database/registry service
- UI/API integration
- model-to-strategy execution bridge
- multi-asset portfolio orchestration
