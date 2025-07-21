# 📊 Indicator Evaluator System – Documentation

This module allows you to evaluate technical indicators at any given point in time using historical OHLCV data.

---

## 🧩 Overview

You provide:
- A timestamp (e.g., `"2024-03-05 03:00:00"`)
- A timeframe (e.g., `1m`, `10m`, `1h`, `d`) from `config/indicator_settings.yml`

The program:
- Loads 1-minute candles
- Resamples them to the desired timeframe
- Calculates selected indicators
- Prints results for that moment

---

## 📂 Folder Structure

```
barinex/
├── config/
│   └── indicator_settings.yml    # Timeframe configuration
├── db/
│   └── operations.py             # Fetch OHLCV data from PostgreSQL
├── indicators/
│   ├── rsi.py
│   ├── macd.py
│   └── adx.py
├── logic/
│   └── indicator_evaluator.py    # Core logic to call all indicators
├── scripts/
│   └── evaluate_indicators_at.py # CLI entry point
```

---

## ⚙️ Config: `indicator_settings.yml`

```yaml
# This file configures the timeframe used when calculating indicators.
# Valid options: 1m, 5m, 15m, 30m, 1h, 4h, d, w
# (meaning: 1 minute, 5 minutes, 1 hour, 1 day, etc.)
timeframe: 1h
```

---

## 🧠 Logic Breakdown

### 1. `evaluate_indicators_at.py`
- Reads the timestamp and timeframe
- Estimates how many minutes of data are needed
- Fetches 1m OHLCV data from PostgreSQL
- Resamples to desired timeframe
- Feeds last 30–50 candles to indicator evaluator
- Prints the indicator values

### 2. `resample_df()`
- Aggregates OHLCV from 1m → target timeframe using:
  - Open: first
  - High: max
  - Low: min
  - Close: last
  - Volume: sum

---

## 🧮 Indicators Used

### ✅ RSI (Relative Strength Index)
- **Purpose:** Momentum oscillator
- **Period:** 14 candles
- **Range:** 0–100
- **Signals:**
  - < 30 → Oversold (Bullish)
  - > 70 → Overbought (Bearish)

### ✅ MACD (Moving Average Convergence Divergence)
- **Components:**
  - EMA(12) - EMA(26) = MACD Line
  - EMA(9) of MACD Line = Signal Line
  - MACD Histogram = MACD - Signal
- **Bullish:** MACD crosses above signal
- **Bearish:** MACD crosses below signal

### ✅ ADX (Average Directional Index)
- **Purpose:** Strength of trend
- **Period:** 14 candles
- **Range:**
  - < 20 → Weak/sideways
  - 20–40 → Moderate trend
  - > 40 → Strong trend

---

## 📌 Notes and Rules

- Minimum resampled candles needed: ~35
- If indicators return `NaN`, not enough data is available
- Warnings from `ta` are safe to ignore unless they repeat often
- All timestamps are assumed to be UTC
- PostgreSQL table format assumed: `ohlcv_<symbol>` with `time`, `open`, `high`, `low`, `close`, `volume`

---

## ✅ Sample Output

```bash
$ python scripts/evaluate_indicators_at.py "2024-03-05 03:00:00"

[ℹ️] Resampled rows: 51
🕒 2024-03-05 03:00:00  |  Timeframe: 1h
RSI: 75.23
MACD: 34.94
ADX: 73.14
```

---

## 📦 Future Ideas

- Add more indicators (Stochastic RSI, Bollinger Bands)
- Add final summary label: `➡️ Market: STRONG BULLISH`
- Export results to CSV or JSON
- Visualize on chart

---

© 2025 - barinex indicator module
