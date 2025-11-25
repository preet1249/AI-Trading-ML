"""
News Service
Fetch and analyze news using Google Custom Search API
"""
import requests
from typing import List, Dict
from datetime import datetime, timedelta

from app.config import settings


async def fetch_news(symbol: str, days: int = 2) -> List[Dict]:
    """
    Fetch recent news for a symbol

    Args:
        symbol: Trading symbol
        days: Number of days to look back

    Returns:
        List of news articles
    """
    # TODO: Implement Google Custom Search API

    # Calculate date filter
    date_from = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    # Build search query
    query = f"{symbol} stock news after:{date_from}"

    # API request
    # url = "https://www.googleapis.com/customsearch/v1"
    # params = {
    #     "key": settings.GOOGLE_CUSTOM_SEARCH_API_KEY,
    #     "cx": settings.GOOGLE_SEARCH_ENGINE_ID,
    #     "q": query,
    #     "num": 10
    # }

    # response = requests.get(url, params=params)
    # data = response.json()

    # Parse results
    articles = []
    # for item in data.get("items", []):
    #     articles.append({
    #         "title": item.get("title"),
    #         "snippet": item.get("snippet"),
    #         "link": item.get("link"),
    #         "date": item.get("pagemap", {}).get("metatags", [{}])[0].get("article:published_time")
    #     })

    return articles


async def analyze_sentiment(articles: List[Dict]) -> Dict:
    """
    Analyze sentiment of news articles using Qwen

    Args:
        articles: List of news articles

    Returns:
        Sentiment analysis result
    """
    # TODO: Implement Qwen-based sentiment analysis

    # Combine headlines and snippets
    text = "\n".join([
        f"{article['title']}: {article['snippet']}"
        for article in articles
    ])

    # Use Qwen to analyze sentiment
    # sentiment_score = await qwen_sentiment_analysis(text)

    return {
        "sentiment": 0.0,  # -1 to 1
        "key_events": [],
        "summary": "No significant news"
    }
