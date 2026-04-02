import argparse
import importlib.util
import os
import pathlib
import sys
import unittest
from unittest.mock import patch


ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPTS_DIR = ROOT / "scripts"
DEV_PATH = ROOT / "scripts" / "dev.py"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def load_module():
    module_name = "scripts_dev"
    spec = importlib.util.spec_from_file_location(module_name, DEV_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class DevEntrypointTests(unittest.TestCase):
    def test_expected_commands_registered(self) -> None:
        module = load_module()
        self.assertIn("backend", module.COMMANDS)
        self.assertIn("frontend", module.COMMANDS)
        self.assertIn("check", module.COMMANDS)
        self.assertIn("smoke", module.COMMANDS)
        self.assertIn("demo", module.COMMANDS)

    def test_bootstrap_fails_when_python_too_old(self) -> None:
        module = load_module()
        args = argparse.Namespace(
            env_file=str(ROOT / ".env"),
            skip_init_artifacts=False,
            with_check=False,
            with_smoke=False,
        )
        with patch.object(module, "require_python_311_plus", return_value=(False, "old")):
            exit_code = module.run_bootstrap(args)
        self.assertEqual(exit_code, 2)

    def test_bootstrap_runs_preflight_and_artifact_init(self) -> None:
        module = load_module()
        args = argparse.Namespace(
            env_file=str(ROOT / ".env"),
            skip_init_artifacts=False,
            with_check=False,
            with_smoke=False,
        )
        with patch.object(module, "load_env_file") as load_env:
            with patch.object(module, "require_python_311_plus", return_value=(True, "")):
                with patch.object(module, "resolve_npm_executable", return_value="npm"):
                    with patch.object(module, "run_command", return_value=0) as run_command:
                        with patch.object(module, "ensure_artifact_dirs_from_env", return_value=[]):
                            with patch.dict(os.environ, {"DATABASE_ENABLED": "false"}, clear=False):
                                exit_code = module.run_bootstrap(args)
        self.assertEqual(exit_code, 0)
        load_env.assert_called_once()
        run_command.assert_called_once()

    def test_bootstrap_starts_postgres_and_runs_migrations_when_db_enabled(self) -> None:
        module = load_module()
        args = argparse.Namespace(
            env_file=str(ROOT / ".env"),
            skip_init_artifacts=False,
            with_check=False,
            with_smoke=False,
        )
        with patch.object(module, "load_env_file"):
            with patch.object(module, "require_python_311_plus", return_value=(True, "")):
                with patch.object(module, "resolve_npm_executable", return_value="npm"):
                    with patch.object(module, "ensure_artifact_dirs_from_env", return_value=[]):
                        with patch.object(module, "run_command", return_value=0) as run_command:
                            with patch.dict(
                                os.environ,
                                {
                                    "DATABASE_ENABLED": "true",
                                    "DATABASE_URL": "postgresql+psycopg://capstone:capstone@127.0.0.1:5432/capstone",
                                },
                                clear=False,
                            ):
                                exit_code = module.run_bootstrap(args)
        self.assertEqual(exit_code, 0)
        self.assertGreaterEqual(run_command.call_count, 5)

    def test_main_dispatches_to_script_command(self) -> None:
        module = load_module()
        parsed = argparse.Namespace(command="backend", args=["--port", "8001"])
        with patch.object(module, "parse_args", return_value=parsed):
            with patch.object(module, "run_script", return_value=0) as run_script:
                exit_code = module.main()
        self.assertEqual(exit_code, 0)
        run_script.assert_called_once_with("scripts/dev_backend.py", ["--port", "8001"])


if __name__ == "__main__":
    unittest.main()
