import importlib.util
import os
import sys
import unittest
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

FASTAPI_AVAILABLE = importlib.util.find_spec("fastapi") is not None

if FASTAPI_AVAILABLE:
    from fastapi.testclient import TestClient

    from api.app import create_app
    from api.config import APISettings
    from api.dependencies import get_asset_research_service
    from asset_research import (
        AssetResearchProviderError,
        AssetResearchUnavailableError,
    )
    from asset_research.models import (
        AssetResearchMemoResult,
        AssetResearchMemoSection,
        AssetResearchQuestionResult,
        GroundingDescriptor,
    )


def utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


class FakeAssetResearchService:
    def generate_memo(self, *, asset_class: str, symbol: str) -> AssetResearchMemoResult:
        return AssetResearchMemoResult(
            asset_class=asset_class,  # type: ignore[arg-type]
            symbol=symbol,
            name="Apple" if symbol == "AAPL" else symbol,
            generated_at=utc("2026-03-26T12:00:00Z"),
            sections=(
                AssetResearchMemoSection("Overview", "Grounded overview."),
                AssetResearchMemoSection(
                    "Recent Price / Performance Context",
                    "Grounded performance context.",
                ),
            ),
            grounding=(
                GroundingDescriptor(
                    source="catalog",
                    status="used",
                    detail="Using shared catalog context.",
                ),
            ),
            warnings=("No live filings feed is wired yet.",),
        )

    def answer_question(
        self,
        *,
        asset_class: str,
        symbol: str,
        question: str,
    ) -> AssetResearchQuestionResult:
        return AssetResearchQuestionResult(
            asset_class=asset_class,  # type: ignore[arg-type]
            symbol=symbol,
            name="Apple" if symbol == "AAPL" else symbol,
            question=question,
            generated_at=utc("2026-03-26T12:05:00Z"),
            answer="Grounded answer.",
            grounding=(
                GroundingDescriptor(
                    source="recent_run_history",
                    status="used",
                    detail="Loaded recent run history.",
                ),
            ),
            warnings=(),
        )


class UnavailableAssetResearchService:
    def generate_memo(self, *, asset_class: str, symbol: str):  # noqa: ANN001,ARG002
        raise AssetResearchUnavailableError("Grounded AI research is disabled.")

    def answer_question(self, *, asset_class: str, symbol: str, question: str):  # noqa: ANN001,ARG002
        raise AssetResearchProviderError("Upstream provider request failed.")


@unittest.skipUnless(FASTAPI_AVAILABLE, "fastapi is not installed")
class AssetResearchEndpointTests(unittest.TestCase):
    def create_client(self, service) -> TestClient:  # noqa: ANN001
        app = create_app(APISettings(enable_oanda_provider=False))
        app.dependency_overrides[get_asset_research_service] = lambda: service
        return TestClient(app)

    def test_generate_memo_and_question_success(self) -> None:
        client = self.create_client(FakeAssetResearchService())
        try:
            memo = client.post(
                "/api/v1/asset-research/memos",
                json={"asset_class": "stock", "symbol": "AAPL"},
            )
            self.assertEqual(memo.status_code, 200)
            memo_body = memo.json()
            self.assertEqual(memo_body["asset"]["symbol"], "AAPL")
            self.assertEqual(memo_body["sections"][0]["title"], "Overview")
            self.assertEqual(memo_body["grounding"][0]["source"], "catalog")

            question = client.post(
                "/api/v1/asset-research/questions",
                json={
                    "asset_class": "stock",
                    "symbol": "AAPL",
                    "question": "What matters here?",
                },
            )
            self.assertEqual(question.status_code, 200)
            question_body = question.json()
            self.assertEqual(question_body["answer"], "Grounded answer.")
            self.assertEqual(question_body["question"], "What matters here?")
        finally:
            client.close()

    def test_unavailable_and_provider_failures_are_structured(self) -> None:
        client = self.create_client(UnavailableAssetResearchService())
        try:
            unavailable = client.post(
                "/api/v1/asset-research/memos",
                json={"asset_class": "stock", "symbol": "AAPL"},
            )
            self.assertEqual(unavailable.status_code, 503)
            self.assertEqual(
                unavailable.json()["error"]["code"],
                "asset_research_unavailable",
            )

            provider_error = client.post(
                "/api/v1/asset-research/questions",
                json={
                    "asset_class": "forex",
                    "symbol": "EUR_USD",
                    "question": "Why is this pair strong?",
                },
            )
            self.assertEqual(provider_error.status_code, 502)
            self.assertEqual(
                provider_error.json()["error"]["code"],
                "asset_research_provider_error",
            )
        finally:
            client.close()

    def test_invalid_requests_are_rejected(self) -> None:
        client = self.create_client(FakeAssetResearchService())
        try:
            invalid_asset = client.post(
                "/api/v1/asset-research/memos",
                json={"asset_class": "crypto", "symbol": "BTC"},
            )
            self.assertEqual(invalid_asset.status_code, 422)

            invalid_question = client.post(
                "/api/v1/asset-research/questions",
                json={"asset_class": "stock", "symbol": "AAPL", "question": "no"},
            )
            self.assertEqual(invalid_question.status_code, 422)
        finally:
            client.close()


if __name__ == "__main__":
    unittest.main()
