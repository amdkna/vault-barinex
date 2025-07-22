from datetime import datetime, timezone

import requests

from config.settings import BINANCE_API_URL, DEFAULT_LIMIT


def fetch_binance_ohlcv(
    symbol: str, interval: str, start_ts, end_ts, limit=DEFAULT_LIMIT
):
    params = {
        "symbol": symbol.upper(),
        "interval": interval,
        "startTime": int(start_ts.timestamp() * 1000),
        "endTime": int(end_ts.timestamp() * 1000),
        "limit": limit,
    }

    r = requests.get(BINANCE_API_URL, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()

    ohlcv = []
    for row in data:
        ts = datetime.fromtimestamp(row[0] / 1000, tz=timezone.utc)
        open_, high, low, close, volume = map(
            float, [row[1], row[2], row[3], row[4], row[5]]
        )
        ohlcv.append((ts, open_, high, low, close, volume))
    return ohlcv
