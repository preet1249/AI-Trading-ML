"""
Prediction Agent - INTELLIGENT SYNTHESIS
Combines TA and News data to generate actionable trading predictions
"""
import logging
from typing import Dict, Optional, List
import json

from app.services.qwen_client import qwen_client
from app.core.advanced_analysis import advanced_analysis

logger = logging.getLogger(__name__)


async def predict_node(state: Dict) -> Dict:
    """
    Prediction Agent - Synthesize TA + News → Final prediction

    Combines multi-timeframe technical analysis with news sentiment
    to generate intelligent trading predictions with:
    - Direction (BULLISH/BEARISH/NEUTRAL)
    - Target price levels
    - Confidence score (0-100)
    - Risk level assessment
    - Entry/exit strategy
    - Detailed reasoning

    Args:
        state: {
            "query": user query,
            "symbol": trading symbol,
            "ta_data": technical analysis results,
            "news_data": news sentiment results,
            "analysis_type": "long_term" | "short_term" | "scalping"
        }

    Returns:
        Updated state with prediction
    """
    try:
        symbol = state.get("symbol")
        ta_data = state.get("ta_data", {})
        news_data = state.get("news_data", {})
        analysis_type = state.get("analysis_type", "short_term")
        query = state.get("query", "")
        market_status = state.get("market_status", {})
        exchange = state.get("exchange", "Unknown")
        market_type = state.get("market_type", "unknown")

        logger.info(f"Prediction Agent synthesizing data for {symbol} ({market_type})")

        # Check market hours for stocks (but continue with prediction using historical data)
        is_market_closed = False
        market_closed_message = ""

        if market_type == "stock" and market_status.get("is_open") == False:
            is_market_closed = True
            market_closed_message = market_status.get("message", "Market is currently closed")
            logger.info(f"📅 Market closed for {symbol} - generating NEXT TRADING DAY prediction using historical data + news")

        # Check if we have valid data
        if ta_data.get("error") or news_data.get("error"):
            return {
                "prediction": {
                    "direction": "NEUTRAL",
                    "confidence": 0,
                    "reasoning": "Insufficient data for prediction",
                    "error": "Missing TA or News data"
                }
            }

        # Generate prediction with Qwen
        prediction = await generate_prediction_with_qwen(
            symbol=symbol,
            ta_data=ta_data,
            news_data=news_data,
            analysis_type=analysis_type,
            query=query
        )

        # Calculate overall confidence
        confidence = calculate_confidence(ta_data, news_data, prediction)

        # Determine risk level
        risk_level = assess_risk_level(ta_data, news_data, confidence)

        # Generate entry/exit strategy
        strategy = generate_strategy(ta_data, prediction, analysis_type)

        # ADVANCED: Calculate intelligent entry and multiple TPs
        primary_analysis = ta_data.get("primary_analysis", {})
        current_price = primary_analysis.get("current_price", 0)
        atr = primary_analysis.get("atr", 0)
        fib_levels = primary_analysis.get("fibonacci", {})
        order_blocks = primary_analysis.get("order_blocks", [])
        market_condition = ta_data.get("market_condition", "unknown")
        direction = prediction.get("direction", "NEUTRAL")

        # Calculate optimal entry point
        optimal_entry = advanced_analysis.calculate_optimal_entry(
            current_price=current_price,
            direction=direction,
            fib_levels=fib_levels,
            order_blocks=order_blocks,
            atr=atr,
            market_condition=market_condition
        )

        # Use optimal entry or prediction entry
        best_entry = optimal_entry.get("price", current_price)
        entry_reason = optimal_entry.get("reason", "Current price")

        # Calculate stop loss (use prediction or calculate)
        stop_loss = prediction.get("stop_loss")
        if not stop_loss:
            if direction == "BULLISH":
                stop_loss = best_entry - (atr * 1.5)
            elif direction == "BEARISH":
                stop_loss = best_entry + (atr * 1.5)
            else:
                stop_loss = current_price

        # Calculate MULTIPLE TP levels based on market conditions
        multi_tps = advanced_analysis.calculate_multi_tp_levels(
            entry=best_entry,
            stop_loss=stop_loss,
            direction=direction,
            market_condition=market_condition,
            confidence=confidence,
            atr=atr,
            fib_levels=fib_levels
        )

        # Compile final prediction with ADVANCED analysis
        final_prediction = {
            "symbol": symbol,
            "direction": direction,
            "entry_price": best_entry,
            "entry_reason": entry_reason,
            "entry_confidence": optimal_entry.get("confidence", 70),
            "stop_loss": round(stop_loss, 2),
            "target_price": multi_tps[0]["price"] if multi_tps else prediction.get("target_price"),  # TP1 as main target
            "take_profits": multi_tps,  # Multiple TP levels with RR ratios
            "confidence": confidence,
            "risk_level": risk_level,
            "timeframe": ta_data.get("primary_timeframe", "1h"),
            "entry_strategy": strategy.get("entry"),
            "exit_strategy": strategy.get("exit"),
            "key_levels": strategy.get("key_levels", []),
            "reasoning": prediction.get("reasoning", ""),
            "ta_summary": summarize_ta(ta_data),
            "news_impact": news_data.get("news_impact", "minimal"),
            "timestamp": primary_analysis.get("timestamp"),
            # Advanced levels
            "fibonacci_levels": {
                "fib_618": fib_levels.get("fib_618"),
                "fib_500": fib_levels.get("fib_500"),
                "fib_382": fib_levels.get("fib_382")
            },
            "pivot_points": {
                "PP": primary_analysis.get("pivots", {}).get("PP"),
                "R1": primary_analysis.get("pivots", {}).get("R1"),
                "S1": primary_analysis.get("pivots", {}).get("S1")
            },
            "order_blocks": order_blocks[:2] if order_blocks else [],
            "market_condition": market_condition,
            # Market status
            "market_closed": is_market_closed,
            "market_status_message": market_closed_message,
            "exchange": exchange,
            "market_type": market_type
        }

        # Log prediction type
        if is_market_closed:
            logger.info(
                f"📅 NEXT DAY Prediction completed for {symbol}: {final_prediction['direction']} "
                f"(confidence: {confidence}%, risk: {risk_level}) - Market closed, using historical data + news"
            )
        else:
            logger.info(
                f"Prediction Agent completed: {final_prediction['direction']} "
                f"(confidence: {confidence}%, risk: {risk_level})"
            )

        return {"prediction": final_prediction}

    except Exception as e:
        logger.error(f"Prediction Agent error: {str(e)}")
        return {
            "prediction": {
                "direction": "NEUTRAL",
                "confidence": 0,
                "reasoning": f"Error generating prediction: {str(e)}",
                "error": str(e)
            }
        }


