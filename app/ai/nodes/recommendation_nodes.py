"""
코디 추천 LangGraph 노드
"""

import json
from typing import Dict, Any, List
from app.ai.schemas.workflow_state import RecommendationState
from app.ai.clients.azure_openai_client import azure_openai_client
from app.utils.json_parser import parse_json_from_text
from typing import Optional, Tuple
from app.domains.wardrobe.model import ClosetItem
from langchain_openai import AzureChatOpenAI
from app.core.config import Config
from app.ai.prompts.recommendation_prompts import (
    build_recommendation_prompt,
    build_tpo_recommendation_prompt,
    build_todays_pick_prompt,
)
import logging

logger = logging.getLogger(__name__)


def generate_candidates_node(state: RecommendationState) -> RecommendationState:
    """후보 코디 조합 생성 노드 (규칙 기반)"""
    # recommender 위치 변경(도메인 구조) 하위호환
    from app.domains.recommendation.service import recommender

    tops = state.get("tops", [])
    bottoms = state.get("bottoms", [])

    candidates = []
    for top in tops:
        for bottom in bottoms:
            score, reasons = recommender.calculate_outfit_score(top, bottom)
            candidates.append(
                {"top": top, "bottom": bottom, "score": score, "reasons": reasons}
            )

    # 점수 순으로 정렬
    candidates.sort(key=lambda x: x["score"], reverse=True)

    # 상위 후보만 선택 (LLM에 전달할 후보 수 제한)
    top_candidates = candidates[: min(10, len(candidates))]

    state["candidates"] = top_candidates
    return state


def prepare_llm_input_node(state: RecommendationState) -> RecommendationState:
    """LLM 입력 준비 노드"""
    candidates = state.get("candidates", [])
    if not candidates:
        return state

    # 후보에서 상의/하의 요약 정보 추출
    tops_summary = []
    bottoms_summary = []
    candidate_tops = {}
    candidate_bottoms = {}

    for candidate in candidates:
        top = candidate["top"]
        bottom = candidate["bottom"]
        top_id = top.get("id")
        bottom_id = bottom.get("id")

        if top_id not in candidate_tops:
            attrs = top.get("attributes", {})
            candidate_tops[top_id] = top
            tops_summary.append(
                {
                    "id": top_id,
                    "cat": (
                        (attrs.get("category") or {}).get("sub", "unknown")
                        if isinstance(attrs, dict)
                        else "unknown"
                    ),
                    "col": (
                        (attrs.get("color") or {}).get("primary", "unknown")
                        if isinstance(attrs, dict)
                        else "unknown"
                    ),
                    "style": (
                        (attrs.get("style_tags") or [])[:3]
                        if isinstance(attrs, dict)
                        else []
                    ),
                    "form": round(
                        (
                            (attrs.get("scores") or {}).get("formality", 0.5)
                            if isinstance(attrs, dict)
                            else 0.5
                        ),
                        2,
                    ),
                }
            )

        if bottom_id not in candidate_bottoms:
            attrs = bottom.get("attributes", {})
            candidate_bottoms[bottom_id] = bottom
            bottoms_summary.append(
                {
                    "id": bottom_id,
                    "cat": (
                        (attrs.get("category") or {}).get("sub", "unknown")
                        if isinstance(attrs, dict)
                        else "unknown"
                    ),
                    "col": (
                        (attrs.get("color") or {}).get("primary", "unknown")
                        if isinstance(attrs, dict)
                        else "unknown"
                    ),
                    "style": (
                        (attrs.get("style_tags") or [])[:3]
                        if isinstance(attrs, dict)
                        else []
                    ),
                    "form": round(
                        (
                            (attrs.get("scores") or {}).get("formality", 0.5)
                            if isinstance(attrs, dict)
                            else 0.5
                        ),
                        2,
                    ),
                }
            )

    state["metadata"] = {
        "tops_summary": tops_summary,
        "bottoms_summary": bottoms_summary,
        "candidate_tops": candidate_tops,
        "candidate_bottoms": candidate_bottoms,
    }

    return state


def call_llm_node(state: RecommendationState) -> RecommendationState:
    """LLM 호출 노드"""
    metadata = state.get("metadata", {})
    tops_summary = metadata.get("tops_summary", [])
    bottoms_summary = metadata.get("bottoms_summary", [])
    count = state.get("count", 1)
    user_request = state.get("user_request")
    weather_info = state.get("weather_info")

    if not tops_summary or not bottoms_summary:
        return state

    try:
        # TPO/날씨 정보가 있으면 해당 프롬프트 사용
        if user_request or weather_info:
            prompt = build_tpo_recommendation_prompt(
                user_request=user_request or "",
                weather_info=weather_info or {},
                tops_summary=tops_summary,
                bottoms_summary=bottoms_summary,
                count=count,
            )
        else:
            prompt = build_recommendation_prompt(
                tops_summary=tops_summary, bottoms_summary=bottoms_summary, count=count
            )

        response_text = azure_openai_client.generate_content(
            prompt, temperature=0.7, max_tokens=1000
        )

        # JSON 파싱
        parsed, _ = parse_json_from_text(response_text)

        if parsed:
            if isinstance(parsed, dict):
                parsed = [parsed]
            state["llm_recommendations"] = parsed if isinstance(parsed, list) else []
        else:
            state["llm_recommendations"] = []

    except Exception as e:
        # LLM 호출 실패 시 빈 리스트
        state["llm_recommendations"] = []
        state["metadata"]["llm_error"] = str(e)

    return state


