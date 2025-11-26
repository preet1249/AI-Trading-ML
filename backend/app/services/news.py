"""
News Service - REAL DATA
Fetch and analyze news using Google Custom Search API
NO MOCK DATA - Production-ready
"""
import aiohttp
from typing import List, Dict
from datetime import datetime, timedelta
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class NewsService:
    """Real Google Custom Search API integration for news"""

    GOOGLE_SEARCH_URL = "https://www.googleapis.com/customsearch/v1"

    @classmethod
    async def fetch_news(
        cls,
        symbol: str,
        days: int = 1,
        max_results: int = 10
    ) -> List[Dict]:
        """
        Fetch real recent news for a symbol using Google Custom Search

        Args:
            symbol: Trading symbol (e.g., BTC, AAPL, TSLA)
            days: Number of days to look back (default 1 - last 24 hours only)
            max_results: Maximum number of results (default 10)

        Returns:
            List of news articles with title, snippet, link, date
        """
        try:
            if not settings.GOOGLE_CUSTOM_SEARCH_API_KEY:
                logger.warning("Google Custom Search API key not configured")
                return []

            if not settings.GOOGLE_SEARCH_ENGINE_ID:
                logger.warning("Google Search Engine ID not configured")
                return []

            # Clean symbol for search query
            clean_symbol = symbol.replace("USDT", "").replace("USD", "")

            # Calculate date filter (e.g., "after:2024-01-01")
            date_from = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

            # Build search query
            # Example: "BTC Bitcoin news after:2024-01-15"
            query = f"{clean_symbol} stock news after:{date_from}"

            logger.info(f"Fetching news for {symbol} (query: {query})")

            # API parameters
            params = {
                "key": settings.GOOGLE_CUSTOM_SEARCH_API_KEY,
                "cx": settings.GOOGLE_SEARCH_ENGINE_ID,
                "q": query,
                "num": min(max_results, 10),  # Google max is 10 per request
                "sort": "date"  # Sort by date
            }

            # Make API request
            async with aiohttp.ClientSession() as session:
                async with session.get(cls.GOOGLE_SEARCH_URL, params=params) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Google Search API error: {response.status} - {error_text}")
                        return []

                    data = await response.json()

            # Parse results
            articles = []
            for item in data.get("items", []):
                # Extract date from metadata if available
                article_date = None
                metatags = item.get("pagemap", {}).get("metatags", [{}])
                if metatags:
                    article_date = metatags[0].get("article:published_time")

                articles.append({
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", ""),
                    "link": item.get("link", ""),
                    "date": article_date,
                    "source": item.get("displayLink", "")
                })

            logger.info(f"Successfully fetched {len(articles)} news articles for {symbol}")
            return articles

        except Exception as e:
            logger.error(f"Error fetching news: {str(e)}")
            return []  # Return empty list on error (don't fail prediction)

    @classmethod
    def extract_sentiment_keywords(cls, articles: List[Dict]) -> Dict[str, int]:
        """
        Extract sentiment keywords from articles (basic implementation)

        Args:
            articles: List of news articles

        Returns:
            Dictionary with keyword counts
        """
        positive_keywords = [
            "surge", "rally", "gain", "profit", "growth", "bullish",
            "breakthrough", "soar", "rise", "up", "high", "record"
        ]

        negative_keywords = [
            "crash", "drop", "fall", "loss", "decline", "bearish",
            "plunge", "down", "low", "fear", "sell-off", "warning"
        ]

        positive_count = 0
        negative_count = 0

        for article in articles:
            text = (article.get("title", "") + " " + article.get("snippet", "")).lower()

            for keyword in positive_keywords:
                positive_count += text.count(keyword)

            for keyword in negative_keywords:
                negative_count += text.count(keyword)

        return {
            "positive": positive_count,
            "negative": negative_count,
            "total": positive_count + negative_count
        }


# Singleton instance
news_service = NewsService()
