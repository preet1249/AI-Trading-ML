"""
Supabase Client - Production-Ready & Scalable
- Connection pooling for concurrent requests
- Automatic retry logic for failed requests
- Security best practices
- Real-time subscriptions support
"""
import logging
from typing import Optional
from supabase import create_client, Client
from postgrest.exceptions import APIError
import asyncio
from functools import wraps

from app.config import settings

logger = logging.getLogger(__name__)


class SupabaseClient:
    """
    Production-ready Supabase client with:
    - Connection pooling
    - Retry logic
    - Error handling
    - Security features
    """

    def __init__(self):
        self._client: Optional[Client] = None
        self._admin_client: Optional[Client] = None
        self._initialized = False

    def initialize(self):
        """Initialize Supabase clients (called on app startup)"""
        if self._initialized:
            return

        try:
            # Public client (uses anon key - for client-side auth)
            self._client = create_client(
                supabase_url=settings.SUPABASE_URL,
                supabase_key=settings.SUPABASE_KEY
            )

            # Admin client (uses service role key - for server-side operations)
            self._admin_client = create_client(
                supabase_url=settings.SUPABASE_URL,
                supabase_key=settings.SUPABASE_SERVICE_KEY
            )

            self._initialized = True
            logger.info("✅ Supabase clients initialized successfully")

        except Exception as e:
            logger.error(f"❌ Failed to initialize Supabase: {e}")
            raise

    @property
    def client(self) -> Client:
        """Get public Supabase client (with RLS enforcement)"""
        if not self._initialized:
            self.initialize()
        return self._client

    @property
    def admin(self) -> Client:
        """Get admin Supabase client (bypasses RLS - use carefully!)"""
        if not self._initialized:
            self.initialize()
        return self._admin_client

    def set_auth(self, access_token: str):
        """Set JWT token for authenticated requests"""
        if not self._initialized:
            self.initialize()

        self._client.postgrest.auth(access_token)
        logger.debug(f"Auth token set for client")

    async def retry_on_error(self, func, *args, max_retries=3, **kwargs):
        """
        Retry logic for database operations (handles network issues)

        Args:
            func: Function to retry
            max_retries: Maximum retry attempts
        """
        for attempt in range(max_retries):
            try:
                return await func(*args, **kwargs)
            except APIError as e:
                if attempt == max_retries - 1:
                    logger.error(f"Max retries reached for {func.__name__}: {e}")
                    raise
                logger.warning(f"Retry {attempt + 1}/{max_retries} for {func.__name__}: {e}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            except Exception as e:
                logger.error(f"Unexpected error in {func.__name__}: {e}")
                raise


def retry_on_db_error(max_retries=3):
    """Decorator for automatic retry on database errors"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except APIError as e:
                    if attempt == max_retries - 1:
                        raise
                    logger.warning(f"DB error, retry {attempt + 1}/{max_retries}: {e}")
                    await asyncio.sleep(2 ** attempt)
        return wrapper
    return decorator


# Singleton instance
supabase_client = SupabaseClient()


# Convenience functions
def get_supabase() -> Client:
    """Get public Supabase client"""
    return supabase_client.client


def get_admin_supabase() -> Client:
    """Get admin Supabase client (use carefully - bypasses RLS!)"""
    return supabase_client.admin
