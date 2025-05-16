from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from typing import List, Optional

from app.models.user import User, friendship
from app.schemas.user import UserCreate, UserUpdate, UserLocationUpdate

class UserRepository:
    def __init__(self, db: Session):
        self.db = db
        
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()
        
    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()
        
    def get_user_by_google_id(self, google_id: str) -> Optional[User]:
        return self.db.query(User).filter(User.google_id == google_id).first()
        
    def create_user(self, **user_data) -> User:
        user = User(**user_data)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
        
    def update_user(self, user_id: int, user_data: UserUpdate) -> Optional[User]:
        user = self.get_user_by_id(user_id)
        if not user:
            return None
            
        # Update user attributes
        for field, value in user_data.dict(exclude_unset=True).items():
            setattr(user, field, value)
            
        # Update location if coordinates are provided
        if user_data.latitude and user_data.longitude:
            user.latitude = user_data.latitude
            user.longitude = user_data.longitude
            user.location = text(f"ST_SetSRID(ST_MakePoint({user_data.longitude}, {user_data.latitude}), 4326)")
            
        self.db.commit()
        self.db.refresh(user)
        return user
        
    def update_user_location(self, user_id: int, location_data: UserLocationUpdate) -> Optional[User]:
        user = self.get_user_by_id(user_id)
        if not user:
            return None
            
        user.latitude = location_data.latitude
        user.longitude = location_data.longitude
        user.location = text(f"ST_SetSRID(ST_MakePoint({location_data.longitude}, {location_data.latitude}), 4326)")
        
        self.db.commit()
        self.db.refresh(user)
        return user
        
    def update_fcm_token(self, user_id: int, fcm_token: str) -> Optional[User]:
        user = self.get_user_by_id(user_id)
        if not user:
            return None
            
        user.fcm_token = fcm_token
        self.db.commit()
        self.db.refresh(user)
        return user
        
    def get_nearby_users(self, latitude: float, longitude: float, radius_km: float, limit: int = 50) -> List[User]:
        """Get users within a certain radius (in kilometers)"""
        point = f"ST_SetSRID(ST_MakePoint({longitude}, {latitude}), 4326)"
        
        nearby_users = self.db.query(User).filter(
            text(f"ST_DWithin(location, {point}::geography, {radius_km * 1000})")
        ).limit(limit).all()
        
        return nearby_users
        
    def get_user_friends(self, user_id: int) -> List[User]:
        user = self.get_user_by_id(user_id)
        if not user:
            return []
            
        return user.friends
        
    def add_friend(self, user_id: int, friend_id: int) -> bool:
        user = self.get_user_by_id(user_id)
        friend = self.get_user_by_id(friend_id)
        
        if not user or not friend:
            return False
            
        if friend not in user.friends:
            user.friends.append(friend)
            self.db.commit()
            
        return True
        
    def remove_friend(self, user_id: int, friend_id: int) -> bool:
        user = self.get_user_by_id(user_id)
        friend = self.get_user_by_id(friend_id)
        
        if not user or not friend:
            return False
            
        if friend in user.friends:
            user.friends.remove(friend)
            self.db.commit()
            
        return True 