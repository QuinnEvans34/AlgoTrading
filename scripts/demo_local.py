"""Run a deterministic local smoke/demo workflow."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from _common import (
    DEFAULT_ENV_FILE,
    ROOT,
    build_command_env,
    load_env_file,
    run_command,
)


def run_step(name: str, command: list[str]) -> int:
    print()
    print(f"[demo] {name}")
    env = build_command_env(prepend_src_to_pythonpath=True)
    exit_code = run_command(command, env=env)
    if exit_code != 0:
        print(f"[demo] FAILED: {name} (exit={exit_code})")
        return exit_code
    print(f"[demo] PASSED: {name}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run local smoke/demo flow")
    parser.add_argument(
        "--env-file",
        default=str(DEFAULT_ENV_FILE),
        help="Optional .env file path (default: .env)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    load_env_file(Path(args.env_file))
    artifact_root = ROOT / "artifacts"
    research_artifacts = artifact_root / "research_runs"
    paper_artifacts = artifact_root / "paper_trading"
    steps = [
        ("Initialize artifact directories", [sys.executable, "scripts/init_artifacts.py"]),
        ("Research runner demo", [sys.executable, "examples/research_run_demo.py"]),
        ("Paper trading demo", [sys.executable, "examples/paper_trading_demo.py"]),
        ("Live execution boundary demo", [sys.executable, "examples/live_execution_boundary_demo.py"]),
        ("Manual live execution demo", [sys.executable, "examples/manual_live_execution_demo.py"]),
    ]

    for name, command in steps:
        exit_code = run_step(name, command)
        if exit_code != 0:
            return exit_code

    print()
    print("[demo] Local smoke demo completed.")
    print(f"[demo] Research artifacts path: {research_artifacts}")
    print(f"[demo] Paper-trading artifacts path: {paper_artifacts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
