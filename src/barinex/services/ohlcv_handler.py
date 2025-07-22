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
DEFAULT_INTERVAL = settings.default_interval  # e.g. "1m"


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
    except Exception as exc:
        logger.error(f"[DB] Unable to load symbols: {exc}")
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
    except Exception as exc:
        logger.error(f"[DB] Error fetching last timestamp for {symbol}: {exc}")
        raise


def run_full_fetch(
    symbol: str,
    start: str,
    end: str,
    symbols: Optional[List[str]] = None
) -> List[tuple]:
    """
    Fetch OHLCV for `symbol` between ISO `start` and `end`, in daily chunks.
    Returns the list of rows fetched (for the last chunk).

    Args:
        symbol: Trading symbol to fetch (e.g. 'BTCUSDT').
        start: ISO-formatted start datetime string.
        end:   ISO-formatted end datetime string.
        symbols: ignored (present for backward compatibility).

    Side-effects:
        - Ensures the table exists.
        - Inserts any missing candles.
    """
    start_dt = datetime.fromisoformat(start)
    end_dt = datetime.fromisoformat(end)
    all_rows: List[tuple] = []

    # Always fetch only the one symbol passed in
    syms = [symbol]

    for sym in syms:
        create_table_if_not_exists(sym)

        last_ts = get_last_timestamp(sym)
        cursor = (
            max(start_dt, last_ts + timedelta(minutes=1))
            if last_ts
            else start_dt
        )

        if cursor >= end_dt:
            logger.info(f"[SKIP] {sym} up to date (last: {last_ts})")
            continue

        while cursor < end_dt:
            chunk_end = min(end_dt, cursor + CHUNK_SIZE)
            try:
                rows = fetch_binance_ohlcv(sym, DEFAULT_INTERVAL, cursor, chunk_end)
            except Exception as exc:
                logger.error(f"[ERROR] Fetch {sym} {cursor}→{chunk_end}: {exc}")
                break

            if not rows:
                logger.warning(f"[WARN] No rows for {sym} {cursor}→{chunk_end}")
                cursor = chunk_end
                continue

            save_ohlcv(sym, rows)
            logger.info(f"[SAVE] {sym}: {len(rows)} rows {cursor}→{chunk_end}")
            all_rows.extend(rows)

            # Advance past the last timestamp fetched
            last_time = rows[-1][0]
            cursor = (
                datetime.fromisoformat(last_time)
                if isinstance(last_time, str)
                else last_time
            ) + timedelta(minutes=1)

    return all_rows
