from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Boolean, Text, Enum
from sqlalchemy.orm import relationship
from geoalchemy2 import Geography
from sqlalchemy.sql.expression import text
from datetime import datetime
import enum

from app.models.base import BaseModel

class CampaignCategory(str, enum.Enum):
    COFFEE = "咖啡優惠"
    FOOD = "美食優惠"
    RIDE_SHARING = "共乘"
    SHOPPING = "購物優惠"
    ENTERTAINMENT = "娛樂"
    OTHER = "其他"

class Campaign(BaseModel):
    __tablename__ = "campaigns"

    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    image_url = Column(String, nullable=True)
    
    # Category
    category = Column(Enum(CampaignCategory), default=CampaignCategory.OTHER, nullable=False)
    
    # Location
    address = Column(String, nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    location = Column(Geography(geometry_type='POINT', srid=4326), nullable=False)
    
    # Campaign details
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    max_participants = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Creator relationship
    creator_id = Column(Integer, ForeignKey("users.id"))
    creator = relationship("User", back_populates="created_campaigns")
    
    # Business relationship (optional)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=True)
    business = relationship("Business", back_populates="campaigns")
    
    # Participant relationships
    participants = relationship("UserCampaign", back_populates="campaign")
    
    # Chat group
    chat_group_id = Column(Integer, ForeignKey("chat_groups.id"), nullable=True)
    chat_group = relationship("ChatGroup", back_populates="campaign")
    
    def __init__(self, **kwargs):
        super(Campaign, self).__init__(**kwargs)
        
        # Create geography point from lat/long
        if 'latitude' in kwargs and 'longitude' in kwargs:
            self.location = text(f"ST_SetSRID(ST_MakePoint({kwargs['longitude']}, {kwargs['latitude']}), 4326)")

class UserCampaign(BaseModel):
    __tablename__ = "user_campaigns"

    user_id = Column(Integer, ForeignKey("users.id"))
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    joined_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="joined_campaigns")
    campaign = relationship("Campaign", back_populates="participants") 