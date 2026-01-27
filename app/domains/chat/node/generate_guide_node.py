"""
채팅 인텐트 분석 노드 및 채팅 워크플로우
"""

import logging
from app.ai.schemas.workflow_state import ChatState
from app.ai.clients.azure_openai_client import azure_openai_client
from app.domains.chat.enums import NodeName

logger = logging.getLogger(__name__)


async def generate_guide_node(state: ChatState) -> ChatState:
    """코디 추천 요청 유도"""
    user_query = state.get("user_query", "")

    # 간단한 페르소나 설정
    system_prompt = """
    당신은 친절한 패션 AI 어시스턴트 나노바나나입니다.
    사용자가 코디 추천을 요청하지 않았더라도, 자연스럽게 코디 추천을 유도하는 대화를 이끌어가세요.
    사용자가 코디 추천에 관심을 가질 수 있도록, 날씨나 계절에 맞는 패션 아이템을 언급하며 대화를 진행하세요.
    사용자가 코디 추천을 요청할 때까지 친절하고 흥미로운 대화를 이어가세요.
    """

    prompt = f"{system_prompt}\n\nUser: {user_query}\nAI:"

    try:
        response = await azure_openai_client.generate_content(prompt)
        state["response"] = response
    except Exception as e:
        state["response"] = "죄송합니다, 잠시 대화가 어렵네요."

    return state
