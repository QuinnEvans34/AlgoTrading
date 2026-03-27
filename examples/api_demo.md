# API Demo (Local)

## 1) Install API Dependencies
```bash
py -3 -m pip install -r requirements-api.txt
```

## 2) Start the API
```bash
py -3 -m uvicorn api.app:app --app-dir src --host 127.0.0.1 --port 8000 --reload
```

## 3) Health Check
```bash
curl http://127.0.0.1:8000/api/v1/health
```

## 4) Capabilities
```bash
curl http://127.0.0.1:8000/api/v1/metadata/capabilities
```

## 5) Strategy Research Run (Inline Candles)
```bash
curl -X POST http://127.0.0.1:8000/api/v1/research/strategy-runs \
  -H "Content-Type: application/json" \
  -d '{
    "instrument": { "symbol": "AAPL", "asset_class": "stock" },
    "interval": "1d",
    "candle_source": {
      "source_type": "inline_candles",
      "candles": [
        { "timestamp": "2026-01-01T00:00:00Z", "open": 100, "high": 101, "low": 99, "close": 100.5, "volume": 1000 },
        { "timestamp": "2026-01-02T00:00:00Z", "open": 100.5, "high": 102, "low": 100, "close": 101.2, "volume": 1000 },
        { "timestamp": "2026-01-03T00:00:00Z", "open": 101.2, "high": 103, "low": 101, "close": 102.5, "volume": 1000 },
        { "timestamp": "2026-01-04T00:00:00Z", "open": 102.5, "high": 104, "low": 102, "close": 103.1, "volume": 1000 }
      ]
    },
    "strategy_spec": {
      "backtest_config": {
        "warmup_bars": 1,
        "min_signal_confidence": 0.0
      }
    }
  }'
```

## 6) Run Summaries (Persisted)
```bash
curl http://127.0.0.1:8000/api/v1/research/runs
```

