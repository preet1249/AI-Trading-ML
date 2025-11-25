"""
Helper Utilities
"""
from datetime import datetime
from typing import Any


def timestamp_to_datetime(timestamp: int) -> datetime:
    """Convert Unix timestamp to datetime"""
    return datetime.fromtimestamp(timestamp / 1000)


def datetime_to_timestamp(dt: datetime) -> int:
    """Convert datetime to Unix timestamp"""
    return int(dt.timestamp() * 1000)


def format_price(price: float, decimals: int = 2) -> str:
    """Format price with specified decimals"""
    return f"{price:.{decimals}f}"


def validate_symbol(symbol: str) -> bool:
    """Validate trading symbol format"""
    # Basic validation - can be enhanced
    return len(symbol) >= 2 and symbol.isalnum()


def validate_timeframe(timeframe: str) -> bool:
    """Validate timeframe format"""
    valid_timeframes = ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w"]
    return timeframe in valid_timeframes
