from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.models.chat import ChatGroup, ChatMember, ChatMessage
from app.models.user import User
from app.schemas.chat import ChatGroupCreate, MessageCreate

class ChatRepository:
    def __init__(self, db: Session):
        self.db = db
        
    def get_chat_group_by_id(self, chat_group_id: int) -> Optional[ChatGroup]:
        return self.db.query(ChatGroup).filter(ChatGroup.id == chat_group_id).first()
        
    def get_user(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()
        
    def get_chat_groups_for_user(self, user_id: int) -> List[ChatGroup]:
        """Get all chat groups where the user is a member"""
        return self.db.query(ChatGroup).join(
            ChatMember, ChatGroup.id == ChatMember.chat_group_id
        ).filter(ChatMember.user_id == user_id).all()
        
    def get_direct_chat_between_users(self, user_id1: int, user_id2: int) -> Optional[ChatGroup]:
        """Get direct chat between two users if it exists"""
        # Find chat groups that are direct messages and both users are members
        user1_groups = set(chat_group.id for chat_group in self.get_chat_groups_for_user(user_id1) if chat_group.is_direct)
        user2_groups = set(chat_group.id for chat_group in self.get_chat_groups_for_user(user_id2) if chat_group.is_direct)
        
        # Find common chat groups
        common_group_ids = user1_groups.intersection(user2_groups)
        
        for group_id in common_group_ids:
            # Check if this group has exactly 2 members
            member_count = self.db.query(ChatMember).filter(ChatMember.chat_group_id == group_id).count()
            if member_count == 2:
                return self.get_chat_group_by_id(group_id)
                
        return None
        
    def create_chat_group(self, group_data: ChatGroupCreate) -> ChatGroup:
        """Create a new chat group"""
        chat_group = ChatGroup(
            name=group_data.name,
            is_direct=group_data.is_direct
        )
        
        if group_data.campaign_id:
            chat_group.campaign_id = group_data.campaign_id
            
        self.db.add(chat_group)
        self.db.commit()
        self.db.refresh(chat_group)
        
        # Add members
        for user_id in group_data.member_ids:
            # First member is admin
            is_admin = user_id == group_data.member_ids[0]
            self.add_chat_member(chat_group.id, user_id, is_admin)
            
        return chat_group
        
    def add_chat_member(self, chat_group_id: int, user_id: int, is_admin: bool = False) -> Optional[ChatMember]:
        """Add a user to a chat group"""
        # Check if user is already a member
        existing = self.db.query(ChatMember).filter(
            ChatMember.chat_group_id == chat_group_id,
            ChatMember.user_id == user_id
        ).first()
        
        if existing:
            return existing
            
        member = ChatMember(
            chat_group_id=chat_group_id,
            user_id=user_id,
            is_admin=is_admin
        )
        
        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)
        
        return member
        
    def remove_chat_member(self, chat_group_id: int, user_id: int) -> bool:
        """Remove a user from a chat group"""
        deleted = self.db.query(ChatMember).filter(
            ChatMember.chat_group_id == chat_group_id,
            ChatMember.user_id == user_id
        ).delete()
        
        self.db.commit()
        return deleted > 0
        
    def is_chat_member(self, chat_group_id: int, user_id: int) -> bool:
        """Check if a user is a member of a chat group"""
        return self.db.query(ChatMember).filter(
            ChatMember.chat_group_id == chat_group_id,
            ChatMember.user_id == user_id
        ).first() is not None
        
    def get_chat_group_members(self, chat_group_id: int) -> List[ChatMember]:
        """Get all members of a chat group"""
        return self.db.query(ChatMember).filter(
            ChatMember.chat_group_id == chat_group_id
        ).all()
        
    def get_chat_messages(self, chat_group_id: int, limit: int = 50, before_id: Optional[int] = None) -> List[ChatMessage]:
        """Get messages from a chat group, with pagination"""
        query = self.db.query(ChatMessage).filter(ChatMessage.chat_group_id == chat_group_id)
        
        if before_id:
            query = query.filter(ChatMessage.id < before_id)
            
        return query.order_by(ChatMessage.id.desc()).limit(limit).all()
        
    def create_message(self, chat_group_id: int, user_id: int, content: str, message_type: str = "text") -> ChatMessage:
        """Create a new chat message"""
        message = ChatMessage(
            chat_group_id=chat_group_id,
            user_id=user_id,
            content=content,
            message_type=message_type
        )
        
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        
        return message
        
    def delete_message(self, message_id: int) -> bool:
        """Delete a chat message"""
        message = self.db.query(ChatMessage).filter(ChatMessage.id == message_id).first()
        
        if not message:
            return False
            
        self.db.delete(message)
        self.db.commit()
        
        return True 