"""Test verification tracking and uncertainty indicators"""
import sys
sys.path.insert(0, '.')

from datetime import datetime, timedelta
from app.services.verification_tracker import VerificationTracker, VerificationStatus, DataFreshnessLevel


def test_data_age_calculation():
    """Test data age calculation"""
    print("Testing data age calculation...")
    
    # Test with recent data
    recent_date = datetime.utcnow() - timedelta(days=5)
    age = VerificationTracker.calculate_data_age_days(recent_date)
    assert age == 5, f"Expected 5 days, got {age}"
    print(f"✓ Recent data age: {age} days")
    
    # Test with old data
    old_date = datetime.utcnow() - timedelta(days=45)
    age = VerificationTracker.calculate_data_age_days(old_date)
    assert age == 45, f"Expected 45 days, got {age}"
    print(f"✓ Old data age: {age} days")
    
    # Test with None
    age = VerificationTracker.calculate_data_age_days(None)
    assert age is None, f"Expected None, got {age}"
    print("✓ None date returns None")


def test_freshness_level():
    """Test freshness level determination"""
    print("\nTesting freshness level...")
    
    # Fresh data (< 7 days)
    fresh_date = datetime.utcnow() - timedelta(days=3)
    level = VerificationTracker.get_freshness_level(fresh_date)
    assert level == DataFreshnessLevel.FRESH, f"Expected FRESH, got {level}"
    print(f"✓ 3 days old: {level.value}")
    
    # Recent data (7-30 days)
    recent_date = datetime.utcnow() - timedelta(days=15)
    level = VerificationTracker.get_freshness_level(recent_date)
    assert level == DataFreshnessLevel.RECENT, f"Expected RECENT, got {level}"
    print(f"✓ 15 days old: {level.value}")
    
    # Stale data (> 30 days)
    stale_date = datetime.utcnow() - timedelta(days=45)
    level = VerificationTracker.get_freshness_level(stale_date)
    assert level == DataFreshnessLevel.STALE, f"Expected STALE, got {level}"
    print(f"✓ 45 days old: {level.value}")
    
    # Unknown (None)
    level = VerificationTracker.get_freshness_level(None)
    assert level == DataFreshnessLevel.UNKNOWN, f"Expected UNKNOWN, got {level}"
    print(f"✓ No date: {level.value}")


def test_verification_status():
    """Test verification status checking"""
    print("\nTesting verification status...")
    
    # Verified
    is_verified = VerificationTracker.is_verified(VerificationStatus.VERIFIED)
    assert is_verified is True, "Expected True for verified status"
    print("✓ Verified status: True")
    
    # Unverified
    is_verified = VerificationTracker.is_verified(VerificationStatus.UNVERIFIED)
    assert is_verified is False, "Expected False for unverified status"
    print("✓ Unverified status: False")
    
    # None
    is_verified = VerificationTracker.is_verified(None)
    assert is_verified is False, "Expected False for None status"
    print("✓ None status: False")


def test_uncertainty_indicators():
    """Test uncertainty indicator addition"""
    print("\nTesting uncertainty indicators...")
    
    # Test with verified, fresh data
    data = {"name": "Test Scheme"}
    fresh_date = datetime.utcnow() - timedelta(days=3)
    result = VerificationTracker.add_uncertainty_indicators(
        data.copy(),
        last_updated=fresh_date,
        verification_status=VerificationStatus.VERIFIED,
        verification_source="Official Government Portal"
    )
    
    assert result['is_verified'] is True
    assert result['data_age_days'] == 3
    assert result['freshness_level'] == DataFreshnessLevel.FRESH.value
    assert 'data_warnings' not in result  # No warnings for verified, fresh data
    print("✓ Verified, fresh data: No warnings")
    
    # Test with unverified, stale data
    data = {"name": "Test Scheme"}
    stale_date = datetime.utcnow() - timedelta(days=45)
    result = VerificationTracker.add_uncertainty_indicators(
        data.copy(),
        last_updated=stale_date,
        verification_status=VerificationStatus.UNVERIFIED,
        verification_source="Third-party source"
    )
    
    assert result['is_verified'] is False
    assert result['data_age_days'] == 45
    assert result['freshness_level'] == DataFreshnessLevel.STALE.value
    assert 'data_warnings' in result
    assert len(result['data_warnings']) == 2  # Stale + unverified warnings
    print(f"✓ Unverified, stale data: {len(result['data_warnings'])} warnings")
    print(f"  Warnings: {result['data_warnings']}")


def test_mark_as_verified():
    """Test marking data as verified"""
    print("\nTesting mark as verified...")
    
    verification_data = VerificationTracker.mark_as_verified("Official Source")
    
    assert verification_data['verification_status'] == VerificationStatus.VERIFIED
    assert verification_data['verified_at'] is not None
    assert verification_data['verification_source'] == "Official Source"
    assert verification_data['last_updated'] is not None
    print("✓ Mark as verified: All fields set correctly")


def test_mark_as_unverified():
    """Test marking data as unverified"""
    print("\nTesting mark as unverified...")
    
    verification_data = VerificationTracker.mark_as_unverified("Unofficial Source")
    
    assert verification_data['verification_status'] == VerificationStatus.UNVERIFIED
    assert verification_data['verified_at'] is None
    assert verification_data['verification_source'] == "Unofficial Source"
    assert verification_data['last_updated'] is not None
    print("✓ Mark as unverified: All fields set correctly")


def test_should_reverify():
    """Test reverification check"""
    print("\nTesting reverification check...")
    
    # Recent verification (< 30 days)
    recent_verification = datetime.utcnow() - timedelta(days=15)
    should_reverify = VerificationTracker.should_reverify(recent_verification, reverification_days=30)
    assert should_reverify is False, "Should not need reverification"
    print("✓ Recent verification (15 days): No reverification needed")
    
    # Old verification (> 30 days)
    old_verification = datetime.utcnow() - timedelta(days=45)
    should_reverify = VerificationTracker.should_reverify(old_verification, reverification_days=30)
    assert should_reverify is True, "Should need reverification"
    print("✓ Old verification (45 days): Reverification needed")
    
    # No verification
    should_reverify = VerificationTracker.should_reverify(None, reverification_days=30)
    assert should_reverify is True, "Should need verification"
    print("✓ No verification: Verification needed")


if __name__ == "__main__":
    print("=" * 60)
    print("Verification Tracking Tests")
    print("=" * 60)
    
    try:
        test_data_age_calculation()
        test_freshness_level()
        test_verification_status()
        test_uncertainty_indicators()
        test_mark_as_verified()
        test_mark_as_unverified()
        test_should_reverify()
        
        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
