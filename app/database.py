"""Database configuration and session management"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.engine import Engine
from typing import Generator
from app.config import get_settings

settings = get_settings()

# Detect if using SQLite
is_sqlite = settings.database_url.startswith("sqlite")

# Create database engine
if is_sqlite:
    engine: Engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},  # Required for SQLite
        echo=settings.debug
    )
else:
    engine: Engine = create_engine(
        settings.database_url,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_pre_ping=True,
        echo=settings.debug
    )

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for models
Base = declarative_base()


def init_db():
    """
    Initialize database (create tables)
    """
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for getting database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()