from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from datetime import datetime

from app.core.database import get_db
from app.core.auth import get_current_user
from app.repositories.campaign_repository import CampaignRepository
from app.repositories.user_repository import UserRepository
from app.repositories.chat_repository import ChatRepository
from app.repositories.review_repository import ReviewRepository
from app.services.notification_service import NotificationService
from app.models.user import User as UserModel
from app.models.campaign import Campaign as CampaignModel, CampaignCategory as CampaignCategoryModel
from app.schemas.campaign import (
    Campaign, CampaignCreate, CampaignUpdate, 
    CampaignNearbySearch, CampaignJoin, CampaignCategory
)
from app.schemas.review import Review, ReviewCreate
from app.schemas.chat import ChatGroupCreate

router = APIRouter()

@router.post("/", response_model=Campaign)
async def create_campaign(
    campaign_data: CampaignCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Create a new campaign
    """
    campaign_repo = CampaignRepository(db)
    chat_repo = ChatRepository(db)
    
    # Create campaign
    campaign = campaign_repo.create_campaign(current_user.id, campaign_data)
    
    # Create chat group for the campaign
    chat_group = chat_repo.create_chat_group(
        ChatGroupCreate(
            name=campaign.title,
            is_direct=False,
            member_ids=[current_user.id],
            campaign_id=campaign.id
        )
    )
    
    # Update campaign with chat group
    campaign_repo.update_campaign(
        campaign.id, 
        CampaignUpdate(chat_group_id=chat_group.id)
    )
    
    # Notify nearby users (async)
    notification_service = NotificationService(db)
    await notification_service.notify_campaign_created(campaign.id)
    
    # Include participant count in response
    setattr(campaign, "participant_count", 1)  # Creator is first participant
    
    return campaign

@router.get("/", response_model=List[Campaign])
async def get_campaigns(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get all campaigns
    """
    campaign_repo = CampaignRepository(db)
    campaigns = db.query(CampaignModel).offset(skip).limit(limit).all()
    
    # Add participant count to each campaign
    for campaign in campaigns:
        participants = campaign_repo.get_campaign_participants(campaign.id)
        setattr(campaign, "participant_count", len(participants))
    
    return campaigns

@router.get("/mine", response_model=List[Campaign])
async def get_my_campaigns(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get campaigns created by the current user
    """
    campaign_repo = CampaignRepository(db)
    campaigns = campaign_repo.get_campaigns_by_creator(current_user.id)
    
    # Add participant count to each campaign
    for campaign in campaigns:
        participants = campaign_repo.get_campaign_participants(campaign.id)
        setattr(campaign, "participant_count", len(participants))
    
    return campaigns

@router.get("/joined", response_model=List[Campaign])
async def get_joined_campaigns(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get campaigns joined by the current user
    """
    campaign_repo = CampaignRepository(db)
    campaigns = campaign_repo.get_user_joined_campaigns(current_user.id)
    
    # Add participant count to each campaign
    for campaign in campaigns:
        participants = campaign_repo.get_campaign_participants(campaign.id)
        setattr(campaign, "participant_count", len(participants))
    
    return campaigns

@router.post("/nearby", response_model=List[Campaign])
async def get_nearby_campaigns(
    search: CampaignNearbySearch,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get campaigns near a location
    """
    campaign_repo = CampaignRepository(db)
    campaigns = campaign_repo.get_nearby_campaigns(
        search.latitude,
        search.longitude,
        search.radius,
        search.limit,
        search.category
    )
    
    # Add participant count to each campaign
    for campaign in campaigns:
        participants = campaign_repo.get_campaign_participants(campaign.id)
        setattr(campaign, "participant_count", len(participants))
    
    return campaigns

@router.get("/{campaign_id}", response_model=Campaign)
async def get_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get a campaign by ID
    """
    campaign_repo = CampaignRepository(db)
    campaign = campaign_repo.get_campaign_by_id(campaign_id)
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="找不到此揪團"
        )
    
    # Add participant count
    participants = campaign_repo.get_campaign_participants(campaign.id)
    setattr(campaign, "participant_count", len(participants))
    
    return campaign

@router.put("/{campaign_id}", response_model=Campaign)
async def update_campaign(
    campaign_id: int,
    campaign_data: CampaignUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Update a campaign
    """
    campaign_repo = CampaignRepository(db)
    campaign = campaign_repo.get_campaign_by_id(campaign_id)
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="找不到此揪團"
        )
        
    # Check if user is the creator
    if campaign.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有揪團建立者可以修改揪團"
        )
    
    # Update campaign
    updated_campaign = campaign_repo.update_campaign(campaign_id, campaign_data)
    
    # Notify participants of update
    notification_service = NotificationService(db)
    await notification_service.notify_campaign_update(
        campaign_id,
        "update",
        f"揪團「{campaign.title}」已更新"
    )
    
    # Add participant count
    participants = campaign_repo.get_campaign_participants(updated_campaign.id)
    setattr(updated_campaign, "participant_count", len(participants))
    
    return updated_campaign

@router.delete("/{campaign_id}", response_model=dict)
async def delete_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Delete a campaign
    """
    campaign_repo = CampaignRepository(db)
    campaign = campaign_repo.get_campaign_by_id(campaign_id)
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="找不到此揪團"
        )
        
    # Check if user is the creator
    if campaign.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有揪團建立者可以刪除揪團"
        )
    
    # Notify participants of deletion
    notification_service = NotificationService(db)
    await notification_service.notify_campaign_update(
        campaign_id,
        "delete",
        f"揪團「{campaign.title}」已被刪除"
    )
    
    # Delete campaign
    success = campaign_repo.delete_campaign(campaign_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="刪除揪團失敗"
        )
    
    return {"status": "success", "message": "成功刪除揪團"}

@router.post("/join", response_model=dict)
async def join_campaign(
    join_data: CampaignJoin,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Join a campaign
    """
    campaign_repo = CampaignRepository(db)
    chat_repo = ChatRepository(db)
    
    # Join campaign
    user_campaign = campaign_repo.join_campaign(current_user.id, join_data.campaign_id)
    
    if not user_campaign:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="加入揪團失敗，揪團可能已滿或不存在"
        )
    
    # Get campaign
    campaign = campaign_repo.get_campaign_by_id(join_data.campaign_id)
    
    # Add user to chat group
    if campaign.chat_group_id:
        chat_repo.add_chat_member(campaign.chat_group_id, current_user.id)
    
    # Notify other participants
    notification_service = NotificationService(db)
    await notification_service.notify_user_joined_campaign(join_data.campaign_id, current_user.id)
    
    return {"status": "success", "message": "成功加入揪團"}

@router.post("/{campaign_id}/leave", response_model=dict)
async def leave_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Leave a campaign
    """
    campaign_repo = CampaignRepository(db)
    chat_repo = ChatRepository(db)
    
    # Get campaign to check if user is creator
    campaign = campaign_repo.get_campaign_by_id(campaign_id)
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="找不到此揪團"
        )
    
    # Creator cannot leave their own campaign
    if campaign.creator_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="揪團建立者不能離開自己的揪團"
        )
    
    # Leave campaign
    success = campaign_repo.leave_campaign(current_user.id, campaign_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="離開揪團失敗"
        )
    
    # Remove user from chat group
    if campaign.chat_group_id:
        chat_repo.remove_chat_member(campaign.chat_group_id, current_user.id)
    
    return {"status": "success", "message": "成功離開揪團"}

