"""Property-based tests for eligibility determination correctness.

Feature: bharatsahayak, Property 6: Eligibility Determination Correctness
**Validates: Requirements 2.3**

This test verifies that eligibility is determined correctly for all criteria
combinations, ensuring that the EligibilityChecker returns "eligible" if and
only if the user profile satisfies all criteria in the scheme's eligibility_criteria.
"""

import pytest
from hypothesis import given, settings, strategies as st, assume, HealthCheck
from datetime import datetime

from src.core.eligibility_checker import EligibilityChecker
from src.models.user import UserProfile
from src.models.scheme import Scheme
from src.models.eligibility import EligibilityCriteria
from src.models.location import Location


# Custom strategies for generating valid test data
@st.composite
def location_strategy(draw):
    """Generate valid Location instances."""
    states = ["Maharashtra", "Karnataka", "Tamil Nadu", "Gujarat", "Rajasthan", "Punjab"]
    districts = {
        "Maharashtra": ["Pune", "Mumbai", "Nagpur"],
        "Karnataka": ["Bangalore", "Mysore", "Hubli"],
        "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai"],
        "Gujarat": ["Ahmedabad", "Surat", "Vadodara"],
        "Rajasthan": ["Jaipur", "Jodhpur", "Udaipur"],
        "Punjab": ["Ludhiana", "Amritsar", "Jalandhar"]
    }
    
    state = draw(st.sampled_from(states))
    district = draw(st.sampled_from(districts[state]))
    
    return Location(
        state=state,
        district=district,
        pincode=draw(st.text(min_size=6, max_size=6, alphabet=st.characters(whitelist_categories=('Nd',))))
    )


@st.composite
def user_profile_strategy(draw):
    """Generate valid UserProfile instances with all fields populated."""
    return UserProfile(
        user_id=f"user_{draw(st.integers(min_value=1000, max_value=9999))}",
        phone_number=f"+91{draw(st.integers(min_value=1000000000, max_value=9999999999))}",
        language=draw(st.sampled_from(["hi", "en", "mr", "ta", "gu"])),
        location=draw(location_strategy()),
        age=draw(st.integers(min_value=1, max_value=100)),
        gender=draw(st.sampled_from(["male", "female", "other"])),
        education_level=draw(st.sampled_from(["illiterate", "primary", "secondary", "higher_secondary", "graduate", "postgraduate"])),
        occupation=draw(st.sampled_from(["farmer", "laborer", "student", "unemployed", "teacher", "engineer", "doctor"])),
        income_bracket=draw(st.sampled_from([
            "0-100000", "100000-300000", "300000-500000", "500000-1000000", "1000000+"
        ])),
        household_size=draw(st.integers(min_value=1, max_value=15))
    )


@st.composite
def eligibility_criteria_strategy(draw):
    """Generate valid EligibilityCriteria instances."""
    # Generate age criteria
    has_age_criteria = draw(st.booleans())
    if has_age_criteria:
        age_min = draw(st.integers(min_value=0, max_value=80))
        age_max = draw(st.integers(min_value=age_min + 1, max_value=100))
    else:
        age_min = None
        age_max = None
    
    # Generate income criteria
    has_income_criteria = draw(st.booleans())
    income_max = draw(st.integers(min_value=100000, max_value=2000000)) if has_income_criteria else None
    
    # Generate occupation criteria
    has_occupation_criteria = draw(st.booleans())
    occupation = draw(st.lists(
        st.sampled_from(["farmer", "laborer", "student", "unemployed", "teacher"]),
        min_size=1, max_size=3, unique=True
    )) if has_occupation_criteria else None
    
    # Generate location criteria
    has_location_criteria = draw(st.booleans())
    location = draw(st.lists(
        st.sampled_from(["Maharashtra", "Karnataka", "Tamil Nadu", "Maharashtra/Pune", "Karnataka/Bangalore"]),
        min_size=1, max_size=3, unique=True
    )) if has_location_criteria else None
    
    # Generate education criteria
    has_education_criteria = draw(st.booleans())
    education = draw(st.lists(
        st.sampled_from(["illiterate", "primary", "secondary", "higher_secondary", "graduate"]),
        min_size=1, max_size=3, unique=True
    )) if has_education_criteria else None
    
    # Generate gender criteria
    has_gender_criteria = draw(st.booleans())
    gender = draw(st.sampled_from(["male", "female", "other", "any"])) if has_gender_criteria else None
    
    return EligibilityCriteria(
        age_min=age_min,
        age_max=age_max,
        income_max=income_max,
        gender=gender,
        occupation=occupation,
        education=education,
        location=location,
        caste=None,  # Not testing caste criteria in this property test
        custom_criteria={}
    )


