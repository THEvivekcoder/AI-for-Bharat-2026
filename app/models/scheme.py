"""Scheme models for government schemes and eligibility"""

from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base
from app.db_types import GUID, JSONType


class Scheme(Base):
    """Government scheme information"""
    __tablename__ = "schemes"

    scheme_id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=True)

    benefits = Column(JSONType, nullable=True)
    eligibility_criteria = Column(JSONType, nullable=False)
    required_documents = Column(JSONType, nullable=True)
    application_process = Column(JSONType, nullable=True)

    application_url = Column(String(500), nullable=True)
    department = Column(String(100), nullable=True)
    state = Column(String(50), nullable=True, index=True)
    last_updated = Column(DateTime, nullable=True)
    source_url = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Verification tracking fields
    verification_status = Column(String(20), nullable=True, default="unverified")
    verified_at = Column(DateTime, nullable=True)
    verification_source = Column(String(255), nullable=True)

    # Relationships
    translations = relationship(
        "SchemeTranslation",
        back_populates="scheme",
        cascade="all, delete-orphan"
    )


class SchemeTranslation(Base):
    """Translations for scheme information"""
    __tablename__ = "scheme_translations"

    translation_id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    scheme_id = Column(
        GUID(),
        ForeignKey("schemes.scheme_id", ondelete="CASCADE"),
        nullable=False
    )

    language = Column(String(10), nullable=False, index=True)
    name = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    benefits = Column(JSONType, nullable=True)

    # Relationships
    scheme = relationship("Scheme", back_populates="translations")

    __table_args__ = (
        {'schema': None},
    )