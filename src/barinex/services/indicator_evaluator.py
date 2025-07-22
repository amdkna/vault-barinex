#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict

import yaml
from pandas import DataFrame

from barinex.config.settings import settings
from barinex.db.operations import get_ohlcv_data
from barinex.services.evaluator import evaluate_indicators
from barinex.exceptions import ValidationError
from barinex.utils.resample import resample_df


def load_config() -> Dict:
    """
    Load indicator settings (e.g. timeframe) from YAML.
    """
    cfg_path = Path(settings.project_root) / "config" / "indicator_settings.yml"
    with cfg_path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def main(timestamp_str: str) -> None:
    """
    CLI entrypoint: fetch recent data, resample, and print indicator values.
    """
    cfg = load_config()
    timeframe: str = cfg.get("timeframe", "1h")

    dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S").replace(
        tzinfo=timezone.utc
    )
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

    df: DataFrame = get_ohlcv_data(
        symbol="BTCUSDT",
        start=dt - timedelta(minutes=minutes_needed),
        end=dt,
    )

    df_resampled = resample_df(df, timeframe)
    print(f"[ℹ️] Resampled rows: {len(df_resampled)}")
    if len(df_resampled) < 35:
        print(f"⚠️ Not enough data ({len(df_resampled)} candles) to compute indicators reliably.")
        return

    df_resampled = df_resampled[df_resampled["time"] <= dt]
    if df_resampled.empty:
        print(f"❌ No data at {timestamp_str} with timeframe '{timeframe}'.")
        return

    try:
        results = evaluate_indicators(df_resampled)
    except ValidationError as e:
        print(f"❌ Validation error: {e}")
        return

    print(f"🕒 {timestamp_str}  |  Timeframe: {timeframe}")
    for name, value in results.items():
        print(f"{name}: {value:.2f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compute indicators at a given timestamp")
    parser.add_argument(
        "timestamp",
        help="Timestamp (e.g. '2021-01-01 14:24:12', UTC)",
    )
    args = parser.parse_args()
    main(args.timestamp)
