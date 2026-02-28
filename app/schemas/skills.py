"""Skills and Employment schemas for request/response validation"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal


class SkillProgramBase(BaseModel):
    """Base skill program schema"""
    name: str = Field(..., min_length=1, max_length=255)
    provider: Optional[str] = Field(None, max_length=100)
    category: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None
    duration_weeks: Optional[int] = Field(None, ge=0)
    cost: Optional[Decimal] = Field(None, ge=0)
    state: Optional[str] = Field(None, max_length=50)
    district: Optional[str] = Field(None, max_length=50)
    mode: Optional[str] = Field(None, max_length=20)  # in-person, online, hybrid
    eligibility_criteria: Optional[Dict[str, Any]] = None
    certification: bool = False
    placement_support: bool = False
    registration_url: Optional[str] = Field(None, max_length=500)
    contact: Optional[str] = Field(None, max_length=100)


class SkillProgramCreate(SkillProgramBase):
    """Skill program creation schema"""
    pass


class SkillProgramResponse(SkillProgramBase):
    """Skill program response schema"""
    program_id: str
    created_at: datetime
    updated_at: datetime
    relevance_score: Optional[float] = Field(None, ge=0.0, le=1.0)  # For matched results
    match_reason: Optional[str] = None  # Explanation for match

    class Config:
        from_attributes = True


class SkillProgramFilters(BaseModel):
    """Filters for skill program search"""
    category: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    mode: Optional[str] = None
    max_cost: Optional[Decimal] = None
    certification_required: Optional[bool] = None
    placement_support_required: Optional[bool] = None


class SkillPreferences(BaseModel):
    """User preferences for skill program matching"""
    current_skills: Optional[List[str]] = []
    interests: Optional[List[str]] = []
    career_goals: Optional[List[str]] = []
    max_duration_weeks: Optional[int] = None
    max_cost: Optional[Decimal] = None
    preferred_mode: Optional[str] = None  # in-person, online, hybrid
    location_state: Optional[str] = None
    location_district: Optional[str] = None


class SkillMatchRequest(BaseModel):
    """Request for personalized skill program matching"""
    user_profile: Dict[str, Any]  # User profile data
    preferences: SkillPreferences
    limit: int = Field(10, ge=1, le=50)


class JobPostingBase(BaseModel):
    """Base job posting schema"""
    title: str = Field(..., min_length=1, max_length=255)
    department: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    qualifications: Optional[Dict[str, Any]] = None  # education, experience requirements
    location: Optional[Dict[str, Any]] = None  # state, district, multiple locations
    application_deadline: Optional[date] = None
    application_url: Optional[str] = Field(None, max_length=500)
    posted_date: Optional[date] = None


class JobPostingCreate(JobPostingBase):
    """Job posting creation schema"""
    pass


class JobPostingResponse(JobPostingBase):
    """Job posting response schema"""
    job_id: str
    created_at: datetime
    updated_at: datetime
    match_score: Optional[float] = Field(None, ge=0.0, le=1.0)  # For matched results
    match_reason: Optional[str] = None  # Explanation for match

    class Config:
        from_attributes = True


class Qualifications(BaseModel):
    """User qualifications for job matching"""
    education_level: Optional[str] = None  # 10th, 12th, graduate, postgraduate, etc.
    degree: Optional[str] = None
    experience_years: Optional[int] = Field(None, ge=0)
    skills: Optional[List[str]] = []
    certifications: Optional[List[str]] = []


class JobPreferences(BaseModel):
    """User preferences for job search"""
    departments: Optional[List[str]] = []
    locations: Optional[List[str]] = []  # Preferred states/districts
    min_qualification: Optional[str] = None


class JobSearchRequest(BaseModel):
    """Request for job search"""
    qualifications: Qualifications
    preferences: JobPreferences
    limit: int = Field(10, ge=1, le=50)


class JobAlertsRequest(BaseModel):
    """Request for job alerts based on user profile"""
    user_profile: Dict[str, Any]
    qualifications: Qualifications
    preferences: JobPreferences
    days_back: int = Field(30, ge=1, le=90)  # Look for jobs posted in last N days
