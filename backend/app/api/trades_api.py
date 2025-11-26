"""
Trades API Routes
- Create, close, cancel trades
- Get trade history
- Trade statistics & P&L
"""
from fastapi import APIRouter, HTTPException, status, Header, Query
from pydantic import BaseModel
from typing import Optional, List

from app.services.auth_service import auth_service
from app.services.trade_service import trade_service

router = APIRouter(prefix="/trades", tags=["Trades"])


# ============================================
# REQUEST MODELS
# ============================================

class CreateTradeRequest(BaseModel):
    symbol: str
    direction: str  # "LONG" or "SHORT"
    entry_price: float
    position_size: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit_1: Optional[float] = None
    take_profit_2: Optional[float] = None
    take_profit_3: Optional[float] = None
    prediction_id: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None


class CloseTradeRequest(BaseModel):
    exit_price: float
    notes: Optional[str] = None


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

@router.post("/")
async def create_trade(
    request: CreateTradeRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Create new trade

    Body:
    - **symbol**: Trading symbol
    - **direction**: "LONG" or "SHORT"
    - **entry_price**: Entry price
    - **position_size**: Position size (optional)
    - **stop_loss**: Stop loss price (optional)
    - **take_profit_1/2/3**: Take profit levels (optional)
    - **prediction_id**: Related prediction ID (optional)
    - **notes**: Trade notes (optional)
    - **tags**: Trade tags (optional)

    Returns:
        - Trade ID
    """
    user = await get_current_user(authorization)
    user_id = user.get("id")

    success, message, trade_id = await trade_service.create_trade(
        user_id=user_id,
        symbol=request.symbol,
        direction=request.direction,
        entry_price=request.entry_price,
        position_size=request.position_size,
        stop_loss=request.stop_loss,
        take_profit_1=request.take_profit_1,
        take_profit_2=request.take_profit_2,
        take_profit_3=request.take_profit_3,
        prediction_id=request.prediction_id,
        notes=request.notes,
        tags=request.tags
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    return {
        "success": True,
        "message": message,
        "trade_id": trade_id
    }


@router.post("/{trade_id}/close")
async def close_trade(
    trade_id: str,
    request: CloseTradeRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Close trade and calculate P&L

    Path params:
    - **trade_id**: Trade UUID

    Body:
    - **exit_price**: Exit price
    - **notes**: Closing notes (optional)

    Returns:
        - P&L calculation
    """
    user = await get_current_user(authorization)
    user_id = user.get("id")

    success, message = await trade_service.close_trade(
        trade_id=trade_id,
        user_id=user_id,
        exit_price=request.exit_price,
        notes=request.notes
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    return {
        "success": True,
        "message": message
    }


@router.delete("/{trade_id}")
async def cancel_trade(
    trade_id: str,
    authorization: Optional[str] = Header(None)
):
    """
    Cancel trade

    Path params:
    - **trade_id**: Trade UUID
    """
    user = await get_current_user(authorization)
    user_id = user.get("id")

    success, message = await trade_service.cancel_trade(
        trade_id=trade_id,
        user_id=user_id
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    return {
        "success": True,
        "message": message
    }


@router.get("/")
async def get_trades(
    authorization: Optional[str] = Header(None),
    status: Optional[str] = Query(None, regex="^(open|closed|cancelled)$"),
    limit: int = Query(50, ge=1, le=100)
):
    """
    Get user's trades

    Query params:
    - **status**: Filter by status ("open", "closed", "cancelled")
    - **limit**: Max trades to return (1-100)

    Returns:
        - List of trades
    """
    user = await get_current_user(authorization)
    user_id = user.get("id")

    trades = await trade_service.get_user_trades(
        user_id=user_id,
        status=status,
        limit=limit
    )

    return {
        "success": True,
        "total": len(trades),
        "trades": trades
    }


@router.get("/stats")
async def get_trade_stats(authorization: Optional[str] = Header(None)):
    """
    Get user's trade statistics

    Returns:
        - Total trades
        - Win rate
        - Total P&L
        - Best/worst trades
        - Average risk-reward ratio
    """
    user = await get_current_user(authorization)
    user_id = user.get("id")

    stats = await trade_service.get_trade_stats(user_id)

    return {
        "success": True,
        "stats": stats
    }
