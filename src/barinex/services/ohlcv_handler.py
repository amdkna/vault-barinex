# src/barinex/services/ohlcv_handler.py

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional, List

import psycopg2
from psycopg2.extensions import connection as _Connection

from barinex.config.settings import settings
from barinex.db.schema import create_table_if_not_exists
from barinex.db.operations import save_ohlcv, get_ohlcv_data
from barinex.fetcher.binance import fetch_binance_ohlcv

logger = logging.getLogger(__name__)

# How much history to pull per request
CHUNK_SIZE = timedelta(days=1)
DEFAULT_INTERVAL = "1m"


def load_symbols_from_db() -> List[str]:
    """
    Retrieve all trading symbols from `public.symbols`.
    """
    sql = "SELECT symbol FROM public.symbols;"
    try:
        with psycopg2.connect(
            host=settings.pg_host,
            port=settings.pg_port,
            database=settings.pg_db,
            user=settings.pg_user,
            password=settings.pg_password,
        ) as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
                return [row[0] for row in cur.fetchall()]
    except Exception as e:
        logger.error(f"[DB] Unable to load symbols: {e}")
        raise


def get_last_timestamp(symbol: str) -> Optional[datetime]:
    """
    Return the most recent timestamp in `public.ohlcv_<symbol>` or None.
    """
    table = f"public.ohlcv_{symbol.lower()}"
    sql = f"SELECT MAX(time) FROM {table};"
    try:
        with psycopg2.connect(
            host=settings.pg_host,
            port=settings.pg_port,
            database=settings.pg_db,
            user=settings.pg_user,
            password=settings.pg_password,
        ) as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
                return cur.fetchone()[0]
    except Exception as e:
        logger.error(f"[DB] Error fetching last timestamp for {symbol}: {e}")
        raise


def run_full_fetch(start: str, end: str, symbols: Optional[List[str]] = None) -> None:
    """
    Fetch OHLCV for each symbol between ISO `start` and `end`, in daily chunks.

    Args:
        start: ISO-formatted start datetime.
        end:   ISO-formatted end datetime.
        symbols: optional list of symbols; if None, all from DB.

    Side-effects:
        - Ensures each table exists
        - Inserts any missing candles
    """
    start_dt = datetime.fromisoformat(start)
    end_dt = datetime.fromisoformat(end)
    symbols = symbols or load_symbols_from_db()

    for symbol in symbols:
        create_table_if_not_exists(symbol)

        last_ts = get_last_timestamp(symbol)
        if last_ts:
            cursor = max(start_dt, last_ts + timedelta(minutes=1))
        else:
            cursor = start_dt

        if cursor >= end_dt:
            logger.info(f"[SKIP] {symbol} up to date (last: {last_ts})")
            continue

        while cursor < end_dt:
            chunk_end = min(end_dt, cursor + CHUNK_SIZE)
            try:
                rows = fetch_binance_ohlcv(symbol, DEFAULT_INTERVAL, cursor, chunk_end)
            except Exception as e:
                logger.error(f"[ERROR] Fetch {symbol} {cursor}→{chunk_end}: {e}")
                break

            if not rows:
                logger.info(f"[WARN] No rows for {symbol} {cursor}→{chunk_end}")
                cursor = chunk_end
                continue

            save_ohlcv(symbol, rows)
            logger.info(f"[SAVE] {symbol}: {len(rows)} rows {cursor}→{chunk_end}")

            # Advance to one minute past the last timestamp fetched
            last_ts_val = rows[-1][0]
            cursor = (
                datetime.fromisoformat(last_ts_val)
                if isinstance(last_ts_val, str)
                else last_ts_val
            ) + timedelta(minutes=1)

    logger.info("🎉 All symbols backfilled.")
