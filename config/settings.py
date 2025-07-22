import os
from datetime import timezone

from dotenv import load_dotenv

# Load .env file
load_dotenv()

# PostgreSQL config
PG_CONFIG = {
    "host": os.getenv("PG_HOST"),
    "port": os.getenv("PG_PORT"),
    "database": os.getenv("PG_DB"),
    "user": os.getenv("PG_USER"),
    "password": os.getenv("PG_PASSWORD"),
}

# Binance API config
BINANCE_API_URL = "https://api.binance.com/api/v3/klines"
DEFAULT_INTERVAL = "1m"
DEFAULT_LIMIT = 1000  # max per request

# Date range defaults
START_DATE = os.getenv("START_DATE", "2024-01-01T00:00:00Z")
END_DATE = os.getenv("END_DATE")  # if None, use now at runtime
TIMEZONE = timezone.utc

# Paths
SYMBOLS_FILE = "./symbols.yml"
LOG_FILE = "logs/ohlcv_fetcher.log"
