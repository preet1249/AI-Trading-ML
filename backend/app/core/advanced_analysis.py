"""
Advanced Mathematical Analysis
- Fibonacci retracements and extensions
- Pivot points (Classic, Woodie, Camarilla)
- Support/Resistance zones
- Order blocks
- Fair value gaps
- Liquidity zones
- Entry point calculations
"""
import logging
from typing import List, Dict, Tuple, Optional
import numpy as np

logger = logging.getLogger(__name__)


class AdvancedAnalysis:
    """Advanced mathematical analysis for intelligent entry/exit points"""

    @classmethod
    def calculate_fibonacci_levels(
        cls,
        high: float,
        low: float,
        trend: str = "bullish"
    ) -> Dict[str, float]:
        """
        Calculate Fibonacci retracement and extension levels

        Args:
            high: Recent high price
            low: Recent low price
            trend: "bullish" or "bearish"

        Returns:
            Dict with Fibonacci levels
        """
        diff = high - low

        if trend == "bullish":
            # Retracement levels (pullback zones for long entries)
            return {
                "fib_0": high,
                "fib_236": high - (diff * 0.236),  # Shallow pullback
                "fib_382": high - (diff * 0.382),  # Optimal entry zone
                "fib_500": high - (diff * 0.500),  # Mid retracement
                "fib_618": high - (diff * 0.618),  # Golden ratio (best entry)
                "fib_786": high - (diff * 0.786),  # Deep retracement
                "fib_100": low,
                # Extension levels (targets)
                "fib_1272": high + (diff * 0.272),  # TP1
                "fib_1618": high + (diff * 0.618),  # TP2 (golden extension)
                "fib_2618": high + (diff * 1.618),  # TP3
            }
        else:
            # Bearish - inverse
            return {
                "fib_0": low,
                "fib_236": low + (diff * 0.236),
                "fib_382": low + (diff * 0.382),
                "fib_500": low + (diff * 0.500),
                "fib_618": low + (diff * 0.618),  # Golden ratio entry
                "fib_786": low + (diff * 0.786),
                "fib_100": high,
                # Extension levels
                "fib_1272": low - (diff * 0.272),
                "fib_1618": low - (diff * 0.618),
                "fib_2618": low - (diff * 1.618),
            }

    @classmethod
    def calculate_pivot_points(
        cls,
        high: float,
        low: float,
        close: float,
        method: str = "classic"
    ) -> Dict[str, float]:
        """
        Calculate pivot points for support/resistance

        Args:
            high: Previous period high
            low: Previous period low
            close: Previous period close
            method: "classic", "woodie", or "camarilla"

        Returns:
            Dict with pivot levels (PP, R1-R3, S1-S3)
        """
        if method == "classic":
            pp = (high + low + close) / 3
            r1 = (2 * pp) - low
            s1 = (2 * pp) - high
            r2 = pp + (high - low)
            s2 = pp - (high - low)
            r3 = high + 2 * (pp - low)
            s3 = low - 2 * (high - pp)

        elif method == "woodie":
            pp = (high + low + (2 * close)) / 4
            r1 = (2 * pp) - low
            s1 = (2 * pp) - high
            r2 = pp + (high - low)
            s2 = pp - (high - low)
            r3 = high + 2 * (pp - low)
            s3 = low - 2 * (high - pp)

        elif method == "camarilla":
            # Camarilla pivots for intraday scalping
            pp = (high + low + close) / 3
            r1 = close + (high - low) * 1.1 / 12
            r2 = close + (high - low) * 1.1 / 6
            r3 = close + (high - low) * 1.1 / 4
            r4 = close + (high - low) * 1.1 / 2  # Breakout level
            s1 = close - (high - low) * 1.1 / 12
            s2 = close - (high - low) * 1.1 / 6
            s3 = close - (high - low) * 1.1 / 4
            s4 = close - (high - low) * 1.1 / 2  # Breakdown level

            return {
                "PP": pp,
                "R1": r1, "R2": r2, "R3": r3, "R4": r4,
                "S1": s1, "S2": s2, "S3": s3, "S4": s4
            }

        else:
            pp = (high + low + close) / 3
            r1 = s1 = r2 = s2 = r3 = s3 = pp

        return {
            "PP": pp,
            "R1": r1, "R2": r2, "R3": r3,
            "S1": s1, "S2": s2, "S3": s3
        }

    @classmethod
    def find_order_blocks(
        cls,
        candles: List[Dict],
        lookback: int = 20
    ) -> List[Dict]:
        """
        Find order blocks (institutional buying/selling zones)

        Order block = last down candle before strong up move (bullish)
                    = last up candle before strong down move (bearish)

        Args:
            candles: List of OHLCV candles
            lookback: Number of candles to analyze

        Returns:
            List of order blocks with price zones
        """
        if len(candles) < lookback:
            return []

        order_blocks = []
        recent_candles = candles[-lookback:]

        for i in range(1, len(recent_candles) - 3):
            prev_candle = recent_candles[i - 1]
            current = recent_candles[i]
            next1 = recent_candles[i + 1]
            next2 = recent_candles[i + 2]

            # Bullish order block (last red before strong green)
            is_red = current["close"] < current["open"]
            strong_green = (
                next1["close"] > next1["open"] and
                next2["close"] > next2["open"] and
                next1["close"] > current["high"]
            )

            if is_red and strong_green:
                order_blocks.append({
                    "type": "bullish",
                    "high": current["high"],
                    "low": current["low"],
                    "zone": (current["low"] + current["high"]) / 2,
                    "strength": "high"
                })

            # Bearish order block (last green before strong red)
            is_green = current["close"] > current["open"]
            strong_red = (
                next1["close"] < next1["open"] and
                next2["close"] < next2["open"] and
                next1["close"] < current["low"]
            )

            if is_green and strong_red:
                order_blocks.append({
                    "type": "bearish",
                    "high": current["high"],
                    "low": current["low"],
                    "zone": (current["low"] + current["high"]) / 2,
                    "strength": "high"
                })

        # Return last 3 most relevant
        return order_blocks[-3:] if order_blocks else []

    @classmethod
    def find_fair_value_gaps(
        cls,
        candles: List[Dict],
        lookback: int = 50
    ) -> List[Dict]:
        """
        Find Fair Value Gaps (FVG) - imbalance zones

        FVG = Gap between candle[i-1].high and candle[i+1].low (bullish)
            = Gap between candle[i-1].low and candle[i+1].high (bearish)

        Args:
            candles: List of OHLCV candles
            lookback: Number of candles to check

        Returns:
            List of FVGs
        """
        if len(candles) < lookback + 2:
            return []

        fvgs = []
        recent_candles = candles[-lookback:]

        for i in range(1, len(recent_candles) - 1):
            prev = recent_candles[i - 1]
            current = recent_candles[i]
            next_candle = recent_candles[i + 1]

            # Bullish FVG (gap up)
            if prev["high"] < next_candle["low"]:
                gap_size = next_candle["low"] - prev["high"]
                fvgs.append({
                    "type": "bullish",
                    "top": next_candle["low"],
                    "bottom": prev["high"],
                    "mid": (next_candle["low"] + prev["high"]) / 2,
                    "size": gap_size
                })

            # Bearish FVG (gap down)
            if prev["low"] > next_candle["high"]:
                gap_size = prev["low"] - next_candle["high"]
                fvgs.append({
                    "type": "bearish",
                    "top": prev["low"],
                    "bottom": next_candle["high"],
                    "mid": (prev["low"] + next_candle["high"]) / 2,
                    "size": gap_size
                })

        return fvgs[-5:] if fvgs else []

    @classmethod
    def calculate_optimal_entry(
        cls,
        current_price: float,
        direction: str,
        fib_levels: Dict,
        order_blocks: List[Dict],
        atr: float,
        market_condition: str
    ) -> Dict:
        """
        Calculate optimal entry point based on multiple factors

        Args:
            current_price: Current market price
            direction: "BULLISH" or "BEARISH"
            fib_levels: Fibonacci levels
            order_blocks: Order block zones
            atr: Average True Range
            market_condition: Market condition

        Returns:
            Dict with entry info
        """
        if direction == "BULLISH":
            # Look for bullish entry zones
            entry_candidates = []

            # Fib 0.618 (golden ratio) - best entry
            if "fib_618" in fib_levels:
                entry_candidates.append({
                    "price": fib_levels["fib_618"],
                    "reason": "Fibonacci 0.618 golden ratio pullback",
                    "confidence": 90
                })

            # Fib 0.5 - mid retracement
            if "fib_500" in fib_levels:
                entry_candidates.append({
                    "price": fib_levels["fib_500"],
                    "reason": "Fibonacci 0.5 retracement",
                    "confidence": 75
                })

            # Bullish order blocks
            for ob in order_blocks:
                if ob["type"] == "bullish":
                    entry_candidates.append({
                        "price": ob["zone"],
                        "reason": "Bullish order block (institutional zone)",
                        "confidence": 85
                    })

            # If no pullback expected, enter at current price
            if not entry_candidates or market_condition == "trending":
                entry_candidates.append({
                    "price": current_price,
                    "reason": "Immediate entry (strong trend, no pullback expected)",
                    "confidence": 70
                })

        else:  # BEARISH
            entry_candidates = []

            if "fib_618" in fib_levels:
                entry_candidates.append({
                    "price": fib_levels["fib_618"],
                    "reason": "Fibonacci 0.618 golden ratio rally",
                    "confidence": 90
                })

            if "fib_500" in fib_levels:
                entry_candidates.append({
                    "price": fib_levels["fib_500"],
                    "reason": "Fibonacci 0.5 retracement",
                    "confidence": 75
                })

            for ob in order_blocks:
                if ob["type"] == "bearish":
                    entry_candidates.append({
                        "price": ob["zone"],
                        "reason": "Bearish order block (institutional zone)",
                        "confidence": 85
                    })

            if not entry_candidates or market_condition == "trending":
                entry_candidates.append({
                    "price": current_price,
                    "reason": "Immediate entry (strong trend, no rally expected)",
                    "confidence": 70
                })

        # Sort by confidence and return best
        entry_candidates.sort(key=lambda x: x["confidence"], reverse=True)

        return entry_candidates[0] if entry_candidates else {
            "price": current_price,
            "reason": "Current market price",
            "confidence": 60
        }

    @classmethod
    def calculate_multi_tp_levels(
        cls,
        entry: float,
        stop_loss: float,
        direction: str,
        market_condition: str,
        confidence: int,
        atr: float,
        fib_levels: Dict
    ) -> List[Dict]:
        """
        Calculate multiple TP levels based on market conditions

        Risk-Reward Logic:
        - Risky/Volatile market: 1:2 (conservative)
        - Moderate confidence: 1:3
        - Strong momentum: 1:4-1:5 (aggressive)

        Args:
            entry: Entry price
            stop_loss: Stop loss price
            direction: "BULLISH" or "BEARISH"
            market_condition: Market state
            confidence: Confidence score (0-100)
            atr: Average True Range
            fib_levels: Fibonacci extension levels

        Returns:
            List of TP levels with risk-reward ratios
        """
        risk = abs(entry - stop_loss)

        # Determine risk-reward based on conditions
        if market_condition == "volatile" or confidence < 50:
            # Risky - conservative TPs
            rr_ratios = [2.0, 3.0]
        elif market_condition == "trending" and confidence >= 70:
            # Strong momentum - aggressive TPs
            rr_ratios = [2.0, 3.5, 5.0]
        else:
            # Moderate - balanced TPs
            rr_ratios = [2.0, 3.0, 4.0]

        tp_levels = []

        if direction == "BULLISH":
            for i, rr in enumerate(rr_ratios, 1):
                tp_price = entry + (risk * rr)

                # Try to align with Fibonacci extensions
                reason = f"Risk-Reward 1:{rr}"
                if "fib_1272" in fib_levels and abs(tp_price - fib_levels["fib_1272"]) < atr:
                    tp_price = fib_levels["fib_1272"]
                    reason = f"Fibonacci 1.272 extension (RR ~1:{rr})"
                elif "fib_1618" in fib_levels and abs(tp_price - fib_levels["fib_1618"]) < atr * 2:
                    tp_price = fib_levels["fib_1618"]
                    reason = f"Fibonacci 1.618 golden extension (RR ~1:{rr})"

                tp_levels.append({
                    "level": i,
                    "price": round(tp_price, 2),
                    "rr": f"1:{rr}",
                    "reason": reason,
                    "percentage": round(((tp_price - entry) / entry) * 100, 2)
                })

        else:  # BEARISH
            for i, rr in enumerate(rr_ratios, 1):
                tp_price = entry - (risk * rr)

                reason = f"Risk-Reward 1:{rr}"
                if "fib_1272" in fib_levels and abs(tp_price - fib_levels["fib_1272"]) < atr:
                    tp_price = fib_levels["fib_1272"]
                    reason = f"Fibonacci 1.272 extension (RR ~1:{rr})"
                elif "fib_1618" in fib_levels and abs(tp_price - fib_levels["fib_1618"]) < atr * 2:
                    tp_price = fib_levels["fib_1618"]
                    reason = f"Fibonacci 1.618 golden extension (RR ~1:{rr})"

                tp_levels.append({
                    "level": i,
                    "price": round(tp_price, 2),
                    "rr": f"1:{rr}",
                    "reason": reason,
                    "percentage": round(((entry - tp_price) / entry) * 100, 2)
                })

        return tp_levels


# Singleton instance
advanced_analysis = AdvancedAnalysis()
