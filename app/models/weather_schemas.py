from typing import Optional
from pydantic import BaseModel


class DailyWeatherResponse(BaseModel):
    date_id: str
    min_temp: Optional[float] = None
    max_temp: Optional[float] = None
    rain_type: int
    message: str
    region: Optional[str] = None

    class Config:
        from_attributes = True
