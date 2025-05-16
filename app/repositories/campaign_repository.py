from sqlalchemy.orm import Session
from sqlalchemy.sql import text, func
from typing import List, Optional, Tuple

from app.models.campaign import Campaign, UserCampaign
from app.models.user import User
from app.schemas.campaign import CampaignCreate, CampaignUpdate, CampaignCategory

class CampaignRepository:
    def __init__(self, db: Session):
        self.db = db
        
    def get_campaign_by_id(self, campaign_id: int) -> Optional[Campaign]:
        return self.db.query(Campaign).filter(Campaign.id == campaign_id).first()
        
    def get_campaigns_by_creator(self, creator_id: int) -> List[Campaign]:
        return self.db.query(Campaign).filter(Campaign.creator_id == creator_id).all()
        
    def get_campaigns_by_business(self, business_id: int) -> List[Campaign]:
        return self.db.query(Campaign).filter(Campaign.business_id == business_id).all()
        
    def create_campaign(self, creator_id: int, campaign_data: CampaignCreate) -> Campaign:
        campaign_dict = campaign_data.dict()
        campaign = Campaign(**campaign_dict, creator_id=creator_id)
        
        self.db.add(campaign)
        self.db.commit()
        self.db.refresh(campaign)
        
        # Creator automatically joins their own campaign
        self.join_campaign(creator_id, campaign.id)
        
        return campaign
        
    def update_campaign(self, campaign_id: int, campaign_data: CampaignUpdate) -> Optional[Campaign]:
        campaign = self.get_campaign_by_id(campaign_id)
        if not campaign:
            return None
            
        # Update campaign attributes
        for field, value in campaign_data.dict(exclude_unset=True).items():
            setattr(campaign, field, value)
            
        self.db.commit()
        self.db.refresh(campaign)
        return campaign
        
    def delete_campaign(self, campaign_id: int) -> bool:
        campaign = self.get_campaign_by_id(campaign_id)
        if not campaign:
            return False
            
        # Delete all user-campaign associations first
        self.db.query(UserCampaign).filter(UserCampaign.campaign_id == campaign_id).delete()
        
        # Then delete the campaign
        self.db.delete(campaign)
        self.db.commit()
        return True
        
    def join_campaign(self, user_id: int, campaign_id: int) -> Optional[UserCampaign]:
        # Check if campaign exists and is active
        campaign = self.get_campaign_by_id(campaign_id)
        if not campaign or not campaign.is_active:
            return None
            
        # Check if user already joined
        existing = self.db.query(UserCampaign).filter(
            UserCampaign.user_id == user_id,
            UserCampaign.campaign_id == campaign_id
        ).first()
        
        if existing:
            return existing
            
        # Check if campaign is full
        if campaign.max_participants:
            participant_count = self.db.query(func.count(UserCampaign.id)).filter(
                UserCampaign.campaign_id == campaign_id
            ).scalar()
            
            if participant_count >= campaign.max_participants:
                return None
                
        # Join campaign
        user_campaign = UserCampaign(user_id=user_id, campaign_id=campaign_id)
        self.db.add(user_campaign)
        self.db.commit()
        self.db.refresh(user_campaign)
        
        return user_campaign
        
    def leave_campaign(self, user_id: int, campaign_id: int) -> bool:
        # Can't leave if you're the creator
        campaign = self.get_campaign_by_id(campaign_id)
        if not campaign or campaign.creator_id == user_id:
            return False
            
        # Delete user-campaign association
        deleted = self.db.query(UserCampaign).filter(
            UserCampaign.user_id == user_id,
            UserCampaign.campaign_id == campaign_id
        ).delete()
        
        self.db.commit()
        return deleted > 0
        
    def get_campaign_participants(self, campaign_id: int) -> List[Tuple[User, UserCampaign]]:
        return self.db.query(User, UserCampaign).join(
            UserCampaign, User.id == UserCampaign.user_id
        ).filter(UserCampaign.campaign_id == campaign_id).all()
        
    def get_nearby_campaigns(
        self, 
        latitude: float, 
        longitude: float, 
        radius_km: float, 
        limit: int = 10, 
        category: Optional[CampaignCategory] = None
    ) -> List[Campaign]:
        """Get campaigns within a certain radius (in kilometers)"""
        point = f"ST_SetSRID(ST_MakePoint({longitude}, {latitude}), 4326)"
        
        query = self.db.query(Campaign).filter(
            Campaign.is_active == True,
            text(f"ST_DWithin(location, {point}::geography, {radius_km * 1000})")
        )
        
        # Add category filter if specified
        if category:
            query = query.filter(Campaign.category == category)
        
        # Order by distance and limit results
        nearby_campaigns = query.order_by(
            text(f"ST_Distance(location, {point}::geography)")
        ).limit(limit).all()
        
        return nearby_campaigns
        
    def get_user_joined_campaigns(self, user_id: int) -> List[Campaign]:
        return self.db.query(Campaign).join(
            UserCampaign, Campaign.id == UserCampaign.campaign_id
        ).filter(UserCampaign.user_id == user_id).all() 