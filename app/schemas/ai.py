from pydantic import BaseModel
from typing import Optional, List, Dict, Any

# Schema for AI caption generation
class CaptionGenerateRequest(BaseModel):
    image_url: str
    user_id: int
    
class CaptionGenerateResponse(BaseModel):
    caption: str
    tags: List[str]
    
# Schema for AI recommendation push
class RecommendationPushRequest(BaseModel):
    campaign_id: int
    max_users: Optional[int] = 50
    radius_km: Optional[float] = 10.0
    
class RecommendationPushResponse(BaseModel):
    notified_users_count: int
    status: str 