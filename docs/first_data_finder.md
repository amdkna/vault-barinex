# First Data Finder

This document explains the **First Data Finder** script and the associated database table used to store the first available 1-minute OHLCV data date for each symbol.

---

## Table of Contents

- [First Data Finder](#first-data-finder)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Database Table Schema](#database-table-schema)
  - [Configuration](#configuration)
  - [Script Location](#script-location)
  - [Dependencies](#dependencies)
  - [Usage](#usage)
  - [Program Logic](#program-logic)
  - [Symbols File Format](#symbols-file-format)

---

## Overview

The **First Data Finder** script (`first_data_finder.py`) scans Binance’s 1-minute OHLCV data to determine the very first date on which each symbol generated any data. It performs a fast **binary search** over calendar days instead of a linear day-by-day scan, drastically reducing the number of API calls.

Once discovered, the script upserts the result into a PostgreSQL table named `symbols`.

---

## Database Table Schema

Run the following SQL in your PostgreSQL client (e.g., Navicat) to create the table:

```sql
CREATE TABLE IF NOT EXISTS public.symbols (
  symbol     TEXT        PRIMARY KEY,
  first_date TIMESTAMPTZ NOT NULL
);
```

* **symbol**: The trading pair (e.g., `BTCUSDT`).
* **first\_date**: The timestamp (UTC midnight) of the first 1-minute bar for that symbol.

Ensure your database user (e.g. `coinuser`) has **USAGE** on the `public` schema and **INSERT/UPDATE** on this table:

```sql
GRANT USAGE ON SCHEMA public TO coinuser;
GRANT INSERT, UPDATE ON TABLE public.symbols TO coinuser;
```

---

## Configuration

* **`config/settings.py`** must define `PG_CONFIG`, `BINANCE_API_URL`, and `DEFAULT_INTERVAL` (e.g., `"1m"`).
* **`config/symbols.yml`** lists the base symbols (see below).

---

## Script Location

Place the script here in your repository:

```
barinex/
└── scripts/
    └── first_data_finder.py
```

---

## Dependencies

Install required Python packages:

```bash
pip install requests pyyaml psycopg2-binary
```

---

## Usage

Run the script from your project root:

```bash
python scripts/first_data_finder.py
```

The script will print progress lines such as:

```
[BTCUSDT] testing 2017-07-14…
→ BTCUSDT: 2017-07-14
[ETHUSDT] testing 2017-08-14…
→ ETHUSDT: 2017-08-14
…
```

After completion, the `public.symbols` table will contain one row per symbol with its first data date.

---

## Program Logic

1. **Load Symbols**: Reads `config/symbols.yml`, uppercases each symbol, and appends `USDT`.
2. **Binary Search**: For each symbol:

   * Define a date range from `2017-01-01` to today.
   * Maintain two pointers (`low`, `high`) representing day offsets.
   * On each iteration, test the midpoint day by calling Binance’s `/klines` endpoint with `startTime` and `endTime` for that 24h window and `limit=1`.
   * If data exists, move `high` to midpoint; otherwise move `low` just after.
   * Loop until `low == high`; convert that to a calendar date.
3. **Upsert**: Insert or update the discovered `first_date` into `public.symbols` using `ON CONFLICT`.
4. **Error Handling**:

   * I/O errors when loading YAML are fatal.
   * HTTP or parsing errors are retried per day test.
   * Database permission errors print a grant hint and exit.

---

## Symbols File Format

Your `config/symbols.yml` should look like:

```yaml
symbols:
  - btc
  - eth
  - bnb
  - sol
  - ada
  - ltc
  - xrp
  - matic
  - doge
  - trx
  - atom
  - ftm
  - avax
  - dot
  - near
  - icp
  - fil
  - algo
  - etc
  - mkr
```

The script will transform each entry to `SYMBOLUSDT` (e.g., `btc` → `BTCUSDT`).

---

*End of document.*
