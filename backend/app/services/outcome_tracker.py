"""
Automatic Prediction Outcome Tracker
- Runs as background task
- Checks predictions after timeframe completes
- Fetches actual prices from Binance/Twelve Data (FREE)
- Calculates accuracy automatically
- Updates MongoDB + Leaderboard
- $0 Cost (uses existing free APIs)
"""
import logging
import asyncio
from typing import Dict, Optional
from datetime import datetime, timedelta

from app.services.binance import get_binance_price
from app.services.twelve_data_service import get_stock_price
from app.services.prediction_service import prediction_service

logger = logging.getLogger(__name__)


class OutcomeTracker:
    """
    Automatic prediction outcome tracking
    - Checks if predictions were right/wrong
    - Uses free APIs already integrated
    - No manual input needed
    """

    # Timeframe to minutes mapping
    TIMEFRAME_MINUTES = {
        "1m": 1,
        "5m": 5,
        "15m": 15,
        "30m": 30,
        "1h": 60,
        "4h": 240,
        "1d": 1440,
        "1w": 10080
    }

    @classmethod
    def _parse_timeframe(cls, timeframe: str) -> int:
        """Convert timeframe string to minutes"""
        return cls.TIMEFRAME_MINUTES.get(timeframe, 60)  # Default to 1h

    @classmethod
    async def _get_current_price(cls, symbol: str, market_type: str) -> Optional[float]:
        """
        Get current price from free APIs

        Args:
            symbol: Trading symbol
            market_type: "crypto" or "stock"

        Returns:
            Current price or None
        """
        try:
            if market_type == "crypto":
                # Use Binance API (FREE, no keys needed)
                price = await get_binance_price(symbol)
                return price
            else:
                # Use Twelve Data API (FREE tier)
                price = await get_stock_price(symbol)
                return price

        except Exception as e:
            logger.error(f"Failed to get current price for {symbol}: {e}")
            return None

    @classmethod
    def _calculate_accuracy(
        cls,
        direction: str,
        entry_price: float,
        actual_price: float,
        stop_loss: float,
        take_profits: list,
        confidence: int
    ) -> tuple[str, float]:
        """
        Calculate prediction outcome and accuracy score

        Args:
            direction: "BULLISH" or "BEARISH"
            entry_price: Predicted entry price
            actual_price: Actual price at check time
            stop_loss: Stop loss level
            take_profits: List of TP levels
            confidence: Original confidence (0-100)

        Returns:
            (outcome, accuracy_score)
        """
        # Calculate price movement
        if direction == "BULLISH":
            price_moved_correctly = actual_price > entry_price
            hit_stop_loss = actual_price <= stop_loss if stop_loss else False
        else:  # BEARISH
            price_moved_correctly = actual_price < entry_price
            hit_stop_loss = actual_price >= stop_loss if stop_loss else False

        # Determine outcome
        if hit_stop_loss:
            outcome = "LOSS"
            accuracy_score = 0
        elif price_moved_correctly:
            # Check how many TPs hit
            tps_hit = 0
            for tp in take_profits:
                tp_price = float(tp.get("price", 0))
                if direction == "BULLISH" and actual_price >= tp_price:
                    tps_hit += 1
                elif direction == "BEARISH" and actual_price <= tp_price:
                    tps_hit += 1

            if tps_hit > 0:
                outcome = "WIN"
                # Accuracy based on TPs hit and confidence
                tp_percentage = (tps_hit / len(take_profits)) * 100 if take_profits else 100
                accuracy_score = (tp_percentage * 0.7) + (confidence * 0.3)  # Weighted average
            else:
                outcome = "PARTIAL"
                # Moved in right direction but didn't hit TP
                accuracy_score = confidence * 0.5
        else:
            outcome = "LOSS"
            accuracy_score = 0

        return outcome, min(100, accuracy_score)

    @classmethod
    async def check_prediction_outcome(cls, prediction: Dict) -> bool:
        """
        Check single prediction outcome

        Args:
            prediction: Prediction document from MongoDB

        Returns:
            Success status
        """
        try:
            prediction_id = str(prediction["_id"])
            symbol = prediction["symbol"]
            market_type = prediction.get("prediction_data", {}).get("market_type", "crypto")
            direction = prediction["direction"]
            entry_price = float(prediction["entry_price"])
            stop_loss = float(prediction.get("stop_loss", 0)) if prediction.get("stop_loss") else None
            take_profits = prediction.get("take_profits", [])
            confidence = int(prediction.get("confidence", 50))

            # Get current price from free API
            logger.info(f"📊 Checking outcome for {symbol} (prediction {prediction_id[:8]}...)")
            actual_price = await cls._get_current_price(symbol, market_type)

            if not actual_price:
                logger.warning(f"Could not get price for {symbol}, will retry later")
                return False

            # Calculate outcome
            outcome, accuracy_score = cls._calculate_accuracy(
                direction, entry_price, actual_price, stop_loss, take_profits, confidence
            )

            # Update in database
            success = await prediction_service.update_prediction_outcome(
                prediction_id=prediction_id,
                outcome=outcome,
                accuracy_score=accuracy_score,
                actual_price=actual_price
            )

            if success:
                logger.info(
                    f"✅ Outcome: {outcome} | Accuracy: {accuracy_score:.1f}% | "
                    f"{symbol} | Entry: ${entry_price:.2f} → Actual: ${actual_price:.2f}"
                )
            else:
                logger.error(f"Failed to update outcome for {prediction_id}")

            return success

        except Exception as e:
            logger.error(f"Error checking prediction outcome: {e}")
            return False

    @classmethod
    async def run_background_checker(cls, interval: int = 60):
        """
        Background task that runs continuously

        Args:
            interval: Check interval in seconds (default: 1 minute)
        """
        logger.info("🤖 Starting automatic outcome tracker...")

        while True:
            try:
                # Get predictions pending outcome check
                pending_predictions = await prediction_service.get_pending_predictions(limit=50)

                if pending_predictions:
                    logger.info(f"📋 Found {len(pending_predictions)} predictions to check")

                    # Check each prediction
                    for prediction in pending_predictions:
                        # Check if timeframe has passed
                        created_at = prediction.get("created_at")
                        timeframe = prediction.get("prediction_data", {}).get("timeframe", "1h")

                        if isinstance(created_at, datetime):
                            time_elapsed = datetime.utcnow() - created_at
                        else:
                            # If it's a string, parse it
                            continue

                        timeframe_minutes = cls._parse_timeframe(timeframe)
                        required_wait = timedelta(minutes=timeframe_minutes)

                        # Only check if timeframe has passed
                        if time_elapsed >= required_wait:
                            await cls.check_prediction_outcome(prediction)
                            await asyncio.sleep(1)  # Rate limit API calls
                        else:
                            logger.debug(
                                f"Skipping {prediction['_id']} - timeframe not complete "
                                f"({time_elapsed.total_seconds() // 60:.0f}m / {timeframe_minutes}m)"
                            )

                else:
                    logger.debug("No pending predictions to check")

                # Wait before next check
                await asyncio.sleep(interval)

            except Exception as e:
                logger.error(f"Error in background checker: {e}")
                await asyncio.sleep(interval)

    @classmethod
    async def manual_check(cls, prediction_id: str) -> tuple[bool, str]:
        """
        Manually check prediction outcome (for testing)

        Args:
            prediction_id: Prediction ID

        Returns:
            (success, message)
        """
        try:
            prediction = await prediction_service.get_prediction_by_id(prediction_id)

            if not prediction:
                return False, "Prediction not found"

            if prediction.get("outcome"):
                return False, f"Outcome already checked: {prediction['outcome']}"

            success = await cls.check_prediction_outcome(prediction)

            if success:
                return True, "Outcome checked successfully"
            else:
                return False, "Failed to check outcome"

        except Exception as e:
            logger.error(f"Error in manual check: {e}")
            return False, str(e)


# Singleton instance
outcome_tracker = OutcomeTracker()
