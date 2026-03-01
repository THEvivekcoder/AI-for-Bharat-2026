"""Eligibility checking engine for BharatSahayak."""

from typing import List, Optional, Tuple
from dataclasses import dataclass

from src.models.user import UserProfile
from src.models.scheme import Scheme
from src.models.eligibility import EligibilityCriteria


@dataclass
class EligibilityResult:
    """Result of eligibility check."""
    
    is_eligible: bool
    reasoning: List[str]
    missing_criteria: List[str]
    confidence: float = 1.0


class EligibilityChecker:
    """
    Eligibility checking engine that evaluates user profiles against scheme criteria.
    
    Supports checking:
    - Age range (age_min, age_max)
    - Income limits (income_max)
    - Occupation matching
    - Location-based eligibility (state, district)
    - Education level
    - Gender criteria
    - Custom criteria
    """
    
    def check_eligibility(
        self,
        user_profile: UserProfile,
        scheme: Scheme
    ) -> EligibilityResult:
        """
        Check if user meets scheme eligibility criteria.
        
        Evaluates all criteria in the scheme's eligibility_criteria:
        - Age range: User age must be within [age_min, age_max]
        - Income limit: User income must be <= income_max
        - Occupation: User occupation must be in the occupation list
        - Location: User state/district must be in the location list
        - Education: User education level must be in the education list
        - Gender: User gender must match gender requirement
        
        Args:
            user_profile: User profile with personal information
            scheme: Scheme with eligibility criteria
            
        Returns:
            EligibilityResult with is_eligible flag, reasoning, and missing criteria
        """
        criteria = scheme.eligibility_criteria
        reasoning = []
        missing_criteria = []
        
        # Check age range
        age_eligible, age_reason, age_missing = self._check_age(
            user_profile.age,
            criteria.age_min,
            criteria.age_max
        )
        if age_reason:
            reasoning.append(age_reason)
        if age_missing:
            missing_criteria.extend(age_missing)
        
        # Check income limit
        income_eligible, income_reason, income_missing = self._check_income(
            user_profile.income_bracket,
            criteria.income_max
        )
        if income_reason:
            reasoning.append(income_reason)
        if income_missing:
            missing_criteria.extend(income_missing)
        
        # Check occupation
        occupation_eligible, occupation_reason, occupation_missing = self._check_occupation(
            user_profile.occupation,
            criteria.occupation
        )
        if occupation_reason:
            reasoning.append(occupation_reason)
        if occupation_missing:
            missing_criteria.extend(occupation_missing)
        
        # Check location
        location_eligible, location_reason, location_missing = self._check_location(
            user_profile.location.state,
            user_profile.location.district,
            criteria.location
        )
        if location_reason:
            reasoning.append(location_reason)
        if location_missing:
            missing_criteria.extend(location_missing)
        
        # Check education level
        education_eligible, education_reason, education_missing = self._check_education(
            user_profile.education_level,
            criteria.education
        )
        if education_reason:
            reasoning.append(education_reason)
        if education_missing:
            missing_criteria.extend(education_missing)
        
        # Check gender
        gender_eligible, gender_reason, gender_missing = self._check_gender(
            user_profile.gender,
            criteria.gender
        )
        if gender_reason:
            reasoning.append(gender_reason)
        if gender_missing:
            missing_criteria.extend(gender_missing)
        
        # Determine overall eligibility
        is_eligible = (
            age_eligible and
            income_eligible and
            occupation_eligible and
            location_eligible and
            education_eligible and
            gender_eligible
        )
        
        # Calculate confidence based on missing profile data
        confidence = self._calculate_confidence(user_profile, missing_criteria)
        
        return EligibilityResult(
            is_eligible=is_eligible,
            reasoning=reasoning,
            missing_criteria=missing_criteria,
            confidence=confidence
        )
    
    def _check_age(
        self,
        user_age: Optional[int],
        age_min: Optional[int],
        age_max: Optional[int]
    ) -> Tuple[bool, Optional[str], List[str]]:
        """
        Check age eligibility.
        
        Returns:
            (is_eligible, reason, missing_criteria)
        """
        # If no age criteria, automatically eligible
        if age_min is None and age_max is None:
            return True, None, []
        
        # If user age is missing but criteria exists
        if user_age is None:
            criteria_desc = []
            if age_min is not None and age_max is not None:
                criteria_desc.append(f"Age must be between {age_min} and {age_max}")
            elif age_min is not None:
                criteria_desc.append(f"Age must be at least {age_min}")
            elif age_max is not None:
                criteria_desc.append(f"Age must be at most {age_max}")
            
            return False, None, [f"Age information required: {criteria_desc[0]}"]
        
        # Check age range
        if age_min is not None and user_age < age_min:
            return False, f"Age {user_age} is below minimum requirement of {age_min}", []
        
        if age_max is not None and user_age > age_max:
            return False, f"Age {user_age} exceeds maximum limit of {age_max}", []
        
        # Eligible
        age_range = []
        if age_min is not None:
            age_range.append(f"minimum {age_min}")
        if age_max is not None:
            age_range.append(f"maximum {age_max}")
        
        if age_range:
            return True, f"Age {user_age} meets requirement ({', '.join(age_range)})", []
        
        return True, None, []
    
    def _check_income(
        self,
        user_income_bracket: Optional[str],
        income_max: Optional[int]
    ) -> Tuple[bool, Optional[str], List[str]]:
        """
        Check income eligibility.
        
        Income bracket format: "min-max" (e.g., "100000-300000")
        
        Returns:
            (is_eligible, reason, missing_criteria)
        """
        # If no income criteria, automatically eligible
        if income_max is None:
            return True, None, []
        
        # If user income is missing but criteria exists
        if user_income_bracket is None:
            return False, None, [f"Income information required: Annual income must be at most ₹{income_max:,}"]
        
        # Parse income bracket to get the upper bound
        try:
            # Handle formats like "100000-300000" or "300000+"
            if '-' in user_income_bracket:
                parts = user_income_bracket.split('-')
                user_income_upper = int(parts[1])
            elif '+' in user_income_bracket:
                # For "300000+", use the lower bound as estimate
                user_income_upper = int(user_income_bracket.replace('+', ''))
            else:
                # Single value
                user_income_upper = int(user_income_bracket)
        except (ValueError, IndexError):
            return False, None, [f"Invalid income bracket format: {user_income_bracket}"]
        
        # Check if income is within limit
        if user_income_upper > income_max:
            return False, f"Income ₹{user_income_upper:,} exceeds maximum limit of ₹{income_max:,}", []
        
        return True, f"Income ₹{user_income_upper:,} is within limit of ₹{income_max:,}", []
    
    def _check_occupation(
        self,
        user_occupation: Optional[str],
        eligible_occupations: Optional[List[str]]
    ) -> Tuple[bool, Optional[str], List[str]]:
        """
        Check occupation eligibility.
        
        Returns:
            (is_eligible, reason, missing_criteria)
        """
        # If no occupation criteria, automatically eligible
        if not eligible_occupations:
            return True, None, []
        
        # If user occupation is missing but criteria exists
        if user_occupation is None:
            return False, None, [f"Occupation information required: Must be one of {', '.join(eligible_occupations)}"]
        
        # Check if user occupation matches (case-insensitive)
        user_occupation_lower = user_occupation.lower()
        eligible_occupations_lower = [occ.lower() for occ in eligible_occupations]
        
        if user_occupation_lower in eligible_occupations_lower:
            return True, f"Occupation '{user_occupation}' is eligible", []
        
        return False, f"Occupation '{user_occupation}' is not eligible. Required: {', '.join(eligible_occupations)}", []
    
    def _check_location(
        self,
        user_state: str,
        user_district: str,
        eligible_locations: Optional[List[str]]
    ) -> Tuple[bool, Optional[str], List[str]]:
        """
        Check location-based eligibility.
        
        Location list can contain states or "state/district" combinations.
        Examples: ["Maharashtra", "Karnataka/Bangalore"]
        
        Returns:
            (is_eligible, reason, missing_criteria)
        """
        # If no location criteria, automatically eligible (scheme available everywhere)
        if not eligible_locations:
            return True, None, []
        
        # Check if user state or state/district matches (case-insensitive)
        user_state_lower = user_state.lower()
        user_district_lower = user_district.lower()
        
        for location in eligible_locations:
            location_lower = location.lower()
            
            # Check for state match
            if location_lower == user_state_lower:
                return True, f"Location {user_state} is eligible", []
            
            # Check for state/district match
            if '/' in location_lower:
                parts = location_lower.split('/')
                if len(parts) == 2:
                    loc_state, loc_district = parts[0].strip(), parts[1].strip()
                    if loc_state == user_state_lower and loc_district == user_district_lower:
                        return True, f"Location {user_state}/{user_district} is eligible", []
        
        return False, f"Location {user_state}/{user_district} is not eligible. Available in: {', '.join(eligible_locations)}", []
    
    def _check_education(
        self,
        user_education: Optional[str],
        eligible_education: Optional[List[str]]
    ) -> Tuple[bool, Optional[str], List[str]]:
        """
        Check education level eligibility.
        
        Returns:
            (is_eligible, reason, missing_criteria)
        """
        # If no education criteria, automatically eligible
        if not eligible_education:
            return True, None, []
        
        # If user education is missing but criteria exists
        if user_education is None:
            return False, None, [f"Education information required: Must be one of {', '.join(eligible_education)}"]
        
        # Check if user education matches (case-insensitive)
        user_education_lower = user_education.lower()
        eligible_education_lower = [edu.lower() for edu in eligible_education]
        
        if user_education_lower in eligible_education_lower:
            return True, f"Education level '{user_education}' is eligible", []
        
        return False, f"Education level '{user_education}' is not eligible. Required: {', '.join(eligible_education)}", []
    
    def _check_gender(
        self,
        user_gender: Optional[str],
        required_gender: Optional[str]
    ) -> Tuple[bool, Optional[str], List[str]]:
        """
        Check gender eligibility.
        
        Returns:
            (is_eligible, reason, missing_criteria)
        """
        # If no gender criteria or "any", automatically eligible
        if not required_gender or required_gender.lower() == 'any':
            return True, None, []
        
        # If user gender is missing but criteria exists
        if user_gender is None:
            return False, None, [f"Gender information required: Must be {required_gender}"]
        
        # Check if user gender matches (case-insensitive)
        if user_gender.lower() == required_gender.lower():
            return True, f"Gender '{user_gender}' is eligible", []
        
        return False, f"Gender '{user_gender}' is not eligible. Required: {required_gender}", []
    
    def _calculate_confidence(
        self,
        user_profile: UserProfile,
        missing_criteria: List[str]
    ) -> float:
        """
        Calculate confidence score based on profile completeness.
        
        Confidence is reduced when:
        - User profile has missing optional fields
        - There are missing criteria that couldn't be evaluated
        
        Returns:
            Confidence score between 0.0 and 1.0
        """
        # Start with full confidence
        confidence = 1.0
        
        # Reduce confidence for each missing criterion
        if missing_criteria:
            # Each missing criterion reduces confidence by 0.1
            confidence -= len(missing_criteria) * 0.1
        
        # Ensure confidence stays within bounds
        return max(0.0, min(1.0, confidence))
