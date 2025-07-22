# src/barinex/indicators/adx.py
from __future__ import annotations

from typing import Set

import pandas as pd
from pandas import DataFrame
from ta.trend import ADXIndicator

from barinex.exceptions import ValidationError


def calculate_adx(df: DataFrame, period: int = 14) -> float:
    """
    Calculate the latest Average Directional Index (ADX) for given OHLC data.

    Args:
        df: DataFrame containing 'high', 'low', 'close' columns.
        period: Lookback window for ADX computation (number of periods).

    Returns:
        The most-recent ADX value. Returns `nan` if `len(df) < period`.

    Raises:
        ValidationError: if required columns are missing or computation fails.
    """
    required: Set[str] = {"high", "low", "close"}
    missing = required - set(df.columns)
    if missing:
        raise ValidationError(f"Missing columns for ADX calculation: {missing}")

    if df.shape[0] < period:
        return float("nan")

    try:
        indicator = ADXIndicator(
            high=df["high"], low=df["low"], close=df["close"], window=period
        )
        return float(indicator.adx().iloc[-1])
    except Exception as e:
        raise ValidationError(f"Error computing ADX: {e}")