@st.composite
def scheme_strategy(draw):
    """Generate valid Scheme instances."""
    return Scheme(
        scheme_id=f"SCHEME-{draw(st.integers(min_value=1000, max_value=9999))}",
        name=draw(st.text(min_size=10, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N', 'Zs')))),
        name_translations={},
        category=draw(st.sampled_from(["agriculture", "health", "education", "employment", "social_welfare"])),
        description=draw(st.text(min_size=20, max_size=100, alphabet=st.characters(whitelist_categories=('L', 'N', 'Zs')))),
        description_translations={},
        benefits=["Benefit 1", "Benefit 2"],
        eligibility_criteria=draw(eligibility_criteria_strategy()),
        required_documents=["Aadhaar", "Income Certificate"],
        application_process=["Step 1", "Step 2"],
        application_url="https://example.gov.in/scheme",
        department="Test Department",
        state=None,
        last_updated=datetime(2024, 1, 15, 10, 30, 0),
        source_url="https://example.gov.in/source"
    )


def manually_check_eligibility(user_profile: UserProfile, criteria: EligibilityCriteria) -> bool:
    """
    Manually verify eligibility based on criteria.
    
    This is the oracle function that independently determines eligibility
    to verify the EligibilityChecker implementation.
    
    Returns True if user meets ALL criteria, False otherwise.
    """
    # Check age
    if criteria.age_min is not None or criteria.age_max is not None:
        if user_profile.age is None:
            return False
        if criteria.age_min is not None and user_profile.age < criteria.age_min:
            return False
        if criteria.age_max is not None and user_profile.age > criteria.age_max:
            return False
    
    # Check income
    if criteria.income_max is not None:
        if user_profile.income_bracket is None:
            return False
        
        # Parse income bracket
        try:
            if '-' in user_profile.income_bracket:
                parts = user_profile.income_bracket.split('-')
                user_income_upper = int(parts[1])
            elif '+' in user_profile.income_bracket:
                user_income_upper = int(user_profile.income_bracket.replace('+', ''))
            else:
                user_income_upper = int(user_profile.income_bracket)
            
            if user_income_upper > criteria.income_max:
                return False
        except (ValueError, IndexError):
            return False
    
    # Check occupation
    if criteria.occupation:
        if user_profile.occupation is None:
            return False
        user_occupation_lower = user_profile.occupation.lower()
        eligible_occupations_lower = [occ.lower() for occ in criteria.occupation]
        if user_occupation_lower not in eligible_occupations_lower:
            return False
    
    # Check location
    if criteria.location:
        user_state_lower = user_profile.location.state.lower()
        user_district_lower = user_profile.location.district.lower()
        
        location_match = False
        for location in criteria.location:
            location_lower = location.lower()
            
            # Check state match
            if location_lower == user_state_lower:
                location_match = True
                break
            
            # Check state/district match
            if '/' in location_lower:
                parts = location_lower.split('/')
                if len(parts) == 2:
                    loc_state, loc_district = parts[0].strip(), parts[1].strip()
                    if loc_state == user_state_lower and loc_district == user_district_lower:
                        location_match = True
                        break
        
        if not location_match:
            return False
    
    # Check education
    if criteria.education:
        if user_profile.education_level is None:
            return False
        user_education_lower = user_profile.education_level.lower()
        eligible_education_lower = [edu.lower() for edu in criteria.education]
        if user_education_lower not in eligible_education_lower:
            return False
    
    # Check gender
    if criteria.gender and criteria.gender.lower() != 'any':
        if user_profile.gender is None:
            return False
        if user_profile.gender.lower() != criteria.gender.lower():
            return False
    
    # All criteria passed
    return True


@settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.data_too_large])
@given(
    user_profile=user_profile_strategy(),
    scheme=scheme_strategy()
)
def test_eligibility_determination_correctness(user_profile, scheme):
    """
    Feature: bharatsahayak, Property 6: Eligibility Determination Correctness
    
    For any user profile and scheme, the Eligibility_Checker should return
    "eligible" if and only if the user profile satisfies all criteria in the
    scheme's eligibility_criteria, and "not eligible" otherwise.
    
    This test verifies:
    1. The checker returns is_eligible=True when all criteria are met
    2. The checker returns is_eligible=False when any criterion is not met
    3. The result is consistent with manual verification
    4. Missing user data is handled correctly (returns not eligible)
    """
    # Create eligibility checker instance
    eligibility_checker = EligibilityChecker()
    
    # Get the result from the eligibility checker
    result = eligibility_checker.check_eligibility(user_profile, scheme)
    
    # Manually verify eligibility
    expected_eligible = manually_check_eligibility(user_profile, scheme.eligibility_criteria)
    
    # Property verification: Result should match manual verification
    assert result.is_eligible == expected_eligible, (
        f"Eligibility mismatch for user {user_profile.user_id} and scheme {scheme.scheme_id}.\n"
        f"Expected: {expected_eligible}, Got: {result.is_eligible}\n"
        f"User: age={user_profile.age}, gender={user_profile.gender}, "
        f"occupation={user_profile.occupation}, education={user_profile.education_level}, "
        f"income={user_profile.income_bracket}, location={user_profile.location.state}/{user_profile.location.district}\n"
        f"Criteria: age_min={scheme.eligibility_criteria.age_min}, age_max={scheme.eligibility_criteria.age_max}, "
        f"income_max={scheme.eligibility_criteria.income_max}, gender={scheme.eligibility_criteria.gender}, "
        f"occupation={scheme.eligibility_criteria.occupation}, education={scheme.eligibility_criteria.education}, "
        f"location={scheme.eligibility_criteria.location}\n"
        f"Reasoning: {result.reasoning}\n"
        f"Missing criteria: {result.missing_criteria}"
    )
    
    # Additional verification: If eligible, there should be no missing criteria
    if result.is_eligible:
        assert len(result.missing_criteria) == 0, (
            f"User is marked eligible but has missing criteria: {result.missing_criteria}"
        )
    
    # Additional verification: Confidence should be 1.0 when all data is present and no missing criteria
    if result.is_eligible and len(result.missing_criteria) == 0:
        assert result.confidence == 1.0, (
            f"Confidence should be 1.0 when eligible with no missing criteria, got {result.confidence}"
        )


