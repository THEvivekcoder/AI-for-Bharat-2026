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
from app.config import get_settings

settings = get_settings()

router = APIRouter(prefix="/api")


# ===============================
# REGISTER
# ===============================
@router.post(
    "/auth/register",
    response_model=UserRegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_user(
    request: UserRegisterRequest,
    user_manager: UserManager = Depends(get_user_manager)
):
    try:
        user, otp = user_manager.register_user(request)

        # 🔥 HACKATHON MODE
        if settings.debug:
            otp = "123456"
            logger.info("DEBUG MODE: Static OTP = 123456 (Redis bypassed)")

        message = (
            "OTP sent successfully"
            if user.created_at != user.updated_at
            else "User already exists. OTP sent for login."
        )

        logger.info(f"Registration initiated for {request.phone_number}")

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


# ===============================
# VERIFY OTP
# ===============================
@router.post(
    "/auth/verify",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
async def verify_otp(
    request: OTPVerifyRequest,
    user_manager: UserManager = Depends(get_user_manager)
):
    try:

        # 🔥 HACKATHON MODE (No Redis)
        if settings.debug:
            if request.otp != "123456":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid OTP (DEBUG mode expects 123456)"
                )
            logger.info("DEBUG MODE: OTP verified without Redis")

        else:
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