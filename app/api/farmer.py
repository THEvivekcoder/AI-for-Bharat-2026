"""Farmer Advisory API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.farmer import FarmProfile
from app.models.location import Location
from app.schemas.farmer import (
    FarmProfileCreate,
    FarmProfileUpdate,
    FarmProfileResponse,
    CropRecommendationRequest,
    CropRecommendationResponse,
    FertilizerRecommendationRequest,
    FertilizerRecommendationResponse,
    MandiPriceQuery,
    MandiPriceResponse,
    PriceTrendResponse,
    CropCalendarRequest,
    CropCalendarResponse
)
from app.services.crop_advisor import CropAdvisor
from app.services.fertilizer_advisor import FertilizerAdvisor
from app.services.mandi_price_service import MandiPriceService
from app.redis_client import get_redis
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/farmer", tags=["Farmer Advisory"])


# Farm Profile Management
@router.post("/profile", response_model=FarmProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_farm_profile(
    profile_data: FarmProfileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a farm profile for the current user"""
    logger.info(f"Creating farm profile for user {current_user.user_id}")
    
    # Check if profile already exists
    existing_profile = db.query(FarmProfile).filter(
        FarmProfile.user_id == current_user.user_id
    ).first()
    
    if existing_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Farm profile already exists. Use PUT to update."
        )
    
    # Create or get location
    location = db.query(Location).filter(
        Location.state == profile_data.location.state,
        Location.district == profile_data.location.district,
        Location.pincode == profile_data.location.pincode
    ).first()
    
    if not location:
        location = Location(**profile_data.location.model_dump())
        db.add(location)
        db.flush()
    
    # Create farm profile
    farm_profile = FarmProfile(
        user_id=current_user.user_id,
        land_size_acres=profile_data.land_size_acres,
        soil_type=profile_data.soil_type,
        irrigation_type=profile_data.irrigation_type,
        location_id=location.id,
        current_crops=profile_data.current_crops,
        previous_crops=profile_data.previous_crops,
        livestock=profile_data.livestock
    )
    
    db.add(farm_profile)
    db.commit()
    db.refresh(farm_profile)
    
    # Build response
    response = FarmProfileResponse(
        farm_id=farm_profile.farm_id,
        user_id=farm_profile.user_id,
        land_size_acres=farm_profile.land_size_acres,
        soil_type=farm_profile.soil_type,
        irrigation_type=farm_profile.irrigation_type,
        location=profile_data.location,
        current_crops=farm_profile.current_crops,
        previous_crops=farm_profile.previous_crops,
        livestock=farm_profile.livestock,
        created_at=farm_profile.created_at,
        updated_at=farm_profile.updated_at
    )
    
    logger.info(f"Farm profile created: {farm_profile.farm_id}")
    return response


@router.get("/profile", response_model=FarmProfileResponse)
async def get_farm_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get farm profile for the current user"""
    farm_profile = db.query(FarmProfile).filter(
        FarmProfile.user_id == current_user.user_id
    ).first()
    
    if not farm_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm profile not found. Please create one first."
        )
    
    # Get location
    location = db.query(Location).filter(Location.id == farm_profile.location_id).first()
    
    from app.schemas.farmer import LocationBase
    location_data = LocationBase(
        state=location.state,
        district=location.district,
        block=location.block,
        village=location.village,
        pincode=location.pincode,
        latitude=location.latitude,
        longitude=location.longitude
    )
    
    return FarmProfileResponse(
        farm_id=farm_profile.farm_id,
        user_id=farm_profile.user_id,
        land_size_acres=farm_profile.land_size_acres,
        soil_type=farm_profile.soil_type,
        irrigation_type=farm_profile.irrigation_type,
        location=location_data,
        current_crops=farm_profile.current_crops,
        previous_crops=farm_profile.previous_crops,
        livestock=farm_profile.livestock,
        created_at=farm_profile.created_at,
        updated_at=farm_profile.updated_at
    )


@router.put("/profile", response_model=FarmProfileResponse)
async def update_farm_profile(
    profile_data: FarmProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update farm profile for the current user"""
    farm_profile = db.query(FarmProfile).filter(
        FarmProfile.user_id == current_user.user_id
    ).first()
    
    if not farm_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm profile not found. Please create one first."
        )
    
    # Update fields
    update_data = profile_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(farm_profile, field, value)
    
    db.commit()
    db.refresh(farm_profile)
    
    # Get location for response
    location = db.query(Location).filter(Location.id == farm_profile.location_id).first()
    from app.schemas.farmer import LocationBase
    location_data = LocationBase(
        state=location.state,
        district=location.district,
        block=location.block,
        village=location.village,
        pincode=location.pincode,
        latitude=location.latitude,
        longitude=location.longitude
    )
    
    return FarmProfileResponse(
        farm_id=farm_profile.farm_id,
        user_id=farm_profile.user_id,
        land_size_acres=farm_profile.land_size_acres,
        soil_type=farm_profile.soil_type,
        irrigation_type=farm_profile.irrigation_type,
        location=location_data,
        current_crops=farm_profile.current_crops,
        previous_crops=farm_profile.previous_crops,
        livestock=farm_profile.livestock,
        created_at=farm_profile.created_at,
        updated_at=farm_profile.updated_at
    )


