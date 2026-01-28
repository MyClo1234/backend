import logging
import json
import copy
from typing import Dict, Any
from app.ai.clients.azure_openai_client import azure_openai_client
from app.ai.prompts.extraction_prompts import (
    USER_PROMPT,
    DEFAULT_OBJ,
    build_retry_prompt,
)
from app.utils.json_parser import parse_dict_from_text
from app.utils.validators import validate_schema
from app.utils.helpers import normalize

logger = logging.getLogger(__name__)


async def extract_attributes(
    image_bytes: bytes, retry_on_schema_fail: bool = True
) -> Dict[str, Any]:
    """
    이미지 속성 추출 (Direct LLM Call)

    Args:
        image_bytes: 이미지 바이트 데이터
        retry_on_schema_fail: 스키마 검증 실패 시 재시도 여부

    Returns:
        추출된 속성 딕셔너리
    """
    logger.info(
        f"Starting direct attribute extraction (image size: {len(image_bytes)} bytes)"
    )

    try:
        # 1. 1차 시도
        logger.info("Calling Azure OpenAI Vision API (Attempt 1)...")
        raw_response = await azure_openai_client.generate_with_vision(
            prompt=USER_PROMPT,
            image_bytes=image_bytes,
            temperature=0.3,
            max_tokens=2000,
        )

        if not raw_response:
            raise ValueError("Empty response from Azure OpenAI")

        # 2. JSON 파싱
        parsed, _ = parse_dict_from_text(raw_response)

        # 3. 검증 및 재시도
        if parsed is not None:
            ok, errors = validate_schema(parsed)
            if ok:
                logger.info("Extraction successful on first attempt")
                return normalize(parsed)

            logger.warning(f"Schema validation failed on first attempt: {errors[:2]}")
            if retry_on_schema_fail:
                logger.info("Retrying with correction prompt...")
                retry_prompt = build_retry_prompt(errors)
                raw_response = await azure_openai_client.generate_with_vision(
                    prompt=retry_prompt,
                    image_bytes=image_bytes,
                    temperature=0.2,
                    max_tokens=2000,
                )
                parsed, _ = parse_dict_from_text(raw_response)
                if parsed:
                    logger.info("Extraction successful on retry")
                    return normalize(parsed)

        # 4. 폴백: 부분적인 데이터라도 반환
        if parsed:
            logger.warning(
                "Returning partially valid or normalized data after failed validation"
            )
            return normalize(parsed)

    except Exception as e:
        logger.error(f"Extraction failed: {str(e)}", exc_info=True)

    # 최종 폴백: 기본값 반환
    logger.error("Returning default object due to total failure")
    out = copy.deepcopy(DEFAULT_OBJ)
    out["meta"]["notes"] = "Extraction failed - default returned"
    return out
