"""Property-based tests for personalized recommendation filtering.

Feature: bharatsahayak, Property 21: Personalized Recommendation Filtering
**Validates: Requirements 8.2**

This test verifies that different user profiles receive different recommendations,
ensuring that the recommendation system properly personalizes results based on
user characteristics such as location, occupation, category preferences, and
eligibility criteria.
"""

import pytest
from hypothesis import given, settings, strategies as st, assume
from datetime import datetime
from typing import List, Tuple

from src.core.eligibility_checker import EligibilityChecker
from src.core.scheme_repository import SchemeRepository
from src.models.user import UserProfile, UserPreferences
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
    """Generate valid UserProfile instances with varying characteristics."""
    location = draw(location_strategy())
    occupation = draw(st.sampled_from(["farmer", "laborer", "student", "unemployed", "teacher", "engineer"]))
    
    # Generate category preferences based on occupation
    all_categories = ["agriculture", "health", "education", "employment", "social_welfare"]
    preferred_categories = draw(st.lists(
        st.sampled_from(all_categories),
        min_size=0, max_size=3, unique=True
    ))
    
    return UserProfile(
        user_id=f"user_{draw(st.integers(min_value=1000, max_value=9999))}",
        phone_number=f"+91{draw(st.integers(min_value=1000000000, max_value=9999999999))}",
        language=draw(st.sampled_from(["hi", "en", "mr", "ta", "gu"])),
        location=location,
        age=draw(st.integers(min_value=18, max_value=65)),
        gender=draw(st.sampled_from(["male", "female", "other"])),
        education_level=draw(st.sampled_from(["primary", "secondary", "higher_secondary", "graduate"])),
        occupation=occupation,
        income_bracket=draw(st.sampled_from([
            "0-100000", "100000-300000", "300000-500000"
        ])),
        household_size=draw(st.integers(min_value=1, max_value=10)),
        preferences=UserPreferences(
            preferred_categories=preferred_categories,
            preferred_language=draw(st.sampled_from(["hi", "en", "mr"]))
        )
    )


