import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from secim_chatbot.db import QueryError, QueryResult  # noqa: E402


class FakeDB:
    """In-memory Database: maps a substring of the SQL to a result (or an exception)."""

    def __init__(self, routes=None, default=None):
        self.routes = routes or []          # list of (substring, QueryResult | Exception)
        self.default = default or QueryResult(columns=["x"], rows=[[1]])
        self.executed: list[str] = []

    def run(self, sql, max_rows):
        self.executed.append(sql)
        for needle, outcome in self.routes:
            if needle in sql:
                if isinstance(outcome, Exception):
                    raise outcome
                return outcome
        return self.default

    def ping(self):
        return True


@pytest.fixture
def fake_db():
    return FakeDB()


def real_db_or_skip():
    """MariaDB with the loaded data, if reachable (local dev / CI with DB); otherwise skip."""
    from secim_chatbot.config import Settings
    from secim_chatbot.db import MariaDB

    s = Settings(
        db_host=os.environ.get("DB_HOST", "127.0.0.1"),
        db_user=os.environ.get("DB_USER", "secim_okur"),
        db_password=os.environ.get("DB_PASSWORD", "okur-yerel"),
    )
    db = MariaDB(s)
    if not db.ping():
        pytest.skip("veritabanı erişilemez")
    return db


__all__ = ["FakeDB", "QueryError", "QueryResult", "real_db_or_skip"]
