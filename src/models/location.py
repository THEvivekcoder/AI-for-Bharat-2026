"""Location data model for BharatSahayak."""

from typing import Optional
from pydantic import BaseModel, Field, field_validator


class Location(BaseModel):
    """Location information for users and services."""
    
    state: str = Field(..., min_length=1, description="State name")
    district: str = Field(..., min_length=1, description="District name")
    block: Optional[str] = Field(None, description="Block/Tehsil name")
    village: Optional[str] = Field(None, description="Village name")
    pincode: str = Field(..., pattern=r"^\d{6}$", description="6-digit pincode")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Longitude coordinate")
    
    @field_validator("pincode")
    @classmethod
    def validate_pincode(cls, v: str) -> str:
        """Validate pincode format."""
        if not v.isdigit() or len(v) != 6:
            raise ValueError("Pincode must be exactly 6 digits")
        return v
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "state": "Maharashtra",
                    "district": "Pune",
                    "block": "Haveli",
                    "village": "Kharadi",
                    "pincode": "411014",
                    "latitude": 18.5511,
                    "longitude": 73.9467
                }
            ]
        }
    }
