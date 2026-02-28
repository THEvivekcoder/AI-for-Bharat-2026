"""Pydantic schemas for Farmer Advisory Service"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID


# Location schema (reused from existing)
class LocationBase(BaseModel):
    state: str
    district: str
    block: Optional[str] = None
    village: Optional[str] = None
    pincode: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None


# Farm Profile schemas
class FarmProfileCreate(BaseModel):
    """Schema for creating a farm profile"""
    land_size_acres: float = Field(..., gt=0, description="Land size in acres")
    soil_type: str = Field(..., description="Soil type: clay, loam, sandy, silt, etc.")
    irrigation_type: str = Field(..., description="Irrigation type: rainfed, canal, well, drip, sprinkler")
    location: LocationBase
    current_crops: Optional[List[str]] = None
    previous_crops: Optional[List[str]] = None
    livestock: Optional[List[str]] = None
    
    @field_validator('soil_type')
    @classmethod
    def validate_soil_type(cls, v):
        valid_types = ['clay', 'loam', 'sandy', 'silt', 'black', 'red', 'laterite', 'alluvial']
        if v.lower() not in valid_types:
            raise ValueError(f"Soil type must be one of: {', '.join(valid_types)}")
        return v.lower()
    
    @field_validator('irrigation_type')
    @classmethod
    def validate_irrigation_type(cls, v):
        valid_types = ['rainfed', 'canal', 'well', 'drip', 'sprinkler', 'borewell']
        if v.lower() not in valid_types:
            raise ValueError(f"Irrigation type must be one of: {', '.join(valid_types)}")
        return v.lower()


class FarmProfileUpdate(BaseModel):
    """Schema for updating a farm profile"""
    land_size_acres: Optional[float] = Field(None, gt=0)
    soil_type: Optional[str] = None
    irrigation_type: Optional[str] = None
    current_crops: Optional[List[str]] = None
    previous_crops: Optional[List[str]] = None
    livestock: Optional[List[str]] = None


class FarmProfileResponse(BaseModel):
    """Schema for farm profile response"""
    farm_id: UUID
    user_id: UUID
    land_size_acres: float
    soil_type: str
    irrigation_type: str
    location: LocationBase
    current_crops: Optional[List[str]] = None
    previous_crops: Optional[List[str]] = None
    livestock: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Crop Recommendation schemas
class CropRecommendationRequest(BaseModel):
    """Request for crop recommendations"""
    season: str = Field(..., description="Season: kharif, rabi, zaid")
    include_weather: bool = Field(default=True, description="Include weather data in recommendations")
    
    @field_validator('season')
    @classmethod
    def validate_season(cls, v):
        valid_seasons = ['kharif', 'rabi', 'zaid']
        if v.lower() not in valid_seasons:
            raise ValueError(f"Season must be one of: {', '.join(valid_seasons)}")
        return v.lower()


class CropRecommendationResponse(BaseModel):
    """Schema for crop recommendation response"""
    crop_name: str
    suitability_score: float = Field(..., ge=0, le=1)
    expected_yield: Optional[str] = None
    water_requirement: str
    duration_days: int
    market_demand: Optional[str] = None
    estimated_profit: Optional[str] = None
    reasoning: str
    risks: Optional[List[str]] = None
    season: Optional[str] = None
    
    class Config:
        from_attributes = True


# Fertilizer Recommendation schemas
class SoilData(BaseModel):
    """Soil data for fertilizer recommendations"""
    soil_ph: Optional[float] = Field(None, ge=0, le=14)
    nitrogen_level: Optional[str] = Field(None, description="low, medium, high")
    phosphorus_level: Optional[str] = Field(None, description="low, medium, high")
    potassium_level: Optional[str] = Field(None, description="low, medium, high")
    organic_matter: Optional[str] = Field(None, description="low, medium, high")


class FertilizerRecommendationRequest(BaseModel):
    """Request for fertilizer recommendations"""
    crop_name: str
    growth_stage: str = Field(..., description="sowing, vegetative, flowering, fruiting")
    soil_data: Optional[SoilData] = None
    
    @field_validator('growth_stage')
    @classmethod
    def validate_growth_stage(cls, v):
        valid_stages = ['sowing', 'vegetative', 'flowering', 'fruiting', 'maturity']
        if v.lower() not in valid_stages:
            raise ValueError(f"Growth stage must be one of: {', '.join(valid_stages)}")
        return v.lower()


class FertilizerRecommendationResponse(BaseModel):
    """Schema for fertilizer recommendation response"""
    fertilizer_type: str
    quantity_per_acre: str
    timing: str
    application_method: str
    additional_notes: Optional[str] = None
    crop_name: str
    growth_stage: str
    
    class Config:
        from_attributes = True


# Mandi Price schemas
class MandiPriceQuery(BaseModel):
    """Query parameters for mandi prices"""
    crop_name: str
    location: LocationBase
    radius_km: int = Field(default=50, ge=1, le=200, description="Search radius in kilometers")


class MandiPriceResponse(BaseModel):
    """Schema for mandi price response"""
    mandi_name: str
    crop_name: str
    price_per_quintal: float
    price_date: date
    state: str
    district: str
    distance_km: Optional[float] = None
    source: Optional[str] = None
    
    class Config:
        from_attributes = True


class PriceTrendResponse(BaseModel):
    """Schema for price trend response"""
    crop_name: str
    location: str
    prices: List[Dict[str, Any]]  # List of {date, price, mandi_name}
    average_price: float
    min_price: float
    max_price: float
    trend: str  # increasing, decreasing, stable


# Crop Calendar schemas
class CropCalendarRequest(BaseModel):
    """Request for crop calendar"""
    crop_name: str
    location: LocationBase


class CropCalendarResponse(BaseModel):
    """Schema for crop calendar response"""
    crop_name: str
    state: str
    district: Optional[str] = None
    season: str
    sowing_start: str
    sowing_end: str
    harvest_start: str
    harvest_end: str
    care_schedule: Optional[List[Dict[str, Any]]] = None
    
    class Config:
        from_attributes = True
