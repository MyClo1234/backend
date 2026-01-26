from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base
import uuid


class TodaysPick(Base):
    __tablename__ = "todays_picks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Selected Outfit Items
    top_item_id = Column(String, nullable=True)  # Can be closet_items.id or external ID
    bottom_item_id = Column(
        String, nullable=True
    )  # Can be closet_items.id or external ID

    # Generated Image
    image_url = Column(String, nullable=False)
    prompt = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<TodaysPick(id={self.id}, user_id={self.user_id})>"
