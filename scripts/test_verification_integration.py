"""Integration test for verification tracking with database"""
import sys
sys.path.insert(0, '.')

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models.scheme import Scheme
from app.services.scheme_repository import SchemeRepository
from app.services.verification_tracker import VerificationTracker
import uuid


def test_scheme_verification_tracking():
    """Test verification tracking with actual database operations"""
    print("Testing scheme verification tracking integration...")
    
    db: Session = SessionLocal()
    
    try:
        # Create a test scheme
        test_scheme = Scheme(
            scheme_id=uuid.uuid4(),
            name="Test Verification Scheme",
            category="test",
            description="Testing verification tracking",
            eligibility_criteria={"age_min": 18},
            last_updated=datetime.utcnow() - timedelta(days=45),  # Stale data
            verification_status="unverified",
            created_at=datetime.utcnow()
        )
        
        db.add(test_scheme)
        db.commit()
        db.refresh(test_scheme)
        
        scheme_id = str(test_scheme.scheme_id)
        print(f"✓ Created test scheme: {scheme_id}")
        
        # Test marking as verified
        repository = SchemeRepository(db)
        verified_scheme = repository.mark_scheme_as_verified(
            scheme_id=scheme_id,
            verification_source="Official Test Source"
        )
        
        assert verified_scheme is not None
        assert verified_scheme.verification_status == "verified"
        assert verified_scheme.verified_at is not None
        assert verified_scheme.verification_source == "Official Test Source"
        print("✓ Marked scheme as verified")
        
        # Test marking as unverified
        unverified_scheme = repository.mark_scheme_as_unverified(
            scheme_id=scheme_id,
            source="Unofficial Test Source"
        )
        
        assert unverified_scheme is not None
        assert unverified_scheme.verification_status == "unverified"
        assert unverified_scheme.verified_at is None
        assert unverified_scheme.verification_source == "Unofficial Test Source"
        print("✓ Marked scheme as unverified")
        
        # Test getting schemes needing verification
        schemes_needing_verification = repository.get_schemes_needing_verification(
            reverification_days=30,
            limit=10
        )
        
        assert len(schemes_needing_verification) > 0
        print(f"✓ Found {len(schemes_needing_verification)} schemes needing verification")
        
        # Test uncertainty indicators
        data_age = VerificationTracker.calculate_data_age_days(unverified_scheme.last_updated)
        is_verified = VerificationTracker.is_verified(unverified_scheme.verification_status)
        freshness = VerificationTracker.get_freshness_level(unverified_scheme.last_updated)
        
        print(f"✓ Data age: {data_age} days")
        print(f"✓ Is verified: {is_verified}")
        print(f"✓ Freshness level: {freshness.value}")
        
        # Cleanup
        db.delete(test_scheme)
        db.commit()
        print("✓ Cleaned up test data")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Verification Tracking Integration Test")
    print("=" * 60)
    
    success = test_scheme_verification_tracking()
    
    if success:
        print("\n" + "=" * 60)
        print("✓ Integration test passed!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("✗ Integration test failed!")
        print("=" * 60)
        sys.exit(1)
