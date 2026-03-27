"""Minimal demo: fetch normalized historical candles through OANDA adapter.

Usage (PowerShell):
  $env:OANDA_API_TOKEN="..."
  $env:OANDA_ACCOUNT_ID="..."
  py examples/oanda_historical_demo.py
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from market_data import (  # noqa: E402
    AssetClass,
    BarInterval,
    HistoricalCandleRequest,
    Instrument,
    OandaConfig,
    OandaMarketDataProvider,
)


def main() -> None:
    token = os.getenv("OANDA_API_TOKEN")
    if not token:
        raise RuntimeError("Set OANDA_API_TOKEN before running this demo.")

    account_id = os.getenv("OANDA_ACCOUNT_ID")
    environment = os.getenv("OANDA_ENVIRONMENT", "practice")
    symbol = os.getenv("DEMO_FOREX_SYMBOL", "EUR/USD")

    provider = OandaMarketDataProvider(
        OandaConfig(
            api_token=token,
            account_id=account_id,
            environment=environment,
        )
    )

    now = datetime.now(timezone.utc)
    request = HistoricalCandleRequest(
        instrument=Instrument(symbol=symbol, asset_class=AssetClass.FOREX),
        interval=BarInterval.M1,
        start=now - timedelta(hours=3),
        end=now,
        limit=20,
    )

    response = provider.fetch_historical_candles(request)
    print(f"Provider: {response.provider}")
    print(f"Instrument: {response.instrument.symbol}")
    print(f"Candle count: {len(response.candles)}")
    if response.candles:
        first = response.candles[0]
        last = response.candles[-1]
        print(
            "First:",
            first.timestamp.isoformat(),
            first.open,
            first.high,
            first.low,
            first.close,
        )
        print(
            "Last:",
            last.timestamp.isoformat(),
            last.open,
            last.high,
            last.low,
            last.close,
        )


if __name__ == "__main__":
    main()
