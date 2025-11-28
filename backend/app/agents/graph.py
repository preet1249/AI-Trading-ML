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
from app.services.stock_intelligence import stock_intelligence

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
    exchange: str  # NSE, NASDAQ, NYSE, Binance
    market_type: str  # stock, crypto
    market_status: dict  # Market open/closed info


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
        query = state.get("query", "")
        query_lower = query.lower()
        logger.info(f"Parsing query: {query}")

        # Extract symbol (if not already provided)
        symbol = state.get("symbol")
        exchange = None
        market_type = None
        market_status = {}

        if not symbol:
            # Try AI-powered stock detection first (works for ANY company worldwide)
            stock_symbol, stock_exchange, stock_type = await stock_intelligence.detect_stock_with_ai(query)

            if stock_symbol:
                # Stock detected!
                symbol = stock_symbol
                exchange = stock_exchange
                market_type = stock_type

                # Check market hours for stocks
                is_open, status_msg = stock_intelligence.is_market_open(exchange)
                market_status = {
                    "is_open": is_open,
                    "message": status_msg,
                    "exchange": exchange
                }

                logger.info(f"Stock detected: {symbol} on {exchange}")
                logger.info(f"Market status: {status_msg}")

            else:
                # Try crypto extraction
                symbol = extract_symbol_from_query(query)
                if not symbol:
                    # Ask Qwen to extract symbol
                    symbol = await extract_symbol_with_qwen(query)

                # Determine if crypto or stock based on symbol format
                from app.core.data_fetcher import _is_crypto_symbol
                is_crypto = _is_crypto_symbol(symbol) if symbol else False

                if is_crypto:
                    # Crypto - no market hours restriction
                    market_type = "crypto"
                    exchange = "Binance"
                    market_status = {
                        "is_open": True,
                        "message": "Crypto market is always open (24/7)",
                        "exchange": exchange
                    }
                else:
                    # Stock - assume US market by default
                    market_type = "stock"
                    exchange = "US"
                    is_open, status_msg = stock_intelligence.is_market_open(exchange)
                    market_status = {
                        "is_open": is_open,
                        "message": status_msg,
                        "exchange": exchange
                    }
                    logger.info(f"Stock symbol detected: {symbol} on {exchange}")

        # Determine analysis type
        analysis_type = determine_analysis_type(query_lower)

        # Select appropriate timeframes
        timeframes = select_timeframes(query_lower, analysis_type)

        logger.info(
            f"Parsed: symbol={symbol}, type={analysis_type}, "
            f"timeframes={timeframes}, exchange={exchange}"
        )

        # Update state
        return {
            "query": state.get("query"),
            "symbol": symbol,
            "timeframes": timeframes,
            "analysis_type": analysis_type,
            "user_id": state.get("user_id", ""),
            "exchange": exchange or "Unknown",
            "market_type": market_type or "unknown",
            "market_status": market_status
        }

    except Exception as e:
        logger.error(f"Query parsing error: {e}")
        import traceback
        traceback.print_exc()
        # Fallback to defaults
        return {
            "query": state.get("query"),
            "symbol": state.get("symbol", "BTCUSDT"),
            "timeframes": ["1h"],
            "analysis_type": "short_term",
            "user_id": state.get("user_id", ""),
            "exchange": "Binance",
            "market_type": "crypto",
            "market_status": {"is_open": True, "message": "Crypto 24/7"}
        }


