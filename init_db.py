from app.core.database import engine, Base
from app.models import *  # Import all models to ensure they're registered with SQLAlchemy

def init_db():
    """Initialize the database by creating all tables."""
    print("Creating database tables...")
    Base.metadata.drop_all(bind=engine)  # Drop existing tables
    Base.metadata.create_all(bind=engine)  # Create tables
    print("Database tables created successfully!")

if __name__ == "__main__":
    init_db() 