@settings(max_examples=10, deadline=None)
@given(
    user_profile=user_profile_strategy(),
    scheme=scheme_strategy()
)
def test_eligibility_with_missing_user_data(user_profile, scheme):
    """
    Test that missing user data results in not eligible when criteria exist.
    
    This verifies that the checker correctly handles incomplete user profiles.
    """
    # Create eligibility checker instance
    eligibility_checker = EligibilityChecker()
    
    # Remove a random field from user profile if criteria exists for it
    criteria = scheme.eligibility_criteria
    
    # If there's an age criterion, remove user age
    if criteria.age_min is not None or criteria.age_max is not None:
        user_profile.age = None
        
        result = eligibility_checker.check_eligibility(user_profile, scheme)
        
        # Should not be eligible due to missing age
        assert result.is_eligible is False, (
            "User should not be eligible when age is missing but age criteria exists"
        )
        assert len(result.missing_criteria) > 0, (
            "Missing criteria should be reported when user data is incomplete"
        )
        assert any("Age information required" in criterion for criterion in result.missing_criteria), (
            "Missing age should be reported in missing_criteria"
        )


@settings(max_examples=10, deadline=None)
@given(
    user_profile=user_profile_strategy()
)
def test_eligibility_with_no_criteria(user_profile):
    """
    Test that users are eligible when scheme has no eligibility criteria.
    
    This verifies that schemes without restrictions are universally accessible.
    """
    # Create eligibility checker instance
    eligibility_checker = EligibilityChecker()
    
    # Create a scheme with no eligibility criteria
    scheme = Scheme(
        scheme_id="UNIVERSAL-SCHEME",
        name="Universal Scheme",
        name_translations={},
        category="social_welfare",
        description="A scheme available to everyone",
        description_translations={},
        benefits=["Universal benefit"],
        eligibility_criteria=EligibilityCriteria(
            age_min=None,
            age_max=None,
            income_max=None,
            gender=None,
            occupation=None,
            education=None,
            location=None,
            caste=None,
            custom_criteria={}
        ),
        required_documents=["Aadhaar"],
        application_process=["Apply online"],
        application_url="https://example.gov.in/universal",
        department="Universal Department",
        state=None,
        last_updated=datetime(2024, 1, 15, 10, 30, 0),
        source_url="https://example.gov.in/source"
    )
    
    result = eligibility_checker.check_eligibility(user_profile, scheme)
    
    # Should be eligible since there are no criteria
    assert result.is_eligible is True, (
        "User should be eligible when scheme has no eligibility criteria"
    )
    assert len(result.missing_criteria) == 0, (
        "No missing criteria should be reported when scheme has no criteria"
    )


