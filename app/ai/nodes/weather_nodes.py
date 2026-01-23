"""
날씨 관련 LangGraph 노드
"""
import logging
from datetime import datetime
from app.ai.schemas.workflow_state import RecommendationState
from app.ai.clients.azure_openai_client import azure_openai_client
from app.ai.prompts.weather_prompts import build_weather_extraction_prompt_with_context
from app.services.weather import weather_service
from app.utils.json_parser import parse_dict_from_text

logger = logging.getLogger(__name__)


def extract_weather_query_node(state: RecommendationState) -> RecommendationState:
    """
    사용자 입력에서 날씨 관련 정보 추출 노드
    
    LLM을 사용하여 region_text, target_date, missing을 추출
    """
    new_state = dict(state)
    user_request = state.get("user_request")
    
    if not user_request:
        logger.info("No user_request, skipping weather extraction")
        new_state["weather_query"] = None
        return new_state
    
    try:
        # 현재 날짜 가져오기
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # 프롬프트 생성
        prompt = build_weather_extraction_prompt_with_context(user_request, current_date)
        
        logger.info("Extracting weather query from user request...")
        response_text = azure_openai_client.generate_content(
            prompt,
            temperature=0.3,
            max_tokens=200
        )
        
        # JSON 파싱
        parsed, _ = parse_dict_from_text(response_text)
        
        if parsed and isinstance(parsed, dict):
            weather_query = {
                "region_text": parsed.get("region_text"),
                "target_date": parsed.get("target_date"),
                "missing": parsed.get("missing", [])
            }
            new_state["weather_query"] = weather_query
            logger.info(f"Weather query extracted: {weather_query}")
        else:
            logger.warning("Failed to parse weather query from LLM response")
            new_state["weather_query"] = None
            
    except Exception as e:
        logger.error(f"Error extracting weather query: {str(e)}", exc_info=True)
        new_state["weather_query"] = None
    
    return new_state


def normalize_region_node(state: RecommendationState) -> RecommendationState:
    """
    지역명 정규화 및 regId 매핑 노드
    """
    new_state = dict(state)
    weather_query = state.get("weather_query")
    
    if not weather_query or not weather_query.get("region_text"):
        logger.info("No region_text in weather_query, skipping region normalization")
        return new_state
    
    try:
        region_text = weather_query["region_text"]
        logger.info(f"Normalizing region: {region_text}")
        
        # weather_service를 사용하여 지역 해결
        result = weather_service.resolve_region(region_text)
        
        # 결과를 state에 저장
        new_state["weather_query"] = {
            **weather_query,
            "region_canonical": result["region_canonical"],
            "regId": result["regId"],
            "needs_disambiguation": result["needs_disambiguation"]
        }
        
        # clarifying_question 설정
        if result["needs_disambiguation"]:
            new_state["clarifying_question"] = result["clarifying_question"]
            logger.info(f"Region needs disambiguation: {result['clarifying_question']}")
        else:
            # 이전 clarifying_question이 있으면 제거
            if "clarifying_question" in new_state:
                new_state["clarifying_question"] = None
        
        logger.info(f"Region normalized: {result}")
        
    except Exception as e:
        logger.error(f"Error normalizing region: {str(e)}", exc_info=True)
    
    return new_state


def select_tmfc_node(state: RecommendationState) -> RecommendationState:
    """
    tmFc 선택 노드 및 중기예보 범위 확인
    """
    new_state = dict(state)
    weather_query = state.get("weather_query")
    
    if not weather_query or not weather_query.get("target_date"):
        logger.info("No target_date in weather_query, skipping tmFc selection")
        return new_state
    
    try:
        target_date = weather_query["target_date"]
        
        # 중기예보 범위 확인
        range_check = weather_service.check_weather_range(target_date)
        
        if not range_check["in_range"]:
            # 범위 밖이면 metadata에 이유 저장하고 날씨 없이 진행
            metadata = new_state.get("metadata", {})
            metadata["weather_unavailable_reason"] = range_check["reason"]
            new_state["metadata"] = metadata
            logger.info(f"Weather unavailable: {range_check['reason']}")
            return new_state
        
        # tmFc 선택
        tmFc = weather_service.select_tmfc(target_date)
        
        if tmFc:
            new_state["weather_query"] = {
                **weather_query,
                "tmFc": tmFc
            }
            logger.info(f"tmFc selected: {tmFc}")
        else:
            # tmFc를 찾을 수 없으면 metadata에 이유 저장
            metadata = new_state.get("metadata", {})
            metadata["weather_unavailable_reason"] = "해당 날짜에 대한 예보를 찾을 수 없습니다"
            new_state["metadata"] = metadata
            logger.warning(f"Could not find tmFc for target_date: {target_date}")
        
    except Exception as e:
        logger.error(f"Error selecting tmFc: {str(e)}", exc_info=True)
        metadata = new_state.get("metadata", {})
        metadata["weather_unavailable_reason"] = f"tmFc 선택 중 오류: {str(e)}"
        new_state["metadata"] = metadata
    
    return new_state


