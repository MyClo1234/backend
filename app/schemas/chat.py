from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class ChatMessageBase(BaseModel):
    sender: str
    extracted_5w1h: Optional[Dict[str, Any]] = None


class ChatMessageCreate(ChatMessageBase):
    pass


class ChatMessageResponse(ChatMessageBase):
    message_id: int
    session_id: int

    class Config:
        from_attributes = True


class ChatSessionBase(BaseModel):
    session_summary: Optional[str] = None


class ChatSessionCreate(ChatSessionBase):
    pass


class ChatSessionResponse(ChatSessionBase):
    session_id: int
    user_id: int
    messages: List[ChatMessageResponse] = []

    class Config:
        from_attributes = True
