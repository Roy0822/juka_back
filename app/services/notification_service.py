from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.core.fcm import FCMService
from app.repositories.user_repository import UserRepository
from app.repositories.campaign_repository import CampaignRepository
from app.models.user import User
from app.models.campaign import Campaign

class NotificationService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.campaign_repo = CampaignRepository(db)
        
    async def notify_campaign_created(self, campaign_id: int, radius_km: float = 5.0, limit: int = 50):
        """
        Notify nearby users about a new campaign
        """
        campaign = self.campaign_repo.get_campaign_by_id(campaign_id)
        if not campaign:
            return False
            
        # Get nearby users
        nearby_users = self.user_repo.get_nearby_users(
            campaign.latitude, 
            campaign.longitude,
            radius_km,
            limit
        )
        
        # Filter out users without FCM tokens
        users_with_tokens = [user for user in nearby_users if user.fcm_token and user.id != campaign.creator_id]
        
        if not users_with_tokens:
            return False
            
        # Get creator
        creator = self.user_repo.get_user_by_id(campaign.creator_id)
        
        # Send notifications
        tokens = [user.fcm_token for user in users_with_tokens]
        
        data = {
            "campaign_id": str(campaign.id),
            "type": "new_campaign"
        }
        
        await FCMService.send_multicast(
            tokens=tokens,
            title=f"新措團: {campaign.title}",
            body=f"{creator.name} 創建了一個新措團，點擊查看詳情",
            data=data
        )
        
        return True
        
    async def notify_user_joined_campaign(self, campaign_id: int, user_id: int):
        """
        Notify campaign creator and other participants when a user joins
        """
        campaign = self.campaign_repo.get_campaign_by_id(campaign_id)
        if not campaign:
            return False
            
        user = self.user_repo.get_user_by_id(user_id)
        if not user:
            return False
            
        # Get all participants including creator
        participants = [p[0] for p in self.campaign_repo.get_campaign_participants(campaign_id)]
        
        # Filter out the user who just joined and those without FCM tokens
        recipients = [p for p in participants if p.id != user_id and p.fcm_token]
        
        if not recipients:
            return False
            
        tokens = [p.fcm_token for p in recipients]
        
        data = {
            "campaign_id": str(campaign.id),
            "user_id": str(user.id),
            "type": "user_joined"
        }
        
        await FCMService.send_multicast(
            tokens=tokens,
            title=f"新成員加入「{campaign.title}」",
            body=f"{user.name} 加入了你的措團",
            data=data
        )
        
        return True
        
    async def notify_campaign_update(self, campaign_id: int, update_type: str, message: str):
        """
        Notify all participants about a campaign update
        """
        campaign = self.campaign_repo.get_campaign_by_id(campaign_id)
        if not campaign:
            return False
            
        # Get all participants
        participants = [p[0] for p in self.campaign_repo.get_campaign_participants(campaign_id)]
        
        # Filter out those without FCM tokens
        recipients = [p for p in participants if p.fcm_token]
        
        if not recipients:
            return False
            
        tokens = [p.fcm_token for p in recipients]
        
        data = {
            "campaign_id": str(campaign.id),
            "type": f"campaign_{update_type}"
        }
        
        await FCMService.send_multicast(
            tokens=tokens,
            title=f"措團更新：{campaign.title}",
            body=message,
            data=data
        )
        
        return True
        
    async def notify_chat_message(self, chat_group_id: int, sender_id: int, message_preview: str):
        """
        Notify chat group members about a new message
        """
        from app.repositories.chat_repository import ChatRepository
        chat_repo = ChatRepository(self.db)
        
        # Get chat members excluding sender
        members = chat_repo.get_chat_group_members(chat_group_id)
        if not members:
            return False
            
        # Filter out sender and those without FCM tokens
        recipients = [m.user for m in members if m.user_id != sender_id and m.user.fcm_token]
        
        if not recipients:
            return False
            
        # Get sender and chat group
        sender = self.user_repo.get_user_by_id(sender_id)
        chat_group = chat_repo.get_chat_group_by_id(chat_group_id)
        
        if not sender or not chat_group:
            return False
            
        tokens = [r.fcm_token for r in recipients]
        
        data = {
            "chat_group_id": str(chat_group_id),
            "sender_id": str(sender_id),
            "type": "new_message"
        }
        
        await FCMService.send_multicast(
            tokens=tokens,
            title=f"來自 {chat_group.name} 的新訊息",
            body=f"{sender.name}: {message_preview}",
            data=data
        )
        
        return True 