"""Scheme service API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.services.scheme_repository import SchemeRepository
from app.services.eligibility_checker import EligibilityChecker
from app.services.personalization import PersonalizationEngine
from app.services.verification_tracker import VerificationTracker
from app.schemas.scheme import (
    SchemeResponse,
    SchemeFilters,
    EligibilityCheckRequest,
    EligibilityResult,
    EligibleSchemesRequest,
    EligibleSchemeResponse
)
from app.models.scheme import Scheme

router = APIRouter(prefix="/api/schemes", tags=["schemes"])


def scheme_to_response(scheme: Scheme) -> SchemeResponse:
    """
    Convert Scheme model to SchemeResponse with uncertainty indicators
    
    Args:
        scheme: Scheme database model
        
    Returns:
        SchemeResponse with verification and freshness indicators
    """
    # Calculate uncertainty indicators
    data_age_days = VerificationTracker.calculate_data_age_days(scheme.last_updated)
    is_verified = VerificationTracker.is_verified(scheme.verification_status)
    
    return SchemeResponse(
        scheme_id=str(scheme.scheme_id),
        name=scheme.name,
        category=scheme.category,
        description=scheme.description,
        benefits=scheme.benefits,
        eligibility_criteria=scheme.eligibility_criteria,
        required_documents=scheme.required_documents,
        application_process=scheme.application_process,
        application_url=scheme.application_url,
        department=scheme.department,
        state=scheme.state,
        source_url=scheme.source_url,
        last_updated=scheme.last_updated,
        created_at=scheme.created_at,
        verification_status=scheme.verification_status,
        verified_at=scheme.verified_at,
        verification_source=scheme.verification_source,
        is_verified=is_verified,
        data_age_days=data_age_days,
        translations=[
            {
                "language": t.language,
                "name": t.name,
                "description": t.description,
                "benefits": t.benefits
            }
            for t in scheme.translations
        ] if scheme.translations else None
    )


@router.get("", response_model=List[SchemeResponse])
async def list_schemes(
    category: Optional[str] = Query(None, description="Filter by category"),
    state: Optional[str] = Query(None, description="Filter by state"),
    department: Optional[str] = Query(None, description="Filter by department"),
    query: Optional[str] = Query(None, description="Search query for name/description"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db)
):
    """
    List all schemes with optional filters
    
    - **category**: Filter by scheme category (e.g., agriculture, health, education)
    - **state**: Filter by state (includes central schemes)
    - **department**: Filter by government department
    - **query**: Text search in scheme name and description
    - **limit**: Maximum number of results (default: 100, max: 500)
    - **offset**: Offset for pagination (default: 0)
    """
    repository = SchemeRepository(db)
    
    filters = SchemeFilters(
        category=category,
        state=state,
        department=department,
        query=query
    )
    
    schemes = repository.search_schemes(filters, limit=limit, offset=offset)
    
    # Convert to response models with uncertainty indicators
    return [scheme_to_response(scheme) for scheme in schemes]


@router.get("/{scheme_id}", response_model=SchemeResponse)
async def get_scheme(
    scheme_id: str,
    db: Session = Depends(get_db)
):
    """
    Get scheme details by ID
    
    - **scheme_id**: UUID of the scheme
    """
    repository = SchemeRepository(db)
    scheme = repository.get_scheme_by_id(scheme_id)
    
    if not scheme:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "SCHEME_NOT_FOUND",
                "message": f"Scheme with ID {scheme_id} not found",
                "suggestions": ["Check the scheme ID", "Browse available schemes"]
            }
        )
    
    return scheme_to_response(scheme)


@router.post("/check-eligibility", response_model=EligibilityResult)
async def check_eligibility(
    request: EligibilityCheckRequest,
    db: Session = Depends(get_db)
):
    """
    Check eligibility for a specific scheme
    
    - **scheme_id**: UUID of the scheme to check
    - **user_profile**: User profile data including age, income, location, occupation, etc.
    """
    repository = SchemeRepository(db)
    scheme = repository.get_scheme_by_id(request.scheme_id)
    
    if not scheme:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "SCHEME_NOT_FOUND",
                "message": f"Scheme with ID {request.scheme_id} not found"
            }
        )
    
    checker = EligibilityChecker(db)
    result = checker.check_eligibility(request.user_profile, scheme)
    
    return result


@router.post("/eligible", response_model=List[EligibleSchemeResponse])
async def get_eligible_schemes(
    request: EligibleSchemesRequest,
    limit: int = Query(100, ge=1, le=500, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    personalized: bool = Query(True, description="Enable personalized ranking"),
    db: Session = Depends(get_db)
):
    """
    Get all eligible schemes for user profile with personalized ranking
    
    - **user_profile**: User profile data including age, income, location, occupation, etc.
    - **category**: Optional category filter
    - **state**: Optional state filter
    - **limit**: Maximum number of results (default: 100, max: 500)
    - **offset**: Offset for pagination (default: 0)
    - **personalized**: Enable personalized ranking based on user profile (default: True)
    """
    repository = SchemeRepository(db)
    
    # Get schemes based on filters
    filters = SchemeFilters(
        category=request.category,
        state=request.state
    )
    schemes = repository.search_schemes(filters, limit=limit * 2, offset=offset)  # Get more for ranking
    
    # Check eligibility for each scheme
    checker = EligibilityChecker(db)
    eligible_schemes = checker.get_eligible_schemes(request.user_profile, schemes)
    
    # Apply personalized ranking if enabled
    if personalized and eligible_schemes:
        personalization = PersonalizationEngine()
        
        # Convert schemes to dict format for scoring
        scheme_dicts = []
        for scheme, eligibility in eligible_schemes:
            scheme_dict = {
                "scheme_id": str(scheme.scheme_id),
                "name": scheme.name,
                "category": scheme.category,
                "description": scheme.description,
                "benefits": scheme.benefits,
                "eligibility_criteria": scheme.eligibility_criteria,
                "state": scheme.state,
                "department": scheme.department
            }
            scheme_dicts.append((scheme, eligibility, scheme_dict))
        
        # Score and rank schemes
        scored_schemes = []
        for scheme, eligibility, scheme_dict in scheme_dicts:
            score, explanation = personalization.score_scheme_relevance(
                scheme_dict,
                request.user_profile.model_dump()
            )
            # Add explanation to eligibility result
            eligibility.explanation = explanation
            eligibility.relevance_score = score
            scored_schemes.append((scheme, eligibility, score))
        
        # Sort by relevance score
        scored_schemes.sort(key=lambda x: x[2], reverse=True)
        eligible_schemes = [(s, e) for s, e, _ in scored_schemes]
    
    # Apply limit after ranking
    eligible_schemes = eligible_schemes[:limit]
    
    # Convert to response models
    return [
        EligibleSchemeResponse(
            scheme=scheme_to_response(scheme),
            eligibility=eligibility
        )
        for scheme, eligibility in eligible_schemes
    ]
