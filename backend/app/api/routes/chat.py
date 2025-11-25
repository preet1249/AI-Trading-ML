"""
Chat API Routes
Handles user chat queries for predictions
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from app.api.middleware.auth import get_current_user
from app.models.schemas import User

router = APIRouter()


class ChatRequest(BaseModel):
    """Chat request model"""
    message: str
    symbol: Optional[str] = None
    timeframe: Optional[str] = "1h"


class ChatResponse(BaseModel):
    """Chat response model"""
    message: str
    prediction_id: Optional[str] = None


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Handle chat messages and trigger prediction agents

    Args:
        request: Chat request with message and optional symbol
        current_user: Authenticated user

    Returns:
        Chat response with prediction ID
    """
    try:
        # TODO: Implement LangGraph agent invocation
        # TODO: Parse user message to extract intent
        # TODO: Trigger appropriate agents
        # TODO: Return prediction ID for tracking

        return ChatResponse(
            message="Processing your request...",
            prediction_id=None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
