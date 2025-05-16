from sqlalchemy import Column, String, Integer, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.base import BaseModel

class ChatGroup(BaseModel):
    __tablename__ = "chat_groups"

    name = Column(String)
    is_direct = Column(Boolean, default=False)  # Direct message or group chat
    
    # Related to campaign (optional)
    campaign = relationship("Campaign", back_populates="chat_group", uselist=False)
    
    # Relationships
    members = relationship("ChatMember", back_populates="chat_group")
    messages = relationship("ChatMessage", back_populates="chat_group")

class ChatMember(BaseModel):
    __tablename__ = "chat_members"

    user_id = Column(Integer, ForeignKey("users.id"))
    chat_group_id = Column(Integer, ForeignKey("chat_groups.id"))
    
    # User status
    last_read_at = Column(String, nullable=True)
    is_admin = Column(Boolean, default=False)
    
    # Relationships
    chat_group = relationship("ChatGroup", back_populates="members")
    user = relationship("User")

class ChatMessage(BaseModel):
    __tablename__ = "chat_messages"

    chat_group_id = Column(Integer, ForeignKey("chat_groups.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Message content
    content = Column(Text)
    message_type = Column(String, default="text")  # text, image, etc.
    
    # Relationships
    chat_group = relationship("ChatGroup", back_populates="messages")
    sender = relationship("User") 