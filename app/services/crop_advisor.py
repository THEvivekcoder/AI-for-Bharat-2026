"""Crop Advisor service for crop recommendations"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.farmer import FarmProfile, CropRecommendation, CropCalendar
from app.schemas.farmer import CropRecommendationResponse, CropCalendarResponse
import logging

logger = logging.getLogger(__name__)


class CropAdvisor:
    """Service for providing crop recommendations and calendars"""
    
    # Crop database with characteristics
    CROP_DATABASE = {
        "rice": {
            "water_requirement": "high",
            "duration_days": 120,
            "suitable_soils": ["clay", "loam", "alluvial"],
            "suitable_irrigation": ["canal", "well", "borewell"],
            "seasons": ["kharif"],
            "market_demand": "high",
            "base_yield": "40-50 quintals/acre",
            "risks": ["water logging", "pest attacks", "disease"]
        },
        "wheat": {
            "water_requirement": "medium",
            "duration_days": 120,
            "suitable_soils": ["loam", "clay", "alluvial"],
            "suitable_irrigation": ["canal", "well", "drip"],
            "seasons": ["rabi"],
            "market_demand": "high",
            "base_yield": "30-40 quintals/acre",
            "risks": ["frost damage", "rust disease"]
        },
        "cotton": {
            "water_requirement": "medium",
            "duration_days": 150,
            "suitable_soils": ["black", "loam", "alluvial"],
            "suitable_irrigation": ["canal", "drip", "well"],
            "seasons": ["kharif"],
            "market_demand": "high",
            "base_yield": "15-20 quintals/acre",
            "risks": ["bollworm", "drought", "price volatility"]
        },
        "sugarcane": {
            "water_requirement": "high",
            "duration_days": 365,
            "suitable_soils": ["loam", "clay", "alluvial"],
            "suitable_irrigation": ["canal", "drip", "well"],
            "seasons": ["kharif", "rabi"],
            "market_demand": "high",
            "base_yield": "300-400 quintals/acre",
            "risks": ["water stress", "pest attacks", "long duration"]
        },
        "maize": {
            "water_requirement": "medium",
            "duration_days": 90,
            "suitable_soils": ["loam", "sandy", "alluvial"],
            "suitable_irrigation": ["rainfed", "canal", "well"],
            "seasons": ["kharif", "rabi"],
            "market_demand": "medium",
            "base_yield": "25-30 quintals/acre",
            "risks": ["drought", "pest attacks"]
        },
        "pulses": {
            "water_requirement": "low",
            "duration_days": 90,
            "suitable_soils": ["loam", "sandy", "red"],
            "suitable_irrigation": ["rainfed", "well"],
            "seasons": ["rabi", "zaid"],
            "market_demand": "high",
            "base_yield": "8-12 quintals/acre",
            "risks": ["drought", "pod borer"]
        },
        "groundnut": {
            "water_requirement": "medium",
            "duration_days": 120,
            "suitable_soils": ["sandy", "loam", "red"],
            "suitable_irrigation": ["rainfed", "well"],
            "seasons": ["kharif", "rabi"],
            "market_demand": "high",
            "base_yield": "15-20 quintals/acre",
            "risks": ["drought", "pest attacks", "disease"]
        },
        "soybean": {
            "water_requirement": "medium",
            "duration_days": 100,
            "suitable_soils": ["black", "loam", "alluvial"],
            "suitable_irrigation": ["rainfed", "well"],
            "seasons": ["kharif"],
            "market_demand": "high",
            "base_yield": "12-15 quintals/acre",
            "risks": ["waterlogging", "pest attacks"]
        },
        "vegetables": {
            "water_requirement": "high",
            "duration_days": 60,
            "suitable_soils": ["loam", "sandy", "alluvial"],
            "suitable_irrigation": ["drip", "well", "canal"],
            "seasons": ["kharif", "rabi", "zaid"],
            "market_demand": "high",
            "base_yield": "100-150 quintals/acre",
            "risks": ["pest attacks", "disease", "market price volatility"]
        }
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def recommend_crops(
        self,
        farm_profile: FarmProfile,
        season: str,
        include_weather: bool = True
    ) -> List[CropRecommendationResponse]:
        """
        Recommend suitable crops based on farm profile and season
        
        Args:
            farm_profile: Farm profile with soil, irrigation, location
            season: kharif, rabi, or zaid
            include_weather: Whether to consider weather data (placeholder for now)
        
        Returns:
            List of crop recommendations sorted by suitability score
        """
        logger.info(f"Generating crop recommendations for farm {farm_profile.farm_id}, season {season}")
        
        recommendations = []
        
        for crop_name, crop_data in self.CROP_DATABASE.items():
            # Check if crop is suitable for the season
            if season not in crop_data["seasons"]:
                continue
            
            # Calculate suitability score
            score = self._calculate_suitability_score(
                farm_profile,
                crop_name,
                crop_data
            )
            
            # Generate reasoning
            reasoning = self._generate_reasoning(
                farm_profile,
                crop_name,
                crop_data,
                score
            )
            
            # Create recommendation
            recommendation = CropRecommendationResponse(
                crop_name=crop_name,
                suitability_score=score,
                expected_yield=crop_data["base_yield"],
                water_requirement=crop_data["water_requirement"],
                duration_days=crop_data["duration_days"],
                market_demand=crop_data["market_demand"],
                estimated_profit=self._estimate_profit(crop_name, crop_data),
                reasoning=reasoning,
                risks=crop_data["risks"],
                season=season
            )
            
            recommendations.append(recommendation)
        
        # Sort by suitability score (descending)
        recommendations.sort(key=lambda x: x.suitability_score, reverse=True)
        
        logger.info(f"Generated {len(recommendations)} crop recommendations")
        return recommendations
    
    def _calculate_suitability_score(
        self,
        farm_profile: FarmProfile,
        crop_name: str,
        crop_data: Dict[str, Any]
    ) -> float:
        """Calculate suitability score (0-1) based on farm characteristics"""
        score = 0.0
        factors = 0
        
        # Soil type match (40% weight)
        if farm_profile.soil_type in crop_data["suitable_soils"]:
            score += 0.4
        else:
            score += 0.1  # Partial score for non-ideal soil
        factors += 1
        
        # Irrigation type match (30% weight)
        if farm_profile.irrigation_type in crop_data["suitable_irrigation"]:
            score += 0.3
        else:
            score += 0.1  # Partial score for non-ideal irrigation
        factors += 1
        
        # Water requirement vs irrigation (20% weight)
        water_match = self._check_water_compatibility(
            farm_profile.irrigation_type,
            crop_data["water_requirement"]
        )
        score += water_match * 0.2
        factors += 1
        
        # Land size consideration (10% weight)
        # Larger land gets bonus for high-demand crops
        if farm_profile.land_size_acres >= 5 and crop_data["market_demand"] == "high":
            score += 0.1
        elif farm_profile.land_size_acres < 2:
            # Small farms better for vegetables
            if crop_name == "vegetables":
                score += 0.1
            else:
                score += 0.05
        else:
            score += 0.05
        factors += 1
        
        # Ensure score is between 0 and 1
        return min(1.0, max(0.0, score))
    
    def _check_water_compatibility(self, irrigation_type: str, water_requirement: str) -> float:
        """Check if irrigation type can support water requirement"""
        high_water_irrigation = ["canal", "well", "borewell", "drip"]
        medium_water_irrigation = ["canal", "well", "borewell", "drip", "sprinkler"]
        
        if water_requirement == "high":
            return 1.0 if irrigation_type in high_water_irrigation else 0.3
        elif water_requirement == "medium":
            return 1.0 if irrigation_type in medium_water_irrigation else 0.5
        else:  # low
            return 1.0  # All irrigation types can support low water crops
    
    def _generate_reasoning(
        self,
        farm_profile: FarmProfile,
        crop_name: str,
        crop_data: Dict[str, Any],
        score: float
    ) -> str:
        """Generate human-readable reasoning for recommendation"""
        reasons = []
        
        # Soil compatibility
        if farm_profile.soil_type in crop_data["suitable_soils"]:
            reasons.append(f"Your {farm_profile.soil_type} soil is ideal for {crop_name}")
        else:
            reasons.append(f"Your {farm_profile.soil_type} soil is acceptable but not ideal for {crop_name}")
        
        # Irrigation compatibility
        if farm_profile.irrigation_type in crop_data["suitable_irrigation"]:
            reasons.append(f"Your {farm_profile.irrigation_type} irrigation suits this crop")
        else:
            reasons.append(f"Consider improving irrigation for better results")
        
        # Market demand
        if crop_data["market_demand"] == "high":
            reasons.append("High market demand ensures good prices")
        
        # Duration
        if crop_data["duration_days"] <= 90:
            reasons.append("Short duration crop allows multiple cropping")
        
        return ". ".join(reasons) + "."
    
    def _estimate_profit(self, crop_name: str, crop_data: Dict[str, Any]) -> str:
        """Estimate profit range (simplified)"""
        # This is a simplified estimation
        # In production, this would use real market data
        profit_ranges = {
            "rice": "₹30,000-50,000 per acre",
            "wheat": "₹25,000-40,000 per acre",
            "cotton": "₹40,000-60,000 per acre",
            "sugarcane": "₹80,000-120,000 per acre",
            "maize": "₹20,000-35,000 per acre",
            "pulses": "₹25,000-40,000 per acre",
            "groundnut": "₹30,000-45,000 per acre",
            "soybean": "₹25,000-40,000 per acre",
            "vegetables": "₹60,000-100,000 per acre"
        }
        return profit_ranges.get(crop_name, "₹20,000-40,000 per acre")
    
    def get_crop_calendar(
        self,
        crop_name: str,
        state: str,
        district: Optional[str] = None
    ) -> Optional[CropCalendarResponse]:
        """
        Get crop calendar for specific crop and location
        
        Args:
            crop_name: Name of the crop
            state: State name
            district: District name (optional)
        
        Returns:
            Crop calendar with planting and harvest schedules
        """
        logger.info(f"Fetching crop calendar for {crop_name} in {state}")
        
        # Try to find in database
        query = self.db.query(CropCalendar).filter(
            CropCalendar.crop_name == crop_name.lower(),
            CropCalendar.state == state
        )
        
        if district:
            query = query.filter(CropCalendar.district == district)
        
        calendar = query.first()
        
        if calendar:
            return CropCalendarResponse(
                crop_name=calendar.crop_name,
                state=calendar.state,
                district=calendar.district,
                season=calendar.season,
                sowing_start=calendar.sowing_start,
                sowing_end=calendar.sowing_end,
                harvest_start=calendar.harvest_start,
                harvest_end=calendar.harvest_end,
                care_schedule=calendar.care_schedule
            )
        
        # If not in database, return default calendar based on crop type
        return self._get_default_calendar(crop_name, state)
    
    def _get_default_calendar(self, crop_name: str, state: str) -> Optional[CropCalendarResponse]:
        """Get default crop calendar if not in database"""
        # Default calendars for common crops
        default_calendars = {
            "rice": {
                "kharif": {
                    "sowing_start": "June",
                    "sowing_end": "July",
                    "harvest_start": "October",
                    "harvest_end": "November",
                    "care_schedule": [
                        {"activity": "Transplanting", "timing": "20-25 days after sowing"},
                        {"activity": "First weeding", "timing": "20 days after transplanting"},
                        {"activity": "Second weeding", "timing": "40 days after transplanting"},
                        {"activity": "Fertilizer application", "timing": "At tillering and panicle stages"}
                    ]
                }
            },
            "wheat": {
                "rabi": {
                    "sowing_start": "November",
                    "sowing_end": "December",
                    "harvest_start": "March",
                    "harvest_end": "April",
                    "care_schedule": [
                        {"activity": "First irrigation", "timing": "20-25 days after sowing"},
                        {"activity": "Second irrigation", "timing": "40-45 days after sowing"},
                        {"activity": "Fertilizer application", "timing": "At crown root and flowering stages"}
                    ]
                }
            }
        }
        
        crop_calendar = default_calendars.get(crop_name.lower())
        if not crop_calendar:
            return None
        
        # Determine season based on crop
        crop_data = self.CROP_DATABASE.get(crop_name.lower())
        if not crop_data:
            return None
        
        season = crop_data["seasons"][0]  # Use first season
        season_calendar = crop_calendar.get(season)
        
        if not season_calendar:
            return None
        
        return CropCalendarResponse(
            crop_name=crop_name,
            state=state,
            district=None,
            season=season,
            sowing_start=season_calendar["sowing_start"],
            sowing_end=season_calendar["sowing_end"],
            harvest_start=season_calendar["harvest_start"],
            harvest_end=season_calendar["harvest_end"],
            care_schedule=season_calendar.get("care_schedule")
        )
