from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class SendMessageResponse(BaseModel):
    success: bool
    response: Optional[str] = None
    is_pick_updated: bool = False
    recommendations: Optional[List[Dict[str, Any]]] = None
    todays_pick: Optional[Dict[str, Any]] = None
