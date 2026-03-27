# ML Dataset Subsystem (Feature Engineering + Labels)

## Purpose
The ML dataset subsystem transforms normalized candle data into deterministic, leakage-safe, training-ready tabular artifacts.

Current scope:
- historical-only feature computation
- explicit forward-horizon supervised labels
- deterministic row alignment and missing-value handling
- chronological train/validation/test splits with optional gap bars
- reproducibility metadata and stable schema output

## Architecture
- `src/ml_data/contracts.py`
  - Canonical contracts for request/specs, rows, artifact metadata, and split partitions.
- `src/ml_data/features.py`
  - Feature calculations over normalized candles using only information available up to each row timestamp.
- `src/ml_data/labels.py`
  - Target computations that are allowed to look forward by explicit horizon.
- `src/ml_data/validation.py`
  - Input and config validation (timestamp ordering, split sanity, label spec checks).
- `src/ml_data/splits.py`
  - Chronological split generation with optional temporal gap bars.
- `src/ml_data/dataset_builder.py`
  - End-to-end orchestration from candles -> features -> labels -> aligned dataset artifact.

## Leakage and Alignment Rules
- Features at row `t` use only candles `<= t`.
- Labels at row `t` may use candle `t + horizon` (explicitly configured).
- Warmup rows are dropped using `max_feature_lookback_bars`.
- Tail rows are dropped using `max_label_horizon_bars`.
- Rows with missing feature/label values are dropped (`MissingValuePolicy.DROP_ROW`).

## Included Features (This Phase)
- Return windows: `close[t]/close[t-w] - 1`
- Log return windows: `ln(close[t]/close[t-w])`
- Rolling volatility: std of one-bar returns over window
- Momentum: `close[t] - close[t-w]`
- Price vs SMA: `close[t]/SMA_w[t] - 1`
- SMA spread: `SMA_fast[t]/SMA_slow[t] - 1`
- ATR-normalized range: `ATR_w[t]/close[t]`
- Rolling close z-score
- Candle-structure features:
  - body ratio
  - upper wick ratio
  - lower wick ratio
  - high/low range ratio
- Optional volume features:
  - one-bar volume change
  - rolling volume z-score

## Included Labels (This Phase)
- `FutureReturnLabelSpec`: regression target over horizon bars.
- `DirectionLabelSpec`: binary classification target (`1` if future return > threshold else `0`).

## Reproducibility Metadata
Each artifact includes:
- dataset id
- feature and label schema
- lookback/horizon requirements
- row drop counts (warmup, horizon, missing)
- time range
- deterministic signature hash from config + schema + candle timestamps
- request snapshot

## Integration Boundary
- Input: normalized `market_data.contracts.Candle` sequence.
- Output: `MLDatasetArtifact` with typed rows, schema, metadata, and optional splits.
- No broker/provider assumptions in feature/label contracts.
- No coupling to training frameworks in this phase.

## Deferred to Later Phases
- model training and evaluation pipelines
- hyperparameter search
- experiment tracking platform
- feature store service
- online inference
- multi-asset portfolio dataset composition
- advanced labels (ternary, regime, meta-labeling)
- MACD/RSI/ADX feature families for ML-specific feature packs

