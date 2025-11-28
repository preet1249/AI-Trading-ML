"""
Stock Intelligence Service
- AI-powered country and exchange detection
- Automatic symbol suffix addition (.NS for India, etc.)
- Market hours validation
- Works for ANY company worldwide
"""
import logging
from datetime import datetime, time
from typing import Dict, Optional, Tuple
import pytz
import re

logger = logging.getLogger(__name__)


class StockIntelligence:
    """Intelligent stock symbol detection and market hours"""

    # US Stock Mapping (Common names → Symbols)
    US_STOCKS = {
        # Tech Giants
        "apple": "AAPL",
        "microsoft": "MSFT",
        "google": "GOOGL",
        "alphabet": "GOOGL",
        "amazon": "AMZN",
        "meta": "META",
        "facebook": "META",
        "tesla": "TSLA",
        "nvidia": "NVDA",
        "amd": "AMD",
        "intel": "INTC",
        "netflix": "NFLX",

        # Finance
        "jpmorgan": "JPM",
        "jp morgan": "JPM",
        "bank of america": "BAC",
        "goldman sachs": "GS",
        "morgan stanley": "MS",
        "visa": "V",
        "mastercard": "MA",

        # Others
        "walmart": "WMT",
        "coca cola": "KO",
        "pepsi": "PEP",
        "boeing": "BA",
        "disney": "DIS"
    }

    # Indian Stock Mapping (Common names → NSE Symbols)
    INDIAN_STOCKS = {
        # Banks
        "hdfc bank": "HDFCBANK.NS",
        "hdfcbank": "HDFCBANK.NS",
        "hdfc": "HDFCBANK.NS",
        "icici bank": "ICICIBANK.NS",
        "icicibank": "ICICIBANK.NS",
        "icici": "ICICIBANK.NS",
        "sbi": "SBIN.NS",
        "state bank": "SBIN.NS",
        "axis bank": "AXISBANK.NS",
        "axisbank": "AXISBANK.NS",
        "axis": "AXISBANK.NS",
        "kotak bank": "KOTAKBANK.NS",
        "kotakbank": "KOTAKBANK.NS",
        "kotak": "KOTAKBANK.NS",

        # IT
        "tcs": "TCS.NS",
        "infosys": "INFY.NS",
        "wipro": "WIPRO.NS",
        "hcl tech": "HCLTECH.NS",
        "hcltech": "HCLTECH.NS",
        "tech mahindra": "TECHM.NS",

        # Conglomerates
        "reliance": "RELIANCE.NS",
        "reliance industries": "RELIANCE.NS",
        "tata steel": "TATASTEEL.NS",
        "tatasteel": "TATASTEEL.NS",
        "tata motors": "TATAMOTORS.NS",
        "tatamotors": "TATAMOTORS.NS",

        # Adani Group
        "adani": "ADANIENT.NS",
        "adani enterprises": "ADANIENT.NS",
        "adani green": "ADANIGREEN.NS",
        "adani green energy": "ADANIGREEN.NS",
        "adanigreen": "ADANIGREEN.NS",
        "adani ports": "ADANIPORTS.NS",
        "adaniports": "ADANIPORTS.NS",
        "adani power": "ADANIPOWER.NS",
        "adanipower": "ADANIPOWER.NS",
        "adani total gas": "ATGL.NS",
        "adani gas": "ATGL.NS",
        "adani transmission": "ADANITRANS.NS",
        "adanitrans": "ADANITRANS.NS",

        # FMCG
        "hindustan unilever": "HINDUNILVR.NS",
        "hindunilvr": "HINDUNILVR.NS",
        "hul": "HINDUNILVR.NS",
        "itc": "ITC.NS",
        "britannia": "BRITANNIA.NS",

        # Pharma
        "sun pharma": "SUNPHARMA.NS",
        "sunpharma": "SUNPHARMA.NS",
        "dr reddy": "DRREDDY.NS",
        "cipla": "CIPLA.NS",

        # Telecom & Energy
        "bharti airtel": "BHARTIARTL.NS",
        "airtel": "BHARTIARTL.NS",
        "ntpc": "NTPC.NS",
        "power grid": "POWERGRID.NS",
        "powergrid": "POWERGRID.NS",
        "ongc": "ONGC.NS",
        "oil and natural gas": "ONGC.NS",

        # Auto
        "maruti": "MARUTI.NS",
        "maruti suzuki": "MARUTI.NS",
        "mahindra": "M&M.NS",
        "m&m": "M&M.NS",
        "bajaj auto": "BAJAJ-AUTO.NS",
        "bajajauto": "BAJAJ-AUTO.NS",

        # Metals & Mining
        "coal india": "COALINDIA.NS",
        "coalindia": "COALINDIA.NS",
        "hindalco": "HINDALCO.NS",
        "vedanta": "VEDL.NS",

        # Others
        "larsen": "LT.NS",
        "l&t": "LT.NS",
        "larsen and toubro": "LT.NS",
        "ultratech": "ULTRACEMCO.NS",
        "ultratech cement": "ULTRACEMCO.NS",
        "asian paints": "ASIANPAINT.NS",
        "asianpaint": "ASIANPAINT.NS"
    }

    # Market Hours (in local time)
    MARKET_HOURS = {
        "NSE": {
            "timezone": "Asia/Kolkata",
            "open": time(9, 15),   # 9:15 AM IST
            "close": time(15, 30),  # 3:30 PM IST
            "days": [0, 1, 2, 3, 4]  # Monday-Friday
        },
        "NASDAQ": {
            "timezone": "America/New_York",
            "open": time(9, 30),   # 9:30 AM EST
            "close": time(16, 0),   # 4:00 PM EST
            "days": [0, 1, 2, 3, 4]
        },
        "NYSE": {
            "timezone": "America/New_York",
            "open": time(9, 30),
            "close": time(16, 0),
            "days": [0, 1, 2, 3, 4]
        }
    }

    @classmethod
    async def detect_stock_with_ai(cls, query: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        AI-powered stock detection for ANY company worldwide
        Uses Qwen to detect company, country, and symbol
        Automatically adds exchange suffixes (.NS for India, etc.)

        Args:
            query: User query (e.g., "Adani Green Energy prediction", "Tesla analysis")

        Returns:
            Tuple of (symbol, exchange, market_type)
            - "Adani Green Energy" → ("ADANIGREEN.NS", "NSE", "stock")
            - "Tesla" → ("TSLA", "NASDAQ", "stock")
            - "Reliance Industries" → ("RELIANCE.NS", "NSE", "stock")
        """
        try:
            from app.services.qwen_client import qwen_client

            prompt = f"""Extract stock information from this query: "{query}"

Provide:
1. Company name
2. Stock symbol (ticker)
3. Country (India/US/UK/etc.)
4. Exchange (NSE/NASDAQ/NYSE/LSE/etc.)

Response format (JSON):
{{
    "company": "company name",
    "symbol": "SYMBOL",
    "country": "country",
    "exchange": "exchange"
}}

Rules:
- For Indian companies: Provide NSE symbol WITHOUT .NS suffix (we'll add it)
- For US companies: Provide standard ticker (AAPL, TSLA, etc.)
- If not sure, use your knowledge to guess the most likely company

Examples:
Query: "Adani Green Energy"
{{"company": "Adani Green Energy", "symbol": "ADANIGREEN", "country": "India", "exchange": "NSE"}}

Query: "Tesla stock"
{{"company": "Tesla Inc", "symbol": "TSLA", "country": "US", "exchange": "NASDAQ"}}

Query: "Reliance Industries"
{{"company": "Reliance Industries", "symbol": "RELIANCE", "country": "India", "exchange": "NSE"}}

Now extract from: "{query}"
"""

            response = await qwen_client.generate(prompt, max_tokens=200)

            # Parse JSON response
            import json
            # Extract JSON from response
            json_match = re.search(r'\{[^}]+\}', response)
            if json_match:
                data = json.loads(json_match.group())

                symbol = data.get("symbol", "").upper()
                country = data.get("country", "").lower()
                exchange = data.get("exchange", "").upper()

                # Add exchange suffix based on country
                if country == "india" and not symbol.endswith(".NS"):
                    symbol = f"{symbol}.NS"
                    exchange = "NSE"
                elif country in ["us", "usa", "united states"]:
                    # US stocks don't need suffix
                    exchange = exchange or "NASDAQ"

                logger.info(f"AI detected stock: {symbol} on {exchange} ({country})")
                return symbol, exchange, "stock"

        except Exception as e:
            logger.error(f"AI stock detection failed: {e}")

        return None, None, None

    @classmethod
    def detect_and_normalize_symbol(cls, query: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Intelligently detect stock symbol and exchange from query

        Args:
            query: User query (e.g., "hdfc bank prediction", "tesla scalping")

        Returns:
            Tuple of (symbol, exchange, market_type)
            - symbol: Normalized symbol (e.g., "HDFCBANK.NS", "TSLA")
            - exchange: Exchange name (e.g., "NSE", "NASDAQ")
            - market_type: "stock" or None

        Examples:
            "hdfc bank" → ("HDFCBANK.NS", "NSE", "stock")
            "Tesla" → ("TSLA", "NASDAQ", "stock")
            "AAPL" → ("AAPL", "NASDAQ", "stock")
        """
        query_lower = query.lower().strip()

        # Check Indian stocks first (they have .NS suffix)
        for name, symbol in cls.INDIAN_STOCKS.items():
            if name in query_lower:
                logger.info(f"Detected Indian stock: {name} → {symbol}")
                return symbol, "NSE", "stock"

        # Check US stocks
        for name, symbol in cls.US_STOCKS.items():
            if name in query_lower:
                logger.info(f"Detected US stock: {name} → {symbol}")
                return symbol, "NASDAQ", "stock"

        # Check if it's already a proper symbol
        words = query.upper().split()
        for word in words:
            # Indian stock with .NS suffix
            if ".NS" in word:
                logger.info(f"Detected NSE symbol: {word}")
                return word, "NSE", "stock"

            # US stock symbol (2-5 letters, all caps)
            if word.isalpha() and 2 <= len(word) <= 5:
                # Check if it's a known US ticker
                if word in ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN", "META", "NVDA",
                           "AMD", "NFLX", "JPM", "BAC", "V", "MA", "WMT", "DIS"]:
                    logger.info(f"Detected US ticker: {word}")
                    return word, "NASDAQ", "stock"

        return None, None, None

    @classmethod
    def is_market_open(cls, exchange: str) -> Tuple[bool, str]:
        """
        Check if market is currently open

        Args:
            exchange: Exchange name (NSE, NASDAQ, NYSE)

        Returns:
            Tuple of (is_open: bool, message: str)

        Examples:
            ("NSE") → (True, "Market is open") or (False, "NSE market is closed. Trading hours: 9:15 AM - 3:30 PM IST (Mon-Fri)")
        """
        if exchange not in cls.MARKET_HOURS:
            return True, ""  # Unknown exchange, allow trading

        market_info = cls.MARKET_HOURS[exchange]
        tz = pytz.timezone(market_info["timezone"])
        now = datetime.now(tz)

        # Check if today is a trading day (Monday-Friday)
        if now.weekday() not in market_info["days"]:
            day_name = now.strftime("%A")
            return False, f"{exchange} market is closed. It's {day_name}. Trading days: Monday-Friday"

        # Check if within trading hours
        current_time = now.time()
        market_open = market_info["open"]
        market_close = market_info["close"]

        if market_open <= current_time <= market_close:
            return True, f"{exchange} market is OPEN"
        else:
            tz_name = "IST" if exchange == "NSE" else "EST/EDT"
            return False, (
                f"{exchange} market is CLOSED. "
                f"Trading hours: {market_open.strftime('%I:%M %p')} - {market_close.strftime('%I:%M %p')} {tz_name} (Mon-Fri). "
                f"Current time: {current_time.strftime('%I:%M %p')} {tz_name}"
            )

    @classmethod
    def get_market_info(cls, symbol: str, exchange: str) -> Dict:
        """
        Get comprehensive market information

        Args:
            symbol: Stock symbol
            exchange: Exchange name

        Returns:
            Market info dict
        """
        is_open, message = cls.is_market_open(exchange)

        market_info = cls.MARKET_HOURS.get(exchange, {})
        tz = pytz.timezone(market_info.get("timezone", "UTC")) if market_info else pytz.UTC
        current_time = datetime.now(tz)

        return {
            "symbol": symbol,
            "exchange": exchange,
            "is_open": is_open,
            "status_message": message,
            "current_time": current_time.strftime("%Y-%m-%d %I:%M %p"),
            "timezone": market_info.get("timezone", "UTC"),
            "trading_hours": {
                "open": market_info["open"].strftime("%I:%M %p") if market_info else None,
                "close": market_info["close"].strftime("%I:%M %p") if market_info else None,
                "days": "Monday-Friday"
            }
        }


# Singleton instance
stock_intelligence = StockIntelligence()
