from ta.momentum import RSIIndicator

def calculate_rsi(df, period=14):
    if len(df) < period:
        return float("nan")
    indicator = RSIIndicator(close=df["close"], window=period)
    return indicator.rsi().iloc[-1]
