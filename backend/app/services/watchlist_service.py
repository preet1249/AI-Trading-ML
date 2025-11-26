"""
Watchlist Service - Supabase Storage
- Manage user's favorite symbols
- Price alerts
- Real-time notifications
"""
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import uuid

from app.db.supabase_client import get_admin_supabase

logger = logging.getLogger(__name__)


class WatchlistService:
    """Production-ready watchlist service"""

    @classmethod
    async def add_to_watchlist(
        cls,
        user_id: str,
        symbol: str,
        exchange: str = None,
        market_type: str = "crypto",
        alert_price: float = None,
        alert_enabled: bool = False,
        notes: str = None
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Add symbol to watchlist

        Args:
            user_id: User ID
            symbol: Trading symbol
            exchange: Exchange name
            market_type: "crypto" or "stock"
            alert_price: Price alert level
            alert_enabled: Enable price alerts
            notes: User notes

        Returns:
            (success, message, watchlist_id)
        """
        try:
            watchlist_id = str(uuid.uuid4())
            supabase = get_admin_supabase()

            # Check if already exists
            existing = supabase.table("watchlist").select("id").eq("user_id", user_id).eq("symbol", symbol).execute()

            if existing.data:
                return False, "Symbol already in watchlist", existing.data[0]["id"]

            watchlist_data = {
                "id": watchlist_id,
                "user_id": user_id,
                "symbol": symbol,
                "exchange": exchange,
                "market_type": market_type,
                "notes": notes,
                "alert_price": float(alert_price) if alert_price else None,
                "alert_enabled": alert_enabled,
                "created_at": datetime.utcnow().isoformat()
            }

            supabase.table("watchlist").insert(watchlist_data).execute()

            logger.info(f"✅ Added to watchlist: {symbol} for user {user_id}")
            return True, "Added to watchlist", watchlist_id

        except Exception as e:
            logger.error(f"Failed to add to watchlist: {e}")
            return False, f"Failed to add to watchlist: {str(e)}", None

    @classmethod
    async def remove_from_watchlist(
        cls,
        watchlist_id: str,
        user_id: str
    ) -> Tuple[bool, str]:
        """Remove symbol from watchlist"""
        try:
            supabase = get_admin_supabase()

            supabase.table("watchlist").delete().eq("id", watchlist_id).eq("user_id", user_id).execute()

            logger.info(f"Removed from watchlist: {watchlist_id}")
            return True, "Removed from watchlist"

        except Exception as e:
            logger.error(f"Failed to remove from watchlist: {e}")
            return False, f"Failed to remove from watchlist: {str(e)}"

    @classmethod
    async def get_user_watchlist(cls, user_id: str) -> List[Dict]:
        """Get user's watchlist"""
        try:
            supabase = get_admin_supabase()

            response = supabase.table("watchlist").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()

            return response.data or []

        except Exception as e:
            logger.error(f"Failed to get watchlist: {e}")
            return []

    @classmethod
    async def update_watchlist_item(
        cls,
        watchlist_id: str,
        user_id: str,
        alert_price: float = None,
        alert_enabled: bool = None,
        notes: str = None
    ) -> Tuple[bool, str]:
        """Update watchlist item"""
        try:
            supabase = get_admin_supabase()

            update_data = {"updated_at": datetime.utcnow().isoformat()}

            if alert_price is not None:
                update_data["alert_price"] = float(alert_price)

            if alert_enabled is not None:
                update_data["alert_enabled"] = alert_enabled

            if notes is not None:
                update_data["notes"] = notes

            supabase.table("watchlist").update(update_data).eq("id", watchlist_id).eq("user_id", user_id).execute()

            logger.info(f"Updated watchlist item: {watchlist_id}")
            return True, "Watchlist item updated"

        except Exception as e:
            logger.error(f"Failed to update watchlist item: {e}")
            return False, f"Failed to update watchlist item: {str(e)}"

    @classmethod
    async def check_price_alerts(cls, user_id: str, current_prices: Dict[str, float]) -> List[Dict]:
        """
        Check if any watchlist alerts triggered

        Args:
            user_id: User ID
            current_prices: Dict of {symbol: price}

        Returns:
            List of triggered alerts
        """
        try:
            supabase = get_admin_supabase()

            # Get watchlist with alerts enabled
            response = supabase.table("watchlist").select("*").eq("user_id", user_id).eq("alert_enabled", True).execute()

            watchlist = response.data or []
            triggered_alerts = []

            for item in watchlist:
                symbol = item["symbol"]
                alert_price = item.get("alert_price")

                if symbol in current_prices and alert_price:
                    current_price = current_prices[symbol]

                    # Simple alert: price crossed alert level
                    if current_price >= alert_price:
                        triggered_alerts.append({
                            "watchlist_id": item["id"],
                            "symbol": symbol,
                            "alert_price": alert_price,
                            "current_price": current_price,
                            "notes": item.get("notes", "")
                        })

            return triggered_alerts

        except Exception as e:
            logger.error(f"Failed to check price alerts: {e}")
            return []


# Singleton instance
watchlist_service = WatchlistService()
