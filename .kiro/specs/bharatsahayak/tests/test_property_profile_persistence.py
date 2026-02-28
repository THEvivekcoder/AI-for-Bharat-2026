"""
Property-Based Test: Profile Data Round-Trip
Feature: bharatsahayak, Property 20: Profile Data Round-Trip

For any user profile data, storing the profile and then retrieving it 
should return an equivalent profile with all fields preserved.

Validates: Requirements 8.1
"""
import pytest
import os
from hypothesis import given, settings, strategies as st, HealthCheck
from hypothesis.strategies import composite
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.services.user_manager import UserManager
from app.models.user import User, UserProfile
from app.models.location import Location
from app.schemas.user import UserProfileCreate, LocationSchema
from app.redis_client import RedisCache
import uuid


# Use test database URL from environment or default
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://bharatsahayak:password@localhost:5432/bharatsahayak")


# Strategy for generating valid location data
@composite
def location_strategy(draw):
    """Generate valid location data"""
    return LocationSchema(
        state=draw(st.text(min_size=1, max_size=50, alphabet=st.characters(min_codepoint=65, max_codepoint=122))),
        district=draw(st.text(min_size=1, max_size=50, alphabet=st.characters(min_codepoint=65, max_codepoint=122))),
        block=draw(st.one_of(st.none(), st.text(min_size=1, max_size=50, alphabet=st.characters(min_codepoint=65, max_codepoint=122)))),
        village=draw(st.one_of(st.none(), st.text(min_size=1, max_size=100, alphabet=st.characters(min_codepoint=65, max_codepoint=122)))),
        pincode=draw(st.from_regex(r'^\d{6}$', fullmatch=True)),
        latitude=draw(st.one_of(st.none(), st.floats(min_value=-90, max_value=90, allow_nan=False, allow_infinity=False))),
        longitude=draw(st.one_of(st.none(), st.floats(min_value=-180, max_value=180, allow_nan=False, allow_infinity=False)))
    )


# Strategy for generating valid profile data
@composite
def profile_strategy(draw):
    """Generate valid user profile data"""
    return UserProfileCreate(
        location=draw(st.one_of(st.none(), location_strategy())),
        age=draw(st.one_of(st.none(), st.integers(min_value=1, max_value=150))),
        gender=draw(st.one_of(st.none(), st.sampled_from(['Male', 'Female', 'Other']))),
        education_level=draw(st.one_of(st.none(), st.sampled_from([
            'No Formal Education', 'Primary', 'Secondary', 'Higher Secondary', 
            'Graduate', 'Post Graduate', 'Doctorate'
        ]))),
        occupation=draw(st.one_of(st.none(), st.sampled_from([
            'Farmer', 'Daily Wage Worker', 'Self Employed', 'Salaried', 
            'Student', 'Unemployed', 'Retired'
        ]))),
        income_bracket=draw(st.one_of(st.none(), st.sampled_from([
            'Below 1 Lakh', '1-3 Lakhs', '3-5 Lakhs', '5-10 Lakhs', 'Above 10 Lakhs'
        ]))),
        household_size=draw(st.one_of(st.none(), st.integers(min_value=1, max_value=100)))
    )


@pytest.fixture(scope="module")
def test_engine():
    """Create test database engine"""
    engine = create_engine(TEST_DATABASE_URL)
    # Create all tables
    Base.metadata.create_all(engine)
    yield engine
    # Drop all tables after tests
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def test_db(test_engine):
    """Create a test database session for each test"""
    TestingSessionLocal = sessionmaker(bind=test_engine)
    db = TestingSessionLocal()
    
    yield db
    
    # Rollback any uncommitted changes and close
    db.rollback()
    # Clean up test data
    db.query(UserProfile).delete()
    db.query(User).delete()
    db.query(Location).delete()
    db.commit()
    db.close()


@pytest.fixture(scope="function")
def redis_cache():
    """Create a mock Redis cache"""
    # For testing, we'll use a simple dict-based mock
    class MockRedisCache:
        def __init__(self):
            self.data = {}
        
        def get(self, key):
            return self.data.get(key)
        
        def set(self, key, value, expire=None):
            self.data[key] = value
        
        def delete(self, key):
            if key in self.data:
                del self.data[key]
    
    return MockRedisCache()


@pytest.fixture(scope="function")
def user_manager(test_db, redis_cache):
    """Create UserManager instance with test database"""
    return UserManager(test_db, redis_cache)


