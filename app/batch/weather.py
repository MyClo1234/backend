"""날씨 배치 작업"""

import logging
from sqlalchemy.orm import Session
from app.domains.weather.service import weather_service


async def run_daily_weather_batch(db: Session) -> dict:
    """
    전국 날씨 데이터 배치 수집

    Args:
        db: 데이터베이스 세션 (주입)

    Returns:
        dict: 실행 결과 (성공/실패 개수 등)
    """
    try:
        result = await weather_service.fetchAndLoadWeather(db)
        return result

    except Exception as e:
        logging.error(f"Weather batch error: {str(e)}")
        raise
