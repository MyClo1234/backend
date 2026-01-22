"""
레거시 상수 파일 - 더 이상 사용되지 않음

이 파일의 모든 상수는 app/ai/prompts/extraction_prompts.py로 이동되었습니다.
하위 호환성을 위해 이 파일은 유지되지만, 새로운 코드에서는 extraction_prompts.py를 사용해야 합니다.

DEPRECATED: 이 파일은 향후 제거될 예정입니다.
"""

# 하위 호환성을 위한 재export
from app.ai.prompts.extraction_prompts import (
    ENUMS,
    ALIASES,
    REQUIRED_TOP_KEYS,
    DEFAULT_OBJ,
    SYSTEM_PROMPT,
    USER_PROMPT,
)

__all__ = [
    "ENUMS",
    "ALIASES",
    "REQUIRED_TOP_KEYS",
    "DEFAULT_OBJ",
    "SYSTEM_PROMPT",
    "USER_PROMPT",
]