# Crop Advisory Endpoints
@router.post("/crop-advice", response_model=List[CropRecommendationResponse])
async def get_crop_advice(
    request: CropRecommendationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get crop recommendations based on farm profile and season"""
    logger.info(f"Getting crop advice for user {current_user.user_id}, season {request.season}")
    
    # Get farm profile
    farm_profile = db.query(FarmProfile).filter(
        FarmProfile.user_id == current_user.user_id
    ).first()
    
    if not farm_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm profile not found. Please create a farm profile first."
        )
    
    # Get crop recommendations
    crop_advisor = CropAdvisor(db)
    recommendations = crop_advisor.recommend_crops(
        farm_profile=farm_profile,
        season=request.season,
        include_weather=request.include_weather
    )
    
    logger.info(f"Generated {len(recommendations)} crop recommendations")
    return recommendations


@router.post("/fertilizer-advice", response_model=FertilizerRecommendationResponse)
async def get_fertilizer_advice(
    request: FertilizerRecommendationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get fertilizer recommendations for a specific crop and growth stage"""
    logger.info(f"Getting fertilizer advice for {request.crop_name} at {request.growth_stage} stage")
    
    # Get farm profile
    farm_profile = db.query(FarmProfile).filter(
        FarmProfile.user_id == current_user.user_id
    ).first()
    
    if not farm_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm profile not found. Please create a farm profile first."
        )
    
    # Get fertilizer recommendation
    fertilizer_advisor = FertilizerAdvisor(db)
    recommendation = fertilizer_advisor.recommend_fertilizer(
        farm_profile=farm_profile,
        crop_name=request.crop_name,
        growth_stage=request.growth_stage,
        soil_data=request.soil_data
    )
    
    logger.info(f"Generated fertilizer recommendation for {request.crop_name}")
    return recommendation


@router.get("/market-price", response_model=List[MandiPriceResponse])
async def get_market_price(
    crop_name: str,
    radius_km: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current mandi prices for a crop near user's location"""
    logger.info(f"Getting market prices for {crop_name} within {radius_km}km")
    
    # Get farm profile for location
    farm_profile = db.query(FarmProfile).filter(
        FarmProfile.user_id == current_user.user_id
    ).first()
    
    if not farm_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm profile not found. Please create a farm profile first."
        )
    
    # Get location
    location = db.query(Location).filter(Location.id == farm_profile.location_id).first()
    
    # Get mandi prices
    redis_client = get_redis()
    mandi_service = MandiPriceService(db, redis_client)
    prices = mandi_service.get_current_price(
        crop_name=crop_name,
        location=location,
        radius_km=radius_km
    )
    
    if not prices:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No market prices found for {crop_name} within {radius_km}km. Try increasing the radius or check back later."
        )
    
    logger.info(f"Found {len(prices)} market prices")
    return prices


@router.get("/market-price/trend", response_model=PriceTrendResponse)
async def get_price_trend(
    crop_name: str,
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get price trend for a crop over specified period"""
    logger.info(f"Getting price trend for {crop_name} over {days} days")
    
    # Get farm profile for location
    farm_profile = db.query(FarmProfile).filter(
        FarmProfile.user_id == current_user.user_id
    ).first()
    
    if not farm_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm profile not found. Please create a farm profile first."
        )
    
    # Get location
    location = db.query(Location).filter(Location.id == farm_profile.location_id).first()
    
    # Get price trend
    redis_client = get_redis()
    mandi_service = MandiPriceService(db, redis_client)
    trend = mandi_service.get_price_trend(
        crop_name=crop_name,
        location=location,
        days=days
    )
    
    if not trend:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No price trend data found for {crop_name} in your area."
        )
    
    logger.info(f"Generated price trend for {crop_name}")
    return trend


@router.get("/crop-calendar", response_model=CropCalendarResponse)
async def get_crop_calendar(
    crop_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get crop calendar with planting and harvest schedules"""
    logger.info(f"Getting crop calendar for {crop_name}")
    
    # Get farm profile for location
    farm_profile = db.query(FarmProfile).filter(
        FarmProfile.user_id == current_user.user_id
    ).first()
    
    if not farm_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm profile not found. Please create a farm profile first."
        )
    
    # Get location
    location = db.query(Location).filter(Location.id == farm_profile.location_id).first()
    
    # Get crop calendar
    crop_advisor = CropAdvisor(db)
    calendar = crop_advisor.get_crop_calendar(
        crop_name=crop_name,
        state=location.state,
        district=location.district
    )
    
    if not calendar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Crop calendar not found for {crop_name} in your area."
        )
    
    logger.info(f"Retrieved crop calendar for {crop_name}")
    return calendar
