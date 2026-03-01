"""Unit tests for Pydantic data models."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from src.models import (
    EligibilityCriteria,
    Location,
    Scheme,
    UserPreferences,
    UserProfile,
)


class TestLocation:
    """Test Location model."""
    
    def test_valid_location(self):
        """Test creating a valid location."""
        location = Location(
            state="Maharashtra",
            district="Pune",
            pincode="411014",
            latitude=18.5511,
            longitude=73.9467
        )
        assert location.state == "Maharashtra"
        assert location.district == "Pune"
        assert location.pincode == "411014"
    
    def test_invalid_pincode(self):
        """Test that invalid pincode raises validation error."""
        with pytest.raises(ValidationError):
            Location(
                state="Maharashtra",
                district="Pune",
                pincode="12345"  # Only 5 digits
            )
    
    def test_invalid_latitude(self):
        """Test that invalid latitude raises validation error."""
        with pytest.raises(ValidationError):
            Location(
                state="Maharashtra",
                district="Pune",
                pincode="411014",
                latitude=100.0  # Out of range
            )
    
    def test_location_serialization(self):
        """Test location serialization to dict."""
        location = Location(
            state="Maharashtra",
            district="Pune",
            pincode="411014"
        )
        data = location.model_dump()
        assert data["state"] == "Maharashtra"
        assert data["district"] == "Pune"
        assert data["pincode"] == "411014"
    
    def test_location_deserialization(self):
        """Test location deserialization from dict."""
        data = {
            "state": "Karnataka",
            "district": "Bangalore",
            "pincode": "560001"
        }
        location = Location(**data)
        assert location.state == "Karnataka"
        assert location.district == "Bangalore"


class TestEligibilityCriteria:
    """Test EligibilityCriteria model."""
    
    def test_valid_criteria(self):
        """Test creating valid eligibility criteria."""
        criteria = EligibilityCriteria(
            age_min=18,
            age_max=35,
            income_max=300000,
            gender="any",
            occupation=["farmer", "agricultural_worker"]
        )
        assert criteria.age_min == 18
        assert criteria.age_max == 35
        assert criteria.income_max == 300000
    
    def test_empty_criteria(self):
        """Test creating criteria with no requirements."""
        criteria = EligibilityCriteria()
        assert criteria.age_min is None
        assert criteria.age_max is None
        assert criteria.custom_criteria == {}
    
    def test_custom_criteria(self):
        """Test custom criteria field."""
        criteria = EligibilityCriteria(
            custom_criteria={
                "land_ownership": "yes",
                "household_size": {"min": 2, "max": 8}
            }
        )
        assert criteria.custom_criteria["land_ownership"] == "yes"
        assert criteria.custom_criteria["household_size"]["min"] == 2


class TestScheme:
    """Test Scheme model."""
    
    def test_valid_scheme(self):
        """Test creating a valid scheme."""
        criteria = EligibilityCriteria(age_min=18, occupation=["farmer"])
        scheme = Scheme(
            scheme_id="PM-KISAN-2024",
            name="PM Kisan Samman Nidhi",
            category="agriculture",
            description="Income support for farmers",
            eligibility_criteria=criteria,
            department="Ministry of Agriculture",
            last_updated=datetime.utcnow(),
            source_url="https://pmkisan.gov.in"
        )
        assert scheme.scheme_id == "PM-KISAN-2024"
        assert scheme.category == "agriculture"
        assert scheme.eligibility_criteria.age_min == 18
    
    def test_scheme_with_translations(self):
        """Test scheme with name translations."""
        criteria = EligibilityCriteria()
        scheme = Scheme(
            scheme_id="TEST-001",
            name="Test Scheme",
            name_translations={"hi": "परीक्षण योजना", "mr": "चाचणी योजना"},
            category="education",
            description="Test description",
            eligibility_criteria=criteria,
            department="Test Department",
            last_updated=datetime.utcnow(),
            source_url="https://example.com"
        )
        assert scheme.name_translations["hi"] == "परीक्षण योजना"
        assert scheme.name_translations["mr"] == "चाचणी योजना"
    
    def test_scheme_serialization(self):
        """Test scheme serialization."""
        criteria = EligibilityCriteria(age_min=18)
        scheme = Scheme(
            scheme_id="TEST-001",
            name="Test Scheme",
            category="health",
            description="Test",
            eligibility_criteria=criteria,
            department="Test Dept",
            last_updated=datetime.utcnow(),
            source_url="https://example.com"
        )
        data = scheme.model_dump()
        assert data["scheme_id"] == "TEST-001"
        assert data["category"] == "health"
        assert "eligibility_criteria" in data


class TestUserProfile:
    """Test UserProfile model."""
    
    def test_valid_user_profile(self):
        """Test creating a valid user profile."""
        location = Location(
            state="Maharashtra",
            district="Pune",
            pincode="411014"
        )
        profile = UserProfile(
            user_id="user_123",
            phone_number="+919876543210",
            language="hi",
            location=location,
            age=35,
            gender="male",
            education_level="secondary",
            occupation="farmer"
        )
        assert profile.user_id == "user_123"
        assert profile.phone_number == "+919876543210"
        assert profile.age == 35
    
    def test_phone_number_validation(self):
        """Test phone number validation."""
        location = Location(state="Test", district="Test", pincode="123456")
        
        # Valid phone number with country code
        profile = UserProfile(
            user_id="user_123",
            phone_number="+919876543210",
            language="hi",
            location=location
        )
        assert profile.phone_number == "+919876543210"
        
        # Valid phone number without country code
        profile2 = UserProfile(
            user_id="user_124",
            phone_number="9876543210",
            language="hi",
            location=location
        )
        assert profile2.phone_number == "9876543210"
    
    def test_invalid_phone_number(self):
        """Test that invalid phone number raises error."""
        location = Location(state="Test", district="Test", pincode="123456")
        
        with pytest.raises(ValidationError):
            UserProfile(
                user_id="user_123",
                phone_number="123",  # Too short
                language="hi",
                location=location
            )
    
    def test_gender_validation(self):
        """Test gender validation."""
        location = Location(state="Test", district="Test", pincode="123456")
        
        # Valid gender
        profile = UserProfile(
            user_id="user_123",
            phone_number="+919876543210",
            language="hi",
            location=location,
            gender="female"
        )
        assert profile.gender == "female"
        
        # Invalid gender
        with pytest.raises(ValidationError):
            UserProfile(
                user_id="user_123",
                phone_number="+919876543210",
                language="hi",
                location=location,
                gender="invalid"
            )
    
    def test_education_level_validation(self):
        """Test education level validation."""
        location = Location(state="Test", district="Test", pincode="123456")
        
        # Valid education level
        profile = UserProfile(
            user_id="user_123",
            phone_number="+919876543210",
            language="hi",
            location=location,
            education_level="graduate"
        )
        assert profile.education_level == "graduate"
        
        # Invalid education level
        with pytest.raises(ValidationError):
            UserProfile(
                user_id="user_123",
                phone_number="+919876543210",
                language="hi",
                location=location,
                education_level="invalid_level"
            )
    
    def test_user_profile_serialization(self):
        """Test user profile serialization."""
        location = Location(state="Test", district="Test", pincode="123456")
        profile = UserProfile(
            user_id="user_123",
            phone_number="+919876543210",
            language="hi",
            location=location
        )
        data = profile.model_dump()
        assert data["user_id"] == "user_123"
        assert data["phone_number"] == "+919876543210"
        assert "location" in data
        assert "preferences" in data
    
    def test_user_profile_deserialization(self):
        """Test user profile deserialization."""
        data = {
            "user_id": "user_456",
            "phone_number": "+919876543210",
            "language": "en",
            "location": {
                "state": "Karnataka",
                "district": "Bangalore",
                "pincode": "560001"
            },
            "age": 28,
            "gender": "female",
            "education_level": "graduate"
        }
        profile = UserProfile(**data)
        assert profile.user_id == "user_456"
        assert profile.age == 28
        assert profile.location.state == "Karnataka"


class TestUserPreferences:
    """Test UserPreferences model."""
    
    def test_default_preferences(self):
        """Test default preference values."""
        prefs = UserPreferences()
        assert prefs.notification_enabled is True
        assert prefs.voice_enabled is True
        assert prefs.data_sharing_consent is False
        assert prefs.preferred_categories == []
    
    def test_custom_preferences(self):
        """Test custom preference values."""
        prefs = UserPreferences(
            notification_enabled=False,
            preferred_categories=["agriculture", "health"],
            voice_enabled=False,
            data_sharing_consent=True
        )
        assert prefs.notification_enabled is False
        assert len(prefs.preferred_categories) == 2
        assert prefs.data_sharing_consent is True
