#!/usr/bin/env python3
import logging
import os
import sys
import json
from datetime import datetime, timezone
from time import sleep

# ─── Ensure console uses UTF-8 on Windows and other platforms ─────────────────
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
# ──────────────────────────────────────────────────────────────────────────────

# ─── Make project root importable ──────────────────────────────────────────────
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
# ──────────────────────────────────────────────────────────────────────────────

from config.settings import PG_CONFIG
import psycopg2
import logic.ohlcv_handler as handler  # use handler.run_full_fetch

# --- Logging Setup: Console + File with Unicode fallback ---
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "ohlcv_backfill.log")

class SafeStreamHandler(logging.StreamHandler):
    def emit(self, record):
        try:
            super().emit(record)
        except UnicodeEncodeError:
            msg = self.format(record).encode(self.stream.encoding, errors="replace").decode(self.stream.encoding)
            self.stream.write(msg + self.terminator)
            self.flush()

file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
console_handler = SafeStreamHandler(sys.stdout)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[file_handler, console_handler]
)

# --- Retry Decorator ---
def retry_forever(func):
    def wrapper(*args, **kwargs):
        while True:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logging.error(f"[ERROR] Unhandled error: {e}. Retrying in 10s...")
                sleep(10)
    return wrapper

# --- State File for Duplication Avoidance ---
STATE_FILE = os.path.join(BASE_DIR, "fetcher", "last_fetch.json")

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def get_symbols_first_dates():
    sql = "SELECT symbol, first_date FROM public.symbols;"
    with psycopg2.connect(**PG_CONFIG) as conn, conn.cursor() as cur:
        cur.execute(sql)
        return cur.fetchall()

@retry_forever
def run_ohlcv_backfill():
    logging.info("[START] Starting OHLCV backfill...")
    now = datetime.now(timezone.utc)
    state = load_state()

    for symbol, first_dt in get_symbols_first_dates():
        last = state.get(symbol)
        start = datetime.fromisoformat(last) if last else first_dt

        if start >= now:
            logging.info(f"[SKIP] {symbol} up to date (last: {start.isoformat()})")
            continue

        # Table naming: ohlcv_<symbol_lower>
        table_name = f"public.ohlcv_{symbol.lower()}"
        # Override handler's naming logic if available
        if hasattr(handler, 'get_table_name'):
            handler.get_table_name = lambda sym=symbol: f"public.ohlcv_{sym.lower()}"
        else:
            # fallback: set attribute or config var in handler
            setattr(handler, 'TABLE_PREFIX', 'ohlcv_')

        # Monkey-patch which symbols to fetch
        handler.load_symbols = lambda sym=symbol: [sym]

        logging.info(f"[FETCH] {symbol}: {start.isoformat()} ➔ {now.isoformat()}")
        handler.run_full_fetch(start=start.isoformat(), end=now.isoformat())

        # Log actual rows in the symbol-specific table
        try:
            with psycopg2.connect(**PG_CONFIG) as conn, conn.cursor() as cur:
                cur.execute(
                    f"SELECT COUNT(*) FROM {table_name} WHERE time >= %s AND time < %s;",
                    (start.isoformat(), now.isoformat())
                )
                count = cur.fetchone()[0]
                logging.info(f"[DB] {table_name}: {count} new rows")
        except Exception as db_e:
            logging.error(f"[DB ERROR] counting rows for {table_name}: {db_e}")

        state[symbol] = now.isoformat()
        save_state(state)
        logging.info(f"[DONE] {symbol} backfill complete")

    logging.info("[FINISH] All symbols backfilled.")

if __name__ == "__main__":
    run_ohlcv_backfill()
