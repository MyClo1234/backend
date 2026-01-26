"""
채팅 인텐트 분석 노드 및 채팅 워크플로우
"""

import logging
from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, END
from app.ai.schemas.workflow_state import ChatState
from app.ai.clients.azure_openai_client import azure_openai_client
from app.utils.json_parser import parse_json_from_text
from app.llm.todays_pick_service import recommend_todays_pick_v2
from app.domains.weather.service import weather_service

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
        "weather_wanted": true/false (날씨 언급 여부),
        "special_request": "색상, 소재, 스타일 등에 대한 구체적인 요청 사항 (없으면 null)"
    }}
    """

    try:
        response_text = azure_openai_client.generate_content(prompt, temperature=0)
        parsed, _ = parse_json_from_text(response_text)

        if parsed:
            state["context"]["intent"] = parsed.get("intent", "GENERAL")
            state["context"]["tpo"] = parsed.get("tpo_context")
            state["context"]["special_request"] = parsed.get("special_request")
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


async def handle_recommendation_node(state: ChatState) -> ChatState:
    """추천 의도가 감지되었을 때 추천 서비스를 호출하는 노드"""
    from app.database import SessionLocal
    from uuid import UUID

    user_id = state["context"].get("user_id")
    tpo = state["context"].get("tpo")
    special_request = state["context"].get("special_request")

    # 위치 정보 (Flutter에서 전달받은 값 또는 기본값 서울)
    lat = state["context"].get("lat", 37.5665)
    lon = state["context"].get("lon", 126.9780)

    # 문맥 생성
    context_parts = []
    if tpo:
        context_parts.append(f"TPO: {tpo}")
    if special_request:
        context_parts.append(f"요청사항: {special_request}")
    context = ", ".join(context_parts) if context_parts else None

    try:
        with SessionLocal() as db:
            # 1. 중앙화된 날씨 정보 가져오기 (비동기 처리)
            weather_data = await weather_service.get_weather_info(db, lat, lon)

            # 2. Today's Pick 추천 엔진 호출 (문맥 포함)
            result = recommend_todays_pick_v2(
                user_id=UUID(user_id) if isinstance(user_id, str) else user_id,
                weather=weather_data,
                db=db,
                context=context,
            )

            if result.get("success"):
                state["todays_pick"] = result
                state["context"]["is_pick_updated"] = True

                # AI 응답 생성
                weather_summary = result.get("weather_summary", "날씨 정보 없음")
                reasoning = result.get("reasoning", "코디를 추천해 드립니다.")

                response_parts = []
                if tpo:
                    response_parts.append(f"오늘 {tpo} 일정이 있으시군요!")

                response_parts.append(
                    f"현재 날씨({weather_summary})와 요청하신 내용을 바탕으로 새로운 '오늘의 추천'을 준비했습니다."
                )
                response_parts.append(f"\n추천 사유: {reasoning}")
                response_parts.append(
                    "\n홈 화면에서 나노바나나가 생성한 마네킹 이미지를 바로 확인하실 수 있어요!"
                )

                state["response"] = "\n".join(response_parts)
            else:
                state["response"] = (
                    "죄송합니다, 현재 옷장 정보를 바탕으로 적절한 코디를 찾지 못했습니다."
                )

    except ValueError as ve:
        logger.warning(f"Recommendation validation error: {ve}")
        state["response"] = (
            str(ve)
            if "Insufficient wardrobe items" in str(ve)
            else "죄송합니다, 옷장에 추천할 만한 옷이 충분하지 않아요. 상의와 하의를 더 등록해 주세요!"
        )

    except Exception as e:
        logger.error(f"Error in handle_recommendation_node: {e}", exc_info=True)
        state["response"] = (
            "코디를 추천하는 중에 문제가 발생했습니다. 잠시 후 다시 시도해 주세요."
        )

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

    # Import here to avoid circular dependency if any
    from app.ai.nodes.generation_nodes import generate_todays_pick

    workflow.add_node("generate_todays_pick", generate_todays_pick)

    workflow.set_entry_point("analyze_intent")

    workflow.add_conditional_edges(
        "analyze_intent",
        route_intent,
        {"recommend": "recommend_outfit", "general": "generate_general"},
    )

    workflow.add_edge("generate_general", END)

    # Recommendation flow: Recommend -> Generate Image -> End
    workflow.add_edge("recommend_outfit", "generate_todays_pick")
    workflow.add_edge("generate_todays_pick", END)

    return workflow.compile()


# Singleton
_chat_workflow = None


def get_chat_workflow() -> StateGraph:
    global _chat_workflow
    if _chat_workflow is None:
        _chat_workflow = create_chat_workflow()
    return _chat_workflow