def create_diverse_scheme_set() -> List[Scheme]:
    """
    Create a diverse set of schemes with different eligibility criteria,
    categories, and locations to test personalization.
    """
    schemes = []
    
    # Scheme 1: Maharashtra farmer scheme
    schemes.append(Scheme(
        scheme_id="MH-FARMER-001",
        name="Maharashtra Farmer Support Scheme",
        name_translations={},
        category="agriculture",
        description="Support for farmers in Maharashtra",
        description_translations={},
        benefits=["Financial assistance", "Crop insurance"],
        eligibility_criteria=EligibilityCriteria(
            age_min=18,
            age_max=65,
            income_max=300000,
            gender=None,
            occupation=["farmer"],
            education=None,
            location=["Maharashtra"],
            caste=None,
            custom_criteria={}
        ),
        required_documents=["Aadhaar", "Land records"],
        application_process=["Apply online"],
        application_url="https://example.gov.in/mh-farmer",
        department="Agriculture Department",
        state="Maharashtra",
        last_updated=datetime(2024, 1, 15, 10, 30, 0),
        source_url="https://example.gov.in/source"
    ))
    
    # Scheme 2: Karnataka farmer scheme
    schemes.append(Scheme(
        scheme_id="KA-FARMER-001",
        name="Karnataka Farmer Support Scheme",
        name_translations={},
        category="agriculture",
        description="Support for farmers in Karnataka",
        description_translations={},
        benefits=["Financial assistance", "Seeds subsidy"],
        eligibility_criteria=EligibilityCriteria(
            age_min=18,
            age_max=65,
            income_max=300000,
            gender=None,
            occupation=["farmer"],
            education=None,
            location=["Karnataka"],
            caste=None,
            custom_criteria={}
        ),
        required_documents=["Aadhaar", "Land records"],
        application_process=["Apply online"],
        application_url="https://example.gov.in/ka-farmer",
        department="Agriculture Department",
        state="Karnataka",
        last_updated=datetime(2024, 1, 15, 10, 30, 0),
        source_url="https://example.gov.in/source"
    ))
    
    # Scheme 3: Central education scheme for students
    schemes.append(Scheme(
        scheme_id="CENTRAL-EDU-001",
        name="National Education Support Scheme",
        name_translations={},
        category="education",
        description="Education support for students across India",
        description_translations={},
        benefits=["Scholarship", "Books allowance"],
        eligibility_criteria=EligibilityCriteria(
            age_min=18,
            age_max=30,
            income_max=500000,
            gender=None,
            occupation=["student"],
            education=["secondary", "higher_secondary", "graduate"],
            location=None,  # Central scheme - available everywhere
            caste=None,
            custom_criteria={}
        ),
        required_documents=["Aadhaar", "Income certificate"],
        application_process=["Apply online"],
        application_url="https://example.gov.in/edu",
        department="Education Department",
        state=None,
        last_updated=datetime(2024, 1, 15, 10, 30, 0),
        source_url="https://example.gov.in/source"
    ))
    
    # Scheme 4: Employment scheme for unemployed only
    schemes.append(Scheme(
        scheme_id="CENTRAL-EMP-001",
        name="National Employment Guarantee Scheme",
        name_translations={},
        category="employment",
        description="Employment guarantee for unemployed citizens",
        description_translations={},
        benefits=["Guaranteed employment", "Skill training"],
        eligibility_criteria=EligibilityCriteria(
            age_min=18,
            age_max=60,
            income_max=200000,
            gender=None,
            occupation=["unemployed"],  # Only unemployed, not laborer
            education=None,
            location=None,  # Central scheme
            caste=None,
            custom_criteria={}
        ),
        required_documents=["Aadhaar", "Income certificate"],
        application_process=["Register at employment office"],
        application_url="https://example.gov.in/emp",
        department="Labor Department",
        state=None,
        last_updated=datetime(2024, 1, 15, 10, 30, 0),
        source_url="https://example.gov.in/source"
    ))
    
    # Scheme 5: Health scheme for all
    schemes.append(Scheme(
        scheme_id="CENTRAL-HEALTH-001",
        name="National Health Insurance Scheme",
        name_translations={},
        category="health",
        description="Health insurance for all citizens",
        description_translations={},
        benefits=["Health insurance", "Free treatment"],
        eligibility_criteria=EligibilityCriteria(
            age_min=None,
            age_max=None,
            income_max=500000,
            gender=None,
            occupation=None,
            education=None,
            location=None,  # Central scheme
            caste=None,
            custom_criteria={}
        ),
        required_documents=["Aadhaar"],
        application_process=["Apply online"],
        application_url="https://example.gov.in/health",
        department="Health Department",
        state=None,
        last_updated=datetime(2024, 1, 15, 10, 30, 0),
        source_url="https://example.gov.in/source"
    ))
    
    # Scheme 6: Women-specific scheme
    schemes.append(Scheme(
        scheme_id="CENTRAL-WOMEN-001",
        name="Women Empowerment Scheme",
        name_translations={},
        category="social_welfare",
        description="Empowerment scheme for women",
        description_translations={},
        benefits=["Financial assistance", "Skill training"],
        eligibility_criteria=EligibilityCriteria(
            age_min=18,
            age_max=60,
            income_max=400000,
            gender="female",
            occupation=None,
            education=None,
            location=None,
            caste=None,
            custom_criteria={}
        ),
        required_documents=["Aadhaar", "Income certificate"],
        application_process=["Apply online"],
        application_url="https://example.gov.in/women",
        department="Women and Child Development",
        state=None,
        last_updated=datetime(2024, 1, 15, 10, 30, 0),
        source_url="https://example.gov.in/source"
    ))
    
    return schemes


