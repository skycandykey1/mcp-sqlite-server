"""Offline tests for the read-only safety core — stdlib only, no `mcp`, no API key."""
import os
import sqlite3
import tempfile

from mcp_sqlite import db


def _make_db() -> str:
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT NOT NULL, city TEXT);
        INSERT INTO customers (name, city) VALUES ('Alice','Hanoi'),('Bob','Hue'),('Cara','HCMC');
        """
    )
    conn.commit()
    conn.close()
    return path


def test_list_tables():
    with db.session(_make_db()) as c:
        assert db.list_tables(c) == ["customers"]


def test_describe_table():
    with db.session(_make_db()) as c:
        cols = {col["name"] for col in db.describe_table(c, "customers")}
        assert cols == {"id", "name", "city"}


def test_describe_unknown_table_errors():
    with db.session(_make_db()) as c:
        try:
            db.describe_table(c, "nope")
            assert False, "should have raised"
        except ValueError:
            pass


def test_select_returns_rows():
    with db.session(_make_db()) as c:
        out = db.run_query(c, "SELECT name FROM customers ORDER BY name")
        assert out["columns"] == ["name"]
        assert [r["name"] for r in out["rows"]] == ["Alice", "Bob", "Cara"]


def test_query_rejects_writes():
    bad = [
        "INSERT INTO customers (name) VALUES ('x')",
        "UPDATE customers SET name = 'x'",
        "DELETE FROM customers",
        "DROP TABLE customers",
        "  update customers set city='y'",
    ]
    with db.session(_make_db()) as c:
        for stmt in bad:
            try:
                db.run_query(c, stmt)
                assert False, f"should have rejected: {stmt}"
            except ValueError:
                pass


def test_query_rejects_multiple_statements():
    with db.session(_make_db()) as c:
        try:
            db.run_query(c, "SELECT 1; SELECT 2")
            assert False, "should have rejected multiple statements"
        except ValueError:
            pass


def test_readonly_connection_blocks_writes_even_if_guard_bypassed():
    # Defense in depth: bypass the statement guard and hit the connection directly.
    with db.session(_make_db()) as c:
        try:
            c.execute("INSERT INTO customers (name) VALUES ('x')")
            assert False, "read-only connection should refuse writes"
        except sqlite3.OperationalError:
            pass


def test_query_truncates_to_max_rows():
    with db.session(_make_db()) as c:
        out = db.run_query(c, "SELECT * FROM customers", max_rows=2)
        assert out["row_count"] == 2
        assert out["truncated"] is True
