"""
Pydantic schemas for Chat Session management.
"""

from pydantic import BaseModel, UUID4
from datetime import datetime
from typing import Optional, List, Literal, Any, Dict

# Reasoning step schemas
class ReasoningStepBase(BaseModel):
    # the 'type' helps the UI decide how to render it
    step_type: Literal['gathered_context', 'reasoning', 'tool_call', 'tool_result']
    step_data: Dict[str, Any]
    step_order: int

class ReasoningStepCreate(ReasoningStepBase):
    pass

class ReasoningStep(ReasoningStepBase):
    step_id: UUID4
    message_id: UUID4
    created_at: datetime

    class Config:
        from_attributes = True

# Chat message schemas
class ChatMessageBase(BaseModel):
    role: Literal['user', 'assistant', 'system']
    content: str

class ChatMessageCreate(ChatMessageBase):
    pass

class ChatMessage(ChatMessageBase):
    message_id: UUID4
    session_id: UUID4
    created_at: datetime
    reasoning_steps: List[ReasoningStep] = []

    class Config:
        from_attributes = True


# Chat session schemas
class ChatSessionBase(BaseModel):
    session_title: str
    case_id: int

class ChatSessionCreate(BaseModel):
    case_id: int
    session_title: Optional[str] = None

class ChatSessionResponse(ChatSessionBase):
    session_id: UUID4
    case_id: int
    user_id: UUID4
    created_at: datetime
    updated_at: datetime

    case_name: Optional[str] = None  # Include case name for display convenience

    class Config:
        from_attributes = True

class ChatSessionDetail(ChatSessionResponse):
    messages: List[ChatMessage] = []        


class CaseInfo(BaseModel):
    case_id: int
    case_name: str
    court: Optional[str] = None
    status: str

    class Config:
        from_attributes = True

# request/response models
class CreateSessionRequest(BaseModel):
    case_id: int

class SendMessageRequest(BaseModel):
    content: str    

class RenameSessionRequest(BaseModel):
    session_title: str    