"""
TypedDict definition for Today's Pick workflow state.
"""

from typing import TypedDict, Optional, Dict, List, Any


class TodaysPickState(TypedDict):
    """State for the Today's Pick auto-generation workflow."""

    # Input
    user_id: str
    tops: List[Dict[str, Any]]
    bottoms: List[Dict[str, Any]]
    weather: Dict[str, Any]

    # Recommendation Result
    selected_top: Optional[Dict[str, Any]]
    selected_bottom: Optional[Dict[str, Any]]
    reasoning: Optional[str]
    score: Optional[float]

    # Image Generation
    composite_image_url: Optional[str]

    # Error handling
    error: Optional[str]
