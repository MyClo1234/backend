"""
LangSmith tracing 설정 헬퍼 모듈
"""
import os
from typing import Optional, Dict, Any


def get_langsmith_config(
    project_name: str = "backend-workflows",
    tags: Optional[list] = None,
    metadata: Optional[Dict[str, Any]] = None,
    thread_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    LangSmith tracing 설정 반환
    
    Args:
        project_name: LangSmith 프로젝트 이름
        tags: 추가 태그 리스트
        metadata: 추가 메타데이터 딕셔너리
        thread_id: 스레드 ID (고유 실행 추적용)
    
    Returns:
        LangGraph config 딕셔너리 (tracing 비활성화 시 빈 딕셔너리)
    """
    from app.core.config import Config

    api_key = Config.LANGCHAIN_API_KEY
    tracing_enabled = Config.LANGCHAIN_TRACING_V2

    if not tracing_enabled or not api_key:
        return {}

    # 프로젝트 이름 설정
    if project_name:
        os.environ["LANGCHAIN_PROJECT"] = project_name

    config = {
        "configurable": {
            "thread_id": thread_id or "default",
        },
    }

    if tags:
        config["tags"] = tags

    if metadata:
        config["metadata"] = metadata

    return config
