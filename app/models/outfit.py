from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    ForeignKey,
    Table,
    Boolean,
    Text,
    text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB, UUID
from app.database import Base


class OutfitItem(Base):
    __tablename__ = "outfit_items"

    log_id = Column(Integer, ForeignKey("outfit_logs.log_id"), primary_key=True)
    item_id = Column(Integer, ForeignKey("closet_items.id"), primary_key=True)

    # Relationships
    log = relationship("OutfitLog", back_populates="outfit_items")
    item = relationship("ClosetItem", back_populates="outfit_associations")


class OutfitLog(Base):
    __tablename__ = "outfit_logs"

    log_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    worn_date = Column(Date, nullable=False)
    purpose = Column(String, nullable=True)  # 결혼식, 면접...
    location = Column(String, nullable=True)

    # PostgreSQL JSONB
    weather_snapshot = Column(JSONB, nullable=True)

    # Relationships
    owner = relationship("User", back_populates="outfit_logs")
    outfit_items = relationship("OutfitItem", back_populates="log")
    items = relationship("ClosesetItem", secondary="outfit_items", viewonly=True)


class TodaysPick(Base):
    __tablename__ = "todays_picks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False, server_default=text("now()"))

    top_id = Column(Integer, ForeignKey("closet_items.id"), nullable=True)
    bottom_id = Column(Integer, ForeignKey("closet_items.id"), nullable=True)

    image_url = Column(String, nullable=True)  # 나노바나나가 생성한 이미지 경로 (Blob)
    reasoning = Column(Text, nullable=True)
    weather_snapshot = Column(JSONB, nullable=True)
    is_active = Column(Boolean, default=True)

    # Relationships
    user = relationship("User")
    top = relationship("ClosetItem", foreign_keys=[top_id])
    bottom = relationship("ClosetItem", foreign_keys=[bottom_id])
