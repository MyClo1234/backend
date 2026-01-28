import logging
from datetime import datetime
from typing import Tuple, Optional, Dict, Any
from sqlalchemy.orm import Session
from .model import DailyWeather
from .client import KMAWeatherClient
from .utils import dfs_xy_conv
import asyncio
from app.core.regions import KOREA_REGIONS
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


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
                # _parse_weather_data returns 4 values now (min, max, max_pty, current_pty)
                min_val, max_val, max_rain_type, _ = self._parse_weather_data(items)

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
        오늘 데이터가 DB에 없으면 KMA에서 가져와 저장하고 반환합니다.
        """
        # 1. DB 조회
        today_str = datetime.now().strftime("%Y%m%d")
        cached = (
            db.query(DailyWeather).filter_by(base_date=today_str, nx=nx, ny=ny).first()
        )

        if cached:
            return cached, "DB Cached"

        # 2. KMA 요청
        # 02:00 데이터가 가장 안정적 (Min/Max 포함)
        data = await self.client.fetch_forecast(today_str, "0200", nx, ny, 300)

        if not data or data["response"]["header"]["resultCode"] != "00":
            # 02:00 실패 시 전날 23:00 등 시도할 수도 있지만,
            # 여기서는 간단히 실패 처리 or "아직 생성 안됨"
            return None, "API Error or No Data"

        items = data["response"]["body"]["items"]["item"]
        min_val, max_val, rain_type, current_rain_type = self._parse_weather_data(items)

        # 3. 저장 (DB 오류가 나도 데이터는 반환하도록 예외 처리)
        weather_obj = DailyWeather(
            base_date=today_str,
            base_time="0200",
            nx=nx,
            ny=ny,
            region=region,
            min_temp=min_val,
            max_temp=max_val,
            rain_type=rain_type,
        )

        msg = "Fetched from KMA"
        try:
            db.add(weather_obj)
            db.commit()
            db.refresh(weather_obj)
            msg += " (Saved to DB)"
        except Exception as e:
            # DB 연결/저장 실패 시 롤백 및 로그 출력
            db.rollback()
            print(f"Failed to save weather data to DB: {e}")
            msg += f" (DB Save Failed: {str(e)})"

        # JIT inject current_rain_type (DB에는 없지만 API 응답에는 포함)
        weather_obj.current_rain_type = current_rain_type

        return weather_obj, msg

    async def get_weather_info(
        self, db: Session, lat: float, lon: float
    ) -> Dict[str, Any]:
        """
        코디 추천 엔진에서 사용하기 위한 날씨 정보 간편 반환 함수
        """
        from app.core.regions import get_nearest_region
        from app.core.config import Config

        # KMA API Key 확인
        if not Config.KMA_API_KEY:
            logger.error("KMA_API_KEY is not set in environment variables")
            raise ValueError(
                "KMA_API_KEY가 설정되지 않았습니다. 환경 변수를 확인해주세요."
            )

        # 1. 좌표 변환 (lat, lon -> nx, ny)
        try:
            grid = dfs_xy_conv("toGRID", lat, lon)
            nx, ny = int(grid.get("x", 60)), int(grid.get("y", 127))
            logger.info(f"Converted coordinates: lat={lat}, lon={lon} -> nx={nx}, ny={ny}")
        except Exception as e:
            logger.error(f"Failed to convert coordinates: {e}", exc_info=True)
            raise ValueError(f"좌표 변환 실패: {e}")

        # 2. 가장 가까운 지역명 가져오기
        try:
            region_name, _ = get_nearest_region(lat, lon)
            logger.info(f"Nearest region: {region_name}")
        except Exception as e:
            logger.warning(f"Failed to get nearest region: {e}")
            region_name = "현위치"

        try:
            # 3. 데이터 조회 (DB 또는 API)
            weather_obj, msg = await self.get_daily_weather_summary(
                db, nx, ny, region_name
            )

            if weather_obj:
                min_temp = weather_obj.min_temp
                max_temp = weather_obj.max_temp

                # 가독성을 위한 요약 텍스트 생성 (OutfitRecommender 로직 통합)
                summary = (
                    f"{weather_obj.region or '현위치'} 기온 {min_temp}°C ~ {max_temp}°C"
                )
                if max_temp >= 24:
                    summary += " (여름 날씨)"
                elif max_temp <= 12:
                    summary += " (겨울 날씨)"
                else:
                    summary += " (선선한 날씨)"

                logger.info(f"Weather info retrieved successfully: {summary} (source: {msg})")
                return {
                    "summary": summary,
                    "temp_min": min_temp,
                    "temp_max": max_temp,
                    "region": region_name,
                }
            else:
                logger.warning(f"Weather object is None. Message: {msg}")
                raise ValueError(f"날씨 데이터를 가져올 수 없습니다: {msg}")
        except ValueError:
            # 명시적인 ValueError는 그대로 전파
            raise
        except Exception as e:
            logger.error(f"Error in get_weather_info: {e}", exc_info=True)
            raise ValueError(f"날씨 정보 조회 중 오류 발생: {str(e)}")

    def _parse_weather_data(
        self, items: list
    ) -> Tuple[Optional[float], Optional[float], int, Optional[int]]:
        min_val = None
        max_val = None
        max_rain_type = 0
        current_rain_type = 0

        # 현재 시간 (HH00) 구하기
        now_hour_str = datetime.now().strftime("%H00")

        for item in items:
            cat = item["category"]
            val = item["fcstValue"]
            fcst_time = item["fcstTime"]

            if cat == "TMN":
                min_val = float(val)
            elif cat == "TMX":
                max_val = float(val)
            elif cat == "PTY":
                rain_val = int(val)
                if rain_val > max_rain_type:
                    max_rain_type = rain_val

                # 현재 시각의 강수 형태
                if fcst_time == now_hour_str:
                    current_rain_type = rain_val

        return min_val, max_val, max_rain_type, current_rain_type


# Singleton Instance
weather_service = WeatherService()
