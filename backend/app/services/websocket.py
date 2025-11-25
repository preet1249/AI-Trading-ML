"""
Socket.IO Server - REAL-TIME STREAMING
Real-time communication with frontend
Integrates with Binance and Twelve Data WebSockets
"""
import socketio
import logging
from typing import Dict, Set
from app.config import settings

logger = logging.getLogger(__name__)

# Import WebSocket services
from app.services.binance import binance_ws
from app.services.twelve_data import twelve_data_ws
from app.core.data_fetcher import _is_crypto_symbol

# Initialize Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=settings.CORS_ORIGINS,
    logger=settings.DEBUG,
    engineio_logger=settings.DEBUG
)

# Track subscriptions: {sid: {symbol: {stream_info}}}
client_subscriptions: Dict[str, Dict] = {}


@sio.event
async def connect(sid, environ, auth):
    """Handle client connection"""
    logger.info(f"Client connected: {sid}")

    # TODO: Verify JWT token from auth
    # token = auth.get("token")
    # if not token:
    #     raise ConnectionRefusedError("Authentication required")

    # Initialize subscription tracking for this client
    client_subscriptions[sid] = {}

    await sio.emit("connected", {"status": "ok"}, room=sid)


@sio.event
async def disconnect(sid):
    """Handle client disconnection and cleanup subscriptions"""
    logger.info(f"Client disconnected: {sid}")

    # Unsubscribe from all streams for this client
    if sid in client_subscriptions:
        subscriptions = client_subscriptions[sid]
        for symbol, stream_info in subscriptions.items():
            try:
                is_crypto = stream_info.get("is_crypto", True)
                stream_name = stream_info.get("stream_name")

                if is_crypto and stream_name:
                    await binance_ws.unsubscribe(stream_name)
                elif not is_crypto:
                    await twelve_data_ws.unsubscribe(symbol)

                logger.info(f"Unsubscribed {sid} from {symbol}")
            except Exception as e:
                logger.error(f"Error unsubscribing on disconnect: {e}")

        del client_subscriptions[sid]


@sio.event
async def subscribe_symbol(sid, data):
    """
    Subscribe to real-time price updates for a symbol

    Args:
        sid: Socket ID
        data: {"symbol": "BTCUSDT", "timeframe": "1h"}
    """
    symbol = data.get("symbol")
    timeframe = data.get("timeframe", "1h")

    if not symbol:
        await sio.emit("error", {"message": "Symbol required"}, room=sid)
        return

    logger.info(f"Client {sid} subscribing to {symbol} ({timeframe})")

    try:
        # Detect if crypto or stock
        is_crypto = _is_crypto_symbol(symbol)

        # Define callback to forward data to frontend
        async def price_callback(price_data):
            """Forward real-time data to frontend"""
            await sio.emit("livePrice", price_data, room=sid)

        # Subscribe to appropriate WebSocket
        if is_crypto:
            # Binance WebSocket for crypto
            stream_name = await binance_ws.subscribe_klines(
                symbol=symbol,
                interval=timeframe,
                callback=price_callback
            )

            # Track subscription
            if sid not in client_subscriptions:
                client_subscriptions[sid] = {}

            client_subscriptions[sid][symbol] = {
                "is_crypto": True,
                "stream_name": stream_name,
                "timeframe": timeframe
            }

            logger.info(f"Subscribed {sid} to Binance: {stream_name}")

        else:
            # Twelve Data WebSocket for stocks
            await twelve_data_ws.subscribe(
                symbol=symbol,
                callback=price_callback
            )

            # Track subscription
            if sid not in client_subscriptions:
                client_subscriptions[sid] = {}

            client_subscriptions[sid][symbol] = {
                "is_crypto": False,
                "stream_name": symbol,
                "timeframe": timeframe
            }

            logger.info(f"Subscribed {sid} to Twelve Data: {symbol}")

        # Confirm subscription to client
        await sio.emit("subscription_confirmed", {
            "symbol": symbol,
            "timeframe": timeframe,
            "type": "crypto" if is_crypto else "stock"
        }, room=sid)

    except Exception as e:
        logger.error(f"Error subscribing to {symbol}: {e}")
        await sio.emit("error", {
            "message": f"Failed to subscribe to {symbol}",
            "error": str(e)
        }, room=sid)


@sio.event
async def unsubscribe_symbol(sid, data):
    """Unsubscribe from symbol updates"""
    symbol = data.get("symbol")

    if not symbol or sid not in client_subscriptions:
        return

    logger.info(f"Client {sid} unsubscribing from {symbol}")

    try:
        if symbol in client_subscriptions[sid]:
            stream_info = client_subscriptions[sid][symbol]
            is_crypto = stream_info.get("is_crypto", True)
            stream_name = stream_info.get("stream_name")

            # Unsubscribe from WebSocket
            if is_crypto and stream_name:
                await binance_ws.unsubscribe(stream_name)
            elif not is_crypto:
                await twelve_data_ws.unsubscribe(symbol)

            # Remove from tracking
            del client_subscriptions[sid][symbol]

            logger.info(f"Unsubscribed {sid} from {symbol}")

            await sio.emit("unsubscription_confirmed", {
                "symbol": symbol
            }, room=sid)

    except Exception as e:
        logger.error(f"Error unsubscribing from {symbol}: {e}")


# ============================================
# Utility Functions
# ============================================

async def emit_to_user(user_id: str, event: str, data: dict):
    """Emit event to specific user"""
    await sio.emit(event, data, room=f"user_{user_id}")


async def broadcast_to_all(event: str, data: dict):
    """Broadcast event to all connected clients"""
    await sio.emit(event, data)


async def emit_ta_update(sid: str, ta_data: dict):
    """Emit technical analysis update to client"""
    await sio.emit("taUpdate", ta_data, room=sid)


async def emit_prediction(sid: str, prediction: dict):
    """Emit prediction result to client"""
    await sio.emit("prediction", prediction, room=sid)
