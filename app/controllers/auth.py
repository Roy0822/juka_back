from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode, quote_plus

from app.core.database import get_db
from app.core.auth import get_current_user, get_dev_user
from app.services.auth_service import AuthService
from app.schemas.auth import GoogleAuthRequest, Token
from app.schemas.user import User
from app.core.config import settings

import base64
import json

router = APIRouter()

@router.get("/login/google")
async def login_google(request: Request):
    """
    Generate Google OAuth login URL for client-side redirection
    """
    # Construct the Google OAuth URL
    base_url = "https://accounts.google.com/o/oauth2/v2/auth"
    
    # Use configured redirect URI if available, otherwise build from request
    callback_url = settings.GOOGLE_REDIRECT_URI
    if not callback_url:
        callback_url = str(request.url_for("google_callback"))
    
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "response_type": "code",
        "scope": "openid email profile",
        "redirect_uri": callback_url,
        "access_type": "offline",
        "prompt": "consent"
    }
    
    # If in development mode, we can provide a simplified URL
    if settings.APP_ENV == "development" and (not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET):
        return {"auth_url": f"{callback_url}?code=dev_code"}
    
    auth_url = f"{base_url}?{urlencode(params)}"
    return {"auth_url": auth_url}

@router.get("/callback/google")
async def google_callback(request: Request, code: str, db: Session = Depends(get_db)):
    """
    Handle Google OAuth callback and redirect to the app with token
    """
    # Use configured redirect URI if available, otherwise build from request
    callback_url = settings.GOOGLE_REDIRECT_URI
    if not callback_url:
        callback_url = str(request.url_for("google_callback"))
    
    google_user = await AuthService.verify_google_token(code, callback_url)
    
    if not google_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無法驗證Google憑證",
        )
        
    user, access_token, is_new_user = AuthService.authenticate_user(db, google_user)
    
    # Redirect to the mobile app using custom URL scheme
    app_redirect_url = f"{settings.APP_SCHEME}auth-callback?access_token={quote_plus(access_token)}&user_id={user.id}&is_new_user={str(is_new_user).lower()}"
    
    return RedirectResponse(url=app_redirect_url)

@router.post("/google-login", response_model=Token)
async def google_login(auth_request: GoogleAuthRequest, db: Session = Depends(get_db)):
    """
    Exchange Google OAuth code for a JWT token (for web clients)
    """
    google_user = await AuthService.verify_google_token(auth_request.code, auth_request.redirect_uri)
    
    if not google_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無法驗證Google憑證",
        )
        
    user, access_token, is_new_user = AuthService.authenticate_user(db, google_user)
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/dev-login", response_model=Token)
async def dev_login(db: Session = Depends(get_db)):
    """
    Development mode login - only works in development environment
    """
    from app.core.auth import create_access_token
    
    dev_user = get_dev_user(db)
    
    # Create access token
    token_data = {"sub": str(dev_user.id)}
    access_token = create_access_token(token_data)
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user
    """
    return current_user 