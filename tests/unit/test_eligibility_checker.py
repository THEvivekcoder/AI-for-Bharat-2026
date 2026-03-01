"""Unit tests for EligibilityChecker class."""

import pytest
from datetime import datetime

from src.core.eligibility_checker import EligibilityChecker, EligibilityResult
from src.models.user import UserProfile, UserPreferences
from src.models.scheme import Scheme
from src.models.eligibility import EligibilityCriteria
from src.models.location import Location


@pytest.fixture
def eligibility_checker():
    """Create an EligibilityChecker instance."""
    return EligibilityChecker()


@pytest.fixture
def sample_user_profile():
    """Create a sample user profile for testing."""
    return UserProfile(
        user_id="test_user_123",
        phone_number="+919876543210",
        language="hi",
        location=Location(
            state="Maharashtra",
            district="Pune",
            pincode="411014"
        ),
        age=35,
        gender="male",
        education_level="secondary",
        occupation="farmer",
        income_bracket="100000-300000",
        household_size=5
    )


@pytest.fixture
def sample_scheme():
    """Create a sample scheme for testing."""
    return Scheme(
        scheme_id="TEST-SCHEME-001",
        name="Test Farmer Scheme",
        category="agriculture",
        description="Test scheme for farmers",
        eligibility_criteria=EligibilityCriteria(
            age_min=18,
            age_max=60,
            income_max=500000,
            occupation=["farmer", "agricultural_worker"],
            location=["Maharashtra", "Karnataka"]
        ),
        department="Test Department",
        last_updated=datetime.utcnow(),
        source_url="https://example.com"
    )


class TestAgeEligibility:
    """Test age-based eligibility checking."""
    
    def test_age_within_range(self, eligibility_checker, sample_user_profile, sample_scheme):
        """Test user age within eligible range."""
        result = eligibility_checker.check_eligibility(sample_user_profile, sample_scheme)
        
        assert result.is_eligible is True
        assert any("Age 35 meets requirement" in reason for reason in result.reasoning)
        assert result.confidence == 1.0
    
    def test_age_below_minimum(self, eligibility_checker, sample_user_profile, sample_scheme):
        """Test user age below minimum requirement."""
        sample_user_profile.age = 15
        result = eligibility_checker.check_eligibility(sample_user_profile, sample_scheme)
        
        assert result.is_eligible is False
        assert any("below minimum requirement of 18" in reason for reason in result.reasoning)
    
    def test_age_above_maximum(self, eligibility_checker, sample_user_profile, sample_scheme):
        """Test user age above maximum limit."""
        sample_user_profile.age = 65
        result = eligibility_checker.check_eligibility(sample_user_profile, sample_scheme)
        
        assert result.is_eligible is False
        assert any("exceeds maximum limit of 60" in reason for reason in result.reasoning)
    
    def test_age_at_boundary_minimum(self, eligibility_checker, sample_user_profile, sample_scheme):
        """Test user age exactly at minimum boundary."""
        sample_user_profile.age = 18
        result = eligibility_checker.check_eligibility(sample_user_profile, sample_scheme)
        
        assert result.is_eligible is True
    
    def test_age_at_boundary_maximum(self, eligibility_checker, sample_user_profile, sample_scheme):
        """Test user age exactly at maximum boundary."""
        sample_user_profile.age = 60
        result = eligibility_checker.check_eligibility(sample_user_profile, sample_scheme)
        
        assert result.is_eligible is True
    
    def test_missing_age_with_criteria(self, eligibility_checker, sample_user_profile, sample_scheme):
        """Test missing user age when scheme has age criteria."""
        sample_user_profile.age = None
        result = eligibility_checker.check_eligibility(sample_user_profile, sample_scheme)
        
        assert result.is_eligible is False
        assert len(result.missing_criteria) > 0
        assert any("Age information required" in criterion for criterion in result.missing_criteria)
        assert result.confidence < 1.0
    
    def test_no_age_criteria(self, eligibility_checker, sample_user_profile, sample_scheme):
        """Test when scheme has no age criteria."""
        sample_scheme.eligibility_criteria.age_min = None
        sample_scheme.eligibility_criteria.age_max = None
        
        result = eligibility_checker.check_eligibility(sample_user_profile, sample_scheme)
        
        assert result.is_eligible is True


