"""Start backend API server with predictable local defaults."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

from _common import (
    DEFAULT_ENV_FILE,
    ROOT,
    ensure_artifact_dirs_from_env,
    load_env_file,
    require_python_311_plus,
    run_command,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run backend API server")
    parser.add_argument(
        "--env-file",
        default=str(DEFAULT_ENV_FILE),
        help="Optional .env file path (default: .env)",
    )
    parser.add_argument(
        "--host",
        default=None,
        help="API host override (default from env/API defaults)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="API port override (default from env/API defaults)",
    )
    parser.add_argument(
        "--no-reload",
        action="store_true",
        help="Disable uvicorn auto-reload",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    env_file = Path(args.env_file)
    load_env_file(env_file)
    ok, reason = require_python_311_plus()
    if not ok:
        print(reason)
        return 2
    ensure_artifact_dirs_from_env()

    host = args.host or os.getenv("API_HOST", "127.0.0.1")
    port = args.port or int(os.getenv("API_PORT", "8000"))
    if port <= 0 or port > 65535:
        print(f"Invalid API port: {port}")
        return 2

    command = [
        sys.executable,
        "-m",
        "uvicorn",
        "api.app:app",
        "--app-dir",
        "src",
        "--host",
        host,
        "--port",
        str(port),
    ]
    if not args.no_reload:
        command.append("--reload")

    print(f"Starting backend API on http://{host}:{port}")
    print(f"Using env file: {env_file}")
    return run_command(command)


if __name__ == "__main__":
    raise SystemExit(main())
