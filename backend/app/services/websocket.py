"""
Socket.IO Server
Real-time communication with frontend
"""
import socketio
from app.config import settings

# Initialize Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=settings.CORS_ORIGINS,
    logger=settings.DEBUG,
    engineio_logger=settings.DEBUG
)


@sio.event
async def connect(sid, environ, auth):
    """Handle client connection"""
    print(f"Client connected: {sid}")

    # TODO: Verify JWT token from auth
    # token = auth.get("token")
    # if not token:
    #     raise ConnectionRefusedError("Authentication required")

    # Join user-specific room
    # user_id = "user_123"  # Extract from token
    # await sio.enter_room(sid, f"user_{user_id}")

    await sio.emit("connected", {"status": "ok"}, room=sid)


@sio.event
async def disconnect(sid):
    """Handle client disconnection"""
    print(f"Client disconnected: {sid}")


@sio.event
async def subscribe_symbol(sid, data):
    """Subscribe to real-time price updates for a symbol"""
    symbol = data.get("symbol")
    print(f"Client {sid} subscribed to {symbol}")

    # TODO: Start streaming price updates
    # await start_price_stream(sid, symbol)


@sio.event
async def unsubscribe_symbol(sid, data):
    """Unsubscribe from symbol updates"""
    symbol = data.get("symbol")
    print(f"Client {sid} unsubscribed from {symbol}")

    # TODO: Stop streaming price updates


async def emit_to_user(user_id: str, event: str, data: dict):
    """Emit event to specific user"""
    await sio.emit(event, data, room=f"user_{user_id}")


async def broadcast_price_update(symbol: str, price: float, timestamp: int):
    """Broadcast price update to all subscribed clients"""
    await sio.emit("livePrice", {
        "symbol": symbol,
        "price": price,
        "timestamp": timestamp
    })
