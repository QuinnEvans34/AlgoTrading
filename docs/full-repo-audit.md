# Full Repo Audit

## 1. Executive Summary

This repo is a real multi-subsystem capstone platform, not a thin scaffold. It has a functioning backend domain layer, a FastAPI API, a TypeScript React frontend, local persistence for research and paper-trading artifacts, guarded live-execution boundaries, centralized runtime settings, and usable local developer tooling.

Blunt status assessment: the project is in **strong capstone/demo shape** and **weak production shape**. The architecture is broad and mostly coherent, the safety defaults are conservative, and the core workflows are genuinely wired. The main weaknesses are integration concentration, local-file persistence limits, dict-heavy artifact contracts, limited frontend behavioral testing, and the fact that the live path is intentionally architectural rather than broker-complete.

Short version:
- Strengths: breadth, subsystem separation, safe defaults, deterministic local workflows, meaningful backend test coverage, honest live-trading guardrails.
- Weaknesses: `src/api/services.py` is a large coupling hotspot, frontend confidence is mostly build-time, persistence is single-user/local-first, some response/data shapes stay loose longer than ideal, and production readiness is low.

## 2. System Overview

### What the platform is

This is a local-first, single-user financial research and strategy platform with:
- market data contracts and provider dispatch,
- strategy evaluation,
- historical backtesting,
- diagnostics/performance analytics,
- ML dataset generation and model training/evaluation,
- research orchestration and saved artifacts,
- backend APIs for research/history/compare/paper/live/settings,
- a React frontend for running workflows and viewing results,
- a paper trading sandbox,
- a strictly guarded manual live-execution boundary.

### What a user/operator can do right now

Based on the current codebase, a local operator can:
- run strategy research workflows from the UI or API,
- run ML research workflows from the UI or API,
- persist research runs and reopen them later,
- browse saved run history and compare compatible runs,
- operate a local paper trading account with market/limit orders and price updates,
- inspect live-execution readiness and attempt guarded manual live submissions,
- inspect safe runtime settings/status,
- run local checks, smoke tests, and demo scripts through standardized developer tooling.

### Major runtime flows

#### Research
- UI/API submits a research request.
- `ResearchRunner` orchestrates candle acquisition, strategy or ML execution, diagnostics, and persistence.
- Saved `summary.json`, `detail.json`, manifest, and index entries support later reopening and comparison.

#### History / Compare
- API reads the history index/manifests from local artifact storage.
- Frontend history pages render saved runs and drive compare actions.
- Compare logic assembles strategy or ML comparison payloads from persisted artifacts.

#### Paper Trading
- Manual paper order or price-update requests hit the API.
- `PaperTradingService` updates local paper account state, positions, orders, fills, and PnL.
- State persists to a local JSON file under `artifacts/paper_trading`.

#### Live Execution
- Manual live-intent validation and manual-order submission go through the live boundary only.
- Guard checks evaluate feature flags, live-enabled settings, broker readiness, confirmation phrase, and idempotency.
- Default behavior is fail-closed, with local attempt logging and status visibility.

## 3. Repo / Architecture Overview

### Repo layout

- `src/`: backend packages and application code
- `frontend/`: React + TypeScript frontend
- `docs/`: subsystem and operational docs
- `scripts/`: local developer and smoke/demo tooling
- `tests/`: backend/unit/integration-style regression coverage
- `examples/`: deterministic local example scripts
- `artifacts/`: local runtime persistence roots
- `legacy_reference/`: donor/reference material, not core runtime code

### Backend structure

Main backend packages actually present:
- `market_data`
- `strategy_engine`
- `backtesting`
- `diagnostics`
- `ml_data`
- `modeling`
- `research`
- `paper_trading`
- `live_execution`
- `config`
- `api`

The backend generally follows a clean package-per-subsystem layout. Most subsystems are modest in size and easier to reason about than the central API orchestration layer.

### Frontend structure

The frontend is now TS-first and route-driven:
- `frontend/src/App.tsx` defines top-level routes.
- `frontend/src/pages/` contains main operator pages.
- `frontend/src/components/` contains page-local UI pieces.
- `frontend/src/lib/` contains typed API clients and payload types.

It is a practical operator UI rather than a heavily state-managed SPA. That is appropriate for the project scope.

### Storage / artifact structure

Local storage is part of the core architecture:
- research runs under `artifacts/research_runs`
- paper trading state under `artifacts/paper_trading`
- live attempt logging under `artifacts/live_execution`

Research persistence uses per-run JSON artifacts plus manifest/index metadata. Paper trading uses a single JSON state file. Live execution attempts are recorded in JSONL.

### Config / env structure

Runtime config is centralized in `src/config/app_settings.py`, with safe projection in `src/config/safety.py`. The API compatibility wrapper in `src/api/config.py` adapts centralized settings back into route/service consumption.

Safe defaults are explicit:
- paper trading enabled locally,
- live status visible,
- live submission disabled by default,
- no real credentials required for local/demo use.

### Important entrypoints

