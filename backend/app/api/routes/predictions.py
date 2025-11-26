"""
Predictions API Routes - LANGGRAPH INTEGRATION
Handles prediction creation with intelligent multi-agent workflow
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel, Field
import logging

from app.api.middleware.auth import get_current_user
from app.agents.graph import prediction_workflow
from app.models.schemas import User

logger = logging.getLogger(__name__)

router = APIRouter()


class PredictionRequest(BaseModel):
    """Prediction request model"""
    query: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Natural language query (e.g., 'predict BTC next move', 'long term analysis for AAPL')"
    )
    symbol: Optional[str] = Field(
        None,
        description="Trading symbol (optional, will be extracted from query if not provided)"
    )


class PredictionResponse(BaseModel):
    """Prediction response model"""
    success: bool
    query: str
    symbol: str
    analysis_type: str
    timeframes: List[str]
    prediction: dict
    ta_summary: Optional[str] = None
    news_impact: Optional[str] = None
    confidence: Optional[int] = None
    risk_level: Optional[str] = None
    error: Optional[str] = None


@router.post("/predictions", response_model=PredictionResponse)
async def create_prediction(
    request: PredictionRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Create AI Trading Prediction using Multi-Agent Workflow

    **Intelligent Query Understanding:**
    - Automatically extracts trading symbol from natural language
    - Determines analysis type (long_term, short_term, scalping)
    - Selects appropriate timeframes based on query context

    **Multi-Agent Workflow:**
    1. **Parse Query** - Extract intent, symbol, and timeframes
    2. **TA Agent** - Multi-timeframe technical analysis with ICT/SMC
    3. **News Agent** - Sentiment analysis (conditional - skipped for scalping)
    4. **Prediction Agent** - Synthesize data and generate actionable prediction

    **Example Queries:**
    - "long term prediction for BTC" → Daily + 4H analysis
    - "day trading AAPL today" → 4H + 1H + 15M analysis
    - "next move in ETHUSDT" → Scalping (1H + 15M + 5M)
    - "should I buy Bitcoin?" → Short-term analysis

    **Response includes:**
    - Direction (BULLISH/BEARISH/NEUTRAL)
    - Target price and stop loss
    - Confidence score (0-100)
    - Risk level (LOW/MEDIUM/HIGH)
    - Entry/exit strategy
    - Multi-timeframe technical analysis
    - News sentiment analysis

    Args:
        request: Prediction request with natural language query
        current_user: Authenticated user (from JWT token)

    Returns:
        Complete prediction with TA, news, and AI synthesis

    Raises:
        HTTPException: If prediction fails
    """
    try:
        logger.info(
            f"Prediction request from user {current_user.id if hasattr(current_user, 'id') else 'unknown'}: "
            f"{request.query}"
        )

        # Prepare initial state for LangGraph
        initial_state = {
            "query": request.query,
            "symbol": request.symbol or "",
            "user_id": str(current_user.id) if hasattr(current_user, "id") else "anonymous",
            "timeframes": [],
            "analysis_type": "",
            "ta_data": {},
            "news_data": {},
            "prediction": {}
        }

        # Run LangGraph multi-agent workflow
        logger.info("Starting LangGraph prediction workflow...")
        final_state = await prediction_workflow.ainvoke(initial_state)

        logger.info(
            f"Prediction completed: {final_state.get('symbol')} - "
            f"{final_state.get('prediction', {}).get('direction', 'UNKNOWN')}"
        )

        # Extract prediction data
        prediction = final_state.get("prediction", {})

        # Build response
        response = PredictionResponse(
            success=True,
            query=request.query,
            symbol=final_state.get("symbol", "UNKNOWN"),
            analysis_type=final_state.get("analysis_type", "short_term"),
            timeframes=final_state.get("timeframes", []),
            prediction=prediction,
            ta_summary=prediction.get("ta_summary"),
            news_impact=prediction.get("news_impact"),
            confidence=prediction.get("confidence"),
            risk_level=prediction.get("risk_level")
        )

        return response

    except Exception as e:
        logger.error(f"Prediction error: {str(e)}", exc_info=True)

        # Return error response instead of raising exception
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


@router.get("/predictions/{prediction_id}")
async def get_prediction(
    prediction_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific prediction by ID

    Args:
        prediction_id: Prediction ID
        current_user: Authenticated user

    Returns:
        Prediction result from database

    Note:
        This endpoint requires MongoDB integration for prediction history storage
    """
    try:
        # TODO: Implement prediction retrieval from MongoDB
        # prediction = await db.predictions.find_one({"_id": prediction_id, "user_id": current_user.id})

        raise HTTPException(
            status_code=501,
            detail="Prediction history storage not implemented yet. Use POST /predictions to generate new predictions."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/predictions")
async def get_user_predictions(
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """
    Get user's prediction history

    Args:
        limit: Number of predictions to return (max 50)
        current_user: Authenticated user

    Returns:
        List of user's past predictions

    Note:
        This endpoint requires MongoDB integration for prediction history storage
    """
    try:
        # TODO: Implement prediction history retrieval
        # predictions = await db.predictions.find(
        #     {"user_id": current_user.id}
        # ).sort("created_at", -1).limit(min(limit, 50)).to_list()

        return {
            "success": True,
            "count": 0,
            "predictions": [],
            "message": "Prediction history storage not implemented yet"
        }

    except Exception as e:
        logger.error(f"Get predictions error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
