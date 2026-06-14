"""Read-only SQLite access — the safety-critical core, with ZERO MCP dependency.

This module is deliberately independent of the MCP layer so it can be unit-tested
with nothing but the standard library. The server (server.py) is a thin wrapper.

Two layers of write protection:
  1. The connection is opened in OS read-only mode (`?mode=ro` + `PRAGMA query_only`).
  2. `run_query` statically rejects anything that isn't a single SELECT/WITH.
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Iterator


def connect(path: str) -> sqlite3.Connection:
    """Open a SQLite database in READ-ONLY mode. Any write raises OperationalError."""
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only = ON")  # defense in depth
    return conn


@contextmanager
def session(path: str) -> Iterator[sqlite3.Connection]:
    conn = connect(path)
    try:
        yield conn
    finally:
        conn.close()


def list_tables(conn: sqlite3.Connection) -> list[str]:
    """Return user table names (excludes SQLite internal tables)."""
    rows = conn.execute(
        "SELECT name FROM sqlite_master "
        "WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall()
    return [r["name"] for r in rows]


def _quote_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def describe_table(conn: sqlite3.Connection, table: str) -> list[dict]:
    """Return the column schema for one table."""
    if table not in list_tables(conn):
        raise ValueError(f"unknown table: {table!r}")
    # `table` is validated against the real table list above and quoted -> safe to inline
    # (PRAGMA cannot take a bound parameter).
    rows = conn.execute(f"PRAGMA table_info({_quote_ident(table)})").fetchall()
    return [
        {"name": r["name"], "type": r["type"], "notnull": bool(r["notnull"]), "pk": bool(r["pk"])}
        for r in rows
    ]


def _ensure_read_only(sql: str) -> str:
    stmt = sql.strip().rstrip(";").strip()
    if not stmt:
        raise ValueError("empty query")
    if ";" in stmt:
        raise ValueError("only a single statement is allowed")
    head = stmt.lower()
    if not (head.startswith("select") or head.startswith("with")):
        raise ValueError("only read-only SELECT / WITH queries are allowed")
    return stmt


def run_query(conn: sqlite3.Connection, sql: str, max_rows: int = 100) -> dict:
    """Run a single read-only query and return columns + rows (capped)."""
    stmt = _ensure_read_only(sql)
    max_rows = max(1, min(int(max_rows), 1000))
    cur = conn.execute(stmt)
    cols = [d[0] for d in cur.description] if cur.description else []
    rows = cur.fetchmany(max_rows)
    return {
        "columns": cols,
        "rows": [dict(zip(cols, r)) for r in rows],
        "row_count": len(rows),
        "truncated": len(rows) == max_rows,
    }
