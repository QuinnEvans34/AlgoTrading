import importlib.util
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

FASTAPI_AVAILABLE = importlib.util.find_spec("fastapi") is not None

if FASTAPI_AVAILABLE:
    from fastapi.testclient import TestClient

    from api.app import create_app
    from api.config import APISettings


@unittest.skipUnless(FASTAPI_AVAILABLE, "fastapi is not installed")
class HealthMetadataTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        settings = APISettings(
            default_run_output_dir=self.tempdir.name,
            enable_oanda_provider=False,
        )
        self.client = TestClient(create_app(settings))

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_health(self) -> None:
        resp = self.client.get("/api/v1/health")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["version"], "v1")
        self.assertIn("timestamp", body)

    def test_capabilities(self) -> None:
        resp = self.client.get("/api/v1/metadata/capabilities")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertIn("strategy_research", body["workflows"])
        self.assertIn("technical_rule_v1", body["strategies"])
        self.assertIn("1d", body["intervals"])
        self.assertIn("stock", body["asset_classes"])
        self.assertIn("dummy_classifier", body["model_families"])


if __name__ == "__main__":
    unittest.main()

