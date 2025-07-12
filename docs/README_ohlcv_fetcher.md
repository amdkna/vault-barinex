# OHLCV Data Fetcher – Project Overview

This project is designed to **fetch historical OHLCV data** for crypto trading pairs from Binance, **store it into PostgreSQL** (with TimescaleDB if available), and ensure **resilience, logging, and reusability** for future trading bots or analysis.

---

## 🧩 Folder Structure

```plaintext
project-root/
├── ohlcv_data_fetcher.py       # Main script to backfill OHLCV data
├── config/
│   └── settings.py             # Environment variables and configs
├── db/
│   ├── schema.py               # Creates OHLCV tables
│   └── operations.py           # Saves OHLCV data
├── fetcher/
│   └── binance.py              # Calls Binance API to get OHLCV
├── logic/
│   ├── ohlcv_handler.py        # Orchestrates full symbol fetch
│   └── checker.py              # (Optional) Fills missing timestamps
├── logs/
│   └── ohlcv_backfill.log      # Runtime logs
├── fetcher/last_fetch.json     # Tracks last fetch time per symbol
└── symbols.yml                 # List of symbols to fetch (used dynamically)
```

---

## 🔁 Main Program: `ohlcv_data_fetcher.py`

This script:
- Loads `last_fetch.json` state
- Connects to DB to find symbol start dates
- Uses `ohlcv_handler.run_full_fetch()` per symbol
- Logs how many new rows were added
- Saves updated state

**Core Functions:**
- `load_state()` / `save_state()`: Handles fetch progress
- `run_ohlcv_backfill()`: Main execution logic
- Includes a retry decorator to ensure resiliency

---

## ⚙️ Logic Layer: `ohlcv_handler.py`

This is the main **orchestration engine** for OHLCV fetching:

- `load_symbols_from_db()`: Pulls active symbols from `public.symbols`
- `get_last_timestamp()`: Finds the most recent timestamp in the symbol’s table
- `run_full_fetch(start, end)`: 
  - Loops over each symbol
  - Breaks the time range into 1-day chunks (`CHUNK_SIZE`)
  - Calls `fetch_binance_ohlcv()` for each chunk
  - Saves data with `save_ohlcv()`
  - Ensures no overlap

---

## 🌐 Binance API Wrapper: `binance.py`

- `fetch_binance_ohlcv(symbol, interval, start, end)`:
  - Converts timestamps to milliseconds
  - Requests OHLCV data from Binance
  - Parses response to tuples of `(datetime, open, high, low, close, volume)`

---

## 🛢️ Database Layer

### `schema.py`
- `create_table_if_not_exists(symbol)`:
  - Creates a table like `public.ohlcv_btcusdt`
  - Columns: `time`, `open`, `high`, `low`, `close`, `volume`

### `operations.py`
- `save_ohlcv(symbol, interval, ohlcv)`:
  - Bulk-inserts data into the relevant table
  - Skips duplicates using `ON CONFLICT DO NOTHING`

---

## 🧪 Optional: `checker.py`

Not used in the main program right now. Its purpose:
- `get_existing_timestamps()` – Loads all timestamps
- `find_missing_timestamps()` – Finds gaps by expected 1-minute steps
- `fill_missing()` – Refetches only the missing data

Useful for:
- Healing incomplete data
- Post-processing validation

---

## ⚙️ Config: `settings.py`

Loaded via `dotenv`. Includes:
- `PG_CONFIG` – DB connection settings
- `BINANCE_API_URL` – Endpoint
- `DEFAULT_INTERVAL`, `DEFAULT_LIMIT`
- Date range control via `START_DATE` and `END_DATE`
- File paths: `symbols.yml`, `logs/`

---

## 🔁 Execution Flow

```plaintext
ohlcv_data_fetcher.py
 └── uses ohlcv_handler.run_full_fetch
      ├── uses binance.fetch_binance_ohlcv
      ├── uses schema.create_table_if_not_exists
      ├── uses operations.save_ohlcv
      └── uses settings.PG_CONFIG
```

---

## 🧠 Logic Summary

- Tables are created dynamically per symbol
- Each fetch is done in 1-day chunks to avoid timeouts
- Symbol progress is tracked in `last_fetch.json`
- If fetch fails, retry loop ensures recovery
- Logging is stored in `logs/ohlcv_backfill.log`

---

## 📌 Tips

- To expand, implement hourly or daily fetchers using similar logic.
- Schedule `ohlcv_data_fetcher.py` with cron or task scheduler.
- Add TimescaleDB optimizations like hypertables for scale.