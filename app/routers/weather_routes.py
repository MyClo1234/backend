from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.services.weather_service import get_daily_weather_summary
from pydantic import BaseModel

router = APIRouter()


# 응답 스키마 (프론트엔드가 받을 형태)
class DailyWeatherResponse(BaseModel):
    date_id: str
    min_temp: float | None
    max_temp: float | None
    rain_type: int
    message: str

    class Config:
        from_attributes = True


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/today/summary", response_model=DailyWeatherResponse)
async def get_today_summary(
    nx: int = Query(..., description="격자 X"),
    ny: int = Query(..., description="격자 Y"),
    db: Session = Depends(get_db),
):
    weather_data, msg = get_daily_weather_summary(db, nx, ny)

    if not weather_data:
        # 데이터가 없다는 건 아직 02:15분이 안 지났거나 API 오류
        raise HTTPException(
            status_code=404,
            detail="오늘 기상 정보가 아직 준비되지 않았습니다. (02:15 이후 시도)",
        )

    # 객체에 메시지 필드를 동적으로 붙여서 리턴 (Pydantic이 처리)
    weather_data.message = msg
    return weather_data
