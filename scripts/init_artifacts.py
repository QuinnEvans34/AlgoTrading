"""Create local artifact directories used by the platform."""

from __future__ import annotations

from _common import DEFAULT_ENV_FILE, ensure_artifact_dirs_from_env, load_env_file


def main() -> int:
    load_env_file(DEFAULT_ENV_FILE)
    print("Initializing local artifact directories...")
    paths = ensure_artifact_dirs_from_env()
    for path in paths:
        print(f"  - {path}")
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
