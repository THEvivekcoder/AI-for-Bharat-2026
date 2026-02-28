"""Farmer Advisory models for farm profiles, crops, and recommendations"""
from sqlalchemy import Column, String, Float, Integer, DateTime, Text, ForeignKey, Date
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base


class FarmProfile(Base):
    """Farm profile information for farmers"""
    __tablename__ = "farm_profiles"
    
    farm_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Farm details
    land_size_acres = Column(Float, nullable=False)
    soil_type = Column(String(50), nullable=False)  # clay, loam, sandy, silt, etc.
    irrigation_type = Column(String(50), nullable=False)  # rainfed, canal, well, drip, sprinkler
    
    # Location
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id"), nullable=False)
    
    # Crops
    current_crops = Column(JSONB, nullable=True)  # List of current crops
    previous_crops = Column(JSONB, nullable=True)  # List of previous crops
    livestock = Column(JSONB, nullable=True)  # List of livestock if any
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User")
    location = relationship("Location")


class CropRecommendation(Base):
    """Crop recommendation records"""
    __tablename__ = "crop_recommendations"
    
    recommendation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farm_id = Column(UUID(as_uuid=True), ForeignKey("farm_profiles.farm_id", ondelete="CASCADE"), nullable=False)
    
    # Recommendation details
    crop_name = Column(String(100), nullable=False)
    suitability_score = Column(Float, nullable=False)  # 0-1 score
    expected_yield = Column(String(100), nullable=True)
    water_requirement = Column(String(50), nullable=False)  # low, medium, high
    duration_days = Column(Integer, nullable=False)
    market_demand = Column(String(20), nullable=True)  # high, medium, low
    estimated_profit = Column(String(100), nullable=True)
    reasoning = Column(Text, nullable=False)
    risks = Column(JSONB, nullable=True)  # List of risks
    
    season = Column(String(20), nullable=True)  # kharif, rabi, zaid
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    farm = relationship("FarmProfile")


class FertilizerRecommendation(Base):
    """Fertilizer recommendation records"""
    __tablename__ = "fertilizer_recommendations"
    
    recommendation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farm_id = Column(UUID(as_uuid=True), ForeignKey("farm_profiles.farm_id", ondelete="CASCADE"), nullable=False)
    
    # Crop and soil context
    crop_name = Column(String(100), nullable=False)
    growth_stage = Column(String(50), nullable=False)  # sowing, vegetative, flowering, fruiting
    soil_ph = Column(Float, nullable=True)
    soil_nutrients = Column(JSONB, nullable=True)  # N, P, K levels
    
    # Recommendation details
    fertilizer_type = Column(String(100), nullable=False)  # NPK ratio, organic, etc.
    quantity_per_acre = Column(String(50), nullable=False)
    timing = Column(String(100), nullable=False)  # when to apply
    application_method = Column(String(100), nullable=False)  # broadcast, band, foliar
    additional_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    farm = relationship("FarmProfile")


class MandiPrice(Base):
    """Market (mandi) price information"""
    __tablename__ = "mandi_prices"
    
    price_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Crop and location
    crop_name = Column(String(100), nullable=False, index=True)
    mandi_name = Column(String(100), nullable=False)
    state = Column(String(50), nullable=False, index=True)
    district = Column(String(50), nullable=False, index=True)
    
    # Location coordinates for distance calculation
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # Price information
    price_per_quintal = Column(Float, nullable=False)  # Price in INR per 100kg
    price_date = Column(Date, nullable=False, index=True)
    
    # Metadata
    source = Column(String(100), nullable=True)  # API source
    last_updated = Column(DateTime, nullable=True)  # When price data was last verified/updated
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Index for efficient queries
    __table_args__ = (
        {'schema': None},
    )


class CropCalendar(Base):
    """Crop calendar with planting and harvest schedules"""
    __tablename__ = "crop_calendars"
    
    calendar_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Crop and location
    crop_name = Column(String(100), nullable=False, index=True)
    state = Column(String(50), nullable=False, index=True)
    district = Column(String(50), nullable=True)
    season = Column(String(20), nullable=False)  # kharif, rabi, zaid
    
    # Schedule
    sowing_start = Column(String(20), nullable=False)  # Month or date range
    sowing_end = Column(String(20), nullable=False)
    harvest_start = Column(String(20), nullable=False)
    harvest_end = Column(String(20), nullable=False)
    
    # Care schedule
    care_schedule = Column(JSONB, nullable=True)  # List of care activities with timing
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
