"""
Yahoo Finance Service - FREE FALLBACK
Provides free stock data for Indian and global markets
Used as fallback when TwelveData quota exceeded or paid plan required
"""
import yfinance as yf
import logging
from typing import List, Dict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class YahooFinanceService:
    """Free Yahoo Finance data for stocks (especially Indian markets)"""

    # Timeframe mapping
    TIMEFRAME_MAP = {
        "1m": "1m",
        "5m": "5m",
        "15m": "15m",
        "30m": "30m",
        "1h": "1h",
        "4h": "4h",  # Yahoo doesn't have 4h, will use 1d
        "1d": "1d",
        "1w": "1wk"
    }

    @classmethod
    async def fetch_candles(
        cls,
        symbol: str,
        timeframe: str = "1h",
        limit: int = 200
    ) -> List[Dict]:
        """
        Fetch historical candle data from Yahoo Finance

        Args:
            symbol: Stock symbol (e.g., RELIANCE.NS, AAPL)
            timeframe: Candle timeframe (1m, 5m, 15m, 1h, 1d)
            limit: Number of candles to fetch

        Returns:
            List of candle data with OHLCV format
        """
        try:
            # Map timeframe
            yf_interval = cls.TIMEFRAME_MAP.get(timeframe, "1h")

            # Calculate period based on timeframe and limit
            period = cls._calculate_period(timeframe, limit)

            logger.info(f"Fetching Yahoo Finance data: {symbol} {timeframe} (period: {period})")

            # Fetch data from Yahoo Finance
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=yf_interval)

            if df.empty:
                raise Exception(f"No data returned from Yahoo Finance for {symbol}")

            # Convert to our candle format
            candles = []
            for index, row in df.iterrows():
                # Convert timestamp to milliseconds
                timestamp = int(index.timestamp() * 1000)

                candles.append({
                    "timestamp": timestamp,
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": float(row["Volume"])
                })

            # Limit to requested number of candles
            candles = candles[-limit:]

            logger.info(f"✅ Yahoo Finance: Fetched {len(candles)} candles for {symbol}")
            return candles

        except Exception as e:
            logger.error(f"Yahoo Finance error for {symbol}: {str(e)}")
            raise

    @classmethod
    async def get_current_price(cls, symbol: str) -> float:
        """
        Get current price for a symbol

        Args:
            symbol: Stock symbol

        Returns:
            Current price
        """
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1d", interval="1m")

            if data.empty:
                raise Exception(f"No price data for {symbol}")

            # Get latest close price
            current_price = float(data["Close"].iloc[-1])

            logger.info(f"✅ Yahoo Finance: Current price for {symbol}: ${current_price:.2f}")
            return current_price

        except Exception as e:
            logger.error(f"Yahoo Finance price error: {str(e)}")
            raise

    @staticmethod
    def _calculate_period(timeframe: str, limit: int) -> str:
        """
        Calculate Yahoo Finance period parameter based on timeframe and limit

        Yahoo Finance periods: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max

        Args:
            timeframe: Candle timeframe
            limit: Number of candles needed

        Returns:
            Period string for Yahoo Finance
        """
        # Calculate approximate days needed
        if timeframe == "1m":
            # 1m data only available for last 7 days
            return "7d"
        elif timeframe == "5m":
            # 5m data available for 60 days
            return "60d" if limit > 100 else "1mo"
        elif timeframe == "15m":
            return "60d" if limit > 100 else "1mo"
        elif timeframe == "1h":
            # 1h data available for 730 days
            days = (limit * 1) / 24  # hours to days
            if days <= 5:
                return "5d"
            elif days <= 30:
                return "1mo"
            elif days <= 90:
                return "3mo"
            else:
                return "6mo"
        elif timeframe == "1d":
            if limit <= 30:
                return "1mo"
            elif limit <= 90:
                return "3mo"
            elif limit <= 180:
                return "6mo"
            elif limit <= 365:
                return "1y"
            else:
                return "2y"
        elif timeframe == "1w":
            if limit <= 52:
                return "1y"
            elif limit <= 104:
                return "2y"
            else:
                return "5y"
        else:
            return "1mo"


# Singleton instance
yahoo_finance_service = YahooFinanceService()
