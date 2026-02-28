"""Health Advisory API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.health import (
    SymptomAnalysisRequest,
    HealthGuidance,
    FacilitySearchRequest,
    HealthFacilityResponse,
    HealthSchemeRequest
)
from app.schemas.scheme import SchemeResponse, SchemeFilters
from app.services.health_advisor import HealthAdvisor
from app.services.scheme_repository import SchemeRepository
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/health", tags=["Health Advisory"])


@router.post("/check", response_model=HealthGuidance)
async def check_symptoms(
    request: SymptomAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit symptoms and receive health guidance
    
    This endpoint analyzes symptoms and provides:
    - Urgency level (routine, soon, urgent, emergency)
    - Possible conditions (informational only)
    - Self-care recommendations
    - When to seek medical care
    - Warning signs (red flags)
    - Medical disclaimer
    
    **Important**: This is not a substitute for professional medical advice.
    """
    logger.info(f"Analyzing symptoms for user {current_user.user_id}: {request.symptoms}")
    
    if not request.symptoms:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one symptom is required"
        )
    
    # Analyze symptoms
    health_advisor = HealthAdvisor(db)
    guidance = health_advisor.analyze_symptoms(
        symptoms=request.symptoms,
        user_info=request.user_info
    )
    
    logger.info(f"Generated health guidance with urgency: {guidance.urgency_level}")
    return guidance


@router.get("/facilities", response_model=List[HealthFacilityResponse])
async def find_health_facilities(
    state: str = Query(..., description="State name"),
    district: str = Query(..., description="District name"),
    latitude: Optional[float] = Query(None, ge=-90, le=90, description="Latitude for distance calculation"),
    longitude: Optional[float] = Query(None, ge=-180, le=180, description="Longitude for distance calculation"),
    facility_type: Optional[str] = Query(None, description="Filter by facility type (PHC, CHC, District Hospital, etc.)"),
    radius_km: int = Query(25, ge=1, le=200, description="Search radius in kilometers"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Find nearby health facilities
    
    Returns health facilities in the specified location, optionally filtered by:
    - Facility type (PHC, CHC, District Hospital, Specialty Center)
    - Distance from coordinates (if provided)
    
    Results are sorted by distance (if coordinates provided) or alphabetically by name.
    """
    logger.info(f"Finding health facilities in {district}, {state}")
    
    # Build location object
    from app.schemas.health import Location
    location = Location(
        state=state,
        district=district,
        latitude=latitude,
        longitude=longitude
    )
    
    # Find facilities
    health_advisor = HealthAdvisor(db)
    facilities = health_advisor.find_facilities(
        location=location,
        facility_type=facility_type,
        radius_km=radius_km
    )
    
    if not facilities:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No health facilities found in {district}, {state} within {radius_km}km radius. Try increasing the radius or check nearby districts."
        )
    
    logger.info(f"Found {len(facilities)} health facilities")
    return facilities


@router.post("/facilities/search", response_model=List[HealthFacilityResponse])
async def search_health_facilities(
    request: FacilitySearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Search for health facilities (POST version with request body)
    
    This endpoint accepts a request body with location and search parameters.
    Use this when you need to send complex search criteria.
    """
    logger.info(f"Searching health facilities in {request.location.district}, {request.location.state}")
    
    # Find facilities
    health_advisor = HealthAdvisor(db)
    facilities = health_advisor.find_facilities(
        location=request.location,
        facility_type=request.facility_type,
        radius_km=request.radius_km
    )
    
    if not facilities:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No health facilities found in {request.location.district}, {request.location.state} within {request.radius_km}km radius."
        )
    
    logger.info(f"Found {len(facilities)} health facilities")
    return facilities


@router.get("/schemes", response_model=List[SchemeResponse])
async def get_health_schemes(
    state: Optional[str] = Query(None, description="Filter by state"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get health insurance and benefit schemes
    
    Returns government health schemes including:
    - Health insurance programs
    - Medical benefit schemes
    - Healthcare subsidies
    - Maternal and child health programs
    
    Results can be filtered by state.
    """
    logger.info(f"Fetching health schemes for state: {state or 'all'}")
    
    # Build filters for health category
    filters = SchemeFilters(
        category="health",
        state=state
    )
    
    # Get schemes
    scheme_repo = SchemeRepository(db)
    schemes = scheme_repo.search_schemes(filters=filters)
    
    if not schemes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No health schemes found{' for ' + state if state else ''}. Check back later as new schemes are added regularly."
        )
    
    logger.info(f"Found {len(schemes)} health schemes")
    return schemes
