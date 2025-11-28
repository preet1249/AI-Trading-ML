"""
Chat History API Routes
- Create new chats
- Save messages to chats
- Get chat history
- Delete chats
"""
from fastapi import APIRouter, HTTPException, status, Header
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime

from app.services.chat_service import chat_service
from app.services.auth_service import auth_service

router = APIRouter(prefix="/chat", tags=["Chat History"])


# ============================================
# REQUEST MODELS
# ============================================

class NewChatRequest(BaseModel):
    title: Optional[str] = None


class SaveMessageRequest(BaseModel):
    chat_id: str
    user_message: str
    ai_response: Dict
    prediction_data: Optional[Dict] = None


class UpdateChatTitleRequest(BaseModel):
    title: str


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

@router.post("/new")
async def create_new_chat(
    request: NewChatRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Create a new chat session

    Returns:
        - chat_id: UUID of the new chat
    """
    user = await get_current_user(authorization)
    user_id = user.get("id")

    success, message, chat_id = await chat_service.create_chat(
        user_id=user_id,
        title=request.title
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    return {
        "success": True,
        "chat_id": chat_id,
        "message": "Chat created successfully"
    }


@router.post("/save")
async def save_message(
    request: SaveMessageRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Save a message to a chat

    Body:
    - **chat_id**: Chat UUID
    - **user_message**: User's message
    - **ai_response**: AI's response text
    - **prediction_data**: Optional prediction data

    Returns:
        - success: Boolean
    """
    user = await get_current_user(authorization)
    user_id = user.get("id")

    success, message = await chat_service.save_message(
        chat_id=request.chat_id,
        user_id=user_id,
        user_message=request.user_message,
        ai_response=request.ai_response,
        prediction_data=request.prediction_data
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    return {
        "success": True,
        "message": "Message saved successfully"
    }


@router.get("/history")
async def get_chat_history(
    authorization: Optional[str] = Header(None),
    limit: int = 50
):
    """
    Get user's chat history (list of chats)

    Query params:
    - **limit**: Max chats to return (default: 50)

    Returns:
        - List of chats with metadata
    """
    user = await get_current_user(authorization)
    user_id = user.get("id")

    chats = await chat_service.get_user_chats(
        user_id=user_id,
        limit=limit
    )

    return {
        "success": True,
        "total": len(chats),
        "chats": chats
    }


@router.get("/{chat_id}")
async def get_chat(
    chat_id: str,
    authorization: Optional[str] = Header(None)
):
    """
    Get a specific chat with all messages

    Path params:
    - **chat_id**: Chat UUID

    Returns:
        - Full chat with messages
    """
    user = await get_current_user(authorization)
    user_id = user.get("id")

    chat = await chat_service.get_chat_by_id(
        chat_id=chat_id,
        user_id=user_id
    )

    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )

    return {
        "success": True,
        "chat": chat
    }


@router.delete("/{chat_id}")
async def delete_chat(
    chat_id: str,
    authorization: Optional[str] = Header(None)
):
    """
    Delete a chat

    Path params:
    - **chat_id**: Chat UUID
    """
    user = await get_current_user(authorization)
    user_id = user.get("id")

    success, message = await chat_service.delete_chat(
        chat_id=chat_id,
        user_id=user_id
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    return {
        "success": True,
        "message": "Chat deleted successfully"
    }


@router.patch("/{chat_id}/title")
async def update_chat_title(
    chat_id: str,
    request: UpdateChatTitleRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Update chat title

    Path params:
    - **chat_id**: Chat UUID

    Body:
    - **title**: New title
    """
    user = await get_current_user(authorization)
    user_id = user.get("id")

    success, message = await chat_service.update_chat_title(
        chat_id=chat_id,
        user_id=user_id,
        title=request.title
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    return {
        "success": True,
        "message": "Chat title updated"
    }
