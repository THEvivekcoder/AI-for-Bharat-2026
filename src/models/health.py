"""Health advisory data models for BharatSahayak."""

from typing import List, Optional
from pydantic import BaseModel, Field

from .location import Location


class HealthFacility(BaseModel):
    """Health facility information."""
    
    facility_id: str = Field(..., min_length=1, description="Unique facility identifier")
    name: str = Field(..., min_length=1, description="Facility name")
    facility_type: str = Field(
        ...,
        description="Facility type: PHC, CHC, District Hospital, Specialty Center"
    )
    location: Location = Field(..., description="Facility location")
    address: str = Field(..., min_length=1, description="Full address")
    contact: Optional[str] = Field(None, description="Contact phone number")
    services: List[str] = Field(default_factory=list, description="Available medical services")
    distance_km: Optional[float] = Field(None, ge=0, description="Distance from user location in km")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "facility_id": "PHC-MH-PUNE-001",
                    "name": "Primary Health Centre Kharadi",
                    "facility_type": "PHC",
                    "location": {
                        "state": "Maharashtra",
                        "district": "Pune",
                        "block": "Haveli",
                        "village": "Kharadi",
                        "pincode": "411014",
                        "latitude": 18.5511,
                        "longitude": 73.9467
                    },
                    "address": "Kharadi Road, Near Bus Stand, Kharadi, Pune 411014",
                    "contact": "020-12345678",
                    "services": [
                        "General consultation",
                        "Maternal health",
                        "Child immunization",
                        "Basic diagnostics"
                    ],
                    "distance_km": 5.2
                }
            ]
        }
    }


class HealthGuidance(BaseModel):
    """Health guidance based on symptoms."""
    
    urgency_level: str = Field(
        ...,
        description="Urgency level: routine, soon, urgent, emergency"
    )
    possible_conditions: List[str] = Field(
        default_factory=list,
        description="Possible conditions (informational only)"
    )
    self_care_recommendations: List[str] = Field(
        default_factory=list,
        description="Self-care recommendations"
    )
    when_to_seek_care: str = Field(
        ...,
        min_length=1,
        description="Guidance on when to seek medical care"
    )
    red_flags: List[str] = Field(
        default_factory=list,
        description="Warning signs requiring immediate care"
    )
    disclaimer: str = Field(
        ...,
        min_length=1,
        description="Medical disclaimer"
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence score for the guidance"
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "urgency_level": "soon",
                    "possible_conditions": [
                        "Common cold",
                        "Viral fever",
                        "Seasonal flu"
                    ],
                    "self_care_recommendations": [
                        "Rest and stay hydrated",
                        "Take paracetamol for fever",
                        "Gargle with warm salt water",
                        "Avoid cold drinks"
                    ],
                    "when_to_seek_care": "If fever persists for more than 3 days or exceeds 103°F, consult a doctor",
                    "red_flags": [
                        "Difficulty breathing",
                        "Persistent high fever",
                        "Severe headache",
                        "Chest pain"
                    ],
                    "disclaimer": "This information is for educational purposes only and is not a substitute for professional medical advice, diagnosis, or treatment. Always seek the advice of your physician or other qualified health provider with any questions you may have regarding a medical condition.",
                    "confidence": 0.75
                }
            ]
        }
    }
