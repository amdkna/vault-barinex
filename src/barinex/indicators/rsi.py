# src/barinex/indicators/rsi.py
from __future__ import annotations

from typing import Set

import pandas as pd
from pandas import DataFrame
from ta.momentum import RSIIndicator

from barinex.exceptions import ValidationError


def calculate_rsi(df: DataFrame, period: int = 14) -> float:
    """
    Calculate the latest Relative Strength Index (RSI) for given close-price data.

    Args:
        df: DataFrame containing a 'close' column.
        period: Lookback window for RSI computation.

    Returns:
        The most-recent RSI value. Returns `nan` if `len(df) < period`.

    Raises:
        ValidationError: if required column is missing or computation fails.
    """
    required: Set[str] = {"close"}
    missing = required - set(df.columns)
    if missing:
        raise ValidationError(f"Missing column for RSI calculation: {missing}")

    if df.shape[0] < period:
        return float("nan")

    try:
        indicator = RSIIndicator(close=df["close"], window=period)
        return float(indicator.rsi().iloc[-1])
    except Exception as e:
        raise ValidationError(f"Error computing RSI: {e}")
