"""
날씨 서비스 Facade
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from app.services.weather.weather_resolver import WeatherResolver
from app.services.weather.kma_midta_client import KMAMidTaClient
from app.services.weather.weather_parser import WeatherParser

logger = logging.getLogger(__name__)


class WeatherService:
    """날씨 서비스 Facade - 여러 모듈을 조합하여 날씨 정보 제공"""
    
    def __init__(self):
        self.resolver = WeatherResolver()
        self.client = KMAMidTaClient()
        self.parser = WeatherParser()
    
    def resolve_region(self, region_text: str, disambiguation: Optional[str] = None) -> Dict[str, Any]:
        """
        지역명을 정규화하고 regId로 매핑
        
        Args:
            region_text: 지역명
            disambiguation: disambiguation 정보 (선택사항)
        
        Returns:
            {
                "region_canonical": str,
                "regId": Optional[str],
                "needs_disambiguation": bool,
                "clarifying_question": Optional[str]
            }
        """
        if disambiguation:
            return self.resolver.resolve_with_disambiguation(region_text, disambiguation)
        return self.resolver.resolve_region(region_text)
    
    def select_tmfc(self, target_date: str) -> Optional[str]:
        """
        최근 24시간 내 발표된 예보 중 target_date를 커버하는 tmFc 선택
        
        Args:
            target_date: 목표 날짜 (YYYY-MM-DD)
        
        Returns:
            tmFc (YYYYMMDDHHmm 형식) 또는 None
        """
        try:
            target_date_obj = datetime.strptime(target_date, "%Y-%m-%d")
            now = datetime.now()
            
            # KST 기준 (UTC+9)
            kst_now = now + timedelta(hours=9)
            
            # 최근 24시간 내 후보 tmFc
            candidates = []
            
            # 오늘 18시, 오늘 06시, 어제 18시, 어제 06시
            today_18 = kst_now.replace(hour=18, minute=0, second=0, microsecond=0)
            today_06 = kst_now.replace(hour=6, minute=0, second=0, microsecond=0)
            yesterday_18 = today_18 - timedelta(days=1)
            yesterday_06 = today_06 - timedelta(days=1)
            
            # 현재 시간 이전의 후보만 추가
            for candidate_time in [today_18, today_06, yesterday_18, yesterday_06]:
                if candidate_time <= kst_now:
                    candidates.append(candidate_time)
            
            # target_date가 커버되는 tmFc 선택
            # 중기예보 범위: 실제로는 D+3~10 제공 (API 응답에 taMin3~taMin10 포함)
            # 하지만 공식 문서상: D+4~10(06시) / D+5~10(18시)가 안정적
            # 3일 후도 필요할 수 있으므로 D+3~10으로 확장
            for tmFc_time in sorted(candidates, reverse=True):  # 최신순
                delta = (target_date_obj - tmFc_time).days
                
                # 06시 발표: D+3~10 (실제 API는 3일 후부터 제공 가능)
                if tmFc_time.hour == 6:
                    if 3 <= delta <= 10:
                        return tmFc_time.strftime("%Y%m%d%H%M")
                # 18시 발표: D+3~10 (실제 API는 3일 후부터 제공 가능)
                elif tmFc_time.hour == 18:
                    if 3 <= delta <= 10:
                        return tmFc_time.strftime("%Y%m%d%H%M")
            
            # 커버되는 tmFc가 없음
            logger.warning(f"No valid tmFc found for target_date: {target_date}")
            return None
            
        except Exception as e:
            logger.error(f"Error selecting tmFc: {str(e)}", exc_info=True)
            return None
    
    def check_weather_range(self, target_date: str) -> Dict[str, Any]:
        """
        target_date가 중기예보 범위 내인지 확인
        
        Args:
            target_date: 목표 날짜 (YYYY-MM-DD)
        
        Returns:
            {
                "in_range": bool,
                "reason": Optional[str]  # 범위 밖일 때 이유
            }
        """
        try:
            target_date_obj = datetime.strptime(target_date, "%Y-%m-%d")
            now = datetime.now()
            kst_now = now + timedelta(hours=9)
            
            delta = (target_date_obj - kst_now).days
            
            if delta < 0:
                return {
                    "in_range": False,
                    "reason": "과거 날짜는 예보할 수 없습니다"
                }
            elif delta < 3:
                return {
                    "in_range": False,
                    "reason": "중기예보는 3~10일만 제공됩니다"
                }
            elif delta > 10:
                return {
                    "in_range": False,
                    "reason": "예보 범위 밖입니다 (10일 초과)"
                }
            else:
                return {
                    "in_range": True,
                    "reason": None
                }
                
        except Exception as e:
            logger.error(f"Error checking weather range: {str(e)}", exc_info=True)
            return {
                "in_range": False,
                "reason": f"날짜 확인 중 오류 발생: {str(e)}"
            }
    
    def fetch_weather(self, regId: str, tmFc: str) -> Dict[str, Any]:
        """
        날씨 API 호출
        
        Args:
            regId: 예보구역코드
            tmFc: 발표시각
        
        Returns:
            API 응답 딕셔너리
        
        Raises:
            Exception: API 호출 실패 시
        """
        return self.client.get_mid_ta(regId=regId, tmFc=tmFc)
    
    def parse_weather_response(
        self,
        response: Dict[str, Any],
        target_date: str,
        region_canonical: str,
        tmFc: str
    ) -> Optional[Dict[str, Any]]:
        """
        API 응답을 파싱하여 weather_info 형식으로 변환
        
        Args:
            response: API 응답
            target_date: 목표 날짜
            region_canonical: 정규화된 지역명
            tmFc: 예보 발표시각
        
        Returns:
            weather_info 딕셔너리 또는 None
        """
        return self.parser.parse_mid_ta_response(
            response=response,
            target_date=target_date,
            region_canonical=region_canonical,
            tmFc=tmFc
        )


# 싱글톤 인스턴스
weather_service = WeatherService()
