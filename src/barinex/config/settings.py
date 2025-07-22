from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    # PostgreSQL config
    pg_host: str = Field(..., env="PG_HOST")
    pg_port: int = Field(..., env="PG_PORT")
    pg_db: str = Field(..., env="PG_DB")
    pg_user: str = Field(..., env="PG_USER")
    pg_password: str = Field(..., env="PG_PASSWORD")

    # Binance API config
    binance_api_url: str = Field(
        default="https://api.binance.com/api/v3/klines"
    )
    default_interval: str = Field(default="1m")
    default_limit: int = Field(default=1000)

    # Date range defaults
    start_date: datetime = Field(
        default_factory=lambda: datetime.fromisoformat("2024-01-01T00:00:00+00:00")
    )
    end_date: Optional[datetime] = None
    timezone: timezone = Field(default=timezone.utc)

    # Paths
    symbols_file: Path = Field(default=Path("symbols.yml"))
    log_file: Path = Field(default=Path("logs/ohlcv_fetcher.log"))

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        validate_all = True
        frozen = True


# instantiate a single, project-wide settings object
settings = Settings()