def fetch_weather_node(state: RecommendationState) -> RecommendationState:
    """
    날씨 API 호출 노드
    """
    new_state = dict(state)
    weather_query = state.get("weather_query")
    
    if not weather_query:
        logger.info("No weather_query, skipping weather fetch")
        return new_state
    
    regId = weather_query.get("regId")
    tmFc = weather_query.get("tmFc")
    
    if not regId or not tmFc:
        logger.info("Missing regId or tmFc, skipping weather fetch")
        return new_state
    
    try:
        logger.info(f"Fetching weather: regId={regId}, tmFc={tmFc}")
        response = weather_service.fetch_weather(regId=regId, tmFc=tmFc)
        
        # 응답을 state에 저장
        new_state["weather_query"] = {
            **weather_query,
            "api_response": response
        }
        logger.info("Weather API response received")
        
    except Exception as e:
        logger.error(f"Error fetching weather: {str(e)}", exc_info=True)
        # API 호출 실패 시 metadata에 저장하고 날씨 없이 진행
        metadata = new_state.get("metadata", {})
        metadata["weather_unavailable_reason"] = f"날씨 API 호출 실패: {str(e)}"
        new_state["metadata"] = metadata
    
    return new_state


def parse_weather_node(state: RecommendationState) -> RecommendationState:
    """
    날씨 API 응답 파싱 노드
    """
    new_state = dict(state)
    weather_query = state.get("weather_query")
    
    if not weather_query:
        logger.info("No weather_query, skipping weather parsing")
        return new_state
    
    api_response = weather_query.get("api_response")
    target_date = weather_query.get("target_date")
    region_canonical = weather_query.get("region_canonical")
    tmFc = weather_query.get("tmFc")
    
    if not api_response or not target_date or not region_canonical or not tmFc:
        logger.info("Missing required fields for weather parsing")
        return new_state
    
    try:
        logger.info("Parsing weather response...")
        weather_info = weather_service.parse_weather_response(
            response=api_response,
            target_date=target_date,
            region_canonical=region_canonical,
            tmFc=tmFc
        )
        
        if weather_info:
            new_state["weather_info"] = weather_info
            logger.info(f"Weather info parsed: {weather_info}")
        else:
            logger.warning("Failed to parse weather info from API response")
            metadata = new_state.get("metadata", {})
            metadata["weather_unavailable_reason"] = "날씨 정보 파싱 실패"
            new_state["metadata"] = metadata
        
    except Exception as e:
        logger.error(f"Error parsing weather: {str(e)}", exc_info=True)
        metadata = new_state.get("metadata", {})
        metadata["weather_unavailable_reason"] = f"날씨 정보 파싱 중 오류: {str(e)}"
        new_state["metadata"] = metadata
    
    return new_state


def should_fetch_weather(state: RecommendationState) -> str:
    """
    날씨 정보를 가져올지 결정하는 조건부 엣지 함수
    
    기준: region_text와 target_date가 둘 다 있어야 함
    """
    weather_query = state.get("weather_query")
    
    if not weather_query:
        return "skip"
    
    region_text = weather_query.get("region_text")
    target_date = weather_query.get("target_date")
    
    # 둘 다 있으면 날씨 정보 가져오기
    if region_text and target_date:
        return "fetch"
    
    # 하나라도 없으면 건너뛰기
    return "skip"


def should_continue_after_normalize(state: RecommendationState) -> str:
    """
    지역 정규화 후 계속 진행할지 결정
    
    needs_disambiguation이 True이면 clarifying_question 반환하고 종료
    """
    weather_query = state.get("weather_query")
    
    if not weather_query:
        return "continue"
    
    needs_disambiguation = weather_query.get("needs_disambiguation", False)
    
    if needs_disambiguation:
        return "clarify"  # clarifying_question 반환하고 종료
    else:
        return "continue"  # 계속 진행
