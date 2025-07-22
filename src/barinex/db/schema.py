from __future__ import annotations

import logging

import psycopg2
from psycopg2.extensions import connection as _Connection

from barinex.config.settings import settings
from barinex.exceptions import DatabaseError


def create_table_if_not_exists(symbol: str) -> None:
    """
    Ensure the PostgreSQL table `public.ohlcv_<symbol>` exists.
    
    Args:
        symbol: Trading symbol (e.g. 'ETHUSDT').
    
    Raises:
        DatabaseError: on any SQL error.
    """
    table = f"public.ohlcv_{symbol.lower()}"
    ddl = (
        f"CREATE TABLE IF NOT EXISTS {table} ("
        "time TIMESTAMPTZ PRIMARY KEY, "
        "open NUMERIC NOT NULL, "
        "high NUMERIC NOT NULL, "
        "low NUMERIC NOT NULL, "
        "close NUMERIC NOT NULL, "
        "volume NUMERIC NOT NULL"
        ");"
    )
    try:
        conn: _Connection = psycopg2.connect(
            host=settings.pg_host,
            port=settings.pg_port,
            database=settings.pg_db,
            user=settings.pg_user,
            password=settings.pg_password,
        )
        with conn:
            with conn.cursor() as cur:
                cur.execute(ddl)
        logging.info(f"[DB SCHEMA] Verified table exists: {table}")
    except Exception as e:
        logging.error(f"[DB ERROR] Failed to create/verify table {table}: {e}")
        raise DatabaseError(f"Error creating table for {symbol}: {e}")
