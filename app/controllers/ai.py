from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.core.config import settings
from app.services.ai_service import AIService
from app.repositories.campaign_repository import CampaignRepository
from app.models.user import User as UserModel
from app.schemas.ai import (
    CaptionGenerateRequest, CaptionGenerateResponse,
    RecommendationPushRequest, RecommendationPushResponse
)

router = APIRouter()

@router.post("/generate-caption", response_model=CaptionGenerateResponse)
async def generate_caption(
    request: CaptionGenerateRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Generate caption for an image using AI
    """
    # Check if the user is authorized
    if request.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="無權為其他用戶生成文案"
        )
        
    ai_service = AIService(db)
    caption_result = await ai_service.generate_caption(request)
    
    if not caption_result:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI服務暫時不可用，請稍後再試"
        )
        
    return caption_result

@router.post("/push-recommendation", response_model=RecommendationPushResponse)
async def push_recommendation(
    request: RecommendationPushRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Push campaign recommendations to users using AI
    """
    # Check if campaign exists and user is the creator
    campaign_repo = CampaignRepository(db)
    campaign = campaign_repo.get_campaign_by_id(request.campaign_id)
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="找不到此揪團"
        )
        
    if campaign.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有揪團建立者可以推送推薦"
        )
        
    ai_service = AIService(db)
    result = await ai_service.push_recommendation(request)
    
    if result.status == "failed":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="推送推薦失敗，請稍後再試"
        )
        
    return result

@router.get("/token-info", response_model=dict)
async def get_token_info(
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get info about AI service connection (dev only)
    """
    if settings.APP_ENV != "development":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="僅開發環境可用"
        )
        
    return {
        "ai_server_url": settings.AI_SERVER_URL,
        "token_status": "configured" if settings.AI_ACCESS_TOKEN else "missing",
        "environment": settings.APP_ENV
    } 