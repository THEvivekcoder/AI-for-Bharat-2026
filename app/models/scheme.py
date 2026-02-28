"""Scheme models for government schemes and eligibility"""
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base


class Scheme(Base):
    """Government scheme information"""
    __tablename__ = "schemes"
    
    scheme_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=True)
    benefits = Column(JSONB, nullable=True)
    eligibility_criteria = Column(JSONB, nullable=False)
    required_documents = Column(JSONB, nullable=True)
    application_process = Column(JSONB, nullable=True)
    application_url = Column(String(500), nullable=True)
    department = Column(String(100), nullable=True)
    state = Column(String(50), nullable=True, index=True)
    last_updated = Column(DateTime, nullable=True)
    source_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Verification tracking fields
    verification_status = Column(String(20), nullable=True, default='unverified')  # verified, unverified, pending
    verified_at = Column(DateTime, nullable=True)  # When verification was last performed
    verification_source = Column(String(255), nullable=True)  # Source used for verification
    
    # Relationships
    translations = relationship("SchemeTranslation", back_populates="scheme", cascade="all, delete-orphan")


class SchemeTranslation(Base):
    """Translations for scheme information"""
    __tablename__ = "scheme_translations"
    
    translation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scheme_id = Column(UUID(as_uuid=True), ForeignKey("schemes.scheme_id", ondelete="CASCADE"), nullable=False)
    language = Column(String(10), nullable=False, index=True)
    name = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    benefits = Column(JSONB, nullable=True)
    
    # Relationships
    scheme = relationship("Scheme", back_populates="translations")
    
    # Unique constraint on scheme_id and language
    __table_args__ = (
        {'schema': None},
    )
