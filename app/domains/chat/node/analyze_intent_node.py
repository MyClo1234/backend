"""
채팅 인텐트 분석 노드 및 채팅 워크플로우
"""

import logging
from app.domains.chat.states import ChatState
from app.ai.clients.azure_openai_client import azure_openai_client
from app.utils.json_parser import parse_json_from_text
from app.domains.chat.enums import Intent, NodeName

logger = logging.getLogger(__name__)


async def analyze_intent_node(state: ChatState) -> ChatState:
    """사용자의 입력에서 의도를 분석하는 노드"""
    user_query = state.get("user_query", "")

    prompt = f"""
    당신은 패션 어시스턴트의 의도 분석기입니다. 
    사용자의 입력이 '코디 추천 요청'인지 '일반 대화'인지 판단하세요.
    
    사용자 입력: "{user_query}"
    
    결과를 아래 JSON 형식으로 반환하세요:
    {{
        "intent": "${Intent.RECOMMEND_CODY.value}" 또는 "${Intent.GENERATE_GUIDE.value}",
        "tpo": "발견된 TPO 정보 (결혼식, 데이트, 운동 등, 없으면 None)",
        "special_request": "색상, 소재, 스타일 등에 대한 구체적인 요청 사항 (없으면 null)",
        "reason": "판단 근거",
        "weather_wanted": true/false (날씨 언급 여부),
    }}
    """

    try:
        response_text = await azure_openai_client.generate_content(
            prompt, temperature=0
        )
    except Exception as exception:
        logger.error(f"Chat intent analysis api call error: {exception}")
        raise exception

    parsed, _ = parse_json_from_text(response_text)
    if parsed == None:
        raise ValueError("Parsed intent is None")

    state["context"] = {
        **state["context"],
        "intent": parsed.get("intent", Intent.GENERATE_GUIDE.value),
        "tpo": parsed.get("tpo", None),
        "special_request": parsed.get("special_request"),
        "intent_reason": parsed.get("reason"),  # LLM이 생성한 판단 근거 저장
        "is_recommendation_request": (
            parsed.get("intent") == Intent.RECOMMEND_CODY.value
        ),
    }

    return state
