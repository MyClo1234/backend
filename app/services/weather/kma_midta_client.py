"""
기상청 중기기온조회 API 클라이언트
"""
import logging
from typing import Dict, Any, Optional
import httpx
from app.core.config import Config

logger = logging.getLogger(__name__)


class KMAMidTaClient:
    """기상청 중기기온조회 API 클라이언트"""
    
    BASE_URL = "http://apis.data.go.kr/1360000/MidFcstInfoService/getMidTa"
    
    def __init__(self):
        self.service_key = Config.KMA_SERVICE_KEY
        if not self.service_key:
            logger.warning("KMA_SERVICE_KEY is not set. Weather API calls will fail.")
    
    def get_mid_ta(
        self,
        regId: str,
        tmFc: str,
        numOfRows: int = 10,
        pageNo: int = 1
    ) -> Dict[str, Any]:
        """
        중기기온조회 API 호출
        
        Args:
            regId: 예보구역코드 (예: "11B10101")
            tmFc: 발표시각 (예: "202401280600")
            numOfRows: 한 페이지 결과 수
            pageNo: 페이지 번호
        
        Returns:
            API 응답 딕셔너리
        
        Raises:
            Exception: API 호출 실패 시
        """
        if not self.service_key:
            raise ValueError("KMA_SERVICE_KEY is not set")
        
        params = {
            "serviceKey": self.service_key,  # 이미 URL-encoded된 키 사용 (추가 인코딩 하지 않음)
            "regId": regId,
            "tmFc": tmFc,
            "numOfRows": numOfRows,
            "pageNo": pageNo,
            "dataType": "JSON"  # JSON 형식으로 응답 받기
        }
        
        try:
            logger.info(f"Calling KMA MidTa API: regId={regId}, tmFc={tmFc}")
            response = httpx.get(self.BASE_URL, params=params, timeout=10.0)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"KMA API response received: {len(str(data))} bytes")
            
            return data
            
        except httpx.HTTPError as e:
            logger.error(f"KMA API HTTP error: {str(e)}")
            raise Exception(f"KMA API HTTP error: {str(e)}")
        except Exception as e:
            logger.error(f"KMA API error: {str(e)}", exc_info=True)
            raise Exception(f"KMA API error: {str(e)}")