def get_eligible_schemes_with_ranking(
    user_profile: UserProfile,
    schemes: List[Scheme]
) -> List[Tuple[Scheme, float]]:
    """
    Get eligible schemes for user with relevance ranking.
    
    This mimics the logic in eligible_schemes.py to rank schemes by relevance.
    
    Returns:
        List of (Scheme, relevance_score) tuples, sorted by relevance
    """
    eligibility_checker = EligibilityChecker()
    eligible_schemes = []
    
    # Check eligibility for each scheme
    for scheme in schemes:
        result = eligibility_checker.check_eligibility(user_profile, scheme)
        
        if result.is_eligible:
            # Calculate relevance score
            relevance_score = 0.0
            
            # Base score from confidence
            relevance_score += result.confidence * 0.4
            
            # Location match bonus
            if scheme.state:
                if scheme.state.lower() == user_profile.location.state.lower():
                    relevance_score += 0.3  # State-specific scheme for user's state
            else:
                relevance_score += 0.2  # Central scheme
            
            # Category preference bonus
            if user_profile.preferences.preferred_categories:
                if scheme.category in user_profile.preferences.preferred_categories:
                    relevance_score += 0.2
            
            # Occupation match bonus
            if user_profile.occupation and scheme.eligibility_criteria.occupation:
                if user_profile.occupation.lower() in [
                    occ.lower() for occ in scheme.eligibility_criteria.occupation
                ]:
                    relevance_score += 0.1
            
            # Normalize score to 0-1 range
            relevance_score = min(1.0, relevance_score)
            
            eligible_schemes.append((scheme, relevance_score))
    
    # Sort by relevance score (descending)
    eligible_schemes.sort(key=lambda x: x[1], reverse=True)
    
    return eligible_schemes


@settings(max_examples=20, deadline=None)
@given(
    user_profile1=user_profile_strategy(),
    user_profile2=user_profile_strategy()
)
def test_different_profiles_receive_different_recommendations(user_profile1, user_profile2):
    """
    Feature: bharatsahayak, Property 21: Personalized Recommendation Filtering
    
    For any two different user profiles with characteristics that should affect
    recommendations, the recommendation system should return different results,
    ensuring that recommendations are personalized based on user characteristics.
    
    This test verifies:
    1. Different user profiles receive different eligible schemes when they have
       different characteristics that match different scheme criteria
    2. Rankings differ based on relevance factors (location, occupation, preferences)
    3. The system properly personalizes results based on user attributes
    """
    # Ensure profiles are meaningfully different
    assume(user_profile1.user_id != user_profile2.user_id)
    
    # Create diverse scheme set
    schemes = create_diverse_scheme_set()
    
    # Get recommendations for both users
    recommendations1 = get_eligible_schemes_with_ranking(user_profile1, schemes)
    recommendations2 = get_eligible_schemes_with_ranking(user_profile2, schemes)
    
    # Extract scheme IDs and scores
    scheme_ids1 = [scheme.scheme_id for scheme, _ in recommendations1]
    scheme_ids2 = [scheme.scheme_id for scheme, _ in recommendations2]
    
    scores1 = [score for _, score in recommendations1]
    scores2 = [score for _, score in recommendations2]
    
    # Property verification: When users have different characteristics that
    # should affect eligibility or ranking, recommendations should differ
    
    # Check if users have characteristics that should lead to different recommendations
    has_different_location = user_profile1.location.state != user_profile2.location.state
    has_different_occupation = user_profile1.occupation != user_profile2.occupation
    has_different_gender = user_profile1.gender != user_profile2.gender
    has_different_preferences = user_profile1.preferences.preferred_categories != user_profile2.preferences.preferred_categories
    
    # Check if there are schemes that would be affected by these differences
    has_location_specific_schemes = any(
        scheme.state is not None for scheme, _ in recommendations1 + recommendations2
    )
    has_occupation_specific_schemes = any(
        scheme.eligibility_criteria.occupation is not None 
        for scheme, _ in recommendations1 + recommendations2
    )
    has_gender_specific_schemes = any(
        scheme.eligibility_criteria.gender is not None and scheme.eligibility_criteria.gender.lower() != 'any'
        for scheme, _ in recommendations1 + recommendations2
    )
    
    # If users differ in ways that should affect recommendations AND there are
    # schemes that would be affected, then recommendations should differ
    should_differ = (
        (has_different_location and has_location_specific_schemes) or
        (has_different_occupation and has_occupation_specific_schemes) or
        (has_different_gender and has_gender_specific_schemes)
    )
    
    # For category preferences, only expect difference if there are multiple eligible schemes
    # with different categories that match different preferences
    if has_different_preferences and len(recommendations1) > 1 and len(recommendations2) > 1:
        categories1 = set(scheme.category for scheme, _ in recommendations1)
        categories2 = set(scheme.category for scheme, _ in recommendations2)
        # If there are multiple categories, preferences should affect ranking
        if len(categories1) > 1 or len(categories2) > 1:
            should_differ = True
    
    if should_differ and len(recommendations1) > 0 and len(recommendations2) > 0:
        recommendations_differ = (
            scheme_ids1 != scheme_ids2 or  # Different schemes or different order
            scores1 != scores2  # Different relevance scores
        )
        
        assert recommendations_differ, (
            f"Different user profiles with characteristics that should affect recommendations "
            f"should receive different results.\n"
            f"User 1: state={user_profile1.location.state}, occupation={user_profile1.occupation}, "
            f"gender={user_profile1.gender}, preferences={user_profile1.preferences.preferred_categories}\n"
            f"User 2: state={user_profile2.location.state}, occupation={user_profile2.occupation}, "
            f"gender={user_profile2.gender}, preferences={user_profile2.preferences.preferred_categories}\n"
            f"Recommendations 1: {scheme_ids1}\n"
            f"Recommendations 2: {scheme_ids2}\n"
            f"Scores 1: {scores1}\n"
            f"Scores 2: {scores2}\n"
            f"Has location-specific schemes: {has_location_specific_schemes}\n"
            f"Has occupation-specific schemes: {has_occupation_specific_schemes}\n"
            f"Has gender-specific schemes: {has_gender_specific_schemes}"
        )


