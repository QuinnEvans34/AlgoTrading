"""Canonical developer workflow entrypoint."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import sys
import time
from urllib.parse import urlparse

from _common import (
    DEFAULT_ENV_FILE,
    ROOT,
    ensure_artifact_dirs_from_env,
    load_env_file,
    require_python_311_plus,
    resolve_npm_executable,
    run_command,
)


@dataclass(frozen=True)
class DevCommand:
    name: str
    script: str
    description: str


COMMANDS = {
    "backend": DevCommand(
        name="backend",
        script="scripts/dev_backend.py",
        description="Start backend API server",
    ),
    "frontend": DevCommand(
        name="frontend",
        script="scripts/dev_frontend.py",
        description="Start frontend dev server",
    ),
    "check": DevCommand(
        name="check",
        script="scripts/check.py",
        description="Run local quality checks",
    ),
    "smoke": DevCommand(
        name="smoke",
        script="scripts/smoke_check.py",
        description="Run API operability smoke checks",
    ),
    "demo": DevCommand(
        name="demo",
        script="scripts/demo_local.py",
        description="Run deterministic local demo flow",
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Developer task runner")
    parser.add_argument(
        "command",
        choices=["bootstrap", *COMMANDS.keys()],
        help="Command to execute",
    )
    parser.add_argument(
        "extra",
        nargs=argparse.REMAINDER,
        help="Arguments forwarded to the selected command",
    )
    base_args = parser.parse_args()
    if base_args.command != "bootstrap":
        return argparse.Namespace(command=base_args.command, args=list(base_args.extra))

    bootstrap = argparse.ArgumentParser(description="Run bootstrap preflight")
    bootstrap.add_argument(
        "--env-file",
        default=str(DEFAULT_ENV_FILE),
        help="Optional .env file path (default: .env)",
    )
    bootstrap.add_argument(
        "--skip-init-artifacts",
        action="store_true",
        help="Skip artifact directory initialization",
    )
    bootstrap.add_argument(
        "--with-check",
        action="store_true",
        help="Run scripts/check.py after bootstrap preflight",
    )
    bootstrap.add_argument(
        "--with-smoke",
        action="store_true",
        help="Run scripts/smoke_check.py after bootstrap preflight (backend must be running).",
    )
    parsed_bootstrap = bootstrap.parse_args(base_args.extra)
    parsed_bootstrap.command = "bootstrap"
    return parsed_bootstrap


def run_script(script: str, forwarded_args: list[str] | None = None) -> int:
    args = forwarded_args or []
    command = [sys.executable, script, *args]
    return run_command(command)


def _database_bootstrap_enabled() -> bool:
    enabled = os.getenv("DATABASE_ENABLED", "").strip().lower() in {"1", "true", "yes", "on"}
    url = os.getenv("DATABASE_URL", "").strip()
    return enabled and url != ""


def _database_identity_from_url() -> tuple[str, str]:
    raw_url = os.getenv("DATABASE_URL", "").strip()
    parsed = urlparse(raw_url)
    username = parsed.username or "capstone"
    database = parsed.path.lstrip("/") or "capstone"
    return username, database


def _wait_for_local_postgres(*, attempts: int = 20, delay_seconds: float = 1.0) -> int:
    username, database = _database_identity_from_url()
    for attempt in range(1, attempts + 1):
        exit_code = run_command(
            [
                "docker",
                "compose",
                "exec",
                "-T",
                "postgres",
                "pg_isready",
                "-U",
                username,
                "-d",
                database,
            ],
            label=f"Waiting for Postgres ({attempt}/{attempts})",
            cwd=ROOT,
        )
        if exit_code == 0:
            return 0
        time.sleep(delay_seconds)
    return 1


def run_bootstrap(args: argparse.Namespace) -> int:
    env_file = Path(args.env_file)
    load_env_file(env_file)

    print("Bootstrap preflight")
    print(f"Using env file: {env_file}")

    ok, reason = require_python_311_plus()
    if not ok:
        print(reason)
        return 2

    npm_executable = resolve_npm_executable()
    npm_version_exit = run_command([npm_executable, "--version"], label="Checking npm")
    if npm_version_exit != 0:
        print("npm is required for frontend development.")
        return npm_version_exit

    if not args.skip_init_artifacts:
        paths = ensure_artifact_dirs_from_env()
        print("Initialized artifact directories:")
        for path in paths:
            print(f"  - {path}")

    if _database_bootstrap_enabled():
        docker_exit = run_command(["docker", "--version"], label="Checking docker")
        if docker_exit != 0:
            print("Docker is required for local Postgres bootstrap.")
            return docker_exit

        compose_exit = run_command(
            ["docker", "compose", "up", "-d", "postgres"],
            label="Starting local Postgres",
            cwd=ROOT,
        )
        if compose_exit != 0:
            return compose_exit

        ready_exit = _wait_for_local_postgres()
        if ready_exit != 0:
            print("Local Postgres did not become ready in time.")
            return ready_exit

        migrate_exit = run_command(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            label="Running database migrations",
            cwd=ROOT,
        )
        if migrate_exit != 0:
            return migrate_exit

    if args.with_check:
        exit_code = run_script("scripts/check.py")
        if exit_code != 0:
            return exit_code
    if args.with_smoke:
        exit_code = run_script("scripts/smoke_check.py")
        if exit_code != 0:
            return exit_code

    print("Bootstrap preflight completed.")
    print("Next steps:")
    print(f"  {sys.executable} scripts/dev.py backend")
    print(f"  {sys.executable} scripts/dev.py frontend")
    return 0


def main() -> int:
    args = parse_args()
    if args.command == "bootstrap":
        return run_bootstrap(args)

    command = COMMANDS[args.command]
    forwarded = list(args.args)
    if forwarded and forwarded[0] == "--":
        forwarded = forwarded[1:]
    return run_script(command.script, forwarded)


if __name__ == "__main__":
    raise SystemExit(main())
