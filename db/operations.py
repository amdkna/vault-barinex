import psycopg2
from config.settings import PG_CONFIG
import logging

def save_ohlcv(symbol: str, interval: str, ohlcv: list):
    """
    Bulk-insert OHLCV data into public.ohlcv_<symbol_lowercase> table,
    using `time` as the primary key.
    """
    table_name = f"public.ohlcv_{symbol.lower()}"

    insert_sql = f"""
    INSERT INTO {table_name} (
        time, open, high, low, close, volume
    ) VALUES (%s, %s, %s, %s, %s, %s)
    ON CONFLICT (time) DO NOTHING;
    """
    try:
        with psycopg2.connect(**PG_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.executemany(insert_sql, ohlcv)
            conn.commit()
        logging.info(f"[DB WRITE] Inserted {len(ohlcv)} rows into {table_name}")
    except Exception as e:
        logging.error(f"[DB ERROR] Failed to insert into {table_name}: {e}")
        raise
