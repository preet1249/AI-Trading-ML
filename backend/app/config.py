"""
Configuration Management
Centralized settings for all services with environment variable support
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    Application Settings
    Loaded from .env file
    """

    # ============================================
    # Application Settings
    # ============================================
    APP_NAME: str = "AI Trading Prediction Model"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development, staging, production

    # ============================================
    # API Keys - AI Models
    # ============================================
    OPENROUTER_API_KEY: str
    OPENROUTER_MODEL: str = "qwen/qwen-2.5-72b-instruct"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    TWELVE_DATA_API_KEY: str

    # ============================================
    # Supabase Configuration
    # ============================================
    SUPABASE_URL: str
    SUPABASE_KEY: str  # anon/public key
    SUPABASE_SERVICE_KEY: str  # service role key (admin access)
    SUPABASE_JWT_SECRET: str

    # ============================================
    # MongoDB Configuration (Flexible Analytics)
    # ============================================
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "ai_trading"
    MONGODB_MAX_POOL_SIZE: int = 50
    MONGODB_MIN_POOL_SIZE: int = 10
    MONGODB_TIMEOUT: int = 5000  # milliseconds

    # ============================================
    # Redis Configuration (Caching & Rate Limiting)
    # ============================================
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    REDIS_MAX_CONNECTIONS: int = 50
    REDIS_SOCKET_TIMEOUT: int = 5

    # Cache TTLs
    PRICE_CACHE_TTL: int = 5  # 5 seconds for real-time prices
    PREDICTION_CACHE_TTL: int = 30  # 30 seconds for predictions
    USER_CACHE_TTL: int = 300  # 5 minutes for user data

    # ============================================
    # Security Settings
    # ============================================
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    JWT_ALGORITHM: str = "HS256"  # JWT algorithm for token verification
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ============================================
    # Rate Limiting (Scalable)
    # ============================================
    RATE_LIMIT_PER_MINUTE: int = 60  # Same for all users initially
    RATE_LIMIT_PER_HOUR: int = 1000  # Burst protection
    RATE_LIMIT_PER_DAY: int = 10000  # Daily cap

    # Future pricing tiers (ready to scale)
    FREE_TIER_LIMIT_MINUTE: int = 10
    PRO_TIER_LIMIT_MINUTE: int = 60
    PREMIUM_TIER_LIMIT_MINUTE: int = 300

    # ============================================
    # Database Connection Pool (Scalability)
    # ============================================
    DB_POOL_SIZE: int = 20  # Max concurrent connections
    DB_MAX_OVERFLOW: int = 10  # Extra connections when pool full
    DB_POOL_TIMEOUT: int = 30  # Seconds to wait for connection

    # ============================================
    # CORS Settings
    # ============================================
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:3001",
        "https://your-production-domain.com"
    ]

    # ============================================
    # API Configuration
    # ============================================
    API_V1_PREFIX: str = "/api/v1"

    # Binance API
    BINANCE_API_KEY: Optional[str] = None
    BINANCE_API_SECRET: Optional[str] = None

    # ============================================
    # WebSocket URLs
    # ============================================
    BINANCE_WS_URL: str = "wss://stream.binance.com:9443/ws"
    BINANCE_REST_URL: str = "https://api.binance.com"
    TWELVE_DATA_WS_URL: str = "wss://ws.twelvedata.com/v1/quotes/price"

    # ============================================
    # Logging Configuration
    # ============================================
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # ============================================
    # Performance & Scalability
    # ============================================
    MAX_WORKERS: int = 4  # For background tasks
    REQUEST_TIMEOUT: int = 30  # Seconds
    CACHE_TTL: int = 300  # 5 minutes default cache

    # ============================================
    # Agent Configuration (Qwen AI)
    # ============================================
    QWEN_TEMPERATURE: float = 0.7
    QWEN_MAX_TOKENS: int = 2000
    AGENT_TIMEOUT: int = 30
    TA_AGENT_TIMEOUT: int = 10
    NEWS_AGENT_TIMEOUT: int = 10
    PREDICT_AGENT_TIMEOUT: int = 10

    # ============================================
    # Caching TTLs
    # ============================================
    TA_CACHE_TTL: int = 60
    NEWS_CACHE_TTL: int = 600

    # ============================================
    # Server Configuration
    # ============================================
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Singleton instance
settings = Settings()