class TestIncomeEligibility:
    """Test income-based eligibility checking."""
    
    def test_income_within_limit(self, eligibility_checker, sample_user_profile, sample_scheme):
        """Test user income within limit."""
        result = eligibility_checker.check_eligibility(sample_user_profile, sample_scheme)
        
        assert result.is_eligible is True
        assert any("within limit" in reason for reason in result.reasoning)
    
    def test_income_exceeds_limit(self, eligibility_checker, sample_user_profile, sample_scheme):
        """Test user income exceeds limit."""
        sample_user_profile.income_bracket = "500001-1000000"
        result = eligibility_checker.check_eligibility(sample_user_profile, sample_scheme)
        
        assert result.is_eligible is False
        assert any("exceeds maximum limit" in reason for reason in result.reasoning)
    
    def test_income_at_boundary(self, eligibility_checker, sample_user_profile, sample_scheme):
        """Test user income exactly at limit."""
        sample_user_profile.income_bracket = "400000-500000"
        result = eligibility_checker.check_eligibility(sample_user_profile, sample_scheme)
        
        assert result.is_eligible is True
    
    def test_income_plus_format(self, eligibility_checker, sample_user_profile, sample_scheme):
        """Test income bracket with plus format (e.g., '300000+')."""
        sample_user_profile.income_bracket = "300000+"
        result = eligibility_checker.check_eligibility(sample_user_profile, sample_scheme)
        
        assert result.is_eligible is True
    
    def test_missing_income_with_criteria(self, eligibility_checker, sample_user_profile, sample_scheme):
        """Test missing user income when scheme has income criteria."""
        sample_user_profile.income_bracket = None
        result = eligibility_checker.check_eligibility(sample_user_profile, sample_scheme)
        
        assert result.is_eligible is False
        assert len(result.missing_criteria) > 0
        assert any("Income information required" in criterion for criterion in result.missing_criteria)
    
    def test_no_income_criteria(self, eligibility_checker, sample_user_profile, sample_scheme):
        """Test when scheme has no income criteria."""
        sample_scheme.eligibility_criteria.income_max = None
        
        result = eligibility_checker.check_eligibility(sample_user_profile, sample_scheme)
        
        assert result.is_eligible is True


class TestOccupationEligibility:
    """Test occupation-based eligibility checking."""
    
    def test_occupation_matches(self, eligibility_checker, sample_user_profile, sample_scheme):
        """Test user occupation matches eligible list."""
        result = eligibility_checker.check_eligibility(sample_user_profile, sample_scheme)
        
        assert result.is_eligible is True
        assert any("Occupation 'farmer' is eligible" in reason for reason in result.reasoning)
    
    def test_occupation_not_eligible(self, eligibility_checker, sample_user_profile, sample_scheme):
        """Test user occupation not in eligible list."""
        sample_user_profile.occupation = "teacher"
        result = eligibility_checker.check_eligibility(sample_user_profile, sample_scheme)
        
        assert result.is_eligible is False
        assert any("not eligible" in reason for reason in result.reasoning)
    
    def test_occupation_case_insensitive(self, eligibility_checker, sample_user_profile, sample_scheme):
        """Test occupation matching is case-insensitive."""
        sample_user_profile.occupation = "FARMER"
        result = eligibility_checker.check_eligibility(sample_user_profile, sample_scheme)
        
        assert result.is_eligible is True
    
    def test_missing_occupation_with_criteria(self, eligibility_checker, sample_user_profile, sample_scheme):
        """Test missing user occupation when scheme has occupation criteria."""
        sample_user_profile.occupation = None
        result = eligibility_checker.check_eligibility(sample_user_profile, sample_scheme)
        
        assert result.is_eligible is False
        assert len(result.missing_criteria) > 0
        assert any("Occupation information required" in criterion for criterion in result.missing_criteria)
    
    def test_no_occupation_criteria(self, eligibility_checker, sample_user_profile, sample_scheme):
        """Test when scheme has no occupation criteria."""
        sample_scheme.eligibility_criteria.occupation = None
        
        result = eligibility_checker.check_eligibility(sample_user_profile, sample_scheme)
        
        assert result.is_eligible is True


