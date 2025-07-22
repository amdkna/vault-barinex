# src/barinex/utils/resample.py

from pandas import DataFrame

def resample_df(df: DataFrame, timeframe: str) -> DataFrame:
    """
    Resample an OHLCV DataFrame into a new timeframe.

    Args:
        df: must contain a 'time' column of type datetime64[ns]
            and 'open','high','low','close','volume' columns.
        timeframe: a pandas frequency string, e.g. '1h', '5m', 'd'.

    Returns:
        A resampled DataFrame with aggregated OHLCV and a reset index.
    """
    ohlcv_agg = {
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum",
    }

    df = df.set_index("time")
    df_resampled = df.resample(timeframe).agg(ohlcv_agg).dropna().reset_index()
    return df_resampled
