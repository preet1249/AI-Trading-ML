"""
LangGraph Setup - Agent Orchestration
Multi-agent system with TA, News, and Prediction agents
"""
from typing import TypedDict
from langgraph.graph import StateGraph, END

# TODO: Import agents when implemented
# from app.agents.ta_agent import ta_node
# from app.agents.news_agent import news_node
# from app.agents.predict_agent import predict_node


class AgentState(TypedDict):
    """Shared state across all agents"""
    query: str
    symbol: str
    timeframe: str
    user_id: str
    ta_data: dict
    news_data: dict
    prediction: str


def build_agent_graph() -> StateGraph:
    """
    Build LangGraph agent workflow

    Flow:
    1. TA Agent - Fetch data + calculate indicators
    2. News Agent - Fetch + analyze news sentiment
    3. Predict Agent - Synthesize TA + News → Final prediction

    Returns:
        Compiled LangGraph
    """
    # Initialize graph
    graph = StateGraph(AgentState)

    # TODO: Add nodes when agents are implemented
    # graph.add_node("ta", ta_node)
    # graph.add_node("news", news_node)
    # graph.add_node("predict", predict_node)

    # TODO: Add edges
    # graph.set_entry_point("ta")
    # graph.add_edge("ta", "news")
    # graph.add_edge("news", "predict")
    # graph.add_edge("predict", END)

    # Compile graph
    # app = graph.compile()
    # return app

    return graph
