from __future__ import annotations

import logging
from datetime import datetime
from typing import List

import pandas as pd
import psycopg2
from psycopg2.extensions import connection as _Connection

from barinex.config.settings import settings
from barinex.exceptions import DatabaseError


def _get_connection() -> _Connection:
    """
    Create a new Postgres connection using credentials from settings.
    Raises DatabaseError on failure.
    """
    try:
        return psycopg2.connect(
            host=settings.pg_host,
            port=settings.pg_port,
            database=settings.pg_db,
            user=settings.pg_user,
            password=settings.pg_password,
        )
    except Exception as e:
        logging.error(f"[DB ERROR] Connection failed: {e}")
        raise DatabaseError(f"Unable to connect to DB: {e}")


def get_ohlcv_data(symbol: str, start: datetime, end: datetime) -> pd.DataFrame:
    """
    Fetch OHLCV rows for a given symbol between `start` and `end`.
    
    Args:
        symbol: Trading symbol (e.g. 'BTCUSDT').
        start: Start timestamp (inclusive).
        end: End timestamp (inclusive).
    
    Returns:
        DataFrame with columns [time, open, high, low, close, volume], sorted ascending.
    
    Raises:
        DatabaseError: on any read or SQL error.
    """
    table = f"public.ohlcv_{symbol.lower()}"
    sql = (
        "SELECT time, open, high, low, close, volume "
        f"FROM {table} "
        "WHERE time BETWEEN %s AND %s "
        "ORDER BY time ASC"
    )
    try:
        with _get_connection() as conn:
            df = pd.read_sql(sql, conn, params=(start, end))
        return df
    except Exception as e:
        logging.error(f"[DB ERROR] Query failed for {symbol}: {e}")
        raise DatabaseError(f"Error fetching OHLCV data for {symbol}: {e}")


def save_ohlcv(symbol: str, ohlcv: List[tuple]) -> None:
    """
    Bulk-insert OHLCV data into the PostgreSQL table.
    
    Args:
        symbol: Trading symbol (e.g. 'BTCUSDT').
        ohlcv: List of tuples matching (time, open, high, low, close, volume).
    
    Raises:
        DatabaseError: on any write or SQL error.
    """
    table = f"public.ohlcv_{symbol.lower()}"
    insert_sql = (
        f"INSERT INTO {table} (time, open, high, low, close, volume) "
        "VALUES (%s, %s, %s, %s, %s, %s) "
        "ON CONFLICT (time) DO NOTHING;"
    )
    try:
        with _get_connection() as conn:
            with conn.cursor() as cur:
                cur.executemany(insert_sql, ohlcv)
            conn.commit()
        logging.info(f"[DB WRITE] Inserted {len(ohlcv)} rows into {table}")
    except Exception as e:
        logging.error(f"[DB ERROR] Insert failed for {symbol}: {e}")
        raise DatabaseError(f"Error saving OHLCV data for {symbol}: {e}")
