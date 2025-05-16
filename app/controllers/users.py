from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.auth import get_current_user
from app.repositories.user_repository import UserRepository
from app.repositories.review_repository import ReviewRepository
from app.models.user import User as UserModel
from app.schemas.user import User, UserUpdate, UserLocationUpdate, FriendOperation, FCMTokenUpdate
from app.schemas.review import Review

router = APIRouter()

@router.get("/", response_model=List[User])
async def get_users(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get list of users (admin only in production)
    """
    from app.core.config import settings
    
    # In production, restrict to admin
    if settings.APP_ENV != "development":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="僅開發環境可用"
        )
        
    user_repo = UserRepository(db)
    users = db.query(UserModel).offset(skip).limit(limit).all()
    return users

@router.get("/{user_id}", response_model=User)
async def get_user(
    user_id: int, 
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get user by ID
    """
    user_repo = UserRepository(db)
    user = user_repo.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="使用者不存在"
        )
        
    return user

@router.put("/me", response_model=User)
async def update_user(
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Update current user profile
    """
    user_repo = UserRepository(db)
    updated_user = user_repo.update_user(current_user.id, user_data)
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="使用者不存在"
        )
        
    return updated_user

@router.put("/me/location", response_model=User)
async def update_user_location(
    location: UserLocationUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Update current user location
    """
    user_repo = UserRepository(db)
    updated_user = user_repo.update_user_location(current_user.id, location)
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="使用者不存在"
        )
        
    return updated_user

@router.put("/me/fcm-token", response_model=User)
async def update_fcm_token(
    token_data: FCMTokenUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Update FCM token for push notifications
    """
    user_repo = UserRepository(db)
    updated_user = user_repo.update_fcm_token(current_user.id, token_data.fcm_token)
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="使用者不存在"
        )
        
    return updated_user

@router.get("/me/friends", response_model=List[User])
async def get_friends(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get current user's friends
    """
    user_repo = UserRepository(db)
    friends = user_repo.get_user_friends(current_user.id)
    return friends

@router.post("/me/friends", response_model=User)
async def add_friend(
    friend_data: FriendOperation,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Add a friend
    """
    if friend_data.friend_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能添加自己為好友"
        )
        
    user_repo = UserRepository(db)
    
    # Check if friend exists
    friend = user_repo.get_user_by_id(friend_data.friend_id)
    if not friend:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="使用者不存在"
        )
        
    # Add friend
    success = user_repo.add_friend(current_user.id, friend_data.friend_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="添加好友失敗"
        )
        
    return friend

@router.delete("/me/friends/{friend_id}", response_model=dict)
async def remove_friend(
    friend_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Remove a friend
    """
    user_repo = UserRepository(db)
    
    # Check if friend exists
    friend = user_repo.get_user_by_id(friend_id)
    if not friend:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="使用者不存在"
        )
        
    # Remove friend
    success = user_repo.remove_friend(current_user.id, friend_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="刪除好友失敗"
        )
        
    return {"status": "success", "message": "成功刪除好友關係"}

@router.get("/{user_id}/reviews", response_model=List[Review])
async def get_user_reviews(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get reviews received by a user
    """
    review_repo = ReviewRepository(db)
    reviews = review_repo.get_reviews_by_reviewed(user_id)
    
    for review in reviews:
        reviewer = db.query(UserModel).filter(UserModel.id == review.reviewer_id).first()
        reviewed = db.query(UserModel).filter(UserModel.id == review.reviewed_id).first()
        
        if reviewer:
            review.reviewer_name = reviewer.name
            
        if reviewed:
            review.reviewed_name = reviewed.name
            
    return reviews 