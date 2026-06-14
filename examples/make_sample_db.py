"""Create examples/sample.db so you can try the server in 30 seconds.

    python examples/make_sample_db.py
    SQLITE_DB_PATH=examples/sample.db python -m mcp_sqlite.server
"""
import os
import sqlite3

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "sample.db")


def main() -> None:
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(
        """
        CREATE TABLE customers (
            id   INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            city TEXT
        );
        CREATE TABLE orders (
            id          INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL REFERENCES customers(id),
            product     TEXT NOT NULL,
            amount      REAL NOT NULL
        );
        INSERT INTO customers (name, city) VALUES
            ('Alice', 'Hanoi'), ('Bob', 'Hue'), ('Cara', 'Ho Chi Minh City');
        INSERT INTO orders (customer_id, product, amount) VALUES
            (1, 'Keyboard', 49.0), (1, 'Monitor', 220.0),
            (2, 'Mouse', 19.5), (3, 'Laptop', 1200.0), (3, 'Dock', 150.0);
        """
    )
    conn.commit()
    conn.close()
    print(f"Created {DB_PATH}")
    print("Try:  SQLITE_DB_PATH=examples/sample.db python -m mcp_sqlite.server")


if __name__ == "__main__":
    main()
