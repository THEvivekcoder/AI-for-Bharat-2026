"""Skills Matcher service for matching users with skill programs"""
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.models.skills import SkillProgram
from app.schemas.skills import SkillPreferences, SkillProgramResponse
from app.services.personalization import PersonalizationEngine
import uuid


class SkillsMatcher:
    """Service for matching users with relevant skill development programs"""
    
    def __init__(self, db: Session):
        """Initialize with database session"""
        self.db = db
        self.personalization = PersonalizationEngine()
    
    def match_programs(
        self,
        user_profile: Dict[str, Any],
        preferences: SkillPreferences,
        limit: int = 10
    ) -> List[SkillProgramResponse]:
        """
        Match user with relevant skill programs based on profile and preferences
        
        Args:
            user_profile: User profile data (education, occupation, location, etc.)
            preferences: User preferences for skill programs
            limit: Maximum number of results
            
        Returns:
            List of SkillProgramResponse with relevance scores and match reasons
        """
        # Start with base query
        query = self.db.query(SkillProgram)
        
        # Apply location filters
        if preferences.location_state:
            query = query.filter(
                or_(
                    SkillProgram.state == preferences.location_state,
                    SkillProgram.mode == "online"  # Online programs available everywhere
                )
            )
        
        if preferences.location_district and preferences.location_state:
            query = query.filter(
                or_(
                    and_(
                        SkillProgram.state == preferences.location_state,
                        SkillProgram.district == preferences.location_district
                    ),
                    SkillProgram.mode == "online"
                )
            )
        
        # Apply cost filter
        if preferences.max_cost is not None:
            query = query.filter(
                or_(
                    SkillProgram.cost <= preferences.max_cost,
                    SkillProgram.cost.is_(None)  # Free programs
                )
            )
        
        # Apply duration filter
        if preferences.max_duration_weeks:
            query = query.filter(
                or_(
                    SkillProgram.duration_weeks <= preferences.max_duration_weeks,
                    SkillProgram.duration_weeks.is_(None)
                )
            )
        
        # Apply mode filter
        if preferences.preferred_mode:
            query = query.filter(SkillProgram.mode == preferences.preferred_mode)
        
        # Get all matching programs
        programs = query.all()
        
        # Score and rank programs using PersonalizationEngine
        scored_programs = []
        for program in programs:
            # Convert program to dict for personalization engine
            program_dict = {
                "program_id": str(program.program_id),
                "name": program.name,
                "category": program.category,
                "description": program.description,
                "state": program.state,
                "district": program.district,
                "mode": program.mode,
                "eligibility_criteria": program.eligibility_criteria,
                "certification": program.certification,
                "placement_support": program.placement_support
            }
            
            # Get personalized score and explanation
            preferences_dict = {
                "interests": preferences.interests or [],
                "career_goals": preferences.career_goals or [],
                "current_skills": preferences.current_skills or []
            }
            
            score, explanation = self.personalization.score_skill_program_relevance(
                program_dict,
                user_profile,
                preferences_dict
            )
            
            # Legacy scoring for backward compatibility check
            legacy_score, legacy_reason, has_relevance_match = self._calculate_relevance_score(
                program, user_profile, preferences
            )
            
            # Only include programs that match interests, skills, or career goals
            # This ensures Property 10: all returned programs must be relevant
            if not has_relevance_match:
                continue
            
            # Use personalization engine score and explanation
            program_response = SkillProgramResponse(
                program_id=str(program.program_id),
                name=program.name,
                provider=program.provider,
                category=program.category,
                description=program.description,
                duration_weeks=program.duration_weeks,
                cost=program.cost,
                state=program.state,
                district=program.district,
                mode=program.mode,
                eligibility_criteria=program.eligibility_criteria,
                certification=program.certification,
                placement_support=program.placement_support,
                registration_url=program.registration_url,
                contact=program.contact,
                created_at=program.created_at,
                updated_at=program.updated_at,
                relevance_score=score,
                match_reason=explanation
            )
            
            scored_programs.append((score, program_response))
        
        # Sort by relevance score (descending)
        scored_programs.sort(key=lambda x: x[0], reverse=True)
        
        # Return top N programs
        return [prog for _, prog in scored_programs[:limit]]
    
    def _calculate_relevance_score(
        self,
        program: SkillProgram,
        user_profile: Dict[str, Any],
        preferences: SkillPreferences
    ) -> Tuple[float, str, bool]:
        """
        Calculate relevance score for a program based on user profile and preferences
        
        Args:
            program: SkillProgram to score
            user_profile: User profile data
            preferences: User preferences
            
        Returns:
            Tuple of (score, reason, has_relevance_match) where:
            - score is 0-1
            - reason explains the match
            - has_relevance_match indicates if program matches interests/skills/goals
        """
        score = 0.0
        reasons = []
        has_relevance_match = False  # Track if program matches core criteria
        
        # Interest matching (highest weight: 0.4)
        if preferences.interests:
            interest_match = any(
                interest.lower() in program.category.lower() or
                (program.description and interest.lower() in program.description.lower())
                for interest in preferences.interests
            )
            if interest_match:
                score += 0.4
                reasons.append(f"matches your interest in {program.category}")
                has_relevance_match = True
        
        # Career goals matching (weight: 0.3)
        if preferences.career_goals:
            career_match = any(
                goal.lower() in program.category.lower() or
                (program.description and goal.lower() in program.description.lower())
                for goal in preferences.career_goals
            )
            if career_match:
                score += 0.3
                reasons.append("aligns with your career goals")
                has_relevance_match = True
        
        # Current skills building (weight: 0.2)
        if preferences.current_skills:
            # Programs that build on current skills
            skill_match = any(
                skill.lower() in program.category.lower() or
                (program.description and skill.lower() in program.description.lower())
                for skill in preferences.current_skills
            )
            if skill_match:
                score += 0.2
                reasons.append("builds on your current skills")
                has_relevance_match = True
        
        # Certification bonus (weight: 0.05) - only if there's already a relevance match
        if has_relevance_match and program.certification:
            score += 0.05
            reasons.append("provides certification")
        
        # Placement support bonus (weight: 0.05) - only if there's already a relevance match
        if has_relevance_match and program.placement_support:
            score += 0.05
            reasons.append("offers placement support")
        
        # Location convenience (already filtered, but add small bonus for exact match)
        # Only add location bonus if there's already a relevance match
        if has_relevance_match:
            user_state = user_profile.get("state") or preferences.location_state
            user_district = user_profile.get("district") or preferences.location_district
            
            if program.mode == "online":
                score += 0.02
                reasons.append("available online")
            elif program.state == user_state:
                if program.district == user_district:
                    score += 0.03
                    reasons.append("available in your district")
                else:
                    score += 0.02
                    reasons.append("available in your state")
        
        # Education level matching - only if there's already a relevance match
        if has_relevance_match:
            education_level = user_profile.get("education_level")
            if education_level and program.eligibility_criteria:
                required_education = program.eligibility_criteria.get("education")
                if required_education and education_level in required_education:
                    score += 0.05
                    reasons.append("matches your education level")
        
        # Construct reason string
        reason = "This program " + ", ".join(reasons) if reasons else "No match found"
        
        return min(score, 1.0), reason, has_relevance_match
    
    def get_program_details(self, program_id: str) -> Optional[SkillProgram]:
        """
        Get detailed information about a skill program
        
        Args:
            program_id: UUID of the program
            
        Returns:
            SkillProgram object or None if not found
        """
        try:
            program_uuid = uuid.UUID(program_id)
        except ValueError:
            return None
        
        return self.db.query(SkillProgram).filter(
            SkillProgram.program_id == program_uuid
        ).first()
    
    def get_all_programs(
        self,
        category: Optional[str] = None,
        state: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[SkillProgram]:
        """
        Get all skill programs with optional filters
        
        Args:
            category: Optional category filter
            state: Optional state filter
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of SkillProgram objects
        """
        query = self.db.query(SkillProgram)
        
        if category:
            query = query.filter(SkillProgram.category == category)
        
        if state:
            query = query.filter(
                or_(
                    SkillProgram.state == state,
                    SkillProgram.mode == "online"
                )
            )
        
        query = query.order_by(SkillProgram.created_at.desc())
        query = query.limit(limit).offset(offset)
        
        return query.all()
