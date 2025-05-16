import httpx
import json
from typing import Optional
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.auth import create_access_token
from app.repositories.user_repository import UserRepository
from app.schemas.auth import GoogleUser

class AuthService:
    @staticmethod
    async def verify_google_token(code: str, redirect_uri: str) -> Optional[GoogleUser]:
        """
        Exchange authorization code for Google token and retrieve user info
        """
        # First, exchange authorization code for tokens
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code"
        }
        
        # If in development mode, we can return a mock user
        if settings.APP_ENV == "development" and (not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET):
            return GoogleUser(
                id="dev_google_id",
                email="dev@juka.app",
                name="開發者使用者",
                picture="https://via.placeholder.com/150"
            )
        
        async with httpx.AsyncClient() as client:
            token_response = await client.post(token_url, data=token_data)
            
            if token_response.status_code != 200:
                return None
                
            token_json = token_response.json()
            access_token = token_json.get("access_token")
            
            if not access_token:
                return None
                
            # Use access token to fetch user info
            userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
            headers = {"Authorization": f"Bearer {access_token}"}
            
            userinfo_response = await client.get(userinfo_url, headers=headers)
            
            if userinfo_response.status_code != 200:
                return None
                
            userinfo = userinfo_response.json()
            
            return GoogleUser(
                id=userinfo.get("id"),
                email=userinfo.get("email"),
                name=userinfo.get("name"),
                picture=userinfo.get("picture")
            )
    
    @staticmethod
    def authenticate_user(db: Session, google_user: GoogleUser, fcm_token: Optional[str] = None) -> tuple:
        """
        Authenticate a user with Google credentials
        Returns (user, token, is_new_user)
        """
        user_repo = UserRepository(db)
        
        # Check if user exists
        user = user_repo.get_user_by_google_id(google_user.id)
        is_new_user = False
        
        # Create new user if doesn't exist
        if not user:
            user = user_repo.create_user(
                email=google_user.email,
                name=google_user.name,
                profile_picture=google_user.picture,
                google_id=google_user.id,
                fcm_token=fcm_token
            )
            is_new_user = True
        elif fcm_token:
            # Update FCM token if provided
            user = user_repo.update_fcm_token(user.id, fcm_token)
            
        # Create access token
        token_data = {"sub": str(user.id)}
        access_token = create_access_token(token_data)
        
        return user, access_token, is_new_user 