"""
Binance API Service - REAL DATA
Fetches real-time crypto data from Binance
NO MOCK DATA - All production-ready
"""
import aiohttp
import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class BinanceService:
    """Real Binance API integration"""

    BASE_URL = "https://api.binance.com"

    # Timeframe mapping
    TIMEFRAME_MAP = {
        "1m": "1m",
        "5m": "5m",
        "15m": "15m",
        "30m": "30m",
        "1h": "1h",
        "4h": "4h",
        "1d": "1d",
        "1w": "1w"
    }

    @classmethod
    async def fetch_klines(
        cls,
        symbol: str,
        interval: str = "1h",
        limit: int = 200
    ) -> List[Dict]:
        """
        Fetch real historical candle data from Binance

        Args:
            symbol: Trading pair (e.g., BTCUSDT)
            interval: Timeframe (1m, 5m, 15m, 1h, 4h, 1d)
            limit: Number of candles to fetch (max 1000)

        Returns:
            List of candle data with OHLCV
        """
        try:
            # Convert symbol to Binance format (uppercase, no separator)
            symbol = symbol.upper().replace("/", "").replace("-", "")

            # Map interval
            binance_interval = cls.TIMEFRAME_MAP.get(interval, "1h")

            # Build API URL
            url = f"{cls.BASE_URL}/api/v3/klines"
            params = {
                "symbol": symbol,
                "interval": binance_interval,
                "limit": min(limit, 1000)  # Binance max is 1000
            }

            logger.info(f"Fetching Binance data: {symbol} {interval} (limit: {limit})")

            # Make API request
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Binance API error: {response.status} - {error_text}")
                        raise Exception(f"Binance API error: {response.status}")

                    data = await response.json()

            # Parse candles
            candles = []
            for kline in data:
                candles.append({
                    "timestamp": int(kline[0]),  # Open time
                    "open": float(kline[1]),
                    "high": float(kline[2]),
                    "low": float(kline[3]),
                    "close": float(kline[4]),
                    "volume": float(kline[5])
                })

            logger.info(f"Successfully fetched {len(candles)} candles from Binance")
            return candles

        except Exception as e:
            logger.error(f"Error fetching Binance data: {str(e)}")
            raise

    @classmethod
    async def get_current_price(cls, symbol: str) -> float:
        """
        Get current price for a symbol

        Args:
            symbol: Trading pair (e.g., BTCUSDT)

        Returns:
            Current price
        """
        try:
            symbol = symbol.upper().replace("/", "").replace("-", "")

            url = f"{cls.BASE_URL}/api/v3/ticker/price"
            params = {"symbol": symbol}

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        raise Exception(f"Binance API error: {response.status}")

                    data = await response.json()
                    return float(data["price"])

        except Exception as e:
            logger.error(f"Error fetching current price: {str(e)}")
            raise

    @classmethod
    async def get_24h_stats(cls, symbol: str) -> Dict:
        """
        Get 24-hour statistics

        Args:
            symbol: Trading pair

        Returns:
            24h stats (volume, price change, etc.)
        """
        try:
            symbol = symbol.upper().replace("/", "").replace("-", "")

            url = f"{cls.BASE_URL}/api/v3/ticker/24hr"
            params = {"symbol": symbol}

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        raise Exception(f"Binance API error: {response.status}")

                    data = await response.json()

                    return {
                        "price_change": float(data["priceChange"]),
                        "price_change_percent": float(data["priceChangePercent"]),
                        "high": float(data["highPrice"]),
                        "low": float(data["lowPrice"]),
                        "volume": float(data["volume"]),
                        "quote_volume": float(data["quoteVolume"])
                    }

        except Exception as e:
            logger.error(f"Error fetching 24h stats: {str(e)}")
            raise


# Singleton instance
binance_service = BinanceService()
