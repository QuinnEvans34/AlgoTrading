# Strategy Subsystem (Indicators + Signal Generation)

## Purpose
This subsystem extracts reusable strategy logic into clean domain boundaries so the platform can run technical strategies across asset classes without provider/runtime coupling.

Current scope:
- Indicator calculation utilities over normalized candles
- Strategy contracts and signal models
- Strategy interface
- Initial technical rule strategy (refactored from donor concepts)

## Architecture

### Domain contracts
- `src/strategy_engine/contracts.py`
- Defines:
  - `StrategyInput` (instrument + interval + normalized candles)
  - `StrategySignal` (direction, confidence, rationale, indicator snapshot)
  - `StrategyEvaluation` (signal or no-signal with diagnostics)
  - `SignalDirection` enum

### Indicator layer
- `src/strategy_engine/indicators.py`
- Provider-neutral indicator math over `market_data.contracts.Candle`:
  - RSI, EMA, MACD, Bollinger Bands, Stochastic, ATR, ADX, annualized volatility

### Parameter/config layer
- `src/strategy_engine/parameters.py`
- Explicit strategy parameters with instrument-aware resolution:
  - defaults
  - per-asset-class profiles (`stock`, `forex`)
  - optional per-symbol overrides

### Strategy boundary
- `src/strategy_engine/strategies/base.py`
- `Strategy` interface defines a strict `evaluate(...) -> StrategyEvaluation` contract.

### Initial strategy implementation
- `src/strategy_engine/strategies/technical_rule_strategy.py`
- Implements a rule-based signal strategy using:
  - RSI z-score
  - MACD histogram with noise filtering
  - Stochastic + Bollinger position
  - ADX + volatility filters
  - optional volume sanity filter
  - relative-gap FVG heuristic (fraction-based, not pip-based)

### Minimal engine wrapper
- `src/strategy_engine/engine.py`
- Small orchestration helper to evaluate a strategy from callers.

## Donor Logic Reused (Conceptually)
From:
- `legacy_reference/forex_signal_scanner/indicators/indicator_calculator.py`
- `legacy_reference/forex_signal_scanner/signal_detection/signal_detector.py`

Reused concepts:
- Core technical indicators
- Symmetric buy/sell rule structure
- Confidence scoring from multiple indicator components
- Volatility/ADX gating and MACD noise filtering patterns

## Forex-Specific Assumptions Removed
- No pip-size constants in shared strategy contracts
- No `EUR_USD` defaulting in strategy logic
- No OANDA/provider dependency in indicator or signal code
- No scanner runtime concerns (notifications, macro fetch, execution loop) mixed into strategy evaluation
- FVG threshold uses relative price fraction, not fixed forex pip-size gap

## How This Plugs into Backtesting Later
Backtesting can pass normalized candle windows into `StrategyInput` and consume `StrategyEvaluation`:
- `signal` drives entry/exit simulation
- `indicators` and `diagnostics` support explainability and model diagnostics
- parameter sets can be tuned per asset class or per symbol during walk-forward optimization

## Minimal Demo
- `examples/technical_strategy_demo.py`
- Uses normalized candle objects as input and prints:
  - selected indicator snapshot
  - signal decision (if generated)
  - diagnostics when no signal is produced
