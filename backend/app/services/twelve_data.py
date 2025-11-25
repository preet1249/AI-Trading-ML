"""
Twelve Data API Service - REAL DATA
Stock market data for US, Indian, and global markets
NO MOCK DATA - All production-ready
"""
import aiohttp
import asyncio
from typing import List, Dict, Optional
from datetime import datetime
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class TwelveDataService:
    """Real Twelve Data API integration"""

    BASE_URL = "https://api.twelvedata.com"

    # Timeframe mapping
    TIMEFRAME_MAP = {
        "1m": "1min",
        "5m": "5min",
        "15m": "15min",
        "30m": "30min",
        "1h": "1h",
        "4h": "4h",
        "1d": "1day",
        "1w": "1week"
    }

    @classmethod
    async def fetch_time_series(
        cls,
        symbol: str,
        interval: str = "1h",
        outputsize: int = 200
    ) -> List[Dict]:
        """
        Fetch real historical candle data from Twelve Data

        Args:
            symbol: Stock symbol (e.g., AAPL, RELIANCE.NS, TSLA)
            interval: Timeframe (1m, 5m, 15m, 1h, 4h, 1d)
            outputsize: Number of candles to fetch (max 5000)

        Returns:
            List of candle data with OHLCV
        """
        try:
            if not settings.TWELVE_DATA_API_KEY:
                raise Exception("TWELVE_DATA_API_KEY not configured")

            # Map interval
            td_interval = cls.TIMEFRAME_MAP.get(interval, "1h")

            # Build API URL
            url = f"{cls.BASE_URL}/time_series"
            params = {
                "symbol": symbol,
                "interval": td_interval,
                "outputsize": min(outputsize, 5000),
                "apikey": settings.TWELVE_DATA_API_KEY,
                "format": "JSON"
            }

            logger.info(f"Fetching Twelve Data: {symbol} {interval} (outputsize: {outputsize})")

            # Make API request
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Twelve Data API error: {response.status} - {error_text}")
                        raise Exception(f"Twelve Data API error: {response.status}")

                    data = await response.json()

                    # Check for API errors
                    if "status" in data and data["status"] == "error":
                        raise Exception(f"Twelve Data error: {data.get('message', 'Unknown error')}")

                    if "values" not in data:
                        raise Exception("No data returned from Twelve Data")

            # Parse candles (Twelve Data returns in reverse chronological order)
            candles = []
            for bar in reversed(data["values"]):  # Reverse to get chronological order
                # Convert datetime to timestamp
                dt = datetime.strptime(bar["datetime"], "%Y-%m-%d %H:%M:%S")
                timestamp = int(dt.timestamp() * 1000)

                candles.append({
                    "timestamp": timestamp,
                    "open": float(bar["open"]),
                    "high": float(bar["high"]),
                    "low": float(bar["low"]),
                    "close": float(bar["close"]),
                    "volume": float(bar.get("volume", 0))
                })

            logger.info(f"Successfully fetched {len(candles)} candles from Twelve Data")
            return candles

        except Exception as e:
            logger.error(f"Error fetching Twelve Data: {str(e)}")
            raise

    @classmethod
    async def get_quote(cls, symbol: str) -> Dict:
        """
        Get real-time quote for a symbol

        Args:
            symbol: Stock symbol

        Returns:
            Latest quote data
        """
        try:
            if not settings.TWELVE_DATA_API_KEY:
                raise Exception("TWELVE_DATA_API_KEY not configured")

            url = f"{cls.BASE_URL}/quote"
            params = {
                "symbol": symbol,
                "apikey": settings.TWELVE_DATA_API_KEY
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        raise Exception(f"Twelve Data API error: {response.status}")

                    data = await response.json()

                    if "status" in data and data["status"] == "error":
                        raise Exception(f"Twelve Data error: {data.get('message')}")

                    return {
                        "symbol": data["symbol"],
                        "price": float(data["close"]),
                        "change": float(data.get("change", 0)),
                        "percent_change": float(data.get("percent_change", 0)),
                        "volume": float(data.get("volume", 0)),
                        "timestamp": data.get("timestamp")
                    }

        except Exception as e:
            logger.error(f"Error fetching quote: {str(e)}")
            raise


# Singleton instance
twelve_data_service = TwelveDataService()
