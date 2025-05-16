from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# Message schemas
class MessageBase(BaseModel):
    content: str
    message_type: str = "text"
    
class MessageCreate(MessageBase):
    chat_group_id: int
    
class Message(MessageBase):
    id: int
    created_at: datetime
    chat_group_id: int
    user_id: int
    sender_name: str
    sender_profile_picture: Optional[str] = None
    
    class Config:
        orm_mode = True

# Chat group schemas
class ChatGroupBase(BaseModel):
    name: str
    is_direct: bool = False
    
class ChatGroupCreate(ChatGroupBase):
    member_ids: List[int]
    campaign_id: Optional[int] = None
    
class ChatGroup(ChatGroupBase):
    id: int
    created_at: datetime
    updated_at: datetime
    campaign_id: Optional[int] = None
    
    class Config:
        orm_mode = True
        
class ChatGroupWithMembers(ChatGroup):
    members: List[int]  # User IDs
    
# WebSocket message schemas
class WSMessageBase(BaseModel):
    type: str  # "message", "join", "leave"
    
class WSMessageSend(WSMessageBase):
    type: str = "message"
    content: str
    chat_group_id: int
    message_type: str = "text"
    
class WSMessageReceive(WSMessageBase):
    type: str = "message"
    message: Message 