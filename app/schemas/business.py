from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Base Business schema
class BusinessBase(BaseModel):
    name: str
    description: Optional[str] = None
    address: str
    latitude: float
    longitude: float
    phone: Optional[str] = None
    website: Optional[str] = None
    category: Optional[str] = None
    logo_url: Optional[str] = None
    
# Schema for creating a business
class BusinessCreate(BusinessBase):
    pass
    
# Schema for updating a business
class BusinessUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    category: Optional[str] = None
    logo_url: Optional[str] = None
    
# Schema for returning a business
class Business(BusinessBase):
    id: int
    created_at: datetime
    updated_at: datetime
    is_verified: bool
    
    class Config:
        orm_mode = True 