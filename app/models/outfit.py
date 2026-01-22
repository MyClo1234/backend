from sqlalchemy import Column, Integer, String, Date, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
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
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    worn_date = Column(Date, nullable=False)
    purpose = Column(String, nullable=True)  # 결혼식, 면접...
    location = Column(String, nullable=True)

    # PostgreSQL JSONB
    weather_snapshot = Column(JSONB, nullable=True)

    # Relationships
    owner = relationship("User", back_populates="outfit_logs")
    outfit_items = relationship("OutfitItem", back_populates="log")
    items = relationship("ClosetItem", secondary="outfit_items", viewonly=True)
