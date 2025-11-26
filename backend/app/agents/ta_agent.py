"""
Technical Analysis Agent - INTELLIGENT & REAL DATA
Multi-timeframe analysis with ICT/SMC methodology
Dynamically selects timeframes based on user query context
"""
import asyncio
from typing import Dict, List
import logging
import numpy as np

from app.core.data_fetcher import fetch_candles
from app.core.indicators import calculate_rsi, calculate_macd, calculate_ema
from app.core.market_structure import detect_swings, detect_choch_bos, identify_liquidity
from app.services.qwen_client import qwen_client

logger = logging.getLogger(__name__)


async def ta_node(state: Dict) -> Dict:
    """
    TA Agent - Intelligent multi-timeframe technical analysis

    Analyzes market based on query context:
    - "long term" → 1d timeframe
    - "day trading/today/short term" → 4h, 1h, 15m
    - "next move" → 1h, 15m, 1m

    Args:
        state: {
            "query": user query,
            "symbol": trading symbol,
            "timeframes": list of timeframes to analyze,
            "analysis_type": "long_term" | "short_term" | "scalping"
        }

    Returns:
        Updated state with ta_data
    """
    try:
        symbol = state.get("symbol")
        timeframes = state.get("timeframes", ["1h"])
        analysis_type = state.get("analysis_type", "short_term")

        logger.info(f"TA Agent analyzing {symbol} on timeframes: {timeframes}")

        # Fetch candles for all timeframes in parallel
        candle_data = {}
        tasks = []
        for tf in timeframes:
            tasks.append(fetch_candles(symbol, tf, limit=200))

        # Fetch all at once
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for tf, candles in zip(timeframes, results):
            if isinstance(candles, Exception):
                logger.error(f"Error fetching {tf} data: {candles}")
                continue
            if candles:
                candle_data[tf] = candles

        if not candle_data:
            raise Exception("No candle data fetched")

        # Analyze each timeframe
        multi_tf_analysis = {}

        for tf, candles in candle_data.items():
            logger.info(f"Analyzing {tf} timeframe ({len(candles)} candles)")

            # Extract price arrays
            closes = [c["close"] for c in candles]
            highs = [c["high"] for c in candles]
            lows = [c["low"] for c in candles]
            opens = [c["open"] for c in candles]
            timestamps = [c["timestamp"] for c in candles]

            # Calculate indicators
            rsi = calculate_rsi(closes)
            macd = calculate_macd(closes)
            ema20 = calculate_ema(closes, 20)
            ema50 = calculate_ema(closes, 50) if len(closes) >= 50 else None
            ema200 = calculate_ema(closes, 200) if len(closes) >= 200 else None

            # Detect swings and market structure
            swings = detect_swings(highs, lows, timestamps, order=5)
            structure = detect_choch_bos(swings)
            liquidity = identify_liquidity(highs, lows)

            # Calculate ATR for volatility
            atr = calculate_atr(highs, lows, closes)

            # Determine trend
            trend = determine_trend(closes, ema20, ema50)

            # Store analysis for this timeframe
            multi_tf_analysis[tf] = {
                "rsi": rsi,
                "macd": macd,
                "ema20": ema20,
                "ema50": ema50,
                "ema200": ema200,
                "swings": swings[-10:],  # Last 10 swings
                "choch": structure.get("choch"),
                "bos": structure.get("bos"),
                "liquidity": liquidity[:5],  # Top 5 liquidity levels
                "atr": atr,
                "trend": trend,
                "current_price": closes[-1],
                "price_change_percent": ((closes[-1] - closes[0]) / closes[0]) * 100
            }

        # Determine primary timeframe
        primary_tf = timeframes[len(timeframes) // 2] if len(timeframes) > 1 else timeframes[0]
        primary_analysis = multi_tf_analysis.get(primary_tf, {})

        # Use Qwen to analyze the TA data
        analysis_text = await analyze_with_qwen(
            symbol=symbol,
            multi_tf_data=multi_tf_analysis,
            analysis_type=analysis_type
        )

        # Compile final TA data
        ta_data = {
            "symbol": symbol,
            "timeframes_analyzed": list(multi_tf_analysis.keys()),
            "primary_timeframe": primary_tf,
            "primary_analysis": primary_analysis,
            "multi_timeframe_analysis": multi_tf_analysis,
            "qwen_analysis": analysis_text,
            "market_condition": classify_market_condition(primary_analysis)
        }

        logger.info(f"TA Agent completed analysis for {symbol}")

        return {"ta_data": ta_data}

    except Exception as e:
        logger.error(f"TA Agent error: {str(e)}")
        return {"ta_data": {"error": str(e)}}


def calculate_atr(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
    """Calculate Average True Range"""
    try:
        if len(highs) < period + 1:
            return 0.0

        tr_list = []
        for i in range(1, len(highs)):
            high = highs[i]
            low = lows[i]
            prev_close = closes[i - 1]

            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            tr_list.append(tr)

        atr = sum(tr_list[-period:]) / period
        return float(atr)
    except:
        return 0.0


def determine_trend(closes: List[float], ema20: float, ema50: float = None) -> str:
    """Determine market trend"""
    try:
        current_price = closes[-1]

        if ema50:
            if current_price > ema20 > ema50:
                return "bullish"
            elif current_price < ema20 < ema50:
                return "bearish"

        if current_price > ema20 * 1.01:
            return "bullish"
        elif current_price < ema20 * 0.99:
            return "bearish"

        return "sideways"
    except:
        return "unknown"


def classify_market_condition(analysis: Dict) -> str:
    """Classify market condition"""
    try:
        atr = analysis.get("atr", 0)
        trend = analysis.get("trend", "unknown")
        price = analysis.get("current_price", 0)

        atr_percent = (atr / price) * 100 if price > 0 else 0

        if atr_percent > 3:
            return "volatile"

        if trend == "sideways" and atr_percent < 1.5:
            return "ranging"

        if trend in ["bullish", "bearish"]:
            return "trending"

        return "unknown"
    except:
        return "unknown"


async def analyze_with_qwen(symbol: str, multi_tf_data: Dict, analysis_type: str) -> str:
    """Use Qwen to analyze multi-timeframe TA data"""
    try:
        context = f"Multi-Timeframe Technical Analysis for {symbol} ({analysis_type} analysis):\n\n"

        for tf, data in multi_tf_data.items():
            context += f"**{tf.upper()} Timeframe:**\n"
            context += f"- Trend: {data.get('trend', 'unknown')}\n"
            context += f"- RSI: {data.get('rsi', 0):.2f}\n"
            context += f"- Current Price: ${data.get('current_price', 0):.2f}\n"
            context += f"- EMA20: ${data.get('ema20', 0):.2f}\n"
            context += f"- Structure: {data.get('bos') or data.get('choch') or 'No clear break'}\n"
            context += f"- Price Change: {data.get('price_change_percent', 0):.2f}%\n\n"

        system_prompt = """You are an expert ICT/SMC trader. Analyze the multi-timeframe data and provide:
1. Overall market bias (bullish/bearish/neutral)
2. Key support/resistance levels
3. Market structure analysis (CHOCH, BOS)
4. Trading opportunities

Be concise (3-4 sentences). Focus on actionable insights."""

        analysis = await qwen_client.generate(context, system_prompt, temperature=0.5)

        return analysis

    except Exception as e:
        logger.error(f"Qwen analysis error: {e}")
        return "Unable to generate AI analysis"
