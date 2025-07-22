from datetime import timedelta

import psycopg2

from config.settings import DEFAULT_INTERVAL, PG_CONFIG
from db.operations import save_ohlcv
from db.schema import create_table_if_not_exists
from fetcher.binance import fetch_binance_ohlcv


def fill_missing(symbol: str, interval: str = DEFAULT_INTERVAL):
    create_table_if_not_exists(symbol, interval)  # 🔧 Ensure table exists
    timestamps = get_existing_timestamps(symbol, interval)
    ...


def get_existing_timestamps(symbol: str, interval: str = DEFAULT_INTERVAL) -> list:
    if symbol.upper() == "BTCUSDT" and interval == "1m":
        table = "btc_ohlcv_minute"
    else:
        table = f"{symbol.lower()}_ohlcv_{interval}"

    sql = f"SELECT timestamp FROM {table} ORDER BY timestamp ASC;"

    with psycopg2.connect(**PG_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            return [row[0] for row in cur.fetchall()]


def find_missing_timestamps(timestamps: list, step_minutes: int = 1) -> list:
    if not timestamps:
        return []

    missing = []
    expected = timestamps[0]
    for ts in timestamps[1:]:
        while expected + timedelta(minutes=step_minutes) < ts:
            expected += timedelta(minutes=step_minutes)
            missing.append(expected)
        expected = ts
    return missing


def fill_missing(symbol: str, interval: str = DEFAULT_INTERVAL):
    timestamps = get_existing_timestamps(symbol, interval)
    gaps = find_missing_timestamps(timestamps)

    if not gaps:
        print(f"✅ No missing data for {symbol}")
        return

    print(f"⚠️ Found {len(gaps)} missing timestamps for {symbol}")

    for ts in gaps:
        try:
            next_ts = ts + timedelta(minutes=1)
            data = fetch_binance_ohlcv(symbol, interval, ts, next_ts)
            if data:
                save_ohlcv(symbol, interval, data)
                print(f"✔️ Filled {ts}")
            else:
                print(f"❌ No data returned for {ts}")
        except Exception as e:
            print(f"❌ Error fetching {ts}: {e}")
