from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import json

from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    # In a real app, you'd store a hashed password, not the actual one.
    # hashed_password = Column(String, nullable=False)

    conversations = relationship("Conversation", back_populates="user")

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, default="New Conversation")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    role = Column(String, nullable=False)  # "user" or "assistant"
    
    # Storing structured content as a JSON string (or Text).
    # This allows flexibility for different message types.
    # e.g., {"type": "analysis_result", "bom": "...", "req_doc": "..."}
    # e.g., {"type": "code", "language": "python", "content": "..."}
    content = Column(Text, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    conversation = relationship("Conversation", back_populates="messages")

    def to_dict(self):
        """Helper to convert model to dict, parsing JSON content."""
        return {
            "id": self.id,
            "role": self.role,
            "content": json.loads(self.content),
            "created_at": self.created_at.isoformat()
        }
