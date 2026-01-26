from datetime import datetime
from typing import Tuple, Optional
from sqlalchemy.orm import Session
from .model import DailyWeather
from .client import KMAWeatherClient
import asyncio
from app.core.regions import KOREA_REGIONS
from datetime import datetime, timedelta


class WeatherService:
    def __init__(self):
        self.client = KMAWeatherClient()

    async def fetchAndLoadWeather(self, db: Session):
        # 기상청 데이터는 02:10에 생성되므로, 02:16 실행 시 당일 데이터 조회
        today_str = datetime.now().strftime("%Y%m%d")

        # 전국 17개 지역 정보
        pending_regions = [
            (region, value["nx"], value["ny"])
            for region, value in KOREA_REGIONS.items()
        ]

        # 최대 3번 재시도
        max_retries = 3
        all_weathers = {}  # region -> DailyWeather

        for attempt in range(1, max_retries + 1):
            if not pending_regions:
                break

            tasks = []
            for region, nx, ny in pending_regions:
                tasks.append(self.client.fetch_forecast(today_str, "0200", nx, ny, 168))

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 성공/실패 분류
            failed_regions = []

            for (region, nx, ny), result in zip(pending_regions, results):
                # 성공 여부 확인
                if isinstance(result, Exception) or not result:
                    failed_regions.append((region, nx, ny))
                    continue

                if result["response"]["header"]["resultCode"] != "00":
                    failed_regions.append((region, nx, ny))
                    continue

                # 성공: 데이터 파싱
                items = result["response"]["body"]["items"]["item"]
                min_val, max_val, max_rain_type = self._parse_weather_data(items)

                all_weathers[region] = DailyWeather(
                    base_date=today_str,
                    base_time="0200",
                    nx=nx,
                    ny=ny,
                    region=region,
                    min_temp=min_val,
                    max_temp=max_val,
                    rain_type=max_rain_type,
                )

            # 재시도할 지역 업데이트
            pending_regions = failed_regions

            if pending_regions and attempt < max_retries:
                # 재시도 전 대기 (지수 백오프: 1초 → 3초 → 5초)
                wait_time = attempt * 2 - 1
                await asyncio.sleep(wait_time)

        # 성공한 데이터 저장 (멱등성 보장: upsert 방식)
        total = len(KOREA_REGIONS)
        success = len(all_weathers)
        failed = total - success

        if success > 0:
            # 기존 데이터 일괄 조회 (nx, ny 기반 매칭을 위해 base_date 기준 전체 로드)
            existing_records = (
                db.query(DailyWeather).filter(DailyWeather.base_date == today_str).all()
            )
            # lookup dict: (nx, ny) -> record
            lookup = {(r.nx, r.ny): r for r in existing_records}

            for region, weather_data in all_weathers.items():
                existing = lookup.get((weather_data.nx, weather_data.ny))

                if existing:
                    # 업데이트 (메모리상 객체 수정)
                    existing.region = weather_data.region
                    existing.min_temp = weather_data.min_temp
                    existing.max_temp = weather_data.max_temp
                    existing.rain_type = weather_data.rain_type
                else:
                    # 삽입
                    db.add(weather_data)

            try:
                db.commit()
            except Exception as e:
                db.rollback()
                raise Exception(f"DB commit failed: {str(e)}")

        # 결과 반환
        if failed > 0:
            failed_region_names = [r for r, _, _ in pending_regions]
            # 일부만 성공 - 경고 로그 (Exception 발생 안 함)
            return {
                "status": "partial_success",
                "total": total,
                "success": success,
                "failed": failed,
                "failed_regions": failed_region_names,
                "message": f"Saved {success}/{total} regions. Failed: {failed_region_names}",
            }
        else:
            # 전부 성공
            return {
                "status": "success",
                "total": total,
                "success": success,
                "failed": 0,
                "message": f"All {total} regions saved successfully",
            }

    async def get_daily_weather_summary(
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
        data = await self.client.fetch_forecast(today_str, "0200", nx, ny, 300)

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

        new_weather = DailyWeather(
            date_id=today_str,
            nx=nx,
            ny=ny,
            region=region,
            min_temp=min_val,
            max_temp=max_val,
            rain_type=max_rain_type,
        )

        # 5. DB 저장
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
