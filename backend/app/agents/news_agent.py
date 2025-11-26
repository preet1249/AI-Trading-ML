"""
News Agent - INTELLIGENT SENTIMENT ANALYSIS
Fetches real news and analyzes sentiment with context understanding
"""
import logging
from typing import Dict, List
from datetime import datetime, timedelta

from app.services.news import NewsService
from app.services.qwen_client import qwen_client

logger = logging.getLogger(__name__)


async def news_node(state: Dict) -> Dict:
    """
    News Agent - Intelligent news fetching and sentiment analysis

    Fetches recent news articles and analyzes:
    - Overall market sentiment (bullish/bearish/neutral)
    - Key events and catalysts
    - Risk factors and opportunities
    - Context-aware sentiment weighting

    Args:
        state: {
            "query": user query,
            "symbol": trading symbol,
            "analysis_type": "long_term" | "short_term" | "scalping"
        }

    Returns:
        Updated state with news_data
    """
    try:
        symbol = state.get("symbol")
        analysis_type = state.get("analysis_type", "short_term")

        logger.info(f"News Agent analyzing sentiment for {symbol}")

        # Fetch recent news
        news_articles = await NewsService.fetch_news(symbol, max_results=10)

        if not news_articles:
            logger.warning(f"No news articles found for {symbol}")
            return {
                "news_data": {
                    "symbol": symbol,
                    "articles_count": 0,
                    "sentiment": "neutral",
                    "sentiment_score": 0,
                    "key_events": [],
                    "risk_factors": [],
                    "opportunities": [],
                    "qwen_analysis": "No recent news available for analysis"
                }
            }

        # Analyze sentiment with Qwen
        sentiment_analysis = await analyze_news_with_qwen(
            symbol=symbol,
            articles=news_articles,
            analysis_type=analysis_type
        )

        # Calculate overall sentiment score
        sentiment_score = calculate_sentiment_score(news_articles)

        # Classify sentiment
        sentiment = classify_sentiment(sentiment_score)

        # Extract key information
        key_events = extract_key_events(news_articles)
        risk_factors = extract_risk_factors(sentiment_analysis)
        opportunities = extract_opportunities(sentiment_analysis)

        # Compile news data
        news_data = {
            "symbol": symbol,
            "articles_count": len(news_articles),
            "recent_articles": news_articles[:5],  # Top 5 most recent
            "sentiment": sentiment,
            "sentiment_score": sentiment_score,
            "key_events": key_events,
            "risk_factors": risk_factors,
            "opportunities": opportunities,
            "qwen_analysis": sentiment_analysis,
            "news_impact": assess_news_impact(sentiment_score, len(news_articles))
        }

        logger.info(f"News Agent completed: {sentiment} sentiment ({sentiment_score:.2f})")

        return {"news_data": news_data}

    except Exception as e:
        logger.error(f"News Agent error: {str(e)}")
        return {
            "news_data": {
                "error": str(e),
                "sentiment": "neutral",
                "sentiment_score": 0
            }
        }


def calculate_sentiment_score(articles: List[Dict]) -> float:
    """
    Calculate overall sentiment score from articles

    Returns score between -1.0 (bearish) and +1.0 (bullish)
    """
    try:
        if not articles:
            return 0.0

        bullish_keywords = [
            "rally", "surge", "bullish", "gains", "rise", "pump", "moon",
            "breakthrough", "adoption", "upgrade", "positive", "growth",
            "record high", "all-time high", "ath", "breakout", "uptrend"
        ]

        bearish_keywords = [
            "crash", "dump", "bearish", "decline", "fall", "drop", "plunge",
            "fear", "panic", "sell-off", "collapse", "hack", "scam", "regulation",
            "ban", "lawsuit", "investigation", "negative", "downturn"
        ]

        total_score = 0.0
        articles_with_sentiment = 0

        for article in articles:
            title = article.get("title", "").lower()
            snippet = article.get("snippet", "").lower()
            text = f"{title} {snippet}"

            # Count keyword occurrences
            bullish_count = sum(text.count(kw) for kw in bullish_keywords)
            bearish_count = sum(text.count(kw) for kw in bearish_keywords)

            if bullish_count > 0 or bearish_count > 0:
                # Calculate article score
                article_score = (bullish_count - bearish_count) / (bullish_count + bearish_count + 1)
                total_score += article_score
                articles_with_sentiment += 1

        # Average sentiment score
        if articles_with_sentiment > 0:
            avg_score = total_score / articles_with_sentiment
            # Normalize to [-1, 1] range
            return max(-1.0, min(1.0, avg_score))

        return 0.0

    except Exception as e:
        logger.error(f"Sentiment score calculation error: {e}")
        return 0.0


