"""Authentication endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_user_manager, get_current_user
from app.services.user_manager import UserManager
from app.models.user import User
from app.schemas.user import (
    UserRegisterRequest,
    UserRegisterResponse,
    OTPVerifyRequest,
    TokenResponse,
    UserResponse,
    UserProfileResponse,
    UserProfileCreate,
    UserProfileUpdate,
    LocationSchema
)
from app.logging_config import logger

router = APIRouter(prefix="/api")


@router.post(
    "/auth/register",
    response_model=UserRegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Register a new user with phone number and send OTP for verification"
)
async def register_user(
    request: UserRegisterRequest,
    user_manager: UserManager = Depends(get_user_manager)
):
    """
    Register new user or initiate login for existing user
    
    - **phone_number**: Phone number with country code (e.g., +919876543210)
    - **language**: Preferred language code (e.g., 'hi' for Hindi)
    
    Returns user details and sends OTP for verification
    """
    try:
        user, otp = user_manager.register_user(request)
        
        # In development, include OTP in response
        # In production, OTP should only be sent via SMS
        message = "OTP sent successfully" if user.created_at != user.updated_at else "User already exists. OTP sent for login."
        
        logger.info(f"Registration/Login initiated for {request.phone_number}")
        
        return UserRegisterResponse(
            user_id=str(user.user_id),
            phone_number=user.phone_number,
            message=message,
            otp_sent=True
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post(
    "/auth/verify",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify OTP and authenticate",
    description="Verify OTP and receive JWT access token"
)
async def verify_otp(
    request: OTPVerifyRequest,
    user_manager: UserManager = Depends(get_user_manager)
):
    """
    Verify OTP and authenticate user
    
    - **phone_number**: Phone number used during registration
    - **otp**: 6-digit OTP received via SMS
    
    Returns JWT access token for authenticated requests
    """
    try:
        # Verify OTP
        is_valid = user_manager.verify_otp(request.phone_number, request.otp)
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired OTP"
            )
        
        # Get user
        user = user_manager.get_user_by_phone(request.phone_number)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Generate token
        token, expires_in = user_manager.generate_token(user)
        
        logger.info(f"User authenticated: {user.user_id}")
        
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user_id=str(user.user_id),
            expires_in=expires_in
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OTP verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )


@router.get(
    "/user/profile",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user profile",
    description="Get authenticated user's profile information"
)
async def get_user_profile(
    current_user: User = Depends(get_current_user),
    user_manager: UserManager = Depends(get_user_manager)
):
    """
    Get user profile
    
    Requires authentication via Bearer token
    
    Returns user information including profile details if available
    """
    try:
        # Get profile
        profile = user_manager.get_profile(str(current_user.user_id))
        
        # Build response
        profile_response = None
        if profile:
            location_data = None
            if profile.location:
                location_data = LocationSchema(
                    state=profile.location.state,
                    district=profile.location.district,
                    block=profile.location.block,
                    village=profile.location.village,
                    pincode=profile.location.pincode,
                    latitude=profile.location.latitude,
                    longitude=profile.location.longitude
                )
            
            profile_response = UserProfileResponse(
                profile_id=str(profile.profile_id),
                user_id=str(profile.user_id),
                location=location_data,
                age=profile.age,
                gender=profile.gender,
                education_level=profile.education_level,
                occupation=profile.occupation,
                income_bracket=profile.income_bracket,
                household_size=profile.household_size,
                created_at=profile.created_at,
                updated_at=profile.updated_at
            )
        
        return UserResponse(
            user_id=str(current_user.user_id),
            phone_number=current_user.phone_number,
            language=current_user.language,
            created_at=current_user.created_at,
            updated_at=current_user.updated_at,
            profile=profile_response
        )
    except Exception as e:
        logger.error(f"Get profile error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve profile"
        )


@router.put(
    "/user/profile",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Update user profile",
    description="Create or update user profile information"
)
async def update_user_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    user_manager: UserManager = Depends(get_user_manager)
):
    """
    Update user profile
    
    Requires authentication via Bearer token
    
    Creates profile if it doesn't exist, otherwise updates existing profile
    """
    try:
        user_id = str(current_user.user_id)
        
        # Check if profile exists
        existing_profile = user_manager.get_profile(user_id)
        
        if existing_profile:
            # Update existing profile
            profile = user_manager.update_profile(user_id, profile_data)
        else:
            # Create new profile
            profile_create = UserProfileCreate(**profile_data.model_dump())
            profile = user_manager.create_profile(user_id, profile_create)
        
        # Build response
        location_data = None
        if profile.location:
            location_data = LocationSchema(
                state=profile.location.state,
                district=profile.location.district,
                block=profile.location.block,
                village=profile.location.village,
                pincode=profile.location.pincode,
                latitude=profile.location.latitude,
                longitude=profile.location.longitude
            )
        
        logger.info(f"Profile updated for user: {user_id}")
        
        return UserProfileResponse(
            profile_id=str(profile.profile_id),
            user_id=str(profile.user_id),
            location=location_data,
            age=profile.age,
            gender=profile.gender,
            education_level=profile.education_level,
            occupation=profile.occupation,
            income_bracket=profile.income_bracket,
            household_size=profile.household_size,
            created_at=profile.created_at,
            updated_at=profile.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update profile error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )


@router.delete(
    "/user/data",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user data",
    description="Delete all user data (GDPR compliance)"
)
async def delete_user_data(
    current_user: User = Depends(get_current_user),
    user_manager: UserManager = Depends(get_user_manager)
):
    """
    Delete all user data
    
    Requires authentication via Bearer token
    
    Permanently deletes user account and all associated data
    This action cannot be undone
    """
    try:
        user_id = str(current_user.user_id)
        user_manager.delete_user_data(user_id)
        
        logger.info(f"User data deleted: {user_id}")
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete user error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user data"
        )