- Backend app: `src/api/app.py`
- API dependency wiring: `src/api/dependencies.py`
- Central API service layer: `src/api/services.py`
- Developer task runner: `scripts/dev.py`
- Quality gate: `scripts/check.py`
- Smoke checks: `scripts/smoke_check.py`
- Frontend routes: `frontend/src/App.tsx`

## 4. Subsystem-by-Subsystem Audit

### Market Data

**Purpose**

Provide broker/provider-agnostic contracts for historical candles and quotes, plus provider registration and dispatch.

**Key files**
- `src/market_data/contracts.py`
- `src/market_data/registry.py`
- `src/market_data/service.py`
- `src/market_data/providers/oanda.py`

**How it works**

The package defines typed contracts and a provider registry. `MarketDataService` is intentionally thin and delegates to the provider selected by name. The API layer translates request payloads into `HistoricalCandleRequest` and related domain objects before dispatch.

**Inputs / outputs**
- Input: provider name + historical candle or quote request
- Output: typed candle/quote responses

**Dependencies**
- Used directly by research workflows and preview APIs
- Optionally uses OANDA provider config if enabled

**Strengths**
- Clean provider dispatch model
- Good contract separation
- No obvious over-engineering
- Provider enablement/config is explicit

**Weaknesses**
- Real provider breadth is limited
- Live quote handling exists architecturally but is not a major verified workflow
- Local/demo usefulness depends on inline candle flows when provider credentials are absent

**Gaps / inconsistencies**
- OANDA is the only real provider path referenced
- Not a broad market-data platform yet

**Status**

Complete for capstone scope, limited for broader platform ambitions.

**Grade**

`B+ / 8.0`

### Strategy Engine

**Purpose**

Evaluate trading strategies over candle windows and produce signals/evaluations.

**Key files**
- `src/strategy_engine/engine.py`
- `src/strategy_engine/contracts.py`
- `src/strategy_engine/indicators.py`
- `src/strategy_engine/strategies/*`

**How it works**

The `StrategyEngine` wrapper is intentionally minimal; real behavior lives in strategy implementations and shared indicator logic. This keeps the orchestration layer small and avoids inventing unnecessary abstractions.

**Inputs / outputs**
- Input: `StrategyInput`
- Output: `StrategyEvaluation` and signal objects consumed by backtesting or research workflows

**Dependencies**
- Used by research orchestration and backtesting

**Strengths**
- Small, understandable surface
- Clear strategy boundary
- Indicator code is reusable across research flows

**Weaknesses**
- Minimal wrapper means capabilities live in strategy-specific code, so behavior breadth depends on concrete strategies
- No evidence of a large plugin ecosystem or discovery model beyond supported IDs

**Gaps / inconsistencies**
- More “practical local strategy library” than generalized strategy platform

**Status**

Complete for current scope.

**Grade**

`B+ / 8.0`

### Backtesting

**Purpose**

Simulate single-asset historical strategy execution with costs, equity tracking, trades, and summary metrics.

**Key files**
- `src/backtesting/engine.py`
- `src/backtesting/contracts.py`
- `src/backtesting/execution.py`
- `src/backtesting/costs.py`
- `src/backtesting/metrics.py`
- `src/backtesting/walk_forward.py`
- `src/backtesting/monte_carlo.py`

**How it works**

`BacktestSimulator` performs the main event loop over candles, applies strategy evaluations after warmup, manages positions and risk exits, and builds equity/trade outputs. Cost and execution modeling are separate enough to stay readable.

**Inputs / outputs**
- Input: candles, strategy, backtest config
- Output: `BacktestResult` with trades, equity curve, diagnostics, and summary

**Dependencies**
- Consumes strategy-engine outputs
- Feeds research diagnostics and persisted detail payloads

**Strengths**
- Real implementation, not placeholder math
- Clear handling of warmup, exits, costs, and position flips
- Reasonable separation of metrics and execution helpers

**Weaknesses**
- Single-asset research orientation
- No evidence of portfolio-level simulation depth
- Advanced execution realism is intentionally limited

**Gaps / inconsistencies**
- Paper trading is correctly separate, but shared assumptions between backtest and paper are mostly conceptual rather than normalized into a common execution model

**Status**

Complete for the intended research/backtest slice.

**Grade**

`B+ / 8.2`

### Diagnostics / Performance Analytics

**Purpose**

Build summary analytics and performance diagnostics from strategy/backtest outputs.

**Key files**
- `src/diagnostics/*`
- research serialization paths that expose diagnostics in summaries/details

**How it works**

Diagnostics appear integrated as a downstream analysis layer rather than a standalone service. They are part of the research result payloads and user-facing result pages.

**Inputs / outputs**
- Input: backtest or training outputs
- Output: summary metrics, performance detail, diagnostics sections in saved artifacts

**Dependencies**
- Research runner
- Frontend result pages

**Strengths**
- Integrated into actual user flows
- Supports result detail pages and compare surfaces

**Weaknesses**
- Less independently obvious than some other subsystems because it is embedded in research outputs
- Audit confidence here is based more on integration evidence than isolated module review

