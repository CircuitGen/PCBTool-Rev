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
        from_attributes = True

class MessageResponse(BaseModel):
    id: int
    role: str
    content: Dict[str, Any] # The content is a dictionary, not a string
    created_at: datetime


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
        from_attributes = True

# --- User Schemas ---

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    conversations: List[Conversation] = []

    class Config:
        from_attributes = True

# --- Token Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# --- API Specific Schemas ---

class InitialAnalysisResponse(BaseModel):
    conversation_id: int
    message: MessageResponse

class CodeGenerationResponse(BaseModel):
    message: MessageResponse

class DeploymentGuideResponse(BaseModel):
    message: MessageResponse
    audio_url: Optional[str]

class SchematicResponse(BaseModel):
    message: MessageResponse
