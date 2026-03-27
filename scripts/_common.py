"""Shared helpers for repository developer scripts."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
from typing import Iterable, Mapping


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ENV_FILE = ROOT / ".env"


def load_env_file(path: Path, *, overwrite: bool = False) -> None:
    """Load simple KEY=VALUE pairs from an env file into os.environ."""
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        parsed = value.strip().strip("'").strip('"')
        if overwrite or key not in os.environ:
            os.environ[key] = parsed


def require_python_311_plus() -> tuple[bool, str]:
    if sys.version_info < (3, 11):
        version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        return False, f"Python 3.11+ required, found {version}"
    return True, ""


def resolve_npm_executable() -> str:
    from shutil import which

    return which("npm") or which("npm.cmd") or "npm"


def ensure_artifact_dirs_from_env() -> list[Path]:
    """Create known local artifact directories derived from current env/settings keys."""
    run_dir = Path(os.getenv("API_DEFAULT_RUN_OUTPUT_DIR", "artifacts/research_runs"))
    paper_dir = Path(os.getenv("API_DEFAULT_PAPER_TRADING_DIR", "artifacts/paper_trading"))
    live_log_path = Path(
        os.getenv("LIVE_EXECUTION_ATTEMPT_LOG_PATH", "artifacts/live_execution/attempts.jsonl")
    )
    paths = [ROOT / run_dir, ROOT / paper_dir, ROOT / live_log_path.parent]
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)
    return paths


def build_command_env(
    *,
    extra_env: Mapping[str, str] | None = None,
    prepend_src_to_pythonpath: bool = False,
) -> dict[str, str]:
    env = os.environ.copy()
    if prepend_src_to_pythonpath:
        src_path = str(ROOT / "src")
        current_pythonpath = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = (
            src_path
            if not current_pythonpath
            else f"{src_path}{os.pathsep}{current_pythonpath}"
        )
    if extra_env:
        env.update(extra_env)
    return env


def run_command(
    command: list[str],
    *,
    cwd: Path | None = None,
    env: Mapping[str, str] | None = None,
    label: str | None = None,
) -> int:
    if label:
        print(label)
    print("Command:", " ".join(command))
    completed = subprocess.run(command, cwd=cwd or ROOT, env=env, check=False)
    return completed.returncode


def print_paths(title: str, paths: Iterable[Path]) -> None:
    print(title)
    for path in paths:
        print(f"  - {path}")