**Gaps / inconsistencies**
- Not obviously standardized into one shared diagnostics schema across every workflow branch

**Status**

Complete enough for current workflows.

**Grade**

`B / 7.7`

### ML Dataset Generation

**Purpose**

Generate deterministic, leakage-aware ML datasets from candle series and explicit feature/label specs.

**Key files**
- `src/ml_data/dataset_builder.py`
- `src/ml_data/features.py`
- `src/ml_data/labels.py`
- `src/ml_data/splits.py`
- `src/ml_data/contracts.py`
- `src/ml_data/validation.py`

**How it works**

`build_ml_dataset` validates requests, sorts candles, computes features and labels, applies alignment/lookback/horizon rules, drops unusable rows, and optionally builds chronological splits. Metadata captures signatures and assumptions.

**Inputs / outputs**
- Input: candles + feature specs + label specs + split policy
- Output: `MLDatasetArtifact`

**Dependencies**
- Used by modeling/training and research orchestration

**Strengths**
- Deterministic and explicit
- Good leakage-awareness language in code and metadata
- Clear separation of features, labels, splits, and validation

**Weaknesses**
- More local artifact oriented than scalable data pipeline oriented
- Feature universe is practical rather than especially broad

**Gaps / inconsistencies**
- Some metadata and request snapshots remain dict-shaped rather than fully normalized into stable artifact schemas

**Status**

Complete for current scope.

**Grade**

`B+ / 8.2`

### Model Training / Evaluation

**Purpose**

Train and compare models against ML datasets with controlled splits, optional dependency behavior, and evaluation reporting.

**Key files**
- `src/modeling/trainer.py`
- `src/modeling/models.py`
- `src/modeling/evaluation.py`
- `src/modeling/contracts.py`
- `src/modeling/config.py`
- `src/modeling/artifacts.py`

**How it works**

The trainer turns datasets into tables, validates target labels and split sufficiency, optionally scales appropriate models, fits model instances, evaluates predictions by split, and assembles comparison artifacts.

**Inputs / outputs**
- Input: dataset artifact + target label + model specs + training config
- Output: training/evaluation artifacts and comparison tables

**Dependencies**
- ML dataset generation
- Research orchestration

**Strengths**
- Real training pipeline behavior
- Clear optional dependency policy
- Sensible split-aware evaluation structure

**Weaknesses**
- Model breadth is limited by implemented model adapters
- Production ML concerns like experiment tracking, large dataset handling, and artifact lineage are intentionally limited

**Gaps / inconsistencies**
- Still oriented toward deterministic local research rather than a mature ML platform

**Status**

Complete for capstone research use.

**Grade**

`B+ / 8.0`

### Research Orchestration

**Purpose**

Coordinate end-to-end strategy and ML workflows, persistence, and user-facing results.

**Key files**
- `src/research/runner.py`
- `src/research/contracts.py`
- `src/research/storage.py`
- `src/research/history.py`
- `src/research/compare.py`
- `src/research/validation.py`

**How it works**

`ResearchRunner` is the core orchestration entrypoint. It pulls candles from inline or provider sources, runs strategy or ML workflow branches, assembles summary/detail artifacts, and persists them when configured. History and compare are layered on top of saved manifests and detail payloads.

**Inputs / outputs**
- Input: research run request + candle source + strategy or ML spec
- Output: summary/detail artifacts, persisted manifests, history index records, compare payloads

**Dependencies**
- market data
- strategy engine
- backtesting
- diagnostics
- ml_data
- modeling

**Strengths**
- Real orchestrated workflows
- Persistence is integrated, not bolted on later
- Strategy and ML branches share a coherent research-run idea

**Weaknesses**
- Artifact/detail payloads lean heavily on nested dict structures
- The persistence/history layer is powerful enough for local use but not robust enough for multi-user or high-volume usage

**Gaps / inconsistencies**
- The hybrid story exists at API level but is less central than pure strategy or ML paths

**Status**

Complete for local research baseline, somewhat fragile at the persistence contract edges.

**Grade**

`B+ / 8.1`

### Persistence / History / Compare

**Purpose**

Persist research results, rebuild history if needed, support reopen/detail, and compare compatible runs.

**Key files**
- `src/research/storage.py`
- `src/research/history.py`
- `src/research/compare.py`
- `src/api/history_schemas.py`
- `frontend/src/pages/RunHistoryPage.tsx`
- `frontend/src/pages/CompareRunsPage.tsx`

**How it works**

Each run has its own persisted summary/detail files and manifest metadata. An index file accelerates listing. History endpoints read manifests/index data, with rebuild behavior for missing/corrupt index cases. Compare logic loads saved detail payloads and assembles strategy or ML comparisons.

**Inputs / outputs**
- Input: saved run artifacts and history queries
- Output: history lists, history read payloads, compare cards/rows

**Dependencies**
- research runner persistence
- API services/routes
- frontend history/compare pages

**Strengths**
- Real saved-artifact workflow
- Reopen and compare are actual product features, not mock pages
- Handles index rebuild/fallback cases

