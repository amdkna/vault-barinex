import psycopg2
from config.settings import PG_CONFIG

def create_table_if_not_exists(symbol: str, interval: str = "1m"):
    if symbol.upper() == "BTCUSDT" and interval == "1m":
        table_name = "btc_ohlcv_minute"
    else:
        table_name = f"{symbol.lower()}_ohlcv_{interval}"
    
    create_sql = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        timestamp TIMESTAMPTZ PRIMARY KEY,
        open DOUBLE PRECISION,
        high DOUBLE PRECISION,
        low DOUBLE PRECISION,
        close DOUBLE PRECISION,
        volume DOUBLE PRECISION
    );
    """
    with psycopg2.connect(**PG_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute(create_sql)
        conn.commit()