async def generate_prediction_with_qwen(
    symbol: str,
    ta_data: Dict,
    news_data: Dict,
    analysis_type: str,
    query: str
) -> Dict:
    """Use Qwen to synthesize TA + News into actionable prediction with timeframe-aware targets"""
    try:
        # Build comprehensive context
        context = build_prediction_context(symbol, ta_data, news_data, analysis_type, query)

        # Get timeframe-specific guidance
        primary_tf = ta_data.get("primary_timeframe", "1h")
        timeframes = ta_data.get("timeframes_analyzed", [primary_tf])
        primary = ta_data.get("primary_analysis", {})
        current_price = primary.get("current_price", 0)
        atr = primary.get("atr", 0)

        # INTELLIGENT TIMEFRAME-BASED TARGET/SL RANGES
        tf_guidance = get_timeframe_guidance(primary_tf, atr, current_price, analysis_type)

        system_prompt = f"""You are an expert ICT/SMC trader. Generate a COMPLETE trading plan with specific entry points and confirmation signals.

**Analysis Type**: {analysis_type}
**Primary Timeframe**: {primary_tf.upper()}
**All Timeframes**: {', '.join(timeframes)}
**User Query**: {query}

{tf_guidance}

Provide a JSON response with ALL these fields:
{{
    "direction": "BULLISH" | "BEARISH" | "NEUTRAL",
    "target_price": <float>,
    "stop_loss": <float>,
    "entry_price": <specific float price for entry>,
    "trade_type": "BREAKOUT" | "REVERSAL" | "CONTINUATION",
    "breakout_point": <price level if breakout>,
    "reversal_point": <price level if reversal>,
    "why_breakout_good": "<explain if breakout is valid>",
    "why_reversal_good": "<explain if reversal setup is valid>",
    "market_structure": "<CHOCH/BOS/liquidity sweep description>",
    "confirmation_signals": [
        "Signal 1: <what to watch>",
        "Signal 2: <candle pattern>",
        "Signal 3: <structural confirmation>"
    ],
    "what_to_watch": [
        "<specific price level or candle>",
        "<structural movement to monitor>",
        "<indicator confirmation>"
    ],
    "entry_confirmation": "<HOW to confirm entry - step by step>",
    "reasoning": "<detailed 4-5 sentence explanation covering structure, liquidity, and bias>",
    "key_factors": ["<factor 1>", "<factor 2>", "<factor 3>"]
}}

CRITICAL REQUIREMENTS:
1. **Entry Price**: Give EXACT price for entry, not "wait for rallies"
2. **Trade Type**: Identify if it's breakout/reversal/continuation
3. **Breakout Analysis**: If breakout, explain why it looks good/bad with price level
4. **Reversal Analysis**: If reversal, explain why setup is valid with reversal point
5. **Structure**: Mention CHOCH, BOS, liquidity sweeps, order blocks
6. **Confirmation**: List 3+ specific signals trader must see before entering
7. **What to Watch**: Specific candles, patterns, price action to monitor
8. **Entry Confirmation**: Step-by-step process to confirm trade
9. **TIMEFRAME APPROPRIATE**: Use the target/SL ranges specified above for {primary_tf}

Be SPECIFIC with prices and signals. No vague advice."""

        # Generate prediction
        response = await qwen_client.generate(
            prompt=context,
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=1500  # Increased for detailed predictions
        )

        # Parse JSON response
        try:
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()

            prediction = json.loads(json_str)
            return prediction

        except json.JSONDecodeError:
            # Fallback: parse manually
            logger.warning("Failed to parse JSON, using fallback parsing")
            return parse_prediction_fallback(response)

    except Exception as e:
        logger.error(f"Qwen prediction generation error: {e}")
        return {
            "direction": "NEUTRAL",
            "target_price": None,
            "stop_loss": None,
            "reasoning": "Unable to generate prediction due to AI error",
            "key_factors": []
        }