**Weaknesses**
- Heavy reliance on local JSON files and dict-like payloads
- Not suitable for multi-user concurrency or large histories
- Compare outputs are flexible but not especially rigidly typed

**Gaps / inconsistencies**
- Path data is still exposed in some backend-facing shapes even though frontend avoids leaking filesystem details directly
- Compatibility logic is good enough for current scope, not a general experiment lineage system

**Status**

Functional but locally fragile by design.

**Grade**

`B / 7.6`

### API Layer

**Purpose**

Expose backend functionality through FastAPI routes and Pydantic schemas for research, history, compare, paper, live, settings, metadata, and health.

**Key files**
- `src/api/app.py`
- `src/api/routes/*`
- `src/api/services.py`
- `src/api/schemas.py`
- `src/api/history_schemas.py`
- `src/api/live_execution_schemas.py`
- `src/api/settings_schemas.py`
- `src/api/serializers.py`
- `src/api/dependencies.py`

**How it works**

Routes are mostly thin and dispatch synchronous business logic through `run_in_threadpool`. Dependency wiring constructs subsystem services from centralized settings. `APIService` is the main integration layer that translates API payloads into backend contracts, enforces feature-flag guards, maps domain errors to API errors, and serializes responses.

**Inputs / outputs**

Everything user-facing flows through here:
- research run requests,
- history and compare reads,
- paper trading commands,
- live status/validation/manual submit attempts,
- settings visibility.

**Dependencies**

Nearly every major backend package.

**Strengths**
- Route layer is thin
- Pydantic schemas are generally explicit and strict
- Error mapping and feature-flag guards are centralized
- Current API surface is broad and coherent

**Weaknesses**
- `src/api/services.py` is a clear hotspot at **1084 lines**
- The service layer does too much translation/orchestration in one place
- Long-term maintainability risk is higher here than in most domain packages

**Gaps / inconsistencies**
- Some serializer and schema patterns are clean, but API-to-domain mapping remains hand-rolled and repetitive
- The layer is stable enough now, but future feature growth will make this file a liability unless split by concern

**Status**

Working and broad, but concentrated and somewhat brittle.

**Grade**

`B- / 7.3`

### Frontend Shell + Pages

**Purpose**

Provide a practical operator UI for research runs, result inspection, history/compare, paper trading, live status/manual attempts, metadata, and settings.

**Key files**
- `frontend/src/App.tsx`
- `frontend/src/pages/*`
- `frontend/src/components/*`
- `frontend/src/lib/api/*`
- `frontend/src/lib/history/*`
- `frontend/src/lib/settings/*`
- `frontend/src/lib/liveExecution/*`

**How it works**

The frontend is route-driven and API-first. Most pages use local component state plus `useEffect` fetches. Shared client code lives in `frontend/src/lib/api/client.ts`, with subsystem-specific wrappers and types in adjacent modules.

**Inputs / outputs**
- Input: API responses
- Output: operator forms, tables, detail views, compare surfaces, safety/status panels

**Dependencies**
- Backend API contracts

**Strengths**
- Covers the important workflows
- TS-first source-of-truth is now clean
- Error handling is centralized better than before
- UI scope is appropriate to the project

**Weaknesses**
- Confidence is mostly from typecheck/build and API tests, not UI behavioral tests
- State management is simple but repetitive
- Some pages are thin wrappers without a deeper shared view-model layer

**Gaps / inconsistencies**
- Operator UX is functional, not polished or especially resilient under weird states
- No serious frontend test suite is visible

**Status**

Complete for capstone/demo use, lightly tested.

**Grade**

`B / 7.4`

### Paper Trading

**Purpose**

Maintain an ongoing local paper account separate from backtesting, with orders, fills, positions, prices, and PnL.

**Key files**
- `src/paper_trading/contracts.py`
- `src/paper_trading/account.py`
- `src/paper_trading/orders.py`
- `src/paper_trading/execution.py`
- `src/paper_trading/storage.py`
- `src/paper_trading/service.py`
- `src/api/routes/paper_trading.py`
- `frontend/src/pages/PaperTradingPage.tsx`

**How it works**

`PaperTradingService` loads local state, validates orders, processes market/limit execution under simple rules, updates positions and account balances, and persists state. Price updates can trigger mark updates and limit fills. There is also a simple signal-intent bridge.

**Inputs / outputs**
- Input: paper orders, price updates, signal intents
- Output: account state snapshots, action responses, fills, open orders, positions

**Dependencies**
- local persistence
- market-data instrument contracts
- API/frontend operator flows

**Strengths**
- Cleanly separated from backtesting and live execution
- Real persistent account model
- Explicit fill assumptions and safety boundaries

**Weaknesses**
- Single-account, single-user, local-file only
- No partial fills, risk engine, or true broker semantics
- Price-driven limit behavior depends on explicit updates rather than streaming

**Gaps / inconsistencies**
- Good sandbox, not a realistic OMS/EMS

**Status**

Complete for the intended paper sandbox phase.

**Grade**

`B+ / 8.0`

