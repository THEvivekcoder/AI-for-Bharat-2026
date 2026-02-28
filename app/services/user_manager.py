"""User Manager Service"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional, Tuple
from datetime import timedelta
from fastapi import HTTPException, status

from app.models.user import User, UserProfile
from app.models.location import Location
from app.schemas.user import (
    UserRegisterRequest,
    UserProfileCreate,
    UserProfileUpdate,
    LocationSchema
)
from app.utils.auth import JWTManager, OTPManager
from app.redis_client import RedisCache
from app.security.hashing import hash_phone_number
from app.logging_config import logger
from app.config import get_settings


class UserManager:
    """User management service"""

    def __init__(self, db: Session, redis_cache: RedisCache):
        self.db = db
        self.redis = redis_cache
        self.jwt_manager = JWTManager()
        self.otp_manager = OTPManager()

    # =====================================================
    # REGISTER USER
    # =====================================================
    def register_user(self, request: UserRegisterRequest) -> Tuple[User, str]:
        settings = get_settings()

        phone_hash = hash_phone_number(request.phone_number)

        existing_user = self.db.query(User).filter(
            User.phone_number_hash == phone_hash
        ).first()

        # Existing user → Login flow
        if existing_user:
            otp = self._generate_and_store_otp(request.phone_number)
            logger.info(f"Existing user login attempt: {phone_hash[:8]}...")
            return existing_user, otp

        # New user → Registration flow
        try:
            user = User(
                phone_number=request.phone_number,
                phone_number_hash=phone_hash,
                language=request.language
            )

            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)

            otp = self._generate_and_store_otp(request.phone_number)

            logger.info(f"New user registered: {phone_hash[:8]}...")
            return user, otp

        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"User registration failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already exists"
            )

        except Exception as e:
            self.db.rollback()
            logger.error(f"User registration error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Registration failed"
            )

    # =====================================================
    # VERIFY OTP
    # =====================================================
    def verify_otp(self, phone_number: str, otp: str) -> bool:
        settings = get_settings()

        # 🔥 HACKATHON MODE (NO REDIS)
        if settings.debug:
            if otp == "123456":
                logger.info(f"DEBUG MODE: OTP verified for {phone_number}")
                return True
            return False

        # ===== Production Mode =====

        attempts_key = self.otp_manager.get_otp_attempts_key(phone_number)
        attempts = self.redis.get(attempts_key)

        if attempts and int(attempts) >= 3:
            logger.warning(f"Too many OTP attempts for {phone_number}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed attempts. Please request a new OTP."
            )

        otp_key = self.otp_manager.get_otp_key(phone_number)
        stored_otp = self.redis.get(otp_key)

        if not stored_otp:
            logger.warning(f"OTP expired or not found for {phone_number}")
            return False

        if stored_otp == otp:
            self.redis.delete(otp_key)
            self.redis.delete(attempts_key)
            logger.info(f"OTP verified successfully for {phone_number}")
            return True
        else:
            current_attempts = int(attempts) if attempts else 0
            self.redis.set(attempts_key, str(current_attempts + 1), expire=600)
            logger.warning(f"Invalid OTP for {phone_number}")
            return False

    # =====================================================
    # TOKEN GENERATION
    # =====================================================
    def generate_token(self, user: User) -> Tuple[str, int]:
        settings = get_settings()

        token_data = {
            "sub": str(user.user_id),
            "phone": user.phone_number,
            "language": user.language
        }

        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)

        token = self.jwt_manager.create_access_token(token_data, expires_delta)

        logger.info(f"Token generated for user: {user.user_id}")
        return token, settings.access_token_expire_minutes * 60

    # =====================================================
    # USER LOOKUP
    # =====================================================
    def get_user_by_phone(self, phone_number: str) -> Optional[User]:
        phone_hash = hash_phone_number(phone_number)
        return self.db.query(User).filter(User.phone_number_hash == phone_hash).first()

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        return self.db.query(User).filter(User.user_id == user_id).first()

    # =====================================================
    # OTP GENERATION (MODIFIED)
    # =====================================================
    def _generate_and_store_otp(self, phone_number: str) -> str:
        settings = get_settings()

        # 🔥 HACKATHON MODE
        if settings.debug:
            otp = "123456"
            logger.info(f"DEBUG MODE: Static OTP for {phone_number} = 123456 (Redis skipped)")
            return otp

        # Production Mode
        otp = self.otp_manager.generate_otp()
        otp_key = self.otp_manager.get_otp_key(phone_number)

        self.redis.set(
            otp_key,
            otp,
            expire=self.otp_manager.OTP_EXPIRY_MINUTES * 60
        )

        logger.info(f"OTP generated for {phone_number}: {otp}")
        return otp

    # =====================================================
    # PROFILE MANAGEMENT (UNCHANGED)
    # =====================================================
    def create_profile(self, user_id: str, profile_data: UserProfileCreate) -> UserProfile:
        try:
            existing_profile = self.db.query(UserProfile).filter(
                UserProfile.user_id == user_id
            ).first()

            if existing_profile:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Profile already exists"
                )

            location_id = None
            if profile_data.location:
                location = self._create_location(profile_data.location)
                location_id = location.id

            profile = UserProfile(
                user_id=user_id,
                location_id=location_id,
                age=profile_data.age,
                gender=profile_data.gender,
                education_level=profile_data.education_level,
                occupation=profile_data.occupation,
                income_bracket=profile_data.income_bracket,
                household_size=profile_data.household_size
            )

            self.db.add(profile)
            self.db.commit()
            self.db.refresh(profile)

            logger.info(f"Profile created for user: {user_id}")
            return profile

        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Profile creation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Profile creation failed"
            )

    def get_profile(self, user_id: str) -> Optional[UserProfile]:
        return self.db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

    def delete_user_data(self, user_id: str) -> bool:
        try:
            user = self.get_user_by_id(user_id)

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            self.db.delete(user)
            self.db.commit()

            logger.info(f"User data deleted: {user_id}")
            return True

        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"User deletion error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="User deletion failed"
            )

    # =====================================================
    # LOCATION HELPERS
    # =====================================================
    def _create_location(self, location_data: LocationSchema) -> Location:
        location = Location(
            state=location_data.state,
            district=location_data.district,
            block=location_data.block,
            village=location_data.village,
            pincode=location_data.pincode,
            latitude=location_data.latitude,
            longitude=location_data.longitude
        )
        self.db.add(location)
        self.db.flush()
        return location