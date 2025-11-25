"""
Application Configuration
Loads environment variables and provides settings
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings from environment variables"""

    # ============================================
    # Application Config
    # ============================================
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ============================================
    # API Keys
    # ============================================
    OPENROUTER_API_KEY: str
    OPENROUTER_MODEL: str = "qwen/qwen-2.5-72b-instruct"

    TWELVE_DATA_API_KEY: str

    GOOGLE_CUSTOM_SEARCH_API_KEY: str = ""
    GOOGLE_SEARCH_ENGINE_ID: str = ""

    # ============================================
    # Database & Storage
    # ============================================
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "trading_agent"

    # Redis - Use Upstash in production, local in development
    REDIS_URL: str = "redis://localhost:6379"
    UPSTASH_REDIS_URL: str = ""
    UPSTASH_REDIS_TOKEN: str = ""

    # Supabase
    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_JWT_SECRET: str

    # ============================================
    # Security
    # ============================================
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # ============================================
    # Rate Limiting
    # ============================================
    RATE_LIMIT_PER_MINUTE: int = 10
    RATE_LIMIT_PER_DAY: int = 100
    RATE_LIMIT_BURST: int = 5

    # ============================================
    # WebSocket URLs
    # ============================================
    BINANCE_WS_URL: str = "wss://stream.binance.com:9443/ws"
    TWELVE_DATA_WS_URL: str = "wss://ws.twelvedata.com/v1/quotes/price"

    # ============================================
    # Logging
    # ============================================
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # ============================================
    # Agent Config
    # ============================================
    AGENT_TIMEOUT: int = 30
    TA_AGENT_TIMEOUT: int = 10
    NEWS_AGENT_TIMEOUT: int = 10
    PREDICT_AGENT_TIMEOUT: int = 10

    QWEN_TEMPERATURE: float = 0.7
    QWEN_MAX_TOKENS: int = 2000

    # ============================================
    # Caching
    # ============================================
    CACHE_TTL: int = 300
    TA_CACHE_TTL: int = 60
    NEWS_CACHE_TTL: int = 600

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def redis_connection(self) -> str:
        """Get Redis connection URL (Upstash in production, local in dev)"""
        if self.ENVIRONMENT == "production" and self.UPSTASH_REDIS_URL:
            return self.UPSTASH_REDIS_URL
        return self.REDIS_URL


# Global settings instance
settings = Settings()
