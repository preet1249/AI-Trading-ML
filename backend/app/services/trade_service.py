"""
Trade Tracking Service - Supabase Storage
- Track user's actual trades
- Calculate P&L automatically
- Performance metrics
"""
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import uuid

from app.db.supabase_client import get_admin_supabase

logger = logging.getLogger(__name__)


class TradeService:
    """Production-ready trade tracking service"""

    @classmethod
    async def create_trade(
        cls,
        user_id: str,
        symbol: str,
        direction: str,
        entry_price: float,
        position_size: float = None,
        stop_loss: float = None,
        take_profit_1: float = None,
        take_profit_2: float = None,
        take_profit_3: float = None,
        prediction_id: str = None,
        notes: str = None,
        tags: List[str] = None
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Create new trade

        Args:
            user_id: User ID
            symbol: Trading symbol
            direction: "LONG" or "SHORT"
            entry_price: Entry price
            position_size: Position size
            stop_loss: Stop loss price
            take_profit_1/2/3: Take profit levels
            prediction_id: Related prediction ID
            notes: Trade notes
            tags: Trade tags

        Returns:
            (success, message, trade_id)
        """
        try:
            trade_id = str(uuid.uuid4())
            supabase = get_admin_supabase()

            trade_data = {
                "id": trade_id,
                "user_id": user_id,
                "prediction_id": prediction_id,
                "symbol": symbol,
                "direction": direction,
                "status": "open",
                "entry_price": float(entry_price),
                "entry_time": datetime.utcnow().isoformat(),
                "position_size": float(position_size) if position_size else None,
                "stop_loss": float(stop_loss) if stop_loss else None,
                "take_profit_1": float(take_profit_1) if take_profit_1 else None,
                "take_profit_2": float(take_profit_2) if take_profit_2 else None,
                "take_profit_3": float(take_profit_3) if take_profit_3 else None,
                "notes": notes,
                "tags": tags or [],
                "created_at": datetime.utcnow().isoformat()
            }

            supabase.table("trades").insert(trade_data).execute()

            logger.info(f"✅ Trade created: {trade_id} for {symbol}")
            return True, "Trade created", trade_id

        except Exception as e:
            logger.error(f"Failed to create trade: {e}")
            return False, f"Failed to create trade: {str(e)}", None

    @classmethod
    async def close_trade(
        cls,
        trade_id: str,
        user_id: str,
        exit_price: float,
        notes: str = None
    ) -> Tuple[bool, str]:
        """
        Close trade and calculate P&L

        Args:
            trade_id: Trade ID
            user_id: User ID (for RLS)
            exit_price: Exit price
            notes: Closing notes

        Returns:
            (success, message)
        """
        try:
            supabase = get_admin_supabase()

            # Get trade
            response = supabase.table("trades").select("*").eq("id", trade_id).eq("user_id", user_id).single().execute()

            if not response.data:
                return False, "Trade not found"

            trade = response.data
            entry_price = float(trade["entry_price"])
            direction = trade["direction"]
            position_size = float(trade.get("position_size", 1.0) or 1.0)

            # Calculate P&L
            if direction == "LONG":
                pnl = (exit_price - entry_price) * position_size
                pnl_percentage = ((exit_price - entry_price) / entry_price) * 100
            else:  # SHORT
                pnl = (entry_price - exit_price) * position_size
                pnl_percentage = ((entry_price - exit_price) / entry_price) * 100

            # Calculate risk-reward ratio
            stop_loss = trade.get("stop_loss")
            if stop_loss:
                risk = abs(entry_price - float(stop_loss)) * position_size
                risk_reward_ratio = abs(pnl / risk) if risk > 0 else 0
            else:
                risk_reward_ratio = None

            # Update trade
            update_data = {
                "status": "closed",
                "exit_price": float(exit_price),
                "exit_time": datetime.utcnow().isoformat(),
                "pnl": pnl,
                "pnl_percentage": pnl_percentage,
                "risk_reward_ratio": risk_reward_ratio,
                "notes": f"{trade.get('notes', '')} | Close: {notes}" if notes else trade.get('notes'),
                "updated_at": datetime.utcnow().isoformat()
            }

            supabase.table("trades").update(update_data).eq("id", trade_id).eq("user_id", user_id).execute()

            logger.info(f"✅ Trade closed: {trade_id} | P&L: {pnl:.2f} ({pnl_percentage:.2f}%)")
            return True, f"Trade closed | P&L: {pnl:.2f} ({pnl_percentage:.2f}%)"

        except Exception as e:
            logger.error(f"Failed to close trade: {e}")
            return False, f"Failed to close trade: {str(e)}"

    @classmethod
    async def get_user_trades(
        cls,
        user_id: str,
        status: str = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get user's trades

        Args:
            user_id: User ID
            status: Filter by status ("open", "closed", "cancelled")
            limit: Max trades to return

        Returns:
            List of trades
        """
        try:
            supabase = get_admin_supabase()

            query = supabase.table("trades").select("*").eq("user_id", user_id)

            if status:
                query = query.eq("status", status)

            response = query.order("created_at", desc=True).limit(limit).execute()

            return response.data or []

        except Exception as e:
            logger.error(f"Failed to get user trades: {e}")
            return []

    @classmethod
    async def get_trade_stats(cls, user_id: str) -> Dict:
        """Get user's trade statistics"""
        try:
            supabase = get_admin_supabase()

            # Get all closed trades
            response = supabase.table("trades").select("*").eq("user_id", user_id).eq("status", "closed").execute()

            trades = response.data or []

            if not trades:
                return {
                    "total_trades": 0,
                    "winning_trades": 0,
                    "losing_trades": 0,
                    "win_rate": 0,
                    "total_pnl": 0,
                    "avg_pnl": 0,
                    "best_trade": 0,
                    "worst_trade": 0,
                    "avg_rr": 0
                }

            # Calculate stats
            total_trades = len(trades)
            winning_trades = len([t for t in trades if t.get("pnl", 0) > 0])
            losing_trades = len([t for t in trades if t.get("pnl", 0) < 0])
            win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0

            pnls = [float(t.get("pnl", 0)) for t in trades]
            total_pnl = sum(pnls)
            avg_pnl = total_pnl / total_trades if total_trades > 0 else 0
            best_trade = max(pnls) if pnls else 0
            worst_trade = min(pnls) if pnls else 0

            rr_ratios = [float(t.get("risk_reward_ratio", 0)) for t in trades if t.get("risk_reward_ratio")]
            avg_rr = sum(rr_ratios) / len(rr_ratios) if rr_ratios else 0

            return {
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "losing_trades": losing_trades,
                "win_rate": win_rate,
                "total_pnl": total_pnl,
                "avg_pnl": avg_pnl,
                "best_trade": best_trade,
                "worst_trade": worst_trade,
                "avg_rr": avg_rr
            }

        except Exception as e:
            logger.error(f"Failed to get trade stats: {e}")
            return {}

    @classmethod
    async def cancel_trade(cls, trade_id: str, user_id: str) -> Tuple[bool, str]:
        """Cancel trade"""
        try:
            supabase = get_admin_supabase()

            supabase.table("trades").update({
                "status": "cancelled",
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", trade_id).eq("user_id", user_id).execute()

            logger.info(f"Trade cancelled: {trade_id}")
            return True, "Trade cancelled"

        except Exception as e:
            logger.error(f"Failed to cancel trade: {e}")
            return False, f"Failed to cancel trade: {str(e)}"


# Singleton instance
trade_service = TradeService()
