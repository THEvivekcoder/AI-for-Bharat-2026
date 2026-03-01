"""Mandi price data models for BharatSahayak agricultural advisory."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class MandiPrice(BaseModel):
    """Mandi (market) price information for crops."""
    
    mandi_name: str = Field(..., min_length=1, description="Name of the mandi/market")
    crop_name: str = Field(..., min_length=1, description="Crop name")
    state: str = Field(..., min_length=1, description="State where mandi is located")
    district: str = Field(..., min_length=1, description="District where mandi is located")
    price_per_quintal: float = Field(..., gt=0, description="Price per quintal in Rs.")
    price_date: datetime = Field(..., description="Date of the price")
    distance_km: Optional[float] = Field(None, ge=0, description="Distance from user location in km")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "mandi_name": "Pune APMC",
                    "crop_name": "Wheat",
                    "state": "Maharashtra",
                    "district": "Pune",
                    "price_per_quintal": 2500.0,
                    "price_date": "2024-01-20T00:00:00Z",
                    "distance_km": 15.5
                }
            ]
        }
    }


class MandiPriceQuery(BaseModel):
    """Query parameters for mandi price lookup."""
    
    crop_name: str = Field(..., min_length=1, description="Crop name to query")
    state: str = Field(..., min_length=1, description="User's state")
    district: str = Field(..., min_length=1, description="User's district")
    radius_km: int = Field(default=50, ge=1, le=200, description="Search radius in km")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "crop_name": "Wheat",
                    "state": "Maharashtra",
                    "district": "Pune",
                    "radius_km": 50
                }
            ]
        }
    }
