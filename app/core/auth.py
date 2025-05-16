from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User
from app.core.database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# Function to create access token
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    return encoded_jwt

# Function to verify access token and get current user
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="無效的認證憑證",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.id == user_id).first()
    
    if user is None:
        raise credentials_exception
        
    return user

# Development mode authentication helper
def get_dev_user(db: Session = Depends(get_db)):
    if settings.APP_ENV != "development":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="開發者模式僅在開發環境可用",
        )

    # Get or create a development user
    dev_user = db.query(User).filter(User.email == "dev@juka.app").first()
    
    if not dev_user:
        from app.repositories.user_repository import UserRepository
        user_repo = UserRepository(db)
        dev_user = user_repo.create_user(
            email="dev@juka.app",
            name="開發者使用者",
            profile_picture="https://via.placeholder.com/150",
            google_id="dev_google_id",
            latitude=25.0330,  # Taipei 101
            longitude=121.5654
        )
        
    return dev_user 