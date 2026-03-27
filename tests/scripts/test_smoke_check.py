import importlib.util
import os
import pathlib
import sys
import unittest
from unittest.mock import patch


ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPTS_DIR = ROOT / "scripts"
SMOKE_CHECK_PATH = ROOT / "scripts" / "smoke_check.py"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def load_module():
    module_name = "scripts_smoke_check"
    spec = importlib.util.spec_from_file_location(module_name, SMOKE_CHECK_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class SmokeCheckTests(unittest.TestCase):
    def test_resolve_base_url_from_api_env(self) -> None:
        module = load_module()
        with patch.dict(
            os.environ,
            {
                "API_HOST": "localhost",
                "API_PORT": "9000",
                "API_PREFIX": "/api/v2",
            },
            clear=True,
        ):
            self.assertEqual(module.resolve_base_url(None), "http://localhost:9000/api/v2")

    def test_run_case_fails_when_required_key_missing(self) -> None:
        module = load_module()
        case = module.SmokeCheckCase(name="health", path="/health", required_keys=("status",))
        with patch.object(module, "fetch_json", return_value=(200, {"ok": True}, None)):
            result = module.run_case("http://example/api", case, timeout_seconds=1.0)
        self.assertFalse(result.passed)
        self.assertIn("status", result.missing_keys)

    def test_settings_case_rejects_forbidden_token_keys(self) -> None:
        module = load_module()
        case = module.SmokeCheckCase(
            name="settings",
            path="/settings/system",
            required_keys=("runtime",),
        )
        with patch.object(
            module,
            "fetch_json",
            return_value=(200, {"runtime": {}, "api_token": "secret"}, None),
        ):
            result = module.run_case("http://example/api", case, timeout_seconds=1.0)
        self.assertFalse(result.passed)
        self.assertIn("Forbidden secret keys", result.error or "")

    def test_live_readiness_case_honors_disabled_default(self) -> None:
        module = load_module()
        case = module.SmokeCheckCase(
            name="live",
            path="/live-execution/readiness",
            required_keys=("manual_submission_ready",),
        )
        with patch.dict(os.environ, {"LIVE_EXECUTION_ENABLED": "false"}, clear=True):
            with patch.object(
                module,
                "fetch_json",
                return_value=(200, {"manual_submission_ready": True}, None),
            ):
                result = module.run_case("http://example/api", case, timeout_seconds=1.0)
        self.assertFalse(result.passed)
        self.assertIn("disabled", result.error or "")

    def test_settings_case_requires_expected_keys(self) -> None:
        module = load_module()
        case = module.SmokeCheckCase(
            name="settings",
            path="/settings/system",
            required_keys=("runtime", "feature_flags", "live_safety"),
        )
        with patch.object(
            module,
            "fetch_json",
            return_value=(200, {"runtime": {}, "feature_flags": {}}, None),
        ):
            result = module.run_case("http://example/api", case, timeout_seconds=1.0)
        self.assertFalse(result.passed)
        self.assertIn("live_safety", result.missing_keys)

    def test_live_readiness_case_passes_with_disabled_and_not_ready(self) -> None:
        module = load_module()
        case = module.SmokeCheckCase(
            name="live",
            path="/live-execution/readiness",
            required_keys=("manual_submission_ready",),
        )
        with patch.dict(os.environ, {"LIVE_EXECUTION_ENABLED": "false"}, clear=True):
            with patch.object(
                module,
                "fetch_json",
                return_value=(200, {"manual_submission_ready": False}, None),
            ):
                result = module.run_case("http://example/api", case, timeout_seconds=1.0)
        self.assertTrue(result.passed)


if __name__ == "__main__":
    unittest.main()
