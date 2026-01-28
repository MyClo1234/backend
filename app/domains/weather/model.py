from sqlalchemy import Column, Integer, String, Float, Date, UniqueConstraint
from sqlalchemy.sql import func
from app.database import Base


class DailyWeather(Base):
    __tablename__ = "daily_weather"

    id = Column(Integer, primary_key=True, index=True)
    base_date = Column(String(8), nullable=False)  # 예: "20260123" (조회 기준 날짜)
    base_time = Column(String(4), nullable=False)  # 예: "HHMM"
    nx = Column(Integer, nullable=False)
    ny = Column(Integer, nullable=False)
    region = Column(String(50), nullable=True, index=True)  # 시/도 이름 (예: "Seoul")

    min_temp = Column(Float)  # 일 최저기온 (TMN)
    max_temp = Column(Float)  # 일 최고기온 (TMX)
    rain_type = Column(Integer)  # 강수 형태 (0:맑음, 1:비, 2:비/눈, 3:눈 ...)
    # 하루 중 가장 심한 기상 상태를 저장 (보수적 코디 추천)

    created_at = Column(Date, server_default=func.now())

    # 같은 날짜, 같은 지역(nx, ny)에는 데이터가 1개만 존재해야 함
    # region이 있으면 region 기준 중복 방지도 고려할 수 있으나,
    # 기본적으로 nx,ny가 primary location key이므로 유지.
    # region 검색 속도를 위해 위에서 index=True 추가함.
    __table_args__ = (
        UniqueConstraint("base_date", "nx", "ny", name="uix_daily_weather"),
    )

    @property
    def date_id(self):
        return self.base_date
