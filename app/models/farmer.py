"""Farmer Advisory models for farm profiles, crops, and recommendations"""

from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    DateTime,
    Text,
    ForeignKey,
    Date
)
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base
from app.db_types import GUID, JSONType


class FarmProfile(Base):
    """Farm profile information for farmers"""
    __tablename__ = "farm_profiles"

    farm_id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    user_id = Column(
        GUID(),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )

    land_size_acres = Column(Float, nullable=False)
    soil_type = Column(String(50), nullable=False)
    irrigation_type = Column(String(50), nullable=False)

    location_id = Column(
        GUID(),
        ForeignKey("locations.id"),
        nullable=False
    )

    current_crops = Column(JSONType, nullable=True)
    previous_crops = Column(JSONType, nullable=True)
    livestock = Column(JSONType, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    user = relationship("User")
    location = relationship("Location")


class CropRecommendation(Base):
    """Crop recommendation records"""
    __tablename__ = "crop_recommendations"

    recommendation_id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    farm_id = Column(
        GUID(),
        ForeignKey("farm_profiles.farm_id", ondelete="CASCADE"),
        nullable=False
    )

    crop_name = Column(String(100), nullable=False)
    suitability_score = Column(Float, nullable=False)
    expected_yield = Column(String(100), nullable=True)
    water_requirement = Column(String(50), nullable=False)
    duration_days = Column(Integer, nullable=False)
    market_demand = Column(String(20), nullable=True)
    estimated_profit = Column(String(100), nullable=True)
    reasoning = Column(Text, nullable=False)
    risks = Column(JSONType, nullable=True)

    season = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    farm = relationship("FarmProfile")


class FertilizerRecommendation(Base):
    """Fertilizer recommendation records"""
    __tablename__ = "fertilizer_recommendations"

    recommendation_id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    farm_id = Column(
        GUID(),
        ForeignKey("farm_profiles.farm_id", ondelete="CASCADE"),
        nullable=False
    )

    crop_name = Column(String(100), nullable=False)
    growth_stage = Column(String(50), nullable=False)
    soil_ph = Column(Float, nullable=True)
    soil_nutrients = Column(JSONType, nullable=True)

    fertilizer_type = Column(String(100), nullable=False)
    quantity_per_acre = Column(String(50), nullable=False)
    timing = Column(String(100), nullable=False)
    application_method = Column(String(100), nullable=False)
    additional_notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    farm = relationship("FarmProfile")


class MandiPrice(Base):
    """Market (mandi) price information"""
    __tablename__ = "mandi_prices"

    price_id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    crop_name = Column(String(100), nullable=False, index=True)
    mandi_name = Column(String(100), nullable=False)
    state = Column(String(50), nullable=False, index=True)
    district = Column(String(50), nullable=False, index=True)

    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    price_per_quintal = Column(Float, nullable=False)
    price_date = Column(Date, nullable=False, index=True)

    source = Column(String(100), nullable=True)
    last_updated = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        {'schema': None},
    )


class CropCalendar(Base):
    """Crop calendar with planting and harvest schedules"""
    __tablename__ = "crop_calendars"

    calendar_id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    crop_name = Column(String(100), nullable=False, index=True)
    state = Column(String(50), nullable=False, index=True)
    district = Column(String(50), nullable=True)
    season = Column(String(20), nullable=False)

    sowing_start = Column(String(20), nullable=False)
    sowing_end = Column(String(20), nullable=False)
    harvest_start = Column(String(20), nullable=False)
    harvest_end = Column(String(20), nullable=False)

    care_schedule = Column(JSONType, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )