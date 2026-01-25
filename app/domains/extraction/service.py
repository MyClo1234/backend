"""
이미지 속성 추출 서비스 (LangGraph 워크플로우 래퍼)
"""
from typing import Dict, Any
from app.ai.workflows.extraction_workflow import extract_attributes


class AttributeExtractor:
    """
    이미지 속성 추출 서비스
    
    내부적으로 LangGraph 워크플로우를 사용하여 이미지에서 의류 속성을 추출합니다.
    """
    
    def extract(self, image_bytes: bytes, retry_on_schema_fail: bool = True) -> Dict[str, Any]:
        """
        이미지에서 의류 속성 추출
        
        Args:
            image_bytes: 이미지 바이트 데이터
            retry_on_schema_fail: 스키마 검증 실패 시 재시도 여부 (현재는 항상 True)
        
        Returns:
            추출된 속성 딕셔너리
        """
        # LangGraph 워크플로우 호출
        return extract_attributes(image_bytes, retry_on_schema_fail=retry_on_schema_fail)


# 싱글톤 인스턴스 (하위 호환성 유지)
extractor = AttributeExtractor()
