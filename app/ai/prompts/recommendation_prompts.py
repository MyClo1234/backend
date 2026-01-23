"""
코디 추천 프롬프트 템플릿
"""
import json
from typing import List, Dict, Any


def build_recommendation_prompt(
    tops_summary: List[Dict[str, Any]],
    bottoms_summary: List[Dict[str, Any]],
    count: int = 1
) -> str:
    """
    코디 추천 프롬프트 생성
    
    Args:
        tops_summary: 상의 요약 정보 리스트
        bottoms_summary: 하의 요약 정보 리스트
        count: 추천할 코디 개수
    
    Returns:
        프롬프트 문자열
    """
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
    tops_summary: List[Dict[str, Any]],
    bottoms_summary: List[Dict[str, Any]],
    count: int = 1
) -> str:
    """
    TPO(Time, Place, Occasion)를 고려한 코디 추천 프롬프트 생성
    
    Args:
        user_request: 사용자 요청 (예: "격식 있는 저녁 식사")
        weather_info: 날씨 정보
        tops_summary: 상의 요약 정보 리스트
        bottoms_summary: 하의 요약 정보 리스트
        count: 추천할 코디 개수
    
    Returns:
        프롬프트 문자열
    """
    weather_text = ""
    if weather_info:
        # 확장된 weather_info 포맷 지원
        # {source, region, date, temperature: {min, max}, delta_days}
        temp_info = weather_info.get('temperature', {})
        if isinstance(temp_info, dict):
            min_temp = temp_info.get('min', 'N/A')
            max_temp = temp_info.get('max', 'N/A')
            temp_str = f"{min_temp}°C ~ {max_temp}°C" if min_temp != 'N/A' and max_temp != 'N/A' else 'N/A'
        else:
            temp_str = str(temp_info)
        
        region = weather_info.get('region', 'N/A')
        date = weather_info.get('date', 'N/A')
        source = weather_info.get('source', 'N/A')
        delta_days = weather_info.get('delta_days')
        
        delta_text = f" ({delta_days}일 후 예보)" if delta_days is not None else ""
        
        weather_text = f"""
Weather Information:
- Source: {source}{delta_text}
- Region: {region}
- Date: {date}
- Temperature: {temp_str}
"""
    
    return f"""Recommend {count} best outfit(s) based on the user's request and current weather.

User Request: {user_request}
{weather_text}
Available Tops: {json.dumps(tops_summary, ensure_ascii=False)}
Available Bottoms: {json.dumps(bottoms_summary, ensure_ascii=False)}

Consider:
- User's request (TPO: Time, Place, Occasion)
- Weather appropriateness
- Color harmony
- Style match
- Formality balance

Return JSON array with {count} object(s):
{{
  "top_id": "string",
  "bottom_id": "string",
  "score": 0.0-1.0,
  "reasoning": "한국어 100자 이내 - 날씨와 TPO를 고려한 추천 이유",
  "style_description": "한국어 50자 이내"
}}

JSON only, no markdown, no code blocks."""
