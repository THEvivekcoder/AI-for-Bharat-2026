"""Health advisor service for symptom analysis."""

from typing import List, Dict, Any
import logging

from src.models.health import HealthGuidance

logger = logging.getLogger(__name__)


class HealthAdvisor:
    """Service for analyzing symptoms and providing health guidance."""
    
    # Emergency symptoms that require immediate medical attention
    EMERGENCY_SYMPTOMS = {
        "chest pain", "difficulty breathing", "severe bleeding", "unconscious",
        "severe headache", "stroke symptoms", "heart attack", "seizure",
        "severe abdominal pain", "severe burns", "poisoning", "choking",
        "severe allergic reaction", "high fever with confusion"
    }
    
    # Urgent symptoms that need medical attention soon
    URGENT_SYMPTOMS = {
        "high fever", "persistent vomiting", "severe pain", "blood in stool",
        "blood in urine", "severe diarrhea", "dehydration", "fainting",
        "severe cough", "difficulty swallowing", "severe rash"
    }
    
    # Common symptom patterns and their possible conditions
    SYMPTOM_PATTERNS = {
        ("fever", "cough", "cold"): {
            "conditions": ["Common cold", "Viral fever", "Seasonal flu"],
            "urgency": "soon",
            "self_care": [
                "Rest and stay hydrated",
                "Take paracetamol for fever",
                "Gargle with warm salt water",
                "Avoid cold drinks"
            ],
            "when_to_seek": "If fever persists for more than 3 days or exceeds 103°F, consult a doctor"
        },
        ("fever", "body ache", "headache"): {
            "conditions": ["Viral fever", "Dengue", "Malaria", "Chikungunya"],
            "urgency": "soon",
            "self_care": [
                "Rest and drink plenty of fluids",
                "Take paracetamol for fever and pain",
                "Monitor temperature regularly"
            ],
            "when_to_seek": "If fever persists beyond 3 days, or if you develop rash, bleeding, or severe weakness"
        },
        ("stomach pain", "diarrhea"): {
            "conditions": ["Gastroenteritis", "Food poisoning", "Indigestion"],
            "urgency": "routine",
            "self_care": [
                "Stay hydrated with ORS",
                "Eat bland foods (rice, banana, toast)",
                "Avoid spicy and oily foods",
                "Rest"
            ],
            "when_to_seek": "If diarrhea persists for more than 2 days, or if you see blood in stool"
        },
        ("cough", "sore throat"): {
            "conditions": ["Upper respiratory infection", "Pharyngitis", "Common cold"],
            "urgency": "routine",
            "self_care": [
                "Gargle with warm salt water",
                "Drink warm liquids",
                "Take throat lozenges",
                "Rest your voice"
            ],
            "when_to_seek": "If symptoms worsen or persist beyond a week"
        },
        ("headache", "nausea"): {
            "conditions": ["Migraine", "Tension headache", "Dehydration"],
            "urgency": "routine",
            "self_care": [
                "Rest in a quiet, dark room",
                "Stay hydrated",
                "Apply cold compress to forehead",
                "Take pain reliever if needed"
            ],
            "when_to_seek": "If headache is severe, sudden, or accompanied by vision changes"
        }
    }
    
    # Medical disclaimer
    DISCLAIMER = (
        "This information is for educational purposes only and is not a substitute "
        "for professional medical advice, diagnosis, or treatment. Always seek the "
        "advice of your physician or other qualified health provider with any questions "
        "you may have regarding a medical condition."
    )
    
    def analyze_symptoms(self, symptoms: List[str], user_info: Dict[str, Any] = None) -> HealthGuidance:
        """
        Analyze symptoms and provide health guidance.
        
        Args:
            symptoms: List of symptom descriptions
            user_info: Optional user information (age, gender, etc.)
            
        Returns:
            HealthGuidance with recommendations and urgency level
        """
        if not symptoms:
            return self._create_default_guidance()
        
        # Normalize symptoms (lowercase, strip whitespace)
        normalized_symptoms = [s.lower().strip() for s in symptoms]
        
        # Check for emergency symptoms first
        if self._has_emergency_symptoms(normalized_symptoms):
            return self._create_emergency_guidance(normalized_symptoms)
        
        # Check for urgent symptoms
        if self._has_urgent_symptoms(normalized_symptoms):
            return self._create_urgent_guidance(normalized_symptoms)
        
        # Match symptom patterns
        matched_pattern = self._match_symptom_pattern(normalized_symptoms)
        
        if matched_pattern:
            return self._create_guidance_from_pattern(matched_pattern, normalized_symptoms)
        
        # Default guidance for unmatched symptoms
        return self._create_general_guidance(normalized_symptoms)
    
    def _has_emergency_symptoms(self, symptoms: List[str]) -> bool:
        """Check if any emergency symptoms are present."""
        for symptom in symptoms:
            for emergency in self.EMERGENCY_SYMPTOMS:
                if emergency in symptom:
                    return True
        return False
    
    def _has_urgent_symptoms(self, symptoms: List[str]) -> bool:
        """Check if any urgent symptoms are present."""
        for symptom in symptoms:
            for urgent in self.URGENT_SYMPTOMS:
                if urgent in symptom:
                    return True
        return False
    
    def _match_symptom_pattern(self, symptoms: List[str]) -> Dict[str, Any]:
        """
        Match symptoms against known patterns.
        
        Returns the best matching pattern or None.
        """
        best_match = None
        best_match_count = 0
        
        for pattern_symptoms, pattern_data in self.SYMPTOM_PATTERNS.items():
            match_count = 0
            for pattern_symptom in pattern_symptoms:
                for user_symptom in symptoms:
                    if pattern_symptom in user_symptom or user_symptom in pattern_symptom:
                        match_count += 1
                        break
            
            if match_count > best_match_count:
                best_match_count = match_count
                best_match = pattern_data
        
        # Only return match if at least 2 symptoms match
        if best_match_count >= 2:
            return best_match
        
        return None
    
    def _create_emergency_guidance(self, symptoms: List[str]) -> HealthGuidance:
        """Create guidance for emergency symptoms."""
        return HealthGuidance(
            urgency_level="emergency",
            possible_conditions=["Medical emergency"],
            self_care_recommendations=[],
            when_to_seek_care="SEEK IMMEDIATE MEDICAL ATTENTION. Call emergency services or go to the nearest hospital emergency room immediately.",
            red_flags=[
                "Chest pain or pressure",
                "Difficulty breathing",
                "Severe bleeding",
                "Loss of consciousness",
                "Severe allergic reaction"
            ],
            disclaimer=self.DISCLAIMER,
            confidence=0.95
        )
    
    def _create_urgent_guidance(self, symptoms: List[str]) -> HealthGuidance:
        """Create guidance for urgent symptoms."""
        return HealthGuidance(
            urgency_level="urgent",
            possible_conditions=["Condition requiring medical attention"],
            self_care_recommendations=[
                "Monitor symptoms closely",
                "Stay hydrated",
                "Rest"
            ],
            when_to_seek_care="Seek medical attention within 24 hours. Visit a doctor or health center as soon as possible.",
            red_flags=[
                "Symptoms getting worse",
                "High fever (above 103°F)",
                "Severe pain",
                "Signs of dehydration"
            ],
            disclaimer=self.DISCLAIMER,
            confidence=0.80
        )
    
    def _create_guidance_from_pattern(
        self,
        pattern: Dict[str, Any],
        symptoms: List[str]
    ) -> HealthGuidance:
        """Create guidance from a matched symptom pattern."""
        return HealthGuidance(
            urgency_level=pattern["urgency"],
            possible_conditions=pattern["conditions"],
            self_care_recommendations=pattern["self_care"],
            when_to_seek_care=pattern["when_to_seek"],
            red_flags=[
                "Symptoms worsen significantly",
                "New symptoms develop",
                "Fever above 103°F",
                "Difficulty breathing"
            ],
            disclaimer=self.DISCLAIMER,
            confidence=0.75
        )
    
    def _create_general_guidance(self, symptoms: List[str]) -> HealthGuidance:
        """Create general guidance for unmatched symptoms."""
        return HealthGuidance(
            urgency_level="soon",
            possible_conditions=["Various conditions possible"],
            self_care_recommendations=[
                "Monitor your symptoms",
                "Rest and stay hydrated",
                "Maintain good hygiene",
                "Eat nutritious food"
            ],
            when_to_seek_care="If symptoms persist for more than 2-3 days or worsen, consult a healthcare provider.",
            red_flags=[
                "Symptoms worsen rapidly",
                "High fever develops",
                "Severe pain",
                "Difficulty breathing"
            ],
            disclaimer=self.DISCLAIMER,
            confidence=0.60
        )
    
    def _create_default_guidance(self) -> HealthGuidance:
        """Create default guidance when no symptoms provided."""
        return HealthGuidance(
            urgency_level="routine",
            possible_conditions=[],
            self_care_recommendations=[
                "Maintain a healthy lifestyle",
                "Exercise regularly",
                "Eat balanced meals",
                "Get adequate sleep"
            ],
            when_to_seek_care="Consult a doctor for regular health checkups.",
            red_flags=[],
            disclaimer=self.DISCLAIMER,
            confidence=0.50
        )
