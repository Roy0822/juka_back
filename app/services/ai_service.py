import httpx
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from app.core.config import settings
from app.repositories.campaign_repository import CampaignRepository
from app.repositories.user_repository import UserRepository
from app.services.notification_service import NotificationService
from app.schemas.ai import CaptionGenerateRequest, CaptionGenerateResponse, RecommendationPushRequest, RecommendationPushResponse

class AIService:
    def __init__(self, db: Session):
        self.db = db
        self.campaign_repo = CampaignRepository(db)
        self.user_repo = UserRepository(db)
        self.notification_service = NotificationService(db)
        
    async def generate_caption(self, request: CaptionGenerateRequest) -> Optional[CaptionGenerateResponse]:
        """
        Call the AI service to generate a caption for an image
        """
        if settings.APP_ENV == "development":
            # In development mode, return mock data
            return CaptionGenerateResponse(
                caption="這是一杯精緻的手沖咖啡，香氣四溢！買一送一，快來享用！",
                tags=["咖啡", "手沖", "優惠", "買一送一"]
            )
            
        # Call the AI service
        url = f"{settings.AI_SERVER_URL}/generate-caption"
        headers = {"Authorization": f"Bearer {settings.AI_ACCESS_TOKEN}"}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers=headers,
                    json=request.dict()
                )
                
                if response.status_code == 200:
                    return CaptionGenerateResponse(**response.json())
                else:
                    return None
        except Exception:
            return None
            
    async def push_recommendation(self, request: RecommendationPushRequest) -> Optional[RecommendationPushResponse]:
        """
        Push campaign recommendations to users based on AI recommendations
        Steps:
        1. Call AI service to get recommended users
        2. Send notifications to those users
        """
        campaign = self.campaign_repo.get_campaign_by_id(request.campaign_id)
        if not campaign:
            return RecommendationPushResponse(
                notified_users_count=0,
                status="failed"
            )
            
        if settings.APP_ENV == "development":
            # In development mode, use simple proximity-based recommendation
            # Get nearby users within radius
            nearby_users = self.user_repo.get_nearby_users(
                campaign.latitude, 
                campaign.longitude,
                request.radius_km,
                request.max_users
            )
            
            # Filter out users without FCM tokens and the creator
            users_to_notify = [
                u for u in nearby_users 
                if u.fcm_token and u.id != campaign.creator_id
            ]
            
            # Send notifications
            if users_to_notify:
                await self.notification_service.notify_campaign_created(
                    campaign.id, 
                    request.radius_km, 
                    request.max_users
                )
                
            return RecommendationPushResponse(
                notified_users_count=len(users_to_notify),
                status="success"
            )
        
        # Call the AI service for recommendations
        url = f"{settings.AI_SERVER_URL}/push-recommendation"
        headers = {"Authorization": f"Bearer {settings.AI_ACCESS_TOKEN}"}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers=headers,
                    json=request.dict()
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return RecommendationPushResponse(**result)
                else:
                    # Fallback to simple proximity-based notification
                    await self.notification_service.notify_campaign_created(
                        campaign.id, 
                        request.radius_km, 
                        request.max_users
                    )
                    
                    return RecommendationPushResponse(
                        notified_users_count=0,  # We don't know the exact count
                        status="fallback_success"
                    )
        except Exception:
            # Fallback to simple proximity-based notification
            await self.notification_service.notify_campaign_created(
                campaign.id, 
                request.radius_km, 
                request.max_users
            )
            
            return RecommendationPushResponse(
                notified_users_count=0,  # We don't know the exact count
                status="fallback_success"
            ) 