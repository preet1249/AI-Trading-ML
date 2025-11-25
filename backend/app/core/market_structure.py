"""
Market Structure Analysis
ICT/SMC methodology: Swings, CHOCH, BOS, Liquidity, Order Blocks
"""
from scipy.signal import argrelextrema
import numpy as np
from typing import List, Dict


def detect_swings(
    highs: List[float],
    lows: List[float],
    timestamps: List[int],
    order: int = 5
) -> List[Dict]:
    """
    Detect swing highs and lows

    Args:
        highs: List of high prices
        lows: List of low prices
        timestamps: List of timestamps
        order: Number of candles to look around for extrema

    Returns:
        List of swing points
    """
    highs_array = np.array(highs)
    lows_array = np.array(lows)

    # Find local maxima (swing highs)
    high_indices = argrelextrema(highs_array, np.greater, order=order)[0]

    # Find local minima (swing lows)
    low_indices = argrelextrema(lows_array, np.less, order=order)[0]

    swings = []

    # Add swing highs
    for idx in high_indices[-10:]:  # Last 10 swing highs
        swings.append({
            "type": "high",
            "price": float(highs[idx]),
            "timestamp": int(timestamps[idx])
        })

    # Add swing lows
    for idx in low_indices[-10:]:  # Last 10 swing lows
        swings.append({
            "type": "low",
            "price": float(lows[idx]),
            "timestamp": int(timestamps[idx])
        })

    # Sort by timestamp
    swings.sort(key=lambda x: x["timestamp"])

    return swings


def detect_choch_bos(swings: List[Dict]) -> Dict:
    """
    Detect CHOCH (Change of Character) and BOS (Break of Structure)

    Args:
        swings: List of swing points

    Returns:
        Dict with CHOCH and BOS information
    """
    # TODO: Implement CHOCH/BOS detection logic
    # This is a simplified placeholder

    if len(swings) < 3:
        return {"choch": None, "bos": None}

    # Basic trend detection
    recent_highs = [s for s in swings[-5:] if s["type"] == "high"]
    recent_lows = [s for s in swings[-5:] if s["type"] == "low"]

    if len(recent_highs) >= 2 and recent_highs[-1]["price"] > recent_highs[-2]["price"]:
        return {"choch": None, "bos": "bullish"}
    elif len(recent_lows) >= 2 and recent_lows[-1]["price"] < recent_lows[-2]["price"]:
        return {"choch": None, "bos": "bearish"}

    return {"choch": None, "bos": None}


def identify_liquidity(
    highs: List[float],
    lows: List[float],
    threshold: float = 0.001
) -> List[float]:
    """
    Identify liquidity zones (equal highs/lows)

    Args:
        highs: List of high prices
        lows: List of low prices
        threshold: Price similarity threshold (0.1% default)

    Returns:
        List of liquidity price levels
    """
    liquidity_levels = []

    # Check for equal highs in recent candles
    recent_highs = highs[-20:]
    for i, price in enumerate(recent_highs[:-1]):
        for compare_price in recent_highs[i+1:]:
            if abs(price - compare_price) / price < threshold:
                if price not in liquidity_levels:
                    liquidity_levels.append(float(price))

    # Check for equal lows
    recent_lows = lows[-20:]
    for i, price in enumerate(recent_lows[:-1]):
        for compare_price in recent_lows[i+1:]:
            if abs(price - compare_price) / price < threshold:
                if price not in liquidity_levels:
                    liquidity_levels.append(float(price))

    return liquidity_levels
