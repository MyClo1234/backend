"""
날씨 API 응답 파싱 및 정규화
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class WeatherParser:
    """날씨 API 응답을 파싱하고 정규화하는 클래스"""
    
    @staticmethod
    def parse_mid_ta_response(
        response: Dict[str, Any],
        target_date: str,
        region_canonical: str,
        tmFc: str
    ) -> Optional[Dict[str, Any]]:
        """
        중기기온조회 API 응답을 파싱하여 weather_info 형식으로 변환
        
        Args:
            response: API 응답 딕셔너리
            target_date: 목표 날짜 (YYYY-MM-DD)
            region_canonical: 정규화된 지역명
            tmFc: 예보 발표시각 (YYYYMMDDHHmm 형식)
        
        Returns:
            weather_info 딕셔너리 또는 None (파싱 실패 시)
        """
        try:
            # API 응답 구조 확인 및 디버깅
            logger.debug(f"API response keys: {list(response.keys())}")
            
            # 공공데이터포털 API 응답 구조: response -> body -> items
            if "response" not in response:
                logger.error("Invalid API response structure: no 'response' key")
                logger.error(f"Response structure: {list(response.keys())}")
                return None
            
            response_obj = response["response"]
            
            # header 확인 (에러 체크)
            if "header" in response_obj:
                header = response_obj["header"]
                result_code = header.get("resultCode", "00")
                result_msg = header.get("resultMsg", "")
                
                # resultCode가 "00"이 아니면 에러 또는 NO_DATA
                if result_code != "00":
                    logger.warning(f"API returned error: resultCode={result_code}, resultMsg={result_msg}")
                    if result_code == "03" or "NO_DATA" in result_msg:
                        logger.info("No data available for the requested parameters")
                    return None
            
            # body 확인
            if "body" not in response_obj:
                logger.warning("No 'body' key in response. Response may be empty or error.")
                return None
            
            body = response_obj["body"]
            logger.debug(f"Body keys: {list(body.keys()) if isinstance(body, dict) else type(body)}")
            
            # items 확인
            if "items" not in body:
                logger.warning(f"No 'items' key in body. Body keys: {list(body.keys()) if isinstance(body, dict) else type(body)}")
                return None
            
            items_data = body["items"]
            
            # 공공데이터포털 API 응답 구조: items.item이 리스트
            if isinstance(items_data, dict):
                # items가 dict이고 "item" 키가 있는 경우
                if "item" in items_data:
                    item_list = items_data["item"]
                    # item이 리스트인지 단일 dict인지 확인
                    if isinstance(item_list, list):
                        items = item_list
                    elif isinstance(item_list, dict):
                        items = [item_list]
                    else:
                        logger.warning(f"Unexpected item type: {type(item_list)}")
                        return None
                else:
                    logger.warning(f"No 'item' key in items. Items keys: {list(items_data.keys())}")
                    return None
            elif isinstance(items_data, list):
                # items가 직접 리스트인 경우
                items = items_data
            else:
                logger.warning(f"Unexpected items type: {type(items_data)}")
                return None
            
            if not isinstance(items, list) or len(items) == 0:
                logger.warning(f"Empty or invalid items list. Type: {type(items)}, Value: {items}")
                return None
            
            # 첫 번째 아이템 사용 (일반적으로 하나의 예보만 반환)
            item = items[0]
            
            # target_date에 해당하는 기온 찾기
            # taMin3, taMin4, ..., taMin10 (3일 후부터 10일 후까지)
            # taMax3, taMax4, ..., taMax10
            
            # tmFc에서 날짜 추출 (YYYYMMDDHHmm 형식)
            tmFc_date = datetime.strptime(tmFc[:8], "%Y%m%d")
            target_date_obj = datetime.strptime(target_date, "%Y-%m-%d")
            
            # delta_days 계산 (예보 기준일 대비 목표 날짜까지의 일수)
            delta = (target_date_obj - tmFc_date).days
            
            # 중기예보는 D+4~10(06시) 또는 D+5~10(18시) 범위
            # 하지만 API 응답에는 taMin3~taMin10, taMax3~taMax10이 있음
            # 실제로는 3일 후부터 10일 후까지의 데이터가 있음
            
            # delta_days에 맞는 키 찾기
            if delta < 3 or delta > 10:
                logger.warning(f"Delta days {delta} is out of range (3-10)")
                return None
            
            min_key = f"taMin{delta}"
            max_key = f"taMax{delta}"
            
            if min_key not in item or max_key not in item:
                logger.warning(f"Temperature keys not found: {min_key}, {max_key}")
                return None
            
            min_temp = item.get(min_key)
            max_temp = item.get(max_key)
            
            # None 체크 및 타입 변환
            if min_temp is None or max_temp is None:
                logger.warning(f"Temperature values are None: {min_key}={min_temp}, {max_key}={max_temp}")
                return None
            
            try:
                min_temp = float(min_temp)
                max_temp = float(max_temp)
            except (ValueError, TypeError):
                logger.warning(f"Invalid temperature values: {min_key}={min_temp}, {max_key}={max_temp}")
                return None
            
            # weather_info 형식으로 정규화
            weather_info = {
                "source": "KMA_MidTa",
                "region": region_canonical,
                "date": target_date,
                "temperature": {
                    "min": min_temp,
                    "max": max_temp
                },
                "delta_days": delta
            }
            
            logger.info(f"Parsed weather info: {weather_info}")
            return weather_info
            
        except Exception as e:
            logger.error(f"Error parsing weather response: {str(e)}", exc_info=True)
            return None
