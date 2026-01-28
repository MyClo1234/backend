import logging
from typing import Dict, Any
from app.ai.workflows.extraction_workflow import extract_attributes

logger = logging.getLogger(__name__)


class AttributeExtractor:
    """
    이미지 속성 추출 서비스

    내부적으로 LangGraph 워크플로우를 사용하여 이미지에서 의류 속성을 추출합니다.
    """

    async def extract(
        self, image_bytes: bytes, retry_on_schema_fail: bool = True
    ) -> Dict[str, Any]:
        """
        이미지에서 의류 속성 추출

        Args:
            image_bytes: 이미지 바이트 데이터
            retry_on_schema_fail: 스키마 검증 실패 시 재시도 여부

        Returns:
            추출된 속성 딕셔너리 (신뢰도 포함)
        """
        # 기존 워크플로우를 사용하되, 결과가 항상 신뢰도를 포함하도록 보장하거나
        # 필요 시 여기서 직접 azure_openai_client를 호출하도록 변경 가능합니다.
        # 현재는 기존 워크플로우가 이미 신뢰도를 포함한 구조를 반환하므로 이를 활용합니다.
        # 다만, 가독성과 유지보수를 위해 향후 여기서 직접 호출로 단순화할 수 있습니다.
        logger.info("Extracting attributes with confidence scores...")
        return await extract_attributes(
            image_bytes, retry_on_schema_fail=retry_on_schema_fail
        )


# 싱글톤 인스턴스 (하위 호환성 유지)
extractor = AttributeExtractor()
