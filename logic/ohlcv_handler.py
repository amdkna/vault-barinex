import logging
from datetime import datetime, timedelta
import psycopg2

from fetcher.binance import fetch_binance_ohlcv
from db.schema     import create_table_if_not_exists
from db.operations import save_ohlcv
from config.settings import PG_CONFIG

# Chunk size for each fetch iteration
CHUNK_SIZE = timedelta(days=1)
# OHLCV interval
INTERVAL   = "1m"

def load_symbols_from_db() -> list[str]:
    """
    Fetch list of symbols (e.g. ['BTCUSDT','ETHUSDT',...]) from public.symbols.
    """
    with psycopg2.connect(**PG_CONFIG) as conn, conn.cursor() as cur:
        cur.execute("SELECT symbol FROM public.symbols;")
        return [row[0] for row in cur.fetchall()]


def get_last_timestamp(symbol: str) -> datetime | None:
    """
    Returns the latest `time` value already in public.ohlcv_<symbol> table,
    or None if table is empty.
    """
    table = f"public.ohlcv_{symbol.lower()}"
    query = f"SELECT MAX(time) FROM {table};"
    with psycopg2.connect(**PG_CONFIG) as conn, conn.cursor() as cur:
        cur.execute(query)
        result = cur.fetchone()[0]
        return result


def run_full_fetch(start: str, end: str):
    """
    Fetch OHLCV data from `start` to `end` for each symbol,
    auto-creating tables, skipping already-fetched periods.
    """
    start_dt = datetime.fromisoformat(start)
    end_dt   = datetime.fromisoformat(end)

    symbols = load_symbols_from_db()
    for symbol in symbols:
        # Ensure per-symbol table exists
        create_table_if_not_exists(symbol)

        # Determine where to start: max of provided start and DB's last timestamp + 1 minute
        last_ts = get_last_timestamp(symbol)
        if last_ts:
            # avoid overlap: start one minute after last stored
            db_start = last_ts + timedelta(minutes=1)
            current = max(start_dt, db_start)
        else:
            current = start_dt

        if current >= end_dt:
            logging.info(f"[SKIP] {symbol} up to date (last: {last_ts})")
            continue

        while current < end_dt:
            chunk_end = min(end_dt, current + CHUNK_SIZE)

            # Fetch a chunk of data
            try:
                rows = fetch_binance_ohlcv(symbol, INTERVAL, current, chunk_end)
            except Exception as e:
                logging.error(f"[ERROR] Fetch error for {symbol} from {current} to {chunk_end}: {e}")
                break

            if not rows:
                logging.info(f"[WARN] No rows for {symbol} between {current} and {chunk_end}")
                current = chunk_end
                continue

            # Save fetched rows into the DB
            save_ohlcv(symbol, INTERVAL, rows)
            logging.info(f"[SAVE] {symbol}: {len(rows)} rows from {current} to {chunk_end}")

            # Determine last timestamp and advance to avoid overlap
            raw_ts = rows[-1][0]
            if isinstance(raw_ts, str):
                last_fetched = datetime.fromisoformat(raw_ts)
            else:
                last_fetched = raw_ts

            current = last_fetched + timedelta(minutes=1)

    logging.info("🎉 All symbols backfilled.")
