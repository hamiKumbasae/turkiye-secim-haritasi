"""Read-only query execution against MariaDB/MySQL."""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Protocol

from .config import Settings


@dataclass
class QueryResult:
    columns: list[str]
    rows: list[list[Any]]
    truncated: bool = False          # more rows existed than max_rows
    elapsed_ms: int = 0
    extra: dict = field(default_factory=dict)

    @property
    def row_count(self) -> int:
        return len(self.rows)


class QueryError(RuntimeError):
    """Database rejected or failed the query. Message is passed to the LLM for one retry."""


class Database(Protocol):
    def run(self, sql: str, max_rows: int) -> QueryResult: ...


def to_jsonable(value: Any) -> Any:
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() and value.as_tuple().exponent >= 0 else float(value)
    if isinstance(value, (dt.date, dt.datetime)):
        return value.isoformat()
    if isinstance(value, bytes):
        return value.decode("utf-8", "replace")
    return value


class MariaDB:
    """One short-lived connection per query; the session is forced READ ONLY with a timeout.

    Even if the safety layer had a bug, the server would refuse writes because
    (a) the chatbot's DB user only has SELECT (sql/readonly_user.sql) and
    (b) every query runs inside a READ ONLY transaction.
    """

    def __init__(self, settings: Settings):
        import pymysql  # imported lazily so tests without a DB driver still work

        self._pymysql = pymysql
        self.s = settings
        self._flavour: str | None = None

    def _connect(self):
        return self._pymysql.connect(
            host=self.s.db_host, port=self.s.db_port, user=self.s.db_user, password=self.s.db_password,
            database=self.s.db_name, charset="utf8mb4", autocommit=False,
            connect_timeout=5, read_timeout=self.s.statement_timeout_s + 5,
        )

    def _apply_limits(self, cur) -> None:
        if self._flavour is None:
            cur.execute("SELECT VERSION()")
            self._flavour = "mariadb" if "mariadb" in cur.fetchone()[0].lower() else "mysql"
        t = int(self.s.statement_timeout_s)
        if self._flavour == "mariadb":
            cur.execute(f"SET SESSION max_statement_time = {t}")
        else:
            cur.execute(f"SET SESSION max_execution_time = {t * 1000}")
        cur.execute("SET SESSION TRANSACTION READ ONLY")
        cur.execute("START TRANSACTION READ ONLY")

    def ping(self) -> bool:
        try:
            conn = self._connect()
            conn.close()
            return True
        except Exception:
            return False

    def run(self, sql: str, max_rows: int) -> QueryResult:
        import time

        start = time.perf_counter()
        try:
            conn = self._connect()
        except Exception as e:
            raise QueryError(f"Veritabanına bağlanılamadı: {e}") from e
        try:
            with conn.cursor() as cur:
                self._apply_limits(cur)
                cur.execute(sql)
                columns = [d[0] for d in (cur.description or [])]
                raw = cur.fetchmany(max_rows + 1)
            conn.rollback()
        except self._pymysql.MySQLError as e:
            code, msg = (e.args + ("",))[:2] if e.args else ("", str(e))
            if code in (1969, 3024):
                msg = f"Sorgu {self.s.statement_timeout_s} sn zaman aşımına uğradı; daha dar bir sorgu yaz."
            raise QueryError(f"[{code}] {msg}") from e
        finally:
            conn.close()
        rows = [[to_jsonable(v) for v in r] for r in raw[:max_rows]]
        return QueryResult(
            columns=columns, rows=rows, truncated=len(raw) > max_rows,
            elapsed_ms=int((time.perf_counter() - start) * 1000),
        )