def extract_symbol_from_query(query: str) -> str:
    """Extract trading symbol from query using pattern matching"""
    query_lower = query.lower()

    # Map common names to symbols first (exact match)
    name_to_symbol = {
        "bitcoin": "BTCUSDT",
        "btc": "BTCUSDT",
        "ethereum": "ETHUSDT",
        "eth": "ETHUSDT",
        "binance coin": "BNBUSDT",
        "bnb": "BNBUSDT",
        "solana": "SOLUSDT",
        "sol": "SOLUSDT",
        "cardano": "ADAUSDT",
        "ada": "ADAUSDT",
        "ripple": "XRPUSDT",
        "xrp": "XRPUSDT"
    }

    # Check for exact matches first
    for name, symbol in name_to_symbol.items():
        if re.search(r'\b' + name + r'\b', query_lower):
            return symbol

    # Try crypto symbol patterns with optional USDT suffix
    crypto_pattern = r'\b(BTC|ETH|BNB|XRP|ADA|SOL|DOGE|MATIC|DOT|AVAX|LINK|UNI|ATOM|LTC|ETC|XLM)(USDT|BUSD|USDC|BTC|ETH)?\b'
    match = re.search(crypto_pattern, query, re.IGNORECASE)
    if match:
        symbol = match.group(1).upper()
        suffix = match.group(2)

        # If suffix exists, use it; otherwise add USDT
        if suffix:
            return f"{symbol}{suffix.upper()}"
        else:
            return f"{symbol}USDT"

    # Try stock symbols (2-5 uppercase letters)
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
    """
    Intelligently determine analysis type from query with context understanding

    ULTRA_SCALPING (1m-5m): Session trading, quick moves, seconds/minutes
    SCALPING (5m-15m): Intraday, quick trades, within hours
    SHORT_TERM (15m-4h): Day trading, today, few hours to end of day
    SWING (4h-1d): Few days, this week, swing trades
    LONG_TERM (1d-1w): Weeks/months, investing, position trading
    """
    query_lower = query.lower()

    # PRIORITY 1: Ultra-scalping (1m-5m) - Session-based, real-time
    # Keywords: session, scalp, minute, quick, now, immediate
    ultra_scalping_keywords = [
        "session",  # "today newyork session" → 1m
        "london session", "new york session", "ny session", "asian session",
        "tokyo session", "opening session", "closing session",
        "scalp", "quick trade", "quick move", "quick flip",
        "right now", "immediate", "instantly", "real time", "realtime",
        "1 minute", "1m", "5 minute", "5m", "one minute", "five minute",
        "minute chart", "minute timeframe", "second", "seconds",
        "next candle", "next bar", "current candle"
    ]

    # PRIORITY 2: Scalping (5m-15m) - Intraday quick trades
    scalping_keywords = [
        "intraday", "intra day", "intra-day",
        "next move", "short move", "quick entry",
        "next hour", "within hour", "couple hours",
        "15 minute", "15m", "fifteen minute",
        "fast trade", "rapid"
    ]

    # PRIORITY 3: Short-term day trading (15m-4h) - Today's trading
    short_term_keywords = [
        "today", "day trad", "end of day", "eod",
        "this afternoon", "this evening", "this morning",
        "few hours", "couple of hours", "next few hours",
        "short term", "short-term",
        "hourly", "1 hour", "1h", "4 hour", "4h"
    ]

    # PRIORITY 4: Swing trading (4h-1d) - Multi-day
    swing_keywords = [
        "swing", "swing trade", "swing trading",
        "this week", "few days", "couple days", "next week",
        "end of week", "eow", "weekly target",
        "daily chart", "daily timeframe", "1d"
    ]

    # PRIORITY 5: Long-term (1d-1w+) - Position/investing
    long_term_keywords = [
        "long term", "long-term", "invest", "hold", "hodl",
        "next month", "next year", "this month", "this quarter",
        "weeks", "months", "years",
        "position trad", "position size",
        "monthly", "weekly chart", "1w"
    ]

    # Check in priority order (most specific first)
    if any(keyword in query_lower for keyword in ultra_scalping_keywords):
        return "ultra_scalping"

    if any(keyword in query_lower for keyword in scalping_keywords):
        return "scalping"

    if any(keyword in query_lower for keyword in short_term_keywords):
        return "short_term"

    if any(keyword in query_lower for keyword in swing_keywords):
        return "swing"

    if any(keyword in query_lower for keyword in long_term_keywords):
        return "long_term"

    # Default: If query is very short/vague → short_term
    # "predict BTC" → short_term (4h/1h)
    return "short_term"


