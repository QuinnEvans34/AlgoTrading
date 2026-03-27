"""Run API operability smoke checks for local development."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import json
import os
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from _common import DEFAULT_ENV_FILE, load_env_file


@dataclass(frozen=True)
class SmokeCheckCase:
    name: str
    path: str
    required_keys: tuple[str, ...] = ()


@dataclass(frozen=True)
class SmokeCheckResult:
    case: SmokeCheckCase
    passed: bool
    status_code: int | None = None
    error: str | None = None
    missing_keys: tuple[str, ...] = ()


@dataclass
class SmokeCheckReport:
    base_url: str
    results: list[SmokeCheckResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(result.passed for result in self.results)


FORBIDDEN_SETTINGS_KEYS = {"oanda_api_token", "live_oanda_api_token", "api_token"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run API smoke checks")
    parser.add_argument(
        "--env-file",
        default=str(DEFAULT_ENV_FILE),
        help="Optional .env file path (default: .env)",
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help="API base URL override (for example http://127.0.0.1:8000/api/v1)",
    )
    parser.add_argument("--timeout-seconds", type=float, default=5.0)
    return parser.parse_args()


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    normalized = raw.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


def resolve_base_url(override: str | None) -> str:
    if override:
        return override.rstrip("/")
    vite_base = os.getenv("VITE_API_BASE_URL", "").strip()
    if vite_base:
        return vite_base.rstrip("/")
    host = os.getenv("API_HOST", "127.0.0.1").strip() or "127.0.0.1"
    port = os.getenv("API_PORT", "8000").strip() or "8000"
    prefix = os.getenv("API_PREFIX", "/api/v1").strip() or "/api/v1"
    if not prefix.startswith("/"):
        prefix = f"/{prefix}"
    return f"http://{host}:{port}{prefix}".rstrip("/")


def fetch_json(url: str, timeout_seconds: float) -> tuple[int, dict[str, Any] | None, str | None]:
    request = Request(url=url, method="GET")
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            status_code = int(getattr(response, "status", 200))
            payload = json.loads(response.read().decode("utf-8"))
            if not isinstance(payload, dict):
                return status_code, None, "Response is not a JSON object"
            return status_code, payload, None
    except HTTPError as exc:
        return exc.code, None, f"HTTP error: {exc.code}"
    except URLError as exc:
        return None, None, f"Connection error: {exc.reason}"
    except json.JSONDecodeError as exc:
        return None, None, f"Invalid JSON response: {exc}"


def collect_forbidden_keys(payload: Any, *, forbidden: set[str]) -> set[str]:
    found: set[str] = set()
    if isinstance(payload, dict):
        for key, value in payload.items():
            lowered = str(key).lower()
            if lowered in forbidden:
                found.add(lowered)
            found.update(collect_forbidden_keys(value, forbidden=forbidden))
    elif isinstance(payload, list):
        for item in payload:
            found.update(collect_forbidden_keys(item, forbidden=forbidden))
    return found


def run_case(
    base_url: str,
    case: SmokeCheckCase,
    *,
    timeout_seconds: float,
) -> SmokeCheckResult:
    url = f"{base_url}{case.path}"
    status_code, payload, error = fetch_json(url, timeout_seconds)
    if error:
        return SmokeCheckResult(case=case, passed=False, status_code=status_code, error=error)
    if status_code != 200:
        return SmokeCheckResult(
            case=case,
            passed=False,
            status_code=status_code,
            error=f"Expected HTTP 200, got {status_code}",
        )
    assert payload is not None
    missing = tuple(key for key in case.required_keys if key not in payload)
    if missing:
        return SmokeCheckResult(
            case=case,
            passed=False,
            status_code=status_code,
            error="Missing required keys",
            missing_keys=missing,
        )
    if case.path == "/settings/system":
        leaked = collect_forbidden_keys(payload, forbidden=FORBIDDEN_SETTINGS_KEYS)
        if leaked:
            return SmokeCheckResult(
                case=case,
                passed=False,
                status_code=status_code,
                error=f"Forbidden secret keys present in payload: {sorted(leaked)}",
            )
    if case.path == "/live-execution/readiness":
        live_enabled = _env_bool("LIVE_EXECUTION_ENABLED", False)
        ready = bool(payload.get("manual_submission_ready"))
        if not live_enabled and ready:
            return SmokeCheckResult(
                case=case,
                passed=False,
                status_code=status_code,
                error="Live readiness reports manual submission ready while live is disabled.",
            )
    return SmokeCheckResult(case=case, passed=True, status_code=status_code)


def main() -> int:
    args = parse_args()
    load_env_file(Path(args.env_file))
    base_url = resolve_base_url(args.base_url)
    cases = [
        SmokeCheckCase(
            name="Health endpoint",
            path="/health",
            required_keys=("status", "service", "version", "timestamp"),
        ),
        SmokeCheckCase(
            name="Capabilities endpoint",
            path="/metadata/capabilities",
            required_keys=("workflows", "providers", "feature_flags"),
        ),
        SmokeCheckCase(
            name="Settings endpoint",
            path="/settings/system",
            required_keys=("runtime", "feature_flags", "live_safety", "paper_defaults"),
        ),
        SmokeCheckCase(
            name="Live readiness endpoint",
            path="/live-execution/readiness",
            required_keys=("state", "manual_submission_ready", "checks"),
        ),
    ]
    report = SmokeCheckReport(base_url=base_url)

    print(f"Running smoke checks against: {base_url}")
    for case in cases:
        result = run_case(base_url, case, timeout_seconds=args.timeout_seconds)
        report.results.append(result)
        status = "PASS" if result.passed else "FAIL"
        details = f" ({result.error})" if result.error else ""
        if result.missing_keys:
            details = f"{details} missing={list(result.missing_keys)}"
        print(f"[{status}] {case.name}{details}")

    if report.passed:
        print("Smoke checks passed.")
        return 0
    print("Smoke checks failed.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
