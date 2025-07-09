from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

# --- Message Schemas ---

class MessageContent(BaseModel):
    type: str
    data: Dict[str, Any]

class MessageBase(BaseModel):
    role: str
    content: str # JSON string

class MessageCreate(MessageBase):
    pass

class Message(MessageBase):
    id: int
    conversation_id: int
    created_at: datetime

    class Config:
        orm_mode = True

# --- Conversation Schemas ---

class ConversationBase(BaseModel):
    title: Optional[str] = "New Conversation"

class ConversationCreate(ConversationBase):
    pass

class Conversation(ConversationBase):
    id: int
    user_id: int
    created_at: datetime
    messages: List[Message] = []

    class Config:
        orm_mode = True

# --- User Schemas ---

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int
    conversations: List[Conversation] = []

    class Config:
        orm_mode = True

# --- API Specific Schemas ---

class InitialAnalysisResponse(BaseModel):
    conversation_id: int
    message: Dict[str, Any]

class CodeGenerationResponse(BaseModel):
    message: Dict[str, Any]

class DeploymentGuideResponse(BaseModel):
    message: Dict[str, Any]
    audio_url: Optional[str]

class SchematicResponse(BaseModel):
    message: Dict[str, Any]