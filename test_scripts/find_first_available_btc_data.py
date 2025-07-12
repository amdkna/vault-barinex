#!/usr/bin/env python3
"""
find_first_available_btc_data.py

Binary-search the first 1m OHLCV bar for BTCUSDT on Binance.
"""

import requests
import datetime
import sys

API_URL  = "https://api.binance.com/api/v3/klines"
SYMBOL   = "BTCUSDT"
INTERVAL = "1m"
TIMEOUT  = 5  # seconds per request

def has_data_for_day(date: datetime.date) -> bool:
    """Return True if any 1m bar exists on `date`."""
    day_start = datetime.datetime(date.year, date.month, date.day, tzinfo=datetime.timezone.utc)
    params = {
        "symbol": SYMBOL,
        "interval": INTERVAL,
        "startTime": int(day_start.timestamp() * 1000),
        "limit": 1,
    }
    r = requests.get(API_URL, params=params, timeout=TIMEOUT)
    r.raise_for_status()
    return bool(r.json())

def find_first_day(start: datetime.date, end: datetime.date) -> datetime.date:
    """Binary-search the earliest date in [start…end] with data."""
    low, high = 0, (end - start).days
    while low < high:
        mid = (low + high) // 2
        day = start + datetime.timedelta(days=mid)
        print(f"Testing {day}…", file=sys.stderr)
        if has_data_for_day(day):
            high = mid
        else:
            low = mid + 1
    return start + datetime.timedelta(days=low)

def main():
    guess = datetime.date(2017, 1, 1)                       # starting point
    today = datetime.datetime.utcnow().date()              # Binance uses UTC timestamps

    first_day = find_first_day(guess, today)
    print(f"▶ First day with any data: {first_day.isoformat()}")

    # fetch the very first bar on that day
    day_start = datetime.datetime(first_day.year, first_day.month, first_day.day,
                                  tzinfo=datetime.timezone.utc)
    params = {
        "symbol": SYMBOL,
        "interval": INTERVAL,
        "startTime": int(day_start.timestamp() * 1000),
        "limit": 1,
    }
    r = requests.get(API_URL, params=params, timeout=TIMEOUT)
    r.raise_for_status()
    bar = r.json()[0]
    ts = datetime.datetime.fromtimestamp(bar[0] / 1000, tz=datetime.timezone.utc)
    print(f"▶ First bar timestamp: {ts.isoformat()}")

if __name__ == "__main__":
    main()
