"""Eligibility checker for government schemes"""
from typing import List, Dict, Any, Tuple, Optional
from app.models.scheme import Scheme
from app.schemas.scheme import EligibilityResult
from sqlalchemy.orm import Session


class EligibilityChecker:
    """Check user eligibility for government schemes"""
    
    def __init__(self, db: Session):
        """Initialize with database session"""
        self.db = db
    
    def check_eligibility(
        self, 
        user_profile: Dict[str, Any], 
        scheme: Scheme
    ) -> EligibilityResult:
        """
        Check if user meets scheme eligibility criteria
        
        Evaluates: age, income, occupation, location, caste, gender, education, etc.
        
        Args:
            user_profile: Dictionary with user profile data
            scheme: Scheme object with eligibility_criteria
            
        Returns:
            EligibilityResult with is_eligible, missing_criteria, confidence, explanation
        """
        criteria = scheme.eligibility_criteria
        missing_criteria = []
        confidence = 1.0
        
        # Check age criteria
        if 'age_min' in criteria and criteria['age_min'] is not None:
            user_age = user_profile.get('age')
            if user_age is None:
                missing_criteria.append('age')
                confidence *= 0.5
            elif user_age < criteria['age_min']:
                missing_criteria.append(f"age (minimum {criteria['age_min']} required)")
        
        if 'age_max' in criteria and criteria['age_max'] is not None:
            user_age = user_profile.get('age')
            if user_age is None:
                if 'age' not in missing_criteria:
                    missing_criteria.append('age')
                    confidence *= 0.5
            elif user_age > criteria['age_max']:
                missing_criteria.append(f"age (maximum {criteria['age_max']} allowed)")
        
        # Check income criteria
        if 'income_max' in criteria and criteria['income_max'] is not None:
            user_income = user_profile.get('income_bracket')
            if user_income is None:
                missing_criteria.append('income_bracket')
                confidence *= 0.7
            else:
                # Try to extract numeric value from income bracket
                # This is a simplified check - real implementation would need proper parsing
                try:
                    # Assume income_bracket is like "0-50000", "50000-100000", etc.
                    if '-' in str(user_income):
                        income_parts = str(user_income).split('-')
                        max_income = int(income_parts[-1])
                        if max_income > criteria['income_max']:
                            missing_criteria.append(f"income (maximum {criteria['income_max']} required)")
                except (ValueError, IndexError):
                    # If parsing fails, we can't determine eligibility
                    confidence *= 0.7
        
        # Check gender criteria
        if 'gender' in criteria and criteria['gender'] is not None:
            user_gender = user_profile.get('gender')
            if user_gender is None:
                missing_criteria.append('gender')
                confidence *= 0.8
            elif user_gender.lower() != criteria['gender'].lower():
                missing_criteria.append(f"gender ({criteria['gender']} required)")
        
        # Check occupation criteria
        if 'occupation' in criteria and criteria['occupation']:
            user_occupation = user_profile.get('occupation')
            if user_occupation is None:
                missing_criteria.append('occupation')
                confidence *= 0.7
            elif user_occupation not in criteria['occupation']:
                missing_criteria.append(f"occupation (must be one of: {', '.join(criteria['occupation'])})")
        
        # Check education criteria
        if 'education' in criteria and criteria['education']:
            user_education = user_profile.get('education_level')
            if user_education is None:
                missing_criteria.append('education_level')
                confidence *= 0.7
            elif user_education not in criteria['education']:
                missing_criteria.append(f"education (must be one of: {', '.join(criteria['education'])})")
        
        # Check location criteria
        if 'location' in criteria and criteria['location']:
            user_state = user_profile.get('location', {}).get('state') if isinstance(user_profile.get('location'), dict) else user_profile.get('state')
            user_district = user_profile.get('location', {}).get('district') if isinstance(user_profile.get('location'), dict) else user_profile.get('district')
            
            if user_state is None:
                missing_criteria.append('location (state)')
                confidence *= 0.7
            else:
                # Check if user's state or district is in the allowed locations
                location_match = False
                for loc in criteria['location']:
                    if user_state and user_state.lower() in loc.lower():
                        location_match = True
                        break
                    if user_district and user_district.lower() in loc.lower():
                        location_match = True
                        break
                
                if not location_match:
                    missing_criteria.append(f"location (must be in: {', '.join(criteria['location'])})")
        
        # Check caste criteria
        if 'caste' in criteria and criteria['caste']:
            user_caste = user_profile.get('caste')
            if user_caste is None:
                missing_criteria.append('caste')
                confidence *= 0.8
            elif user_caste not in criteria['caste']:
                missing_criteria.append(f"caste (must be one of: {', '.join(criteria['caste'])})")
        
        # Check custom criteria
        if 'custom_criteria' in criteria and criteria['custom_criteria']:
            for key, required_value in criteria['custom_criteria'].items():
                user_value = user_profile.get(key)
                if user_value is None:
                    missing_criteria.append(key)
                    confidence *= 0.7
                elif user_value != required_value:
                    missing_criteria.append(f"{key} (required: {required_value})")
        
        # Determine eligibility
        is_eligible = len(missing_criteria) == 0
        
        # Generate explanation
        explanation = self.explain_eligibility(
            is_eligible=is_eligible,
            missing_criteria=missing_criteria,
            scheme_name=scheme.name,
            language='en'
        )
        
        return EligibilityResult(
            is_eligible=is_eligible,
            missing_criteria=missing_criteria,
            confidence=confidence,
            explanation=explanation
        )
    
    def get_eligible_schemes(
        self, 
        user_profile: Dict[str, Any],
        schemes: Optional[List[Scheme]] = None
    ) -> List[Tuple[Scheme, EligibilityResult]]:
        """
        Get all schemes user is eligible for with eligibility details
        
        Args:
            user_profile: Dictionary with user profile data
            schemes: Optional list of schemes to check (if None, checks all schemes)
            
        Returns:
            List of tuples (Scheme, EligibilityResult) for eligible schemes
        """
        if schemes is None:
            schemes = self.db.query(Scheme).all()
        
        eligible_schemes = []
        
        for scheme in schemes:
            result = self.check_eligibility(user_profile, scheme)
            if result.is_eligible:
                eligible_schemes.append((scheme, result))
        
        return eligible_schemes
    
    def explain_eligibility(
        self, 
        is_eligible: bool,
        missing_criteria: List[str],
        scheme_name: str,
        language: str = 'en'
    ) -> str:
        """
        Generate human-readable explanation of eligibility decision
        
        Args:
            is_eligible: Whether user is eligible
            missing_criteria: List of missing or unmet criteria
            scheme_name: Name of the scheme
            language: Language for explanation (default: 'en')
            
        Returns:
            Human-readable explanation string
        """
        if language == 'hi':
            if is_eligible:
                return f"आप {scheme_name} योजना के लिए पात्र हैं।"
            else:
                criteria_text = ", ".join(missing_criteria)
                return f"आप {scheme_name} योजना के लिए पात्र नहीं हैं। आवश्यक मानदंड: {criteria_text}"
        else:
            # English explanation
            if is_eligible:
                return f"You are eligible for the {scheme_name} scheme."
            else:
                if len(missing_criteria) == 1:
                    return f"You are not eligible for the {scheme_name} scheme. Missing or unmet criteria: {missing_criteria[0]}"
                else:
                    criteria_text = ", ".join(missing_criteria[:-1]) + f" and {missing_criteria[-1]}"
                    return f"You are not eligible for the {scheme_name} scheme. Missing or unmet criteria: {criteria_text}"
