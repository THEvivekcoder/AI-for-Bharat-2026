"""Job Matcher service for matching users with government job postings"""
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.models.skills import JobPosting
from app.schemas.skills import Qualifications, JobPreferences, JobPostingResponse
from app.services.personalization import PersonalizationEngine
from datetime import datetime, timedelta, date
import uuid


class JobMatcher:
    """Service for matching users with government job opportunities"""
    
    # Education level hierarchy for matching
    EDUCATION_LEVELS = {
        "below_10th": 0,
        "10th": 1,
        "12th": 2,
        "diploma": 3,
        "graduate": 4,
        "postgraduate": 5,
        "doctorate": 6
    }
    
    def __init__(self, db: Session):
        """Initialize with database session"""
        self.db = db
        self.personalization = PersonalizationEngine()
    
    def search_jobs(
        self,
        qualifications: Qualifications,
        preferences: JobPreferences,
        limit: int = 10
    ) -> List[JobPostingResponse]:
        """
        Search government jobs matching qualifications and preferences
        
        Args:
            qualifications: User's education, experience, skills
            preferences: Job search preferences (departments, locations)
            limit: Maximum number of results
            
        Returns:
            List of JobPostingResponse with match scores and reasons
        """
        # Start with base query - only active jobs
        query = self.db.query(JobPosting)
        
        # Filter out expired jobs
        today = date.today()
        query = query.filter(
            or_(
                JobPosting.application_deadline >= today,
                JobPosting.application_deadline.is_(None)
            )
        )
        
        # Apply department filter
        if preferences.departments:
            query = query.filter(
                JobPosting.department.in_(preferences.departments)
            )
        
        # Get all matching jobs
        jobs = query.all()
        
        # Filter by location preference and qualifications, then score
        scored_jobs = []
        for job in jobs:
            # Check location match
            if preferences.locations and job.location:
                location_match = self._check_location_match(
                    job.location, preferences.locations
                )
                if not location_match:
                    continue
            
            # Check qualification match
            if not self._check_qualification_match(job, qualifications):
                continue
            
            # Convert job to dict for personalization engine
            job_dict = {
                "job_id": str(job.job_id),
                "title": job.title,
                "department": job.department,
                "description": job.description,
                "qualifications": job.qualifications,
                "location": job.location,
                "application_deadline": job.application_deadline,
                "posted_date": job.posted_date
            }
            
            # Build user profile dict from qualifications and preferences
            user_profile_dict = {
                "education_level": qualifications.education_level,
                "experience_years": qualifications.experience_years,
                "skills": qualifications.skills or [],
                "state": preferences.locations[0] if preferences.locations else None,
                "preferred_departments": preferences.departments or []
            }
            
            qualifications_dict = {
                "education_level": qualifications.education_level,
                "experience_years": qualifications.experience_years,
                "skills": qualifications.skills or []
            }
            
            # Get personalized score and explanation
            score, explanation = self.personalization.score_job_relevance(
                job_dict,
                user_profile_dict,
                qualifications_dict
            )
            
            # Convert to response schema
            job_response = JobPostingResponse(
                job_id=str(job.job_id),
                title=job.title,
                department=job.department,
                description=job.description,
                qualifications=job.qualifications,
                location=job.location,
                application_deadline=job.application_deadline,
                application_url=job.application_url,
                posted_date=job.posted_date,
                created_at=job.created_at,
                updated_at=job.updated_at,
                match_score=score,
                match_reason=explanation
            )
            
            scored_jobs.append((score, job_response))
        
        # Sort by match score (descending)
        scored_jobs.sort(key=lambda x: x[0], reverse=True)
        
        # Return top N jobs
        return [job for _, job in scored_jobs[:limit]]
    
    def _check_location_match(
        self,
        job_location: Dict[str, Any],
        preferred_locations: List[str]
    ) -> bool:
        """
        Check if job location matches user preferences
        
        Args:
            job_location: Job location data (state, district, etc.)
            preferred_locations: List of preferred states/districts
            
        Returns:
            True if location matches, False otherwise
        """
        if not job_location:
            return True  # No location restriction
        
        job_state = job_location.get("state", "").lower()
        job_district = job_location.get("district", "").lower()
        job_locations = job_location.get("locations", [])
        
        # Check if any preferred location matches
        for pref_loc in preferred_locations:
            pref_loc_lower = pref_loc.lower()
            
            # Check state match
            if job_state and pref_loc_lower in job_state:
                return True
            
            # Check district match
            if job_district and pref_loc_lower in job_district:
                return True
            
            # Check multiple locations
            if job_locations:
                for loc in job_locations:
                    if isinstance(loc, str) and pref_loc_lower in loc.lower():
                        return True
                    elif isinstance(loc, dict):
                        loc_state = loc.get("state", "").lower()
                        loc_district = loc.get("district", "").lower()
                        if pref_loc_lower in loc_state or pref_loc_lower in loc_district:
                            return True
        
        return False
    
    def _check_qualification_match(
        self,
        job: JobPosting,
        qualifications: Qualifications
    ) -> bool:
        """
        Check if user qualifications meet job requirements
        
        Args:
            job: JobPosting to check
            qualifications: User's qualifications
            
        Returns:
            True if qualifications match (within one level), False otherwise
        """
        if not job.qualifications:
            return True  # No specific requirements
        
        required_education = job.qualifications.get("education_level")
        if not required_education:
            return True
        
        # Get user's education level
        user_level = self.EDUCATION_LEVELS.get(
            qualifications.education_level.lower() if qualifications.education_level else "below_10th",
            0
        )
        
        # Get required education level
        required_level = self.EDUCATION_LEVELS.get(
            required_education.lower(),
            0
        )
        
        # Allow if user's education is within one level of requirement
        # (one level below or any level above)
        return user_level >= required_level - 1
    
    def _calculate_match_score(
        self,
        job: JobPosting,
        qualifications: Qualifications,
        preferences: JobPreferences
    ) -> Tuple[float, str]:
        """
        Calculate match score for a job based on qualifications and preferences
        
        Args:
            job: JobPosting to score
            qualifications: User's qualifications
            preferences: User's preferences
            
        Returns:
            Tuple of (score, reason) where score is 0-1 and reason explains the match
        """
        score = 0.0
        reasons = []
        
        # Education level match (weight: 0.3)
        if job.qualifications and qualifications.education_level:
            required_education = job.qualifications.get("education_level", "").lower()
            user_education = qualifications.education_level.lower()
            
            user_level = self.EDUCATION_LEVELS.get(user_education, 0)
            required_level = self.EDUCATION_LEVELS.get(required_education, 0)
            
            if user_level >= required_level:
                if user_level == required_level:
                    score += 0.3
                    reasons.append("exactly matches your education level")
                else:
                    score += 0.25
                    reasons.append("your education exceeds requirements")
            elif user_level == required_level - 1:
                score += 0.15
                reasons.append("you're close to the education requirement")
        
        # Experience match (weight: 0.25)
        if job.qualifications and qualifications.experience_years is not None:
            required_experience = job.qualifications.get("experience_years", 0)
            if qualifications.experience_years >= required_experience:
                score += 0.25
                reasons.append(f"you meet the {required_experience} years experience requirement")
            elif qualifications.experience_years >= required_experience - 1:
                score += 0.15
                reasons.append("you're close to the experience requirement")
        
        # Skills match (weight: 0.2)
        if job.qualifications and qualifications.skills:
            required_skills = job.qualifications.get("skills", [])
            if required_skills:
                matching_skills = set(
                    skill.lower() for skill in qualifications.skills
                ).intersection(
                    set(skill.lower() for skill in required_skills)
                )
                
                if matching_skills:
                    skill_match_ratio = len(matching_skills) / len(required_skills)
                    score += 0.2 * skill_match_ratio
                    reasons.append(f"you have {len(matching_skills)} of the required skills")
        
        # Department preference match (weight: 0.15)
        if preferences.departments and job.department:
            if job.department in preferences.departments:
                score += 0.15
                reasons.append("in your preferred department")
        
        # Location preference match (weight: 0.1)
        if preferences.locations and job.location:
            if self._check_location_match(job.location, preferences.locations):
                score += 0.1
                reasons.append("in your preferred location")
        
        # Deadline urgency (small bonus for jobs closing soon)
        if job.application_deadline:
            days_until_deadline = (job.application_deadline - date.today()).days
            if 0 < days_until_deadline <= 7:
                score += 0.05
                reasons.append(f"deadline in {days_until_deadline} days")
            elif 7 < days_until_deadline <= 30:
                score += 0.03
        
        # Recent posting bonus
        if job.posted_date:
            days_since_posted = (date.today() - job.posted_date).days
            if days_since_posted <= 7:
                score += 0.02
                reasons.append("recently posted")
        
        # If no specific matches, give base score
        if score == 0:
            score = 0.1
            reasons.append("government job opportunity")
        
        # Construct reason string
        reason = "This job " + ", ".join(reasons) if reasons else "Government job opportunity"
        
        return min(score, 1.0), reason
    
    def get_job_alerts(
        self,
        user_profile: Dict[str, Any],
        qualifications: Qualifications,
        preferences: JobPreferences,
        days_back: int = 30
    ) -> List[JobPostingResponse]:
        """
        Get new job postings matching user profile (posted in last N days)
        
        Args:
            user_profile: User profile data
            qualifications: User's qualifications
            preferences: Job search preferences
            days_back: Look for jobs posted in last N days
            
        Returns:
            List of JobPostingResponse for recent matching jobs
        """
        # Calculate cutoff date
        cutoff_date = date.today() - timedelta(days=days_back)
        
        # Query recent jobs
        query = self.db.query(JobPosting)
        
        # Filter by posted date
        query = query.filter(
            or_(
                JobPosting.posted_date >= cutoff_date,
                JobPosting.created_at >= datetime.combine(cutoff_date, datetime.min.time())
            )
        )
        
        # Filter out expired jobs
        today = date.today()
        query = query.filter(
            or_(
                JobPosting.application_deadline >= today,
                JobPosting.application_deadline.is_(None)
            )
        )
        
        jobs = query.all()
        
        # Filter and score jobs
        scored_jobs = []
        for job in jobs:
            # Check location match
            if preferences.locations and job.location:
                location_match = self._check_location_match(
                    job.location, preferences.locations
                )
                if not location_match:
                    continue
            
            # Check qualification match
            if not self._check_qualification_match(job, qualifications):
                continue
            
            # Convert job to dict for personalization engine
            job_dict = {
                "job_id": str(job.job_id),
                "title": job.title,
                "department": job.department,
                "description": job.description,
                "qualifications": job.qualifications,
                "location": job.location,
                "application_deadline": job.application_deadline,
                "posted_date": job.posted_date
            }
            
            # Build user profile dict
            user_profile_dict = {
                "education_level": qualifications.education_level,
                "experience_years": qualifications.experience_years,
                "skills": qualifications.skills or [],
                "state": preferences.locations[0] if preferences.locations else user_profile.get("state"),
                "preferred_departments": preferences.departments or []
            }
            
            qualifications_dict = {
                "education_level": qualifications.education_level,
                "experience_years": qualifications.experience_years,
                "skills": qualifications.skills or []
            }
            
            # Get personalized score and explanation
            score, explanation = self.personalization.score_job_relevance(
                job_dict,
                user_profile_dict,
                qualifications_dict
            )
            
            # Convert to response schema
            job_response = JobPostingResponse(
                job_id=str(job.job_id),
                title=job.title,
                department=job.department,
                description=job.description,
                qualifications=job.qualifications,
                location=job.location,
                application_deadline=job.application_deadline,
                application_url=job.application_url,
                posted_date=job.posted_date,
                created_at=job.created_at,
                updated_at=job.updated_at,
                match_score=score,
                match_reason=explanation
            )
            
            scored_jobs.append((score, job_response))
        
        # Sort by match score (descending)
        scored_jobs.sort(key=lambda x: x[0], reverse=True)
        
        return [job for _, job in scored_jobs]
    
    def get_job_by_id(self, job_id: str) -> Optional[JobPosting]:
        """
        Get detailed information about a job posting
        
        Args:
            job_id: UUID of the job
            
        Returns:
            JobPosting object or None if not found
        """
        try:
            job_uuid = uuid.UUID(job_id)
        except ValueError:
            return None
        
        return self.db.query(JobPosting).filter(
            JobPosting.job_id == job_uuid
        ).first()
