"""
Twelve Data API Service
Stock market data for US, Indian, and global markets
"""
import asyncio
import websockets
import json
from typing import Callable

from app.config import settings


class TwelveDataWebSocket:
    """Twelve Data WebSocket client"""

    def __init__(self):
        self.ws = None
        self.api_key = settings.TWELVE_DATA_API_KEY

    async def connect(self):
        """Connect to Twelve Data WebSocket"""
        ws_url = f"{settings.TWELVE_DATA_WS_URL}?apikey={self.api_key}"
        self.ws = await websockets.connect(ws_url)

    async def subscribe(
        self,
        symbol: str,
        interval: str,
        callback: Callable
    ):
        """
        Subscribe to price stream

        Args:
            symbol: Stock symbol (e.g., AAPL, RELIANCE.NS)
            interval: Interval (1min, 5min, 15min, 1h, 4h, 1day)
            callback: Callback function for new data
        """
        if not self.ws:
            await self.connect()

        # Subscribe message
        subscribe_msg = {
            "action": "subscribe",
            "params": {
                "symbols": symbol,
                "interval": interval
            }
        }

        await self.ws.send(json.dumps(subscribe_msg))

        # Listen for messages
        async for message in self.ws:
            data = json.loads(message)
            await callback(data)

    async def disconnect(self):
        """Close connection"""
        if self.ws:
            await self.ws.close()
