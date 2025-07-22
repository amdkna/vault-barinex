import argparse
import os
import sys
from datetime import datetime, timedelta, timezone

import yaml

# Allow project root imports
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from db.operations import get_ohlcv_data
from logic.indicator_evaluator import evaluate_indicators

CONFIG_PATH = os.path.join(BASE_DIR, "config", "indicator_settings.yml")

def load_config():
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)

def resample_df(df, timeframe: str):
    ohlcv_agg = {
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum"
    }
    df.set_index("time", inplace=True)
    df_resampled = df.resample(timeframe).agg(ohlcv_agg).dropna().reset_index()
    return df_resampled

def main(timestamp_str):
    config = load_config()
    timeframe = config.get("timeframe", "1h")

    dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    # Estimate how many minutes we need based on desired timeframe
    frame_map = {
        "1m": 50,
        "5m": 5 * 50,
        "10m": 10 * 50,
        "15m": 15 * 50,
        "30m": 30 * 50,
        "1h": 60 * 50,
        "4h": 240 * 50,
        "d": 1440 * 50,
    }
    minutes_needed = frame_map.get(timeframe, 200)

    df = get_ohlcv_data(symbol='btcusdt', start=dt - timedelta(minutes=minutes_needed), end=dt)

    df_resampled = resample_df(df, timeframe)
    print(f"[ℹ️] Resampled rows: {len(df_resampled)}")
    if len(df_resampled) < 35:
        print(f"⚠️ Not enough data ({len(df_resampled)} candles) to compute indicators reliably.")



    # Keep only rows before or equal to timestamp
    df_resampled = df_resampled[df_resampled["time"] <= dt]
    if df_resampled.empty:
        print(f"❌ No resampled data found for {timestamp_str} with timeframe '{timeframe}'")
        return

    indicators = evaluate_indicators(df_resampled)
    print(f"🕒 {timestamp_str}  |  Timeframe: {timeframe}")
    for k, v in indicators.items():
        print(f"{k}: {v:.2f}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("timestamp", help="Timestamp (e.g., 2021-01-01 14:24:12)")
    args = parser.parse_args()
    main(args.timestamp)