@settings(max_examples=10, deadline=None)
@given(
    base_profile=user_profile_strategy()
)
def test_location_affects_recommendations(base_profile):
    """
    Test that user location affects which schemes are recommended.
    
    This verifies that state-specific schemes are prioritized for users
    in that state, and that location-based eligibility is enforced.
    """
    # Create two profiles with different locations but same other characteristics
    profile_maharashtra = UserProfile(
        user_id="user_mh",
        phone_number=base_profile.phone_number,
        language=base_profile.language,
        location=Location(state="Maharashtra", district="Pune", pincode="411014"),
        age=base_profile.age,
        gender=base_profile.gender,
        education_level=base_profile.education_level,
        occupation="farmer",  # Set to farmer to be eligible for state schemes
        income_bracket=base_profile.income_bracket,
        household_size=base_profile.household_size,
        preferences=base_profile.preferences
    )
    
    profile_karnataka = UserProfile(
        user_id="user_ka",
        phone_number=base_profile.phone_number,
        language=base_profile.language,
        location=Location(state="Karnataka", district="Bangalore", pincode="560001"),
        age=base_profile.age,
        gender=base_profile.gender,
        education_level=base_profile.education_level,
        occupation="farmer",  # Set to farmer to be eligible for state schemes
        income_bracket=base_profile.income_bracket,
        household_size=base_profile.household_size,
        preferences=base_profile.preferences
    )
    
    # Create scheme set
    schemes = create_diverse_scheme_set()
    
    # Get recommendations
    recommendations_mh = get_eligible_schemes_with_ranking(profile_maharashtra, schemes)
    recommendations_ka = get_eligible_schemes_with_ranking(profile_karnataka, schemes)
    
    # Extract scheme IDs
    scheme_ids_mh = [scheme.scheme_id for scheme, _ in recommendations_mh]
    scheme_ids_ka = [scheme.scheme_id for scheme, _ in recommendations_ka]
    
    # Verify location-based differences
    # Maharashtra user should get Maharashtra scheme
    if "MH-FARMER-001" in scheme_ids_mh:
        assert "MH-FARMER-001" not in scheme_ids_ka, (
            "Maharashtra-specific scheme should not be recommended to Karnataka user"
        )
    
    # Karnataka user should get Karnataka scheme
    if "KA-FARMER-001" in scheme_ids_ka:
        assert "KA-FARMER-001" not in scheme_ids_mh, (
            "Karnataka-specific scheme should not be recommended to Maharashtra user"
        )


