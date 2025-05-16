import json
from typing import Dict, Set, List, Optional, Any
from fastapi import WebSocket
from datetime import datetime
from sqlalchemy.orm import Session

from app.repositories.chat_repository import ChatRepository
from app.services.notification_service import NotificationService
from app.models.chat import ChatMessage

class ConnectionManager:
    def __init__(self):
        # Map of chat_group_id -> set of websocket connections
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        
        # Map of websocket -> (user_id, chat_group_id)
        self.connection_map: Dict[WebSocket, tuple] = {}
        
    async def connect(self, websocket: WebSocket, chat_group_id: int, user_id: int):
        await websocket.accept()
        
        if chat_group_id not in self.active_connections:
            self.active_connections[chat_group_id] = set()
            
        self.active_connections[chat_group_id].add(websocket)
        self.connection_map[websocket] = (user_id, chat_group_id)
        
        # Notify other users in the chat group
        await self.broadcast_join(chat_group_id, user_id)
        
    def disconnect(self, websocket: WebSocket):
        if websocket in self.connection_map:
            user_id, chat_group_id = self.connection_map[websocket]
            
            if chat_group_id in self.active_connections:
                self.active_connections[chat_group_id].discard(websocket)
                
                # Remove chat group if empty
                if not self.active_connections[chat_group_id]:
                    del self.active_connections[chat_group_id]
                    
            del self.connection_map[websocket]
            return user_id, chat_group_id
            
        return None, None
        
    async def broadcast_join(self, chat_group_id: int, user_id: int):
        """Broadcast to other users in the chat group that a user has joined"""
        if chat_group_id in self.active_connections:
            message = {
                "type": "join",
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self.broadcast(chat_group_id, message, exclude_user_id=user_id)
            
    async def broadcast(self, chat_group_id: int, message: dict, exclude_user_id: Optional[int] = None):
        """Broadcast a message to all connected users in a chat group"""
        if chat_group_id in self.active_connections:
            for connection in self.active_connections[chat_group_id]:
                if exclude_user_id is not None:
                    # Skip if this connection belongs to the excluded user
                    conn_user_id, _ = self.connection_map[connection]
                    if conn_user_id == exclude_user_id:
                        continue
                        
                await connection.send_text(json.dumps(message))
                
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific connection"""
        await websocket.send_text(json.dumps(message))
        
    def get_connected_users(self, chat_group_id: int) -> Set[int]:
        """Get the set of user IDs connected to a chat group"""
        if chat_group_id not in self.active_connections:
            return set()
            
        return {self.connection_map[conn][0] for conn in self.active_connections[chat_group_id]}
        
    def is_user_connected(self, chat_group_id: int, user_id: int) -> bool:
        """Check if a user is connected to a chat group"""
        return user_id in self.get_connected_users(chat_group_id)

# Singleton instance
connection_manager = ConnectionManager()

class ChatService:
    def __init__(self, db: Session):
        self.db = db
        self.chat_repo = ChatRepository(db)
        self.notification_service = NotificationService(db)
        
    async def handle_message(self, websocket: WebSocket, user_id: int, message_data: dict):
        """Handle an incoming chat message"""
        chat_group_id = message_data.get("chat_group_id")
        content = message_data.get("content")
        message_type = message_data.get("message_type", "text")
        
        if not chat_group_id or not content:
            await connection_manager.send_personal_message(
                {"type": "error", "message": "缺少必要的訊息資料"},
                websocket
            )
            return
            
        # Check if user is a member of the chat group
        if not self.chat_repo.is_chat_member(chat_group_id, user_id):
            await connection_manager.send_personal_message(
                {"type": "error", "message": "您不是此聊天室的成員"},
                websocket
            )
            return
            
        # Save message to database
        db_message = self.chat_repo.create_message(
            chat_group_id=chat_group_id,
            user_id=user_id,
            content=content,
            message_type=message_type
        )
        
        # Get user info
        user = self.chat_repo.get_user(user_id)
        
        # Prepare message for broadcast
        message_obj = {
            "id": db_message.id,
            "content": db_message.content,
            "message_type": db_message.message_type,
            "created_at": db_message.created_at.isoformat(),
            "chat_group_id": db_message.chat_group_id,
            "user_id": db_message.user_id,
            "sender_name": user.name,
            "sender_profile_picture": user.profile_picture
        }
        
        broadcast_data = {
            "type": "message",
            "message": message_obj
        }
        
        # Broadcast to all connected users in the chat group
        await connection_manager.broadcast(chat_group_id, broadcast_data)
        
        # Send push notification to users not currently connected
        connected_users = connection_manager.get_connected_users(chat_group_id)
        
        # If there are members not connected via WebSocket, send them a push notification
        if not all(member.user_id in connected_users for member in self.chat_repo.get_chat_group_members(chat_group_id)):
            # Create a short preview of the message (first 50 chars)
            message_preview = content[:50] + ("..." if len(content) > 50 else "")
            await self.notification_service.notify_chat_message(chat_group_id, user_id, message_preview)
            
        return db_message 