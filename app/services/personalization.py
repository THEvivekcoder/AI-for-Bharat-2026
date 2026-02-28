"""Personalization and recommendation scoring service"""
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime


class PersonalizationEngine:
    """
    Service for calculating personalized relevance scores for schemes, jobs, and skill programs.
    Implements requirement 8.2: Personalized Recommendations
    """
    
    # Category weights for different recommendation types
    SCHEME_WEIGHTS = {
        "occupation_match": 0.25,
        "location_match": 0.20,
        "income_match": 0.20,
        "age_match": 0.15,
        "education_match": 0.10,
        "category_preference": 0.10
    }
    
    JOB_WEIGHTS = {
        "education_match": 0.30,
        "experience_match": 0.25,
        "skills_match": 0.20,
        "location_match": 0.15,
        "department_preference": 0.10
    }
    
    SKILL_WEIGHTS = {
        "interest_match": 0.35,
        "career_goal_match": 0.25,
        "skill_building": 0.20,
        "location_match": 0.10,
        "education_match": 0.10
    }
    
    def score_scheme_relevance(
        self,
        scheme: Dict[str, Any],
        user_profile: Dict[str, Any]
    ) -> Tuple[float, str]:
        """
        Calculate personalized relevance score for a scheme
        
        Args:
            scheme: Scheme data with eligibility_criteria, category, state, etc.
            user_profile: User profile with occupation, location, income, age, education
            
        Returns:
            Tuple of (score, explanation) where score is 0-1
        """
        score = 0.0
        reasons = []
        
        eligibility = scheme.get("eligibility_criteria", {})
        
        # Occupation match
        user_occupation = user_profile.get("occupation", "").lower()
        eligible_occupations = eligibility.get("occupation", [])
        
        if eligible_occupations:
            if any(occ.lower() in user_occupation or user_occupation in occ.lower() 
                   for occ in eligible_occupations):
                score += self.SCHEME_WEIGHTS["occupation_match"]
                reasons.append(f"designed for {user_occupation}s")
            else:
                # Penalize mismatch - scheme has occupation criteria but user doesn't match
                score += self.SCHEME_WEIGHTS["occupation_match"] * 0.2
        
        # Location match
        user_state = user_profile.get("state", "").lower()
        scheme_state = scheme.get("state", "").lower() if scheme.get("state") else None
        eligible_locations = eligibility.get("location", [])
        
        if scheme_state is None:
            # Central scheme - available everywhere
            score += self.SCHEME_WEIGHTS["location_match"] * 0.8
            reasons.append("available nationwide")
        elif scheme_state == user_state:
            score += self.SCHEME_WEIGHTS["location_match"]
            reasons.append(f"available in {user_profile.get('state', 'your state')}")
        elif eligible_locations and any(
            loc.lower() == user_state or user_state in loc.lower()
            for loc in eligible_locations
        ):
            score += self.SCHEME_WEIGHTS["location_match"]
            reasons.append("available in your location")
        else:
            # State-specific scheme but user is in different state
            if scheme_state:
                score += self.SCHEME_WEIGHTS["location_match"] * 0.1
        
        # Income match
        user_income = user_profile.get("income_bracket")
        max_income = eligibility.get("income_max")
        
        if max_income and user_income:
            # Parse income bracket (e.g., "0-50000", "50000-100000")
            try:
                if "-" in user_income:
                    income_parts = user_income.split("-")
                    user_income_value = int(income_parts[1])
                else:
                    user_income_value = int(user_income)
                
                if user_income_value <= max_income:
                    score += self.SCHEME_WEIGHTS["income_match"]
                    reasons.append("matches your income level")
                else:
                    # User income exceeds limit
                    score += self.SCHEME_WEIGHTS["income_match"] * 0.1
            except (ValueError, IndexError):
                pass
        
        # Age match
        user_age = user_profile.get("age")
        min_age = eligibility.get("age_min")
        max_age = eligibility.get("age_max")
        
        if user_age:
            age_matches = True
            if min_age and user_age < min_age:
                age_matches = False
            if max_age and user_age > max_age:
                age_matches = False
            
            if age_matches:
                score += self.SCHEME_WEIGHTS["age_match"]
                if min_age or max_age:
                    reasons.append("suitable for your age group")
            else:
                # Age doesn't match criteria
                score += self.SCHEME_WEIGHTS["age_match"] * 0.1
        
        # Education match - enhanced to differentiate education levels
        user_education = user_profile.get("education_level", "").lower()
        eligible_education = eligibility.get("education", [])
        
        # Education level hierarchy for better matching
        education_levels = {
            "below_10th": 0,
            "10th": 1,
            "12th": 2,
            "diploma": 3,
            "graduate": 4,
            "postgraduate": 5,
            "doctorate": 6
        }
        
        if eligible_education:
            # Check if user's education matches any eligible level
            user_level = education_levels.get(user_education, 0)
            eligible_levels = [education_levels.get(edu.lower(), 0) for edu in eligible_education]
            
            if user_level in eligible_levels:
                # Exact match
                score += self.SCHEME_WEIGHTS["education_match"]
                reasons.append("matches your education level")
            elif user_level > max(eligible_levels):
                # User is overqualified - partial credit
                score += self.SCHEME_WEIGHTS["education_match"] * 0.7
                reasons.append("your education exceeds requirements")
            elif user_level < min(eligible_levels):
                # User is underqualified - small credit
                score += self.SCHEME_WEIGHTS["education_match"] * 0.2
            else:
                # User is within range but not exact match
                score += self.SCHEME_WEIGHTS["education_match"] * 0.5
        
        # Category preference (if user has shown interest in this category)
        # This would be based on interaction history - for now, give small base score
        scheme_category = scheme.get("category", "").lower()
        if scheme_category:
            score += self.SCHEME_WEIGHTS["category_preference"] * 0.5
        
        # Construct explanation
        if reasons:
            explanation = f"Recommended because it {', '.join(reasons)}"
        else:
            explanation = "This scheme may be relevant to you"
        
        return min(score, 1.0), explanation
    
    def score_job_relevance(
        self,
        job: Dict[str, Any],
        user_profile: Dict[str, Any],
        qualifications: Optional[Dict[str, Any]] = None
    ) -> Tuple[float, str]:
        """
        Calculate personalized relevance score for a job posting
        
        Args:
            job: Job posting data with qualifications, location, department
            user_profile: User profile with education, location, preferences
            qualifications: Optional explicit qualifications (education, experience, skills)
            
        Returns:
            Tuple of (score, explanation) where score is 0-1
        """
        score = 0.0
        reasons = []
        
        # Use qualifications from parameter or extract from user_profile
        if qualifications is None:
            qualifications = {
                "education_level": user_profile.get("education_level"),
                "experience_years": user_profile.get("experience_years", 0),
                "skills": user_profile.get("skills", [])
            }
        
        job_qualifications = job.get("qualifications", {})
        
        # Education level hierarchy
        education_levels = {
            "below_10th": 0,
            "10th": 1,
            "12th": 2,
            "diploma": 3,
            "graduate": 4,
            "postgraduate": 5,
            "doctorate": 6
        }
        
        # Education match
        required_education = job_qualifications.get("education_level", "").lower()
        user_education = qualifications.get("education_level", "").lower()
        
        if required_education and user_education:
            user_level = education_levels.get(user_education, 0)
            required_level = education_levels.get(required_education, 0)
            
            if user_level >= required_level:
                if user_level == required_level:
                    score += self.JOB_WEIGHTS["education_match"]
                    reasons.append("matches your education level")
                else:
                    score += self.JOB_WEIGHTS["education_match"] * 0.9
                    reasons.append("your education exceeds requirements")
            elif user_level == required_level - 1:
                score += self.JOB_WEIGHTS["education_match"] * 0.5
                reasons.append("close to education requirement")
        
        # Experience match
        required_experience = job_qualifications.get("experience_years", 0)
        user_experience = qualifications.get("experience_years", 0)
        
        if user_experience >= required_experience:
            score += self.JOB_WEIGHTS["experience_match"]
            reasons.append(f"you meet the {required_experience} years experience requirement")
        elif user_experience >= required_experience - 1:
            score += self.JOB_WEIGHTS["experience_match"] * 0.6
            reasons.append("close to experience requirement")
        
        # Skills match
        required_skills = job_qualifications.get("skills", [])
        user_skills = qualifications.get("skills", [])
        
        if required_skills and user_skills:
            matching_skills = set(
                skill.lower() for skill in user_skills
            ).intersection(
                set(skill.lower() for skill in required_skills)
            )
            
            if matching_skills:
                skill_ratio = len(matching_skills) / len(required_skills)
                score += self.JOB_WEIGHTS["skills_match"] * skill_ratio
                reasons.append(f"you have {len(matching_skills)} of {len(required_skills)} required skills")
        
        # Location match
        user_state = user_profile.get("state", "").lower()
        user_district = user_profile.get("district", "").lower()
        job_location = job.get("location", {})
        
        if job_location:
            job_state = job_location.get("state", "").lower()
            job_district = job_location.get("district", "").lower()
            
            if job_state == user_state:
                if job_district and job_district == user_district:
                    score += self.JOB_WEIGHTS["location_match"]
                    reasons.append("in your district")
                else:
                    score += self.JOB_WEIGHTS["location_match"] * 0.7
                    reasons.append("in your state")
        
        # Department preference (if user has preferences)
        preferred_departments = user_profile.get("preferred_departments", [])
        job_department = job.get("department", "")
        
        if preferred_departments and job_department:
            if job_department in preferred_departments:
                score += self.JOB_WEIGHTS["department_preference"]
                reasons.append("in your preferred department")
        
        # Construct explanation
        if reasons:
            explanation = f"Recommended because {', '.join(reasons)}"
        else:
            explanation = "This job may be suitable for you"
        
        return min(score, 1.0), explanation
    
    def score_skill_program_relevance(
        self,
        program: Dict[str, Any],
        user_profile: Dict[str, Any],
        preferences: Optional[Dict[str, Any]] = None
    ) -> Tuple[float, str]:
        """
        Calculate personalized relevance score for a skill program
        
        Args:
            program: Skill program data with category, description, location
            user_profile: User profile with education, occupation, location
            preferences: Optional preferences with interests, career_goals, current_skills
            
        Returns:
            Tuple of (score, explanation) where score is 0-1
        """
        score = 0.0
        reasons = []
        
        # Use preferences from parameter or extract from user_profile
        if preferences is None:
            preferences = {
                "interests": user_profile.get("interests", []),
                "career_goals": user_profile.get("career_goals", []),
                "current_skills": user_profile.get("skills", [])
            }
        
        program_category = program.get("category", "").lower()
        program_description = program.get("description", "").lower()
        program_name = program.get("name", "").lower()
        
        # Interest match - enhanced to count number of matching interests
        interests = preferences.get("interests", [])
        if interests:
            matching_interests = [
                interest for interest in interests
                if (interest.lower() in program_category or
                    interest.lower() in program_description or
                    interest.lower() in program_name)
            ]
            
            if matching_interests:
                # Score based on proportion of interests that match
                match_ratio = len(matching_interests) / len(interests)
                score += self.SKILL_WEIGHTS["interest_match"] * match_ratio
                reasons.append(f"matches {len(matching_interests)} of your interests")
            else:
                # No interests match - give minimal score
                score += self.SKILL_WEIGHTS["interest_match"] * 0.1
        
        # Career goal match
        career_goals = preferences.get("career_goals", [])
        if career_goals:
            goal_match = any(
                goal.lower() in program_category or
                goal.lower() in program_description or
                goal.lower() in program_name
                for goal in career_goals
            )
            if goal_match:
                score += self.SKILL_WEIGHTS["career_goal_match"]
                reasons.append("aligns with your career goals")
        
        # Skill building (programs that build on current skills)
        current_skills = preferences.get("current_skills", [])
        if current_skills:
            skill_match = any(
                skill.lower() in program_category or
                skill.lower() in program_description or
                skill.lower() in program_name
                for skill in current_skills
            )
            if skill_match:
                score += self.SKILL_WEIGHTS["skill_building"]
                reasons.append("builds on your current skills")
        
        # Location match
        user_state = user_profile.get("state", "").lower()
        user_district = user_profile.get("district", "").lower()
        program_state = program.get("state", "").lower() if program.get("state") else None
        program_district = program.get("district", "").lower() if program.get("district") else None
        program_mode = program.get("mode", "").lower()
        
        if program_mode == "online":
            score += self.SKILL_WEIGHTS["location_match"]
            reasons.append("available online")
        elif program_state == user_state:
            if program_district and program_district == user_district:
                score += self.SKILL_WEIGHTS["location_match"]
                reasons.append("available in your district")
            else:
                score += self.SKILL_WEIGHTS["location_match"] * 0.7
                reasons.append("available in your state")
        elif program_state and program_state != user_state:
            # Program in different state - give minimal score
            score += self.SKILL_WEIGHTS["location_match"] * 0.2
        
        # Education match
        user_education = user_profile.get("education_level", "").lower()
        program_eligibility = program.get("eligibility_criteria", {})
        eligible_education = program_eligibility.get("education", [])
        
        if eligible_education:
            if any(edu.lower() in user_education or user_education in edu.lower()
                   for edu in eligible_education):
                score += self.SKILL_WEIGHTS["education_match"]
                reasons.append("suitable for your education level")
        
        # Construct explanation
        if reasons:
            explanation = f"Recommended because it {', '.join(reasons)}"
        else:
            explanation = "This program may be relevant to you"
        
        return min(score, 1.0), explanation
    
    def rank_recommendations(
        self,
        items: List[Dict[str, Any]],
        user_profile: Dict[str, Any],
        recommendation_type: str,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Dict[str, Any], float, str]]:
        """
        Rank a list of items (schemes, jobs, or programs) by personalized relevance
        
        Args:
            items: List of items to rank
            user_profile: User profile for personalization
            recommendation_type: One of "scheme", "job", "skill_program"
            additional_params: Optional additional parameters (qualifications, preferences)
            
        Returns:
            List of tuples (item, score, explanation) sorted by score descending
        """
        scored_items = []
        
        for item in items:
            if recommendation_type == "scheme":
                score, explanation = self.score_scheme_relevance(item, user_profile)
            elif recommendation_type == "job":
                qualifications = additional_params.get("qualifications") if additional_params else None
                score, explanation = self.score_job_relevance(item, user_profile, qualifications)
            elif recommendation_type == "skill_program":
                preferences = additional_params.get("preferences") if additional_params else None
                score, explanation = self.score_skill_program_relevance(item, user_profile, preferences)
            else:
                raise ValueError(f"Unknown recommendation type: {recommendation_type}")
            
            scored_items.append((item, score, explanation))
        
        # Sort by score descending
        scored_items.sort(key=lambda x: x[1], reverse=True)
        
        return scored_items

    
    def generate_detailed_explanation(
        self,
        item: Dict[str, Any],
        user_profile: Dict[str, Any],
        recommendation_type: str,
        score: float,
        base_explanation: str
    ) -> str:
        """
        Generate a detailed explanation for a recommendation
        
        Args:
            item: The recommended item (scheme, job, or program)
            user_profile: User profile data
            recommendation_type: One of "scheme", "job", "skill_program"
            score: Relevance score
            base_explanation: Base explanation from scoring
            
        Returns:
            Detailed explanation string
        """
        # Add relevance level description
        if score >= 0.8:
            relevance = "Highly recommended"
        elif score >= 0.6:
            relevance = "Good match"
        elif score >= 0.4:
            relevance = "Moderate match"
        else:
            relevance = "May be relevant"
        
        # Build detailed explanation
        explanation_parts = [f"{relevance}. {base_explanation}"]
        
        # Add profile-specific context
        if recommendation_type == "scheme":
            if user_profile.get("occupation"):
                explanation_parts.append(
                    f"Based on your occupation as {user_profile['occupation']}"
                )
            if user_profile.get("state"):
                explanation_parts.append(
                    f"and your location in {user_profile['state']}"
                )
        
        elif recommendation_type == "job":
            if user_profile.get("education_level"):
                explanation_parts.append(
                    f"Your {user_profile['education_level']} education qualifies you for this position"
                )
            if user_profile.get("experience_years"):
                explanation_parts.append(
                    f"with {user_profile['experience_years']} years of experience"
                )
        
        elif recommendation_type == "skill_program":
            interests = user_profile.get("interests", [])
            if interests:
                explanation_parts.append(
                    f"Aligns with your interests in {', '.join(interests[:2])}"
                )
        
        return ". ".join(explanation_parts) + "."
