import os
import sys
import tempfile
import unittest
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class MigrationTests(unittest.TestCase):
    def test_upgrade_head_creates_research_run_metadata_table(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            db_path = Path(tempdir) / "migration.sqlite3"
            config = Config(str(ROOT / "alembic.ini"))
            config.set_main_option("script_location", str(ROOT / "alembic"))
            config.set_main_option(
                "sqlalchemy.url",
                f"sqlite+pysqlite:///{db_path.as_posix()}",
            )
            command.upgrade(config, "head")

            engine = create_engine(f"sqlite+pysqlite:///{db_path.as_posix()}")
            inspector = inspect(engine)
            self.assertIn("research_run_metadata", inspector.get_table_names())
            columns = {column["name"] for column in inspector.get_columns("research_run_metadata")}
            self.assertIn("artifact_fingerprint", columns)
            self.assertIn("last_synced_at", columns)
            engine.dispose()
