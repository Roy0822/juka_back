from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

# Base User schema
class UserBase(BaseModel):
    email: EmailStr
    name: str
    profile_picture: Optional[str] = None
    
# Schema for creating a new user
class UserCreate(UserBase):
    google_id: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    fcm_token: Optional[str] = None
    
# Schema for updating a user
class UserUpdate(BaseModel):
    name: Optional[str] = None
    profile_picture: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    fcm_token: Optional[str] = None
    preferences: Optional[str] = None
    
# Schema for returning a user
class User(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    preferences: Optional[str] = None
    
    class Config:
        orm_mode = True
        
# Schema for user location update
class UserLocationUpdate(BaseModel):
    latitude: float
    longitude: float
    
# Schema for friend operations
class FriendOperation(BaseModel):
    friend_id: int

# Schema for FCM token update
class FCMTokenUpdate(BaseModel):
    fcm_token: str 