@router.get("/{campaign_id}/participants", response_model=List[dict])
async def get_campaign_participants(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get participants of a campaign
    """
    campaign_repo = CampaignRepository(db)
    
    # Check if campaign exists
    campaign = campaign_repo.get_campaign_by_id(campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="找不到此揪團"
        )
    
    # Get participants
    participants_with_join_info = campaign_repo.get_campaign_participants(campaign_id)
    
    # Format response
    result = []
    for user, user_campaign in participants_with_join_info:
        result.append({
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "profile_picture": user.profile_picture,
            "joined_at": user_campaign.joined_at,
            "is_creator": user.id == campaign.creator_id
        })
    
    return result

@router.post("/{campaign_id}/reviews", response_model=Review)
async def create_review(
    campaign_id: int,
    review_data: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Create a review for another participant
    """
    campaign_repo = CampaignRepository(db)
    review_repo = ReviewRepository(db)
    user_repo = UserRepository(db)
    
    # Check if campaign exists
    campaign = campaign_repo.get_campaign_by_id(campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="找不到此揪團"
        )
    
    # Check if reviewer participated in the campaign
    participants = [p[0].id for p in campaign_repo.get_campaign_participants(campaign_id)]
    if current_user.id not in participants:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有揪團參與者可以評價其他參與者"
        )
    
    # Check if reviewed user participated in the campaign
    if review_data.reviewed_id not in participants:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="被評價的使用者不是此揪團的參與者"
        )
    
    # Check if reviewer is trying to review themselves
    if current_user.id == review_data.reviewed_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能評價自己"
        )
    
    # Create review
    review = review_repo.create_review(current_user.id, review_data)
    
    # Add names for response
    reviewer = user_repo.get_user_by_id(current_user.id)
    reviewed = user_repo.get_user_by_id(review_data.reviewed_id)
    
    review.reviewer_name = reviewer.name
    review.reviewed_name = reviewed.name
    
    return review

@router.get("/{campaign_id}/reviews", response_model=List[Review])
async def get_campaign_reviews(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get all reviews for a campaign
    """
    campaign_repo = CampaignRepository(db)
    review_repo = ReviewRepository(db)
    
    # Check if campaign exists
    campaign = campaign_repo.get_campaign_by_id(campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="找不到此揪團"
        )
    
    # Get reviews
    reviews = review_repo.get_reviews_by_campaign(campaign_id)
    
    # Add names
    for review in reviews:
        reviewer = db.query(UserModel).filter(UserModel.id == review.reviewer_id).first()
        reviewed = db.query(UserModel).filter(UserModel.id == review.reviewed_id).first()
        
        if reviewer:
            review.reviewer_name = reviewer.name
            
        if reviewed:
            review.reviewed_name = reviewed.name
    
    return reviews

@router.get("/categories", response_model=Dict[str, str])
async def get_campaign_categories():
    """
    Get all available campaign categories
    """
    return {category.name: category.value for category in CampaignCategory} 