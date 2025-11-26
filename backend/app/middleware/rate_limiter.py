"""
Rate Limiting Middleware - Redis-based
- 100 requests/hour per user (configurable)
- Sliding window algorithm
- Graceful degradation if Redis fails
- Ready for pricing tiers
"""
import logging
from typing import Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import time

from app.db.redis_client import get_redis
from app.services.auth_service import auth_service
from app.config import settings

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Production-ready rate limiter
    - Per-user limits
    - Multiple time windows
    - Pricing tier support
    """

    # Tier limits (requests per window)
    TIER_LIMITS = {
        "free": {
            "minute": settings.FREE_TIER_LIMIT_MINUTE,
            "hour": 100,
            "day": 1000
        },
        "pro": {
            "minute": settings.PRO_TIER_LIMIT_MINUTE,
            "hour": 600,
            "day": 10000
        },
        "premium": {
            "minute": settings.PREMIUM_TIER_LIMIT_MINUTE,
            "hour": 3000,
            "day": 50000
        }
    }

    @classmethod
    async def get_user_tier(cls, user_id: str) -> str:
        """Get user's subscription tier (from cache or DB)"""
        try:
            redis = get_redis()

            # Check cache first
            cached_user = await redis.get_cached_user(user_id)
            if cached_user:
                return cached_user.get("subscription_tier", "free")

            # Not in cache, get from Supabase
            from app.db.supabase_client import get_admin_supabase
            supabase = get_admin_supabase()

            response = supabase.table("users").select("subscription_tier").eq("id", user_id).single().execute()

            if response.data:
                tier = response.data.get("subscription_tier", "free")
                # Cache user data
                await redis.cache_user(user_id, {"subscription_tier": tier})
                return tier

            return "free"

        except Exception as e:
            logger.error(f"Error getting user tier: {e}")
            return "free"

    @classmethod
    async def check_rate_limit(
        cls,
        user_id: str,
        tier: str = "free",
        window: str = "hour"
    ) -> tuple[bool, dict]:
        """
        Check if user is within rate limit

        Args:
            user_id: User ID
            tier: Subscription tier
            window: Time window ("minute", "hour", "day")

        Returns:
            (allowed, metadata)
        """
        try:
            redis = get_redis()

            # Get limits for tier
            tier_limits = cls.TIER_LIMITS.get(tier, cls.TIER_LIMITS["free"])
            limit = tier_limits.get(window, 100)

            # Window in seconds
            window_seconds = {
                "minute": 60,
                "hour": 3600,
                "day": 86400
            }.get(window, 3600)

            # Check Redis rate limit
            allowed, current_count, remaining = await redis.check_rate_limit(
                user_id=user_id,
                limit=limit,
                window=window_seconds
            )

            metadata = {
                "limit": limit,
                "current": current_count,
                "remaining": remaining,
                "window": window,
                "tier": tier,
                "reset_in": window_seconds
            }

            return allowed, metadata

        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # Fail open - allow request if Redis fails
            return True, {"error": "Rate limit check unavailable"}

    @classmethod
    async def get_user_from_token(cls, authorization: Optional[str]) -> Optional[dict]:
        """Extract user from JWT token"""
        try:
            if not authorization or not authorization.startswith("Bearer "):
                return None

            token = authorization.replace("Bearer ", "")
            user_data = await auth_service.verify_token(token)

            return user_data

        except Exception as e:
            logger.error(f"Error extracting user from token: {e}")
            return None


async def rate_limit_middleware(request: Request, call_next):
    """
    FastAPI middleware for rate limiting

    Usage:
        app.middleware("http")(rate_limit_middleware)
    """
    # Skip rate limiting for certain paths
    skip_paths = ["/", "/health", "/docs", "/openapi.json", "/api/v1/auth/signup", "/api/v1/auth/login"]

    if request.url.path in skip_paths:
        return await call_next(request)

    try:
        # Get user from token
        authorization = request.headers.get("authorization")
        user_data = await RateLimiter.get_user_from_token(authorization)

        if not user_data:
            # No token - apply IP-based rate limiting (more lenient)
            client_ip = request.client.host
            user_id = f"ip:{client_ip}"
            tier = "free"
        else:
            user_id = user_data.get("id")
            tier = await RateLimiter.get_user_tier(user_id)

        # Check rate limit (hour window)
        allowed, metadata = await RateLimiter.check_rate_limit(
            user_id=user_id,
            tier=tier,
            window="hour"
        )

        if not allowed:
            logger.warning(
                f"Rate limit exceeded: {user_id} | "
                f"{metadata['current']}/{metadata['limit']} requests"
            )

            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "success": False,
                    "error": "Rate limit exceeded",
                    "message": f"You have exceeded your rate limit of {metadata['limit']} requests per hour",
                    "metadata": {
                        "limit": metadata["limit"],
                        "remaining": metadata["remaining"],
                        "reset_in_seconds": metadata["reset_in"],
                        "tier": metadata["tier"],
                        "upgrade_url": "/upgrade"
                    }
                }
            )

        # Add rate limit headers
        response = await call_next(request)

        response.headers["X-RateLimit-Limit"] = str(metadata["limit"])
        response.headers["X-RateLimit-Remaining"] = str(metadata["remaining"])
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + metadata["reset_in"])
        response.headers["X-RateLimit-Tier"] = metadata["tier"]

        return response

    except Exception as e:
        logger.error(f"Rate limit middleware error: {e}")
        # Fail open - allow request on error
        return await call_next(request)


# Decorator for manual rate limiting
def require_rate_limit(tier: str = None, window: str = "hour"):
    """
    Decorator for manual rate limiting on specific endpoints

    Usage:
        @app.post("/api/v1/predictions")
        @require_rate_limit(tier="free", window="hour")
        async def get_prediction():
            ...
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Get request from kwargs
            request = kwargs.get("request") or args[0] if args else None

            if not request:
                return await func(*args, **kwargs)

            # Extract user
            authorization = request.headers.get("authorization")
            user_data = await RateLimiter.get_user_from_token(authorization)

            if not user_data:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required for this endpoint"
                )

            user_id = user_data.get("id")
            user_tier = await RateLimiter.get_user_tier(user_id)

            # If specific tier required, check it
            if tier and user_tier != tier:
                allowed, metadata = await RateLimiter.check_rate_limit(
                    user_id=user_id,
                    tier=tier,
                    window=window
                )
            else:
                allowed, metadata = await RateLimiter.check_rate_limit(
                    user_id=user_id,
                    tier=user_tier,
                    window=window
                )

            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "Rate limit exceeded",
                        "metadata": metadata
                    }
                )

            return await func(*args, **kwargs)

        return wrapper
    return decorator
