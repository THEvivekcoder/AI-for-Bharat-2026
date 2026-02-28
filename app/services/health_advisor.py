"""Health Advisor service for symptom analysis and health guidance"""
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.health import HealthFacility
from app.schemas.health import (
    HealthGuidance,
    BasicHealthInfo,
    HealthFacilityResponse,
    Location
)
import logging
import math

logger = logging.getLogger(__name__)


class HealthAdvisor:
    """Service for providing health guidance and facility information"""
    
    # Emergency symptoms that require immediate medical attention
    EMERGENCY_SYMPTOMS = [
        "chest pain",
        "difficulty breathing",
        "severe bleeding",
        "unconscious",
        "seizure",
        "severe head injury",
        "stroke symptoms",
        "heart attack",
        "severe abdominal pain",
        "poisoning",
        "severe burns",
        "choking",
        "severe allergic reaction",
        "loss of consciousness",
        "paralysis",
        "severe trauma"
    ]
    
    # Urgent symptoms requiring medical care soon
    URGENT_SYMPTOMS = [
        "high fever",
        "persistent vomiting",
        "severe diarrhea",
        "dehydration",
        "severe pain",
        "bleeding",
        "infection",
        "difficulty urinating",
        "severe headache",
        "vision problems",
        "confusion",
        "severe cough"
    ]
    
    # Symptom to condition mapping (simplified)
    SYMPTOM_CONDITIONS = {
        "fever": ["Common cold", "Flu", "Viral infection", "Bacterial infection"],
        "cough": ["Common cold", "Bronchitis", "Pneumonia", "Allergies"],
        "headache": ["Tension headache", "Migraine", "Dehydration", "Stress"],
        "stomach pain": ["Indigestion", "Gastritis", "Food poisoning", "Ulcer"],
        "diarrhea": ["Food poisoning", "Viral gastroenteritis", "Bacterial infection"],
        "vomiting": ["Food poisoning", "Viral gastroenteritis", "Motion sickness"],
        "body ache": ["Flu", "Viral infection", "Overexertion", "Dengue"],
        "sore throat": ["Viral pharyngitis", "Bacterial pharyngitis", "Tonsillitis"],
        "runny nose": ["Common cold", "Allergies", "Sinusitis"],
        "fatigue": ["Anemia", "Thyroid disorder", "Chronic fatigue", "Sleep deprivation"],
        "dizziness": ["Low blood pressure", "Dehydration", "Inner ear problem", "Anemia"],
        "rash": ["Allergic reaction", "Viral infection", "Skin infection", "Eczema"],
        "joint pain": ["Arthritis", "Injury", "Gout", "Viral infection"]
    }
    
    # Self-care recommendations by symptom
    SELF_CARE_RECOMMENDATIONS = {
        "fever": [
            "Rest and stay hydrated",
            "Take paracetamol if fever is high (above 100°F)",
            "Use cool compresses on forehead",
            "Wear light clothing",
            "Monitor temperature regularly"
        ],
        "cough": [
            "Stay hydrated with warm liquids",
            "Use honey and ginger tea",
            "Avoid cold drinks and ice cream",
            "Rest your voice",
            "Use steam inhalation"
        ],
        "headache": [
            "Rest in a quiet, dark room",
            "Apply cold or warm compress",
            "Stay hydrated",
            "Avoid screens and bright lights",
            "Take paracetamol if needed"
        ],
        "stomach pain": [
            "Eat bland foods (rice, banana, toast)",
            "Avoid spicy and oily foods",
            "Stay hydrated with ORS",
            "Rest and avoid heavy meals",
            "Apply warm compress on abdomen"
        ],
        "diarrhea": [
            "Drink ORS (oral rehydration solution)",
            "Eat bland foods",
            "Avoid dairy and spicy foods",
            "Maintain hygiene",
            "Rest and monitor hydration"
        ]
    }
    
    # Standard disclaimer
    HEALTH_DISCLAIMER = (
        "This guidance is for informational purposes only and is not a substitute for "
        "professional medical advice, diagnosis, or treatment. Always seek the advice of "
        "your physician or other qualified health provider with any questions you may have "
        "regarding a medical condition. If you think you may have a medical emergency, "
        "call your doctor or emergency services immediately."
    )
    
    def __init__(self, db: Session):
        self.db = db
    
    def analyze_symptoms(
        self,
        symptoms: List[str],
        user_info: Optional[BasicHealthInfo] = None
    ) -> HealthGuidance:
        """
        Analyze symptoms and provide health guidance
        
        Args:
            symptoms: List of symptoms described by user
            user_info: Optional basic health information
        
        Returns:
            HealthGuidance with urgency level, recommendations, and disclaimer
        """
        logger.info(f"Analyzing symptoms: {symptoms}")
        
        # Normalize symptoms to lowercase
        normalized_symptoms = [s.lower().strip() for s in symptoms]
        
        # Check for emergency symptoms
        urgency_level, emergency_detected = self._determine_urgency(normalized_symptoms)
        
        # Get possible conditions
        possible_conditions = self._identify_conditions(normalized_symptoms)
        
        # Get self-care recommendations
        self_care = self._get_self_care_recommendations(normalized_symptoms, urgency_level)
        
        # Determine when to seek care
        when_to_seek_care = self._get_care_timing(urgency_level, emergency_detected)
        
        # Get red flags
        red_flags = self._get_red_flags(normalized_symptoms, urgency_level)
        
        # Calculate confidence (simplified)
        confidence = self._calculate_confidence(normalized_symptoms, possible_conditions)
        
        guidance = HealthGuidance(
            urgency_level=urgency_level,
            possible_conditions=possible_conditions[:5],  # Top 5 conditions
            self_care_recommendations=self_care,
            when_to_seek_care=when_to_seek_care,
            red_flags=red_flags,
            disclaimer=self.HEALTH_DISCLAIMER,
            confidence=confidence
        )
        
        logger.info(f"Generated health guidance with urgency level: {urgency_level}")
        return guidance
    
    def _determine_urgency(self, symptoms: List[str]) -> Tuple[str, bool]:
        """
        Determine urgency level based on symptoms
        
        Returns:
            Tuple of (urgency_level, emergency_detected)
        """
        # Check for emergency symptoms
        for symptom in symptoms:
            for emergency in self.EMERGENCY_SYMPTOMS:
                if emergency in symptom:
                    return ("emergency", True)
        
        # Check for urgent symptoms
        for symptom in symptoms:
            for urgent in self.URGENT_SYMPTOMS:
                if urgent in symptom:
                    return ("urgent", False)
        
        # Check symptom severity indicators
        severity_keywords = ["severe", "extreme", "unbearable", "intense", "acute"]
        for symptom in symptoms:
            if any(keyword in symptom for keyword in severity_keywords):
                return ("urgent", False)
        
        # Check for multiple symptoms (may indicate more serious condition)
        if len(symptoms) >= 4:
            return ("soon", False)
        
        # Default to routine
        return ("routine", False)
    
    def _identify_conditions(self, symptoms: List[str]) -> List[str]:
        """Identify possible conditions based on symptoms"""
        condition_scores = {}
        
        for symptom in symptoms:
            # Find matching conditions for each symptom
            for key, conditions in self.SYMPTOM_CONDITIONS.items():
                if key in symptom:
                    for condition in conditions:
                        condition_scores[condition] = condition_scores.get(condition, 0) + 1
        
        # Sort conditions by frequency (most common first)
        sorted_conditions = sorted(
            condition_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Return condition names
        return [condition for condition, _ in sorted_conditions]
    
    def _get_self_care_recommendations(
        self,
        symptoms: List[str],
        urgency_level: str
    ) -> List[str]:
        """Get self-care recommendations based on symptoms"""
        if urgency_level == "emergency":
            return ["Seek emergency medical care immediately", "Call ambulance or go to nearest hospital"]
        
        if urgency_level == "urgent":
            return ["Seek medical care as soon as possible", "Visit nearest health facility today"]
        
        recommendations = set()
        
        # Add general recommendations
        recommendations.add("Rest and get adequate sleep")
        recommendations.add("Stay well hydrated")
        recommendations.add("Maintain good hygiene")
        
        # Add symptom-specific recommendations
        for symptom in symptoms:
            for key, recs in self.SELF_CARE_RECOMMENDATIONS.items():
                if key in symptom:
                    recommendations.update(recs[:3])  # Add top 3 recommendations
        
        return list(recommendations)[:8]  # Return max 8 recommendations
    
    def _get_care_timing(self, urgency_level: str, emergency_detected: bool) -> str:
        """Get guidance on when to seek medical care"""
        if urgency_level == "emergency":
            return "Seek emergency medical care IMMEDIATELY. Call ambulance or go to nearest hospital now."
        
        if urgency_level == "urgent":
            return "Seek medical care within 24 hours. Visit a doctor or health facility today."
        
        if urgency_level == "soon":
            return "Schedule a medical consultation within 2-3 days if symptoms persist or worsen."
        
        return "Monitor symptoms. Seek medical care if symptoms worsen or persist beyond 3-5 days."
    
    def _get_red_flags(self, symptoms: List[str], urgency_level: str) -> List[str]:
        """Get warning signs that require immediate medical attention"""
        red_flags = []
        
        if urgency_level == "emergency":
            red_flags.append("You are experiencing emergency symptoms")
        
        # General red flags
        red_flags.extend([
            "Symptoms suddenly worsen",
            "High fever above 103°F (39.4°C)",
            "Difficulty breathing or shortness of breath",
            "Severe or persistent pain",
            "Signs of dehydration (dark urine, dizziness, dry mouth)",
            "Symptoms persist beyond 5-7 days",
            "New or unusual symptoms develop"
        ])
        
        return red_flags[:6]  # Return top 6 red flags
    
    def _calculate_confidence(
        self,
        symptoms: List[str],
        possible_conditions: List[str]
    ) -> float:
        """Calculate confidence score for the guidance"""
        # Base confidence
        confidence = 0.7
        
        # Reduce confidence if no conditions identified
        if not possible_conditions:
            confidence -= 0.2
        
        # Reduce confidence if symptoms are vague
        vague_keywords = ["pain", "discomfort", "feeling unwell", "not feeling good"]
        vague_count = sum(1 for s in symptoms if any(k in s for k in vague_keywords))
        if vague_count >= len(symptoms) * 0.5:
            confidence -= 0.1
        
        # Increase confidence if specific symptoms
        specific_keywords = ["fever", "cough", "vomiting", "diarrhea", "rash"]
        specific_count = sum(1 for s in symptoms if any(k in s for k in specific_keywords))
        if specific_count >= 2:
            confidence += 0.1
        
        return min(1.0, max(0.3, confidence))
    
    def find_facilities(
        self,
        location: Location,
        facility_type: Optional[str] = None,
        radius_km: int = 25
    ) -> List[HealthFacilityResponse]:
        """
        Find nearby health facilities
        
        Args:
            location: User location with state, district, and coordinates
            facility_type: Optional filter by facility type (PHC, CHC, etc.)
            radius_km: Search radius in kilometers
        
        Returns:
            List of health facilities sorted by distance
        """
        logger.info(f"Finding health facilities near {location.district}, {location.state}")
        
        # Build query
        query = self.db.query(HealthFacility).filter(
            HealthFacility.state == location.state,
            HealthFacility.district == location.district
        )
        
        if facility_type:
            query = query.filter(HealthFacility.facility_type == facility_type)
        
        facilities = query.all()
        
        # Calculate distances if coordinates provided
        facilities_with_distance = []
        for facility in facilities:
            distance = None
            if (location.latitude and location.longitude and 
                facility.latitude and facility.longitude):
                distance = self._calculate_distance(
                    location.latitude,
                    location.longitude,
                    float(facility.latitude),
                    float(facility.longitude)
                )
                
                # Filter by radius
                if distance > radius_km:
                    continue
            
            facility_response = HealthFacilityResponse(
                facility_id=str(facility.facility_id),
                name=facility.name,
                facility_type=facility.facility_type,
                state=facility.state,
                district=facility.district,
                address=facility.address,
                latitude=float(facility.latitude) if facility.latitude else None,
                longitude=float(facility.longitude) if facility.longitude else None,
                contact=facility.contact,
                services=facility.services,
                distance_km=round(distance, 2) if distance else None,
                created_at=facility.created_at
            )
            
            facilities_with_distance.append(facility_response)
        
        # Sort by distance (facilities without distance at the end)
        facilities_with_distance.sort(
            key=lambda x: (x.distance_km is None, x.distance_km if x.distance_km else float('inf'))
        )
        
        logger.info(f"Found {len(facilities_with_distance)} health facilities")
        return facilities_with_distance
    
    def _calculate_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """
        Calculate distance between two coordinates using Haversine formula
        
        Returns:
            Distance in kilometers
        """
        # Earth radius in kilometers
        R = 6371.0
        
        # Convert to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = (math.sin(dlat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        distance = R * c
        return distance
