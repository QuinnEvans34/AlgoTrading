"""Run local quality gates for backend and frontend."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from _common import (
    DEFAULT_ENV_FILE,
    load_env_file,
    resolve_npm_executable,
    run_command,
)


def run_step(name: str, command: list[str]) -> int:
    print()
    print(f"[check] {name}")
    exit_code = run_command(command)
    if exit_code != 0:
        print(f"[check] FAILED: {name} (exit={exit_code})")
        return exit_code
    print(f"[check] PASSED: {name}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run repository quality checks")
    parser.add_argument(
        "--env-file",
        default=str(DEFAULT_ENV_FILE),
        help="Optional .env file path (default: .env)",
    )
    parser.add_argument("--skip-compile", action="store_true", help="Skip compileall")
    parser.add_argument("--skip-tests", action="store_true", help="Skip backend tests")
    parser.add_argument("--skip-frontend", action="store_true", help="Skip frontend build")
    parser.add_argument(
        "--with-smoke",
        action="store_true",
        help="Run API smoke check at the end (backend must already be running).",
    )
    parser.add_argument(
        "--smoke-base-url",
        default=None,
        help="Optional API base URL for smoke check (for example http://127.0.0.1:8000/api/v1).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    load_env_file(Path(args.env_file))
    npm_executable = resolve_npm_executable()
    steps: list[tuple[str, list[str]]] = []

    if not args.skip_compile:
        steps.append(("Backend compile check", [sys.executable, "-m", "compileall", "src"]))
    if not args.skip_tests:
        steps.append(("Backend test suite", [sys.executable, "-m", "unittest", "discover", "tests"]))
    if not args.skip_frontend:
        steps.append(
            (
                "Frontend typecheck+build",
                [npm_executable, "--prefix", "frontend", "run", "build"],
            )
        )
    if args.with_smoke:
        smoke_command = [sys.executable, "scripts/smoke_check.py"]
        if args.smoke_base_url:
            smoke_command.extend(["--base-url", args.smoke_base_url])
        steps.append(("API smoke check", smoke_command))

    if not steps:
        print("No checks selected.")
        return 0

    for name, command in steps:
        exit_code = run_step(name, command)
        if exit_code != 0:
            return exit_code

    print()
    print("[check] All selected checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
