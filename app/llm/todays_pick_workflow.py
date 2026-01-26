"""
LangGraph workflow for Today's Pick auto-generation.
"""

from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session

from app.llm.todays_pick_state import TodaysPickState
from app.llm.todays_pick_nodes import (
    recommend_outfit_node,
    generate_composite_image_node,
    save_to_db_node,
)


def create_todays_pick_workflow(db: Session):
    """
    Create and compile the Today's Pick auto-generation workflow.

    Args:
        db: Database session for the save_to_db node

    Returns:
        Compiled LangGraph workflow
    """
    workflow = StateGraph(TodaysPickState)

    # Add nodes
    workflow.add_node("recommend", recommend_outfit_node)
    workflow.add_node("generate_image", generate_composite_image_node)
    workflow.add_node("save_db", lambda state: save_to_db_node(state, db))

    # Define flow
    workflow.set_entry_point("recommend")
    workflow.add_edge("recommend", "generate_image")
    workflow.add_edge("generate_image", "save_db")
    workflow.add_edge("save_db", END)

    return workflow.compile()


def run_todays_pick_workflow(
    db: Session,
    user_id: str,
    tops: list,
    bottoms: list,
    weather: dict,
) -> TodaysPickState:
    """
    Execute the Today's Pick workflow.

    Args:
        db: Database session
        user_id: User ID (UUID as string)
        tops: List of available top items
        bottoms: List of available bottom items
        weather: Weather information dict

    Returns:
        Final state with results or error
    """
    workflow = create_todays_pick_workflow(db)

    initial_state: TodaysPickState = {
        "user_id": user_id,
        "tops": tops,
        "bottoms": bottoms,
        "weather": weather,
        "selected_top": None,
        "selected_bottom": None,
        "reasoning": None,
        "score": None,
        "composite_image_url": None,
        "error": None,
    }

    result = workflow.invoke(initial_state)
    return result
