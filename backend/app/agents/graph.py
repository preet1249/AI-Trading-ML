"""
LangGraph Setup - INTELLIGENT AGENT ORCHESTRATION
Multi-agent system with query understanding and dynamic routing
"""
import logging
import re
from typing import TypedDict, List
from langgraph.graph import StateGraph, END

from app.agents.ta_agent import ta_node
from app.agents.news_agent import news_node
from app.agents.predict_agent import predict_node
from app.services.qwen_client import qwen_client

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """Shared state across all agents"""
    query: str
    symbol: str
    timeframes: List[str]
    analysis_type: str
    user_id: str
    ta_data: dict
    news_data: dict
    prediction: dict


async def parse_query_node(state: AgentState) -> AgentState:
    """
    Intelligent Query Understanding Node

    Parses user query to determine:
    - Trading symbol
    - Analysis type (long_term, short_term, scalping)
    - Appropriate timeframes

    Examples:
    - "long term prediction for BTC" → long_term, ["1d", "4h"]
    - "day trading AAPL today" → short_term, ["4h", "1h", "15m"]
    - "next move in ETHUSDT" → scalping, ["1h", "15m", "5m"]
    - "should I buy Bitcoin?" → short_term, ["4h", "1h"]
    """
    try:
        query = state.get("query", "").lower()
        logger.info(f"Parsing query: {query}")

        # Extract symbol (if not already provided)
        symbol = state.get("symbol")
        if not symbol:
            symbol = extract_symbol_from_query(query)
            if not symbol:
                # Ask Qwen to extract symbol
                symbol = await extract_symbol_with_qwen(query)

        # Determine analysis type
        analysis_type = determine_analysis_type(query)

        # Select appropriate timeframes
        timeframes = select_timeframes(query, analysis_type)

        logger.info(
            f"Parsed: symbol={symbol}, type={analysis_type}, "
            f"timeframes={timeframes}"
        )

        # Update state
        return {
            "query": state.get("query"),
            "symbol": symbol,
            "timeframes": timeframes,
            "analysis_type": analysis_type,
            "user_id": state.get("user_id", "")
        }

    except Exception as e:
        logger.error(f"Query parsing error: {e}")
        # Fallback to defaults
        return {
            "query": state.get("query"),
            "symbol": state.get("symbol", "BTCUSDT"),
            "timeframes": ["1h"],
            "analysis_type": "short_term",
            "user_id": state.get("user_id", "")
        }


def extract_symbol_from_query(query: str) -> str:
    """Extract trading symbol from query using pattern matching"""
    # Common crypto symbols
    crypto_patterns = [
        r'\b(BTC|ETH|BNB|XRP|ADA|SOL|DOGE|MATIC|DOT|AVAX|LINK|UNI|ATOM|LTC|ETC|XLM)(USDT|BUSD|USDC|BTC|ETH)?\b',
        r'\bbitcoin\b',
        r'\bethereum\b',
        r'\bbinance\s+coin\b',
    ]

    # Stock symbols (2-5 uppercase letters)
    stock_patterns = [
        r'\b([A-Z]{2,5})\b(?!.*(?:on|in|at|for|the|and|or|is|are|was))',
    ]

    # Try crypto patterns first
    for pattern in crypto_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            symbol = match.group(1).upper()
            # Map common names to symbols
            name_to_symbol = {
                "BITCOIN": "BTCUSDT",
                "ETHEREUM": "ETHUSDT",
                "BINANCE": "BNBUSDT",
            }
            if symbol in name_to_symbol:
                return name_to_symbol[symbol]
            # Add USDT if not already present
            if not any(symbol.endswith(suffix) for suffix in ["USDT", "BUSD", "USDC", "BTC", "ETH"]):
                return f"{symbol}USDT"
            return symbol

    # Try stock symbols
    words = query.upper().split()
    for word in words:
        if len(word) >= 2 and len(word) <= 5 and word.isalpha():
            # Common stock symbols
            if word in ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN", "META", "NVDA", "AMD", "NFLX"]:
                return word

    return ""


async def extract_symbol_with_qwen(query: str) -> str:
    """Use Qwen to extract symbol from complex queries"""
    try:
        system_prompt = """Extract the trading symbol from the user query.

If it's a crypto, return the symbol with USDT suffix (e.g., BTCUSDT, ETHUSDT).
If it's a stock, return just the ticker (e.g., AAPL, GOOGL).

Respond with ONLY the symbol, nothing else. If no symbol found, respond with "BTCUSDT"."""

        response = await qwen_client.generate(
            prompt=query,
            system_prompt=system_prompt,
            temperature=0.1,
            max_tokens=20
        )

        symbol = response.strip().upper()
        # Validate symbol
        if len(symbol) >= 3 and len(symbol) <= 12:
            return symbol

        return "BTCUSDT"  # Default

    except Exception as e:
        logger.error(f"Qwen symbol extraction error: {e}")
        return "BTCUSDT"


