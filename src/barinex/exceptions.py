# src/barinex/exceptions.py

class BarinexError(Exception):
    """Base exception for barinex package."""


class DatabaseError(BarinexError):
    """Errors interacting with the database."""


class FetchError(BarinexError):
    """Errors fetching OHLCV data from external APIs."""


class ValidationError(BarinexError):
    """Invalid data or configuration errors."""
