from __future__ import annotations

from typing import Dict
from pandas import DataFrame

from barinex.indicators.adx import calculate_adx
from barinex.indicators.macd import calculate_macd_signal
from barinex.indicators.rsi import calculate_rsi
from barinex.exceptions import ValidationError


def evaluate_indicators(df: DataFrame) -> Dict[str, float]:
    """
    Compute a suite of indicators on the given OHLCV DataFrame.

    Args:
        df: Must contain at least 'high','low','close','volume','open','time'.

    Returns:
        A dict mapping indicator names → latest value.

    Raises:
        ValidationError if any indicator calculation fails.
    """
    results: Dict[str, float] = {}
    try:
        results["adx"] = calculate_adx(df)
        results["macd"] = calculate_macd_signal(df)
        results["rsi"] = calculate_rsi(df)
    except ValidationError:
        # Bubble up as-is
        raise
    except Exception as e:
        raise ValidationError(f"Error evaluating indicators: {e}")
    return results
