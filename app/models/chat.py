from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from app.database import Base


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    session_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_summary = Column(Text, nullable=True)  # Long-term memory

    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    message_id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.session_id"), nullable=False)
    sender = Column(String, nullable=False)  # 'USER' or 'AGENT'

    # PostgreSQL JSONB
    extracted_5w1h = Column(JSONB, nullable=True)  # 육하원칙 데이터
    clarification_count = Column(Integer, default=0)  # 재질문 횟수

    # Relationships
    session = relationship("ChatSession", back_populates="messages")
