"""
FastAPI Application Entry Point
AI Trading Prediction Model Backend
- Multi-agent prediction system
- Real-time WebSockets
- Database integration (Supabase, MongoDB, Redis)
- Automatic outcome tracking
- Rate limiting & caching
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import socketio
import asyncio
import logging

from app.config import settings
from app.api.routes import chat, predictions, health, cli
from app.services.websocket import sio

# Database clients
from app.db.supabase_client import supabase_client
from app.db.mongodb_client import mongodb_client
from app.db.redis_client import redis_client

# New API routes
from app.api import auth, predictions_api, trades_api, watchlist_api, chat_history

# Middleware
from app.middleware.rate_limiter import rate_limit_middleware

# Background tasks
from app.services.outcome_tracker import outcome_tracker

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Trading Predictor API",
    description="Multi-agent AI system for trading predictions",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ============================================
# Middleware Configuration
# ============================================

# CORS - Allow frontend to access API
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gzip compression for responses
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Rate limiting middleware (Redis-based)
app.middleware("http")(rate_limit_middleware)

# ============================================
# Socket.IO Integration
# ============================================

# Mount Socket.IO app
socket_app = socketio.ASGIApp(
    sio,
    other_asgi_app=app,
    socketio_path="socket.io",
)

# ============================================
# API Routes
# ============================================

# Health & existing routes
app.include_router(health.router, tags=["Health"])
app.include_router(cli.router, prefix="/api/v1", tags=["CLI"])  # Simple CLI endpoint (no auth)
app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])
app.include_router(predictions.router, prefix="/api/v1", tags=["Predictions"])

# New database-integrated routes
app.include_router(auth.router, prefix="/api/v1", tags=["Authentication"])
app.include_router(chat_history.router, prefix="/api/v1", tags=["Chat History"])
app.include_router(predictions_api.router, prefix="/api/v1", tags=["Predictions API"])
app.include_router(trades_api.router, prefix="/api/v1", tags=["Trades"])
app.include_router(watchlist_api.router, prefix="/api/v1", tags=["Watchlist"])

# ============================================
# Application Events
# ============================================

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("🚀 Starting AI Trading Predictor API...")
    logger.info(f"📊 Environment: {settings.ENVIRONMENT}")
    logger.info(f"🔗 CORS Origins: {settings.CORS_ORIGINS}")

    try:
        # Initialize Supabase
        logger.info("Initializing Supabase...")
        supabase_client.initialize()

        # Initialize MongoDB
        logger.info("Initializing MongoDB...")
        await mongodb_client.initialize()

        # Initialize Redis
        logger.info("Initializing Redis...")
        await redis_client.initialize()

        logger.info("✅ All database connections initialized")

        # Start intelligent background task for outcome tracking (every 12 hours)
        logger.info("Starting INTELLIGENT outcome tracker (runs every 12 hours)...")
        asyncio.create_task(outcome_tracker.run_intelligent_checker(interval=43200))  # 12 hours = 43200 seconds

        logger.info("✅ Background tasks started")
        logger.info("🎉 AI Trading Predictor API is ready!")

    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🛑 Shutting down AI Trading Predictor API...")

    try:
        # Close MongoDB
        if mongodb_client._initialized:
            await mongodb_client.close()
            logger.info("MongoDB connection closed")

        # Close Redis
        if redis_client._initialized:
            await redis_client.close()
            logger.info("Redis connection closed")

        logger.info("✅ Cleanup complete")

    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# ============================================
# Root Endpoint
# ============================================

@app.get("/")
async def root():
    """Root endpoint - API info"""
    return {
        "name": "AI Trading Predictor API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
    }


# Export socket app for uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:socket_app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
    )
