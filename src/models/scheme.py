"""Scheme data model for BharatSahayak."""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, HttpUrl

from .eligibility import EligibilityCriteria


class Scheme(BaseModel):
    """Government scheme information."""
    
    scheme_id: str = Field(..., min_length=1, description="Unique scheme identifier")
    name: str = Field(..., min_length=1, description="Scheme name in English")
    name_translations: Dict[str, str] = Field(
        default_factory=dict,
        description="Scheme name translations (language code -> translated name)"
    )
    category: str = Field(
        ...,
        description="Scheme category: agriculture, health, education, employment, social_welfare"
    )
    description: str = Field(..., min_length=1, description="Detailed scheme description")
    description_translations: Dict[str, str] = Field(
        default_factory=dict,
        description="Description translations (language code -> translated description)"
    )
    benefits: List[str] = Field(default_factory=list, description="List of scheme benefits")
    eligibility_criteria: EligibilityCriteria = Field(..., description="Eligibility requirements")
    required_documents: List[str] = Field(default_factory=list, description="Required documents for application")
    application_process: List[str] = Field(default_factory=list, description="Step-by-step application process")
    application_url: Optional[str] = Field(None, description="Online application URL")
    department: str = Field(..., min_length=1, description="Responsible government department")
    state: Optional[str] = Field(None, description="State (None for central schemes)")
    last_updated: datetime = Field(..., description="Last verification/update timestamp")
    source_url: str = Field(..., description="Official source URL for verification")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "scheme_id": "PM-KISAN-2024",
                    "name": "Pradhan Mantri Kisan Samman Nidhi",
                    "name_translations": {
                        "hi": "प्रधानमंत्री किसान सम्मान निधि",
                        "mr": "प्रधानमंत्री किसान सन्मान निधी"
                    },
                    "category": "agriculture",
                    "description": "Income support scheme for farmers providing Rs. 6000 per year in three installments",
                    "description_translations": {
                        "hi": "किसानों के लिए आय सहायता योजना जो तीन किस्तों में प्रति वर्ष 6000 रुपये प्रदान करती है"
                    },
                    "benefits": [
                        "Rs. 2000 per installment (3 times per year)",
                        "Direct bank transfer",
                        "No intermediaries"
                    ],
                    "eligibility_criteria": {
                        "age_min": 18,
                        "occupation": ["farmer"],
                        "custom_criteria": {
                            "land_ownership": "yes",
                            "cultivable_land": "any"
                        }
                    },
                    "required_documents": [
                        "Aadhaar card",
                        "Bank account details",
                        "Land ownership documents"
                    ],
                    "application_process": [
                        "Visit PM-KISAN portal or nearest CSC",
                        "Fill registration form with Aadhaar and bank details",
                        "Upload land records",
                        "Submit application",
                        "Receive confirmation SMS"
                    ],
                    "application_url": "https://pmkisan.gov.in",
                    "department": "Ministry of Agriculture and Farmers Welfare",
                    "state": None,
                    "last_updated": "2024-01-15T10:30:00Z",
                    "source_url": "https://pmkisan.gov.in"
                }
            ]
        }
    }
