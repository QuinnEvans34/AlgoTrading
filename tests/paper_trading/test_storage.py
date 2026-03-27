import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from paper_trading import PaperAccountConfig  # noqa: E402
from paper_trading.storage import PaperTradingStorage  # noqa: E402


class PaperTradingStorageTests(unittest.TestCase):
    def test_bootstrap_and_reload(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            storage = PaperTradingStorage(Path(tempdir))
            config = PaperAccountConfig(initial_cash=50_000.0)
            state = storage.load_or_initialize(config)
            self.assertTrue(storage.state_path.exists())
            self.assertEqual(state.account.cash, 50_000.0)

            loaded = storage.load_or_initialize(PaperAccountConfig(initial_cash=1.0))
            self.assertEqual(loaded.account.cash, 50_000.0)
            self.assertEqual(loaded.config.initial_cash, 50_000.0)

    def test_reset_state_overwrites_existing(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            storage = PaperTradingStorage(Path(tempdir))
            storage.load_or_initialize(PaperAccountConfig(initial_cash=10_000.0))
            reset = storage.reset_state(PaperAccountConfig(initial_cash=75_000.0))
            self.assertEqual(reset.account.cash, 75_000.0)
            loaded = storage.load_or_initialize(PaperAccountConfig(initial_cash=1.0))
            self.assertEqual(loaded.account.cash, 75_000.0)


if __name__ == "__main__":
    unittest.main()

