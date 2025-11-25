"""
Binance API Service - REAL DATA
Fetches real-time crypto data from Binance
NO MOCK DATA - All production-ready
Includes WebSocket streaming for real-time updates
"""
import aiohttp
import asyncio
import websockets
import json
from typing import List, Dict, Optional, Callable
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


# ============================================
# WebSocket Streaming
# ============================================

class BinanceWebSocket:
    """
    Real-time Binance WebSocket streams

    Supports:
    - Kline (candle) streams for real-time price updates
    - 24-hour ticker streams
    - Trade streams
    """

    WS_BASE_URL = "wss://stream.binance.com:9443/ws"

    def __init__(self):
        self.connections = {}  # {stream_name: websocket}
        self.callbacks = {}     # {stream_name: callback}
        self.running = {}       # {stream_name: bool}

    async def subscribe_klines(
        self,
        symbol: str,
        interval: str,
        callback: Callable[[Dict], None]
    ) -> str:
        """
        Subscribe to real-time kline (candle) updates

        Args:
            symbol: Trading pair (e.g., BTCUSDT)
            interval: Kline interval (1m, 5m, 15m, 1h, 4h, 1d)
            callback: Async function to call with kline data

        Returns:
            Stream name for managing the subscription
        """
        # Format symbol and interval
        symbol = symbol.lower().replace("/", "").replace("-", "")
        interval_map = {
            "1m": "1m", "5m": "5m", "15m": "15m",
            "30m": "30m", "1h": "1h", "4h": "4h",
            "1d": "1d", "1w": "1w"
        }
        interval = interval_map.get(interval, "1h")

        # Create stream name
        stream_name = f"{symbol}@kline_{interval}"

        # Store callback
        self.callbacks[stream_name] = callback
        self.running[stream_name] = True

        # Start WebSocket connection in background
        asyncio.create_task(self._kline_stream(stream_name))

        logger.info(f"Subscribed to Binance kline stream: {stream_name}")
        return stream_name

    async def _kline_stream(self, stream_name: str):
        """Internal method to handle WebSocket connection"""
        url = f"{self.WS_BASE_URL}/{stream_name}"

        while self.running.get(stream_name, False):
            try:
                async with websockets.connect(url) as ws:
                    self.connections[stream_name] = ws
                    logger.info(f"Connected to Binance stream: {stream_name}")

                    # Handle ping/pong
                    async def send_pong():
                        while self.running.get(stream_name, False):
                            try:
                                pong = await ws.ping()
                                await asyncio.wait_for(pong, timeout=10)
                                await asyncio.sleep(60)  # Ping every minute
                            except Exception as e:
                                logger.error(f"Ping error: {e}")
                                break

                    # Start ping task
                    ping_task = asyncio.create_task(send_pong())

                    # Listen for messages
                    async for message in ws:
                        if not self.running.get(stream_name, False):
                            break

                        try:
                            data = json.loads(message)

                            # Parse kline data
                            if "k" in data:
                                kline = data["k"]
                                candle_data = {
                                    "timestamp": kline["t"],
                                    "open": float(kline["o"]),
                                    "high": float(kline["h"]),
                                    "low": float(kline["l"]),
                                    "close": float(kline["c"]),
                                    "volume": float(kline["v"]),
                                    "is_closed": kline["x"],  # True if candle is closed
                                    "symbol": kline["s"]
                                }

                                # Call callback
                                callback = self.callbacks.get(stream_name)
                                if callback:
                                    await callback(candle_data)

                        except Exception as e:
                            logger.error(f"Error processing message: {e}")

                    # Cancel ping task
                    ping_task.cancel()

            except Exception as e:
                logger.error(f"WebSocket error for {stream_name}: {e}")
                if self.running.get(stream_name, False):
                    logger.info(f"Reconnecting in 5 seconds...")
                    await asyncio.sleep(5)
                else:
                    break

        logger.info(f"Stopped stream: {stream_name}")

    async def subscribe_ticker(
        self,
        symbol: str,
        callback: Callable[[Dict], None]
    ) -> str:
        """
        Subscribe to 24-hour ticker updates

        Args:
            symbol: Trading pair
            callback: Async function to call with ticker data

        Returns:
            Stream name
        """
        symbol = symbol.lower().replace("/", "").replace("-", "")
        stream_name = f"{symbol}@ticker"

        self.callbacks[stream_name] = callback
        self.running[stream_name] = True

        asyncio.create_task(self._ticker_stream(stream_name))

        logger.info(f"Subscribed to Binance ticker stream: {stream_name}")
        return stream_name

    async def _ticker_stream(self, stream_name: str):
        """Internal method for ticker stream"""
        url = f"{self.WS_BASE_URL}/{stream_name}"

        while self.running.get(stream_name, False):
            try:
                async with websockets.connect(url) as ws:
                    self.connections[stream_name] = ws

                    async for message in ws:
                        if not self.running.get(stream_name, False):
                            break

                        try:
                            data = json.loads(message)

                            ticker_data = {
                                "symbol": data["s"],
                                "price": float(data["c"]),
                                "price_change": float(data["p"]),
                                "price_change_percent": float(data["P"]),
                                "high": float(data["h"]),
                                "low": float(data["l"]),
                                "volume": float(data["v"]),
                                "timestamp": data["E"]
                            }

                            callback = self.callbacks.get(stream_name)
                            if callback:
                                await callback(ticker_data)

                        except Exception as e:
                            logger.error(f"Error processing ticker: {e}")

            except Exception as e:
                logger.error(f"Ticker WebSocket error: {e}")
                if self.running.get(stream_name, False):
                    await asyncio.sleep(5)
                else:
                    break

    async def unsubscribe(self, stream_name: str):
        """Unsubscribe from a stream"""
        self.running[stream_name] = False

        if stream_name in self.connections:
            try:
                await self.connections[stream_name].close()
            except:
                pass
            del self.connections[stream_name]

        if stream_name in self.callbacks:
            del self.callbacks[stream_name]

        logger.info(f"Unsubscribed from stream: {stream_name}")

    async def close_all(self):
        """Close all WebSocket connections"""
        for stream_name in list(self.running.keys()):
            await self.unsubscribe(stream_name)

        logger.info("Closed all Binance WebSocket connections")


# Singleton WebSocket instance
binance_ws = BinanceWebSocket()
