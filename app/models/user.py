"""User models"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base
from app.security.encrypted_types import EncryptedString


class User(Base):
    """User account"""
    __tablename__ = "users"
    
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone_number = Column(EncryptedString(15), unique=False, nullable=False, index=False)  # Encrypted, no unique constraint
    phone_number_hash = Column(String(64), unique=True, nullable=False, index=True)  # Hash for lookups
    language = Column(String(10), nullable=False, default="hi")
    role = Column(String(20), nullable=False, default="user")  # user, admin, analyst
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationship
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")


class UserProfile(Base):
    """User profile information"""
    __tablename__ = "user_profiles"
    
    profile_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Location
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id"), nullable=True)
    
    # Demographics
    age = Column(Integer, nullable=True)
    gender = Column(String(20), nullable=True)
    education_level = Column(String(50), nullable=True)
    occupation = Column(String(50), nullable=True)
    income_bracket = Column(String(50), nullable=True)
    household_size = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="profile")
    location = relationship("Location")
