from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.review import Review
from app.schemas.review import ReviewCreate

class ReviewRepository:
    def __init__(self, db: Session):
        self.db = db
        
    def get_review_by_id(self, review_id: int) -> Optional[Review]:
        return self.db.query(Review).filter(Review.id == review_id).first()
        
    def get_reviews_by_reviewer(self, reviewer_id: int) -> List[Review]:
        return self.db.query(Review).filter(Review.reviewer_id == reviewer_id).all()
        
    def get_reviews_by_reviewed(self, reviewed_id: int) -> List[Review]:
        return self.db.query(Review).filter(Review.reviewed_id == reviewed_id).all()
        
    def get_reviews_by_campaign(self, campaign_id: int) -> List[Review]:
        return self.db.query(Review).filter(Review.campaign_id == campaign_id).all()
        
    def create_review(self, reviewer_id: int, review_data: ReviewCreate) -> Review:
        review = Review(
            reviewer_id=reviewer_id,
            reviewed_id=review_data.reviewed_id,
            campaign_id=review_data.campaign_id,
            rating=review_data.rating,
            comment=review_data.comment
        )
        
        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)
        
        return review
        
    def update_review(self, review_id: int, rating: float, comment: Optional[str] = None) -> Optional[Review]:
        review = self.get_review_by_id(review_id)
        if not review:
            return None
            
        review.rating = rating
        if comment is not None:
            review.comment = comment
            
        self.db.commit()
        self.db.refresh(review)
        return review
        
    def delete_review(self, review_id: int) -> bool:
        review = self.get_review_by_id(review_id)
        if not review:
            return False
            
        self.db.delete(review)
        self.db.commit()
        return True
        
    def get_user_average_rating(self, user_id: int) -> Optional[float]:
        """Get the average rating for a user"""
        from sqlalchemy import func
        
        result = self.db.query(func.avg(Review.rating)).filter(Review.reviewed_id == user_id).scalar()
        return float(result) if result else None 