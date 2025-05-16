import os
from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    APP_ENV: str = "development"
    DATABASE_URL: str
    
    # Firebase settings
    FCM_SERVER_KEY: Optional[str] = None  # Legacy method
    FCM_SERVICE_ACCOUNT_JSON: Optional[str] = None  # New recommended method
    FCM_AUTH_METHOD: str = "service_account"  # Options: service_account, server_key
    
    AI_SERVER_URL: Optional[str] = None
    AI_ACCESS_TOKEN: Optional[str] = None
    
    # Auth settings
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: Optional[str] = None
    APP_SCHEME: str = "juka://"  # Custom URL scheme for mobile app deep linking
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Image storage settings
    UPLOAD_FOLDER: str = "uploads"
    MAX_CONTENT_LENGTH: int = 10 * 1024 * 1024  # 10MB max upload size
    ALLOWED_EXTENSIONS: List[str] = ["jpg", "jpeg", "png", "gif"]
    STORAGE_TYPE: str = "local"  # Options: local, s3
    S3_BUCKET: Optional[str] = None
    S3_REGION: Optional[str] = None
    S3_ACCESS_KEY: Optional[str] = None
    S3_SECRET_KEY: Optional[str] = None
    PUBLIC_URL_PREFIX: Optional[str] = None
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

settings = Settings() 