import psycopg2

from config.settings import PG_CONFIG


def create_table_if_not_exists(symbol: str):
    """
    Create the per-symbol table public.ohlcv_<symbol_lowercase>
    with `time` as the PRIMARY KEY.
    """
    table_name = f"public.ohlcv_{symbol.lower()}"
    create_sql = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        time    TIMESTAMPTZ PRIMARY KEY,
        open    NUMERIC    NOT NULL,
        high    NUMERIC    NOT NULL,
        low     NUMERIC    NOT NULL,
        close   NUMERIC    NOT NULL,
        volume  NUMERIC    NOT NULL
    );
    """
    with psycopg2.connect(**PG_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute(create_sql)
        conn.commit()
