"""Scheme schemas for request/response validation"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class EligibilityCriteria(BaseModel):
    """Eligibility criteria for schemes"""
    age_min: Optional[int] = Field(None, ge=0, le=150)
    age_max: Optional[int] = Field(None, ge=0, le=150)
    income_max: Optional[int] = Field(None, ge=0)
    gender: Optional[str] = Field(None, max_length=20)
    occupation: Optional[List[str]] = None
    education: Optional[List[str]] = None
    location: Optional[List[str]] = None  # states/districts where applicable
    caste: Optional[List[str]] = None
    custom_criteria: Optional[Dict[str, Any]] = None


class SchemeTranslationSchema(BaseModel):
    """Scheme translation schema"""
    language: str = Field(..., min_length=2, max_length=10)
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    benefits: Optional[List[str]] = None

    class Config:
        from_attributes = True


class SchemeBase(BaseModel):
    """Base scheme schema"""
    name: str = Field(..., min_length=1, max_length=255)
    category: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None
    benefits: Optional[List[str]] = None
    eligibility_criteria: EligibilityCriteria
    required_documents: Optional[List[str]] = None
    application_process: Optional[List[str]] = None
    application_url: Optional[str] = Field(None, max_length=500)
    department: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=50)
    source_url: Optional[str] = Field(None, max_length=500)
    
    # Verification tracking
    verification_status: Optional[str] = Field(None, max_length=20)  # verified, unverified, pending
    verification_source: Optional[str] = Field(None, max_length=255)


class SchemeCreate(SchemeBase):
    """Scheme creation schema"""
    translations: Optional[List[SchemeTranslationSchema]] = None


class SchemeUpdate(BaseModel):
    """Scheme update schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    category: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = None
    benefits: Optional[List[str]] = None
    eligibility_criteria: Optional[EligibilityCriteria] = None
    required_documents: Optional[List[str]] = None
    application_process: Optional[List[str]] = None
    application_url: Optional[str] = Field(None, max_length=500)
    department: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=50)
    source_url: Optional[str] = Field(None, max_length=500)
    last_updated: Optional[datetime] = None
    
    # Verification tracking
    verification_status: Optional[str] = Field(None, max_length=20)
    verified_at: Optional[datetime] = None
    verification_source: Optional[str] = Field(None, max_length=255)


class SchemeResponse(SchemeBase):
    """Scheme response schema"""
    scheme_id: str
    last_updated: Optional[datetime] = None
    created_at: datetime
    translations: Optional[List[SchemeTranslationSchema]] = None
    
    # Verification tracking
    verified_at: Optional[datetime] = None
    
    # Uncertainty indicator (computed field)
    is_verified: bool = Field(default=False, description="Whether the scheme data has been verified")
    data_age_days: Optional[int] = Field(None, description="Days since last update")

    class Config:
        from_attributes = True


class SchemeFilters(BaseModel):
    """Filters for scheme search"""
    category: Optional[str] = None
    state: Optional[str] = None
    department: Optional[str] = None
    query: Optional[str] = None  # Text search in name/description


class EligibilityResult(BaseModel):
    """Result of eligibility check"""
    is_eligible: bool
    missing_criteria: List[str] = []
    confidence: float = Field(..., ge=0.0, le=1.0)
    explanation: Optional[str] = None
    relevance_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Personalized relevance score")


class EligibilityCheckRequest(BaseModel):
    """Request to check eligibility for a scheme"""
    scheme_id: str
    user_profile: Dict[str, Any]  # Flexible user profile data


class EligibleSchemesRequest(BaseModel):
    """Request to get all eligible schemes"""
    user_profile: Dict[str, Any]  # Flexible user profile data
    category: Optional[str] = None
    state: Optional[str] = None


class EligibleSchemeResponse(BaseModel):
    """Response with scheme and eligibility details"""
    scheme: SchemeResponse
    eligibility: EligibilityResult
