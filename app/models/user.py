from sqlalchemy import Column, String, Float, Boolean, Table, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text
from geoalchemy2 import Geography

from app.models.base import BaseModel

# Association table for user friendships
friendship = Table(
    'friendship',
    BaseModel.metadata,
    Column('user_id', ForeignKey('users.id'), primary_key=True),
    Column('friend_id', ForeignKey('users.id'), primary_key=True)
)

class User(BaseModel):
    __tablename__ = "users"

    email = Column(String, unique=True, index=True)
    name = Column(String)
    profile_picture = Column(String, nullable=True)
    google_id = Column(String, unique=True, index=True)
    
    # Location data
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    location = Column(Geography(geometry_type='POINT', srid=4326), nullable=True)
    
    # FCM token for push notifications
    fcm_token = Column(String, nullable=True)
    
    # Preferences (can be extended)
    preferences = Column(String, nullable=True)  # JSON string with user preferences
    
    # Relationships
    friends = relationship(
        "User",
        secondary=friendship,
        primaryjoin="User.id == friendship.c.user_id",
        secondaryjoin="User.id == friendship.c.friend_id",
        backref="friended_by",
        viewonly=True
    )
    
    # Campaign relationships
    created_campaigns = relationship("Campaign", back_populates="creator")
    joined_campaigns = relationship("UserCampaign", back_populates="user")
    
    # Review relationships
    given_reviews = relationship("Review", foreign_keys="Review.reviewer_id", back_populates="reviewer")
    received_reviews = relationship("Review", foreign_keys="Review.reviewed_id", back_populates="reviewed")
    
    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        
        # Create geography point from lat/long if provided
        if 'latitude' in kwargs and 'longitude' in kwargs and kwargs['latitude'] and kwargs['longitude']:
            self.location = text(f"ST_SetSRID(ST_MakePoint({kwargs['longitude']}, {kwargs['latitude']}), 4326)") 