### Live Execution Boundary / Manual Live Path

**Purpose**

Define the future live-broker seam and enforce manual, guarded, disabled-by-default live submission behavior.

**Key files**
- `src/live_execution/contracts.py`
- `src/live_execution/service.py`
- `src/live_execution/guards.py`
- `src/live_execution/readiness.py`
- `src/live_execution/attempt_log.py`
- `src/live_execution/brokers/*`
- `src/api/routes/live_execution.py`
- `frontend/src/pages/LiveExecutionPage.tsx`

**How it works**

The service resolves a broker adapter, exposes status and readiness, validates intents, and handles manual live-order attempts only if every guard passes. Local attempt logging captures safe summaries. Default adapters are `null` and `oanda_stub`, which reinforces that this is an architectural boundary, not a finished trading system.

**Inputs / outputs**
- Input: live intent validation or manual live-order request
- Output: readiness snapshots, validation previews, guarded submit responses, local attempt records

**Dependencies**
- centralized settings
- adapter registry
- API/frontend guardrail surfaces

**Strengths**
- Honest, explicit, fail-closed design
- Good manual confirmation and idempotency concepts
- Clear separation from paper trading

**Weaknesses**
- No real broker implementation
- Submission usefulness is architectural rather than operational
- Attempt logging is not audit-grade

**Gaps / inconsistencies**
- The existence of submit endpoints could be misread as “live trading exists” unless docs stay explicit

**Status**

Strong boundary design, intentionally partial execution reality.

**Grade**

`B+ / 8.3`

### Settings / Config / Safety

**Purpose**

Centralize runtime config, feature flags, storage paths, paper defaults, live safety settings, and safe frontend/API visibility.

**Key files**
- `src/config/app_settings.py`
- `src/config/environment.py`
- `src/config/feature_flags.py`
- `src/config/safety.py`
- `src/api/config.py`
- `src/api/settings_schemas.py`
- `src/api/routes/settings.py`
- `frontend/src/pages/SettingsPage.tsx`

**How it works**

`AppSettings.from_env()` is the backend source of truth. Safe projection strips secrets and exposes only status/config booleans and non-sensitive runtime fields. The API compatibility wrapper keeps older API wiring usable without splitting config models across layers again.

**Inputs / outputs**
- Input: environment variables and defaults
- Output: subsystem settings objects and safe status snapshots

**Dependencies**
- used across API, market-data provider setup, paper trading, live execution, and tooling

**Strengths**
- Better centralized than most student projects
- Safe snapshot model is explicit
- Live defaults remain conservative

**Weaknesses**
- `src/api/config.py` exists as a compatibility adapter, which is understandable but adds a translation layer that could drift over time
- Still env-file/local-process focused

**Gaps / inconsistencies**
- Good for local ops, not a mature deployment config system

**Status**

Complete and one of the stronger parts of the repo.

**Grade**

`A- / 8.6`

### Dev / Deployment Tooling

**Purpose**

Standardize local setup, startup, checks, smoke validation, and demos.

**Key files**
- `scripts/dev.py`
- `scripts/check.py`
- `scripts/smoke_check.py`
- `scripts/dev_backend.py`
- `scripts/dev_frontend.py`
- `scripts/init_artifacts.py`
- `README.md`
- `docs/local-development.md`
- `docs/demo-runbook.md`
- `docs/deployment-foundation.md`

**How it works**

Python wrapper scripts provide one boring, cross-platform path for bootstrap, backend start, frontend start, checks, smoke, and demo. This is the right choice for the repo’s actual shape.

**Inputs / outputs**
- Input: local env and installed dependencies
- Output: predictable local dev workflow

**Dependencies**
- centralized settings/env handling
- backend/frontend tooling

**Strengths**
- Practical and readable
- Stronger than typical capstone dev ergonomics
- Safe defaults remain explicit in the docs and scripts

**Weaknesses**
- No CI pipeline yet
- No container/devcontainer path
- Startup reliability still depends on manual multi-terminal use

**Gaps / inconsistencies**
- Good local ops foundation, not deployment automation

**Status**

Complete for local development scope.

**Grade**

`B+ / 8.1`

### Tests

**Purpose**

Provide backend unit/integration-style verification and regression coverage for core flows.

**Key files**
- `tests/api/*`
- `tests/research/*`
- `tests/paper_trading/*`
- `tests/live_execution/*`
- `tests/scripts/*`

**How it works**

The test suite relies on `unittest`, plus FastAPI `TestClient` for route regression. Current quality tooling runs `python -m unittest discover tests`.

**Inputs / outputs**
- Input: isolated temp directories and local offline payloads
- Output: backend confidence and regression protection

**Dependencies**
- nearly every backend package

**Strengths**
- Real backend coverage
- Important safety defaults and cross-flow regressions are tested
- Current suite passed during this audit

**Weaknesses**
- No serious frontend interaction tests
- Build pass is not the same as UI behavior confidence
- Production-like concurrency and persistence edge cases are lightly represented

**Gaps / inconsistencies**
- Test breadth is better than average for a capstone, but confidence is still backend-heavy

