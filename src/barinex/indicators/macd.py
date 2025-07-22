# src/barinex/indicators/macd.py
from __future__ import annotations

from typing import Set

import pandas as pd
from pandas import DataFrame
from ta.trend import MACD

from barinex.exceptions import ValidationError


def calculate_macd_signal(
    df: DataFrame, fast: int = 12, slow: int = 26, signal: int = 9
) -> float:
    """
    Calculate the latest MACD histogram (MACD – signal) for given close-price data.

    Args:
        df: DataFrame containing a 'close' column.
        fast: Fast EMA period.
        slow: Slow EMA period.
        signal: Signal-line EMA period.

    Returns:
        The most-recent MACD difference value. Returns `nan` if not enough data.

    Raises:
        ValidationError: if required column is missing or computation fails.
    """
    required: Set[str] = {"close"}
    missing = required - set(df.columns)
    if missing:
        raise ValidationError(f"Missing column for MACD calculation: {missing}")

    if df.shape[0] < slow + signal:
        return float("nan")

    try:
        indicator = MACD(
            close=df["close"],
            window_slow=slow,
            window_fast=fast,
            window_sign=signal,
        )
        return float(indicator.macd_diff().iloc[-1])
    except Exception as e:
        raise ValidationError(f"Error computing MACD signal: {e}")
