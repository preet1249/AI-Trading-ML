"""
Intelligent Prediction Outcome Tracker with ML Learning
- Runs every 12 hours automatically
- Batch checks: 1 API call per symbol (not per prediction!)
- Deep failure analysis for learning
- Saves to training_data for ML improvement
- Makes model smarter over time
"""
import logging
import asyncio
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict

from app.services.binance import binance_service
from app.services.twelve_data_service import twelve_data_service
from app.services.prediction_service import prediction_service
from app.db.mongodb_client import get_mongodb

logger = logging.getLogger(__name__)


class OutcomeTracker:
    """
    Intelligent outcome tracker with ML learning
    - Batch processing: 1 API call validates 100s of predictions
    - Deep analysis on failures
    - Learns from mistakes
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
        return cls.TIMEFRAME_MINUTES.get(timeframe, 60)

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
                price = await binance_service.get_current_price(symbol)
                return price
            else:
                price = await twelve_data_service.get_current_price(symbol)
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
    ) -> tuple[str, float, int]:
        """
        Calculate prediction outcome and accuracy score

        Returns:
            (outcome, accuracy_score, tps_hit)
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
            tps_hit = 0
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
                accuracy_score = (tp_percentage * 0.7) + (confidence * 0.3)
            else:
                outcome = "PARTIAL"
                accuracy_score = confidence * 0.5
        else:
            outcome = "LOSS"
            accuracy_score = 0
            tps_hit = 0

        return outcome, min(100, accuracy_score), tps_hit

    @classmethod
    async def _analyze_failure(cls, prediction: Dict, actual_price: float) -> Dict:
        """
        Deep analysis of why prediction failed

        Args:
            prediction: Failed prediction data
            actual_price: Actual price at check time

        Returns:
            Detailed failure analysis for ML learning
        """
        try:
            pred_data = prediction.get("prediction_data", {})

            # Extract prediction details
            direction = prediction.get("direction", "NEUTRAL")
            entry_price = float(prediction.get("entry_price", 0))
            stop_loss = float(prediction.get("stop_loss", 0)) if prediction.get("stop_loss") else None
            confidence = int(prediction.get("confidence", 50))
            timeframe = pred_data.get("timeframe", "1h")
            market_condition = pred_data.get("market_condition", "")
            ta_summary = pred_data.get("ta_summary", "")

            # Calculate price movement
            price_change_pct = ((actual_price - entry_price) / entry_price) * 100

            # Analyze what went wrong
            failure_reasons = []

            # 1. Direction was wrong
            if direction == "BULLISH" and actual_price < entry_price:
                failure_reasons.append("Direction misprediction: Expected BULLISH but price went DOWN")
            elif direction == "BEARISH" and actual_price > entry_price:
                failure_reasons.append("Direction misprediction: Expected BEARISH but price went UP")

            # 2. Stop loss hit
            if stop_loss:
                if direction == "BULLISH" and actual_price <= stop_loss:
                    sl_distance = ((entry_price - stop_loss) / entry_price) * 100
                    failure_reasons.append(f"Stop loss hit: SL too tight ({sl_distance:.2f}% from entry)")
                elif direction == "BEARISH" and actual_price >= stop_loss:
                    sl_distance = ((stop_loss - entry_price) / entry_price) * 100
                    failure_reasons.append(f"Stop loss hit: SL too tight ({sl_distance:.2f}% from entry)")

            # 3. Overconfidence
            if confidence > 70 and price_change_pct < 0:
                failure_reasons.append(f"Overconfidence: {confidence}% confidence but price moved {price_change_pct:.2f}%")

            # 4. Timeframe mismatch
            if timeframe in ["1m", "5m"] and abs(price_change_pct) > 5:
                failure_reasons.append(f"Timeframe mismatch: {timeframe} too short for {price_change_pct:.2f}% move")

            # 5. Market condition ignored
            if "volatile" in market_condition.lower() and confidence > 60:
                failure_reasons.append("High confidence in volatile market - risky")

            # Build learning data
            failure_analysis = {
                "prediction_id": str(prediction["_id"]),
                "symbol": prediction.get("symbol", ""),
                "timeframe": timeframe,
                "direction": direction,
                "entry_price": entry_price,
                "actual_price": actual_price,
                "price_change_pct": price_change_pct,
                "confidence": confidence,
                "market_condition": market_condition,
                "failure_reasons": failure_reasons,
                "ta_summary": ta_summary,
                "created_at": prediction.get("created_at"),
                "checked_at": datetime.utcnow(),

                # Pattern tags for ML learning
                "failure_pattern": {
                    "wrong_direction": direction == "BULLISH" and actual_price < entry_price or direction == "BEARISH" and actual_price > entry_price,
                    "sl_too_tight": stop_loss and abs((entry_price - stop_loss) / entry_price) < 0.01,  # SL < 1%
                    "overconfident": confidence > 70,
                    "volatile_market": "volatile" in market_condition.lower(),
                    "short_timeframe": timeframe in ["1m", "5m", "15m"]
                },

                # Learnings
                "what_to_avoid": failure_reasons,
                "market_lesson": f"In {market_condition} market with {timeframe} timeframe, {direction} prediction failed by {abs(price_change_pct):.2f}%"
            }

            return failure_analysis

        except Exception as e:
            logger.error(f"Error analyzing failure: {e}")
            return {}

    @classmethod
    async def _save_training_data(cls, prediction: Dict, outcome: str, accuracy_score: float, actual_price: float, failure_analysis: Dict = None):
        """
        Save prediction outcome to training_data collection for ML learning

        Args:
            prediction: Prediction data
            outcome: WIN/LOSS/PARTIAL
            accuracy_score: 0-100
            actual_price: Actual price
            failure_analysis: Deep analysis if failed
        """
        try:
            mongo = get_mongodb()

            training_doc = {
                "prediction_id": str(prediction["_id"]),
                "user_id": prediction.get("user_id"),
                "symbol": prediction.get("symbol"),
                "outcome": outcome,
                "accuracy_score": accuracy_score,
                "prediction_data": prediction.get("prediction_data", {}),
                "actual_price": actual_price,
                "created_at": prediction.get("created_at"),
                "checked_at": datetime.utcnow(),

                # Add failure analysis if available
                "failure_analysis": failure_analysis if outcome == "LOSS" and failure_analysis else None,

                # Tags for easy querying
                "tags": {
                    "outcome": outcome,
                    "direction": prediction.get("direction"),
                    "timeframe": prediction.get("prediction_data", {}).get("timeframe", "1h"),
                    "market_condition": prediction.get("prediction_data", {}).get("market_condition", ""),
                    "confidence_range": "high" if prediction.get("confidence", 0) > 70 else "medium" if prediction.get("confidence", 0) > 40 else "low"
                }
            }

            await mongo.training_data.insert_one(training_doc)
            logger.info(f"💾 Saved training data for {prediction.get('symbol')} ({outcome})")

        except Exception as e:
            logger.error(f"Failed to save training data: {e}")

    @classmethod
    async def run_intelligent_checker(cls, interval: int = 43200):
        """
        Intelligent background checker - runs every 12 hours

        Smart Design:
        1. Group predictions by symbol
        2. 1 API call per symbol (batch check)
        3. Deep analysis on failures
        4. Save learnings for ML

        Args:
            interval: Check interval in seconds (default: 12 hours = 43200s)
        """
        logger.info("🤖 Starting INTELLIGENT outcome tracker (every 12 hours)...")

        while True:
            try:
                logger.info("=" * 60)
                logger.info("🔍 INTELLIGENT TRACKER RUN STARTED")
                logger.info("=" * 60)

                # Get all pending predictions (no limit)
                pending_predictions = await prediction_service.get_pending_predictions(limit=10000)

                if not pending_predictions:
                    logger.info("No pending predictions to check")
                    await asyncio.sleep(interval)
                    continue

                # Filter: Only check predictions where timeframe has passed
                ready_predictions = []
                for pred in pending_predictions:
                    created_at = pred.get("created_at")
                    if not isinstance(created_at, datetime):
                        continue

                    timeframe = pred.get("prediction_data", {}).get("timeframe", "1h")
                    timeframe_minutes = cls._parse_timeframe(timeframe)
                    time_elapsed = datetime.utcnow() - created_at

                    if time_elapsed >= timedelta(minutes=timeframe_minutes):
                        ready_predictions.append(pred)

                if not ready_predictions:
                    logger.info("No predictions ready for checking (timeframes not complete)")
                    await asyncio.sleep(interval)
                    continue

                logger.info(f"📋 Found {len(ready_predictions)} predictions ready to check")

                # GROUP BY SYMBOL (smart batching!)
                symbol_groups = defaultdict(list)
                for pred in ready_predictions:
                    symbol = pred.get("symbol", "UNKNOWN")
                    symbol_groups[symbol].append(pred)

                total_symbols = len(symbol_groups)
                logger.info(f"📊 Grouped into {total_symbols} unique symbols")
                logger.info(f"🎯 API calls needed: {total_symbols} (instead of {len(ready_predictions)})")

                # Process each symbol group
                checked_count = 0
                wins = 0
                losses = 0
                partials = 0

                for symbol, predictions in symbol_groups.items():
                    logger.info(f"\n{'='*50}")
                    logger.info(f"📍 Processing {symbol} ({len(predictions)} predictions)")

                    # 1 API CALL FOR THIS SYMBOL
                    market_type = predictions[0].get("prediction_data", {}).get("market_type", "crypto")
                    actual_price = await cls._get_current_price(symbol, market_type)

                    if not actual_price:
                        logger.warning(f"❌ Could not fetch price for {symbol}, skipping")
                        continue

                    logger.info(f"💰 Current price for {symbol}: ${actual_price:.2f}")

                    # Check ALL predictions for this symbol with same price!
                    for pred in predictions:
                        try:
                            prediction_id = str(pred["_id"])
                            direction = pred.get("direction", "NEUTRAL")
                            entry_price = float(pred.get("entry_price", 0))
                            stop_loss = float(pred.get("stop_loss", 0)) if pred.get("stop_loss") else None
                            take_profits = pred.get("take_profits", [])
                            confidence = int(pred.get("confidence", 50))

                            # Calculate outcome
                            outcome, accuracy_score, tps_hit = cls._calculate_accuracy(
                                direction, entry_price, actual_price, stop_loss, take_profits, confidence
                            )

                            # Track stats
                            if outcome == "WIN":
                                wins += 1
                            elif outcome == "LOSS":
                                losses += 1
                            else:
                                partials += 1

                            # Deep analysis on failures
                            failure_analysis = None
                            if outcome == "LOSS":
                                logger.warning(f"❌ FAILURE detected for {symbol}, analyzing...")
                                failure_analysis = await cls._analyze_failure(pred, actual_price)
                                logger.info(f"🧠 Failure reasons: {failure_analysis.get('failure_reasons', [])}")

                            # Update outcome in database
                            await prediction_service.update_prediction_outcome(
                                prediction_id=prediction_id,
                                outcome=outcome,
                                accuracy_score=accuracy_score,
                                actual_price=actual_price
                            )

                            # Save to training data for ML learning
                            await cls._save_training_data(
                                prediction=pred,
                                outcome=outcome,
                                accuracy_score=accuracy_score,
                                actual_price=actual_price,
                                failure_analysis=failure_analysis
                            )

                            checked_count += 1

                            # Log result
                            emoji = "✅" if outcome == "WIN" else "⚠️" if outcome == "PARTIAL" else "❌"
                            logger.info(
                                f"{emoji} {prediction_id[:8]}... | {direction} | "
                                f"Entry: ${entry_price:.2f} → Actual: ${actual_price:.2f} | "
                                f"{outcome} ({accuracy_score:.1f}%) | TPs hit: {tps_hit}/{len(take_profits)}"
                            )

                        except Exception as e:
                            logger.error(f"Error checking prediction {pred.get('_id')}: {e}")
                            continue

                    # Small delay between symbols
                    await asyncio.sleep(0.5)

                # Summary
                logger.info("\n" + "=" * 60)
                logger.info("🎉 INTELLIGENT TRACKER RUN COMPLETED")
                logger.info(f"📊 Results:")
                logger.info(f"   • Total checked: {checked_count}")
                logger.info(f"   • Wins: {wins} ✅")
                logger.info(f"   • Losses: {losses} ❌")
                logger.info(f"   • Partial: {partials} ⚠️")
                logger.info(f"   • API calls used: {total_symbols}")
                logger.info(f"   • Efficiency: {checked_count}/{total_symbols} = {checked_count/total_symbols if total_symbols > 0 else 0:.1f} predictions per API call")
                logger.info(f"⏰ Next run in 12 hours...")
                logger.info("=" * 60 + "\n")

                # Wait 12 hours
                await asyncio.sleep(interval)

            except Exception as e:
                logger.error(f"Error in intelligent checker: {e}", exc_info=True)
                await asyncio.sleep(interval)

    @classmethod
    async def manual_check(cls, prediction_id: str) -> tuple[bool, str]:
        """Manually trigger outcome check"""
        try:
            prediction = await prediction_service.get_prediction_by_id(prediction_id)

            if not prediction:
                return False, "Prediction not found"

            if prediction.get("outcome"):
                return False, f"Outcome already checked: {prediction['outcome']}"

            # Get price
            symbol = prediction.get("symbol")
            market_type = prediction.get("prediction_data", {}).get("market_type", "crypto")
            actual_price = await cls._get_current_price(symbol, market_type)

            if not actual_price:
                return False, f"Could not fetch price for {symbol}"

            # Calculate outcome
            direction = prediction.get("direction")
            entry_price = float(prediction.get("entry_price", 0))
            stop_loss = float(prediction.get("stop_loss", 0)) if prediction.get("stop_loss") else None
            take_profits = prediction.get("take_profits", [])
            confidence = int(prediction.get("confidence", 50))

            outcome, accuracy_score, _ = cls._calculate_accuracy(
                direction, entry_price, actual_price, stop_loss, take_profits, confidence
            )

            # Analyze if failed
            failure_analysis = None
            if outcome == "LOSS":
                failure_analysis = await cls._analyze_failure(prediction, actual_price)

            # Update
            await prediction_service.update_prediction_outcome(
                prediction_id=prediction_id,
                outcome=outcome,
                accuracy_score=accuracy_score,
                actual_price=actual_price
            )

            # Save training data
            await cls._save_training_data(
                prediction=prediction,
                outcome=outcome,
                accuracy_score=accuracy_score,
                actual_price=actual_price,
                failure_analysis=failure_analysis
            )

            return True, f"Outcome: {outcome} ({accuracy_score:.1f}%)"

        except Exception as e:
            logger.error(f"Error in manual check: {e}")
            return False, str(e)


# Singleton instance
outcome_tracker = OutcomeTracker()
