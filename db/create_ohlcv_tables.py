#!/usr/bin/env python3
"""
Utility script to create per-symbol OHLCV tables in PostgreSQL.
Writes a table for each symbol found in public.symbols:
  public.ohlcv_<symbol_lowercase>
"""
import os
import sys

# ─── Make project root importable ──────────────────────────────────────────────
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
# ──────────────────────────────────────────────────────────────────────────────

from config.settings import PG_CONFIG
import psycopg2


def create_tables():
    conn = psycopg2.connect(**PG_CONFIG)
    # Use autocommit to avoid explicit commit calls
    conn.autocommit = True

    with conn.cursor() as cur:
        # Fetch all symbols
        cur.execute("SELECT symbol FROM public.symbols;")
        rows = cur.fetchall()

        if not rows:
            print("No symbols found in public.symbols table.")
            return

        for (symbol,) in rows:
            table_name = f"public.ohlcv_{symbol.lower()}"
            ddl = f"""
CREATE TABLE IF NOT EXISTS {table_name} (
    time   TIMESTAMPTZ NOT NULL PRIMARY KEY,
    open   NUMERIC     NOT NULL,
    high   NUMERIC     NOT NULL,
    low    NUMERIC     NOT NULL,
    close  NUMERIC     NOT NULL,
    volume NUMERIC     NOT NULL
);
"""
            try:
                cur.execute(ddl)
                print(f"✔ Created or verified table: {table_name}")
            except Exception as e:
                print(f"✖ Failed to create table {table_name}: {e}")

    conn.close()


if __name__ == "__main__":
    create_tables()
