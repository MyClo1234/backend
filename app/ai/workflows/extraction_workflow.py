"""
이미지 속성 추출 LangGraph 워크플로우
"""
import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from app.ai.schemas.workflow_state import ExtractionState
from app.ai.nodes.extraction_nodes import (
    preprocess_image_node,
    call_azure_openai_node,
    parse_json_node,
    validate_schema_node,
    retry_node,
    normalize_result_node,
    should_retry
)

logger = logging.getLogger(__name__)


def create_extraction_workflow() -> StateGraph:
    """이미지 속성 추출 워크플로우 생성"""
    workflow = StateGraph(ExtractionState)
    
    # 노드 추가
    workflow.add_node("preprocess", preprocess_image_node)
    workflow.add_node("call_api", call_azure_openai_node)
    workflow.add_node("parse_json", parse_json_node)
    workflow.add_node("validate", validate_schema_node)
    workflow.add_node("retry", retry_node)
    workflow.add_node("normalize", normalize_result_node)
    
    # 엣지 정의
    workflow.set_entry_point("preprocess")
    workflow.add_edge("preprocess", "call_api")
    workflow.add_edge("call_api", "parse_json")
    workflow.add_edge("parse_json", "validate")
    
    # 조건부 엣지: 검증 결과에 따라 분기
    workflow.add_conditional_edges(
        "validate",
        should_retry,
        {
            "end": "normalize",  # 검증 성공 시 정규화 후 종료
            "retry": "retry",    # 재시도 필요
            "normalize": "normalize"  # 정규화 후 종료
        }
    )
    
    workflow.add_edge("retry", "parse_json")  # 재시도 후 다시 파싱
    workflow.add_edge("normalize", END)
    
    return workflow.compile()


# 싱글톤 워크플로우 인스턴스
_extraction_workflow = None


def get_extraction_workflow() -> StateGraph:
    """이미지 속성 추출 워크플로우 인스턴스 반환"""
    global _extraction_workflow
    if _extraction_workflow is None:
        _extraction_workflow = create_extraction_workflow()
    return _extraction_workflow


def extract_attributes(image_bytes: bytes, retry_on_schema_fail: bool = True) -> Dict[str, Any]:
    """
    이미지 속성 추출 (기존 인터페이스 유지)
    
    Args:
        image_bytes: 이미지 바이트 데이터
        retry_on_schema_fail: 스키마 검증 실패 시 재시도 여부
    
    Returns:
        추출된 속성 딕셔너리
    """
    logger.info(f"Starting attribute extraction (image size: {len(image_bytes)} bytes)")
    
    # 초기 상태 설정
    initial_state: ExtractionState = {
        "image_bytes": image_bytes,
        "raw_response": None,
        "parsed_json": None,
        "errors": [],
        "retry_count": 0,
        "final_result": None,
        "confidence": 0.0
    }
    
    # 워크플로우 실행
    try:
        workflow = get_extraction_workflow()
        logger.info("Invoking extraction workflow...")
        final_state = workflow.invoke(initial_state)
        logger.info("Workflow execution completed")
    except Exception as e:
        logger.error(f"Workflow execution failed: {str(e)}", exc_info=True)
        from app.ai.prompts.extraction_prompts import DEFAULT_OBJ
        import copy
        out = copy.deepcopy(DEFAULT_OBJ)
        out["meta"]["notes"] = f"Workflow execution failed: {str(e)}"
        return out
    
    # 최종 결과 반환
    if final_state.get("final_result"):
        logger.info(f"Extraction successful (confidence: {final_state.get('confidence', 0)})")
        return final_state["final_result"]
    else:
        # 폴백: 기본값 반환
        logger.error("No final result from workflow")
        logger.error(f"Final state: errors={final_state.get('errors', [])}, "
                    f"raw_response={'exists' if final_state.get('raw_response') else 'None'}, "
                    f"parsed_json={'exists' if final_state.get('parsed_json') else 'None'}")
        from app.ai.prompts.extraction_prompts import DEFAULT_OBJ
        import copy
        out = copy.deepcopy(DEFAULT_OBJ)
        out["meta"]["notes"] = "Workflow execution failed - no final result"
        return out
