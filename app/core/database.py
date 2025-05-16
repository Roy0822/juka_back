from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from urllib.parse import urlparse

from app.core.config import settings

# Parse the DB URL to check if it's an async URL
parsed_url = urlparse(settings.DATABASE_URL)
is_async_url = parsed_url.scheme == 'postgresql+asyncpg'

# If using an async URL, convert to sync for SQLAlchemy ORM
sync_url = settings.DATABASE_URL
if is_async_url:
    # Convert asyncpg URL to psycopg2 URL for SQLAlchemy ORM
    sync_url = settings.DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')

# Create SQLAlchemy engine
engine = create_engine(sync_url)

# Create sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Function to create tables
def create_tables():
    Base.metadata.create_all(bind=engine) 