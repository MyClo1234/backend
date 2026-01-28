from typing_extensions import List, Dict, TypedDict, Optional, Any


class ChatState(TypedDict):
    """AI 채팅 워크플로우 상태"""

    user_query: str
    context: Dict[str, Any]
    response: Optional[str]
    recommendations: Optional[List[Dict[str, Any]]]
    todays_pick: Optional[Dict[str, Any]]
    current_node: Optional[str]
