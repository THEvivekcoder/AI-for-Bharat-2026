"""Skills and Employment service API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.services.skills_matcher import SkillsMatcher
from app.services.job_matcher import JobMatcher
from app.schemas.skills import (
    SkillProgramResponse,
    SkillMatchRequest,
    JobPostingResponse,
    JobSearchRequest,
    JobAlertsRequest
)

router = APIRouter(prefix="/api", tags=["skills"])


@router.get("/skills", response_model=List[SkillProgramResponse])
async def list_skill_programs(
    category: Optional[str] = Query(None, description="Filter by category"),
    state: Optional[str] = Query(None, description="Filter by state"),
    district: Optional[str] = Query(None, description="Filter by district"),
    mode: Optional[str] = Query(None, description="Filter by mode (in-person, online, hybrid)"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db)
):
    """
    List skill development programs with optional filters
    
    - **category**: Filter by program category (technical, vocational, digital, entrepreneurship)
    - **state**: Filter by state (includes online programs)
    - **district**: Filter by district
    - **mode**: Filter by delivery mode (in-person, online, hybrid)
    - **limit**: Maximum number of results (default: 100, max: 500)
    - **offset**: Offset for pagination (default: 0)
    """
    matcher = SkillsMatcher(db)
    
    programs = matcher.get_all_programs(
        category=category,
        state=state,
        limit=limit,
        offset=offset
    )
    
    # Convert to response models
    return [
        SkillProgramResponse(
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
            updated_at=program.updated_at
        )
        for program in programs
    ]


@router.post("/skills/match", response_model=List[SkillProgramResponse])
async def match_skill_programs(
    request: SkillMatchRequest,
    db: Session = Depends(get_db)
):
    """
    Get personalized skill program recommendations
    
    - **user_profile**: User profile data (education, occupation, location, etc.)
    - **preferences**: User preferences for skill programs (interests, career goals, budget, etc.)
    - **limit**: Maximum number of results (default: 10, max: 50)
    
    Returns programs ranked by relevance with match scores and explanations.
    """
    matcher = SkillsMatcher(db)
    
    try:
        matched_programs = matcher.match_programs(
            user_profile=request.user_profile,
            preferences=request.preferences,
            limit=request.limit
        )
        
        return matched_programs
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "MATCHING_ERROR",
                "message": "Failed to match skill programs",
                "details": str(e)
            }
        )


@router.get("/jobs", response_model=List[JobPostingResponse])
async def search_jobs(
    title: Optional[str] = Query(None, description="Search in job title"),
    department: Optional[str] = Query(None, description="Filter by department"),
    state: Optional[str] = Query(None, description="Filter by state"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db)
):
    """
    Search government job postings with optional filters
    
    - **title**: Search in job title
    - **department**: Filter by government department
    - **state**: Filter by state/location
    - **limit**: Maximum number of results (default: 100, max: 500)
    - **offset**: Offset for pagination (default: 0)
    """
    from app.models.skills import JobPosting
    from datetime import date
    from sqlalchemy import or_
    
    query = db.query(JobPosting)
    
    # Filter out expired jobs
    today = date.today()
    query = query.filter(
        or_(
            JobPosting.application_deadline >= today,
            JobPosting.application_deadline.is_(None)
        )
    )
    
    # Apply filters
    if title:
        search_term = f"%{title}%"
        query = query.filter(JobPosting.title.ilike(search_term))
    
    if department:
        query = query.filter(JobPosting.department == department)
    
    # Note: Location filter would require JSONB querying
    # Simplified for now - can be enhanced later
    
    query = query.order_by(JobPosting.created_at.desc())
    query = query.limit(limit).offset(offset)
    
    jobs = query.all()
    
    # Convert to response models
    return [
        JobPostingResponse(
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
            updated_at=job.updated_at
        )
        for job in jobs
    ]


@router.post("/jobs/search", response_model=List[JobPostingResponse])
async def search_jobs_with_matching(
    request: JobSearchRequest,
    db: Session = Depends(get_db)
):
    """
    Search government jobs with qualification matching
    
    - **qualifications**: User's education, experience, skills, certifications
    - **preferences**: Job search preferences (departments, locations)
    - **limit**: Maximum number of results (default: 10, max: 50)
    
    Returns jobs ranked by match score with explanations.
    """
    matcher = JobMatcher(db)
    
    try:
        matched_jobs = matcher.search_jobs(
            qualifications=request.qualifications,
            preferences=request.preferences,
            limit=request.limit
        )
        
        return matched_jobs
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "JOB_SEARCH_ERROR",
                "message": "Failed to search jobs",
                "details": str(e)
            }
        )


@router.post("/jobs/alerts", response_model=List[JobPostingResponse])
async def get_job_alerts(
    request: JobAlertsRequest,
    db: Session = Depends(get_db)
):
    """
    Get job alerts for new postings matching user profile
    
    - **user_profile**: User profile data
    - **qualifications**: User's education, experience, skills
    - **preferences**: Job search preferences
    - **days_back**: Look for jobs posted in last N days (default: 30, max: 90)
    
    Returns recent job postings that match user qualifications and preferences.
    """
    matcher = JobMatcher(db)
    
    try:
        job_alerts = matcher.get_job_alerts(
            user_profile=request.user_profile,
            qualifications=request.qualifications,
            preferences=request.preferences,
            days_back=request.days_back
        )
        
        return job_alerts
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "JOB_ALERTS_ERROR",
                "message": "Failed to get job alerts",
                "details": str(e)
            }
        )


@router.get("/skills/{program_id}", response_model=SkillProgramResponse)
async def get_skill_program(
    program_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a skill program
    
    - **program_id**: UUID of the skill program
    """
    matcher = SkillsMatcher(db)
    program = matcher.get_program_details(program_id)
    
    if not program:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "PROGRAM_NOT_FOUND",
                "message": f"Skill program with ID {program_id} not found",
                "suggestions": ["Check the program ID", "Browse available programs"]
            }
        )
    
    return SkillProgramResponse(
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
        updated_at=program.updated_at
    )


@router.get("/jobs/{job_id}", response_model=JobPostingResponse)
async def get_job(
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a job posting
    
    - **job_id**: UUID of the job posting
    """
    matcher = JobMatcher(db)
    job = matcher.get_job_by_id(job_id)
    
    if not job:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "JOB_NOT_FOUND",
                "message": f"Job posting with ID {job_id} not found",
                "suggestions": ["Check the job ID", "Browse available jobs"]
            }
        )
    
    return JobPostingResponse(
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
        updated_at=job.updated_at
    )
