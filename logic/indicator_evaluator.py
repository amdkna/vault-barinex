from indicators import rsi, macd, adx

def evaluate_indicators(df):
    results = {}
    try:
        results["RSI"] = rsi.calculate_rsi(df)
    except Exception as e:
        results["RSI"] = float("nan")
        print(f"[⚠️ RSI Error] {e}")
    try:
        results["MACD"] = macd.calculate_macd_signal(df)
    except Exception as e:
        results["MACD"] = float("nan")
        print(f"[⚠️ MACD Error] {e}")
    try:
        results["ADX"] = adx.calculate_adx(df)
    except Exception as e:
        results["ADX"] = float("nan")
        print(f"[⚠️ ADX Error] {e}")
    return results
