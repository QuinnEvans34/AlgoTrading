import os
import unittest
import importlib.util
import pathlib


def load_tests(loader: unittest.TestLoader, tests, pattern):  # noqa: ANN001
    api_dir = pathlib.Path(os.path.dirname(__file__)) / "api"
    suite = unittest.TestSuite()
    for test_file in sorted(api_dir.glob("test_*.py")):
        module_name = f"_dynamic_{test_file.stem}"
        spec = importlib.util.spec_from_file_location(module_name, test_file)
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        suite.addTests(loader.loadTestsFromModule(module))
    return suite

