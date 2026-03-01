"""Farm profile data models for BharatSahayak agricultural advisory."""

from typing import List, Optional
from pydantic import BaseModel, Field

from .location import Location


class FarmProfile(BaseModel):
    """Farm profile information for agricultural advisory."""
    
    user_id: str = Field(..., min_length=1, description="User ID who owns the farm")
    land_size_acres: float = Field(..., gt=0, description="Farm land size in acres")
    soil_type: str = Field(..., min_length=1, description="Soil type (e.g., clay, loam, sandy, black)")
    irrigation_type: str = Field(
        ...,
        description="Irrigation type: rainfed, canal, well, drip, sprinkler"
    )
    location: Location = Field(..., description="Farm location")
    current_crops: List[str] = Field(default_factory=list, description="Currently growing crops")
    previous_crops: List[str] = Field(default_factory=list, description="Previously grown crops")
    livestock: Optional[List[str]] = Field(None, description="Livestock owned (if any)")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "user_id": "user_123456",
                    "land_size_acres": 5.0,
                    "soil_type": "black",
                    "irrigation_type": "well",
                    "location": {
                        "state": "Maharashtra",
                        "district": "Pune",
                        "block": "Haveli",
                        "village": "Kharadi",
                        "pincode": "411014",
                        "latitude": 18.5511,
                        "longitude": 73.9467
                    },
                    "current_crops": ["wheat", "sugarcane"],
                    "previous_crops": ["cotton", "soybean"],
                    "livestock": ["cow", "buffalo"]
                }
            ]
        }
    }


class CropRecommendation(BaseModel):
    """Crop recommendation with reasoning."""
    
    crop_name: str = Field(..., min_length=1, description="Recommended crop name")
    suitability_score: float = Field(..., ge=0, le=1, description="Suitability score (0-1)")
    expected_yield: str = Field(..., description="Expected yield estimate")
    water_requirement: str = Field(..., description="Water requirement level")
    duration_days: int = Field(..., gt=0, description="Crop duration in days")
    market_demand: str = Field(..., description="Market demand: high, medium, low")
    estimated_profit: Optional[str] = Field(None, description="Estimated profit range")
    reasoning: str = Field(..., min_length=1, description="Reasoning for recommendation")
    risks: List[str] = Field(default_factory=list, description="Potential risks")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "crop_name": "Soybean",
                    "suitability_score": 0.85,
                    "expected_yield": "15-20 quintals per acre",
                    "water_requirement": "medium",
                    "duration_days": 90,
                    "market_demand": "high",
                    "estimated_profit": "Rs. 25,000-35,000 per acre",
                    "reasoning": "Black soil is ideal for soybean. Current season (Kharif) is perfect. Good market demand in your region.",
                    "risks": ["Pest attack in humid conditions", "Price fluctuation"]
                }
            ]
        }
    }
