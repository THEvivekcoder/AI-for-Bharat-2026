"""Health models for health facilities and symptom data"""

from sqlalchemy import Column, String, DateTime, Text, Numeric
from datetime import datetime
import uuid

from app.database import Base
from app.db_types import GUID, JSONType


class HealthFacility(Base):
    """Health facility information"""
    __tablename__ = "health_facilities"

    facility_id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    name = Column(String(255), nullable=False, index=True)
    facility_type = Column(String(50), nullable=False, index=True)  # PHC, CHC, District Hospital, Specialty Center
    state = Column(String(50), nullable=False, index=True)
    district = Column(String(50), nullable=False, index=True)
    address = Column(Text, nullable=True)

    latitude = Column(Numeric(10, 8), nullable=True)
    longitude = Column(Numeric(11, 8), nullable=True)

    contact = Column(String(100), nullable=True)

    services = Column(JSONType, nullable=True)  # Cross-database JSON

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)