def build_prediction_context(
    symbol: str,
    ta_data: Dict,
    news_data: Dict,
    analysis_type: str,
    query: str
) -> str:
    """Build comprehensive context for Qwen prediction"""
    context = f"# Trading Analysis for {symbol}\n\n"

    # Technical Analysis Summary
    context += "## Technical Analysis\n\n"

    primary_tf = ta_data.get("primary_timeframe", "1h")
    primary = ta_data.get("primary_analysis", {})
    multi_tf = ta_data.get("multi_timeframe_analysis", {})

    context += f"**Primary Timeframe**: {primary_tf.upper()}\n"
    context += f"- Current Price: ${primary.get('current_price', 0):.2f}\n"
    context += f"- Trend: {primary.get('trend', 'unknown').upper()}\n"
    context += f"- RSI: {primary.get('rsi', 0):.2f}\n"
    context += f"- EMA20: ${primary.get('ema20', 0):.2f}\n"

    if primary.get('ema50'):
        context += f"- EMA50: ${primary.get('ema50', 0):.2f}\n"

    context += f"- ATR: ${primary.get('atr', 0):.4f}\n"
    context += f"- Market Structure: {primary.get('bos') or primary.get('choch') or 'No clear break'}\n"
    context += f"- Market Condition: {ta_data.get('market_condition', 'unknown').upper()}\n"
    context += f"- Price Change: {primary.get('price_change_percent', 0):.2f}%\n\n"

    # Multi-timeframe confluence
    if len(multi_tf) > 1:
        context += "**Multi-Timeframe Analysis**:\n"
        for tf, data in multi_tf.items():
            context += f"- {tf.upper()}: {data.get('trend', 'unknown')} trend, RSI {data.get('rsi', 0):.0f}\n"
        context += "\n"

    # Qwen TA Analysis
    if ta_data.get("qwen_analysis"):
        context += f"**AI Technical Analysis**:\n{ta_data['qwen_analysis']}\n\n"

    # News Sentiment
    context += "## News Sentiment\n\n"
    context += f"- Overall Sentiment: {news_data.get('sentiment', 'neutral').upper()}\n"
    context += f"- Sentiment Score: {news_data.get('sentiment_score', 0):.2f}\n"
    context += f"- Articles Analyzed: {news_data.get('articles_count', 0)}\n"
    context += f"- News Impact: {news_data.get('news_impact', 'minimal').upper()}\n\n"

    # Key events
    key_events = news_data.get("key_events", [])
    if key_events:
        context += "**Key Events**:\n"
        for event in key_events[:3]:
            context += f"- {event}\n"
        context += "\n"

    # Qwen News Analysis
    if news_data.get("qwen_analysis"):
        context += f"**AI News Analysis**:\n{news_data['qwen_analysis']}\n\n"

    return context


