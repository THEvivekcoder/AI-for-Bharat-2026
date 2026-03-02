"""Skill development and job posting data models for BharatSahayak."""

from datetime import date, datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from .eligibility import EligibilityCriteria
from .location import Location


class SkillProgram(BaseModel):
    """Skill development program information."""
    
    program_id: str = Field(..., min_length=1, description="Unique program identifier")
    name: str = Field(..., min_length=1, description="Program name")
    provider: str = Field(..., min_length=1, description="Training provider organization")
    category: str = Field(
        ...,
        description="Program category: technical, vocational, digital, entrepreneurship"
    )
    description: str = Field(..., min_length=1, description="Detailed program description")
    duration_weeks: int = Field(..., gt=0, description="Program duration in weeks")
    cost: float = Field(..., ge=0, description="Program cost in rupees (0 for free)")
    location: Location = Field(..., description="Program location")
    mode: str = Field(..., description="Delivery mode: in-person, online, hybrid")
    eligibility_criteria: EligibilityCriteria = Field(..., description="Eligibility requirements")
    certification: bool = Field(..., description="Whether certification is provided")
    placement_support: bool = Field(..., description="Whether placement assistance is provided")
    registration_url: str = Field(..., description="Registration/application URL")
    contact: str = Field(..., min_length=1, description="Contact information")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "program_id": "PMKVY-ELEC-2024",
                    "name": "Electrician Training Program",
                    "provider": "National Skill Development Corporation",
                    "category": "technical",
                    "description": "Comprehensive electrician training covering residential and commercial wiring, safety protocols, and electrical maintenance",
                    "duration_weeks": 12,
                    "cost": 0,
                    "location": {
                        "state": "Maharashtra",
                        "district": "Pune",
                        "block": "Haveli",
                        "village": None,
                        "pincode": "411014",
                        "latitude": 18.5204,
                        "longitude": 73.8567
                    },
                    "mode": "in-person",
                    "eligibility_criteria": {
                        "age_min": 18,
                        "age_max": 35,
                        "education": ["8th pass", "10th pass", "12th pass"],
                        "custom_criteria": {}
                    },
                    "certification": True,
                    "placement_support": True,
                    "registration_url": "https://pmkvyofficial.org/electrician",
                    "contact": "1800-123-9626"
                }
            ]
        }
    }


class JobPosting(BaseModel):
    """Government job posting information."""
    
    job_id: str = Field(..., min_length=1, description="Unique job identifier")
    title: str = Field(..., min_length=1, description="Job title")
    department: str = Field(..., min_length=1, description="Government department/organization")
    description: str = Field(..., min_length=1, description="Job description and responsibilities")
    qualifications: Dict[str, List[str]] = Field(
        ...,
        description="Required qualifications (education, experience, skills)"
    )
    location: Location = Field(..., description="Job location")
    application_deadline: date = Field(..., description="Last date to apply")
    application_url: str = Field(..., description="Application portal URL")
    posted_date: date = Field(..., description="Job posting date")
    salary_range: Optional[str] = Field(None, description="Salary range (if disclosed)")
    vacancies: Optional[int] = Field(None, gt=0, description="Number of vacancies")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "job_id": "MAHA-PWD-2024-001",
                    "title": "Junior Engineer (Civil)",
                    "department": "Maharashtra Public Works Department",
                    "description": "Junior Engineer position for civil engineering projects including road construction, building maintenance, and infrastructure development",
                    "qualifications": {
                        "education": ["Diploma in Civil Engineering", "B.E./B.Tech in Civil Engineering"],
                        "experience": ["Freshers welcome", "0-2 years experience"],
                        "skills": ["AutoCAD", "Site supervision", "Quality control"]
                    },
                    "location": {
                        "state": "Maharashtra",
                        "district": "Pune",
                        "block": None,
                        "village": None,
                        "pincode": "411001",
                        "latitude": 18.5204,
                        "longitude": 73.8567
                    },
                    "application_deadline": "2024-03-31",
                    "application_url": "https://mahapwd.gov.in/recruitment",
                    "posted_date": "2024-01-15",
                    "salary_range": "Rs. 35,000 - 50,000 per month",
                    "vacancies": 25
                }
            ]
        }
    }
