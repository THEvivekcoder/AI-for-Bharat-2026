"""Location model"""
from sqlalchemy import Column, String, Float
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.database import Base


class Location(Base):
    """Location information"""
    __tablename__ = "locations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    state = Column(String(50), nullable=False, index=True)
    district = Column(String(50), nullable=False, index=True)
    block = Column(String(50), nullable=True)
    village = Column(String(100), nullable=True)
    pincode = Column(String(10), nullable=False, index=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
