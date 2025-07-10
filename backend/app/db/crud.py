from sqlalchemy.orm import Session
import json

from . import models as db_models
from app.models import schemas

from app.services import security_service

def get_user_by_username(db: Session, username: str) -> db_models.User | None:
    """
    Retrieve a user from the database by their username.
    """
    return db.query(db_models.User).filter(db_models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate) -> db_models.User:
    """
    Create a new user in the database with a hashed password.
    """
    hashed_password = security_service.get_password_hash(user.password)
    db_user = db_models.User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, username: str, password: str) -> db_models.User | None:
    """
    Authenticate a user. Returns the user object if successful, otherwise None.
    """
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not security_service.verify_password(password, user.hashed_password):
        return None
    return user

def get_or_create_user(db: Session, username: str) -> db_models.User:
    """
    Get a user by username, or create them if they don't exist.
    """
    db_user = get_user_by_username(db, username)
    if not db_user:
        db_user = create_user(db, schemas.UserCreate(username=username))
    return db_user

def create_conversation(db: Session, user_id: int, title: str = "New Conversation") -> db_models.Conversation:
    """
    Create a new conversation for a user.
    """
    db_conversation = db_models.Conversation(user_id=user_id, title=title)
    db.add(db_conversation)
    db.commit()
    db.refresh(db_conversation)
    return db_conversation

def create_message(db: Session, conversation_id: int, role: str, content: dict) -> db_models.Message:
    """
    Create a new message in a conversation.
    The 'content' dictionary is converted to a JSON string for storage.
    """
    content_str = json.dumps(content)
    db_message = db_models.Message(
        conversation_id=conversation_id,
        role=role,
        content=content_str
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

def get_conversation(db: Session, conversation_id: int) -> db_models.Conversation | None:
    """
    Retrieve a conversation by its ID.
    """
    return db.query(db_models.Conversation).filter(db_models.Conversation.id == conversation_id).first()

def get_message(db: Session, message_id: int) -> db_models.Message | None:
    """
    Retrieve a message by its ID.
    """
    return db.query(db_models.Message).filter(db_models.Message.id == message_id).first()

def get_conversations_by_user(db: Session, user_id: int) -> list[db_models.Conversation]:
    """
    Retrieve all conversations for a specific user, ordered by creation date.
    """
    return db.query(db_models.Conversation).filter(db_models.Conversation.user_id == user_id).order_by(db_models.Conversation.created_at.desc()).all()

def delete_conversation(db: Session, conversation_id: int, user_id: int) -> db_models.Conversation | None:
    """
    Deletes a conversation by its ID, ensuring it belongs to the user.
    """
    db_conversation = db.query(db_models.Conversation).filter(
        db_models.Conversation.id == conversation_id,
        db_models.Conversation.user_id == user_id
    ).first()
    
    if db_conversation:
        db.delete(db_conversation)
        db.commit()
    
    return db_conversation
