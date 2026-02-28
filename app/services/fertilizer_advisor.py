"""Fertilizer Advisor service for fertilizer recommendations"""
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.farmer import FarmProfile, FertilizerRecommendation
from app.schemas.farmer import FertilizerRecommendationResponse, SoilData
import logging

logger = logging.getLogger(__name__)


class FertilizerAdvisor:
    """Service for providing fertilizer recommendations"""
    
    # Crop nutrient requirements (NPK ratios and quantities)
    CROP_NUTRIENT_REQUIREMENTS = {
        "rice": {
            "sowing": {
                "npk_ratio": "10:26:26",
                "quantity": "50 kg/acre",
                "timing": "At the time of sowing or transplanting",
                "method": "Band placement or broadcasting"
            },
            "vegetative": {
                "npk_ratio": "Urea (46% N)",
                "quantity": "40 kg/acre",
                "timing": "20-25 days after transplanting",
                "method": "Top dressing"
            },
            "flowering": {
                "npk_ratio": "Urea (46% N)",
                "quantity": "30 kg/acre",
                "timing": "At panicle initiation stage",
                "method": "Top dressing"
            }
        },
        "wheat": {
            "sowing": {
                "npk_ratio": "12:32:16",
                "quantity": "60 kg/acre",
                "timing": "At the time of sowing",
                "method": "Drilling with seed"
            },
            "vegetative": {
                "npk_ratio": "Urea (46% N)",
                "quantity": "40 kg/acre",
                "timing": "20-25 days after sowing (Crown root stage)",
                "method": "Top dressing followed by irrigation"
            },
            "flowering": {
                "npk_ratio": "Urea (46% N)",
                "quantity": "20 kg/acre",
                "timing": "At flowering stage",
                "method": "Top dressing"
            }
        },
        "cotton": {
            "sowing": {
                "npk_ratio": "12:32:16",
                "quantity": "50 kg/acre",
                "timing": "At sowing",
                "method": "Band placement"
            },
            "vegetative": {
                "npk_ratio": "Urea (46% N)",
                "quantity": "50 kg/acre",
                "timing": "30-35 days after sowing",
                "method": "Side dressing"
            },
            "flowering": {
                "npk_ratio": "19:19:19",
                "quantity": "20 kg/acre",
                "timing": "At flowering and boll formation",
                "method": "Foliar spray (2% solution)"
            }
        },
        "maize": {
            "sowing": {
                "npk_ratio": "12:32:16",
                "quantity": "50 kg/acre",
                "timing": "At sowing",
                "method": "Band placement"
            },
            "vegetative": {
                "npk_ratio": "Urea (46% N)",
                "quantity": "60 kg/acre",
                "timing": "25-30 days after sowing (Knee-high stage)",
                "method": "Side dressing"
            }
        },
        "sugarcane": {
            "sowing": {
                "npk_ratio": "12:32:16",
                "quantity": "100 kg/acre",
                "timing": "At planting",
                "method": "Band placement in furrows"
            },
            "vegetative": {
                "npk_ratio": "Urea (46% N)",
                "quantity": "80 kg/acre",
                "timing": "45-60 days after planting",
                "method": "Side dressing"
            },
            "maturity": {
                "npk_ratio": "Urea (46% N)",
                "quantity": "60 kg/acre",
                "timing": "90-120 days after planting",
                "method": "Side dressing"
            }
        },
        "pulses": {
            "sowing": {
                "npk_ratio": "12:32:16",
                "quantity": "40 kg/acre",
                "timing": "At sowing",
                "method": "Drilling with seed"
            },
            "flowering": {
                "npk_ratio": "0:52:34 (DAP)",
                "quantity": "20 kg/acre",
                "timing": "At flowering",
                "method": "Foliar spray"
            }
        },
        "vegetables": {
            "sowing": {
                "npk_ratio": "19:19:19",
                "quantity": "40 kg/acre",
                "timing": "At transplanting or sowing",
                "method": "Broadcasting and mixing"
            },
            "vegetative": {
                "npk_ratio": "Urea (46% N)",
                "quantity": "30 kg/acre",
                "timing": "15-20 days after planting",
                "method": "Side dressing"
            },
            "flowering": {
                "npk_ratio": "0:52:34 (DAP)",
                "quantity": "20 kg/acre",
                "timing": "At flowering/fruiting",
                "method": "Side dressing or foliar spray"
            }
        }
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def recommend_fertilizer(
        self,
        farm_profile: FarmProfile,
        crop_name: str,
        growth_stage: str,
        soil_data: Optional[SoilData] = None
    ) -> FertilizerRecommendationResponse:
        """
        Recommend fertilizer based on crop, growth stage, and soil conditions
        
        Args:
            farm_profile: Farm profile information
            crop_name: Name of the crop
            growth_stage: Current growth stage (sowing, vegetative, flowering, fruiting, maturity)
            soil_data: Optional soil test data
        
        Returns:
            Fertilizer recommendation with type, quantity, timing, and method
        """
        logger.info(f"Generating fertilizer recommendation for {crop_name} at {growth_stage} stage")
        
        # Get base recommendation for crop and stage
        crop_requirements = self.CROP_NUTRIENT_REQUIREMENTS.get(crop_name.lower())
        
        if not crop_requirements:
            # Default recommendation for unknown crops
            return self._get_default_recommendation(crop_name, growth_stage)
        
        stage_requirement = crop_requirements.get(growth_stage.lower())
        
        if not stage_requirement:
            # If stage not found, try to find closest stage
            stage_requirement = self._get_closest_stage_requirement(crop_requirements, growth_stage)
        
        # Adjust recommendation based on soil data if available
        if soil_data:
            stage_requirement = self._adjust_for_soil_data(stage_requirement, soil_data)
        
        # Generate additional notes
        additional_notes = self._generate_additional_notes(
            farm_profile,
            crop_name,
            growth_stage,
            soil_data
        )
        
        return FertilizerRecommendationResponse(
            fertilizer_type=stage_requirement["npk_ratio"],
            quantity_per_acre=stage_requirement["quantity"],
            timing=stage_requirement["timing"],
            application_method=stage_requirement["method"],
            additional_notes=additional_notes,
            crop_name=crop_name,
            growth_stage=growth_stage
        )
    
    def _get_default_recommendation(self, crop_name: str, growth_stage: str) -> FertilizerRecommendationResponse:
        """Get default recommendation for unknown crops"""
        default_recommendations = {
            "sowing": {
                "npk_ratio": "12:32:16",
                "quantity": "50 kg/acre",
                "timing": "At the time of sowing",
                "method": "Band placement or broadcasting"
            },
            "vegetative": {
                "npk_ratio": "Urea (46% N)",
                "quantity": "40 kg/acre",
                "timing": "20-30 days after sowing",
                "method": "Top dressing"
            },
            "flowering": {
                "npk_ratio": "19:19:19",
                "quantity": "20 kg/acre",
                "timing": "At flowering stage",
                "method": "Foliar spray or side dressing"
            },
            "fruiting": {
                "npk_ratio": "0:52:34",
                "quantity": "20 kg/acre",
                "timing": "At fruiting stage",
                "method": "Side dressing"
            },
            "maturity": {
                "npk_ratio": "0:0:50 (Potash)",
                "quantity": "15 kg/acre",
                "timing": "At maturity stage",
                "method": "Side dressing"
            }
        }
        
        stage_rec = default_recommendations.get(growth_stage.lower(), default_recommendations["vegetative"])
        
        return FertilizerRecommendationResponse(
            fertilizer_type=stage_rec["npk_ratio"],
            quantity_per_acre=stage_rec["quantity"],
            timing=stage_rec["timing"],
            application_method=stage_rec["method"],
            additional_notes="This is a general recommendation. Soil testing is recommended for precise fertilizer application.",
            crop_name=crop_name,
            growth_stage=growth_stage
        )
    
    def _get_closest_stage_requirement(self, crop_requirements: Dict, growth_stage: str) -> Dict[str, str]:
        """Find closest matching growth stage if exact match not found"""
        stage_mapping = {
            "fruiting": "flowering",
            "maturity": "flowering"
        }
        
        mapped_stage = stage_mapping.get(growth_stage.lower(), "vegetative")
        return crop_requirements.get(mapped_stage, crop_requirements.get("sowing"))
    
    def _adjust_for_soil_data(self, base_recommendation: Dict[str, str], soil_data: SoilData) -> Dict[str, str]:
        """Adjust fertilizer recommendation based on soil test data"""
        adjusted = base_recommendation.copy()
        adjustments = []
        
        # Adjust based on soil pH
        if soil_data.soil_ph:
            if soil_data.soil_ph < 5.5:
                adjustments.append("Apply lime to correct soil acidity before fertilizer application")
            elif soil_data.soil_ph > 8.0:
                adjustments.append("Apply gypsum to correct soil alkalinity")
        
        # Adjust based on nutrient levels
        if soil_data.nitrogen_level == "high":
            adjustments.append("Reduce nitrogen application by 25%")
        elif soil_data.nitrogen_level == "low":
            adjustments.append("Increase nitrogen application by 25%")
        
        if soil_data.phosphorus_level == "high":
            adjustments.append("Reduce phosphorus application")
        elif soil_data.phosphorus_level == "low":
            adjustments.append("Increase phosphorus application")
        
        if soil_data.potassium_level == "low":
            adjustments.append("Apply additional potash (MOP) at 20 kg/acre")
        
        # Add adjustments to method if any
        if adjustments:
            adjusted["method"] = adjusted["method"] + ". " + ". ".join(adjustments)
        
        return adjusted
    
    def _generate_additional_notes(
        self,
        farm_profile: FarmProfile,
        crop_name: str,
        growth_stage: str,
        soil_data: Optional[SoilData]
    ) -> str:
        """Generate additional notes and recommendations"""
        notes = []
        
        # Irrigation-specific notes
        if farm_profile.irrigation_type == "drip":
            notes.append("With drip irrigation, consider fertigation for better nutrient efficiency")
        elif farm_profile.irrigation_type == "rainfed":
            notes.append("Apply fertilizer before expected rainfall for better absorption")
        
        # Soil type specific notes
        if farm_profile.soil_type in ["sandy", "laterite"]:
            notes.append("Sandy soils require split application to prevent nutrient leaching")
        elif farm_profile.soil_type == "clay":
            notes.append("Clay soils retain nutrients well, avoid over-application")
        
        # Organic matter recommendation
        notes.append("Apply well-decomposed farmyard manure (FYM) at 5-10 tons/acre for better soil health")
        
        # Micronutrient recommendation
        if growth_stage in ["vegetative", "flowering"]:
            notes.append("Consider foliar spray of micronutrients (Zinc, Boron) if deficiency symptoms appear")
        
        # Soil testing recommendation
        if not soil_data:
            notes.append("Soil testing is highly recommended for precise fertilizer management")
        
        return ". ".join(notes) + "."