def select_timeframes(query: str, analysis_type: str) -> List[str]:
    """
    Intelligently select timeframes based on query and analysis type

    Multi-timeframe approach: LTF (entry) + MTF (trend) + HTF (bias)

    ULTRA_SCALPING: 1m (entry) + 5m (trend) + 15m (bias)
    SCALPING: 5m (entry) + 15m (trend) + 1h (bias)
    SHORT_TERM: 15m (entry) + 1h (trend) + 4h (bias)
    SWING: 1h (entry) + 4h (trend) + 1d (bias)
    LONG_TERM: 4h (entry) + 1d (trend) + 1w (bias)

    Examples:
    - "BTC prediction today newyork session" → ultra_scalping → ["1m", "5m", "15m"]
    - "scalp ETHUSDT" → scalping → ["5m", "15m", "1h"]
    - "day trading AAPL today" → short_term → ["15m", "1h", "4h"]
    - "swing trade BTC this week" → swing → ["1h", "4h", "1d"]
    - "long term Bitcoin investment" → long_term → ["4h", "1d", "1w"]
    """
    # Comprehensive timeframe mapping
    timeframe_map = {
        "ultra_scalping": ["1m", "5m", "15m"],  # Session trading
        "scalping": ["5m", "15m", "1h"],        # Intraday quick trades
        "short_term": ["15m", "1h", "4h"],      # Day trading
        "swing": ["1h", "4h", "1d"],            # Multi-day swings
        "long_term": ["4h", "1d", "1w"]         # Position trading
    }

    query_lower = query.lower()

    # Check if user explicitly mentions timeframes
    explicit_timeframes = []
    timeframe_patterns = {
        "1m": ["1m", "1 min", "one minute", "minute chart"],
        "5m": ["5m", "5 min", "five minute"],
        "15m": ["15m", "15 min", "fifteen minute"],
        "1h": ["1h", "1 hour", "hourly", "hour chart"],
        "4h": ["4h", "4 hour"],
        "1d": ["1d", "daily", "day chart"],
        "1w": ["1w", "weekly", "week chart"]
    }

    for tf, patterns in timeframe_patterns.items():
        if any(pattern in query_lower for pattern in patterns):
            explicit_timeframes.append(tf)

    # Use explicit timeframes if user specified them
    if explicit_timeframes:
        # Ensure multi-TF analysis with complementary timeframes
        if len(explicit_timeframes) == 1:
            base_tf = explicit_timeframes[0]
            # Add higher timeframe for trend context
            if base_tf == "1m":
                explicit_timeframes.extend(["5m", "15m"])
            elif base_tf == "5m":
                explicit_timeframes.extend(["15m", "1h"])
            elif base_tf == "15m":
                explicit_timeframes.extend(["1h", "4h"])
            elif base_tf == "1h":
                explicit_timeframes.extend(["4h", "1d"])
            elif base_tf == "4h":
                explicit_timeframes.extend(["1d", "1w"])
            elif base_tf == "1d":
                explicit_timeframes.extend(["1w"])

        return explicit_timeframes[:3]  # Max 3 timeframes for efficiency

    # Use intelligent defaults based on analysis type
    return timeframe_map.get(analysis_type, ["15m", "1h", "4h"])


def should_skip_news(state: AgentState) -> str:
    """
    Conditional routing: Skip news for ultra-short-term scalping

    News relevance:
    - Ultra-scalping (1m-5m): Skip news (price action only)
    - Scalping (5m-15m): Skip news (technical focus)
    - Short-term+ (15m+): Include news (fundamental impact)

    Returns:
        "predict" - skip news, go directly to prediction
        "news" - include news analysis
    """
    analysis_type = state.get("analysis_type", "short_term")

    # Skip news for ultra-fast timeframes (1m-15m)
    if analysis_type in ["ultra_scalping", "scalping"]:
        logger.info(f"Skipping news for {analysis_type} - focusing on price action")
        # Set minimal news data
        state["news_data"] = {
            "sentiment": "neutral",
            "sentiment_score": 0,
            "news_impact": f"minimal (news skipped for {analysis_type})",
            "qwen_analysis": f"News analysis skipped - {analysis_type} focuses on technical price action"
        }
        return "predict"

    # Include news for day trading and beyond (15m+)
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
