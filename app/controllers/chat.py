from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.auth import get_current_user
from app.services.chat_service import connection_manager, ChatService
from app.repositories.chat_repository import ChatRepository
from app.models.user import User as UserModel
from app.schemas.chat import ChatGroup, ChatGroupCreate, Message, ChatGroupWithMembers

router = APIRouter()

@router.get("/groups", response_model=List[ChatGroup])
async def get_chat_groups(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get all chat groups for the current user
    """
    chat_repo = ChatRepository(db)
    chat_groups = chat_repo.get_chat_groups_for_user(current_user.id)
    return chat_groups

@router.get("/groups/{chat_group_id}", response_model=ChatGroupWithMembers)
async def get_chat_group(
    chat_group_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get a chat group by ID
    """
    chat_repo = ChatRepository(db)
    
    # Check if chat group exists
    chat_group = chat_repo.get_chat_group_by_id(chat_group_id)
    if not chat_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="找不到此聊天室"
        )
    
    # Check if user is a member
    if not chat_repo.is_chat_member(chat_group_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您不是此聊天室的成員"
        )
    
    # Get members
    members = chat_repo.get_chat_group_members(chat_group_id)
    member_ids = [member.user_id for member in members]
    
    # Create response
    response = ChatGroupWithMembers(
        id=chat_group.id,
        name=chat_group.name,
        is_direct=chat_group.is_direct,
        created_at=chat_group.created_at,
        updated_at=chat_group.updated_at,
        campaign_id=chat_group.campaign_id,
        members=member_ids
    )
    
    return response

@router.post("/groups", response_model=ChatGroup)
async def create_chat_group(
    group_data: ChatGroupCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Create a new chat group
    """
    chat_repo = ChatRepository(db)
    
    # Ensure creator is in the member list
    if current_user.id not in group_data.member_ids:
        group_data.member_ids.insert(0, current_user.id)
    
    # Create group
    chat_group = chat_repo.create_chat_group(group_data)
    return chat_group

@router.post("/direct/{user_id}", response_model=ChatGroup)
async def create_direct_chat(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Create or get direct chat with another user
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能與自己創建私聊"
        )
    
    chat_repo = ChatRepository(db)
    
    # Check if other user exists
    other_user = chat_repo.get_user(user_id)
    if not other_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="使用者不存在"
        )
    
    # Check if direct chat already exists
    existing_chat = chat_repo.get_direct_chat_between_users(current_user.id, user_id)
    if existing_chat:
        return existing_chat
    
    # Create new direct chat
    group_name = f"{current_user.name} & {other_user.name}"
    group_data = ChatGroupCreate(
        name=group_name,
        is_direct=True,
        member_ids=[current_user.id, user_id]
    )
    
    chat_group = chat_repo.create_chat_group(group_data)
    return chat_group

@router.get("/groups/{chat_group_id}/messages", response_model=List[Message])
async def get_chat_messages(
    chat_group_id: int,
    limit: int = 50,
    before_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get messages from a chat group
    """
    chat_repo = ChatRepository(db)
    
    # Check if chat group exists
    chat_group = chat_repo.get_chat_group_by_id(chat_group_id)
    if not chat_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="找不到此聊天室"
        )
    
    # Check if user is a member
    if not chat_repo.is_chat_member(chat_group_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您不是此聊天室的成員"
        )
    
    # Get messages
    messages = chat_repo.get_chat_messages(chat_group_id, limit, before_id)
    
    # Add sender info
    for message in messages:
        sender = chat_repo.get_user(message.user_id)
        if sender:
            message.sender_name = sender.name
            message.sender_profile_picture = sender.profile_picture
    
    return messages

@router.websocket("/ws/{chat_group_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    chat_group_id: int, 
    token: str
):
    """
    WebSocket endpoint for real-time chat
    """
    # Validate token
    from jose import jwt, JWTError
    from app.core.config import settings
    from app.core.database import SessionLocal
    
    try:
        # Verify token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = int(payload.get("sub"))
        
        # Get DB session
        db = SessionLocal()
        
        try:
            # Check if user exists
            chat_repo = ChatRepository(db)
            user = chat_repo.get_user(user_id)
            if not user:
                await websocket.close(code=1008, reason="Invalid user")
                return
                
            # Check if user is member of chat group
            if not chat_repo.is_chat_member(chat_group_id, user_id):
                await websocket.close(code=1008, reason="Not a member of this chat group")
                return
                
            # Accept connection
            await connection_manager.connect(websocket, chat_group_id, user_id)
            
            chat_service = ChatService(db)
            
            try:
                while True:
                    # Receive and process messages
                    data = await websocket.receive_text()
                    import json
                    message_data = json.loads(data)
                    
                    # Handle message
                    await chat_service.handle_message(websocket, user_id, message_data)
                    
            except WebSocketDisconnect:
                connection_manager.disconnect(websocket)
                
            except Exception as e:
                print(f"WebSocket error: {e}")
                connection_manager.disconnect(websocket)
                
        finally:
            db.close()
            
    except JWTError:
        await websocket.close(code=1008, reason="Invalid token")
        return 