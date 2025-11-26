"""
Prediction API Endpoint
Handles user queries and returns AI-powered trading predictions
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional
import logging

from app.agents.graph import prediction_workflow
from app.middleware.auth import get_current_user
from app.middleware.rate_limit import rate_limit

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/predict", tags=["Predictions"])


class PredictionRequest(BaseModel):
    """Prediction request model"""
    query: str = Field(..., min_length=3, max_length=500, description="User query (e.g., 'predict BTC next move')")
    symbol: Optional[str] = Field(None, description="Trading symbol (optional, will be extracted from query)")


class PredictionResponse(BaseModel):
    """Prediction response model"""
    success: bool
    query: str
    symbol: str
    analysis_type: str
    timeframes: list
    prediction: dict
    ta_data: Optional[dict] = None
    news_data: Optional[dict] = None
    error: Optional[str] = None


@router.post("/", response_model=PredictionResponse, dependencies=[Depends(rate_limit)])
async def generate_prediction(
    request: PredictionRequest,
    user_id: str = Depends(get_current_user)
):
    """
    Generate AI Trading Prediction

    This endpoint runs the complete multi-agent workflow:
    1. Parse Query - Extract symbol, determine timeframes
    2. TA Agent - Multi-timeframe technical analysis
    3. News Agent - Sentiment analysis (conditional)
    4. Prediction Agent - Synthesize and generate prediction

    **Examples:**
    - "long term prediction for BTC" ’ Analyzes daily + 4h timeframes
    - "day trading AAPL today" ’ Analyzes 4h + 1h + 15m
    - "next move in ETHUSDT" ’ Analyzes 1h + 15m + 5m (scalping)
    - "should I buy Bitcoin?" ’ Short-term analysis

    **Rate Limits:**
    - 10 requests per minute
    - 100 requests per day

    Args:
        request: Prediction request with query and optional symbol
        user_id: Authenticated user ID (from JWT token)

    Returns:
        PredictionResponse with complete analysis and prediction

    Raises:
        HTTPException: If prediction fails or rate limit exceeded
    """
    try:
        logger.info(f"Prediction request from user {user_id}: {request.query}")

        # Prepare initial state
        initial_state = {
            "query": request.query,
            "symbol": request.symbol or "",
            "user_id": user_id,
            "timeframes": [],
            "analysis_type": "",
            "ta_data": {},
            "news_data": {},
            "prediction": {}
        }

        # Run LangGraph workflow
        logger.info("Starting LangGraph prediction workflow...")
        final_state = await prediction_workflow.ainvoke(initial_state)

        logger.info(
            f"Prediction completed: {final_state.get('symbol')} - "
            f"{final_state.get('prediction', {}).get('direction', 'UNKNOWN')}"
        )

        # Build response
        response = PredictionResponse(
            success=True,
            query=request.query,
            symbol=final_state.get("symbol", "UNKNOWN"),
            analysis_type=final_state.get("analysis_type", "short_term"),
            timeframes=final_state.get("timeframes", []),
            prediction=final_state.get("prediction", {}),
            ta_data=final_state.get("ta_data"),
            news_data=final_state.get("news_data")
        )

        return response

    except Exception as e:
        logger.error(f"Prediction error: {str(e)}", exc_info=True)

        return PredictionResponse(
            success=False,
            query=request.query,
            symbol=request.symbol or "UNKNOWN",
            analysis_type="unknown",
            timeframes=[],
            prediction={
                "direction": "NEUTRAL",
                "confidence": 0,
                "reasoning": "Error generating prediction"
            },
            error=str(e)
        )


@router.get("/health")
async def health_check():
    """
    Health check endpoint

    Returns:
        Status of the prediction service
    """
    return {
        "status": "healthy",
        "service": "prediction",
        "agents": ["ta", "news", "predict"],
        "workflow": "langgraph"
    }
