"""
코디 추천 LangGraph 노드
"""
import json
from typing import Dict, Any, List
from app.ai.schemas.workflow_state import RecommendationState
from app.ai.clients.azure_openai_client import azure_openai_client
from app.ai.prompts.recommendation_prompts import (
    build_recommendation_prompt,
    build_tpo_recommendation_prompt
)
from app.utils.json_parser import parse_json_from_text


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
            candidates.append({
                "top": top,
                "bottom": bottom,
                "score": score,
                "reasons": reasons
            })
    
    # 점수 순으로 정렬
    candidates.sort(key=lambda x: x["score"], reverse=True)
    
    # 상위 후보만 선택 (LLM에 전달할 후보 수 제한)
    top_candidates = candidates[:min(10, len(candidates))]
    
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
            tops_summary.append({
                "id": top_id,
                "cat": (attrs.get("category") or {}).get("sub", "unknown") if isinstance(attrs, dict) else "unknown",
                "col": (attrs.get("color") or {}).get("primary", "unknown") if isinstance(attrs, dict) else "unknown",
                "style": ((attrs.get("style_tags") or [])[:3] if isinstance(attrs, dict) else []),
                "form": round(((attrs.get("scores") or {}).get("formality", 0.5) if isinstance(attrs, dict) else 0.5), 2),
            })
        
        if bottom_id not in candidate_bottoms:
            attrs = bottom.get("attributes", {})
            candidate_bottoms[bottom_id] = bottom
            bottoms_summary.append({
                "id": bottom_id,
                "cat": (attrs.get("category") or {}).get("sub", "unknown") if isinstance(attrs, dict) else "unknown",
                "col": (attrs.get("color") or {}).get("primary", "unknown") if isinstance(attrs, dict) else "unknown",
                "style": ((attrs.get("style_tags") or [])[:3] if isinstance(attrs, dict) else []),
                "form": round(((attrs.get("scores") or {}).get("formality", 0.5) if isinstance(attrs, dict) else 0.5), 2),
            })
    
    state["metadata"] = {
        "tops_summary": tops_summary,
        "bottoms_summary": bottoms_summary,
        "candidate_tops": candidate_tops,
        "candidate_bottoms": candidate_bottoms
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
                count=count
            )
        else:
            prompt = build_recommendation_prompt(
                tops_summary=tops_summary,
                bottoms_summary=bottoms_summary,
                count=count
            )
        
        response_text = azure_openai_client.generate_content(
            prompt,
            temperature=0.7,
            max_tokens=1000
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
            final_outfits.append({
                "top": top_item,
                "bottom": bottom_item,
                "score": float(rec.get("score", 0.5)),
                "reasoning": rec.get("reasoning", ""),
                "style_description": rec.get("style_description", ""),
                "reasons": [rec.get("reasoning", "AI 추천")] if rec.get("reasoning") else []
            })
    
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
            top_cat = (top_attrs.get("category") or {}) if isinstance(top_attrs, dict) else {}
            bottom_cat = (
                (bottom_attrs.get("category") or {}) if isinstance(bottom_attrs, dict) else {}
            )
            final_outfits.append({
                "top": candidate["top"],
                "bottom": candidate["bottom"],
                "score": candidate["score"],
                "reasoning": "규칙 기반 추천",
                "style_description": (
                    f"{(top_cat.get('sub') or top_cat.get('main') or 'Top')} & "
                    f"{(bottom_cat.get('sub') or bottom_cat.get('main') or 'Bottom')}"
                ),
                "reasons": candidate.get("reasons", [])
            })
        state["final_outfits"] = final_outfits
    else:
        state["final_outfits"] = []
    
    return state


def should_use_llm(state: RecommendationState) -> str:
    """LLM 사용 여부 결정"""
    candidates = state.get("candidates", [])
    if not candidates:
        return "fallback"
    return "llm"
