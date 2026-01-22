"""
이미지 속성 추출 LangGraph 노드
"""
import copy
import logging
from typing import Dict, Any
from app.ai.schemas.workflow_state import ExtractionState
from app.ai.clients.azure_openai_client import azure_openai_client
from app.ai.prompts.extraction_prompts import USER_PROMPT, DEFAULT_OBJ, build_retry_prompt
from app.utils.json_parser import parse_json_from_text
from app.utils.validators import validate_schema
from app.utils.helpers import normalize

logger = logging.getLogger(__name__)


def preprocess_image_node(state: ExtractionState) -> ExtractionState:
    """이미지 전처리 노드"""
    # 이미지는 이미 bytes로 들어오므로 추가 전처리 없음
    # 필요시 여기서 이미지 검증 등 수행
    return state


def call_azure_openai_node(state: ExtractionState) -> ExtractionState:
    """Azure OpenAI Vision API 호출 노드"""
    try:
        logger.info("Calling Azure OpenAI Vision API...")
        raw_response = azure_openai_client.generate_with_vision(
            prompt=USER_PROMPT,
            image_bytes=state["image_bytes"],
            temperature=0.3,
            max_tokens=2000
        )
        if not raw_response or not raw_response.strip():
            logger.warning("Azure OpenAI returned empty response")
            state["raw_response"] = None
            state["errors"].append("Empty response from API")
        else:
            logger.info(f"API response received (length: {len(raw_response)})")
            state["raw_response"] = raw_response
            state["errors"] = []
    except Exception as e:
        # API 호출 실패 시 에러만 저장하고 final_result는 설정하지 않음
        # (나중에 normalize_result_node에서 처리)
        logger.error(f"Azure OpenAI API call failed: {str(e)}", exc_info=True)
        state["raw_response"] = None
        state["errors"].append(f"API call failed: {str(e)}")
    return state


def parse_json_node(state: ExtractionState) -> ExtractionState:
    """JSON 파싱 노드"""
    if state.get("raw_response"):
        logger.info("Parsing JSON from response...")
        parsed, repaired = parse_json_from_text(state["raw_response"])
        state["parsed_json"] = parsed
        if parsed is None:
            logger.warning(f"JSON parsing failed. Repaired text head: {repaired[:160]}")
            state["errors"].append(f"JSON parsing failed. Response preview: {state['raw_response'][:200]}")
        else:
            logger.info("JSON parsing successful")
    else:
        logger.warning("No raw_response to parse")
    return state


def validate_schema_node(state: ExtractionState) -> ExtractionState:
    """스키마 검증 노드"""
    if state.get("parsed_json"):
        logger.info("Validating schema...")
        ok, errs = validate_schema(state["parsed_json"])
        if ok:
            # 검증 성공 - 정규화 후 최종 결과 설정
            logger.info("Schema validation successful")
            normalized = normalize(state["parsed_json"])
            state["final_result"] = normalized
            state["confidence"] = normalized.get("confidence", 0.5)
        else:
            # 검증 실패 - 에러 저장
            logger.warning(f"Schema validation failed: {errs[:3]}")
            state["errors"] = errs
    else:
        logger.warning("No parsed_json to validate")
    return state


def retry_node(state: ExtractionState) -> ExtractionState:
    """재시도 노드"""
    if state.get("retry_count", 0) >= 1:
        # 이미 재시도했으면 더 이상 재시도하지 않음
        logger.info("Already retried, skipping retry")
        return state
    
    if state.get("errors") and not state.get("final_result"):
        # 에러가 있고 최종 결과가 없으면 재시도
        logger.info(f"Retrying with errors: {state['errors'][:2]}")
        retry_prompt = build_retry_prompt(state["errors"])
        try:
            raw_response = azure_openai_client.generate_with_vision(
                prompt=retry_prompt,
                image_bytes=state["image_bytes"],
                temperature=0.2,
                max_tokens=2000
            )
            if not raw_response or not raw_response.strip():
                logger.warning("Retry returned empty response")
                state["raw_response"] = None
                state["errors"].append("Empty response from retry API call")
            else:
                logger.info(f"Retry response received (length: {len(raw_response)})")
                state["raw_response"] = raw_response
                state["retry_count"] = state.get("retry_count", 0) + 1
                state["errors"] = []  # 재시도 시 에러 초기화
        except Exception as e:
            logger.error(f"Retry API call failed: {str(e)}", exc_info=True)
            state["errors"].append(f"Retry failed: {str(e)}")
    else:
        logger.info("No retry needed (no errors or final_result exists)")
    
    return state


def normalize_result_node(state: ExtractionState) -> ExtractionState:
    """결과 정규화 노드"""
    if state.get("final_result"):
        # 이미 최종 결과가 있으면 그대로 반환
        logger.info("Final result already exists, skipping normalization")
        return state
    
    if state.get("parsed_json"):
        # 파싱은 성공했지만 검증 실패한 경우 정규화하여 반환
        logger.info("Normalizing parsed JSON (schema validation may have failed)")
        normalized = normalize(state["parsed_json"])
        errors = state.get("errors", [])
        if errors:
            normalized["meta"]["notes"] = (
                (normalized["meta"]["notes"] or "") + 
                f" | SCHEMA_INVALID: {', '.join(errors[:3])}"
            )[:300]
        state["final_result"] = normalized
        state["confidence"] = normalized.get("confidence", 0.2)
        logger.info(f"Normalized result with confidence: {state['confidence']}")
    else:
        # 모든 시도 실패 시 기본값 반환
        logger.error(f"All extraction attempts failed. Errors: {state.get('errors', [])}")
        logger.error(f"State: raw_response={'exists' if state.get('raw_response') else 'None'}, "
                    f"parsed_json={'exists' if state.get('parsed_json') else 'None'}, "
                    f"retry_count={state.get('retry_count', 0)}")
        out = copy.deepcopy(DEFAULT_OBJ)
        error_summary = "; ".join(state.get("errors", [])[:3]) if state.get("errors") else "Unknown error"
        out["meta"]["notes"] = f"All extraction attempts failed: {error_summary}"
        state["final_result"] = out
        state["confidence"] = 0.1
    
    return state


def should_retry(state: ExtractionState) -> str:
    """재시도 여부 결정"""
    if state.get("final_result"):
        logger.info("Final result exists, going to normalize")
        return "end"  # "end"는 워크플로우에서 "normalize"로 매핑됨
    if state.get("retry_count", 0) >= 1:
        logger.info("Already retried, going to normalize")
        return "normalize"
    if state.get("errors") and not state.get("final_result"):
        logger.info("Errors exist and no final result, going to retry")
        return "retry"
    logger.info("No errors or already processed, going to normalize")
    return "normalize"
