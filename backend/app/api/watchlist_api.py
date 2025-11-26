"""
Watchlist API Routes
- Add/remove symbols from watchlist
- Get watchlist
- Update price alerts
- Check price alerts
"""
from fastapi import APIRouter, HTTPException, status, Header, Query
from pydantic import BaseModel
from typing import Optional, List, Dict

from app.services.auth_service import auth_service
from app.services.watchlist_service import watchlist_service

router = APIRouter(prefix="/watchlist", tags=["Watchlist"])


# ============================================
# REQUEST MODELS
# ============================================

class AddToWatchlistRequest(BaseModel):
    symbol: str
    exchange: Optional[str] = None
    market_type: str = "crypto"  # "crypto" or "stock"
    alert_price: Optional[float] = None
    alert_enabled: bool = False
    notes: Optional[str] = None


class UpdateWatchlistRequest(BaseModel):
    alert_price: Optional[float] = None
    alert_enabled: Optional[bool] = None
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
async def add_to_watchlist(
    request: AddToWatchlistRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Add symbol to watchlist

    Body:
    - **symbol**: Trading symbol
    - **exchange**: Exchange name (optional)
    - **market_type**: "crypto" or "stock"
    - **alert_price**: Price alert level (optional)
    - **alert_enabled**: Enable price alerts (default: false)
    - **notes**: User notes (optional)

    Returns:
        - Watchlist item ID
    """
    user = await get_current_user(authorization)
    user_id = user.get("id")

    success, message, watchlist_id = await watchlist_service.add_to_watchlist(
        user_id=user_id,
        symbol=request.symbol,
        exchange=request.exchange,
        market_type=request.market_type,
        alert_price=request.alert_price,
        alert_enabled=request.alert_enabled,
        notes=request.notes
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    return {
        "success": True,
        "message": message,
        "watchlist_id": watchlist_id
    }


@router.delete("/{watchlist_id}")
async def remove_from_watchlist(
    watchlist_id: str,
    authorization: Optional[str] = Header(None)
):
    """
    Remove symbol from watchlist

    Path params:
    - **watchlist_id**: Watchlist item UUID
    """
    user = await get_current_user(authorization)
    user_id = user.get("id")

    success, message = await watchlist_service.remove_from_watchlist(
        watchlist_id=watchlist_id,
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
async def get_watchlist(authorization: Optional[str] = Header(None)):
    """
    Get user's watchlist

    Returns:
        - List of watchlist items
    """
    user = await get_current_user(authorization)
    user_id = user.get("id")

    watchlist = await watchlist_service.get_user_watchlist(user_id)

    return {
        "success": True,
        "total": len(watchlist),
        "watchlist": watchlist
    }


@router.patch("/{watchlist_id}")
async def update_watchlist_item(
    watchlist_id: str,
    request: UpdateWatchlistRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Update watchlist item

    Path params:
    - **watchlist_id**: Watchlist item UUID

    Body:
    - **alert_price**: Price alert level (optional)
    - **alert_enabled**: Enable/disable alerts (optional)
    - **notes**: User notes (optional)
    """
    user = await get_current_user(authorization)
    user_id = user.get("id")

    success, message = await watchlist_service.update_watchlist_item(
        watchlist_id=watchlist_id,
        user_id=user_id,
        alert_price=request.alert_price,
        alert_enabled=request.alert_enabled,
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


@router.post("/check-alerts")
async def check_price_alerts(
    current_prices: Dict[str, float],
    authorization: Optional[str] = Header(None)
):
    """
    Check if any price alerts triggered

    Body:
    - **current_prices**: Dict of {symbol: price}

    Returns:
        - List of triggered alerts
    """
    user = await get_current_user(authorization)
    user_id = user.get("id")

    triggered_alerts = await watchlist_service.check_price_alerts(
        user_id=user_id,
        current_prices=current_prices
    )

    return {
        "success": True,
        "total_alerts": len(triggered_alerts),
        "triggered_alerts": triggered_alerts
    }
