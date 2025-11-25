"""
FastAPI Application Entry Point
AI Trading Prediction Model Backend
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import socketio

from app.config import settings
from app.api.routes import chat, predictions, health
from app.services.websocket import sio

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

app.include_router(health.router, tags=["Health"])
app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])
app.include_router(predictions.router, prefix="/api/v1", tags=["Predictions"])

# ============================================
# Application Events
# ============================================

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    print("🚀 Starting AI Trading Predictor API...")
    print(f"📊 Environment: {settings.ENVIRONMENT}")
    print(f"🔗 CORS Origins: {settings.CORS_ORIGINS}")
    # Initialize database connections, WebSocket connections, etc.


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("🛑 Shutting down AI Trading Predictor API...")
    # Close database connections, WebSocket connections, etc.


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
