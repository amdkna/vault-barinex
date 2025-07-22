#!/usr/bin/env python3
from __future__ import annotations

import json
import logging
from functools import wraps
from pathlib import Path
from time import sleep
from datetime import datetime, timezone
from typing import Any, Dict, List

import psycopg2

from barinex.config.settings import settings
from barinex.exceptions import FetchError, DatabaseError
from barinex.services.ohlcv_handler import run_full_fetch
from barinex.db.operations import save_ohlcv

# Set up logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
log_dir = settings.log_file.parent
log_dir.mkdir(parents=True, exist_ok=True)
file_handler = logging.FileHandler(settings.log_file, encoding="utf-8")
console_handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
for h in (file_handler, console_handler):
    h.setFormatter(formatter)
    logger.addHandler(h)

# Paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATE_FILE = PROJECT_ROOT / "fetcher" / "last_fetch.json"


def retry_forever(interval: int = 10):
    """
    Decorator to retry a function indefinitely on exception.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            while True:
                try:
                    return fn(*args, **kwargs)
                except Exception as exc:
                    logger.error(f"[RETRY] {fn.__name__} failed: {exc}. Sleeping {interval}s…")
                    sleep(interval)
        return wrapper
    return decorator


def load_state() -> Dict[str, str]:
    """
    Load last-fetch timestamps from the state file.
    """
    try:
        if STATE_FILE.exists():
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning(f"[STATE] Could not load state: {exc}")
    return {}


def save_state(state: Dict[str, str]) -> None:
    """
    Persist last-fetch timestamps to the state file.
    """
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    except Exception as exc:
        logger.error(f"[STATE] Could not save state: {exc}")


def get_symbols_first_dates() -> List[tuple[str, datetime]]:
    """
    Read (symbol, first_date) rows from `public.symbols`.
    """
    sql = "SELECT symbol, first_date FROM public.symbols;"
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
                return cur.fetchall()
    except Exception as exc:
        logger.error(f"[DB] Error fetching symbols: {exc}")
        raise DatabaseError(f"Failed to fetch symbols: {exc}")


@retry_forever(interval=10)
def run_ohlcv_backfill() -> None:
    """
    Main backfill loop: for each symbol, fetch missing OHLCV data and save it.
    """
    logger.info("[START] OHLCV backfill")
    now = datetime.now(timezone.utc)
    state = load_state()

    for symbol, first_dt in get_symbols_first_dates():
        last_iso = state.get(symbol)
        start_iso = last_iso if last_iso else first_dt.isoformat()
        logger.info(f"[FETCH] {symbol} since {start_iso} → {now.isoformat()}")

        try:
            rows = run_full_fetch(
                symbol=symbol,
                start=start_iso,
                end=now.isoformat()
            )
            save_ohlcv(symbol=symbol, ohlcv=rows)
        except FetchError as fe:
            logger.error(f"[FETCH ERROR] {symbol}: {fe}")
            continue
        except DatabaseError as de:
            logger.error(f"[DB ERROR] {symbol}: {de}")
            continue

        # Update state
        state[symbol] = now.isoformat()
        save_state(state)
        logger.info(f"[DONE] {symbol} backfill complete")

    logger.info("[FINISH] All symbols backfilled.")


if __name__ == "__main__":
    run_ohlcv_backfill()
