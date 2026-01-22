"""
이미지 속성 추출 LangGraph 노드
"""
import copy
from typing import Dict, Any
from app.ai.schemas.workflow_state import ExtractionState
from app.ai.clients.azure_openai_client import azure_openai_client
from app.ai.prompts.extraction_prompts import USER_PROMPT, DEFAULT_OBJ, build_retry_prompt
from app.utils.json_parser import parse_json_from_text
from app.utils.validators import validate_schema
from app.utils.helpers import normalize


def preprocess_image_node(state: ExtractionState) -> ExtractionState:
    """이미지 전처리 노드"""
    # 이미지는 이미 bytes로 들어오므로 추가 전처리 없음
    # 필요시 여기서 이미지 검증 등 수행
    return state


def call_azure_openai_node(state: ExtractionState) -> ExtractionState:
    """Azure OpenAI Vision API 호출 노드"""
    try:
        raw_response = azure_openai_client.generate_with_vision(
            prompt=USER_PROMPT,
            image_bytes=state["image_bytes"],
            temperature=0.3,
            max_tokens=2000
        )
        state["raw_response"] = raw_response
        state["errors"] = []
    except Exception as e:
        # API 호출 실패 시 기본값 반환
        out = copy.deepcopy(DEFAULT_OBJ)
        out["meta"]["notes"] = f"AZURE_OPENAI_ERROR: {str(e)}"
        state["final_result"] = out
        state["errors"].append(f"API call failed: {str(e)}")
        state["confidence"] = 0.1
    return state


def parse_json_node(state: ExtractionState) -> ExtractionState:
    """JSON 파싱 노드"""
    if state.get("raw_response"):
        parsed, repaired = parse_json_from_text(state["raw_response"])
        state["parsed_json"] = parsed
        if parsed is None:
            out = copy.deepcopy(DEFAULT_OBJ)
            out["meta"]["notes"] = f"JSON_PARSE_FAILED. repaired_head={repaired[:160]}"
            state["final_result"] = out
            state["confidence"] = 0.1
            state["errors"].append("JSON parsing failed")
    return state


def validate_schema_node(state: ExtractionState) -> ExtractionState:
    """스키마 검증 노드"""
    if state.get("parsed_json"):
        ok, errs = validate_schema(state["parsed_json"])
        if ok:
            # 검증 성공 - 정규화 후 최종 결과 설정
            normalized = normalize(state["parsed_json"])
            state["final_result"] = normalized
            state["confidence"] = normalized.get("confidence", 0.5)
        else:
            # 검증 실패 - 에러 저장
            state["errors"] = errs
    return state


def retry_node(state: ExtractionState) -> ExtractionState:
    """재시도 노드"""
    if state.get("retry_count", 0) >= 1:
        # 이미 재시도했으면 더 이상 재시도하지 않음
        return state
    
    if state.get("errors") and not state.get("final_result"):
        # 에러가 있고 최종 결과가 없으면 재시도
        retry_prompt = build_retry_prompt(state["errors"])
        try:
            raw_response = azure_openai_client.generate_with_vision(
                prompt=retry_prompt,
                image_bytes=state["image_bytes"],
                temperature=0.2,
                max_tokens=2000
            )
            state["raw_response"] = raw_response
            state["retry_count"] = state.get("retry_count", 0) + 1
            state["errors"] = []
        except Exception as e:
            state["errors"].append(f"Retry failed: {str(e)}")
    
    return state


def normalize_result_node(state: ExtractionState) -> ExtractionState:
    """결과 정규화 노드"""
    if state.get("parsed_json") and not state.get("final_result"):
        # 파싱은 성공했지만 검증 실패한 경우 정규화하여 반환
        normalized = normalize(state["parsed_json"])
        errors = state.get("errors", [])
        if errors:
            normalized["meta"]["notes"] = (
                (normalized["meta"]["notes"] or "") + 
                f" | SCHEMA_INVALID: {errors[:3]}"
            )[:300]
        state["final_result"] = normalized
        state["confidence"] = normalized.get("confidence", 0.2)
    elif not state.get("final_result"):
        # 모든 시도 실패 시 기본값 반환
        out = copy.deepcopy(DEFAULT_OBJ)
        out["meta"]["notes"] = "All extraction attempts failed"
        state["final_result"] = out
        state["confidence"] = 0.1
    
    return state


def should_retry(state: ExtractionState) -> str:
    """재시도 여부 결정"""
    if state.get("final_result"):
        return "end"
    if state.get("retry_count", 0) >= 1:
        return "normalize"
    if state.get("errors") and not state.get("final_result"):
        return "retry"
    return "normalize"
