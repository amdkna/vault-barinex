import psycopg2
from config.settings import PG_CONFIG
from datetime import datetime


def save_ohlcv(symbol: str, interval: str, ohlcv: list):
    if symbol.upper() == "BTCUSDT" and interval == "1m":
        table_name = "btc_ohlcv_minute"
    else:
        table_name = f"{symbol.lower()}_ohlcv_{interval}"

    insert_sql = f"""
    INSERT INTO {table_name} (timestamp, open, high, low, close, volume)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON CONFLICT (timestamp) DO NOTHING;
    """
    with psycopg2.connect(**PG_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.executemany(insert_sql, ohlcv)
        conn.commit()

def get_first_timestamp(symbol: str, interval: str) -> datetime | None:
    if symbol.upper() == "BTCUSDT" and interval == "1m":
        table_name = "btc_ohlcv_minute"
    else:
        table_name = f"{symbol.lower()}_ohlcv_{interval}"

    sql = f"SELECT MIN(timestamp) FROM {table_name};"

    try:
        with psycopg2.connect(**PG_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
                result = cur.fetchone()
                return result[0] if result and result[0] else None
    except psycopg2.errors.UndefinedTable:
        return None
