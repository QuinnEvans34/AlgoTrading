# Market Data Subsystem (Provider-Agnostic Foundation)

## Purpose
This subsystem provides a strict provider boundary for market data so the platform can support multiple asset classes and vendors without leaking provider-specific formats into shared logic.

Current implementation scope:
- Provider-neutral contracts for candles/quotes
- Provider interface
- Shared retry/backoff utility
- OANDA adapter (historical candles + live quote method)
- Minimal demo for historical candle fetch

## Architecture

### Core contracts
- `src/market_data/contracts.py`
- Defines normalized types:
  - `Instrument`
  - `HistoricalCandleRequest`
  - `HistoricalCandleResponse`
  - `Candle`
  - `LiveQuoteRequest`
  - `Quote`
  - `AssetClass`, `BarInterval`

No OANDA-specific fields are required by these contracts.

### Provider boundary
- `src/market_data/providers/base.py`
- `MarketDataProvider` defines:
  - `fetch_historical_candles(...)`
  - `fetch_live_quote(...)`

Future stock/forex providers implement this same contract.

### OANDA adapter
- `src/market_data/providers/oanda.py`
- Implements:
  - Symbol translation from generic forex symbols (e.g., `EUR/USD`) to OANDA format (`EUR_USD`)
  - Historical candle fetch with:
    - chunked range requests
    - retry on transient failures
    - count-based fallback if time-range request returns empty
    - expanded-window fallback
  - Live quote fetch via pricing endpoint
  - Normalization into shared `Candle` / `Quote` models

### Shared robustness utility
- `src/market_data/retry.py`
- Generic retry/backoff utility reusable by future adapters.

### Optional provider registry/service
- `src/market_data/registry.py`
- `src/market_data/service.py`
- Simple wiring layer for pluggable providers.

## Donor Logic Reused (Conceptually)
From `legacy_reference/forex_signal_scanner/data_fetcher/data_fetcher.py`:
- Retry behavior for transient request failures
- Empty-response fallback strategy (`count` fallback)
- Expanded-window fallback approach
- Chunked historical fetch concept

## Donor Assumptions Intentionally Not Reused
- No shared-code forex pip math
- No hard-coded `EUR_USD` defaults in contracts
- No OANDA-specific instrument format in external interface
- No coupling to strategy, backtesting, or live-trading scripts
- No direct import of donor project structure

## Future Provider Extension Points
- Add stock historical provider adapter (example: Polygon, Alpaca, or another source)
- Add stock live quote adapter
- Add provider capability metadata (historical/live support matrix)
- Add cache + rate-limit coordination above adapter boundary

## Minimal Demo
- `examples/oanda_historical_demo.py`
- Fetches normalized recent historical candles through the OANDA adapter.
- Environment variables:
  - `OANDA_API_TOKEN` (required)
  - `OANDA_ACCOUNT_ID` (optional for historical candles, required for live quote calls)
  - `OANDA_ENVIRONMENT` (`practice` default, or `live`)
  - `DEMO_FOREX_SYMBOL` (optional, defaults to `EUR/USD`)
