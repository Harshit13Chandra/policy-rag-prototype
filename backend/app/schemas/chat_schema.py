from datetime import datetime
from pydantic import BaseModel

class ConversationCreateResponse(BaseModel):
    id: str
    title: str

class ConversationResponse(BaseModel):
    id: str
    title: str
    updated_at: datetime
    is_archived: bool

class ConversationListResponse(BaseModel):
    items: list[ConversationResponse]

class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: datetime
    citations: list[dict] = []

class MessageListResponse(BaseModel):
    items: list[MessageResponse]

class QueryRequest(BaseModel):
    conversation_id: str
    question: str

class ConversationUpdate(BaseModel):
    title: str
