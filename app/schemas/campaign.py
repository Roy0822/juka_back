from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

# Campaign Category Enum
class CampaignCategory(str, Enum):
    COFFEE = "咖啡優惠"
    FOOD = "美食優惠"
    RIDE_SHARING = "共乘"
    SHOPPING = "購物優惠"
    ENTERTAINMENT = "娛樂"
    OTHER = "其他"

# Base Campaign schema
class CampaignBase(BaseModel):
    title: str
    description: Optional[str] = None
    latitude: float
    longitude: float
    address: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    max_participants: Optional[int] = None
    business_id: Optional[int] = None
    category: CampaignCategory = CampaignCategory.OTHER
    
# Schema for creating a campaign
class CampaignCreate(CampaignBase):
    image_url: Optional[str] = None
    
# Schema for updating a campaign
class CampaignUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    address: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    max_participants: Optional[int] = None
    is_active: Optional[bool] = None
    category: Optional[CampaignCategory] = None
    
# Schema for returning a campaign
class Campaign(CampaignBase):
    id: int
    created_at: datetime
    updated_at: datetime
    image_url: Optional[str] = None
    is_active: bool
    creator_id: int
    chat_group_id: Optional[int] = None
    participant_count: Optional[int] = None
    
    class Config:
        orm_mode = True
        
# Schema for nearby campaign search
class CampaignNearbySearch(BaseModel):
    latitude: float
    longitude: float
    radius: float = Field(default=5.0, description="Search radius in kilometers")
    limit: int = Field(default=10, description="Maximum number of results")
    category: Optional[CampaignCategory] = None
    
# Schema for joining a campaign
class CampaignJoin(BaseModel):
    campaign_id: int 