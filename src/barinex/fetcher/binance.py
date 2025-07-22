import logging
import os
from datetime import datetime, timedelta, timezone

import psycopg2
import requests
from dotenv import load_dotenv
from tqdm import tqdm

# --- Setup Logging ---
logging.basicConfig(
    filename="ohlcv_fetcher.log",
    filemode="a",
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
console.setFormatter(formatter)
logging.getLogger().addHandler(console)

# --- Configs ---
load_dotenv()
PG_CONFIG = {
    "host": os.getenv("PG_HOST"),
    "port": os.getenv("PG_PORT"),
    "database": os.getenv("PG_DB"),
    "user": os.getenv("PG_USER"),
    "password": os.getenv("PG_PASSWORD"),
}
BINANCE_API = "https://api.binance.com/api/v3/klines"
SYMBOL = "BTCUSDT"
INTERVAL = "1m"
LIMIT = 1000  # Max per Binance API call

START_DATE = datetime(2024, 1, 1, tzinfo=timezone.utc)
END_DATE = datetime.now(timezone.utc)


# --- DB Functions ---
def get_db_conn():
    return psycopg2.connect(**PG_CONFIG)


def save_ohlcv_to_db(ohlcv):
    insert_sql = """
    INSERT INTO btc_ohlcv_minute (timestamp, open, high, low, close, volume)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON CONFLICT (timestamp) DO NOTHING;
    """
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.executemany(insert_sql, ohlcv)
        conn.commit()


# --- Binance API Fetch ---
def fetch_binance_ohlcv(start_ts, end_ts):
    params = {
        "symbol": SYMBOL,
        "interval": INTERVAL,
        "startTime": int(start_ts.timestamp() * 1000),
        "endTime": int(end_ts.timestamp() * 1000),
        "limit": LIMIT,
    }
    r = requests.get(BINANCE_API, params=params, timeout=10)
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


def main():
    logging.info(
        f"Starting fetch from {START_DATE.date()} to {END_DATE.date()} for {SYMBOL} 1m bars."
    )
    current = START_DATE
    total_minutes = int((END_DATE - START_DATE).total_seconds() // 60)
    total_chunks = total_minutes // LIMIT + 1

    # Progress bar
    with tqdm(total=total_chunks, desc="Fetching OHLCV") as pbar:
        while current < END_DATE:
            end_chunk = min(current + timedelta(minutes=LIMIT), END_DATE)
            try:
                ohlcv = fetch_binance_ohlcv(current, end_chunk)
                if ohlcv:
                    save_ohlcv_to_db(ohlcv)
                    logging.info(
                        f"Fetched and saved {len(ohlcv)} rows: {current} -> {end_chunk}"
                    )
                else:
                    logging.warning(f"No data fetched for {current} -> {end_chunk}")
            except Exception as e:
                logging.error(f"Error for chunk {current} - {end_chunk}: {e}")
            # Set next chunk start time
            current = end_chunk
            pbar.update(1)
    logging.info("✅ Finished fetching all data.")


if __name__ == "__main__":
    main()
