"""Lambda handler for crop recommendation advisory."""

import json
import os
import logging
from typing import Dict, Any, List
from datetime import datetime

from src.models.farm import FarmProfile, CropRecommendation

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))


# Crop database with suitability information
CROP_DATABASE = {
    "soybean": {
        "suitable_soils": ["black", "loam", "clay"],
        "seasons": ["kharif"],
        "water_requirement": "medium",
        "duration_days": 90,
        "market_demand": "high"
    },
    "wheat": {
        "suitable_soils": ["loam", "clay", "alluvial"],
        "seasons": ["rabi"],
        "water_requirement": "medium",
        "duration_days": 120,
        "market_demand": "high"
    },
    "rice": {
        "suitable_soils": ["clay", "loam"],
        "seasons": ["kharif"],
        "water_requirement": "high",
        "duration_days": 120,
        "market_demand": "high"
    },
    "cotton": {
        "suitable_soils": ["black", "loam"],
        "seasons": ["kharif"],
        "water_requirement": "medium",
        "duration_days": 150,
        "market_demand": "medium"
    },
    "sugarcane": {
        "suitable_soils": ["loam", "clay", "alluvial"],
        "seasons": ["year-round"],
        "water_requirement": "high",
        "duration_days": 365,
        "market_demand": "high"
    },
    "maize": {
        "suitable_soils": ["loam", "sandy", "clay"],
        "seasons": ["kharif", "rabi", "zaid"],
        "water_requirement": "medium",
        "duration_days": 90,
        "market_demand": "medium"
    },
    "pulses": {
        "suitable_soils": ["loam", "sandy", "black"],
        "seasons": ["rabi", "zaid"],
        "water_requirement": "low",
        "duration_days": 100,
        "market_demand": "high"
    },
    "groundnut": {
        "suitable_soils": ["sandy", "loam"],
        "seasons": ["kharif", "zaid"],
        "water_requirement": "medium",
        "duration_days": 120,
        "market_demand": "medium"
    },
    "mung_bean": {
        "suitable_soils": ["loam", "sandy", "black"],
        "seasons": ["zaid"],
        "water_requirement": "low",
        "duration_days": 60,
        "market_demand": "high"
    },
    "watermelon": {
        "suitable_soils": ["sandy", "loam"],
        "seasons": ["zaid"],
        "water_requirement": "medium",
        "duration_days": 90,
        "market_demand": "medium"
    }
}


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle POST /farmer/crop-advice requests.
    
    Request Body:
    {
        "user_id": "...",
        "land_size_acres": 5.0,
        "soil_type": "black",
        "irrigation_type": "well",
        "location": {...},
        "current_crops": [...],
        "previous_crops": [...],
        "season": "kharif"  // optional, auto-detected if not provided
    }
    
    Response:
    {
        "recommendations": [
            {
                "crop_name": "...",
                "suitability_score": 0.85,
                "expected_yield": "...",
                "water_requirement": "...",
                "duration_days": 90,
                "market_demand": "...",
                "estimated_profit": "...",
                "reasoning": "...",
                "risks": [...]
            }
        ]
    }
    
    Error Responses:
    - 400: Invalid request body
    - 500: Internal server error
    """
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Validate required fields
        required_fields = ['user_id', 'land_size_acres', 'soil_type', 'irrigation_type', 'location']
        missing_fields = [field for field in required_fields if field not in body]
        
        if missing_fields:
            return error_response(400, f"Missing required fields: {', '.join(missing_fields)}")
        
        # Parse farm profile
        try:
            farm_profile = FarmProfile(**body)
        except Exception as e:
            logger.error(f"Invalid farm profile: {str(e)}")
            return error_response(400, f"Invalid farm profile data: {str(e)}")
        
        # Determine season (if not provided)
        season = body.get('season')
        if not season:
            season = _detect_season()
        
        logger.info(f"Generating crop recommendations for user {farm_profile.user_id}, season: {season}")
        
        # Generate crop recommendations
        recommendations = _generate_recommendations(farm_profile, season)
        
        # Convert to dict format
        recommendations_dict = [rec.model_dump() for rec in recommendations]
        
        logger.info(f"Generated {len(recommendations)} recommendations")
        return success_response({'recommendations': recommendations_dict})
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON in request body")
        return error_response(400, "Invalid JSON in request body")
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return error_response(500, "Internal server error")


def _detect_season() -> str:
    """
    Detect current agricultural season based on month.
    
    Kharif: June-October (monsoon crops)
    Rabi: November-March (winter crops)
    Zaid: April-May (summer crops)
    """
    month = datetime.now().month
    
    if 6 <= month <= 10:
        return "kharif"
    elif 11 <= month or month <= 3:
        return "rabi"
    else:
        return "zaid"


def _generate_recommendations(farm_profile: FarmProfile, season: str) -> List[CropRecommendation]:
    """
    Generate crop recommendations based on farm profile and season.
    
    Args:
        farm_profile: Farm profile information
        season: Current agricultural season
        
    Returns:
        List of crop recommendations sorted by suitability score
    """
    recommendations = []
    soil_type = farm_profile.soil_type.lower()
    irrigation = farm_profile.irrigation_type.lower()
    
    for crop_name, crop_info in CROP_DATABASE.items():
        # Check soil suitability
        if soil_type not in crop_info["suitable_soils"]:
            continue
        
        # Check season suitability
        if season not in crop_info["seasons"] and "year-round" not in crop_info["seasons"]:
            continue
        
        # Check water availability
        water_req = crop_info["water_requirement"]
        if water_req == "high" and irrigation == "rainfed":
            continue  # Skip high water requirement crops for rainfed farms
        
        # Calculate suitability score
        suitability_score = _calculate_suitability(
            crop_info, soil_type, irrigation, farm_profile
        )
        
        # Generate reasoning
        reasoning = _generate_reasoning(
            crop_name, crop_info, soil_type, season, irrigation
        )
        
        # Identify risks
        risks = _identify_risks(crop_name, crop_info, irrigation, farm_profile)
        
        # Create recommendation
        recommendation = CropRecommendation(
            crop_name=crop_name.capitalize(),
            suitability_score=suitability_score,
            expected_yield=_estimate_yield(crop_name, farm_profile.land_size_acres),
            water_requirement=water_req,
            duration_days=crop_info["duration_days"],
            market_demand=crop_info["market_demand"],
            estimated_profit=_estimate_profit(crop_name, farm_profile.land_size_acres),
            reasoning=reasoning,
            risks=risks
        )
        
        recommendations.append(recommendation)
    
    # Sort by suitability score (descending)
    recommendations.sort(key=lambda x: x.suitability_score, reverse=True)
    
    # Return top 5 recommendations
    return recommendations[:5]


def _calculate_suitability(
    crop_info: Dict[str, Any],
    soil_type: str,
    irrigation: str,
    farm_profile: FarmProfile
) -> float:
    """Calculate suitability score (0-1) for a crop."""
    score = 0.5  # Base score
    
    # Bonus for ideal soil match
    if soil_type in crop_info["suitable_soils"][:2]:  # Top 2 suitable soils
        score += 0.2
    else:
        score += 0.1
    
    # Bonus for good irrigation match
    water_req = crop_info["water_requirement"]
    if water_req == "low":
        score += 0.15
    elif water_req == "medium" and irrigation in ["well", "canal", "drip"]:
        score += 0.15
    elif water_req == "high" and irrigation in ["canal", "drip", "sprinkler"]:
        score += 0.15
    
    # Bonus for high market demand
    if crop_info["market_demand"] == "high":
        score += 0.1
    
    # Ensure score is between 0 and 1
    return min(1.0, max(0.0, score))


def _generate_reasoning(
    crop_name: str,
    crop_info: Dict[str, Any],
    soil_type: str,
    season: str,
    irrigation: str
) -> str:
    """Generate human-readable reasoning for recommendation."""
    reasons = []
    
    # Soil suitability
    reasons.append(f"{soil_type.capitalize()} soil is suitable for {crop_name}")
    
    # Season match
    reasons.append(f"Current season ({season}) is ideal for this crop")
    
    # Water availability
    water_req = crop_info["water_requirement"]
    if irrigation != "rainfed":
        reasons.append(f"{water_req.capitalize()} water requirement matches your {irrigation} irrigation")
    
    # Market demand
    if crop_info["market_demand"] == "high":
        reasons.append("Good market demand in your region")
    
    return ". ".join(reasons) + "."


def _identify_risks(
    crop_name: str,
    crop_info: Dict[str, Any],
    irrigation: str,
    farm_profile: FarmProfile
) -> List[str]:
    """Identify potential risks for the crop."""
    risks = []
    
    # Water-related risks
    if crop_info["water_requirement"] == "high" and irrigation == "well":
        risks.append("High water requirement may strain well capacity")
    
    # Duration-related risks
    if crop_info["duration_days"] > 150:
        risks.append("Long duration crop requires sustained care")
    
    # Market risks
    if crop_info["market_demand"] == "medium":
        risks.append("Moderate price fluctuation possible")
    
    # Generic risks
    risks.append("Pest and disease management required")
    
    return risks


def _estimate_yield(crop_name: str, land_size: float) -> str:
    """Estimate crop yield based on crop type and land size."""
    # Simplified yield estimates (quintals per acre)
    yield_per_acre = {
        "soybean": "15-20",
        "wheat": "20-25",
        "rice": "25-30",
        "cotton": "10-15",
        "sugarcane": "300-400",
        "maize": "20-25",
        "pulses": "8-12",
        "groundnut": "15-20",
        "mung_bean": "6-8",
        "watermelon": "100-150"
    }
    
    yield_range = yield_per_acre.get(crop_name, "10-15")
    return f"{yield_range} quintals per acre"


def _estimate_profit(crop_name: str, land_size: float) -> str:
    """Estimate profit range based on crop type and land size."""
    # Simplified profit estimates (Rs. per acre)
    profit_per_acre = {
        "soybean": "25,000-35,000",
        "wheat": "20,000-30,000",
        "rice": "30,000-40,000",
        "cotton": "35,000-50,000",
        "sugarcane": "50,000-80,000",
        "maize": "20,000-30,000",
        "pulses": "25,000-35,000",
        "groundnut": "30,000-40,000",
        "mung_bean": "20,000-30,000",
        "watermelon": "40,000-60,000"
    }
    
    profit_range = profit_per_acre.get(crop_name, "20,000-30,000")
    return f"Rs. {profit_range} per acre"


def success_response(data: Dict[str, Any], status_code: int = 200) -> Dict[str, Any]:
    """Create a successful API response."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(data)
    }


def error_response(status_code: int, message: str) -> Dict[str, Any]:
    """Create an error API response."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'error': message
        })
    }
