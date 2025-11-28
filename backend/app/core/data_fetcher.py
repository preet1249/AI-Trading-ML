"""
Unified Data Fetcher - REAL DATA
Automatically routes to Binance (crypto) or Twelve Data (stocks)
NO MOCK DATA - Production-ready
"""
from typing import List, Dict
import logging

from app.services.binance import binance_service
from app.services.twelve_data import twelve_data_service

logger = logging.getLogger(__name__)


async def fetch_candles(
    symbol: str,
    timeframe: str = "1h",
    limit: int = 200
) -> List[Dict]:
    """
    Fetch real candle data for any symbol (crypto or stock)

    Automatically detects:
    - Crypto symbols (BTCUSDT, ETHUSDT, etc.) → Binance
    - Stock symbols (AAPL, TSLA, RELIANCE.NS, etc.) → Twelve Data

    Args:
        symbol: Trading symbol (e.g., BTCUSDT, AAPL, RELIANCE.NS)
        timeframe: Candle timeframe (1m, 5m, 15m, 1h, 4h, 1d)
        limit: Number of candles to fetch

    Returns:
        List of candle data with OHLCV format
    """
    try:
        # Normalize symbol format for Binance (fix BTC-USD → BTCUSDT)
        symbol = _normalize_symbol(symbol)

        # Detect if crypto or stock
        is_crypto = _is_crypto_symbol(symbol)

        if is_crypto:
            logger.info(f"Fetching crypto data for {symbol} from Binance")
            candles = await binance_service.fetch_klines(
                symbol=symbol,
                interval=timeframe,
                limit=limit
            )
        else:
            logger.info(f"Fetching stock data for {symbol} from Twelve Data")
            candles = await twelve_data_service.fetch_time_series(
                symbol=symbol,
                interval=timeframe,
                outputsize=limit
            )

        if not candles:
            raise Exception(f"No data returned for {symbol}")

        logger.info(f"Successfully fetched {len(candles)} candles for {symbol}")
        return candles

    except Exception as e:
        logger.error(f"Error fetching candles for {symbol}: {str(e)}")
        raise


async def get_current_price(symbol: str) -> float:
    """
    Get current price for any symbol

    Args:
        symbol: Trading symbol

    Returns:
        Current price
    """
    try:
        # Normalize symbol
        symbol = _normalize_symbol(symbol)
        is_crypto = _is_crypto_symbol(symbol)

        if is_crypto:
            return await binance_service.get_current_price(symbol)
        else:
            quote = await twelve_data_service.get_quote(symbol)
            return quote["price"]

    except Exception as e:
        logger.error(f"Error fetching current price for {symbol}: {str(e)}")
        raise


def _normalize_symbol(symbol: str) -> str:
    """
    Normalize symbol to correct format for exchanges

    Converts common formats to Binance format:
    - BTC-USD → BTCUSDT
    - BTC/USD → BTCUSDT
    - ETH-USDT → ETHUSDT
    - AAPL → AAPL (stocks unchanged)

    Args:
        symbol: Trading symbol in any format

    Returns:
        Normalized symbol
    """
    # Remove hyphens, slashes, spaces
    symbol = symbol.replace("-", "").replace("/", "").replace(" ", "").upper()

    # Convert USD to USDT for crypto (if not already USDT)
    if symbol.endswith("USD") and not symbol.endswith("USDT"):
        symbol = symbol[:-3] + "USDT"

    return symbol


def _is_crypto_symbol(symbol: str) -> bool:
    """
    Detect if symbol is crypto or stock

    Crypto symbols typically:
    - End with USDT, BUSD, BTC, ETH, BNB
    - Are all uppercase with no dots

    Stock symbols:
    - May contain dots (e.g., RELIANCE.NS, BRK.A)
    - May be mixed case

    Args:
        symbol: Trading symbol

    Returns:
        True if crypto, False if stock
    """
    symbol_upper = symbol.upper()

    # Check for crypto suffixes
    crypto_suffixes = ["USDT", "BUSD", "BTC", "ETH", "BNB", "USDC", "DAI"]
    for suffix in crypto_suffixes:
        if symbol_upper.endswith(suffix):
            return True

    # Check for stock exchange suffixes (contains dot)
    if "." in symbol:
        return False

    # If symbol is short (3-5 chars) and no dots, likely stock
    if 2 <= len(symbol) <= 5 and "." not in symbol:
        return False

    # Default: if longer than 5 chars, likely crypto pair
    return len(symbol) > 5


async def get_market_info(symbol: str) -> Dict:
    """
    Get market information for a symbol

    Args:
        symbol: Trading symbol

    Returns:
        Market info (current price, 24h stats, etc.)
    """
    try:
        is_crypto = _is_crypto_symbol(symbol)

        if is_crypto:
            current_price = await binance_service.get_current_price(symbol)
            stats_24h = await binance_service.get_24h_stats(symbol)

            return {
                "symbol": symbol,
                "current_price": current_price,
                "price_change_24h": stats_24h["price_change"],
                "price_change_percent_24h": stats_24h["price_change_percent"],
                "high_24h": stats_24h["high"],
                "low_24h": stats_24h["low"],
                "volume_24h": stats_24h["volume"],
                "market_type": "crypto",
                "exchange": "Binance"
            }
        else:
            quote = await twelve_data_service.get_quote(symbol)

            return {
                "symbol": quote["symbol"],
                "current_price": quote["price"],
                "price_change": quote["change"],
                "price_change_percent": quote["percent_change"],
                "volume": quote["volume"],
                "market_type": "stock",
                "exchange": "TwelveData"
            }

    except Exception as e:
        logger.error(f"Error fetching market info for {symbol}: {str(e)}")
        raise
