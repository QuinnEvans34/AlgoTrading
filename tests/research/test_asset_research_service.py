from __future__ import annotations

from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
import sys
import tempfile
import unittest

import httpx

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from asset_research import (  # noqa: E402
    OpenAIResponsesAssetResearchProvider,
)
from asset_research.service import AssetResearchService  # noqa: E402
from market_data import (  # noqa: E402
    AssetClass,
    BarInterval,
    Candle,
    HistoricalCandleRequest,
    HistoricalCandleResponse,
    Instrument,
    MarketDataProviderRegistry,
    MarketDataService,
)
from persistence import (  # noqa: E402
    ResearchRunMetadataListResult,
    ResearchRunMetadataQuery,
    ResearchRunMetadataRecord,
    SavedResearchConfigRecord,
)


def utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class FakeProvider:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload
        self.calls: list[dict[str, object]] = []

    def generate_json(
        self,
        *,
        instructions: str,
        input_text: str,
        schema_name: str,
        schema: dict[str, object],
    ) -> dict[str, object]:
        self.calls.append(
            {
                "instructions": instructions,
                "input_text": input_text,
                "schema_name": schema_name,
                "schema": schema,
            }
        )
        return self.payload


class FakeWorkflowRepository:
    def __init__(self, records: tuple[SavedResearchConfigRecord, ...]) -> None:
        self._records = records

    def list_saved_configs(self, *, config_type=None, limit=100):  # noqa: ANN001,ARG002
        return self._records[:limit]


class FakeMetadataRepository:
    def __init__(self, records: tuple[ResearchRunMetadataRecord, ...]) -> None:
        self._records = records

    def list_run_metadata(
        self,
        query: ResearchRunMetadataQuery,  # noqa: ARG002
    ) -> ResearchRunMetadataListResult:
        return ResearchRunMetadataListResult(
            items=self._records,
            total=len(self._records),
            limit=query.limit,
            offset=query.offset,
        )


class StubForexProvider:
    @property
    def name(self) -> str:
        return "stub_fx"

    def fetch_historical_candles(
        self,
        request: HistoricalCandleRequest,
    ) -> HistoricalCandleResponse:
        candles = (
            Candle(
                timestamp=utc("2026-03-20T00:00:00Z"),
                open=1.08,
                high=1.09,
                low=1.07,
                close=1.085,
                volume=1000.0,
            ),
            Candle(
                timestamp=utc("2026-03-21T00:00:00Z"),
                open=1.085,
                high=1.095,
                low=1.08,
                close=1.09,
                volume=1050.0,
            ),
        )
        return HistoricalCandleResponse(
            provider=self.name,
            instrument=request.instrument,
            interval=request.interval,
            candles=candles,
            metadata={},
        )

    def fetch_live_quote(self, request):  # noqa: ANN001,ARG002
        raise NotImplementedError


def saved_config_record(symbol: str, asset_class: str = "stock") -> SavedResearchConfigRecord:
    now = utc("2026-03-26T12:00:00Z")
    return SavedResearchConfigRecord(
        id="strategy_cfg_001",
        config_type="strategy",
        name="trend-template",
        description=None,
        config_schema_version=1,
        payload_json={"instrument": {"symbol": symbol, "asset_class": asset_class}, "interval": "1d"},
        instrument_symbol=symbol,
        asset_class=asset_class,
        interval="1d",
        created_at=now,
        updated_at=now,
        last_used_at=None,
    )


def run_metadata_record(symbol: str, asset_class: str = "stock") -> ResearchRunMetadataRecord:
    now = utc("2026-03-26T12:00:00Z")
    return ResearchRunMetadataRecord(
        run_id="run_001",
        run_name="trend-aapl",
        workflow_type="strategy_research",
        status="success",
        started_at=now,
        ended_at=now + timedelta(minutes=3),
        duration_ms=180000,
        instrument_symbol=symbol,
        asset_class=asset_class,
        interval="1d",
        candle_count=220,
        candle_source_type="inline_candles",
        has_strategy=True,
        has_ml=False,
        strategy_id="technical_rule_v1",
        total_trades=12,
        total_return_pct=8.4,
        total_net_pnl=1200.0,
        max_drawdown_pct=-3.2,
        sharpe_ratio=1.1,
        ml_task_type=None,
        ml_target_label=None,
        ml_best_model_id=None,
        ml_primary_metric_name=None,
        ml_best_validation_value=None,
        ml_best_test_value=None,
        ml_model_count_executed=None,
        ml_model_count_skipped=None,
        ml_warning_count=None,
        summary_path="run_001/summary.json",
        detail_path="run_001/detail.json",
        manifest_path="run_001/manifest.json",
        metadata_schema_version=1,
        artifact_schema_version=1,
        metadata_source="dual_write",
        manifest_synthetic=False,
        summary_available=True,
        detail_available=True,
        created_at=now,
        updated_at=now,
        artifact_fingerprint="fp",
        last_synced_at=now,
    )


class AssetResearchServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_stock_memo_context_uses_catalog_history_and_saved_configs(self) -> None:
        provider = FakeProvider(
            {
                "overview": "Overview text.",
                "recent_price_performance_context": "No compatible stock preview is currently wired.",
                "business_profile_context": "Business context.",
                "filing_fundamental_highlights": "Filing context is limited to the curated checklist.",
                "risks_open_questions": "Risk context.",
                "bottom_line_takeaway": "Bottom line.",
            }
        )
        service = AssetResearchService(
            provider=provider,
            market_data_service=MarketDataService(MarketDataProviderRegistry()),
            provider_registry=MarketDataProviderRegistry(),
            metadata_repository=FakeMetadataRepository((run_metadata_record("AAPL"),)),
            workflow_repository=FakeWorkflowRepository((saved_config_record("AAPL"),)),
            run_output_dir=Path(self.tempdir.name),
            enabled=True,
        )

        result = service.generate_memo(asset_class="stock", symbol="AAPL")

        self.assertEqual(result.symbol, "AAPL")
        self.assertEqual(result.sections[0].title, "Overview")
        self.assertTrue(
            any("filings and fundamentals data" in warning for warning in result.warnings)
        )
        self.assertIn('"saved_configs"', str(provider.calls[0]["input_text"]))
        self.assertIn('"market_price": null', str(provider.calls[0]["input_text"]))

    def test_forex_memo_uses_provider_backed_market_data_when_available(self) -> None:
        registry = MarketDataProviderRegistry()
        registry.register(StubForexProvider())
        provider = FakeProvider(
            {
                "overview": "Overview text.",
                "recent_price_performance_context": "Price context.",
                "macro_context": "Macro context.",
                "key_drivers": "Drivers.",
                "risks_open_questions": "Risks.",
                "bottom_line_takeaway": "Bottom line.",
            }
        )
        service = AssetResearchService(
            provider=provider,
            market_data_service=MarketDataService(registry),
            provider_registry=registry,
            metadata_repository=None,
            workflow_repository=FakeWorkflowRepository((saved_config_record("EUR_USD", "forex"),)),
            run_output_dir=Path(self.tempdir.name),
            enabled=True,
        )

        result = service.generate_memo(asset_class="forex", symbol="EUR_USD")

        self.assertEqual(result.asset_class, "forex")
        self.assertFalse(
            any("FX price preview is not currently available" in warning for warning in result.warnings)
        )
        self.assertIn('"market_price"', str(provider.calls[0]["input_text"]))
        self.assertIn("stub_fx", str(provider.calls[0]["input_text"]))

    def test_openai_provider_parses_structured_response(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.url.path, "/responses")
            return httpx.Response(
                200,
                json={
                    "output": [
                        {
                            "content": [
                                {
                                    "text": '{"answer":"Grounded answer."}'
                                }
                            ]
                        }
                    ]
                },
            )

        transport = httpx.MockTransport(handler)
        client = httpx.Client(transport=transport, base_url="https://example.test")
        provider = OpenAIResponsesAssetResearchProvider(
            api_key="test-key",
            model="test-model",
            timeout_seconds=5,
            base_url="https://example.test",
            client=client,
        )

        payload = provider.generate_json(
            instructions="Use only provided context.",
            input_text='{"question":"What matters?"}',
            schema_name="asset_research_answer",
            schema={"type": "object"},
        )

        self.assertEqual(payload["answer"], "Grounded answer.")


if __name__ == "__main__":
    unittest.main()
