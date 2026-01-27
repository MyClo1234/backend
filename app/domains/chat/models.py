from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func
from app.database import Base


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    session_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    session_summary = Column(Text, nullable=True)  # Long-term memory
    finished_at = Column(DateTime, nullable=True)  # Timestamp when session was finished
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )  # Session creation timestamp

    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship(
        "ChatMessage",
        back_populates="session",
        order_by="ChatMessage.created_at.asc()",  # 메시지 순서 보장
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    message_id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.session_id"), nullable=False)
    sender = Column(String, nullable=False)  # 'USER' or 'AGENT'
    content = Column(Text, nullable=False)  # 메시지 내용
    node_name = Column(String, nullable=True)  # 어떤 노드에서 생성된 메시지인지 (AGENT인 경우)
    message_metadata = Column(JSONB, nullable=True)  # 노드별 메타데이터 (예: intent, tpo 등)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )  # 메시지 생성 시간

    # Relationships
    session = relationship("ChatSession", back_populates="messages")
