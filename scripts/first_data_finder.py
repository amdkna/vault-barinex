#!/usr/bin/env python3
"""
scripts/first_data_finder.py

Find and record the first available 1m OHLCV date for each symbol listed
in config/symbols.yml, saving results into the `symbols` table.
Handles permission errors by printing guidance on granting privileges.
"""

import os
import sys
import time
import datetime
import yaml
import requests
import psycopg2
from psycopg2 import sql, errors

# ─── Make project root importable ──────────────────────────────────────────────
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
# ──────────────────────────────────────────────────────────────────────────────

from config.settings import PG_CONFIG, BINANCE_API_URL, DEFAULT_INTERVAL

# Parameters
TIMEOUT = 5  # seconds per HTTP request
TABLE_NAME = sql.Identifier('public', 'symbols')  # schema-qualified


def load_symbols(path=None) -> list:
    """Load base symbols from YAML and append 'USDT', uppercased."""
    cfg_path = path or os.path.join(BASE_DIR, "config", "symbols.yml")
    if not os.path.exists(cfg_path):
        raise FileNotFoundError(f"Symbols file not found: {cfg_path}")
    with open(cfg_path, "r") as f:
        data = yaml.safe_load(f)
    raw = data.get("symbols", []) if isinstance(data, dict) else []
    return [sym.upper() + "USDT" for sym in raw]


def has_data_for_day(symbol: str, date: datetime.date) -> bool:
    """Return True if Binance has at least one bar for symbol on that UTC date."""
    day_start = datetime.datetime(date.year, date.month, date.day,
                                  tzinfo=datetime.timezone.utc)
    day_end = day_start + datetime.timedelta(days=1)
    params = {
        "symbol":    symbol,
        "interval":  DEFAULT_INTERVAL,
        "startTime": int(day_start.timestamp() * 1000),
        "endTime":   int(day_end.timestamp() * 1000),
        "limit":     1,
    }
    r = requests.get(BINANCE_API_URL, params=params, timeout=TIMEOUT)
    r.raise_for_status()
    data = r.json()
    return bool(data)


def find_first_day(symbol: str,
                   guess_date: datetime.date,
                   end_date: datetime.date) -> datetime.date:
    """Binary-search the earliest UTC date between guess_date…end_date with any data."""
    low, high = 0, (end_date - guess_date).days
    while low < high:
        mid = (low + high) // 2
        day = guess_date + datetime.timedelta(days=mid)
        print(f"[{symbol}] testing {day}…")
        if has_data_for_day(symbol, day):
            high = mid
        else:
            low = mid + 1
        time.sleep(0.1)  # throttle
    return guess_date + datetime.timedelta(days=low)


def upsert_first_date(symbol: str, first_dt: datetime.datetime):
    """Insert or update into symbols table, with error handling."""
    insert = sql.SQL(
        "INSERT INTO {table} (symbol, first_date) VALUES (%s, %s) "
        "ON CONFLICT (symbol) DO UPDATE SET first_date = EXCLUDED.first_date;"
    ).format(table=TABLE_NAME)
    try:
        with psycopg2.connect(**PG_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute(insert, (symbol, first_dt))
            conn.commit()
    except errors.InsufficientPrivilege as e:
        print(f"Permission error writing to table {TABLE_NAME}: {e}", file=sys.stderr)
        print("Please grant INSERT, UPDATE privileges:" , file=sys.stderr)
        print(f"  GRANT INSERT, UPDATE ON TABLE public.symbols TO {PG_CONFIG.get('user')};", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected DB error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    try:
        symbols = load_symbols()
    except Exception as e:
        print(f"Error loading symbols: {e}", file=sys.stderr)
        sys.exit(1)

    guess = datetime.date(2017, 1, 1)  # Binance launched mid-2017
    today = datetime.datetime.utcnow().date()

    for sym in symbols:
        try:
            first_day = find_first_day(sym, guess, today)
            first_dt = datetime.datetime.combine(
                first_day, datetime.time.min,
                tzinfo=datetime.timezone.utc)
            print(f"→ {sym}: {first_day}")
            upsert_first_date(sym, first_dt)
        except Exception as e:
            print(f"❌ {sym}: failed – {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
