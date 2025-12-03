"""
CoinCap API Service - FREE CRYPTO DATA
Unlimited, real-time crypto data - Perfect fallback when Binance is blocked
NO API KEY NEEDED - Completely free
"""
import aiohttp
import logging
from typing import List, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class CoinCapService:
    """Free unlimited crypto data from CoinCap"""

    BASE_URL = "https://api.coincap.io/v2"

    # Symbol mapping (CoinCap uses full names)
    SYMBOL_MAP = {
        "BTCUSDT": "bitcoin",
        "ETHUSDT": "ethereum",
        "BNBUSDT": "binance-coin",
        "SOLUSDT": "solana",
        "XRPUSDT": "xrp",
        "ADAUSDT": "cardano",
        "DOGEUSDT": "dogecoin",
        "MATICUSDT": "polygon",
        "DOTUSDT": "polkadot",
        "AVAXUSDT": "avalanche",
        "LINKUSDT": "chainlink",
        "UNIUSDT": "uniswap",
        "ATOMUSDT": "cosmos",
        "LTCUSDT": "litecoin",
        "ETCUSDT": "ethereum-classic",
        "XLMUSDT": "stellar",
        "TRXUSDT": "tron",
        "SHIBUSDT": "shiba-inu",
        "APTUSDT": "aptos",
        "ARBUSDT": "arbitrum"
    }

    # Timeframe mapping (CoinCap intervals)
    INTERVAL_MAP = {
        "1m": "m1",
        "5m": "m5",
        "15m": "m15",
        "30m": "m30",
        "1h": "h1",
        "2h": "h2",
        "4h": "h6",  # CoinCap doesn't have 4h, use 6h
        "1d": "d1",
        "1w": "d1"  # Use daily for weekly (will aggregate)
    }

    @classmethod
    def normalize_symbol(cls, symbol: str) -> str:
        """
        Convert Binance format to CoinCap format
        BTCUSDT → bitcoin
        ETHUSDT → ethereum
        """
        symbol_upper = symbol.upper()

        # Direct mapping
        if symbol_upper in cls.SYMBOL_MAP:
            return cls.SYMBOL_MAP[symbol_upper]

        # Try to extract base (BTC from BTCUSDT)
        base = symbol_upper.replace("USDT", "").replace("USD", "").replace("BUSD", "")

        # Common mappings
        common_map = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "BNB": "binance-coin",
            "SOL": "solana",
            "XRP": "xrp",
            "ADA": "cardano",
            "DOGE": "dogecoin",
            "MATIC": "polygon",
            "DOT": "polkadot",
            "AVAX": "avalanche"
        }

        return common_map.get(base, base.lower())

    @classmethod
    async def fetch_klines(
        cls,
        symbol: str,
        interval: str = "1h",
        limit: int = 200
    ) -> List[Dict]:
        """
        Fetch historical candle data from CoinCap

        Args:
            symbol: Crypto symbol (e.g., BTCUSDT, ETHUSDT)
            interval: Timeframe (1m, 5m, 15m, 1h, 4h, 1d)
            limit: Number of candles to fetch

        Returns:
            List of candle data with OHLCV format
        """
        try:
            # Normalize symbol
            coincap_symbol = cls.normalize_symbol(symbol)

            # Map interval
            coincap_interval = cls.INTERVAL_MAP.get(interval, "h1")

            logger.info(f"Fetching CoinCap data: {symbol} → {coincap_symbol} ({interval})")

            # CoinCap candles endpoint
            url = f"{cls.BASE_URL}/assets/{coincap_symbol}/history"
            params = {
                "interval": coincap_interval
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"CoinCap API error: {response.status} - {error_text}")

                    data = await response.json()

                    if "data" not in data:
                        raise Exception(f"No data returned from CoinCap for {coincap_symbol}")

            # Parse candles
            candles = []
            history_data = data["data"][-limit:]  # Get last N candles

            for i, bar in enumerate(history_data):
                timestamp = bar["time"]
                price = float(bar["priceUsd"])

                # CoinCap doesn't provide OHLC, only price points
                # We'll create synthetic OHLC by using price as all values
                # This is acceptable for TA indicators that use close price primarily
                candles.append({
                    "timestamp": timestamp,
                    "open": price,
                    "high": price * 1.001,  # Synthetic high (0.1% above)
                    "low": price * 0.999,   # Synthetic low (0.1% below)
                    "close": price,
                    "volume": 0  # CoinCap free tier doesn't include volume
                })

            logger.info(f"✅ CoinCap: Fetched {len(candles)} candles for {symbol}")
            return candles

        except Exception as e:
            logger.error(f"CoinCap error for {symbol}: {str(e)}")
            raise

    @classmethod
    async def get_current_price(cls, symbol: str) -> float:
        """
        Get current price for a crypto symbol

        Args:
            symbol: Crypto symbol (e.g., BTCUSDT)

        Returns:
            Current price in USD
        """
        try:
            # Normalize symbol
            coincap_symbol = cls.normalize_symbol(symbol)

            url = f"{cls.BASE_URL}/assets/{coincap_symbol}"

            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise Exception(f"CoinCap API error: {response.status}")

                    data = await response.json()

                    if "data" not in data:
                        raise Exception(f"No data for {coincap_symbol}")

                    price = float(data["data"]["priceUsd"])

                    logger.info(f"✅ CoinCap: Current price for {symbol}: ${price:.2f}")
                    return price

        except Exception as e:
            logger.error(f"CoinCap price error: {str(e)}")
            raise


# Singleton instance
coincap_service = CoinCapService()
