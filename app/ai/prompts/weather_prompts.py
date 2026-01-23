"""
날씨 정보 추출 프롬프트
"""
import json
from typing import Optional


def build_weather_extraction_prompt(user_request: str) -> str:
    """
    사용자 요청에서 날씨 관련 정보 추출 프롬프트 생성
    
    LLM은 오직 추출만 수행:
    - region_text: 원문 그대로 (예: "서울", "수원", "강원도")
    - target_date: YYYY-MM-DD 형식 또는 null
    - missing: 누락된 필드 배열
    
    절대 시키지 말 것:
    - regId 추측
    - tmFc 계산
    - 예보 범위 판단
    
    Args:
        user_request: 사용자 요청 텍스트
    
    Returns:
        프롬프트 문자열
    """
    return f"""사용자의 요청에서 날씨 정보를 추출하세요.

사용자 요청: {user_request}

다음 정보를 추출하세요:
1. region_text: 지역명 (원문 그대로, 예: "서울", "수원", "강원도", "부산")
2. target_date: 날짜 (YYYY-MM-DD 형식, 없으면 null)
3. missing: 누락된 필드 배열 (예: ["region"], ["date"], ["region", "date"], [])

중요:
- region_text는 사용자가 말한 그대로 추출 (변환하지 않음)
- target_date는 "내일", "모레", "3일 후" 등을 현재 날짜 기준으로 계산하여 YYYY-MM-DD 형식으로 변환
- 날짜가 명시되지 않았으면 null
- region_text와 target_date가 모두 있으면 missing은 []
- 하나라도 없으면 missing에 해당 필드명 추가

JSON 형식으로 반환:
{{
  "region_text": "서울" 또는 null,
  "target_date": "2026-01-28" 또는 null,
  "missing": ["region"] 또는 ["date"] 또는 ["region", "date"] 또는 []
}}

JSON만 반환하세요. 설명이나 마크다운 코드 블록 없이 순수 JSON만."""


def build_weather_extraction_prompt_with_context(user_request: str, current_date: str) -> str:
    """
    현재 날짜 컨텍스트를 포함한 날씨 정보 추출 프롬프트
    
    Args:
        user_request: 사용자 요청 텍스트
        current_date: 현재 날짜 (YYYY-MM-DD 형식)
    
    Returns:
        프롬프트 문자열
    """
    return f"""사용자의 요청에서 날씨 정보를 추출하세요.

현재 날짜: {current_date}
사용자 요청: {user_request}

다음 정보를 추출하세요:
1. region_text: 지역명 (원문 그대로, 예: "서울", "수원", "강원도", "부산")
2. target_date: 날짜 (YYYY-MM-DD 형식, 없으면 null)
3. missing: 누락된 필드 배열 (예: ["region"], ["date"], ["region", "date"], [])

중요:
- region_text는 사용자가 말한 그대로 추출 (변환하지 않음)
- target_date는 "내일", "모레", "3일 후" 등을 현재 날짜({current_date}) 기준으로 계산하여 YYYY-MM-DD 형식으로 변환
- 날짜가 명시되지 않았으면 null
- region_text와 target_date가 모두 있으면 missing은 []
- 하나라도 없으면 missing에 해당 필드명 추가

JSON 형식으로 반환:
{{
  "region_text": "서울" 또는 null,
  "target_date": "2026-01-28" 또는 null,
  "missing": ["region"] 또는 ["date"] 또는 ["region", "date"] 또는 []
}}

JSON만 반환하세요. 설명이나 마크다운 코드 블록 없이 순수 JSON만."""
