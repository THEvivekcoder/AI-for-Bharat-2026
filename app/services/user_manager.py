"""User Manager Service"""
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional, Tuple
from datetime import timedelta
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
from fastapi import HTTPException, status


class UserManager:
    """User management service"""
    
    def __init__(self, db: Session, redis_cache: RedisCache):
        self.db = db
        self.redis = redis_cache
        self.jwt_manager = JWTManager()
        self.otp_manager = OTPManager()
    
    def register_user(self, request: UserRegisterRequest) -> Tuple[User, str]:
        """
        Register a new user and send OTP
        
        Args:
            request: User registration request
            
        Returns:
            Tuple of (User, OTP)
            
        Raises:
            HTTPException: If user already exists or registration fails
        """
        # Hash phone number for lookup
        phone_hash = hash_phone_number(request.phone_number)
        
        # Check if user already exists
        existing_user = self.db.query(User).filter(
            User.phone_number_hash == phone_hash
        ).first()
        
        if existing_user:
            # User exists, generate OTP for login
            otp = self._generate_and_store_otp(request.phone_number)
            logger.info(f"Existing user login attempt: {phone_hash[:8]}...")
            return existing_user, otp
        
        # Create new user
        try:
            user = User(
                phone_number=request.phone_number,  # Will be encrypted automatically
                phone_number_hash=phone_hash,
                language=request.language
            )
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            
            # Generate OTP
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
    
    def verify_otp(self, phone_number: str, otp: str) -> bool:
        """
        Verify OTP for phone number
        
        Args:
            phone_number: User's phone number
            otp: OTP to verify
            
        Returns:
            True if OTP is valid, False otherwise
        """
        # Check attempts
        attempts_key = self.otp_manager.get_otp_attempts_key(phone_number)
        attempts = self.redis.get(attempts_key)
        
        if attempts and int(attempts) >= 3:
            logger.warning(f"Too many OTP attempts for {phone_number}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed attempts. Please request a new OTP."
            )
        
        # Get stored OTP
        otp_key = self.otp_manager.get_otp_key(phone_number)
        stored_otp = self.redis.get(otp_key)
        
        if not stored_otp:
            logger.warning(f"OTP expired or not found for {phone_number}")
            return False
        
        # Verify OTP
        if stored_otp == otp:
            # Clear OTP and attempts
            self.redis.delete(otp_key)
            self.redis.delete(attempts_key)
            logger.info(f"OTP verified successfully for {phone_number}")
            return True
        else:
            # Increment attempts
            current_attempts = int(attempts) if attempts else 0
            self.redis.set(attempts_key, str(current_attempts + 1), expire=600)
            logger.warning(f"Invalid OTP for {phone_number}")
            return False
    
    def generate_token(self, user: User) -> Tuple[str, int]:
        """
        Generate JWT token for user
        
        Args:
            user: User object
            
        Returns:
            Tuple of (token, expiry_seconds)
        """
        token_data = {
            "sub": str(user.user_id),
            "phone": user.phone_number,
            "language": user.language
        }
        
        from app.config import get_settings
        settings = get_settings()
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
        
        token = self.jwt_manager.create_access_token(token_data, expires_delta)
        
        logger.info(f"Token generated for user: {user.user_id}")
        return token, settings.access_token_expire_minutes * 60
    
    def get_user_by_phone(self, phone_number: str) -> Optional[User]:
        """
        Get user by phone number
        
        Args:
            phone_number: User's phone number
            
        Returns:
            User object or None
        """
        phone_hash = hash_phone_number(phone_number)
        return self.db.query(User).filter(User.phone_number_hash == phone_hash).first()
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Get user by ID
        
        Args:
            user_id: User's ID
            
        Returns:
            User object or None
        """
        return self.db.query(User).filter(User.user_id == user_id).first()
    
    def create_profile(self, user_id: str, profile_data: UserProfileCreate) -> UserProfile:
        """
        Create user profile
        
        Args:
            user_id: User's ID
            profile_data: Profile data
            
        Returns:
            Created UserProfile
            
        Raises:
            HTTPException: If profile creation fails
        """
        try:
            # Check if profile already exists
            existing_profile = self.db.query(UserProfile).filter(
                UserProfile.user_id == user_id
            ).first()
            
            if existing_profile:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Profile already exists"
                )
            
            # Create location if provided
            location_id = None
            if profile_data.location:
                location = self._create_location(profile_data.location)
                location_id = location.id
            
            # Create profile
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
        """
        Get user profile
        
        Args:
            user_id: User's ID
            
        Returns:
            UserProfile or None
        """
        return self.db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    
    def update_profile(self, user_id: str, profile_data: UserProfileUpdate) -> UserProfile:
        """
        Update user profile
        
        Args:
            user_id: User's ID
            profile_data: Updated profile data
            
        Returns:
            Updated UserProfile
            
        Raises:
            HTTPException: If profile not found or update fails
        """
        try:
            profile = self.get_profile(user_id)
            
            if not profile:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Profile not found"
                )
            
            # Update location if provided
            if profile_data.location:
                if profile.location_id:
                    # Update existing location
                    location = self.db.query(Location).filter(
                        Location.id == profile.location_id
                    ).first()
                    if location:
                        self._update_location(location, profile_data.location)
                else:
                    # Create new location
                    location = self._create_location(profile_data.location)
                    profile.location_id = location.id
            
            # Update profile fields
            if profile_data.age is not None:
                profile.age = profile_data.age
            if profile_data.gender is not None:
                profile.gender = profile_data.gender
            if profile_data.education_level is not None:
                profile.education_level = profile_data.education_level
            if profile_data.occupation is not None:
                profile.occupation = profile_data.occupation
            if profile_data.income_bracket is not None:
                profile.income_bracket = profile_data.income_bracket
            if profile_data.household_size is not None:
                profile.household_size = profile_data.household_size
            
            self.db.commit()
            self.db.refresh(profile)
            
            logger.info(f"Profile updated for user: {user_id}")
            return profile
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Profile update error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Profile update failed"
            )
    
    def delete_user_data(self, user_id: str) -> bool:
        """
        Delete all user data (GDPR compliance)
        
        Args:
            user_id: User's ID
            
        Returns:
            True if deletion successful
            
        Raises:
            HTTPException: If user not found or deletion fails
        """
        try:
            user = self.get_user_by_id(user_id)
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Delete user (cascade will delete profile)
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
    
    def _generate_and_store_otp(self, phone_number: str) -> str:
        """
        Generate OTP and store in Redis
        
        Args:
            phone_number: User's phone number
            
        Returns:
            Generated OTP
        """
        otp = self.otp_manager.generate_otp()
        otp_key = self.otp_manager.get_otp_key(phone_number)
        
        # Store OTP with expiry
        self.redis.set(
            otp_key,
            otp,
            expire=self.otp_manager.OTP_EXPIRY_MINUTES * 60
        )
        
        # In production, send OTP via SMS
        # For development, log it
        logger.info(f"OTP generated for {phone_number}: {otp}")
        
        return otp
    
    def _create_location(self, location_data: LocationSchema) -> Location:
        """
        Create location record
        
        Args:
            location_data: Location data
            
        Returns:
            Created Location
        """
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
    
    def _update_location(self, location: Location, location_data: LocationSchema) -> None:
        """
        Update location record
        
        Args:
            location: Existing location
            location_data: Updated location data
        """
        location.state = location_data.state
        location.district = location_data.district
        location.block = location_data.block
        location.village = location_data.village
        location.pincode = location_data.pincode
        location.latitude = location_data.latitude
        location.longitude = location_data.longitude
