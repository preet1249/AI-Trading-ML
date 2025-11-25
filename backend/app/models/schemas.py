"""
Pydantic Schemas for Data Validation
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


# ============================================
# User Schemas
# ============================================

class User(BaseModel):
    """User model"""
    id: str
    email: str
    created_at: str


# ============================================
# Market Data Schemas
# ============================================

class Candle(BaseModel):
    """OHLCV candle data"""
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float


class MarketData(BaseModel):
    """Market data with candles"""
    symbol: str
    timeframe: str
    candles: List[Candle]


# ============================================
# Technical Analysis Schemas
# ============================================

class Swing(BaseModel):
    """Swing high/low point"""
    type: Literal["high", "low"]
    price: float
    timestamp: int


class OrderBlock(BaseModel):
    """Order block (demand/supply)"""
    type: Literal["demand", "supply"]
    price: float
    timestamp: int


class Zone(BaseModel):
    """Support/Resistance or S/D zone"""
    type: Literal["support", "resistance", "demand", "supply"]
    high: float
    low: float


class MACD(BaseModel):
    """MACD indicator values"""
    line: float
    signal: float
    histogram: float


class TechnicalAnalysis(BaseModel):
    """Complete technical analysis data"""
    rsi: float
    macd: MACD
    ema20: float
    swings: List[Swing]
    choch: Optional[str] = None
    bos: Optional[str] = None
    liquidity: List[float]
    order_blocks: List[OrderBlock]
    zones: List[Zone]
    trend: Literal["bullish", "bearish", "sideways"]


# ============================================
# News Schemas
# ============================================

class NewsData(BaseModel):
    """News sentiment data"""
    sentiment: float = Field(..., ge=-1, le=1, description="Sentiment score from -1 to 1")
    key_events: List[str]
    summary: str


# ============================================
# Prediction Schemas
# ============================================

class PredictionResponse(BaseModel):
    """Prediction result"""
    id: str
    symbol: str
    direction: Literal["UP", "DOWN", "SIDEWAYS"]
    target: Optional[float] = None
    confidence: float = Field(..., ge=0, le=100, description="Confidence score 0-100")
    reasoning: str
    ta_data: TechnicalAnalysis
    news_data: NewsData
    created_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "id": "pred_123",
                "symbol": "BTCUSDT",
                "direction": "UP",
                "target": 70000,
                "confidence": 85,
                "reasoning": "Bullish BOS confirmed, demand OB at support",
                "created_at": "2024-01-01T00:00:00Z"
            }
        }


# ============================================
# Agent State Schemas
# ============================================

class AgentState(BaseModel):
    """LangGraph agent state"""
    query: str
    symbol: str
    timeframe: str = "1h"
    user_id: str
    ta_data: Optional[TechnicalAnalysis] = None
    news_data: Optional[NewsData] = None
    prediction: Optional[str] = None