**Status**

Good backend coverage, incomplete overall product verification.

**Grade**

`B / 7.8`

### Docs

**Purpose**

Explain subsystem behavior, local development, safety defaults, demo workflows, and current implementation boundaries.

**Key files**
- `README.md`
- `docs/*.md`

**How it works**

Docs now cover major subsystems, local development, demo flow, deployment foundation, safety settings, and final hardening checks. They generally track implementation better than earlier phase-planning docs usually do.

**Strengths**
- Better documented than most student repos
- Operational docs are practical
- Safety language is generally honest

**Weaknesses**
- There are many docs now, so drift risk exists
- Some subsystem docs are stronger on intended structure than on current limitations

**Gaps / inconsistencies**
- A single audit document like this was missing before this phase

**Status**

Useful and above average, but requires maintenance discipline.

**Grade**

`B / 7.8`

## 5. End-to-End Flow Audit

### Strategy research run

**Appears fully wired?**

Yes.

**Evidence**
- API route exists and dispatches into `APIService`.
- `ResearchRunner` handles strategy branch orchestration.
- frontend strategy page submits and renders results.
- regression tests cover strategy run creation and saved detail retrieval.

**Weakest seam**

API service translation and long serializer path, not the domain logic.

**What likely breaks first**

Schema drift or serializer mismatch rather than core strategy/backtest execution.

**Confidence**

`High`

### ML research run

**Appears fully wired?**

Yes.

**Evidence**
- API route and frontend page exist.
- dataset build and training pipeline are real.
- regression tests create ML runs and inspect saved detail paths.

**Weakest seam**

Target-label/model-spec request validation and long nested result payloads.

**What likely breaks first**

Unusual model configurations or optional dependency edges, not the happy-path dummy/local models.

**Confidence**

`High`

### Save + reopen run

**Appears fully wired?**

Yes.

**Evidence**
- research persistence writes summary/detail/manifest/index structures.
- history and research detail routes are tested.
- frontend history and result pages exist.

**Weakest seam**

Local JSON artifact integrity and dict-heavy payload assumptions.

**What likely breaks first**

Corrupt or hand-edited artifacts, cross-version schema drift, or concurrent local writes.

**Confidence**

`High`

### Compare runs

**Appears fully wired?**

Yes, for compatible saved runs.

**Evidence**
- compare route and service path exist.
- frontend compare page exists.
- strategy compare regression exists.

**Weakest seam**

Loose row payload typing and compatibility logic depending on saved detail shape.

**What likely breaks first**

Inconsistent persisted detail payloads or mixed/incompatible run comparisons.

**Confidence**

`Medium-High`

### Paper trading flow

**Appears fully wired?**

Yes.

**Evidence**
- paper API routes exist,
- service/storage are real,
- frontend paper page exists,
- tests cover market order, limit order, price update, and storage flow.

**Weakest seam**

Single-file state persistence and explicit price-update dependence.

**What likely breaks first**

Concurrent writes, corrupt state file, or edge cases around shorting/fill assumptions.

**Confidence**

`High`

### Live readiness + guarded manual live path

**Appears fully wired?**

Yes, as a guarded boundary. No, as a real live trading implementation.

**Evidence**
- status/readiness/validate/manual submit/attempts routes exist,
- guards and attempt log exist,
- frontend live page exists,
- safety regression tests confirm fail-closed defaults.

**Weakest seam**

Human misunderstanding of capability versus readiness. The architecture is real, but actual broker execution is intentionally not.

**What likely breaks first**

Expectations, not code: someone assuming stub adapters mean real trading support.

**Confidence**

`High` for guardrails, `Low` for real-world live trading capability because that is not implemented.

### Frontend -> API -> backend flow

**Appears fully wired?**

Yes for the core paths inspected.

**Evidence**
- route coverage is broad,
- frontend pages map to actual endpoints,
- current build passes,
- backend regressions cover API behavior for major flows.

**Weakest seam**

Frontend runtime behavior under bad states is less verified than backend behavior.

**What likely breaks first**

UI state/error handling in odd API failure cases rather than the API itself.

**Confidence**

`Medium`

## 6. Code Quality / Engineering Audit

### Modularity

Good overall. The repo is meaningfully separated by subsystem and most backend packages are easier to reason about than average student codebases.

### Separation of concerns

Mostly good, with one major exception:
- domain packages are relatively clean,
- route handlers are thin,
- but `src/api/services.py` has become the main “everything translation layer” and is the clearest separation-of-concerns violation in the repo.

### Naming consistency

Good enough. Names are generally explicit and subsystem-oriented. Minor inconsistency comes from historical compatibility wrappers and differing naming conventions across phases.

### Type quality

Backend type discipline is decent and much better than pure-dict codebases. Frontend TS types are now aligned more closely with backend responses. That said, persisted artifact internals and compare row payloads still rely on flexible dict shapes in places where long-term stability would benefit from stricter normalization.

### Validation quality

