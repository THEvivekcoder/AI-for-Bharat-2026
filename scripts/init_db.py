"""Initialize database with tables"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import engine, Base
from app.models import User, UserProfile, Location
from app.logging_config import logger


def init_db():
    """Create all database tables"""
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully!")
    except Exception as e:
        logger.error(f"Failed to create database tables: {str(e)}")
        raise


if __name__ == "__main__":
    init_db()
