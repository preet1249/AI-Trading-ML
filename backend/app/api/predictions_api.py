"""
Predictions API Routes
- Get predictions with caching
- User prediction history
- User statistics
- Manual outcome check
"""
from fastapi import APIRouter, HTTPException, status, Header, Query
from pydantic import BaseModel
from typing import Optional, List, Dict

from app.services.auth_service import auth_service
from app.services.prediction_service import prediction_service
from app.services.outcome_tracker import outcome_tracker
from app.db.redis_client import get_redis

router = APIRouter(prefix="/predictions", tags=["Predictions"])


# ============================================
# HELPER FUNCTIONS
# ============================================

async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """Get current user from JWT token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )

    token = authorization.replace("Bearer ", "")
    user_data = await auth_service.verify_token(token)

    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    return user_data


# ============================================
# ROUTES
# ============================================

@router.get("/history")
async def get_prediction_history(
    authorization: Optional[str] = Header(None),
    limit: int = Query(10, ge=1, le=100),
    skip: int = Query(0, ge=0)
):
    """
    Get user's prediction history

    Query params:
    - **limit**: Max predictions to return (1-100)
    - **skip**: Skip N predictions (pagination)

    Returns:
        - List of predictions with outcomes
    """
    user = await get_current_user(authorization)
    user_id = user.get("id")

    predictions = await prediction_service.get_user_predictions(
        user_id=user_id,
        limit=limit,
        skip=skip
    )

    return {
        "success": True,
        "total": len(predictions),
        "predictions": predictions
    }


@router.get("/stats")
async def get_user_stats(authorization: Optional[str] = Header(None)):
    """
    Get user's prediction statistics

    Returns:
        - Total predictions
        - Win rate
        - Average accuracy
        - Wins/losses breakdown
    """
    user = await get_current_user(authorization)
    user_id = user.get("id")

    stats = await prediction_service.get_user_stats(user_id)

    return {
        "success": True,
        "stats": stats
    }


@router.get("/{prediction_id}")
async def get_prediction(
    prediction_id: str,
    authorization: Optional[str] = Header(None)
):
    """
    Get single prediction by ID (with caching)

    Path params:
    - **prediction_id**: Prediction UUID

    Returns:
        - Full prediction data
    """
    user = await get_current_user(authorization)

    prediction = await prediction_service.get_prediction_by_id(prediction_id)

    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction not found"
        )

    # Verify user owns this prediction
    if prediction.get("user_id") != user.get("id"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this prediction"
        )

    return {
        "success": True,
        "prediction": prediction
    }


@router.post("/{prediction_id}/check-outcome")
async def check_prediction_outcome(
    prediction_id: str,
    authorization: Optional[str] = Header(None)
):
    """
    Manually trigger outcome check for a prediction

    Path params:
    - **prediction_id**: Prediction UUID

    Returns:
        - Outcome check result
    """
    user = await get_current_user(authorization)

    # Verify prediction belongs to user
    prediction = await prediction_service.get_prediction_by_id(prediction_id)

    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction not found"
        )

    if prediction.get("user_id") != user.get("id"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this prediction"
        )

    # Check outcome
    success, message = await outcome_tracker.manual_check(prediction_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    return {
        "success": True,
        "message": message
    }


@router.get("/leaderboard/global")
async def get_global_leaderboard(
    start: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    """
    Get global leaderboard (top users by accuracy)

    Query params:
    - **start**: Start rank (0-indexed)
    - **limit**: Number of users to return

    Returns:
        - Top users with accuracy scores
    """
    redis = get_redis()

    leaderboard = await redis.get_leaderboard(
        leaderboard="global",
        start=start,
        end=start + limit - 1
    )

    return {
        "success": True,
        "leaderboard": leaderboard
    }


@router.get("/leaderboard/my-rank")
async def get_my_rank(authorization: Optional[str] = Header(None)):
    """
    Get current user's rank in leaderboard

    Returns:
        - User's rank and accuracy score
    """
    user = await get_current_user(authorization)
    user_id = user.get("id")

    redis = get_redis()

    rank_data = await redis.get_user_rank(user_id, leaderboard="global")

    if not rank_data:
        return {
            "success": True,
            "message": "Not ranked yet (make some predictions!)",
            "rank": None
        }

    return {
        "success": True,
        "rank": rank_data
    }
