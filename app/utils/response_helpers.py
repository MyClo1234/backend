"""
공용 응답 헬퍼 함수
라우터에서 반복되는 예외 처리 및 응답 패턴을 통합
"""
from typing import Any, Dict, Optional
from fastapi import HTTPException


def create_success_response(data: Any, **kwargs) -> Dict[str, Any]:
    """
    성공 응답 생성
    
    Args:
        data: 응답 데이터
        **kwargs: 추가 필드 (예: count, method, message 등)
        
    Returns:
        성공 응답 딕셔너리
    """
    response = {"success": True}
    if isinstance(data, dict):
        response.update(data)
    else:
        response["data"] = data
    response.update(kwargs)
    return response


def handle_route_exception(e: Exception) -> HTTPException:
    """
    라우터 예외 처리
    
    Args:
        e: 발생한 예외
        
    Returns:
        HTTPException
    """
    if isinstance(e, HTTPException):
        return e
    return HTTPException(status_code=500, detail=str(e))
