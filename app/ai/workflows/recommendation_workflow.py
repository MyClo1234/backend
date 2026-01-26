"""
코디 추천 LangGraph 워크플로우
"""

from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, END
from app.ai.schemas.workflow_state import RecommendationState
from app.ai.nodes.recommendation_nodes import (
    generate_candidates_node,
    prepare_llm_input_node,
    call_llm_node,
    process_llm_results_node,
    fallback_recommendation_node,
    should_use_llm,
)
from app.ai.nodes.generation_nodes import nano_banana_node


def create_recommendation_workflow() -> StateGraph:
    """코디 추천 워크플로우 생성"""
    workflow = StateGraph(RecommendationState)

    # 노드 추가
    workflow.add_node("generate_candidates", generate_candidates_node)
    workflow.add_node("prepare_llm_input", prepare_llm_input_node)
    workflow.add_node("call_llm", call_llm_node)
    workflow.add_node("process_llm_results", process_llm_results_node)
    workflow.add_node("fallback", fallback_recommendation_node)
    workflow.add_node("generate_image", nano_banana_node)

    # 엣지 정의
    workflow.set_entry_point("generate_candidates")
    workflow.add_edge("generate_candidates", "prepare_llm_input")

    # 조건부 엣지: 후보가 있으면 LLM 사용, 없으면 폴백
    workflow.add_conditional_edges(
        "prepare_llm_input", should_use_llm, {"llm": "call_llm", "fallback": "fallback"}
    )

    workflow.add_edge("call_llm", "process_llm_results")
    workflow.add_edge("process_llm_results", "generate_image")
    workflow.add_edge("fallback", "generate_image")
    workflow.add_edge("generate_image", END)

    return workflow.compile()


# 싱글톤 워크플로우 인스턴스
_recommendation_workflow = None


def get_recommendation_workflow() -> StateGraph:
    """코디 추천 워크플로우 인스턴스 반환"""
    global _recommendation_workflow
    if _recommendation_workflow is None:
        _recommendation_workflow = create_recommendation_workflow()
    return _recommendation_workflow


def recommend_outfits(
    tops: List[Dict[str, Any]],
    bottoms: List[Dict[str, Any]],
    count: int = 1,
    user_request: Optional[str] = None,
    weather_info: Optional[Dict[str, Any]] = None,
    use_llm: bool = True,
) -> List[Dict[str, Any]]:
    """
    코디 추천 (기존 인터페이스 유지)

    Args:
        tops: 상의 아이템 리스트
        bottoms: 하의 아이템 리스트
        count: 추천할 코디 개수
        user_request: 사용자 요청 (TPO)
        weather_info: 날씨 정보
        use_llm: LLM 사용 여부

    Returns:
        추천된 코디 리스트
    """
    # 초기 상태 설정
    initial_state: RecommendationState = {
        "tops": tops,
        "bottoms": bottoms,
        "candidates": [],
        "llm_recommendations": None,
        "final_outfits": [],
        "metadata": {"user_id": str(kwargs.get("user_id", "unknown"))},
        "user_request": user_request,
        "weather_info": weather_info,
        "count": count,
    }

    if not use_llm:
        # LLM 사용 안 함 - 규칙 기반만 사용
        from app.ai.nodes.recommendation_nodes import (
            generate_candidates_node,
            fallback_recommendation_node,
        )

        state = generate_candidates_node(initial_state)
        state = fallback_recommendation_node(state)
        return state.get("final_outfits", [])

    # 워크플로우 실행
    workflow = get_recommendation_workflow()
    final_state = workflow.invoke(initial_state)

    # 최종 결과 반환
    return final_state.get("final_outfits", [])
