from sqlalchemy import Column, String, Float, Boolean
from sqlalchemy.orm import relationship
from geoalchemy2 import Geography
from sqlalchemy.sql.expression import text

from app.models.base import BaseModel

class Business(BaseModel):
    __tablename__ = "businesses"

    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    
    # Location
    address = Column(String)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    location = Column(Geography(geometry_type='POINT', srid=4326), nullable=True)
    
    # Contact info
    phone = Column(String, nullable=True)
    website = Column(String, nullable=True)
    
    # Business details
    category = Column(String, nullable=True)
    logo_url = Column(String, nullable=True)
    is_verified = Column(Boolean, default=False)
    
    # Relationships
    campaigns = relationship("Campaign", back_populates="business")
    
    def __init__(self, **kwargs):
        super(Business, self).__init__(**kwargs)
        
        # Create geography point from lat/long if provided
        if 'latitude' in kwargs and 'longitude' in kwargs and kwargs['latitude'] and kwargs['longitude']:
            self.location = text(f"ST_SetSRID(ST_MakePoint({kwargs['longitude']}, {kwargs['latitude']}), 4326)") 