@settings(max_examples=10, deadline=None)
@given(
    age=st.integers(min_value=18, max_value=60),
    income_upper=st.integers(min_value=100000, max_value=500000)
)
def test_eligibility_boundary_conditions(age, income_upper):
    """
    Test eligibility at boundary conditions (min/max values).
    
    This verifies that boundary values are handled correctly (inclusive).
    """
    # Create eligibility checker instance
    eligibility_checker = EligibilityChecker()
    
    # Create user at exact boundary
    user_profile = UserProfile(
        user_id="boundary_user",
        phone_number="+919876543210",
        language="hi",
        location=Location(state="Maharashtra", district="Pune", pincode="411014"),
        age=age,
        gender="male",
        education_level="secondary",
        occupation="farmer",
        income_bracket=f"0-{income_upper}",
        household_size=5
    )
    
    # Create scheme with exact boundary criteria
    scheme = Scheme(
        scheme_id="BOUNDARY-SCHEME",
        name="Boundary Test Scheme",
        name_translations={},
        category="agriculture",
        description="Test scheme for boundary conditions",
        description_translations={},
        benefits=["Test benefit"],
        eligibility_criteria=EligibilityCriteria(
            age_min=18,
            age_max=60,
            income_max=500000,
            gender=None,
            occupation=["farmer"],
            education=None,
            location=["Maharashtra"],
            caste=None,
            custom_criteria={}
        ),
        required_documents=["Aadhaar"],
        application_process=["Apply"],
        application_url="https://example.gov.in/boundary",
        department="Test Department",
        state=None,
        last_updated=datetime(2024, 1, 15, 10, 30, 0),
        source_url="https://example.gov.in/source"
    )
    
    result = eligibility_checker.check_eligibility(user_profile, scheme)
    
    # Should be eligible at boundaries (inclusive)
    assert result.is_eligible is True, (
        f"User should be eligible at boundary values: age={age}, income_upper={income_upper}"
    )