def get_timeframe_guidance(timeframe: str, atr: float, current_price: float, analysis_type: str) -> str:
    """
    Generate intelligent timeframe-specific guidance for target/SL calculations

    CRITICAL: Different timeframes need different target/SL ranges!
    - 1m: Tight targets (0.5-1x ATR) for quick scalps
    - 5m: Small targets (1-2x ATR) for session scalps
    - 15m: Medium targets (2-3x ATR) for intraday
    - 1h: Larger targets (3-5x ATR) for day trading
    - 4h: Big targets (5-8x ATR) for swing entries
    - 1d: Very large targets (8-15x ATR) for position trades
    """
    # Calculate ATR multipliers based on timeframe
    tf_multipliers = {
        "1m": {"target": (0.5, 1.0), "sl": (0.3, 0.5), "description": "ultra-tight scalping"},
        "5m": {"target": (1.0, 2.0), "sl": (0.5, 1.0), "description": "session scalping"},
        "15m": {"target": (2.0, 3.0), "sl": (1.0, 1.5), "description": "intraday trading"},
        "1h": {"target": (3.0, 5.0), "sl": (1.5, 2.5), "description": "day trading"},
        "4h": {"target": (5.0, 8.0), "sl": (2.5, 4.0), "description": "swing trading"},
        "1d": {"target": (8.0, 15.0), "sl": (4.0, 8.0), "description": "position trading"}
    }

    multipliers = tf_multipliers.get(timeframe, {"target": (2.0, 4.0), "sl": (1.0, 2.0), "description": "standard trading"})

    # Calculate actual ranges
    target_min = current_price + (atr * multipliers["target"][0])
    target_max = current_price + (atr * multipliers["target"][1])
    sl_min = current_price - (atr * multipliers["sl"][0])
    sl_max = current_price - (atr * multipliers["sl"][1])

    guidance = f"""
**TIMEFRAME-SPECIFIC TARGET/SL GUIDANCE for {timeframe.upper()}**:

This is a **{multipliers['description']}** timeframe. Use APPROPRIATE ranges:

- **ATR**: ${atr:.4f} ({(atr/current_price)*100:.2f}% of price)
- **Current Price**: ${current_price:.2f}

**TARGET RANGE** (for BULLISH):
  - Minimum: ${target_min:.2f} ({multipliers['target'][0]}x ATR)
  - Maximum: ${target_max:.2f} ({multipliers['target'][1]}x ATR)
  - For BEARISH: ${current_price - (atr * multipliers['target'][0]):.2f} to ${current_price - (atr * multipliers['target'][1]):.2f}

**STOP LOSS RANGE**:
  - Minimum: ${sl_max:.2f} ({multipliers['sl'][1]}x ATR)
  - Maximum: ${sl_min:.2f} ({multipliers['sl'][0]}x ATR)

⚠️  **IMPORTANT**:
- For {timeframe} timeframe, DO NOT use targets from daily charts!
- {timeframe} trades are {multipliers['description']} - use TIGHT stops and realistic targets
- A $1000 target on 1m is WRONG - it should be ${target_min:.2f}-${target_max:.2f}
- Risk-reward should be 1:1.5 to 1:3 for this timeframe
"""

    return guidance


