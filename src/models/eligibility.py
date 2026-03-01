"""Eligibility criteria data model for BharatSahayak."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class EligibilityCriteria(BaseModel):
    """Eligibility criteria for schemes and programs."""
    
    age_min: Optional[int] = Field(None, ge=0, le=120, description="Minimum age requirement")
    age_max: Optional[int] = Field(None, ge=0, le=120, description="Maximum age requirement")
    income_max: Optional[int] = Field(None, ge=0, description="Maximum annual income in INR")
    gender: Optional[str] = Field(None, description="Gender requirement (male/female/other/any)")
    occupation: Optional[List[str]] = Field(None, description="List of eligible occupations")
    education: Optional[List[str]] = Field(None, description="List of eligible education levels")
    location: Optional[List[str]] = Field(None, description="List of eligible states/districts")
    caste: Optional[List[str]] = Field(None, description="List of eligible caste categories")
    custom_criteria: Dict[str, Any] = Field(default_factory=dict, description="Flexible additional criteria")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "age_min": 18,
                    "age_max": 35,
                    "income_max": 300000,
                    "gender": "any",
                    "occupation": ["farmer", "agricultural_worker"],
                    "education": ["primary", "secondary", "higher_secondary"],
                    "location": ["Maharashtra", "Karnataka"],
                    "caste": ["SC", "ST", "OBC", "General"],
                    "custom_criteria": {
                        "land_ownership": "yes",
                        "household_size": {"min": 2, "max": 8}
                    }
                }
            ]
        }
    }
