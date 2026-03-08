"""Property-based tests for user profile data round-trip.

Feature: bharatsahayak, Property 20: Profile Data Round-Trip
**Validates: Requirements 8.1**

This test verifies that storing and retrieving user profiles preserves all fields,
ensuring data integrity through the complete storage and retrieval cycle.
"""

import pytest
from hypothesis import given, settings, strategies as st, HealthCheck
from datetime import datetime
from moto import mock_aws
import boto3
from contextlib import contextmanager

from src.core.profile_repository import ProfileRepository
from src.models.user import UserProfile, UserPreferences
from src.models.location import Location


@contextmanager
def create_dynamodb_table():
    """Context manager to create a mock DynamoDB table for user profiles."""
    with mock_aws():
        # Create DynamoDB resource
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        
        # Create UserProfiles table
        table = dynamodb.create_table(
            TableName='UserProfiles',
            KeySchema=[
                {'AttributeName': 'user_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'user_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        yield table


# Custom strategies for generating valid test data
@st.composite
def location_strategy(draw):
    """Generate valid Location instances."""
    states = ["Maharashtra", "Karnataka", "Tamil Nadu", "Gujarat", "Rajasthan", "Punjab"]
    districts = ["Pune", "Mumbai", "Bangalore", "Chennai", "Ahmedabad", "Jaipur"]
    blocks = ["Haveli", "Kurla", "Whitefield", "T Nagar", None]
    villages = ["Kharadi", "Andheri", "Marathahalli", "Adyar", None]
    
    # Generate latitude/longitude with reasonable precision to avoid DynamoDB decimal underflow
    # Use None or values with at least 6 decimal places precision
    lat = draw(st.none() | st.floats(
        min_value=8.0, max_value=37.0,  # India's latitude range
        allow_nan=False, allow_infinity=False
    ).map(lambda x: round(x, 6)))
    
    lon = draw(st.none() | st.floats(
        min_value=68.0, max_value=97.0,  # India's longitude range
        allow_nan=False, allow_infinity=False
    ).map(lambda x: round(x, 6)))
    
    return Location(
        state=draw(st.sampled_from(states)),
        district=draw(st.sampled_from(districts)),
        block=draw(st.sampled_from(blocks)),
        village=draw(st.sampled_from(villages)),
        pincode=draw(st.from_regex(r"^\d{6}$", fullmatch=True)),
        latitude=lat,
        longitude=lon
    )


@st.composite
def user_preferences_strategy(draw):
    """Generate valid UserPreferences instances."""
    categories = ["agriculture", "health", "education", "employment", "social_welfare"]
    
    return UserPreferences(
        notification_enabled=draw(st.booleans()),
        preferred_categories=draw(st.lists(st.sampled_from(categories), max_size=3)),
        voice_enabled=draw(st.booleans()),
        data_sharing_consent=draw(st.booleans())
    )


@st.composite
def user_profile_strategy(draw):
    """Generate valid UserProfile instances with various combinations of optional fields."""
    # Generate base required fields
    user_id = f"user_{draw(st.integers(min_value=100000, max_value=999999))}"
    
    # Phone number: either with +91 prefix or 10 digits
    phone_with_prefix = draw(st.booleans())
    if phone_with_prefix:
        phone_number = f"+91{draw(st.integers(min_value=6000000000, max_value=9999999999))}"
    else:
        phone_number = f"{draw(st.integers(min_value=6000000000, max_value=9999999999))}"
    
    language = draw(st.sampled_from(["hi", "en", "bn", "te", "mr", "ta", "gu", "kn"]))
    location = draw(location_strategy())
    
    # Optional fields - some may be None
    age = draw(st.none() | st.integers(min_value=18, max_value=100))
    gender = draw(st.none() | st.sampled_from(["male", "female", "other"]))
    education_level = draw(st.none() | st.sampled_from([
        "illiterate", "primary", "secondary", "higher_secondary",
        "graduate", "postgraduate", "diploma", "vocational"
    ]))
    occupation = draw(st.none() | st.sampled_from([
        "farmer", "laborer", "shopkeeper", "teacher", "student", "unemployed"
    ]))
    income_bracket = draw(st.none() | st.sampled_from([
        "0-100000", "100000-300000", "300000-500000", "500000-1000000"
    ]))
    household_size = draw(st.none() | st.integers(min_value=1, max_value=15))
    
    preferences = draw(user_preferences_strategy())
    
    # Use fixed timestamps for deterministic comparison
    created_at = datetime(2024, 1, 1, 0, 0, 0)
    updated_at = datetime(2024, 1, 1, 0, 0, 0)
    
    return UserProfile(
        user_id=user_id,
        phone_number=phone_number,
        language=language,
        location=location,
        age=age,
        gender=gender,
        education_level=education_level,
        occupation=occupation,
        income_bracket=income_bracket,
        household_size=household_size,
        preferences=preferences,
        created_at=created_at,
        updated_at=updated_at
    )


@settings(max_examples=5, deadline=None)
@given(profile=user_profile_strategy())
def test_profile_data_roundtrip(profile):
    """
    Feature: bharatsahayak, Property 20: Profile Data Round-Trip
    
    For any user profile data, storing the profile and then retrieving it
    should return an equivalent profile with all fields preserved.
    
    This test verifies:
    1. All required fields are preserved (user_id, phone_number, language, location)
    2. All optional fields are preserved (age, gender, education_level, etc.)
    3. Nested objects (location, preferences) are preserved correctly
    4. None values in optional fields are handled correctly
    """
    with create_dynamodb_table():
        # Create repository with the mocked DynamoDB table
        repo = ProfileRepository(table_name="UserProfiles", region_name="us-east-1")
        
        # Store the profile
        created_profile = repo.create_profile(profile)
        
        # Retrieve the profile
        retrieved_profile = repo.get_profile(profile.user_id)
        
        # Verify all required fields are preserved
        assert retrieved_profile.user_id == profile.user_id
        assert retrieved_profile.phone_number == profile.phone_number
        assert retrieved_profile.language == profile.language
        
        # Verify location fields
        assert retrieved_profile.location.state == profile.location.state
        assert retrieved_profile.location.district == profile.location.district
        assert retrieved_profile.location.block == profile.location.block
        assert retrieved_profile.location.village == profile.location.village
        assert retrieved_profile.location.pincode == profile.location.pincode
        
        # Handle floating point comparison for coordinates
        if profile.location.latitude is not None:
            assert retrieved_profile.location.latitude == pytest.approx(profile.location.latitude, abs=1e-6)
        else:
            assert retrieved_profile.location.latitude is None
        
        if profile.location.longitude is not None:
            assert retrieved_profile.location.longitude == pytest.approx(profile.location.longitude, abs=1e-6)
        else:
            assert retrieved_profile.location.longitude is None
        
        # Verify optional fields
        assert retrieved_profile.age == profile.age
        assert retrieved_profile.gender == profile.gender
        assert retrieved_profile.education_level == profile.education_level
        assert retrieved_profile.occupation == profile.occupation
        assert retrieved_profile.income_bracket == profile.income_bracket
        assert retrieved_profile.household_size == profile.household_size
        
        # Verify preferences
        assert retrieved_profile.preferences.notification_enabled == profile.preferences.notification_enabled
        assert retrieved_profile.preferences.preferred_categories == profile.preferences.preferred_categories
        assert retrieved_profile.preferences.voice_enabled == profile.preferences.voice_enabled
        assert retrieved_profile.preferences.data_sharing_consent == profile.preferences.data_sharing_consent
        
        # Verify timestamps (should be preserved exactly)
        assert retrieved_profile.created_at == profile.created_at
        assert retrieved_profile.updated_at == profile.updated_at


@settings(max_examples=3, deadline=None)
@given(profile=user_profile_strategy())
def test_profile_roundtrip_with_update(profile):
    """
    Test round-trip with profile updates to ensure updated fields are preserved.
    
    This verifies that the update operation also maintains data integrity.
    """
    with create_dynamodb_table():
        # Create repository with the mocked DynamoDB table
        repo = ProfileRepository(table_name="UserProfiles", region_name="us-east-1")
        
        # Create initial profile
        repo.create_profile(profile)
        
        # Update some fields
        updates = {
            'age': 40 if profile.age else 30,
            'occupation': 'teacher'
        }
        
        # Perform update
        updated = repo.update_profile(profile.user_id, updates)
        
        # Verify updated fields
        assert updated.age == updates['age']
        assert updated.occupation == updates['occupation']
        
        # Verify other fields remain unchanged
        assert updated.user_id == profile.user_id
        assert updated.phone_number == profile.phone_number
        assert updated.language == profile.language
        assert updated.location.state == profile.location.state
        
        # Retrieve the profile again to verify persistence
        retrieved = repo.get_profile(profile.user_id)
        
        # Verify the updates persisted
        assert retrieved.age == updates['age']
        assert retrieved.occupation == updates['occupation']
        
        # Verify unchanged fields are still correct
        assert retrieved.user_id == profile.user_id
        assert retrieved.phone_number == profile.phone_number
        assert retrieved.language == profile.language
