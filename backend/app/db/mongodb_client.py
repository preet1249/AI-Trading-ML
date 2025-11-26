"""
MongoDB Client - Production-Ready & Scalable
- Connection pooling for concurrent requests
- Automatic retry logic
- Flexible schema for analytics
- Indexes for performance
"""
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo import IndexModel, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, OperationFailure
import asyncio
from functools import wraps

from app.config import settings

logger = logging.getLogger(__name__)


class MongoDBClient:
    """
    Production-ready MongoDB client with:
    - Async operations (Motor)
    - Connection pooling
    - Retry logic
    - Automatic indexing
    """

    def __init__(self):
        self._client: Optional[AsyncIOMotorClient] = None
        self._db: Optional[AsyncIOMotorDatabase] = None
        self._initialized = False

    async def initialize(self):
        """Initialize MongoDB connection (called on app startup)"""
        if self._initialized:
            return

        try:
            # Create async MongoDB client with connection pooling
            self._client = AsyncIOMotorClient(
                settings.MONGODB_URL,
                maxPoolSize=settings.MONGODB_MAX_POOL_SIZE,
                minPoolSize=settings.MONGODB_MIN_POOL_SIZE,
                serverSelectionTimeoutMS=settings.MONGODB_TIMEOUT,
                retryWrites=True,
                retryReads=True
            )

            # Get database
            self._db = self._client[settings.MONGODB_DB_NAME]

            # Test connection
            await self._client.admin.command('ping')

            # Create indexes
            await self._create_indexes()

            self._initialized = True
            logger.info("✅ MongoDB initialized successfully")

        except Exception as e:
            logger.error(f"❌ Failed to initialize MongoDB: {e}")
            raise

    async def _create_indexes(self):
        """Create indexes for performance"""
        try:
            # Predictions collection indexes
            predictions = self._db.predictions
            await predictions.create_indexes([
                IndexModel([("user_id", ASCENDING), ("created_at", DESCENDING)]),
                IndexModel([("symbol", ASCENDING), ("created_at", DESCENDING)]),
                IndexModel([("created_at", DESCENDING)]),
                IndexModel([("outcome", ASCENDING)]),
                IndexModel([("accuracy_score", DESCENDING)]),
            ])

            # User analytics indexes
            user_analytics = self._db.user_analytics
            await user_analytics.create_indexes([
                IndexModel([("user_id", ASCENDING)], unique=True),
                IndexModel([("total_accuracy", DESCENDING)]),
                IndexModel([("total_predictions", DESCENDING)]),
            ])

            logger.info("✅ MongoDB indexes created")

        except Exception as e:
            logger.warning(f"Index creation warning: {e}")

    @property
    def db(self) -> AsyncIOMotorDatabase:
        """Get database instance"""
        if not self._initialized:
            raise RuntimeError("MongoDB not initialized. Call initialize() first.")
        return self._db

    @property
    def predictions(self) -> AsyncIOMotorCollection:
        """Get predictions collection"""
        return self.db.predictions

    @property
    def user_analytics(self) -> AsyncIOMotorCollection:
        """Get user analytics collection"""
        return self.db.user_analytics

    @property
    def training_data(self) -> AsyncIOMotorCollection:
        """Get AI training data collection"""
        return self.db.training_data

    async def close(self):
        """Close MongoDB connection"""
        if self._client:
            self._client.close()
            logger.info("MongoDB connection closed")

    async def retry_on_error(self, func, *args, max_retries=3, **kwargs):
        """
        Retry logic for MongoDB operations

        Args:
            func: Async function to retry
            max_retries: Maximum retry attempts
        """
        for attempt in range(max_retries):
            try:
                return await func(*args, **kwargs)
            except (ConnectionFailure, OperationFailure) as e:
                if attempt == max_retries - 1:
                    logger.error(f"Max retries reached for {func.__name__}: {e}")
                    raise
                logger.warning(f"Retry {attempt + 1}/{max_retries} for {func.__name__}: {e}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            except Exception as e:
                logger.error(f"Unexpected error in {func.__name__}: {e}")
                raise


def retry_on_mongo_error(max_retries=3):
    """Decorator for automatic retry on MongoDB errors"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except (ConnectionFailure, OperationFailure) as e:
                    if attempt == max_retries - 1:
                        raise
                    logger.warning(f"MongoDB error, retry {attempt + 1}/{max_retries}: {e}")
                    await asyncio.sleep(2 ** attempt)
        return wrapper
    return decorator


# Singleton instance
mongodb_client = MongoDBClient()


# Convenience function
def get_mongodb() -> MongoDBClient:
    """Get MongoDB client"""
    return mongodb_client
