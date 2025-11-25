"""
Prediction Agent
Synthesizes TA and News data to make final prediction
"""
from typing import Dict

# TODO: Import when implemented
# from app.services.qwen import generate_prediction


async def predict_node(state: Dict) -> Dict:
    """
    Prediction Agent - Synthesize TA + News → Final prediction

    Steps:
    1. Combine TA data and news sentiment
    2. Use Qwen to generate prediction
    3. Determine direction (UP/DOWN/SIDEWAYS)
    4. Calculate confidence score
    5. Generate reasoning

    Args:
        state: Agent state with ta_data and news_data

    Returns:
        Updated state with prediction
    """
    # TODO: Implement prediction synthesis
    # ta_data = state["ta_data"]
    # news_data = state["news_data"]

    # Generate prediction with Qwen
    # prediction = await generate_prediction(ta_data, news_data)

    prediction = {
        "direction": "SIDEWAYS",
        "target": None,
        "confidence": 50,
        "reasoning": "Insufficient data for prediction"
    }

    return {"prediction": str(prediction)}
