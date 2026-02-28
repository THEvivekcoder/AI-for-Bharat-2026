"""Test script for User Manager service"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import SessionLocal
from app.redis_client import RedisCache
from app.services.user_manager import UserManager
from app.schemas.user import UserRegisterRequest, UserProfileCreate, LocationSchema
from app.logging_config import logger


def test_user_registration():
    """Test user registration and OTP generation"""
    db = SessionLocal()
    redis_cache = RedisCache()
    user_manager = UserManager(db, redis_cache)
    
    try:
        # Test registration
        request = UserRegisterRequest(
            phone_number="+919876543210",
            language="hi"
        )
        
        user, otp = user_manager.register_user(request)
        logger.info(f"✓ User registered: {user.user_id}")
        logger.info(f"  OTP generated: {otp}")
        
        # Test OTP verification
        is_valid = user_manager.verify_otp(request.phone_number, otp)
        if is_valid:
            logger.info("✓ OTP verification successful")
        else:
            logger.error("✗ OTP verification failed")
            return False
        
        # Test token generation
        token, expiry = user_manager.generate_token(user)
        logger.info(f"✓ JWT token generated (expires in {expiry}s)")
        
        # Test profile creation
        profile_data = UserProfileCreate(
            location=LocationSchema(
                state="Maharashtra",
                district="Mumbai",
                pincode="400001"
            ),
            age=30,
            gender="male",
            occupation="farmer"
        )
        
        profile = user_manager.create_profile(str(user.user_id), profile_data)
        logger.info(f"✓ Profile created: {profile.profile_id}")
        
        # Test profile retrieval
        retrieved_profile = user_manager.get_profile(str(user.user_id))
        if retrieved_profile:
            logger.info("✓ Profile retrieved successfully")
        else:
            logger.error("✗ Profile retrieval failed")
            return False
        
        # Clean up
        user_manager.delete_user_data(str(user.user_id))
        logger.info("✓ User data deleted (cleanup)")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Test failed: {str(e)}")
        return False
    finally:
        db.close()


def main():
    """Run User Manager tests"""
    logger.info("Testing User Manager Service...")
    logger.info("-" * 50)
    
    success = test_user_registration()
    
    logger.info("-" * 50)
    if success:
        logger.info("✓ All User Manager tests passed!")
    else:
        logger.error("✗ User Manager tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
