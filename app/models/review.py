from sqlalchemy import Column, String, Integer, ForeignKey, Text, Float
from sqlalchemy.orm import relationship

from app.models.base import BaseModel

class Review(BaseModel):
    __tablename__ = "reviews"

    # Who wrote the review
    reviewer_id = Column(Integer, ForeignKey("users.id"))
    reviewer = relationship("User", foreign_keys=[reviewer_id], back_populates="given_reviews")
    
    # Who got reviewed
    reviewed_id = Column(Integer, ForeignKey("users.id"))
    reviewed = relationship("User", foreign_keys=[reviewed_id], back_populates="received_reviews")
    
    # Related campaign
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    
    # Review content
    rating = Column(Float, nullable=False)  # 1-5 star rating
    comment = Column(Text, nullable=True)
    
    # Additional attributes could be added for more detailed reviews 