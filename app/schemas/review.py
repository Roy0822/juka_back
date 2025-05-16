from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# Base Review schema
class ReviewBase(BaseModel):
    rating: float = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    comment: Optional[str] = None
    
# Schema for creating a review
class ReviewCreate(ReviewBase):
    reviewed_id: int
    campaign_id: int
    
# Schema for returning a review
class Review(ReviewBase):
    id: int
    created_at: datetime
    reviewer_id: int
    reviewed_id: int
    campaign_id: int
    reviewer_name: Optional[str] = None
    reviewed_name: Optional[str] = None
    
    class Config:
        orm_mode = True 