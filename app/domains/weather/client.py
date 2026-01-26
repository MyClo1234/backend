import aiohttp
from typing import Dict, Any, Optional
from urllib.parse import unquote
from app.core.config import Config


class KMAWeatherClient:
    """기상청 단기예보 API 클라이언트"""

    BASE_URL = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"

    async def fetch_forecast(
        self, base_date: str, base_time: str, nx: int, ny: int, numOfRows: int
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
        # API Key Decoding: requests 라이브러리는 파라미터를 자동으로 인코딩하므로,
        # 이미 인코딩된 키가 들어오면 이중 인코딩되는 문제가 발생합니다.
        # 따라서 항상 디코딩된 상태로 만들어 requests에 넘겨줍니다.
        service_key = unquote(Config.KMA_API_KEY)

        params = {
            "serviceKey": service_key,
            "pageNo": "1",
            "numOfRows": numOfRows,  # 하루치 데이터 커버
            "dataType": "JSON",
            "base_date": base_date,
            "base_time": base_time,
            "nx": nx,
            "ny": ny,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.BASE_URL,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    response.raise_for_status()
                    return await response.json()
        except aiohttp.ClientError as e:
            print(f"KMA API Connection Failed: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None