def determine_analysis_type(query: str) -> str:
    """Determine analysis type from query"""
    # Long-term indicators
    long_term_keywords = [
        "long term", "long-term", "invest", "hold", "hodl",
        "next month", "next year", "weekly", "monthly",
        "swing trade", "swing trading", "position"
    ]

    # Scalping indicators
    scalping_keywords = [
        "scalp", "quick trade", "next move", "right now",
        "immediate", "1 minute", "5 minute", "minute chart",
        "intraday", "quick flip"
    ]

    # Day trading indicators
    short_term_keywords = [
        "day trad", "today", "short term", "short-term",
        "this week", "few days", "daily", "4 hour",
        "hourly", "15 minute"
    ]

    query_lower = query.lower()

    # Check for long-term
    if any(keyword in query_lower for keyword in long_term_keywords):
        return "long_term"

    # Check for scalping
    if any(keyword in query_lower for keyword in scalping_keywords):
        return "scalping"

    # Check for short-term (day trading)
    if any(keyword in query_lower for keyword in short_term_keywords):
        return "short_term"

    # Default to short-term for general queries
    return "short_term"


def select_timeframes(query: str, analysis_type: str) -> List[str]:
    """
    Select appropriate timeframes based on query and analysis type

    Long-term: Daily + 4H for context
    Short-term: 4H + 1H + 15M for day trading
    Scalping: 1H + 15M + 5M for quick moves
    """
    timeframe_map = {
        "long_term": ["1d", "4h"],
        "short_term": ["4h", "1h", "15m"],
        "scalping": ["1h", "15m", "5m"]
    }

    # Check if user explicitly mentions timeframes
    query_lower = query.lower()

    explicit_timeframes = []
    timeframe_patterns = {
        "1m": ["1m", "1 min", "one minute"],
        "5m": ["5m", "5 min", "five minute"],
        "15m": ["15m", "15 min", "fifteen minute"],
        "1h": ["1h", "1 hour", "hourly"],
        "4h": ["4h", "4 hour"],
        "1d": ["1d", "daily", "day"],
        "1w": ["1w", "weekly", "week"]
    }

    for tf, patterns in timeframe_patterns.items():
        if any(pattern in query_lower for pattern in patterns):
            explicit_timeframes.append(tf)

    # Use explicit timeframes if found
    if explicit_timeframes:
        # Ensure we have at least 2 timeframes for multi-TF analysis
        if len(explicit_timeframes) == 1:
            # Add complementary timeframe
            tf = explicit_timeframes[0]
            if tf in ["1m", "5m"]:
                explicit_timeframes.append("15m")
            elif tf in ["15m", "1h"]:
                explicit_timeframes.append("4h")
            elif tf in ["4h", "1d"]:
                explicit_timeframes.append("1d")

        return explicit_timeframes[:3]  # Max 3 timeframes

    # Use default timeframes for analysis type
    return timeframe_map.get(analysis_type, ["1h"])


def should_skip_news(state: AgentState) -> str:
    """
    Conditional routing: Skip news for ultra-short-term scalping

    Returns:
        "predict" - skip news, go directly to prediction
        "news" - include news analysis
    """
    analysis_type = state.get("analysis_type", "short_term")

    # For 1m/5m scalping, news is less relevant - skip it
    timeframes = state.get("timeframes", [])
    has_minute_charts = any(tf in ["1m", "5m"] for tf in timeframes)

    if analysis_type == "scalping" and has_minute_charts:
        logger.info("Skipping news for ultra-short-term scalping")
        # Set empty news data
        state["news_data"] = {
            "sentiment": "neutral",
            "sentiment_score": 0,
            "news_impact": "minimal",
            "qwen_analysis": "News skipped for scalping timeframe"
        }
        return "predict"

    return "news"


def build_agent_graph() -> StateGraph:
    """
    Build Intelligent LangGraph Agent Workflow

    Flow:
    1. Parse Query - Understand intent, extract symbol, select timeframes
    2. TA Agent - Multi-timeframe technical analysis (parallel execution)
    3. News Agent - Sentiment analysis (conditional - skip for scalping)
    4. Predict Agent - Synthesize TA + News → Final prediction

    Features:
    - Dynamic timeframe selection based on query
    - Intelligent routing (skip news for scalping)
    - Multi-timeframe analysis for confluence
    - Context-aware predictions

    Returns:
        Compiled LangGraph workflow
    """
    # Initialize graph with state schema
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("parse_query", parse_query_node)
    graph.add_node("ta", ta_node)
    graph.add_node("news", news_node)
    graph.add_node("predict", predict_node)

    # Define flow
    graph.set_entry_point("parse_query")
    graph.add_edge("parse_query", "ta")

    # Conditional routing: Skip news for scalping
    graph.add_conditional_edges(
        "ta",
        should_skip_news,
        {
            "news": "news",
            "predict": "predict"
        }
    )

    graph.add_edge("news", "predict")
    graph.add_edge("predict", END)

    # Compile graph
    app = graph.compile()

    logger.info("LangGraph workflow compiled successfully")

    return app


# Export compiled graph
prediction_workflow = build_agent_graph()
