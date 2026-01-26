"""
LangGraph 워크플로우 상태 스키마 정의
"""

from typing import TypedDict, List, Dict, Any, Optional


class ExtractionState(TypedDict):
    """이미지 속성 추출 워크플로우 상태"""

    image_bytes: bytes
    raw_response: Optional[str]
    parsed_json: Optional[Dict[str, Any]]
    errors: List[str]
    retry_count: int
    final_result: Optional[Dict[str, Any]]
    confidence: float


class RecommendationState(TypedDict):
    """코디 추천 워크플로우 상태"""

    tops: List[Dict[str, Any]]
    bottoms: List[Dict[str, Any]]
    outers: List[Dict[str, Any]]
    candidates: List[Dict[str, Any]]
    llm_recommendations: Optional[List[Dict[str, Any]]]
    final_outfits: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    user_request: Optional[str]
    weather_info: Optional[Dict[str, Any]]
    count: int


class ChatState(TypedDict):
    """AI 채팅 워크플로우 상태 (향후 사용)"""

    messages: List[Dict[str, Any]]
    user_query: str
    context: Dict[str, Any]
    response: Optional[str]
    recommendations: Optional[List[Dict[str, Any]]]
    todays_pick: Optional[Dict[str, Any]]
