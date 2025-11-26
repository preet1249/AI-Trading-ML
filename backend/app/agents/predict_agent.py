"""
Prediction Agent - INTELLIGENT SYNTHESIS
Combines TA and News data to generate actionable trading predictions
"""
import logging
from typing import Dict, Optional
import json

from app.services.qwen_client import qwen_client

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

        logger.info(f"Prediction Agent synthesizing data for {symbol}")

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

        # Compile final prediction
        final_prediction = {
            "symbol": symbol,
            "direction": prediction.get("direction", "NEUTRAL"),
            "target_price": prediction.get("target_price"),
            "stop_loss": prediction.get("stop_loss"),
            "confidence": confidence,
            "risk_level": risk_level,
            "timeframe": ta_data.get("primary_timeframe", "1h"),
            "entry_strategy": strategy.get("entry"),
            "exit_strategy": strategy.get("exit"),
            "key_levels": strategy.get("key_levels", []),
            "reasoning": prediction.get("reasoning", ""),
            "ta_summary": summarize_ta(ta_data),
            "news_impact": news_data.get("news_impact", "minimal"),
            "timestamp": ta_data.get("primary_analysis", {}).get("timestamp")
        }

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
    """Use Qwen to synthesize TA + News into actionable prediction"""
    try:
        # Build comprehensive context
        context = build_prediction_context(symbol, ta_data, news_data, analysis_type, query)

        system_prompt = f"""You are an expert ICT/SMC trader with deep knowledge of technical analysis and market psychology.

Analyze the provided technical and fundamental data to generate a trading prediction.

**Analysis Type**: {analysis_type}
**User Query**: {query}

Provide a JSON response with:
{{
    "direction": "BULLISH" | "BEARISH" | "NEUTRAL",
    "target_price": <float or null>,
    "stop_loss": <float or null>,
    "reasoning": "<3-4 sentences explaining the prediction>",
    "key_factors": ["<factor 1>", "<factor 2>", "<factor 3>"]
}}

Consider:
1. Multi-timeframe alignment (HTF trend + LTF entry)
2. Market structure (CHOCH, BOS, liquidity)
3. Sentiment confluence (TA + News)
4. Risk-reward ratio
5. Market condition (trending/ranging/volatile)

Be objective and data-driven. If conflicting signals, lean NEUTRAL."""

        # Generate prediction
        response = await qwen_client.generate(
            prompt=context,
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=500
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
    """Generate entry/exit strategy"""
    try:
        primary = ta_data.get("primary_analysis", {})
        current_price = primary.get("current_price", 0)
        atr = primary.get("atr", 0)
        ema20 = primary.get("ema20", 0)
        direction = prediction.get("direction", "NEUTRAL")

        strategy = {
            "entry": "",
            "exit": "",
            "key_levels": []
        }

        if direction == "BULLISH":
            # Entry strategy
            if analysis_type == "scalping":
                strategy["entry"] = f"Enter on pullback to ${ema20:.2f} (EMA20) or on breakout confirmation"
            else:
                strategy["entry"] = f"Enter on dips near ${current_price - atr:.2f} with stop loss below ${current_price - (2*atr):.2f}"

            # Exit strategy
            target = current_price + (2 * atr)
            strategy["exit"] = f"Take profit at ${target:.2f} (2x ATR target)"
            strategy["key_levels"] = [
                f"Support: ${ema20:.2f}",
                f"Target: ${target:.2f}",
                f"Stop: ${current_price - (2*atr):.2f}"
            ]

        elif direction == "BEARISH":
            # Entry strategy
            if analysis_type == "scalping":
                strategy["entry"] = f"Enter on pullback to ${ema20:.2f} (EMA20) or on breakdown confirmation"
            else:
                strategy["entry"] = f"Enter on rallies near ${current_price + atr:.2f} with stop loss above ${current_price + (2*atr):.2f}"

            # Exit strategy
            target = current_price - (2 * atr)
            strategy["exit"] = f"Take profit at ${target:.2f} (2x ATR target)"
            strategy["key_levels"] = [
                f"Resistance: ${ema20:.2f}",
                f"Target: ${target:.2f}",
                f"Stop: ${current_price + (2*atr):.2f}"
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
