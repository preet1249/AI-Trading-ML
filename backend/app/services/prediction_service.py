"""
Prediction Service - Dual Storage Strategy
- MongoDB: Flexible prediction storage + analytics
- Supabase: Structured queries with RLS
- Redis: Smart caching (30s TTL)
"""
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import uuid

from app.db.mongodb_client import get_mongodb
from app.db.supabase_client import get_admin_supabase
from app.db.redis_client import get_redis

logger = logging.getLogger(__name__)


class PredictionService:
    """Production-ready prediction service with dual storage"""

    @classmethod
    async def save_prediction(
        cls,
        user_id: str,
        prediction_data: Dict
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Save prediction to both MongoDB and Supabase

        Args:
            user_id: User ID
            prediction_data: Complete prediction data

        Returns:
            (success, message, prediction_id)
        """
        try:
            prediction_id = str(uuid.uuid4())

            # Extract key fields
            symbol = prediction_data.get("symbol", "")
            direction = prediction_data.get("direction", "NEUTRAL")
            confidence = prediction_data.get("confidence", 0)
            entry_price = prediction_data.get("entry_price", 0)
            stop_loss = prediction_data.get("stop_loss", 0)
            take_profits = prediction_data.get("take_profits", [])

            # MongoDB: Store FULL prediction data (flexible schema)
            mongo = get_mongodb()
            mongo_doc = {
                "_id": prediction_id,
                "user_id": user_id,
                "symbol": symbol,
                "direction": direction,
                "confidence": confidence,
                "entry_price": entry_price,
                "stop_loss": stop_loss,
                "take_profits": take_profits,
                "prediction_data": prediction_data,
                "created_at": datetime.utcnow(),
                "outcome": None,  # Will be updated later
                "outcome_checked_at": None,
                "accuracy_score": None
            }
            await mongo.predictions.insert_one(mongo_doc)

            # Supabase: Store structured data (for RLS queries)
            supabase = get_admin_supabase()
            supabase_doc = {
                "id": prediction_id,
                "user_id": user_id,
                "query": prediction_data.get("query", ""),
                "symbol": symbol,
                "exchange": prediction_data.get("exchange", ""),
                "market_type": prediction_data.get("market_type", "crypto"),
                "direction": direction,
                "confidence": confidence,
                "risk_level": prediction_data.get("risk_level", "MEDIUM"),
                "entry_price": float(entry_price) if entry_price else None,
                "entry_reason": prediction_data.get("entry_reason", ""),
                "entry_confidence": prediction_data.get("entry_confidence", 0),
                "stop_loss": float(stop_loss) if stop_loss else None,
                "target_price": float(take_profits[0]["price"]) if take_profits else None,
                "take_profits": take_profits,
                "timeframe": prediction_data.get("timeframe", ""),
                "analysis_type": prediction_data.get("analysis_type", ""),
                "fibonacci_levels": prediction_data.get("fibonacci_levels", {}),
                "pivot_points": prediction_data.get("pivot_points", {}),
                "order_blocks": prediction_data.get("order_blocks", []),
                "market_condition": prediction_data.get("market_condition", ""),
                "prediction_data": prediction_data,
                "market_closed": prediction_data.get("market_closed", False),
                "created_at": datetime.utcnow().isoformat()
            }
            supabase.table("predictions").insert(supabase_doc).execute()

            # Redis: Cache prediction (30s)
            redis = get_redis()
            await redis.cache_prediction(prediction_id, prediction_data)

            logger.info(f"✅ Prediction saved: {prediction_id} for {symbol}")
            return True, "Prediction saved", prediction_id

        except Exception as e:
            logger.error(f"Failed to save prediction: {e}")
            return False, f"Failed to save prediction: {str(e)}", None

    @classmethod
    async def get_user_predictions(
        cls,
        user_id: str,
        limit: int = 10,
        skip: int = 0
    ) -> List[Dict]:
        """
        Get user's prediction history (from MongoDB for flexibility)

        Args:
            user_id: User ID
            limit: Max predictions to return
            skip: Skip N predictions (pagination)

        Returns:
            List of predictions
        """
        try:
            mongo = get_mongodb()

            predictions = await mongo.predictions.find(
                {"user_id": user_id}
            ).sort(
                "created_at", -1
            ).skip(skip).limit(limit).to_list(length=limit)

            # Convert ObjectId to string
            for pred in predictions:
                pred["_id"] = str(pred["_id"])

            return predictions

        except Exception as e:
            logger.error(f"Failed to get user predictions: {e}")
            return []

    @classmethod
    async def get_prediction_by_id(cls, prediction_id: str) -> Optional[Dict]:
        """Get single prediction by ID (check cache first)"""
        try:
            # Check Redis cache first
            redis = get_redis()
            cached = await redis.get_cached_prediction(prediction_id)
            if cached:
                logger.debug(f"Cache hit for prediction {prediction_id}")
                return cached

            # Not in cache, get from MongoDB
            mongo = get_mongodb()
            prediction = await mongo.predictions.find_one({"_id": prediction_id})

            if prediction:
                prediction["_id"] = str(prediction["_id"])
                # Cache for next time
                await redis.cache_prediction(prediction_id, prediction)
                return prediction

            return None

        except Exception as e:
            logger.error(f"Failed to get prediction: {e}")
            return None

    @classmethod
    async def get_user_stats(cls, user_id: str) -> Dict:
        """Get user's prediction statistics"""
        try:
            mongo = get_mongodb()

            # Aggregate statistics
            pipeline = [
                {"$match": {"user_id": user_id}},
                {"$group": {
                    "_id": None,
                    "total": {"$sum": 1},
                    "wins": {"$sum": {"$cond": [{"$eq": ["$outcome", "WIN"]}, 1, 0]}},
                    "losses": {"$sum": {"$cond": [{"$eq": ["$outcome", "LOSS"]}, 1, 0]}},
                    "pending": {"$sum": {"$cond": [{"$eq": ["$outcome", None]}, 1, 0]}},
                    "avg_accuracy": {"$avg": "$accuracy_score"}
                }}
            ]

            result = await mongo.predictions.aggregate(pipeline).to_list(length=1)

            if result:
                stats = result[0]
                return {
                    "total_predictions": stats.get("total", 0),
                    "wins": stats.get("wins", 0),
                    "losses": stats.get("losses", 0),
                    "pending": stats.get("pending", 0),
                    "win_rate": (stats.get("wins", 0) / stats.get("total", 1)) * 100,
                    "avg_accuracy": stats.get("avg_accuracy", 0) or 0
                }
            else:
                return {
                    "total_predictions": 0,
                    "wins": 0,
                    "losses": 0,
                    "pending": 0,
                    "win_rate": 0,
                    "avg_accuracy": 0
                }

        except Exception as e:
            logger.error(f"Failed to get user stats: {e}")
            return {}

    @classmethod
    async def update_prediction_outcome(
        cls,
        prediction_id: str,
        outcome: str,
        accuracy_score: float,
        actual_price: float
    ) -> bool:
        """
        Update prediction outcome (called by background task)

        Args:
            prediction_id: Prediction ID
            outcome: "WIN", "LOSS", or "PARTIAL"
            accuracy_score: 0-100 score
            actual_price: Actual price at check time

        Returns:
            Success status
        """
        try:
            mongo = get_mongodb()

            # Update MongoDB
            result = await mongo.predictions.update_one(
                {"_id": prediction_id},
                {"$set": {
                    "outcome": outcome,
                    "accuracy_score": accuracy_score,
                    "actual_price": actual_price,
                    "outcome_checked_at": datetime.utcnow()
                }}
            )

            if result.modified_count > 0:
                # Get user_id for leaderboard update
                prediction = await mongo.predictions.find_one({"_id": prediction_id})
                if prediction:
                    user_id = prediction["user_id"]

                    # Update user analytics
                    await cls._update_user_analytics(user_id)

                    # Update leaderboard
                    stats = await cls.get_user_stats(user_id)
                    redis = get_redis()
                    await redis.update_leaderboard(
                        user_id,
                        stats.get("avg_accuracy", 0)
                    )

                logger.info(f"✅ Outcome updated for prediction {prediction_id}: {outcome}")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to update outcome: {e}")
            return False

    @classmethod
    async def _update_user_analytics(cls, user_id: str):
        """Update user analytics in MongoDB"""
        try:
            mongo = get_mongodb()
            stats = await cls.get_user_stats(user_id)

            await mongo.user_analytics.update_one(
                {"user_id": user_id},
                {"$set": {
                    "user_id": user_id,
                    "total_predictions": stats["total_predictions"],
                    "wins": stats["wins"],
                    "losses": stats["losses"],
                    "pending": stats["pending"],
                    "win_rate": stats["win_rate"],
                    "total_accuracy": stats["avg_accuracy"],
                    "updated_at": datetime.utcnow()
                }},
                upsert=True
            )

        except Exception as e:
            logger.error(f"Failed to update user analytics: {e}")

    @classmethod
    async def get_pending_predictions(cls, limit: int = 100) -> List[Dict]:
        """Get predictions pending outcome check"""
        try:
            mongo = get_mongodb()

            # Get predictions where outcome is None and created > 1 min ago
            cutoff_time = datetime.utcnow() - timedelta(minutes=1)

            predictions = await mongo.predictions.find({
                "outcome": None,
                "created_at": {"$lt": cutoff_time}
            }).limit(limit).to_list(length=limit)

            for pred in predictions:
                pred["_id"] = str(pred["_id"])

            return predictions

        except Exception as e:
            logger.error(f"Failed to get pending predictions: {e}")
            return []


# Singleton instance
prediction_service = PredictionService()
