"""
CLI API Routes - Unauthenticated endpoint for simple CLI usage
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

from app.agents.graph import prediction_workflow

router = APIRouter()
logger = logging.getLogger(__name__)


class CLIRequest(BaseModel):
    """CLI request model"""
    query: str


class CLIResponse(BaseModel):
    """CLI response model"""
    success: bool
    prediction: str
    message: str = ""


@router.post("/cli/predict", response_model=CLIResponse)
async def cli_predict(request: CLIRequest):
    """
    Simple prediction endpoint for CLI usage (no authentication required)

    Args:
        request: CLI request with query

    Returns:
        Prediction response
    """
    try:
        logger.info(f"CLI prediction request: {request.query}")

        # Invoke the prediction workflow
        result = await prediction_workflow.ainvoke({
            "query": request.query,
            "user_id": "cli-user",  # Dummy user ID for CLI
        })

        # Extract prediction from result
        prediction_data = result.get("prediction", {})

        if not prediction_data or prediction_data.get("error"):
            error_msg = prediction_data.get("reasoning", "Could not generate prediction")
            return CLIResponse(
                success=False,
                prediction="",
                message=error_msg
            )

        # Format prediction for CLI display
        formatted_prediction = format_prediction_for_cli(prediction_data)

        return CLIResponse(
            success=True,
            prediction=formatted_prediction,
            message="Success"
        )

    except Exception as e:
        logger.error(f"CLI prediction error: {str(e)}")
        import traceback
        traceback.print_exc()
        return CLIResponse(
            success=False,
            prediction="",
            message=f"Error: {str(e)}"
        )


def format_prediction_for_cli(pred: dict) -> str:
    """Format prediction dictionary into readable CLI text"""
    try:
        lines = []

        # Header
        symbol = pred.get("symbol", "Unknown")
        direction = pred.get("direction", "NEUTRAL")
        confidence = pred.get("confidence", 0)
        is_market_closed = pred.get("market_closed", False)
        market_status_msg = pred.get("market_status_message", "")

        lines.append(f"📊 PREDICTION FOR {symbol}")
        lines.append("=" * 60)
        lines.append("")

        # Market status indicator (for stocks when closed)
        if is_market_closed:
            lines.append("📅 MARKET CLOSED - NEXT TRADING DAY PREDICTION")
            lines.append("ℹ️  Using: Last 100 candles + Latest news (<24h)")
            if market_status_msg:
                lines.append(f"ℹ️  Status: {market_status_msg}")
            lines.append("")
            lines.append("─" * 60)
            lines.append("")

        # Main prediction
        lines.append(f"🎯 DIRECTION: {direction}")
        lines.append(f"💪 CONFIDENCE: {confidence}%")
        lines.append(f"⚠️  RISK LEVEL: {pred.get('risk_level', 'MEDIUM')}")
        lines.append(f"⏰ TIMEFRAME: {pred.get('timeframe', '1h').upper()}")
        lines.append("")

        # Entry & Exit
        entry = pred.get("entry_price", 0)
        stop_loss = pred.get("stop_loss", 0)
        target = pred.get("target_price", 0)

        lines.append("📍 ENTRY & EXIT LEVELS:")
        lines.append(f"  Entry:      ${entry:.2f}")
        lines.append(f"  Stop Loss:  ${stop_loss:.2f}")
        lines.append(f"  Target:     ${target:.2f}")

        # Multiple TPs if available
        take_profits = pred.get("take_profits", [])
        if take_profits:
            lines.append("")
            lines.append("🎯 TAKE PROFIT LEVELS:")
            for i, tp in enumerate(take_profits[:3], 1):
                lines.append(f"  TP{i}: ${tp.get('price', 0):.2f} (RR: {tp.get('risk_reward', 0):.1f})")

        lines.append("")

        # Entry reason
        entry_reason = pred.get("entry_reason", "")
        if entry_reason:
            lines.append(f"💡 ENTRY REASON: {entry_reason}")
            lines.append("")

        # Reasoning
        reasoning = pred.get("reasoning", "")
        if reasoning:
            lines.append("📝 ANALYSIS:")
            # Wrap reasoning text
            import textwrap
            wrapped = textwrap.fill(reasoning, width=60)
            lines.append(wrapped)
            lines.append("")

        # Key levels
        key_levels = pred.get("key_levels", [])
        if key_levels:
            lines.append("🔑 KEY LEVELS:")
            for level in key_levels[:4]:
                lines.append(f"  • {level}")
            lines.append("")

        # Market condition
        market_condition = pred.get("market_condition", "")
        if market_condition:
            lines.append(f"📈 MARKET: {market_condition.upper()}")
            lines.append("")

        lines.append("=" * 60)
        lines.append("⚠️  DISCLAIMER: This is AI-generated analysis. Always DYOR!")

        return "\n".join(lines)

    except Exception as e:
        logger.error(f"Formatting error: {e}")
        return f"Prediction generated but formatting failed: {str(pred)}"
