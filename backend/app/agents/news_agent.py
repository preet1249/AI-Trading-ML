"""
News Agent
Fetches and analyzes recent news for sentiment
"""
from typing import Dict

# TODO: Import when implemented
# from app.services.news import fetch_news, analyze_sentiment


async def news_node(state: Dict) -> Dict:
    """
    News Agent - Fetch and analyze news sentiment

    Steps:
    1. Fetch recent news (<2 days) via Google Custom Search
    2. Extract headlines and snippets
    3. Use Qwen to analyze sentiment
    4. Return sentiment score and key events

    Args:
        state: Agent state with symbol

    Returns:
        Updated state with news_data
    """
    # TODO: Implement news fetching and analysis
    # symbol = state["symbol"]

    # Fetch news
    # news_articles = await fetch_news(symbol, days=2)

    # Analyze sentiment with Qwen
    # sentiment = await analyze_sentiment(news_articles)

    news_data = {
        "sentiment": 0.0,
        "key_events": [],
        "summary": "No recent news found"
    }

    return {"news_data": news_data}
