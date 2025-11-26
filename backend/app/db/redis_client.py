"""
Redis Client - Production-Ready Caching & Rate Limiting
- Smart caching (5s price, 30s prediction)
- Rate limiting (100 req/hour per user)
- Leaderboard (sorted sets)
- Connection pooling
"""
import logging
import json
from typing import Optional, Any, List, Dict
from datetime import timedelta
import redis.asyncio as aioredis
from redis.asyncio.connection import ConnectionPool
from redis.exceptions import RedisError, ConnectionError
import asyncio
from functools import wraps

from app.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """
    Production-ready Redis client with:
    - Async operations
    - Connection pooling
    - Retry logic
    - Smart caching strategies
    """

    def __init__(self):
        self._client: Optional[aioredis.Redis] = None
        self._pool: Optional[ConnectionPool] = None
        self._initialized = False

    async def initialize(self):
        """Initialize Redis connection (called on app startup)"""
        if self._initialized:
            return

        try:
            # Create connection pool
            self._pool = ConnectionPool.from_url(
                settings.REDIS_URL,
                password=settings.REDIS_PASSWORD,
                db=settings.REDIS_DB,
                max_connections=settings.REDIS_MAX_CONNECTIONS,
                socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
                decode_responses=True,
                retry_on_timeout=True
            )

            # Create Redis client
            self._client = aioredis.Redis(connection_pool=self._pool)

            # Test connection
            await self._client.ping()

            self._initialized = True
            logger.info("✅ Redis initialized successfully")

        except Exception as e:
            logger.error(f"❌ Failed to initialize Redis: {e}")
            raise

    @property
    def client(self) -> aioredis.Redis:
        """Get Redis client"""
        if not self._initialized:
            raise RuntimeError("Redis not initialized. Call initialize() first.")
        return self._client

    async def close(self):
        """Close Redis connection"""
        if self._client:
            await self._client.close()
            await self._pool.disconnect()
            logger.info("Redis connection closed")

    # ============================================
    # CACHING METHODS
    # ============================================

    async def cache_price(self, symbol: str, price: float, ttl: int = None):
        """
        Cache price data (5s TTL by default)

        Args:
            symbol: Trading symbol
            price: Current price
            ttl: Time to live in seconds
        """
        try:
            key = f"price:{symbol}"
            ttl = ttl or settings.PRICE_CACHE_TTL
            await self._client.setex(key, ttl, str(price))
        except RedisError as e:
            logger.error(f"Failed to cache price: {e}")

    async def get_cached_price(self, symbol: str) -> Optional[float]:
        """Get cached price"""
        try:
            key = f"price:{symbol}"
            price = await self._client.get(key)
            return float(price) if price else None
        except (RedisError, ValueError) as e:
            logger.error(f"Failed to get cached price: {e}")
            return None

    async def cache_prediction(self, prediction_id: str, data: Dict, ttl: int = None):
        """
        Cache prediction data (30s TTL by default)

        Args:
            prediction_id: Unique prediction ID
            data: Prediction data dictionary
            ttl: Time to live in seconds
        """
        try:
            key = f"prediction:{prediction_id}"
            ttl = ttl or settings.PREDICTION_CACHE_TTL
            await self._client.setex(key, ttl, json.dumps(data))
        except RedisError as e:
            logger.error(f"Failed to cache prediction: {e}")

    async def get_cached_prediction(self, prediction_id: str) -> Optional[Dict]:
        """Get cached prediction"""
        try:
            key = f"prediction:{prediction_id}"
            data = await self._client.get(key)
            return json.loads(data) if data else None
        except (RedisError, json.JSONDecodeError) as e:
            logger.error(f"Failed to get cached prediction: {e}")
            return None

    async def cache_user(self, user_id: str, data: Dict, ttl: int = None):
        """Cache user data (5min TTL by default)"""
        try:
            key = f"user:{user_id}"
            ttl = ttl or settings.USER_CACHE_TTL
            await self._client.setex(key, ttl, json.dumps(data))
        except RedisError as e:
            logger.error(f"Failed to cache user: {e}")

    async def get_cached_user(self, user_id: str) -> Optional[Dict]:
        """Get cached user data"""
        try:
            key = f"user:{user_id}"
            data = await self._client.get(key)
            return json.loads(data) if data else None
        except (RedisError, json.JSONDecodeError) as e:
            logger.error(f"Failed to get cached user: {e}")
            return None

    async def invalidate_cache(self, pattern: str):
        """Invalidate cache by pattern"""
        try:
            keys = await self._client.keys(pattern)
            if keys:
                await self._client.delete(*keys)
        except RedisError as e:
            logger.error(f"Failed to invalidate cache: {e}")

    # ============================================
    # RATE LIMITING METHODS
    # ============================================

    async def check_rate_limit(
        self,
        user_id: str,
        limit: int = 100,
        window: int = 3600
    ) -> tuple[bool, int, int]:
        """
        Check if user is within rate limit (sliding window)

        Args:
            user_id: User ID
            limit: Max requests allowed
            window: Time window in seconds (default 1 hour)

        Returns:
            (allowed, current_count, remaining)
        """
        try:
            key = f"ratelimit:{user_id}:{window}"

            # Increment counter
            count = await self._client.incr(key)

            # Set expiry on first request
            if count == 1:
                await self._client.expire(key, window)

            allowed = count <= limit
            remaining = max(0, limit - count)

            if not allowed:
                logger.warning(f"Rate limit exceeded for user {user_id}: {count}/{limit}")

            return allowed, count, remaining

        except RedisError as e:
            logger.error(f"Rate limit check failed: {e}")
            # Allow request if Redis fails (fail open)
            return True, 0, limit

    async def get_remaining_requests(self, user_id: str, limit: int = 100, window: int = 3600) -> int:
        """Get remaining requests for user"""
        try:
            key = f"ratelimit:{user_id}:{window}"
            count = await self._client.get(key)
            count = int(count) if count else 0
            return max(0, limit - count)
        except RedisError as e:
            logger.error(f"Failed to get remaining requests: {e}")
            return limit

    async def reset_rate_limit(self, user_id: str, window: int = 3600):
        """Reset rate limit for user"""
        try:
            key = f"ratelimit:{user_id}:{window}"
            await self._client.delete(key)
        except RedisError as e:
            logger.error(f"Failed to reset rate limit: {e}")

    # ============================================
    # LEADERBOARD METHODS (Sorted Sets)
    # ============================================

    async def update_leaderboard(self, user_id: str, accuracy: float, leaderboard: str = "global"):
        """
        Update user's position in leaderboard

        Args:
            user_id: User ID
            accuracy: Accuracy score (0-100)
            leaderboard: Leaderboard name
        """
        try:
            key = f"leaderboard:{leaderboard}"
            await self._client.zadd(key, {user_id: accuracy})
        except RedisError as e:
            logger.error(f"Failed to update leaderboard: {e}")

    async def get_leaderboard(
        self,
        leaderboard: str = "global",
        start: int = 0,
        end: int = 9
    ) -> List[Dict]:
        """
        Get top users from leaderboard

        Args:
            leaderboard: Leaderboard name
            start: Start rank (0-indexed)
            end: End rank

        Returns:
            List of {user_id, accuracy, rank}
        """
        try:
            key = f"leaderboard:{leaderboard}"

            # Get top users with scores (descending order)
            results = await self._client.zrevrange(
                key, start, end, withscores=True
            )

            leaderboard_data = []
            for rank, (user_id, accuracy) in enumerate(results, start=start + 1):
                leaderboard_data.append({
                    "user_id": user_id,
                    "accuracy": float(accuracy),
                    "rank": rank
                })

            return leaderboard_data

        except RedisError as e:
            logger.error(f"Failed to get leaderboard: {e}")
            return []

    async def get_user_rank(self, user_id: str, leaderboard: str = "global") -> Optional[Dict]:
        """Get user's rank in leaderboard"""
        try:
            key = f"leaderboard:{leaderboard}"

            # Get rank (0-indexed)
            rank = await self._client.zrevrank(key, user_id)
            if rank is None:
                return None

            # Get score
            accuracy = await self._client.zscore(key, user_id)

            return {
                "user_id": user_id,
                "accuracy": float(accuracy) if accuracy else 0,
                "rank": rank + 1  # Convert to 1-indexed
            }

        except RedisError as e:
            logger.error(f"Failed to get user rank: {e}")
            return None

    # ============================================
    # RETRY LOGIC
    # ============================================

    async def retry_on_error(self, func, *args, max_retries=3, **kwargs):
        """Retry logic for Redis operations"""
        for attempt in range(max_retries):
            try:
                return await func(*args, **kwargs)
            except (ConnectionError, RedisError) as e:
                if attempt == max_retries - 1:
                    logger.error(f"Max retries reached for {func.__name__}: {e}")
                    raise
                logger.warning(f"Retry {attempt + 1}/{max_retries} for {func.__name__}: {e}")
                await asyncio.sleep(2 ** attempt)
            except Exception as e:
                logger.error(f"Unexpected error in {func.__name__}: {e}")
                raise


def retry_on_redis_error(max_retries=3):
    """Decorator for automatic retry on Redis errors"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except (ConnectionError, RedisError) as e:
                    if attempt == max_retries - 1:
                        raise
                    logger.warning(f"Redis error, retry {attempt + 1}/{max_retries}: {e}")
                    await asyncio.sleep(2 ** attempt)
        return wrapper
    return decorator


# Singleton instance
redis_client = RedisClient()


# Convenience function
def get_redis() -> RedisClient:
    """Get Redis client"""
    return redis_client
