"""Test script to validate the setup"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import engine, SessionLocal
from app.redis_client import get_redis
from app.logging_config import logger
from app.models import User, Location, UserProfile


def test_database():
    """Test database connection"""
    try:
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            logger.info("✓ Database connection successful")
            return True
    except Exception as e:
        logger.error(f"✗ Database connection failed: {str(e)}")
        return False


def test_redis():
    """Test Redis connection"""
    try:
        redis_client = get_redis()
        redis_client.ping()
        logger.info("✓ Redis connection successful")
        return True
    except Exception as e:
        logger.error(f"✗ Redis connection failed: {str(e)}")
        return False


def test_models():
    """Test database models"""
    try:
        db = SessionLocal()
        
        # Test creating a location
        location = Location(
            state="Test State",
            district="Test District",
            pincode="123456"
        )
        db.add(location)
        db.commit()
        db.refresh(location)
        
        # Test creating a user
        user = User(
            phone_number="+919999999999",
            language="hi"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Test creating a user profile
        profile = UserProfile(
            user_id=user.user_id,
            location_id=location.id,
            age=30,
            gender="male"
        )
        db.add(profile)
        db.commit()
        
        # Clean up
        db.delete(profile)
        db.delete(user)
        db.delete(location)
        db.commit()
        db.close()
        
        logger.info("✓ Database models working correctly")
        return True
    except Exception as e:
        logger.error(f"✗ Database models test failed: {str(e)}")
        return False


def main():
    """Run all tests"""
    logger.info("Starting setup validation...")
    logger.info("-" * 50)
    
    results = []
    results.append(("Database Connection", test_database()))
    results.append(("Redis Connection", test_redis()))
    results.append(("Database Models", test_models()))
    
    logger.info("-" * 50)
    logger.info("Test Results:")
    for name, result in results:
        status = "PASS" if result else "FAIL"
        logger.info(f"  {name}: {status}")
    
    all_passed = all(result for _, result in results)
    if all_passed:
        logger.info("\n✓ All tests passed! Setup is complete.")
    else:
        logger.error("\n✗ Some tests failed. Please check the configuration.")
        sys.exit(1)


if __name__ == "__main__":
    main()
