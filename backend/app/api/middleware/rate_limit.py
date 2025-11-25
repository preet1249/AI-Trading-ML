"""
Rate Limiting Middleware
Uses Redis (Upstash) for tracking request rates
"""
from fastapi import HTTPException, status, Request
from typing import Optional
import time

from app.config import settings
from app.models.database import get_redis_client


class RateLimiter:
    """Rate limiter using Redis"""

    def __init__(
        self,
        requests_per_minute: int = settings.RATE_LIMIT_PER_MINUTE,
        requests_per_day: int = settings.RATE_LIMIT_PER_DAY
    ):
        self.requests_per_minute = requests_per_minute
        self.requests_per_day = requests_per_day

    async def check_rate_limit(self, user_id: str) -> None:
        """
        Check if user has exceeded rate limits

        Args:
            user_id: User ID to check

        Raises:
            HTTPException: If rate limit exceeded
        """
        redis = await get_redis_client()

        # Check per-minute limit
        minute_key = f"ratelimit:{user_id}:minute"
        minute_count = await redis.incr(minute_key)

        if minute_count == 1:
            await redis.expire(minute_key, 60)

        if minute_count > self.requests_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: {self.requests_per_minute} requests per minute"
            )

        # Check per-day limit
        day_key = f"ratelimit:{user_id}:day"
        day_count = await redis.incr(day_key)

        if day_count == 1:
            await redis.expire(day_key, 86400)  # 24 hours

        if day_count > self.requests_per_day:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: {self.requests_per_day} requests per day"
            )


# Global rate limiter instance
rate_limiter = RateLimiter()
