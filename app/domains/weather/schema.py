from typing import Optional
from pydantic import BaseModel, ConfigDict


class DailyWeatherResponse(BaseModel):
    date_id: str
    min_temp: Optional[float] = None
    max_temp: Optional[float] = None
    rain_type: int
    message: str
    region: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