def parse_prediction_fallback(response: str) -> Dict:
    """Fallback parser if JSON parsing fails"""
    prediction = {
        "direction": "NEUTRAL",
        "target_price": None,
        "stop_loss": None,
        "reasoning": response[:200],
        "key_factors": []
    }

    # Try to extract direction
    response_lower = response.lower()
    if "bullish" in response_lower:
        prediction["direction"] = "BULLISH"
    elif "bearish" in response_lower:
        prediction["direction"] = "BEARISH"

    return prediction


def calculate_confidence(ta_data: Dict, news_data: Dict, prediction: Dict) -> int:
    """Calculate overall confidence score (0-100)"""
    try:
        confidence = 50  # Base confidence

        # TA confidence factors
        primary = ta_data.get("primary_analysis", {})
        trend = primary.get("trend", "unknown")
        rsi = primary.get("rsi", 50)
        market_condition = ta_data.get("market_condition", "unknown")

        # Strong trend increases confidence
        if trend in ["bullish", "bearish"]:
            confidence += 10

        # RSI extremes increase confidence
        if rsi > 70 or rsi < 30:
            confidence += 5

        # Trending market increases confidence
        if market_condition == "trending":
            confidence += 10
        elif market_condition == "volatile":
            confidence -= 10

        # Multi-timeframe alignment
        multi_tf = ta_data.get("multi_timeframe_analysis", {})
        if len(multi_tf) > 1:
            trends = [data.get("trend") for data in multi_tf.values()]
            # All same trend = strong alignment
            if len(set(trends)) == 1 and trends[0] in ["bullish", "bearish"]:
                confidence += 15

        # News sentiment alignment
        news_sentiment = news_data.get("sentiment", "neutral")
        news_impact = news_data.get("news_impact", "minimal")

        # Sentiment aligns with prediction
        direction = prediction.get("direction", "NEUTRAL")
        if (news_sentiment == "bullish" and direction == "BULLISH") or \
           (news_sentiment == "bearish" and direction == "BEARISH"):
            confidence += 10

        # High news impact
        if news_impact in ["high", "medium"]:
            confidence += 5

        # Ensure confidence is within bounds
        return max(0, min(100, confidence))

    except Exception as e:
        logger.error(f"Confidence calculation error: {e}")
        return 50


def assess_risk_level(ta_data: Dict, news_data: Dict, confidence: int) -> str:
    """Assess risk level (LOW/MEDIUM/HIGH)"""
    try:
        market_condition = ta_data.get("market_condition", "unknown")
        news_impact = news_data.get("news_impact", "minimal")
        primary = ta_data.get("primary_analysis", {})
        atr_percent = (primary.get("atr", 0) / primary.get("current_price", 1)) * 100

        # High volatility = high risk
        if market_condition == "volatile" or atr_percent > 3:
            return "HIGH"

        # High news impact = higher risk
        if news_impact == "high":
            return "HIGH"

        # Low confidence = higher risk
        if confidence < 50:
            return "HIGH"
        elif confidence < 70:
            return "MEDIUM"

        return "LOW"

    except:
        return "MEDIUM"


