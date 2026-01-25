from datetime import datetime
from typing import Tuple, Optional
from sqlalchemy.orm import Session
from .model import DailyWeather
from .client import KMAWeatherClient


class WeatherService:
    def __init__(self):
        self.client = KMAWeatherClient()

    def get_daily_weather_summary(
        self, db: Session, nx: int, ny: int, region: Optional[str] = None
    ) -> Tuple[Optional[DailyWeather], str]:
        """
        오늘 날짜의 기상 정보를 조회합니다.
        1. Region(시/도)이 있으면 해당 지역의 캐시된 날씨가 있는지 먼저 확인합니다.
        2. 없으면 NX, NY로 DB 조회합니다.
        3. DB에 없으면 API(02:00 기준)를 호출하여 저장합니다.
        """
        today_str = datetime.now().strftime("%Y%m%d")

        # 1. DB 조회 (Region 우선)
        if region:
            cached_by_region = (
                db.query(DailyWeather)
                .filter_by(date_id=today_str, region=region)
                .first()
            )
            if cached_by_region:
                return cached_by_region, "DB Cached (Region)"

        # 2. DB 조회 (NX, NY) - region으로 못 찾았거나 region이 없는 경우
        cached_data = (
            db.query(DailyWeather).filter_by(date_id=today_str, nx=nx, ny=ny).first()
        )
        if cached_data:
            return cached_data, "DB Cached (Grid)"

        # 3. API 호출
        data = self.client.fetch_forecast(today_str, "0200", nx, ny)

        if not data:
            return None, "Connection Error"

        if data["response"]["header"]["resultCode"] != "00":
            return (
                None,
                f"API Error or Not Ready: {data['response']['header']['resultMsg']}",
            )

        items = data["response"]["body"]["items"]["item"]

        # 4. 데이터 파싱
        min_val, max_val, max_rain_type = self._parse_weather_data(items)

        # 5. DB 저장
        new_weather = DailyWeather(
            date_id=today_str,
            nx=nx,
            ny=ny,
            region=region,
            min_temp=min_val,
            max_temp=max_val,
            rain_type=max_rain_type,
        )

        db.add(new_weather)
        try:
            db.commit()
            db.refresh(new_weather)
        except Exception:
            db.rollback()
            # 동시성 이슈 등으로 저장 실패 시, 이미 저장된 데이터가 있는지 확인
            existing = (
                db.query(DailyWeather)
                .filter_by(date_id=today_str, nx=nx, ny=ny)
                .first()
            )
            if existing:
                return existing, "DB Cached (Concurrent Save)"
            else:
                return None, "Save Failed"

        return new_weather, "API Fetched & Saved"

    def _parse_weather_data(
        self, items: list
    ) -> Tuple[Optional[float], Optional[float], int]:
        min_val = None
        max_val = None
        max_rain_type = 0

        for item in items:
            cat = item["category"]
            val = item["fcstValue"]

            if cat == "TMN":
                min_val = float(val)
            elif cat == "TMX":
                max_val = float(val)
            elif cat == "PTY":
                rain_val = int(val)
                if rain_val > max_rain_type:
                    max_rain_type = rain_val

        return min_val, max_val, max_rain_type


# Singleton Instance
weather_service = WeatherService()
