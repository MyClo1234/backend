"""
코디 추천 프롬프트 템플릿
"""

import json
from typing import List, Dict, Any


def build_recommendation_prompt(
    tops_summary: List[Dict[str, Any]],
    bottoms_summary: List[Dict[str, Any]],
    count: int = 1,
) -> str:
    """기본 상/하의 조합 추천 (단순 버전)"""
    return f"""Recommend {count} best outfit(s) from these pre-filtered combinations.

Tops: {json.dumps(tops_summary, ensure_ascii=False)}
Bottoms: {json.dumps(bottoms_summary, ensure_ascii=False)}

Consider color harmony, style match, formality balance.

Return JSON array with {count} object(s):
{{
  "top_id": "string",
  "bottom_id": "string",
  "score": 0.0-1.0,
  "reasoning": "한국어 100자 이내",
  "style_description": "한국어 50자 이내"
}}

JSON only, no markdown, no code blocks."""


def build_tpo_recommendation_prompt(
    user_request: str,
    weather_info: Dict[str, Any],
    tops_summary: List[Dict[str, Any]],  # 원본 인자 유지
    bottoms_summary: List[Dict[str, Any]],  # 원본 인자 유지
    outer_summary: List[Dict[str, Any]] = None,  # 아우터 추가 (선택사항)
    count: int = 1,
) -> str:
    """
    원본의 인자 구조를 유지하면서 상세 속성(소재, 레이어링 등) 로직을 결합한 버전
    """

    # 데이터를 AI가 읽기 좋게 카테고리별로 묶어줌
    wardrobe_context = {
        "top": tops_summary,
        "bottom": bottoms_summary,
        "outer": outer_summary if outer_summary else [],
    }

    weather_text = ""
    if weather_info:
        weather_text = f"""
Current Weather:
- Temp: {weather_info.get('temperature', 'N/A')}°C
- Condition: {weather_info.get('condition', 'N/A')}
- Precipitation: {weather_info.get('precipitation', 'N/A')}
"""

    return f"""Recommend {count} outfit(s) based on the context.

[Context]
User Request: {user_request}
{weather_text}

[Available Items]
{json.dumps(wardrobe_context, ensure_ascii=False)}

[Styling Rules]
1. Weather: Combine 'scores.warmth' and 'thickness' to match the Temp. 
2. Safety: If precipitation is not "none", avoid "suede", "silk", "leather".
3. Layering: Follow 'meta.layering_rank' (1:Inner, 2:Mid, 3:Outer).
4. Category: Must include (1 Top + 1 Bottom). Add 1 Outer if Temp < 15°C.

Return ONLY a JSON array of {count} objects:
{{
  "outfit_id": "outfit_n",
  "combination": {{
    "outer_id": "string|null",
    "top_id": "string",
    "bottom_id": "string"
  }},
  "score": 0.0-1.0,
  "reasoning": "한국어 100자 이내 (날씨/TPO/소재 고려)",
  "style_description": "한국어 50자 이내"
}}

JSON only, no markdown."""


def build_todays_pick_prompt(
    weather_summary: str,
    temp_min: float,
    temp_max: float,
    tops_list: str,
    bottoms_list: str,
    context: str = "특별한 요청 없음",
) -> str:
    """Today's Pick 전용 프롬프트 (v2 style)"""
    return f"""당신은 전문 패션 스타일리스트입니다.
오늘 날씨와 사용자의 옷장, 그리고 사용자의 특별한 요청사항을 고려하여 최적의 코디를 추천해주세요.

**날씨 정보:**
- 날씨: {weather_summary}
- 최저/최고 기온: {temp_min}°C ~ {temp_max}°C

**상의 목록:**
{tops_list}

**하의 목록:**
{bottoms_list}

**사용자 요청 및 문맥:**
{context}

반드시 다음 JSON 형식으로만 응답하세요 (다른 텍스트 출력 금지):
{{
  "top_id": "선택한 상의 ID",
  "bottom_id": "선택한 하의 ID",  
  "reasoning": "이 조합을 선택한 이유 (한국어, 2-3문장)",
  "score": 0.0~1.0 사이의 추천 신뢰도
}}

규칙:
- 사용자 요청 및 문맥(TPO 등)을 최우선으로 반영
- 문맥에 "이전에 추천한 조합은 제외"라는 지시가 있으면, 해당 상의 ID와 하의 ID 조합을 절대 선택하지 마세요. 반드시 다른 상의나 하의를 선택해야 합니다.
- 사용자가 "다른 옷", "다시 추천", "새로운 코디" 등을 요청한 경우, 이전 추천과는 다른 조합을 선택하세요.
- 날씨에 적합한 보온성/통풍성 고려
- 색상 조화 및 스타일 통일성 유지
- 가능한 한 다양한 옷 조합을 추천하세요 (같은 옷만 반복 추천하지 마세요)
- JSON만 출력, 마크다운 코드블록(```) 사용 금지
"""
