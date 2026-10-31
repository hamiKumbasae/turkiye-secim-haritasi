"""SQL safety layer.

Every query the LLM produces passes through `validate_sql` before it reaches the
database. The checks are done on the parsed AST (sqlglot), never with regexes:

1. exactly one statement, and it must parse as MySQL/MariaDB;
2. the root must be a read-only query (SELECT / UNION / WITH ... SELECT);
3. no write/DDL/session nodes anywhere in the tree (INSERT, UPDATE, SET, INTO OUTFILE,
   FOR UPDATE locks, ...);
4. every referenced table is in an allow-list (CTE names are allowed, other schemas
   such as information_schema or mysql are not);
5. dangerous functions (SLEEP, BENCHMARK, LOAD_FILE, GET_LOCK, ...) are rejected;
6. a LIMIT is added to the outermost query (or clamped if it is larger than the cap).

The query that is executed is *re-generated from the AST*, so comments, stacked
statements or anything sqlglot did not understand cannot slip through.

This is one layer of several: the database user only has SELECT, the session is set
to READ ONLY and a statement timeout is enforced (see db.py).
"""
from __future__ import annotations

from dataclasses import dataclass

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError

DIALECT = "mysql"
ALLOWED_TABLES = frozenset({"secim", "birim", "oy"})
ALLOWED_SCHEMAS = frozenset({"", "secim"})

FORBIDDEN_FUNCTIONS = frozenset(
    {
        "SLEEP", "BENCHMARK", "LOAD_FILE", "GET_LOCK", "RELEASE_LOCK", "RELEASE_ALL_LOCKS",
        "IS_FREE_LOCK", "IS_USED_LOCK", "MASTER_POS_WAIT", "SOURCE_POS_WAIT", "SYS_EVAL",
        "SYS_EXEC", "UUID_SHORT", "LAST_INSERT_ID", "ROW_COUNT", "FOUND_ROWS", "DATABASE",
        "USER", "CURRENT_USER", "SESSION_USER", "SYSTEM_USER", "VERSION", "CONNECTION_ID",
        "PASSWORD", "ENCRYPT", "DES_ENCRYPT", "DES_DECRYPT", "COLUMN_CREATE", "NEXTVAL",
        "SETVAL", "LASTVAL", "WAIT_FOR_EXECUTED_GTID_SET", "SCHEMA", "CURRENT_SCHEMA",
        "CURRENT_VERSION", "CURRENT_ROLE",
    }
)

# Node types that must never appear anywhere in the tree.
_FORBIDDEN_NODES: tuple[type[exp.Expression], ...] = tuple(
    t
    for t in (
        getattr(exp, name, None)
        for name in (
            "Insert", "Update", "Delete", "Merge", "Create", "Drop", "Alter", "AlterTable",
            "TruncateTable", "Command", "Set", "SetItem", "Use", "Grant", "Revoke", "Transaction",
            "Commit", "Rollback", "Into", "Lock", "LoadData", "Copy", "Pragma", "Kill", "Analyze",
            "Describe", "Show", "Cache", "Uncache", "Refresh",
        )
    )
    if isinstance(t, type)
)


class UnsafeSQLError(ValueError):
    """Raised when a query fails a safety check. The message is shown to the LLM on retry."""


@dataclass(frozen=True)
class SafeSQL:
    sql: str            # the query that will be executed (regenerated from the AST)
    original: str       # what the LLM produced
    limit: int          # the effective outer LIMIT
    limit_added: bool   # True if we injected or clamped the LIMIT


def _strip(sql: str) -> str:
    sql = sql.strip()
    # tolerate ```sql fences and a single trailing semicolon
    if sql.startswith("```"):
        sql = sql.strip("`")
        if sql.lower().startswith("sql"):
            sql = sql[3:]
    return sql.strip().rstrip(";").strip()


def _function_names(node: exp.Expression) -> set[str]:
    if isinstance(node, exp.Anonymous):
        return {str(node.this).upper()}
    names = {type(node).__name__.upper()}
    if hasattr(node, "sql_name"):
        names.add(node.sql_name().upper())
    return names


def validate_sql(sql: str, max_rows: int = 200) -> SafeSQL:
    if not sql or not sql.strip():
        raise UnsafeSQLError("Boş sorgu.")
    cleaned = _strip(sql)
    try:
        statements = [s for s in sqlglot.parse(cleaned, read=DIALECT) if s is not None]
    except ParseError as e:
        raise UnsafeSQLError(f"SQL ayrıştırılamadı: {str(e).splitlines()[0]}") from e
    except Exception as e:  # sqlglot can raise TokenError etc.
        raise UnsafeSQLError(f"SQL ayrıştırılamadı: {e}") from e
    if len(statements) != 1:
        raise UnsafeSQLError(f"Tek bir SELECT sorgusu olmalı, {len(statements)} ifade bulundu.")
    tree = statements[0]

    if not isinstance(tree, (exp.Select, exp.Union, exp.Intersect, exp.Except)):
        raise UnsafeSQLError(f"Yalnızca SELECT sorgularına izin var ({type(tree).__name__} reddedildi).")

    for node in tree.walk():
        if isinstance(node, _FORBIDDEN_NODES):
            raise UnsafeSQLError(f"İzin verilmeyen ifade: {type(node).__name__}.")
        if isinstance(node, exp.Select) and node.args.get("locks"):
            raise UnsafeSQLError("FOR UPDATE / LOCK IN SHARE MODE kullanılamaz.")
        if isinstance(node, exp.Func):
            bad = _function_names(node) & FORBIDDEN_FUNCTIONS
            if bad:
                raise UnsafeSQLError(f"İzin verilmeyen fonksiyon: {sorted(bad)[0]}.")
        if isinstance(node, (exp.Parameter, exp.SessionParameter)) or (
            isinstance(node, exp.Var) and str(node.this).startswith("@")
        ):
            raise UnsafeSQLError("Değişken/oturum parametresi kullanılamaz.")

    cte_names = {cte.alias_or_name.lower() for cte in tree.find_all(exp.CTE)}
    for table in tree.find_all(exp.Table):
        name = table.name.lower()
        schema = (table.db or "").lower()
        if schema not in ALLOWED_SCHEMAS:
            raise UnsafeSQLError(f"İzin verilmeyen şema: {schema}.")
        if not name:
            raise UnsafeSQLError("Tablo adı çözülemedi.")
        if name in cte_names and not schema:
            continue
        if name not in ALLOWED_TABLES:
            raise UnsafeSQLError(
                f"İzin verilmeyen tablo: {name}. Kullanılabilir tablolar: {', '.join(sorted(ALLOWED_TABLES))}."
            )

    # Outer LIMIT: add when missing, clamp when too large or not a plain number.
    limit_added = False
    limit_node = tree.args.get("limit")
    current = None
    if limit_node is not None:
        value = limit_node.expression if isinstance(limit_node, exp.Limit) else limit_node
        if isinstance(value, exp.Literal) and value.is_int:
            current = int(value.this)
    if current is None or current > max_rows:
        offset = tree.args.get("offset")
        tree = tree.limit(max_rows, copy=False)
        if offset is not None:
            tree.set("offset", offset)
        limit_added = True
        current = max_rows

    final_sql = tree.sql(dialect=DIALECT, comments=False, pretty=True)
    return SafeSQL(sql=final_sql, original=sql, limit=current, limit_added=limit_added)
