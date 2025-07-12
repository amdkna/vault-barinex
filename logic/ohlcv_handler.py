"""
ohlcv_handler.py

Handles full OHLCV backfill from Binance for multiple symbols.
Skips already-fetched data and handles symbols in lowercase format from YAML.
Each symbol is converted to BINANCE's format (e.g., 'btc' -> 'BTCUSDT').
"""

import logging
import yaml
from datetime import datetime, timedelta

from tqdm import tqdm

from config.settings import DEFAULT_LIMIT, DEFAULT_INTERVAL, TIMEZONE, START_DATE
from fetcher.binance import fetch_binance_ohlcv
from db.schema import create_table_if_not_exists
from db.operations import save_ohlcv, get_first_timestamp


def load_symbols(path: str = "./symbols.yml") -> list:
    """
    Loads symbols from a YAML file.
    Converts them to uppercase Binance symbols with 'USDT' suffix.

    Accepts:
    - List format: ['btc', 'eth']
    - Dict format: { symbols: ['btc', 'eth'] }

    Returns:
        list[str]: List of symbols like ['BTCUSDT', 'ETHUSDT']
    """
    with open(path, "r") as f:
        raw = yaml.safe_load(f)

    if isinstance(raw, dict) and "symbols" in raw:
        symbols = raw["symbols"]
    elif isinstance(raw, list):
        symbols = raw
    else:
        raise ValueError("❌ Invalid symbols.yml format")

    return [symbol.upper() + "USDT" for symbol in symbols]


def run_full_fetch(start=START_DATE, end=None):
    """
    Performs full historical fetch for each symbol from the list.
    If data exists in DB, it skips already-fetched time range.
    If no data exists, starts from `start`.

    Args:
        start (datetime): Start date for historical fetch
        end (datetime|str): Optional end time (ISO string or datetime object)
    """
    symbols = load_symbols()
    end = datetime.now(TIMEZONE) if end is None else datetime.fromisoformat(end)

    for symbol in symbols:
        interval = DEFAULT_INTERVAL
        create_table_if_not_exists(symbol, interval)

        db_start = get_first_timestamp(symbol, interval)
        if db_start:
            current = max(db_start, start)
        else:
            current = start

        total_minutes = int((end - current).total_seconds() // 60)
        total_chunks = total_minutes // DEFAULT_LIMIT + 1

        logging.info(f"▶️ Fetching {symbol} from {current} to {end}")

        with tqdm(total=total_chunks, desc=symbol) as pbar:
            while current < end:
                chunk_end = min(current + timedelta(minutes=DEFAULT_LIMIT), end)
                try:
                    ohlcv = fetch_binance_ohlcv(symbol, interval, current, chunk_end)
                    if ohlcv:
                        save_ohlcv(symbol, interval, ohlcv)
                        logging.info(f"✅ {symbol}: {len(ohlcv)} rows saved from {current} to {chunk_end}")
                    else:
                        logging.warning(f"⚠️ {symbol}: No data {current} → {chunk_end}")
                except Exception as e:
                    logging.error(f"❌ {symbol}: Error from {current} to {chunk_end}: {e}")
                current = chunk_end
                pbar.update(1)

        logging.info(f"✅ Done with {symbol}\n")