class TestLocationEligibility:
    """Test location-based eligibility checking."""
    
    def test_location_state_matches(self, eligibility_checker, sample_user_profile, sample_scheme):
        """Test user state matches eligible locations."""
        result = eligibility_checker.check_eligibility(sample_user_profile, sample_scheme)
        
        assert result.is_eligible is True
        assert any("Location Maharashtra is eligible" in reason for reason in result.reasoning)
    
    def test_location_not_eligible(self, eligibility_checker, sample_user_profile, sample_scheme):
        """Test user location not in eligible list."""
        sample_user_profile.location.state = "Tamil Nadu"
        result = eligibility_checker.check_eligibility(sample_user_profile, sample_scheme)
        
        assert result.is_eligible is False
        assert any("not eligible" in reason for reason in result.reasoning)
    
    def test_location_state_district_match(self, eligibility_checker, sample_user_profile, sample_scheme):
        """Test state/district combination matching."""
        sample_scheme.eligibility_criteria.location = ["Maharashtra/Pune", "Karnataka/Bangalore"]
        result = eligibility_checker.check_eligibility(sample_user_profile, sample_scheme)
        
        assert result.is_eligible is True
    
    def test_location_case_insensitive(self, eligibility_checker, sample_user_profile, sample_scheme):
        """Test location matching is case-insensitive."""
        sample_scheme.eligibility_criteria.location = ["maharashtra", "karnataka"]
        result = eligibility_checker.check_eligibility(sample_user_profile, sample_scheme)
        
        assert result.is_eligible is True
    
    def test_no_location_criteria(self, eligibility_checker, sample_user_profile, sample_scheme):
        """Test when scheme has no location criteria (available everywhere)."""
        sample_scheme.eligibility_criteria.location = None
        
        result = eligibility_checker.check_eligibility(sample_user_profile, sample_scheme)
        
        assert result.is_eligible is True


class TestEducationEligibility:
    """Test education-based eligibility checking."""
    
    def test_education_matches(self, eligibility_checker, sample_user_profile, sample_scheme):
        """Test user education matches eligible list."""
        sample_scheme.eligibility_criteria.education = ["primary", "secondary", "higher_secondary"]
        result = eligibility_checker.check_eligibility(sample_user_profile, sample_scheme)
        
        assert result.is_eligible is True
        assert any("Education level 'secondary' is eligible" in reason for reason in result.reasoning)
    
    def test_education_not_eligible(self, eligibility_checker, sample_user_profile, sample_scheme):
        """Test user education not in eligible list."""
        sample_scheme.eligibility_criteria.education = ["graduate", "postgraduate"]
        result = eligibility_checker.check_eligibility(sample_user_profile, sample_scheme)
        
        assert result.is_eligible is False
        assert any("not eligible" in reason for reason in result.reasoning)
    
    def test_missing_education_with_criteria(self, eligibility_checker, sample_user_profile, sample_scheme):
        """Test missing user education when scheme has education criteria."""
        sample_user_profile.education_level = None
        sample_scheme.eligibility_criteria.education = ["secondary", "graduate"]
        result = eligibility_checker.check_eligibility(sample_user_profile, sample_scheme)
        
        assert result.is_eligible is False
        assert len(result.missing_criteria) > 0
        assert any("Education information required" in criterion for criterion in result.missing_criteria)
    
    def test_no_education_criteria(self, eligibility_checker, sample_user_profile, sample_scheme):
        """Test when scheme has no education criteria."""
        sample_scheme.eligibility_criteria.education = None
        
        result = eligibility_checker.check_eligibility(sample_user_profile, sample_scheme)
        
        assert result.is_eligible is True


