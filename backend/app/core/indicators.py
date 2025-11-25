"""
Technical Indicators
RSI, MACD, EMA calculations using TA-Lib
"""
import talib
import numpy as np
from typing import List


def calculate_rsi(closes: List[float], period: int = 14) -> float:
    """
    Calculate RSI (Relative Strength Index)

    Args:
        closes: List of closing prices
        period: RSI period (default 14)

    Returns:
        Latest RSI value
    """
    closes_array = np.array(closes, dtype=float)
    rsi = talib.RSI(closes_array, timeperiod=period)
    return float(rsi[-1]) if not np.isnan(rsi[-1]) else 50.0


def calculate_macd(
    closes: List[float],
    fast: int = 12,
    slow: int = 26,
    signal: int = 9
) -> dict:
    """
    Calculate MACD (Moving Average Convergence Divergence)

    Args:
        closes: List of closing prices
        fast: Fast EMA period
        slow: Slow EMA period
        signal: Signal line period

    Returns:
        Dict with MACD line, signal, histogram
    """
    closes_array = np.array(closes, dtype=float)
    macd_line, signal_line, histogram = talib.MACD(
        closes_array,
        fastperiod=fast,
        slowperiod=slow,
        signalperiod=signal
    )

    return {
        "line": float(macd_line[-1]) if not np.isnan(macd_line[-1]) else 0.0,
        "signal": float(signal_line[-1]) if not np.isnan(signal_line[-1]) else 0.0,
        "histogram": float(histogram[-1]) if not np.isnan(histogram[-1]) else 0.0,
    }


def calculate_ema(closes: List[float], period: int = 20) -> float:
    """
    Calculate EMA (Exponential Moving Average)

    Args:
        closes: List of closing prices
        period: EMA period

    Returns:
        Latest EMA value
    """
    closes_array = np.array(closes, dtype=float)
    ema = talib.EMA(closes_array, timeperiod=period)
    return float(ema[-1]) if not np.isnan(ema[-1]) else closes[-1]
