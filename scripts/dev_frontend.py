"""Start frontend dev server with optional root env loading."""

from __future__ import annotations

import argparse
from pathlib import Path

from _common import (
    DEFAULT_ENV_FILE,
    load_env_file,
    require_python_311_plus,
    resolve_npm_executable,
    run_command,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run frontend dev server")
    parser.add_argument(
        "--env-file",
        default=str(DEFAULT_ENV_FILE),
        help="Optional root .env file path (default: .env)",
    )
    parser.add_argument("--host", default=None, help="Vite host override")
    parser.add_argument("--port", type=int, default=None, help="Vite port override")
    parser.add_argument("--open", action="store_true", help="Open browser on start")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    env_file = Path(args.env_file)
    load_env_file(env_file)
    ok, reason = require_python_311_plus()
    if not ok:
        print(reason)
        return 2
    npm_executable = resolve_npm_executable()

    command = [npm_executable, "--prefix", "frontend", "run", "dev", "--"]
    if args.host:
        command.extend(["--host", args.host])
    if args.port:
        command.extend(["--port", str(args.port)])
    if args.open:
        command.append("--open")

    print("Starting frontend dev server...")
    print(f"Using env file: {env_file}")
    return run_command(command)


if __name__ == "__main__":
    raise SystemExit(main())