class TestGenderEligibility:
    """Test gender-based eligibility checking."""
    
    def test_gender_matches(self, eligibility_checker, sample_user_profile, sample_scheme):
        """Test user gender matches requirement."""
        sample_scheme.eligibility_criteria.gender = "male"
        result = eligibility_checker.check_eligibility(sample_user_profile, sample_scheme)
        
        assert result.is_eligible is True
        assert any("Gender 'male' is eligible" in reason for reason in result.reasoning)
    
    def test_gender_not_eligible(self, eligibility_checker, sample_user_profile, sample_scheme):
        """Test user gender doesn't match requirement."""
        sample_scheme.eligibility_criteria.gender = "female"
        result = eligibility_checker.check_eligibility(sample_user_profile, sample_scheme)
        
        assert result.is_eligible is False
        assert any("not eligible" in reason for reason in result.reasoning)
    
    def test_gender_any(self, eligibility_checker, sample_user_profile, sample_scheme):
        """Test gender requirement is 'any'."""
        sample_scheme.eligibility_criteria.gender = "any"
        result = eligibility_checker.check_eligibility(sample_user_profile, sample_scheme)
        
        assert result.is_eligible is True
    
    def test_missing_gender_with_criteria(self, eligibility_checker, sample_user_profile, sample_scheme):
        """Test missing user gender when scheme has gender criteria."""
        sample_user_profile.gender = None
        sample_scheme.eligibility_criteria.gender = "male"
        result = eligibility_checker.check_eligibility(sample_user_profile, sample_scheme)
        
        assert result.is_eligible is False
        assert len(result.missing_criteria) > 0
        assert any("Gender information required" in criterion for criterion in result.missing_criteria)
    
    def test_no_gender_criteria(self, eligibility_checker, sample_user_profile, sample_scheme):
        """Test when scheme has no gender criteria."""
        sample_scheme.eligibility_criteria.gender = None
        
        result = eligibility_checker.check_eligibility(sample_user_profile, sample_scheme)
        
        assert result.is_eligible is True


class TestCombinedCriteria:
    """Test combinations of multiple criteria."""
    
    def test_all_criteria_met(self, eligibility_checker, sample_user_profile, sample_scheme):
        """Test user meets all eligibility criteria."""
        result = eligibility_checker.check_eligibility(sample_user_profile, sample_scheme)
        
        assert result.is_eligible is True
        assert len(result.reasoning) > 0
        assert len(result.missing_criteria) == 0
        assert result.confidence == 1.0
    
    def test_one_criterion_fails(self, eligibility_checker, sample_user_profile, sample_scheme):
        """Test user fails one criterion."""
        sample_user_profile.age = 70  # Exceeds max age
        result = eligibility_checker.check_eligibility(sample_user_profile, sample_scheme)
        
        assert result.is_eligible is False
    
    def test_multiple_criteria_fail(self, eligibility_checker, sample_user_profile, sample_scheme):
        """Test user fails multiple criteria."""
        sample_user_profile.age = 70  # Exceeds max age
        sample_user_profile.occupation = "teacher"  # Not eligible occupation
        result = eligibility_checker.check_eligibility(sample_user_profile, sample_scheme)
        
        assert result.is_eligible is False
        assert len([r for r in result.reasoning if "not eligible" in r.lower() or "exceeds" in r.lower()]) >= 2
    
    def test_missing_multiple_fields(self, eligibility_checker, sample_user_profile, sample_scheme):
        """Test multiple missing profile fields."""
        sample_user_profile.age = None
        sample_user_profile.occupation = None
        result = eligibility_checker.check_eligibility(sample_user_profile, sample_scheme)
        
        assert result.is_eligible is False
        assert len(result.missing_criteria) >= 2
        assert result.confidence < 1.0


class TestConfidenceCalculation:
    """Test confidence score calculation."""
    
    def test_full_confidence_all_data(self, eligibility_checker, sample_user_profile, sample_scheme):
        """Test full confidence when all data is present."""
        result = eligibility_checker.check_eligibility(sample_user_profile, sample_scheme)
        
        assert result.confidence == 1.0
    
    def test_reduced_confidence_missing_data(self, eligibility_checker, sample_user_profile, sample_scheme):
        """Test reduced confidence when data is missing."""
        sample_user_profile.age = None
        result = eligibility_checker.check_eligibility(sample_user_profile, sample_scheme)
        
        assert result.confidence < 1.0
        assert result.confidence >= 0.0
    
    def test_confidence_bounds(self, eligibility_checker, sample_user_profile, sample_scheme):
        """Test confidence stays within 0-1 bounds."""
        # Create scheme with many criteria
        sample_scheme.eligibility_criteria.education = ["secondary"]
        sample_scheme.eligibility_criteria.gender = "male"
        
        # Remove all user data
        sample_user_profile.age = None
        sample_user_profile.occupation = None
        sample_user_profile.education_level = None
        sample_user_profile.gender = None
        sample_user_profile.income_bracket = None
        
        result = eligibility_checker.check_eligibility(sample_user_profile, sample_scheme)
        
        assert 0.0 <= result.confidence <= 1.0
