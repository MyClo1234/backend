import uuid
from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_name = Column(String, nullable=False)
    body_shape = Column(String, nullable=True)
    height = Column(DECIMAL(5, 2), nullable=True)  # cm
    weight = Column(DECIMAL(5, 2), nullable=True)  # kg
    age = Column(Integer, nullable=True)
    gender = Column(String, nullable=True)  # 'MALE', 'FEMALE', etc.
    password = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=text("now()"))

    # Relationships
    closet_items = relationship("ClosetItem", back_populates="owner")
    outfit_logs = relationship("OutfitLog", back_populates="owner")
    chat_sessions = relationship("ChatSession", back_populates="user")
