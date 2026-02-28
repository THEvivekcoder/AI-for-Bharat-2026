"""Health models for health facilities and symptom data"""
from sqlalchemy import Column, String, DateTime, Text, Numeric, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid
from app.database import Base


class HealthFacility(Base):
    """Health facility information"""
    __tablename__ = "health_facilities"
    
    facility_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    facility_type = Column(String(50), nullable=False, index=True)  # PHC, CHC, District Hospital, Specialty Center
    state = Column(String(50), nullable=False, index=True)
    district = Column(String(50), nullable=False, index=True)
    address = Column(Text, nullable=True)
    latitude = Column(Numeric(10, 8), nullable=True)
    longitude = Column(Numeric(11, 8), nullable=True)
    contact = Column(String(100), nullable=True)
    services = Column(JSONB, nullable=True)  # List of services offered
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
