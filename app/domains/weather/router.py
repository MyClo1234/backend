from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import SessionLocal
from .service import weather_service
from .schema import DailyWeatherResponse
from app.core.regions import get_nearest_region

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/today/summary", response_model=DailyWeatherResponse)
async def get_today_summary(
    lat: float = Query(..., description="위도"),
    lon: float = Query(..., description="경도"),
    db: Session = Depends(get_db),
):
    # 1. 가장 가까운 지역 찾기
    region_name, region_data = get_nearest_region(lat, lon)
    nx = region_data["nx"]
    ny = region_data["ny"]

    # 2. 날씨 데이터 조회 (Region 이름으로 캐싱/조회)
    weather_data, msg = await weather_service.get_daily_weather_summary(
        db, nx, ny, region_name
    )

    if not weather_data:
        # 데이터가 없다는 건 아직 02:15분이 안 지났거나 API 오류
        raise HTTPException(
            status_code=404,
            detail=f"오늘 기상 정보가 아직 준비되지 않았습니다. (02:15 이후 시도) - 상세: {msg}",
        )

    # Pydantic 모델 변환을 위해 객체에 메시지 추가 (JIT 속성 주입)
    # SQLAlchemy 객체는 동적 속성 할당이 가능함
    weather_data.message = msg
    return weather_data


@router.get("/weather/batch")
async def fetchAndLoadWeather(
    db: Session = Depends(get_db),
):
    return await weather_service.fetchAndLoadWeather(db)
