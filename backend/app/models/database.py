"""
Database Connections
MongoDB and Redis (Upstash) clients
"""
from motor.motor_asyncio import AsyncIOMotorClient
from redis.asyncio import Redis
from typing import Optional

from app.config import settings

# ============================================
# MongoDB Connection
# ============================================

_mongo_client: Optional[AsyncIOMotorClient] = None


async def get_mongo_client() -> AsyncIOMotorClient:
    """Get MongoDB client (singleton)"""
    global _mongo_client

    if _mongo_client is None:
        _mongo_client = AsyncIOMotorClient(settings.MONGODB_URI)

    return _mongo_client


async def get_mongo_db():
    """Get MongoDB database"""
    client = await get_mongo_client()
    return client[settings.MONGODB_DB_NAME]


async def close_mongo_connection():
    """Close MongoDB connection"""
    global _mongo_client
    if _mongo_client:
        _mongo_client.close()
        _mongo_client = None


# ============================================
# Redis Connection (Upstash)
# ============================================

_redis_client: Optional[Redis] = None


async def get_redis_client() -> Redis:
    """Get Redis client (singleton) - Uses Upstash in production"""
    global _redis_client

    if _redis_client is None:
        # Use Upstash Redis in production, local Redis in development
        redis_url = settings.redis_connection

        _redis_client = Redis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True
        )

    return _redis_client


async def close_redis_connection():
    """Close Redis connection"""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None


# ============================================
# Database Utilities
# ============================================

async def ping_mongodb() -> bool:
    """Check MongoDB connection"""
    try:
        client = await get_mongo_client()
        await client.admin.command('ping')
        return True
    except Exception as e:
        print(f"MongoDB connection failed: {e}")
        return False


async def ping_redis() -> bool:
    """Check Redis connection"""
    try:
        redis = await get_redis_client()
        await redis.ping()
        return True
    except Exception as e:
        print(f"Redis connection failed: {e}")
        return False
