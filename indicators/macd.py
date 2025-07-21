from ta.trend import MACD

def calculate_macd_signal(df, fast=12, slow=26, signal=9):
    if len(df) < slow + signal:
        return float("nan")
    indicator = MACD(close=df["close"], window_slow=slow, window_fast=fast, window_sign=signal)
    return indicator.macd_diff().iloc[-1]