def generate_strategy(ta_data: Dict, prediction: Dict, analysis_type: str) -> Dict:
    """Generate timeframe-aware entry/exit strategy"""
    try:
        primary = ta_data.get("primary_analysis", {})
        current_price = primary.get("current_price", 0)
        atr = primary.get("atr", 0)
        ema20 = primary.get("ema20", 0)
        direction = prediction.get("direction", "NEUTRAL")
        primary_tf = ta_data.get("primary_timeframe", "1h")

        # Get timeframe-specific multipliers
        tf_multipliers = {
            "1m": {"target": 0.75, "sl": 0.4},
            "5m": {"target": 1.5, "sl": 0.75},
            "15m": {"target": 2.5, "sl": 1.25},
            "1h": {"target": 4.0, "sl": 2.0},
            "4h": {"target": 6.5, "sl": 3.0},
            "1d": {"target": 10.0, "sl": 5.0}
        }

        multiplier = tf_multipliers.get(primary_tf, {"target": 3.0, "sl": 1.5})
        target_mult = multiplier["target"]
        sl_mult = multiplier["sl"]

        strategy = {
            "entry": "",
            "exit": "",
            "key_levels": []
        }

        if direction == "BULLISH":
            # Entry strategy - timeframe specific
            if primary_tf in ["1m", "5m"]:
                strategy["entry"] = f"Enter on micro pullback or immediate breakout (scalp entry)"
            elif primary_tf in ["15m", "1h"]:
                strategy["entry"] = f"Enter on pullback to ${ema20:.2f} (EMA20) or structural support"
            else:
                strategy["entry"] = f"Enter on dips near ${current_price - atr:.2f} with confirmation"

            # Timeframe-appropriate targets
            target = current_price + (target_mult * atr)
            stop = current_price - (sl_mult * atr)

            strategy["exit"] = f"Take profit at ${target:.2f} ({target_mult}x ATR for {primary_tf})"
            strategy["key_levels"] = [
                f"Entry Zone: ${current_price:.2f}",
                f"Support: ${ema20:.2f}" if ema20 else f"Support: ${current_price - atr:.2f}",
                f"Target: ${target:.2f}",
                f"Stop Loss: ${stop:.2f}"
            ]

        elif direction == "BEARISH":
            # Entry strategy - timeframe specific
            if primary_tf in ["1m", "5m"]:
                strategy["entry"] = f"Enter on micro bounce or immediate breakdown (scalp entry)"
            elif primary_tf in ["15m", "1h"]:
                strategy["entry"] = f"Enter on rally to ${ema20:.2f} (EMA20) or structural resistance"
            else:
                strategy["entry"] = f"Enter on rallies near ${current_price + atr:.2f} with confirmation"

            # Timeframe-appropriate targets
            target = current_price - (target_mult * atr)
            stop = current_price + (sl_mult * atr)

            strategy["exit"] = f"Take profit at ${target:.2f} ({target_mult}x ATR for {primary_tf})"
            strategy["key_levels"] = [
                f"Entry Zone: ${current_price:.2f}",
                f"Resistance: ${ema20:.2f}" if ema20 else f"Resistance: ${current_price + atr:.2f}",
                f"Target: ${target:.2f}",
                f"Stop Loss: ${stop:.2f}"
            ]

        else:
            strategy["entry"] = "Wait for clear directional bias"
            strategy["exit"] = "No trade recommended"
            strategy["key_levels"] = [f"Current Price: ${current_price:.2f}"]

        return strategy

    except Exception as e:
        logger.error(f"Strategy generation error: {e}")
        return {
            "entry": "Unable to generate strategy",
            "exit": "Unable to generate strategy",
            "key_levels": []
        }


def summarize_ta(ta_data: Dict) -> str:
    """Create brief TA summary"""
    try:
        primary = ta_data.get("primary_analysis", {})
        trend = primary.get("trend", "unknown")
        rsi = primary.get("rsi", 0)
        market_condition = ta_data.get("market_condition", "unknown")

        summary = f"{trend.upper()} trend, {market_condition} market, RSI at {rsi:.0f}"
        return summary

    except:
        return "Technical analysis summary unavailable"