def classify_sentiment(score: float) -> str:
    """Classify sentiment based on score"""
    if score > 0.3:
        return "bullish"
    elif score < -0.3:
        return "bearish"
    else:
        return "neutral"


def extract_key_events(articles: List[Dict]) -> List[str]:
    """Extract key events from news articles"""
    try:
        key_events = []

        event_keywords = {
            "regulation": ["regulation", "sec", "lawsuit", "ban", "legal"],
            "adoption": ["adoption", "partnership", "integration", "launch"],
            "technical": ["upgrade", "hardfork", "update", "release"],
            "market": ["etf", "listing", "delisting", "halted"],
            "security": ["hack", "breach", "exploit", "vulnerability"]
        }

        for article in articles[:5]:  # Check top 5 articles
            title = article.get("title", "").lower()
            snippet = article.get("snippet", "").lower()
            text = f"{title} {snippet}"

            for event_type, keywords in event_keywords.items():
                for keyword in keywords:
                    if keyword in text:
                        event_desc = f"{event_type.capitalize()}: {article.get('title', '')[:80]}"
                        if event_desc not in key_events:
                            key_events.append(event_desc)
                        break

        return key_events[:5]  # Return top 5 events

    except Exception as e:
        logger.error(f"Key events extraction error: {e}")
        return []


def extract_risk_factors(analysis: str) -> List[str]:
    """Extract risk factors from Qwen analysis"""
    try:
        risks = []
        analysis_lower = analysis.lower()

        risk_indicators = [
            "risk", "concern", "warning", "threat", "danger",
            "regulatory", "volatile", "uncertain", "negative"
        ]

        # Simple extraction - look for sentences with risk keywords
        sentences = analysis.split(".")
        for sentence in sentences:
            if any(indicator in sentence.lower() for indicator in risk_indicators):
                risks.append(sentence.strip())

        return risks[:3]  # Top 3 risks

    except Exception as e:
        logger.error(f"Risk extraction error: {e}")
        return []


def extract_opportunities(analysis: str) -> List[str]:
    """Extract opportunities from Qwen analysis"""
    try:
        opportunities = []
        analysis_lower = analysis.lower()

        opportunity_indicators = [
            "opportunity", "potential", "upside", "catalyst", "growth",
            "positive", "bullish", "favorable", "support"
        ]

        # Simple extraction - look for sentences with opportunity keywords
        sentences = analysis.split(".")
        for sentence in sentences:
            if any(indicator in sentence.lower() for indicator in opportunity_indicators):
                opportunities.append(sentence.strip())

        return opportunities[:3]  # Top 3 opportunities

    except Exception as e:
        logger.error(f"Opportunity extraction error: {e}")
        return []


def assess_news_impact(sentiment_score: float, articles_count: int) -> str:
    """Assess overall news impact on market"""
    try:
        abs_score = abs(sentiment_score)

        if articles_count >= 8 and abs_score > 0.5:
            return "high"
        elif articles_count >= 5 and abs_score > 0.3:
            return "medium"
        elif articles_count >= 3:
            return "low"
        else:
            return "minimal"

    except:
        return "unknown"


async def analyze_news_with_qwen(symbol: str, articles: List[Dict], analysis_type: str) -> str:
    """Use Qwen to analyze news sentiment and context"""
    try:
        # Prepare news context
        context = f"Recent news articles for {symbol} ({analysis_type} analysis):\n\n"

        for i, article in enumerate(articles[:8], 1):  # Analyze top 8 articles
            title = article.get("title", "")
            snippet = article.get("snippet", "")
            source = article.get("source", "Unknown")
            published = article.get("published_date", "")

            context += f"{i}. **{title}**\n"
            context += f"   Source: {source} | Date: {published}\n"
            context += f"   {snippet}\n\n"

        system_prompt = f"""You are an expert financial news analyst. Analyze the news articles and provide:

1. **Overall Sentiment**: Bullish/Bearish/Neutral with confidence level
2. **Key Catalysts**: Major events driving price action
3. **Risk Factors**: Potential threats or concerns
4. **Opportunities**: Positive developments or catalysts
5. **Market Impact**: Expected short-term and long-term impact

Focus on {analysis_type} perspective. Be concise (4-5 sentences). Provide actionable insights."""

        analysis = await qwen_client.generate(context, system_prompt, temperature=0.4)

        return analysis

    except Exception as e:
        logger.error(f"Qwen news analysis error: {e}")
        return "Unable to generate news analysis"
