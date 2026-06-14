"""A read-only SQLite MCP server (Model Context Protocol).

Exposes all three MCP primitives:
  - tools:     list_tables, describe_table, query
  - resource:  schema://tables  (the full DB schema as text)
  - prompt:    explore_database  (a ready-made exploration prompt)

Run:
    SQLITE_DB_PATH=/path/to/your.db  python -m mcp_sqlite.server
"""
from __future__ import annotations

import os

from mcp.server.fastmcp import FastMCP

from mcp_sqlite.db import describe_table as _describe
from mcp_sqlite.db import list_tables as _list
from mcp_sqlite.db import run_query as _run
from mcp_sqlite.db import session

mcp = FastMCP("sqlite-readonly")


def _db_path() -> str:
    path = os.environ.get("SQLITE_DB_PATH")
    if not path:
        raise RuntimeError("Set the SQLITE_DB_PATH environment variable to your .db file.")
    return path


@mcp.tool()
def list_tables() -> list[str]:
    """List all tables in the database."""
    with session(_db_path()) as conn:
        return _list(conn)


@mcp.tool()
def describe_table(table: str) -> list[dict]:
    """Get the column schema (name, type, nullability, primary key) for one table.

    Args:
        table: Table name, as returned by list_tables.
    """
    with session(_db_path()) as conn:
        return _describe(conn, table)


@mcp.tool()
def query(sql: str, max_rows: int = 100) -> dict:
    """Run a READ-ONLY SQL query (a single SELECT or WITH statement) and return the rows.

    Writes (INSERT/UPDATE/DELETE/DROP/...) are rejected. Results are capped at max_rows.

    Args:
        sql: A single SELECT or WITH statement.
        max_rows: Maximum number of rows to return (1-1000, default 100).
    """
    with session(_db_path()) as conn:
        return _run(conn, sql, max_rows)


@mcp.resource("schema://tables")
def schema_resource() -> str:
    """The full schema of the database, as readable text."""
    with session(_db_path()) as conn:
        tables = _list(conn)
        if not tables:
            return "(no tables)"
        lines = []
        for t in tables:
            cols = ", ".join(f"{c['name']} {c['type']}" for c in _describe(conn, t))
            lines.append(f"{t}({cols})")
        return "\n".join(lines)


@mcp.prompt()
def explore_database() -> str:
    """A ready-made prompt to explore an unfamiliar database."""
    return (
        "List the tables in this database, describe the most interesting ones, "
        "then run a few read-only queries to summarize what data it contains."
    )


def main() -> None:
    mcp.run()  # stdio transport by default


if __name__ == "__main__":
    main()
