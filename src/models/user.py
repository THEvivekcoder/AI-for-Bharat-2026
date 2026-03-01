"""User profile data models for BharatSahayak."""

from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, field_validator

from .location import Location


class UserPreferences(BaseModel):
    """User preferences and settings."""
    
    notification_enabled: bool = Field(default=True, description="Enable notifications")
    preferred_categories: list[str] = Field(default_factory=list, description="Preferred scheme categories")
    voice_enabled: bool = Field(default=True, description="Enable voice interface")
    data_sharing_consent: bool = Field(default=False, description="Consent for data sharing")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "notification_enabled": True,
                    "preferred_categories": ["agriculture", "education"],
                    "voice_enabled": True,
                    "data_sharing_consent": False
                }
            ]
        }
    }


class UserProfile(BaseModel):
    """Complete user profile information."""
    
    user_id: str = Field(..., min_length=1, description="Unique user identifier")
    phone_number: str = Field(..., pattern=r"^\+?[1-9]\d{9,14}$", description="Phone number with country code")
    language: str = Field(..., min_length=2, max_length=10, description="Preferred language code (e.g., 'hi', 'en')")
    location: Location = Field(..., description="User location information")
    age: Optional[int] = Field(None, ge=0, le=120, description="User age")
    gender: Optional[str] = Field(None, description="Gender (male/female/other)")
    education_level: Optional[str] = Field(None, description="Education level")
    occupation: Optional[str] = Field(None, description="Current occupation")
    income_bracket: Optional[str] = Field(None, description="Annual income bracket")
    household_size: Optional[int] = Field(None, ge=1, le=50, description="Number of household members")
    preferences: UserPreferences = Field(default_factory=UserPreferences, description="User preferences")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Account creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v: str) -> str:
        """Validate phone number format."""
        # Remove spaces and dashes
        cleaned = v.replace(" ", "").replace("-", "")
        
        # Check if it starts with + and has valid length
        if cleaned.startswith("+"):
            if len(cleaned) < 11 or len(cleaned) > 16:
                raise ValueError("Phone number with country code must be 10-15 digits")
        else:
            if len(cleaned) != 10:
                raise ValueError("Phone number without country code must be exactly 10 digits")
        
        return cleaned
    
    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: Optional[str]) -> Optional[str]:
        """Validate gender value."""
        if v is not None:
            valid_genders = ["male", "female", "other"]
            if v.lower() not in valid_genders:
                raise ValueError(f"Gender must be one of: {', '.join(valid_genders)}")
            return v.lower()
        return v
    
    @field_validator("education_level")
    @classmethod
    def validate_education_level(cls, v: Optional[str]) -> Optional[str]:
        """Validate education level."""
        if v is not None:
            valid_levels = [
                "illiterate", "primary", "secondary", "higher_secondary",
                "graduate", "postgraduate", "diploma", "vocational"
            ]
            if v.lower() not in valid_levels:
                raise ValueError(f"Education level must be one of: {', '.join(valid_levels)}")
            return v.lower()
        return v
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "user_id": "user_123456",
                    "phone_number": "+919876543210",
                    "language": "hi",
                    "location": {
                        "state": "Maharashtra",
                        "district": "Pune",
                        "block": "Haveli",
                        "village": "Kharadi",
                        "pincode": "411014",
                        "latitude": 18.5511,
                        "longitude": 73.9467
                    },
                    "age": 35,
                    "gender": "male",
                    "education_level": "secondary",
                    "occupation": "farmer",
                    "income_bracket": "100000-300000",
                    "household_size": 5,
                    "preferences": {
                        "notification_enabled": True,
                        "preferred_categories": ["agriculture", "health"],
                        "voice_enabled": True,
                        "data_sharing_consent": False
                    },
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-15T10:30:00Z"
                }
            ]
        }
    }
