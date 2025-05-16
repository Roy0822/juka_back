from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from typing import List, Optional

from app.models.business import Business
from app.schemas.business import BusinessCreate, BusinessUpdate

class BusinessRepository:
    def __init__(self, db: Session):
        self.db = db
        
    def get_business_by_id(self, business_id: int) -> Optional[Business]:
        return self.db.query(Business).filter(Business.id == business_id).first()
        
    def get_businesses(self, skip: int = 0, limit: int = 100) -> List[Business]:
        return self.db.query(Business).offset(skip).limit(limit).all()
        
    def create_business(self, business_data: BusinessCreate) -> Business:
        business_dict = business_data.dict()
        business = Business(**business_dict)
        
        self.db.add(business)
        self.db.commit()
        self.db.refresh(business)
        
        return business
        
    def update_business(self, business_id: int, business_data: BusinessUpdate) -> Optional[Business]:
        business = self.get_business_by_id(business_id)
        if not business:
            return None
            
        # Update business attributes
        for field, value in business_data.dict(exclude_unset=True).items():
            setattr(business, field, value)
            
        # Update location if coordinates are provided
        if business_data.latitude and business_data.longitude:
            business.latitude = business_data.latitude
            business.longitude = business_data.longitude
            business.location = text(f"ST_SetSRID(ST_MakePoint({business_data.longitude}, {business_data.latitude}), 4326)")
            
        self.db.commit()
        self.db.refresh(business)
        return business
        
    def delete_business(self, business_id: int) -> bool:
        business = self.get_business_by_id(business_id)
        if not business:
            return False
            
        self.db.delete(business)
        self.db.commit()
        return True
        
    def get_nearby_businesses(self, latitude: float, longitude: float, radius_km: float, limit: int = 10) -> List[Business]:
        """Get businesses within a certain radius (in kilometers)"""
        point = f"ST_SetSRID(ST_MakePoint({longitude}, {latitude}), 4326)"
        
        nearby_businesses = self.db.query(Business).filter(
            text(f"ST_DWithin(location, {point}::geography, {radius_km * 1000})")
        ).order_by(
            text(f"ST_Distance(location, {point}::geography)")
        ).limit(limit).all()
        
        return nearby_businesses 