Above average. Request schemas are strict, core pipeline validation exists, paper/live guard checks are explicit, and config parsing is centralized. Weaknesses remain around the sheer amount of translation logic in API service code.

### Error handling

Decent. The frontend client now normalizes non-JSON/network errors better, and the backend maps domain errors to API errors reasonably well. The remaining weakness is not obvious missing try/except blocks; it is the complexity concentration in the orchestration layer.

### Duplication

Moderate. Not terrible, but there is visible hand-rolled mapping logic across API schemas, serializers, service translation, and frontend types.

### Dead code / placeholder code

Some placeholder code exists intentionally:
- live broker stubs,
- future-facing provider/broker placeholders.

This is acceptable because the repo is honest about it. The placeholder risk is mostly interpretation risk, not hidden dead code.

### Coupling problems

Main coupling hotspot:
- `src/api/services.py`

Secondary coupling risks:
- persistence/history/compare relying on nested saved artifact dicts,
- frontend depending on many similar but separate API type modules.

### Maintainability risks

Highest maintainability risks:
1. `APIService` growing further.
2. artifact schema drift across persistence/history/detail/compare.
3. frontend runtime behavior not being verified with dedicated UI tests.
4. local-file persistence assumptions limiting future changes.

## 7. Testing / Verification Audit

### What exists now

During this audit:
- `py -3 scripts/check.py` passed.
- `python -m unittest discover tests` passed with **92 tests**.
- targeted regression suites for core flows, paper trading, and live-execution guards also passed.
- frontend `npm --prefix frontend run build` passed.

### What is genuinely covered

Backend confidence is real in these areas:
- strategy research path
- ML research path
- saved run history/read/compare basics
- paper trading happy paths and execution rules
- live-execution guarded rejection behavior
- settings fail-closed defaults
- local script/smoke utility behavior

### What is still not well tested

- frontend behavior under user interaction
- browser-level flow confidence
- persistence race conditions or multi-process conflicts
- real provider/broker integration behavior
- unusual artifact corruption beyond basic fallback cases

### Where confidence is low

Lowest confidence areas:
- frontend UX behavior under API failures or partial backend states
- production-like concurrency and durability behavior
- anything resembling real live execution

### What should be tested first next

1. Browser-level smoke tests for the core UI routes.
2. More persistence corruption and rebuild edge cases for history/paper/live logs.
3. Additional API contract regression around compare/detail payloads.

## 8. Config / Safety / Operational Audit

### Config handling

Config is in relatively good shape. `AppSettings` is the backend source of truth, and `src/config/safety.py` provides a safe projection model for frontend/API visibility.

### Secret hygiene

No obvious plaintext secret leakage was found in the inspected implementation paths. The project uses placeholders and boolean configured/not-configured visibility instead of exposing tokens.

### Live-disabled defaults

Strong and explicit:
- live execution disabled by default,
- live submission disabled by default,
- guard-chain checks reject manual submit attempts under default settings,
- docs and tests support that posture.

### Paper / live / research separation

This boundary is one of the better parts of the repo. Backtesting is not paper trading, and paper trading is not live execution. The architecture preserves that distinction cleanly enough for a capstone project.

### Local startup reliability

Good. The repo now has one obvious way to bootstrap, start, check, and smoke-test the stack through `scripts/dev.py` and related wrappers.

### Demo safety

Good. Local defaults preserve safe behavior, credential-free flows exist, and the live path remains guarded.

### Operational weaknesses

- single-user local assumptions are everywhere in persistence
- no CI safety net yet
- no containerized or hosted deployment path yet

## 9. Grading

| Category | Grade | Score / 10 | Notes |
|---|---:|---:|---|
| Overall Architecture | B+ | 8.2 | Broad, coherent, real subsystem map; main penalty is integration concentration and local-first fragility. |
| Backend Design | B+ | 8.2 | Domain packages are generally cleaner than the integration layer. |
| Frontend Design | B | 7.4 | Practical and complete enough, but lightly tested and not deeply state-hardened. |
| API Layer | B- | 7.3 | Broad and functional, but `APIService` is too large and central. |
| Strategy / Research Design | B+ | 8.1 | Strong capstone workflow design with real orchestration and persistence. |
| Backtesting Layer | B+ | 8.2 | Real simulation logic, appropriate scope, not overclaimed. |
| ML / Data Layer | B+ | 8.1 | Deterministic and thoughtful, with sensible split/evaluation handling. |
| Persistence / Run History | B | 7.6 | Useful and real, but heavily local-file and dict-shaped. |
| Paper Trading | B+ | 8.0 | Clean sandbox separation and good enough execution model for scope. |
| Live Trading Safety | B+ | 8.3 | Strong guardrails and honesty; no credit for real execution because it is not implemented. |
| Config / Safety Controls | A- | 8.6 | One of the strongest areas; centralized, explicit, and safe by default. |
| Dev Experience | B+ | 8.1 | Practical local workflow and quality scripts; no overbuilt tooling. |
| Testing | B | 7.8 | Good backend coverage, weak frontend behavior coverage. |
| Documentation | B | 7.8 | Better than average and practical, but drift risk exists across many docs. |
| Capstone Readiness | A- | 8.7 | Strong showcase baseline if critical seams stay stable. |
| Production Readiness | D+ | 4.2 | Local-file persistence, no real broker path, limited ops/testing depth, no deployment maturity. |

