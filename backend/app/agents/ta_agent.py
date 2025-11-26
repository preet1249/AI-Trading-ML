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
from app.core.advanced_analysis import advanced_analysis
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

            # INTELLIGENT INDICATOR SELECTION based on timeframe
            # Ultra-fast (1m-5m): Focus on price action + momentum
            # Medium (15m-1h): Add EMAs for trend
            # Slow (4h-1d): Include longer EMAs for bias

            # Always calculate these (relevant for all timeframes)
            rsi = calculate_rsi(closes)
            atr = calculate_atr(highs, lows, closes)
            current_price = closes[-1]

            # Timeframe-specific indicators
            ema20 = None
            ema50 = None
            ema200 = None
            macd = None

            if tf in ["1m", "5m"]:
                # Ultra-scalping: Only fast EMA + price action
                ema20 = calculate_ema(closes, 20)
                # Skip MACD and longer EMAs (too slow for 1m)
                logger.info(f"{tf}: Using fast indicators (EMA20, RSI, ATR)")
            elif tf in ["15m", "1h"]:
                # Scalping/intraday: Medium-term indicators
                ema20 = calculate_ema(closes, 20)
                ema50 = calculate_ema(closes, 50) if len(closes) >= 50 else None
                macd = calculate_macd(closes)
                logger.info(f"{tf}: Using medium indicators (EMA20/50, MACD, RSI)")
            else:
                # 4h+ : Full indicator suite
                ema20 = calculate_ema(closes, 20)
                ema50 = calculate_ema(closes, 50) if len(closes) >= 50 else None
                ema200 = calculate_ema(closes, 200) if len(closes) >= 200 else None
                macd = calculate_macd(closes)
                logger.info(f"{tf}: Using full indicators (EMA20/50/200, MACD, RSI)")

            # Market structure analysis (important for all timeframes)
            swing_order = 3 if tf in ["1m", "5m"] else 5  # Smaller swings for faster TFs
            swings = detect_swings(highs, lows, timestamps, order=swing_order)
            structure = detect_choch_bos(swings)
            liquidity = identify_liquidity(highs, lows)

            # Determine trend
            trend = determine_trend(closes, ema20, ema50)

            # ADVANCED ANALYSIS - Fibonacci, Pivots, Order Blocks
            # Calculate recent high/low for Fibonacci
            recent_high = max(highs[-20:]) if len(highs) >= 20 else max(highs)
            recent_low = min(lows[-20:]) if len(lows) >= 20 else min(lows)

            # Fibonacci levels
            fib_levels = advanced_analysis.calculate_fibonacci_levels(
                high=recent_high,
                low=recent_low,
                trend=trend if trend != "sideways" else "bullish"
            )

            # Pivot points
            pivot_points = advanced_analysis.calculate_pivot_points(
                high=highs[-1],
                low=lows[-1],
                close=closes[-1],
                method="camarilla" if tf in ["1m", "5m"] else "classic"
            )

            # Order blocks (institutional zones)
            order_blocks = advanced_analysis.find_order_blocks(candles, lookback=30)

            # Fair value gaps
            fvgs = advanced_analysis.find_fair_value_gaps(candles, lookback=50)

            # Store analysis for this timeframe
            multi_tf_analysis[tf] = {
                "rsi": rsi,
                "macd": macd,  # May be None for 1m/5m
                "ema20": ema20,
                "ema50": ema50,
                "ema200": ema200,
                "swings": swings[-10:],  # Last 10 swings
                "choch": structure.get("choch"),
                "bos": structure.get("bos"),
                "liquidity": liquidity[:5],  # Top 5 liquidity levels
                "atr": atr,
                "trend": trend,
                "current_price": current_price,
                "price_change_percent": ((current_price - closes[0]) / closes[0]) * 100,
                "timeframe_type": get_timeframe_type(tf),  # fast/medium/slow
                # Advanced analysis
                "fibonacci": fib_levels,
                "pivots": pivot_points,
                "order_blocks": order_blocks,
                "fair_value_gaps": fvgs,
                "recent_high": recent_high,
                "recent_low": recent_low
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


def get_timeframe_type(tf: str) -> str:
    """
    Classify timeframe type for intelligent analysis

    Returns:
        fast: 1m-5m (price action focus)
        medium: 15m-1h (trend + momentum)
        slow: 4h+ (full technical analysis)
    """
    if tf in ["1m", "5m"]:
        return "fast"
    elif tf in ["15m", "1h"]:
        return "medium"
    else:
        return "slow"


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
    """Use Qwen to analyze multi-timeframe TA data with timeframe-aware context"""
    try:
        context = f"Multi-Timeframe Technical Analysis for {symbol} ({analysis_type} analysis):\n\n"

        for tf, data in multi_tf_data.items():
            tf_type = data.get('timeframe_type', 'medium')
            context += f"**{tf.upper()} Timeframe ({tf_type}):**\n"
            context += f"- Current Price: ${data.get('current_price', 0):.2f}\n"
            context += f"- Trend: {data.get('trend', 'unknown')}\n"
            context += f"- RSI: {data.get('rsi', 0):.2f}\n"
            context += f"- ATR: {data.get('atr', 0):.4f}\n"

            # Include indicators based on availability
            if data.get('ema20'):
                context += f"- EMA20: ${data.get('ema20', 0):.2f}\n"
            if data.get('ema50'):
                context += f"- EMA50: ${data.get('ema50', 0):.2f}\n"
            if data.get('macd'):
                macd = data.get('macd', {})
                context += f"- MACD: {macd.get('histogram', 0):.4f}\n"

            # Market structure
            context += f"- Structure: {data.get('bos') or data.get('choch') or 'No clear break'}\n"
            context += f"- Price Change: {data.get('price_change_percent', 0):.2f}%\n\n"

        # Timeframe-specific system prompt
        tf_guidance = {
            "ultra_scalping": "Focus on immediate price action, liquidity sweeps, and quick structural breaks. Look for 1m/5m entries.",
            "scalping": "Focus on intraday momentum, RSI divergences, and 15m structural confirmations.",
            "short_term": "Focus on multi-timeframe trend alignment, H1/H4 structure, and day trading setups.",
            "swing": "Focus on daily/4H structure, major swing points, and multi-day trend continuation.",
            "long_term": "Focus on weekly/daily trends, major support/resistance, and position trade setups."
        }

        guidance = tf_guidance.get(analysis_type, "Focus on multi-timeframe confluence")

        system_prompt = f"""You are an expert ICT/SMC trader. Analyze the multi-timeframe data and provide:
1. Overall market bias (bullish/bearish/neutral) based on HTF→LTF confluence
2. Key market structure (CHOCH, BOS, liquidity zones)
3. Price action context for the timeframes analyzed

{guidance}

Be concise (3-4 sentences). Focus on actionable insights."""

        analysis = await qwen_client.generate(context, system_prompt, temperature=0.5)

        return analysis

    except Exception as e:
        logger.error(f"Qwen analysis error: {e}")
        return "Unable to generate AI analysis"
