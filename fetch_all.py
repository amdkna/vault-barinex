import logging
import os
from datetime import datetime, timedelta, timezone
from time import sleep
from logic.ohlcv_handler import run_full_fetch

# --- Logging Setup ---
os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    filename="logs/batch_fetch.log",
    filemode="a",
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO
)

# --- Retry Decorator ---
def retry_forever(func):
    def wrapper(*args, **kwargs):
        while True:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logging.error(f"❌ Unhandled error: {e}. Retrying in 10 seconds...")
                sleep(10)
    return wrapper

@retry_forever
def run_for_all_symbols():
    logging.info("🚀 Starting batch fetch for all symbols (10 years)...")
    start = datetime.now(timezone.utc) - timedelta(days=365 * 10)
    end = datetime.now(timezone.utc)
    run_full_fetch(start=start, end=end.isoformat())
    logging.info("✅ All symbols processed successfully.")

if __name__ == "__main__":
    run_for_all_symbols()
