"""
Twelve Data API Service - REAL DATA
Stock market data for US, Indian, and global markets
NO MOCK DATA - All production-ready
Includes WebSocket streaming for real-time updates
"""
import aiohttp
import asyncio
import websockets
import json
from typing import List, Dict, Optional, Callable
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

    @staticmethod
    def normalize_symbol_for_twelvedata(symbol: str) -> str:
        """
        Normalize symbol to TwelveData format

        TwelveData uses colon separator for exchanges:
        - ADANIGREEN.NS → ADANIGREEN:NSE
        - RELIANCE.BO → RELIANCE:BSE
        - AAPL → AAPL (US stocks unchanged)

        Args:
            symbol: Symbol in standard format

        Returns:
            Symbol in TwelveData format
        """
        # Indian NSE stocks
        if symbol.endswith(".NS"):
            base_symbol = symbol[:-3]  # Remove .NS
            return f"{base_symbol}:NSE"

        # Indian BSE stocks
        if symbol.endswith(".BO"):
            base_symbol = symbol[:-3]  # Remove .BO
            return f"{base_symbol}:BSE"

        # US and other stocks - no change needed
        return symbol

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

            # Normalize symbol for TwelveData format
            normalized_symbol = cls.normalize_symbol_for_twelvedata(symbol)

            # Map interval
            td_interval = cls.TIMEFRAME_MAP.get(interval, "1h")

            # Build API URL
            url = f"{cls.BASE_URL}/time_series"
            params = {
                "symbol": normalized_symbol,
                "interval": td_interval,
                "outputsize": min(outputsize, 5000),
                "apikey": settings.TWELVE_DATA_API_KEY,
                "format": "JSON"
            }

            logger.info(f"Fetching Twelve Data: {symbol} → {normalized_symbol} {interval} (outputsize: {outputsize})")

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

            # Normalize symbol for TwelveData format
            normalized_symbol = cls.normalize_symbol_for_twelvedata(symbol)

            url = f"{cls.BASE_URL}/quote"
            params = {
                "symbol": normalized_symbol,
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


# ============================================
# WebSocket Streaming
# ============================================

class TwelveDataWebSocket:
    """
    Real-time Twelve Data WebSocket streams

    Supports:
    - Price quotes for stocks
    - Real-time updates for US, Indian, and global markets
    """

    WS_BASE_URL = "wss://ws.twelvedata.com/v1/quotes/price"

    def __init__(self):
        self.ws = None
        self.subscribed_symbols = set()
        self.callbacks = {}  # {symbol: callback}
        self.running = False

    async def connect(self):
        """Establish WebSocket connection"""
        if not settings.TWELVE_DATA_API_KEY:
            raise Exception("TWELVE_DATA_API_KEY not configured")

        url = f"{self.WS_BASE_URL}?apikey={settings.TWELVE_DATA_API_KEY}"

        try:
            self.ws = await websockets.connect(url)
            self.running = True
            logger.info("Connected to Twelve Data WebSocket")

            # Start message handler
            asyncio.create_task(self._handle_messages())

        except Exception as e:
            logger.error(f"Failed to connect to Twelve Data WS: {e}")
            raise

    async def _handle_messages(self):
        """Handle incoming WebSocket messages"""
        try:
            async for message in self.ws:
                try:
                    data = json.loads(message)

                    # Handle different message types
                    if data.get("event") == "subscribe-status":
                        logger.info(f"Subscription status: {data}")
                    elif data.get("event") == "price":
                        # Real-time price update
                        symbol = data.get("symbol")
                        price_data = {
                            "symbol": symbol,
                            "price": float(data.get("price", 0)),
                            "timestamp": data.get("timestamp")
                        }

                        # Call callback if exists
                        callback = self.callbacks.get(symbol)
                        if callback:
                            await callback(price_data)

                    elif data.get("event") == "heartbeat":
                        # Heartbeat - keep connection alive
                        pass

                except Exception as e:
                    logger.error(f"Error processing Twelve Data message: {e}")

        except Exception as e:
            logger.error(f"WebSocket message handler error: {e}")
            self.running = False

    async def subscribe(
        self,
        symbol: str,
        callback: Callable[[Dict], None]
    ) -> str:
        """
        Subscribe to real-time price updates

        Args:
            symbol: Stock symbol (e.g., AAPL, RELIANCE.NS)
            callback: Async function to call with price data

        Returns:
            Symbol name
        """
        if not self.running:
            await self.connect()

        # Subscribe message
        subscribe_msg = {
            "action": "subscribe",
            "params": {
                "symbols": symbol
            }
        }

        await self.ws.send(json.dumps(subscribe_msg))

        # Store callback
        self.callbacks[symbol] = callback
        self.subscribed_symbols.add(symbol)

        logger.info(f"Subscribed to Twelve Data stream: {symbol}")
        return symbol

    async def unsubscribe(self, symbol: str):
        """Unsubscribe from a symbol"""
        if symbol in self.subscribed_symbols:
            # Unsubscribe message
            unsubscribe_msg = {
                "action": "unsubscribe",
                "params": {
                    "symbols": symbol
                }
            }

            try:
                await self.ws.send(json.dumps(unsubscribe_msg))
                self.subscribed_symbols.remove(symbol)
                if symbol in self.callbacks:
                    del self.callbacks[symbol]
                logger.info(f"Unsubscribed from: {symbol}")
            except Exception as e:
                logger.error(f"Error unsubscribing: {e}")

    async def close(self):
        """Close WebSocket connection"""
        self.running = False

        if self.ws:
            try:
                # Unsubscribe from all symbols
                if self.subscribed_symbols:
                    unsubscribe_msg = {
                        "action": "unsubscribe",
                        "params": {
                            "symbols": list(self.subscribed_symbols)
                        }
                    }
                    await self.ws.send(json.dumps(unsubscribe_msg))

                await self.ws.close()
            except:
                pass

        self.subscribed_symbols.clear()
        self.callbacks.clear()
        logger.info("Closed Twelve Data WebSocket connection")


# Singleton WebSocket instance
twelve_data_ws = TwelveDataWebSocket()
