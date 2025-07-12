import logging
from datetime import datetime, timedelta
from tqdm import tqdm

from config.settings import DEFAULT_LIMIT, DEFAULT_INTERVAL, TIMEZONE, END_DATE, START_DATE
from fetcher.binance import fetch_binance_ohlcv
from db.schema import create_table_if_not_exists
from db.operations import save_ohlcv
import yaml

def load_symbols(path: str = "./symbols.yml") -> list:
    with open(path, "r") as f:
        raw = yaml.safe_load(f)

    # If file uses dictionary style: symbols: [btc, eth, ...]
    if isinstance(raw, dict) and "symbols" in raw:
        symbols = raw["symbols"]
    elif isinstance(raw, list):
        symbols = raw
    else:
        raise ValueError("❌ Invalid symbols.yml format")

    # Convert to BINANCE format
    return [symbol.upper() + "USDT" for symbol in symbols]
def run_full_fetch(start=START_DATE, end=None):
    end = datetime.now(TIMEZONE) if end is None else datetime.fromisoformat(end)
    symbols = load_symbols()
    interval = DEFAULT_INTERVAL

    for symbol in symbols:
        logging.info(f"▶️ Fetching {symbol} from {start} to {end}")
        create_table_if_not_exists(symbol, interval)
        
        current = datetime.fromisoformat(start) if isinstance(start, str) else start
        total_minutes = int((end - current).total_seconds() // 60)
        total_chunks = total_minutes // DEFAULT_LIMIT + 1

        with tqdm(total=total_chunks, desc=f"{symbol}") as pbar:
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

    logging.info("🎉 All symbols fetched.")