### Top 5 strongest areas

1. Centralized config and safety defaults
2. Clear paper vs live vs research separation
3. Real end-to-end research/history functionality
4. Practical local developer tooling
5. Backend test coverage for core guarded flows

### Top 5 weakest areas

1. `src/api/services.py` coupling and size
2. Lack of frontend behavioral test coverage
3. Local-file persistence fragility and concurrency limits
4. Flexible/dict-heavy artifact and compare payload shapes
5. Production/deployment readiness gap

## 10. Highest-Priority Problems

### Critical issues

1. **API integration concentration**
   - `src/api/services.py` is the main structural debt item.
   - It is already large enough to slow future cleanup and increase regression risk.

2. **Frontend confidence gap**
   - The frontend builds cleanly, but there is no equivalent of the backend regression depth for actual browser behavior.

3. **Persistence robustness ceiling**
   - Research history, paper state, and live attempt logging are all local-file based.
   - This is acceptable for the current scope but should be treated as a hard boundary, not quietly ignored.

### Medium issues

1. **Artifact/data contract looseness**
   - History/detail/compare depend on persisted shapes that are partly rigid and partly dict-like.

2. **Doc drift risk**
   - The repo has many docs now. That is useful, but it increases the maintenance burden.

3. **Compatibility wrapper layering**
   - `src/api/config.py` is reasonable today but could become another drift source if ignored.

### Lower-priority polish

1. UI state polish and empty/error-state refinement
2. Deeper compare-page typing and presentation consistency
3. Additional browser-safe smoke automation

## 11. Recommended Fix Order

### 1. Must fix now

1. Split `src/api/services.py` by concern without changing API contracts.
   - Good cut lines: research/history, paper, live, settings/metadata.
2. Add browser-level smoke coverage for the highest-value frontend routes.
   - Strategy run
   - ML run
   - history/compare
   - paper page
   - settings/live status
3. Tighten artifact contract normalization around history/detail/compare payloads.

### 2. Should fix next

1. Add more persistence edge-case tests:
   - corrupt manifest/detail/index
   - corrupt paper state
   - malformed live attempt log lines
2. Reduce repetitive API/frontend mapping boilerplate where it is obviously duplicated.
3. Add one "release readiness" regression script that chains bootstrap, backend smoke, and selected API flow checks.

### 3. Can defer

1. Container/devcontainer path
2. CI automation
3. richer frontend UX/state abstractions

### 4. Future enhancement only

1. Multi-user or DB-backed persistence
2. real broker adapter implementations
3. production-grade deployment and observability
4. serious portfolio-scale execution/research features

## 12. Appendix

### Key file references

Core entrypoints:
- `src/api/app.py`
- `src/api/dependencies.py`
- `src/api/services.py`
- `src/config/app_settings.py`
- `frontend/src/App.tsx`
- `scripts/dev.py`
- `scripts/check.py`

Research / persistence:
- `src/research/runner.py`
- `src/research/storage.py`
- `src/research/history.py`
- `src/research/compare.py`

Paper / live:
- `src/paper_trading/service.py`
- `src/paper_trading/storage.py`
- `src/live_execution/service.py`
- `src/live_execution/guards.py`

Frontend operator pages:
- `frontend/src/pages/StrategyRunPage.tsx`
- `frontend/src/pages/MLRunPage.tsx`
- `frontend/src/pages/RunHistoryPage.tsx`
- `frontend/src/pages/CompareRunsPage.tsx`
- `frontend/src/pages/PaperTradingPage.tsx`
- `frontend/src/pages/LiveExecutionPage.tsx`
- `frontend/src/pages/SettingsPage.tsx`

Verification evidence:
- `tests/api/test_core_flow_regression.py`
- `tests/api/test_safety_defaults_regression.py`
- `tests/paper_trading/test_service_flow.py`
- `tests/live_execution/test_manual_submission_guards.py`
- `docs/final-hardening-checklist.md`

### Terminology / implementation notes

- **Research run**: a persisted strategy or ML workflow execution with summary/detail artifacts.
- **Paper trading**: ongoing local simulated account state, not historical batch backtesting.
- **Live execution**: guarded boundary and manual attempt path only; not a finished real-trading implementation.
- **Safe settings snapshot**: API/frontend-safe projection of runtime config with no secrets exposed.

### Verification run during this audit

Commands executed during this audit:
- `py -3 scripts/check.py`
- `py -3 -m unittest tests.api.test_core_flow_regression tests.api.test_safety_defaults_regression tests.paper_trading.test_service_flow tests.live_execution.test_manual_submission_guards`

Observed result:
- all selected checks passed
- backend suite passed
- frontend build passed

What that still does **not** prove:
- true frontend behavior under browser interaction
- production deployment reliability
- multi-process persistence safety
- real broker execution capability