@settings(max_examples=10, deadline=None)
@given(
    base_profile=user_profile_strategy()
)
def test_occupation_affects_recommendations(base_profile):
    """
    Test that user occupation affects which schemes are recommended.
    
    This verifies that occupation-specific schemes are only recommended
    to users with matching occupations.
    """
    # Create two profiles with different occupations
    profile_farmer = UserProfile(
        user_id="user_farmer",
        phone_number=base_profile.phone_number,
        language=base_profile.language,
        location=Location(state="Maharashtra", district="Pune", pincode="411014"),
        age=base_profile.age,
        gender=base_profile.gender,
        education_level=base_profile.education_level,
        occupation="farmer",
        income_bracket=base_profile.income_bracket,
        household_size=base_profile.household_size,
        preferences=base_profile.preferences
    )
    
    profile_student = UserProfile(
        user_id="user_student",
        phone_number=base_profile.phone_number,
        language=base_profile.language,
        location=Location(state="Maharashtra", district="Pune", pincode="411014"),
        age=base_profile.age,
        gender=base_profile.gender,
        education_level="secondary",  # Ensure eligible for education scheme
        occupation="student",
        income_bracket=base_profile.income_bracket,
        household_size=base_profile.household_size,
        preferences=base_profile.preferences
    )
    
    # Create scheme set
    schemes = create_diverse_scheme_set()
    
    # Get recommendations
    recommendations_farmer = get_eligible_schemes_with_ranking(profile_farmer, schemes)
    recommendations_student = get_eligible_schemes_with_ranking(profile_student, schemes)
    
    # Extract scheme IDs
    scheme_ids_farmer = [scheme.scheme_id for scheme, _ in recommendations_farmer]
    scheme_ids_student = [scheme.scheme_id for scheme, _ in recommendations_student]
    
    # Verify occupation-based differences
    # Farmer should get farmer schemes
    farmer_schemes_for_farmer = [sid for sid in scheme_ids_farmer if "FARMER" in sid]
    farmer_schemes_for_student = [sid for sid in scheme_ids_student if "FARMER" in sid]
    
    # Student should get education schemes
    edu_schemes_for_student = [sid for sid in scheme_ids_student if "EDU" in sid]
    edu_schemes_for_farmer = [sid for sid in scheme_ids_farmer if "EDU" in sid]
    
    # Farmer should have farmer schemes, student should not
    if farmer_schemes_for_farmer:
        assert len(farmer_schemes_for_student) == 0, (
            "Farmer-specific schemes should not be recommended to students"
        )
    
    # Student should have education schemes, farmer should not
    if edu_schemes_for_student:
        assert len(edu_schemes_for_farmer) == 0, (
            "Student-specific schemes should not be recommended to farmers"
        )


