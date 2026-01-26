"""
채팅 인텐트 분석 노드 및 채팅 워크플로우
"""

import logging
from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, END
from app.ai.schemas.workflow_state import ChatState
from app.ai.clients.azure_openai_client import azure_openai_client
from app.utils.json_parser import parse_json_from_text

logger = logging.getLogger(__name__)


def chat_intent_node(state: ChatState) -> ChatState:
    """사용자의 입력에서 의도를 분석하는 노드"""
    user_query = state.get("user_query", "")

    prompt = f"""
    당신은 패션 어시스턴트의 의도 분석기입니다. 
    사용자의 입력이 '코디 추천 요청'인지 '일반 대화'인지 판단하세요.
    
    사용자 입력: "{user_query}"
    
    결과를 아래 JSON 형식으로 반환하세요:
    {{
        "intent": "RECOMMEND" 또는 "GENERAL",
        "reason": "판단 근거",
        "tpo_context": "발견된 TPO 정보 (결혼식, 데이트, 운동 등, 없으면 null)",
        "weather_wanted": true/false (날씨 언급 여부)
    }}
    """

    try:
        response_text = azure_openai_client.generate_content(prompt, temperature=0)
        parsed, _ = parse_json_from_text(response_text)

        if parsed:
            state["context"]["intent"] = parsed.get("intent", "GENERAL")
            state["context"]["tpo"] = parsed.get("tpo_context")
            state["context"]["is_recommendation_request"] = (
                parsed.get("intent") == "RECOMMEND"
            )
        else:
            state["context"]["intent"] = "GENERAL"

    except Exception as e:
        logger.error(f"Chat intent analysis error: {e}")
        state["context"]["intent"] = "GENERAL"

    return state


def generate_chat_response_node(state: ChatState) -> ChatState:
    """일반 대화 응답 생성 노드"""
    user_query = state.get("user_query", "")
    messages = state.get("messages", [])

    # 간단한 페르소나 설정
    system_prompt = "당신은 친절한 패션 AI 어시스턴트 나노바나나입니다."

    prompt = f"{system_prompt}\n\nUser: {user_query}\nAI:"

    try:
        response = azure_openai_client.generate_content(prompt)
        state["response"] = response
    except Exception as e:
        state["response"] = "죄송합니다, 잠시 대화가 어렵네요."

    return state


def handle_recommendation_node(state: ChatState) -> ChatState:
    """추천 의도가 감지되었을 때 추천 워크플로우를 호출하는 노드"""
    from app.domains.recommendation.service import recommender
    from app.database import SessionLocal  # 임시 세션

    user_id = state["context"].get("user_id")
    tpo = state["context"].get("tpo")

    # 실제 구현에서는 위치 정보를 가져와야 함 (여기서는 서울 기본값 예시)
    lat, lon = 37.5665, 126.9780

    try:
        with SessionLocal() as db:
            # 1. Today's Pick 로직 활용 (날씨 정보 포함)
            result = recommender.get_todays_pick(db, user_id, lat, lon)

            if result.get("success"):
                outfit = result.get("outfit", {})
                state["recommendations"] = [outfit]
                state["response"] = (
                    f"Azure LLM이 오늘의 날씨({result.get('weather_summary')})를 분석하여 추천한 코디입니다. "
                    f"이 코디에 맞춰 나노바나나가 생성한 이미지와 함께 확인해 보세요!\n\n"
                    f"추천 이유: {outfit.get('reasoning', '')}"
                )
                state["context"]["is_pick_updated"] = True
            else:
                state["response"] = "옷장에 추천할 만한 옷이 부족한 것 같아요."

    except Exception as e:
        logger.error(f"Error in handle_recommendation_node: {e}")
        state["response"] = "코디를 추천하는 중에 문제가 발생했습니다."

    return state


def route_intent(state: ChatState) -> str:
    """인텐트에 따라 경로 결정"""
    if state["context"].get("intent") == "RECOMMEND":
        return "recommend"
    return "general"


def create_chat_workflow() -> StateGraph:
    """채팅 워크플로우 생성"""
    workflow = StateGraph(ChatState)

    workflow.add_node("analyze_intent", chat_intent_node)
    workflow.add_node("generate_general", generate_chat_response_node)
    workflow.add_node("recommend_outfit", handle_recommendation_node)

    workflow.set_entry_point("analyze_intent")

    workflow.add_conditional_edges(
        "analyze_intent",
        route_intent,
        {"recommend": "recommend_outfit", "general": "generate_general"},
    )

    workflow.add_edge("generate_general", END)
    workflow.add_edge("recommend_outfit", END)

    return workflow.compile()


# Singleton
_chat_workflow = None


def get_chat_workflow() -> StateGraph:
    global _chat_workflow
    if _chat_workflow is None:
        _chat_workflow = create_chat_workflow()
    return _chat_workflow
