from ta.trend import ADXIndicator


def calculate_adx(df, period=14):
    if len(df) < period:
        return float("nan")
    indicator = ADXIndicator(high=df["high"], low=df["low"], close=df["close"], window=period)
    return indicator.adx().iloc[-1]
