"""Skill development and job posting models for BharatSahayak."""

from datetime import date, datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from .eligibility import EligibilityCriteria
from .location import Location


class SkillProgram(BaseModel):
    """Skill development program information."""
    
    program_id: str = Field(..., min_length=1, description="Unique program identifier")
    name: str = Field(..., min_length=1, description="Program name in English")
    name_translations: Dict[str, str] = Field(
        default_factory=dict,
        description="Program name translations (language code -> translated name)"
    )
    provider: str = Field(..., min_length=1, description="Training provider organization")
    category: str = Field(
        ...,
        description="Program category: technical, vocational, digital, entrepreneurship"
    )
    description: str = Field(..., min_length=1, description="Detailed program description")
    description_translations: Dict[str, str] = Field(
        default_factory=dict,
        description="Description translations (language code -> translated description)"
    )
    duration_weeks: int = Field(..., gt=0, description="Program duration in weeks")
    cost: float = Field(..., ge=0, description="Program cost in INR (0 for free programs)")
    location: Location = Field(..., description="Program location")
    mode: str = Field(
        ...,
        description="Delivery mode: in-person, online, hybrid"
    )
    eligibility: EligibilityCriteria = Field(..., description="Eligibility requirements")
    certification: bool = Field(..., description="Whether program provides certification")
    placement_support: bool = Field(..., description="Whether placement assistance is provided")
    registration_url: str = Field(..., description="Online registration URL")
    contact: str = Field(..., min_length=1, description="Contact information")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Record creation timestamp")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "program_id": "PMKVY-ELECT-2024",
                    "name": "Electrician Training Program",
                    "name_translations": {
                        "hi": "इलेक्ट्रीशियन प्रशिक्षण कार्यक्रम"
                    },
                    "provider": "National Skill Development Corporation",
                    "category": "technical",
                    "description": "Comprehensive electrician training covering residential and commercial electrical work",
                    "description_translations": {
                        "hi": "आवासीय और वाणिज्यिक विद्युत कार्य को कवर करने वाला व्यापक इलेक्ट्रीशियन प्रशिक्षण"
                    },
                    "duration_weeks": 12,
                    "cost": 0,
                    "location": {
                        "state": "Maharashtra",
                        "district": "Pune",
                        "pincode": "411001"
                    },
                    "mode": "in-person",
                    "eligibility": {
                        "age_min": 18,
                        "age_max": 35,
                        "education": ["10th pass", "12th pass"],
                        "custom_criteria": {}
                    },
                    "certification": True,
                    "placement_support": True,
                    "registration_url": "https://pmkvyofficial.org",
                    "contact": "1800-123-9626",
                    "created_at": "2024-01-15T10:30:00Z"
                }
            ]
        }
    }


class JobPosting(BaseModel):
    """Government job posting information."""
    
    job_id: str = Field(..., min_length=1, description="Unique job identifier")
    title: str = Field(..., min_length=1, description="Job title")
    title_translations: Dict[str, str] = Field(
        default_factory=dict,
        description="Job title translations (language code -> translated title)"
    )
    department: str = Field(..., min_length=1, description="Government department/organization")
    description: str = Field(..., min_length=1, description="Detailed job description")
    description_translations: Dict[str, str] = Field(
        default_factory=dict,
        description="Description translations (language code -> translated description)"
    )
    qualifications: List[str] = Field(
        default_factory=list,
        description="Required educational qualifications"
    )
    experience_years: int = Field(0, ge=0, description="Required years of experience")
    location: Location = Field(..., description="Job location")
    salary_range: Optional[str] = Field(None, description="Salary range (e.g., '25000-35000 per month')")
    application_deadline: date = Field(..., description="Last date to apply")
    application_url: str = Field(..., description="Online application URL")
    posted_date: date = Field(..., description="Job posting date")
    vacancies: int = Field(1, gt=0, description="Number of open positions")
    job_type: str = Field(
        "permanent",
        description="Job type: permanent, contract, temporary"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Record creation timestamp")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "job_id": "UPSC-2024-001",
                    "title": "Junior Engineer (Civil)",
                    "title_translations": {
                        "hi": "कनिष्ठ अभियंता (सिविल)"
                    },
                    "department": "Ministry of Railways",
                    "description": "Junior Engineer position for civil engineering work in railway construction and maintenance",
                    "description_translations": {
                        "hi": "रेलवे निर्माण और रखरखाव में सिविल इंजीनियरिंग कार्य के लिए कनिष्ठ अभियंता पद"
                    },
                    "qualifications": [
                        "Diploma in Civil Engineering",
                        "B.Tech in Civil Engineering"
                    ],
                    "experience_years": 0,
                    "location": {
                        "state": "Maharashtra",
                        "district": "Mumbai",
                        "pincode": "400001"
                    },
                    "salary_range": "35000-45000 per month",
                    "application_deadline": "2024-03-31",
                    "application_url": "https://www.rrbcdg.gov.in",
                    "posted_date": "2024-01-15",
                    "vacancies": 50,
                    "job_type": "permanent",
                    "created_at": "2024-01-15T10:30:00Z"
                }
            ]
        }
    }