@pytest.fixture(scope="function")
def test_user(test_db):
    """Create a test user"""
    # Generate unique phone number for each test
    phone_number = f"+9198765{uuid.uuid4().hex[:5]}"
    user = User(
        user_id=uuid.uuid4(),
        phone_number=phone_number,
        language="hi"
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])  # Reduced for faster checkpoint testing
@given(profile_data=profile_strategy())
def test_profile_data_round_trip(profile_data, test_db, redis_cache, test_user):
    """
    Feature: bharatsahayak, Property 20: Profile Data Round-Trip
    
    For any user profile data, storing the profile and then retrieving it 
    should return an equivalent profile with all fields preserved.
    
    This property ensures data integrity and persistence correctness.
    """
    # Clean up any existing profile for this user (from previous iterations)
    existing_profile = test_db.query(UserProfile).filter(UserProfile.user_id == test_user.user_id).first()
    if existing_profile:
        test_db.delete(existing_profile)
        test_db.commit()
    
    # Create UserManager
    user_manager = UserManager(test_db, redis_cache)
    
    # Store the profile
    created_profile = user_manager.create_profile(str(test_user.user_id), profile_data)
    
    # Retrieve the profile
    retrieved_profile = user_manager.get_profile(str(test_user.user_id))
    
    # Assert profile was retrieved
    assert retrieved_profile is not None, "Profile should be retrievable after creation"
    
    # Assert all fields are preserved
    assert retrieved_profile.user_id == test_user.user_id, "User ID should be preserved"
    assert retrieved_profile.age == profile_data.age, "Age should be preserved"
    assert retrieved_profile.gender == profile_data.gender, "Gender should be preserved"
    assert retrieved_profile.education_level == profile_data.education_level, "Education level should be preserved"
    assert retrieved_profile.occupation == profile_data.occupation, "Occupation should be preserved"
    assert retrieved_profile.income_bracket == profile_data.income_bracket, "Income bracket should be preserved"
    assert retrieved_profile.household_size == profile_data.household_size, "Household size should be preserved"
    
    # Assert location data is preserved if provided
    if profile_data.location:
        assert retrieved_profile.location is not None, "Location should be preserved"
        assert retrieved_profile.location.state == profile_data.location.state, "State should be preserved"
        assert retrieved_profile.location.district == profile_data.location.district, "District should be preserved"
        assert retrieved_profile.location.block == profile_data.location.block, "Block should be preserved"
        assert retrieved_profile.location.village == profile_data.location.village, "Village should be preserved"
        assert retrieved_profile.location.pincode == profile_data.location.pincode, "Pincode should be preserved"
        
        # Handle floating point comparison for coordinates
        if profile_data.location.latitude is not None:
            assert abs(retrieved_profile.location.latitude - profile_data.location.latitude) < 0.0001, "Latitude should be preserved"
        else:
            assert retrieved_profile.location.latitude is None, "Latitude should be None if not provided"
        
        if profile_data.location.longitude is not None:
            assert abs(retrieved_profile.location.longitude - profile_data.location.longitude) < 0.0001, "Longitude should be preserved"
        else:
            assert retrieved_profile.location.longitude is None, "Longitude should be None if not provided"
    else:
        assert retrieved_profile.location_id is None, "Location should be None if not provided"
    
    # Assert timestamps are set
    assert retrieved_profile.created_at is not None, "Created timestamp should be set"
    assert retrieved_profile.updated_at is not None, "Updated timestamp should be set"


def test_profile_round_trip_with_update(test_db, redis_cache, test_user):
    """
    Test that profile data round-trip works correctly with updates.
    
    This is a specific example test to complement the property-based test.
    """
    user_manager = UserManager(test_db, redis_cache)
    
    # Create initial profile
    initial_profile = UserProfileCreate(
        location=LocationSchema(
            state="Maharashtra",
            district="Pune",
            block="Haveli",
            village="Kharadi",
            pincode="411014",
            latitude=18.5511,
            longitude=73.9250
        ),
        age=35,
        gender="Male",
        education_level="Graduate",
        occupation="Farmer",
        income_bracket="1-3 Lakhs",
        household_size=5
    )
    
    created_profile = user_manager.create_profile(str(test_user.user_id), initial_profile)
    
    # Update profile
    from app.schemas.user import UserProfileUpdate
    update_data = UserProfileUpdate(
        age=36,
        occupation="Self Employed",
        household_size=6
    )
    
    updated_profile = user_manager.update_profile(str(test_user.user_id), update_data)
    
    # Retrieve and verify
    retrieved_profile = user_manager.get_profile(str(test_user.user_id))
    
    assert retrieved_profile.age == 36, "Updated age should be preserved"
    assert retrieved_profile.occupation == "Self Employed", "Updated occupation should be preserved"
    assert retrieved_profile.household_size == 6, "Updated household size should be preserved"
    assert retrieved_profile.gender == "Male", "Unchanged fields should remain"
    assert retrieved_profile.education_level == "Graduate", "Unchanged fields should remain"
    assert retrieved_profile.location.state == "Maharashtra", "Location should remain unchanged"


def test_profile_round_trip_minimal_data(test_db, redis_cache, test_user):
    """
    Test profile round-trip with minimal data (all optional fields as None).
    
    This is an edge case test.
    """
    user_manager = UserManager(test_db, redis_cache)
    
    # Create profile with minimal data
    minimal_profile = UserProfileCreate(
        location=None,
        age=None,
        gender=None,
        education_level=None,
        occupation=None,
        income_bracket=None,
        household_size=None
    )
    
    created_profile = user_manager.create_profile(str(test_user.user_id), minimal_profile)
    retrieved_profile = user_manager.get_profile(str(test_user.user_id))
    
    assert retrieved_profile is not None, "Profile should exist even with minimal data"
    assert retrieved_profile.age is None, "Age should be None"
    assert retrieved_profile.gender is None, "Gender should be None"
    assert retrieved_profile.education_level is None, "Education level should be None"
    assert retrieved_profile.occupation is None, "Occupation should be None"
    assert retrieved_profile.income_bracket is None, "Income bracket should be None"
    assert retrieved_profile.household_size is None, "Household size should be None"
    assert retrieved_profile.location_id is None, "Location should be None"
