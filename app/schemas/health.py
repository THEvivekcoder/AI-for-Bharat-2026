"""Health schemas for request/response validation"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime


class HealthResponse(BaseModel):
    """Health check response schema"""
    status: str
    version: str
    services: Dict[str, str]


class Location(BaseModel):
    """Location information"""
    state: str = Field(..., min_length=1, max_length=50)
    district: str = Field(..., min_length=1, max_length=50)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)


class BasicHealthInfo(BaseModel):
    """Basic health information for symptom analysis"""
    age: Optional[int] = Field(None, ge=0, le=150)
    gender: Optional[str] = Field(None, max_length=20)
    existing_conditions: Optional[List[str]] = None
    medications: Optional[List[str]] = None


class SymptomAnalysisRequest(BaseModel):
    """Request for symptom analysis"""
    symptoms: List[str] = Field(..., min_items=1)
    user_info: Optional[BasicHealthInfo] = None
    language: str = Field(default="en", min_length=2, max_length=10)


class HealthGuidance(BaseModel):
    """Health guidance response"""
    urgency_level: str = Field(..., pattern="^(routine|soon|urgent|emergency)$")
    possible_conditions: List[str] = []
    self_care_recommendations: List[str] = []
    when_to_seek_care: str
    red_flags: List[str] = []
    disclaimer: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class HealthFacilityBase(BaseModel):
    """Base health facility schema"""
    name: str = Field(..., min_length=1, max_length=255)
    facility_type: str = Field(..., min_length=1, max_length=50)
    state: str = Field(..., min_length=1, max_length=50)
    district: str = Field(..., min_length=1, max_length=50)
    address: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    contact: Optional[str] = Field(None, max_length=100)
    services: Optional[List[str]] = None


class HealthFacilityCreate(HealthFacilityBase):
    """Health facility creation schema"""
    pass


class HealthFacilityResponse(HealthFacilityBase):
    """Health facility response schema"""
    facility_id: str
    distance_km: Optional[float] = None  # Calculated distance from query location
    created_at: datetime

    class Config:
        from_attributes = True


class FacilitySearchRequest(BaseModel):
    """Request to search for health facilities"""
    location: Location
    facility_type: Optional[str] = None
    radius_km: int = Field(default=25, ge=1, le=200)


class HealthSchemeRequest(BaseModel):
    """Request for health insurance schemes"""
    state: Optional[str] = None
    category: Literal["health"] = "health"
