import requests
from typing import Dict, Any, Optional
from app.core.config import Config


class KMAWeatherClient:
    """기상청 단기예보 API 클라이언트"""

    BASE_URL = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"

    def fetch_forecast(
        self, base_date: str, base_time: str, nx: int, ny: int
    ) -> Optional[Dict[str, Any]]:
        """
        기상청 API를 호출하여 예보 데이터를 가져옵니다.

        Args:
            base_date (str): 기준 날짜 (YYYYMMDD)
            base_time (str): 기준 시간 (HHMM)
            nx (int): 격자 X 좌표
            ny (int): 격자 Y 좌표

        Returns:
            Optional[Dict[str, Any]]: API 응답 데이터 (JSON) 또는 실패 시 None
        """
        params = {
            "serviceKey": Config.KMA_API_KEY,
            "pageNo": "1",
            "numOfRows": "300",  # 하루치 데이터 커버
            "dataType": "JSON",
            "base_date": base_date,
            "base_time": base_time,
            "nx": nx,
            "ny": ny,
        }

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"KMA API Connection Failed: {e}")
            return None
