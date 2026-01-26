from sqlalchemy import Column, String, ForeignKey, DateTime, Date, Float, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base
import uuid
from datetime import date


class TodaysPick(Base):
    __tablename__ = "todays_picks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Date tracking
    date = Column(Date, nullable=False, default=date.today, index=True)

    # Selected Outfit Items
    top_item_id = Column(String, nullable=True)
    bottom_item_id = Column(String, nullable=True)

    # Generated Image
    image_url = Column(String, nullable=False)
    prompt = Column(String, nullable=True)

    # LLM Recommendation Metadata
    reasoning = Column(String, nullable=True)  # 추천 이유
    score = Column(Float, nullable=True)  # 추천 점수 (0.0~1.0)
    weather_snapshot = Column(JSON, nullable=True)  # 날씨 정보
    is_active = Column(Boolean, default=True, index=True)  # 활성 상태

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<TodaysPick(id={self.id}, user_id={self.user_id}, date={self.date})>"