def process_llm_results_node(state: RecommendationState) -> RecommendationState:
    """LLM 결과 처리 노드"""
    llm_recommendations = state.get("llm_recommendations", [])
    metadata = state.get("metadata", {})
    candidate_tops = metadata.get("candidate_tops", {})
    candidate_bottoms = metadata.get("candidate_bottoms", {})
    tops = state.get("tops", [])
    bottoms = state.get("bottoms", [])

    final_outfits = []

    for rec in llm_recommendations:
        top_id = rec.get("top_id")
        bottom_id = rec.get("bottom_id")

        # 후보에서 찾기
        top_item = candidate_tops.get(top_id) or next(
            (t for t in tops if t.get("id") == top_id), None
        )
        bottom_item = candidate_bottoms.get(bottom_id) or next(
            (b for b in bottoms if b.get("id") == bottom_id), None
        )

        if top_item and bottom_item:
            final_outfits.append(
                {
                    "top": top_item,
                    "bottom": bottom_item,
                    "score": float(rec.get("score", 0.5)),
                    "reasoning": rec.get("reasoning", ""),
                    "style_description": rec.get("style_description", ""),
                    "reasons": (
                        [rec.get("reasoning", "AI 추천")]
                        if rec.get("reasoning")
                        else []
                    ),
                }
            )

    state["final_outfits"] = final_outfits
    return state


def fallback_recommendation_node(state: RecommendationState) -> RecommendationState:
    """폴백 추천 노드 (LLM 실패 시 규칙 기반 추천)"""
    candidates = state.get("candidates", [])
    count = state.get("count", 1)

    if candidates:
        final_outfits = []
        for candidate in candidates[:count]:
            top_attrs = candidate.get("top", {}).get("attributes", {}) or {}
            bottom_attrs = candidate.get("bottom", {}).get("attributes", {}) or {}
            top_cat = (
                (top_attrs.get("category") or {}) if isinstance(top_attrs, dict) else {}
            )
            bottom_cat = (
                (bottom_attrs.get("category") or {})
                if isinstance(bottom_attrs, dict)
                else {}
            )
            final_outfits.append(
                {
                    "top": candidate["top"],
                    "bottom": candidate["bottom"],
                    "score": candidate["score"],
                    "reasoning": "규칙 기반 추천",
                    "style_description": (
                        f"{(top_cat.get('sub') or top_cat.get('main') or 'Top')} & "
                        f"{(bottom_cat.get('sub') or bottom_cat.get('main') or 'Bottom')}"
                    ),
                    "reasons": candidate.get("reasons", []),
                }
            )
        state["final_outfits"] = final_outfits
    else:
        state["final_outfits"] = []

    return state

    return "llm"


def format_item_for_llm(item: ClosetItem) -> str:
    """ClosetItem을 LLM이 이해하기 쉬운 문자열로 변환"""
    features = item.features or {}

    category = features.get("category", {})
    color = features.get("color", {})
    material = features.get("material", {})

    return (
        f"ID: {item.id} | "
        f"카테고리: {category.get('sub', 'unknown')} | "
        f"색상: {color.get('primary', 'unknown')} | "
        f"소재: {material.get('guess', 'unknown')}"
    )


def recommend_todays_pick_outfit(
    tops: List[ClosetItem],
    bottoms: List[ClosetItem],
    weather: Dict,
    context: Optional[str] = None,
) -> Dict:
    """
    LLM을 사용하여 최적의 상의/하의 조합 추천 (Today's Pick 전용)
    """
    # 아이템 목록을 텍스트로 변환
    tops_list = "\\n".join([format_item_for_llm(item) for item in tops[:15]])
    bottoms_list = "\\n".join([format_item_for_llm(item) for item in bottoms[:15]])

    # 프롬프트 생성
    prompt = build_todays_pick_prompt(
        weather_summary=weather.get("summary", "정보 없음"),
        temp_min=weather.get("temp_min", "?"),
        temp_max=weather.get("temp_max", "?"),
        tops_list=tops_list,
        bottoms_list=bottoms_list,
        context=context or "특별한 요청 없음",
    )

    # LLM 호출
    llm = AzureChatOpenAI(
        azure_deployment=Config.AZURE_OPENAI_DEPLOYMENT_NAME,
        api_version=Config.AZURE_OPENAI_API_VERSION,
        temperature=0.7,
        max_tokens=500,
    )

    response = llm.invoke(prompt)
    result_text = response.content.strip()

    # JSON 파싱
    try:
        # 마크다운 코드블록 제거
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()

        result = json.loads(result_text)

        # 필수 필드 검증
        required_fields = ["top_id", "bottom_id", "reasoning", "score"]
        for field in required_fields:
            if field not in result:
                raise ValueError(f"Missing required field: {field}")

        return result

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        raise ValueError(f"LLM returned invalid JSON: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing LLM response: {e}")
        raise


def should_use_llm(state: RecommendationState) -> str:
    """LLM 사용 여부 결정 (조건부 엣지)"""
    candidates = state.get("candidates", [])
    if candidates:
        return "llm"
    return "fallback"