@settings(max_examples=10, deadline=None)
@given(
    base_profile=user_profile_strategy()
)
def test_category_preferences_affect_ranking(base_profile):
    """
    Test that user category preferences affect scheme ranking.
    
    This verifies that schemes in preferred categories receive higher
    relevance scores and appear higher in recommendations.
    """
    # Create two profiles with different category preferences
    profile_with_ag_pref = UserProfile(
        user_id="user_ag_pref",
        phone_number=base_profile.phone_number,
        language=base_profile.language,
        location=base_profile.location,
        age=base_profile.age,
        gender=base_profile.gender,
        education_level=base_profile.education_level,
        occupation=base_profile.occupation,
        income_bracket=base_profile.income_bracket,
        household_size=base_profile.household_size,
        preferences=UserPreferences(
            preferred_categories=["agriculture"],
            preferred_language="hi"
        )
    )
    
    profile_with_health_pref = UserProfile(
        user_id="user_health_pref",
        phone_number=base_profile.phone_number,
        language=base_profile.language,
        location=base_profile.location,
        age=base_profile.age,
        gender=base_profile.gender,
        education_level=base_profile.education_level,
        occupation=base_profile.occupation,
        income_bracket=base_profile.income_bracket,
        household_size=base_profile.household_size,
        preferences=UserPreferences(
            preferred_categories=["health"],
            preferred_language="hi"
        )
    )
    
    # Create scheme set
    schemes = create_diverse_scheme_set()
    
    # Get recommendations
    recommendations_ag = get_eligible_schemes_with_ranking(profile_with_ag_pref, schemes)
    recommendations_health = get_eligible_schemes_with_ranking(profile_with_health_pref, schemes)
    
    # Find agriculture and health schemes in both recommendations
    ag_scheme_score_in_ag_pref = None
    ag_scheme_score_in_health_pref = None
    health_scheme_score_in_ag_pref = None
    health_scheme_score_in_health_pref = None
    
    for scheme, score in recommendations_ag:
        if scheme.category == "agriculture":
            ag_scheme_score_in_ag_pref = score
        if scheme.category == "health":
            health_scheme_score_in_ag_pref = score
    
    for scheme, score in recommendations_health:
        if scheme.category == "agriculture":
            ag_scheme_score_in_health_pref = score
        if scheme.category == "health":
            health_scheme_score_in_health_pref = score
    
    # Verify that preferred categories get higher scores
    if ag_scheme_score_in_ag_pref is not None and ag_scheme_score_in_health_pref is not None:
        assert ag_scheme_score_in_ag_pref > ag_scheme_score_in_health_pref, (
            f"Agriculture scheme should have higher score for user with agriculture preference. "
            f"Score with ag pref: {ag_scheme_score_in_ag_pref}, "
            f"Score with health pref: {ag_scheme_score_in_health_pref}"
        )
    
    if health_scheme_score_in_health_pref is not None and health_scheme_score_in_ag_pref is not None:
        assert health_scheme_score_in_health_pref > health_scheme_score_in_ag_pref, (
            f"Health scheme should have higher score for user with health preference. "
            f"Score with health pref: {health_scheme_score_in_health_pref}, "
            f"Score with ag pref: {health_scheme_score_in_ag_pref}"
        )


@settings(max_examples=10, deadline=None)
@given(
    base_profile=user_profile_strategy()
)
def test_gender_specific_schemes_are_personalized(base_profile):
    """
    Test that gender-specific schemes are only recommended to matching genders.
    
    This verifies that gender-based eligibility is enforced in recommendations.
    """
    # Create profiles with different genders
    profile_female = UserProfile(
        user_id="user_female",
        phone_number=base_profile.phone_number,
        language=base_profile.language,
        location=base_profile.location,
        age=base_profile.age,
        gender="female",
        education_level=base_profile.education_level,
        occupation=base_profile.occupation,
        income_bracket=base_profile.income_bracket,
        household_size=base_profile.household_size,
        preferences=base_profile.preferences
    )
    
    profile_male = UserProfile(
        user_id="user_male",
        phone_number=base_profile.phone_number,
        language=base_profile.language,
        location=base_profile.location,
        age=base_profile.age,
        gender="male",
        education_level=base_profile.education_level,
        occupation=base_profile.occupation,
        income_bracket=base_profile.income_bracket,
        household_size=base_profile.household_size,
        preferences=base_profile.preferences
    )
    
    # Create scheme set
    schemes = create_diverse_scheme_set()
    
    # Get recommendations
    recommendations_female = get_eligible_schemes_with_ranking(profile_female, schemes)
    recommendations_male = get_eligible_schemes_with_ranking(profile_male, schemes)
    
    # Extract scheme IDs
    scheme_ids_female = [scheme.scheme_id for scheme, _ in recommendations_female]
    scheme_ids_male = [scheme.scheme_id for scheme, _ in recommendations_male]
    
    # Verify gender-specific scheme is only for females
    if "CENTRAL-WOMEN-001" in scheme_ids_female:
        assert "CENTRAL-WOMEN-001" not in scheme_ids_male, (
            "Women-specific scheme should not be recommended to male users"
        )
