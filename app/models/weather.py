from sqlalchemy import Column, Integer, String, Float, Date, UniqueConstraint
from sqlalchemy.sql import func
from app.database import Base


class DailyWeather(Base):
    __tablename__ = "daily_weather"

    id = Column(Integer, primary_key=True, index=True)
    date_id = Column(String(8), nullable=False)  # 예: "20260123" (조회 기준 날짜)
    nx = Column(Integer, nullable=False)
    ny = Column(Integer, nullable=False)

    min_temp = Column(Float)  # 일 최저기온 (TMN)
    max_temp = Column(Float)  # 일 최고기온 (TMX)
    rain_type = Column(Integer)  # 강수 형태 (0:맑음, 1:비, 2:비/눈, 3:눈 ...)
    # 하루 중 가장 심한 기상 상태를 저장 (보수적 코디 추천)

    created_at = Column(Date, server_default=func.now())

    # 같은 날짜, 같은 지역에는 데이터가 1개만 존재해야 함
    __table_args__ = (
        UniqueConstraint("date_id", "nx", "ny", name="uix_daily_weather"),
    )
