"""
Property-Based Test: Eligibility Determination Correctness
Feature: bharatsahayak, Property 6: Eligibility Determination Correctness

For any user profile and scheme, the Eligibility_Checker should return "eligible" 
if and only if the user profile satisfies all criteria in the scheme's 
eligibility_criteria, and "not eligible" otherwise.

Validates: Requirements 2.3
"""
import pytest
from hypothesis import given, settings, strategies as st, HealthCheck, assume
from hypothesis.strategies import composite
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.scheme import Scheme
from app.services.eligibility_checker import EligibilityChecker
import uuid


# Strategy for generating user profiles
@composite
def user_profile_strategy(draw):
    """Generate a valid user profile with various attributes"""
    profile = {}
    
    # Always include some basic fields
    profile['age'] = draw(st.integers(min_value=1, max_value=100))
    profile['gender'] = draw(st.sampled_from(['Male', 'Female', 'Other']))
    
    # Optionally include other fields
    if draw(st.booleans()):
        # Income bracket as string range
        income_ranges = ['0-50000', '50000-100000', '100000-200000', '200000-500000', '500000-1000000']
        profile['income_bracket'] = draw(st.sampled_from(income_ranges))
    
    if draw(st.booleans()):
        profile['occupation'] = draw(st.sampled_from([
            'Farmer', 'Student', 'Worker', 'Self-Employed', 'Unemployed', 'Teacher', 'Doctor'
        ]))
    
    if draw(st.booleans()):
        profile['education_level'] = draw(st.sampled_from([
            'Illiterate', 'Primary', 'Secondary', 'Higher Secondary', 'Graduate', 'Post-Graduate'
        ]))
    
    if draw(st.booleans()):
        profile['caste'] = draw(st.sampled_from(['General', 'OBC', 'SC', 'ST']))
    
    # Location
    states = ['Maharashtra', 'Karnataka', 'Tamil Nadu', 'Uttar Pradesh', 'Bihar', 'Gujarat']
    districts = ['District A', 'District B', 'District C']
    
    if draw(st.booleans()):
        profile['state'] = draw(st.sampled_from(states))
        profile['district'] = draw(st.sampled_from(districts))
        profile['location'] = {
            'state': profile['state'],
            'district': profile['district']
        }
    
    return profile


# Strategy for generating eligibility criteria
@composite
def eligibility_criteria_strategy(draw):
    """Generate eligibility criteria that may or may not match a profile"""
    criteria = {}
    
    # Age criteria
    if draw(st.booleans()):
        criteria['age_min'] = draw(st.integers(min_value=0, max_value=50))
    
    if draw(st.booleans()):
        criteria['age_max'] = draw(st.integers(min_value=18, max_value=100))
    
    # Ensure age_min <= age_max if both are present
    if 'age_min' in criteria and 'age_max' in criteria:
        if criteria['age_min'] > criteria['age_max']:
            criteria['age_min'], criteria['age_max'] = criteria['age_max'], criteria['age_min']
    
    # Income criteria
    if draw(st.booleans()):
        criteria['income_max'] = draw(st.integers(min_value=50000, max_value=500000))
    
    # Gender criteria
    if draw(st.booleans()):
        criteria['gender'] = draw(st.sampled_from(['Male', 'Female', 'Other']))
    
    # Occupation criteria
    if draw(st.booleans()):
        criteria['occupation'] = draw(st.lists(
            st.sampled_from(['Farmer', 'Student', 'Worker', 'Self-Employed', 'Unemployed']),
            min_size=1, max_size=3, unique=True
        ))
    
    # Education criteria
    if draw(st.booleans()):
        criteria['education'] = draw(st.lists(
            st.sampled_from(['Illiterate', 'Primary', 'Secondary', 'Graduate']),
            min_size=1, max_size=3, unique=True
        ))
    
    # Location criteria
    if draw(st.booleans()):
        criteria['location'] = draw(st.lists(
            st.sampled_from(['Maharashtra', 'Karnataka', 'Tamil Nadu', 'Uttar Pradesh', 'Bihar']),
            min_size=1, max_size=3, unique=True
        ))
    
    # Caste criteria
    if draw(st.booleans()):
        criteria['caste'] = draw(st.lists(
            st.sampled_from(['General', 'OBC', 'SC', 'ST']),
            min_size=1, max_size=3, unique=True
        ))
    
    # Custom criteria
    if draw(st.booleans()):
        criteria['custom_criteria'] = {
            'has_land': draw(st.booleans()),
            'is_bpl': draw(st.booleans())
        }
    
    return criteria


def manually_check_eligibility(user_profile: dict, criteria: dict) -> bool:
    """
    Manually verify eligibility based on criteria.
    This is the oracle function that defines correct behavior.
    
    Returns True if user meets ALL criteria, False otherwise.
    """
    # Check age_min
    if 'age_min' in criteria and criteria['age_min'] is not None:
        user_age = user_profile.get('age')
        if user_age is None or user_age < criteria['age_min']:
            return False
    
    # Check age_max
    if 'age_max' in criteria and criteria['age_max'] is not None:
        user_age = user_profile.get('age')
        if user_age is None or user_age > criteria['age_max']:
            return False
    
    # Check income_max
    if 'income_max' in criteria and criteria['income_max'] is not None:
        user_income = user_profile.get('income_bracket')
        if user_income is None:
            return False
        
        # Parse income bracket
        try:
            if '-' in str(user_income):
                income_parts = str(user_income).split('-')
                max_income = int(income_parts[-1])
                if max_income > criteria['income_max']:
                    return False
        except (ValueError, IndexError):
            return False
    
    # Check gender
    if 'gender' in criteria and criteria['gender'] is not None:
        user_gender = user_profile.get('gender')
        if user_gender is None or user_gender.lower() != criteria['gender'].lower():
            return False
    
    # Check occupation
    if 'occupation' in criteria and criteria['occupation']:
        user_occupation = user_profile.get('occupation')
        if user_occupation is None or user_occupation not in criteria['occupation']:
            return False
    
    # Check education
    if 'education' in criteria and criteria['education']:
        user_education = user_profile.get('education_level')
        if user_education is None or user_education not in criteria['education']:
            return False
    
    # Check location
    if 'location' in criteria and criteria['location']:
        user_state = user_profile.get('location', {}).get('state') if isinstance(user_profile.get('location'), dict) else user_profile.get('state')
        user_district = user_profile.get('location', {}).get('district') if isinstance(user_profile.get('location'), dict) else user_profile.get('district')
        
        if user_state is None:
            return False
        
        # Check if user's state or district is in the allowed locations
        location_match = False
        for loc in criteria['location']:
            if user_state and user_state.lower() in loc.lower():
                location_match = True
                break
            if user_district and user_district.lower() in loc.lower():
                location_match = True
                break
        
        if not location_match:
            return False
    
    # Check caste
    if 'caste' in criteria and criteria['caste']:
        user_caste = user_profile.get('caste')
        if user_caste is None or user_caste not in criteria['caste']:
            return False
    
    # Check custom criteria
    if 'custom_criteria' in criteria and criteria['custom_criteria']:
        for key, required_value in criteria['custom_criteria'].items():
            user_value = user_profile.get(key)
            if user_value is None or user_value != required_value:
                return False
    
    # All criteria passed
    return True


@pytest.fixture(scope="function")
def test_db_session():
    """Create a test database session"""
    # For eligibility checking, we don't need a database at all
    # The eligibility checker only needs the scheme object, not DB access
    # Create a mock session
    from unittest.mock import Mock
    session = Mock()
    yield session


@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    user_profile=user_profile_strategy(),
    criteria=eligibility_criteria_strategy()
)
def test_eligibility_determination_correctness(user_profile, criteria, test_db_session):
    """
    Feature: bharatsahayak, Property 6: Eligibility Determination Correctness
    
    For any user profile and scheme, the Eligibility_Checker should return 
    "eligible" if and only if the user profile satisfies all criteria in the 
    scheme's eligibility_criteria, and "not eligible" otherwise.
    
    This is the core property: eligibility determination must be correct.
    """
    # Create a scheme with the generated criteria
    scheme = Scheme(
        scheme_id=uuid.uuid4(),
        name='Test Scheme',
        category='test',
        description='Test scheme for eligibility checking',
        benefits=['Test benefit'],
        eligibility_criteria=criteria,
        required_documents=[],
        application_process=[],
        application_url=None,
        department='Test Department',
        state=None,
        source_url=None,
        last_updated=datetime.utcnow(),
        created_at=datetime.utcnow()
    )
    
    # Create eligibility checker
    checker = EligibilityChecker(test_db_session)
    
    # Check eligibility using the system
    result = checker.check_eligibility(user_profile, scheme)
    
    # Manually verify eligibility (oracle)
    expected_eligible = manually_check_eligibility(user_profile, criteria)
    
    # Property: System result should match manual verification
    assert result.is_eligible == expected_eligible, \
        f"Eligibility mismatch: System returned {result.is_eligible}, expected {expected_eligible}. " \
        f"Profile: {user_profile}, Criteria: {criteria}, Missing: {result.missing_criteria}"


@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    base_profile=user_profile_strategy(),
    criteria=eligibility_criteria_strategy()
)
def test_eligibility_with_matching_profile(base_profile, criteria, test_db_session):
    """
    Feature: bharatsahayak, Property 6: Eligibility Determination Correctness
    
    If we construct a user profile that explicitly satisfies all criteria,
    the system should return eligible=True.
    
    This tests the positive case: eligible profiles are correctly identified.
    """
    # Construct a profile that matches all criteria
    matching_profile = base_profile.copy()
    
    # Match age criteria
    if 'age_min' in criteria and criteria['age_min'] is not None:
        if 'age_max' in criteria and criteria['age_max'] is not None:
            # Age between min and max
            matching_profile['age'] = (criteria['age_min'] + criteria['age_max']) // 2
        else:
            # Age >= min
            matching_profile['age'] = criteria['age_min'] + 10
    elif 'age_max' in criteria and criteria['age_max'] is not None:
        # Age <= max
        matching_profile['age'] = criteria['age_max'] - 10
    
    # Match income criteria
    if 'income_max' in criteria and criteria['income_max'] is not None:
        # Set income below max - ensure the upper bound is less than criteria max
        max_income = criteria['income_max']
        if max_income > 100000:
            matching_profile['income_bracket'] = '50000-100000'
        elif max_income > 50000:
            matching_profile['income_bracket'] = '0-50000'
        else:
            # For very low income requirements, use a range that fits
            matching_profile['income_bracket'] = f'0-{max_income - 1}'
    
    # Match gender criteria
    if 'gender' in criteria and criteria['gender'] is not None:
        matching_profile['gender'] = criteria['gender']
    
    # Match occupation criteria
    if 'occupation' in criteria and criteria['occupation']:
        matching_profile['occupation'] = criteria['occupation'][0]
    
    # Match education criteria
    if 'education' in criteria and criteria['education']:
        matching_profile['education_level'] = criteria['education'][0]
    
    # Match location criteria
    if 'location' in criteria and criteria['location']:
        matching_profile['state'] = criteria['location'][0]
        matching_profile['location'] = {'state': criteria['location'][0], 'district': 'Test District'}
    
    # Match caste criteria
    if 'caste' in criteria and criteria['caste']:
        matching_profile['caste'] = criteria['caste'][0]
    
    # Match custom criteria
    if 'custom_criteria' in criteria and criteria['custom_criteria']:
        for key, value in criteria['custom_criteria'].items():
            matching_profile[key] = value
    
    # Create scheme
    scheme = Scheme(
        scheme_id=uuid.uuid4(),
        name='Test Scheme',
        category='test',
        description='Test scheme',
        benefits=[],
        eligibility_criteria=criteria,
        required_documents=[],
        application_process=[],
        application_url=None,
        department='Test',
        state=None,
        source_url=None,
        last_updated=datetime.utcnow(),
        created_at=datetime.utcnow()
    )
    
    # Check eligibility
    checker = EligibilityChecker(test_db_session)
    result = checker.check_eligibility(matching_profile, scheme)
    
    # Property: Matching profile should be eligible
    assert result.is_eligible == True, \
        f"Profile constructed to match all criteria should be eligible. " \
        f"Missing: {result.missing_criteria}, Criteria: {criteria}"


def test_eligibility_specific_age_criteria(test_db_session):
    """
    Specific example: User aged 25 should be eligible for scheme with age 18-60.
    """
    user_profile = {
        'age': 25,
        'gender': 'Male'
    }
    
    criteria = {
        'age_min': 18,
        'age_max': 60
    }
    
    scheme = Scheme(
        scheme_id=uuid.uuid4(),
        name='Youth Scheme',
        category='employment',
        description='Scheme for youth',
        benefits=['Job training'],
        eligibility_criteria=criteria,
        required_documents=[],
        application_process=[],
        application_url=None,
        department='Employment',
        state=None,
        source_url=None,
        last_updated=datetime.utcnow(),
        created_at=datetime.utcnow()
    )
    
    checker = EligibilityChecker(test_db_session)
    result = checker.check_eligibility(user_profile, scheme)
    
    assert result.is_eligible == True, "User aged 25 should be eligible for age 18-60 scheme"
    assert len(result.missing_criteria) == 0, "Should have no missing criteria"


def test_eligibility_specific_age_too_young(test_db_session):
    """
    Specific example: User aged 15 should NOT be eligible for scheme with age_min 18.
    """
    user_profile = {
        'age': 15,
        'gender': 'Male'
    }
    
    criteria = {
        'age_min': 18,
        'age_max': 60
    }
    
    scheme = Scheme(
        scheme_id=uuid.uuid4(),
        name='Adult Scheme',
        category='employment',
        description='Scheme for adults',
        benefits=['Job training'],
        eligibility_criteria=criteria,
        required_documents=[],
        application_process=[],
        application_url=None,
        department='Employment',
        state=None,
        source_url=None,
        last_updated=datetime.utcnow(),
        created_at=datetime.utcnow()
    )
    
    checker = EligibilityChecker(test_db_session)
    result = checker.check_eligibility(user_profile, scheme)
    
    assert result.is_eligible == False, "User aged 15 should NOT be eligible for age_min 18 scheme"
    assert len(result.missing_criteria) > 0, "Should have missing criteria"
    assert any('age' in criterion.lower() for criterion in result.missing_criteria), \
        "Missing criteria should mention age"


def test_eligibility_specific_income_criteria(test_db_session):
    """
    Specific example: User with income 0-50000 should be eligible for income_max 100000.
    """
    user_profile = {
        'age': 30,
        'income_bracket': '0-50000'
    }
    
    criteria = {
        'income_max': 100000
    }
    
    scheme = Scheme(
        scheme_id=uuid.uuid4(),
        name='Low Income Scheme',
        category='social_welfare',
        description='Scheme for low income families',
        benefits=['Financial assistance'],
        eligibility_criteria=criteria,
        required_documents=[],
        application_process=[],
        application_url=None,
        department='Social Welfare',
        state=None,
        source_url=None,
        last_updated=datetime.utcnow(),
        created_at=datetime.utcnow()
    )
    
    checker = EligibilityChecker(test_db_session)
    result = checker.check_eligibility(user_profile, scheme)
    
    assert result.is_eligible == True, "User with income 0-50000 should be eligible for income_max 100000"


def test_eligibility_specific_occupation_match(test_db_session):
    """
    Specific example: Farmer should be eligible for scheme requiring Farmer occupation.
    """
    user_profile = {
        'age': 40,
        'occupation': 'Farmer'
    }
    
    criteria = {
        'occupation': ['Farmer', 'Agricultural Worker']
    }
    
    scheme = Scheme(
        scheme_id=uuid.uuid4(),
        name='Farmer Scheme',
        category='agriculture',
        description='Scheme for farmers',
        benefits=['Crop insurance'],
        eligibility_criteria=criteria,
        required_documents=[],
        application_process=[],
        application_url=None,
        department='Agriculture',
        state=None,
        source_url=None,
        last_updated=datetime.utcnow(),
        created_at=datetime.utcnow()
    )
    
    checker = EligibilityChecker(test_db_session)
    result = checker.check_eligibility(user_profile, scheme)
    
    assert result.is_eligible == True, "Farmer should be eligible for farmer scheme"


def test_eligibility_specific_occupation_mismatch(test_db_session):
    """
    Specific example: Student should NOT be eligible for scheme requiring Farmer occupation.
    """
    user_profile = {
        'age': 20,
        'occupation': 'Student'
    }
    
    criteria = {
        'occupation': ['Farmer', 'Agricultural Worker']
    }
    
    scheme = Scheme(
        scheme_id=uuid.uuid4(),
        name='Farmer Scheme',
        category='agriculture',
        description='Scheme for farmers',
        benefits=['Crop insurance'],
        eligibility_criteria=criteria,
        required_documents=[],
        application_process=[],
        application_url=None,
        department='Agriculture',
        state=None,
        source_url=None,
        last_updated=datetime.utcnow(),
        created_at=datetime.utcnow()
    )
    
    checker = EligibilityChecker(test_db_session)
    result = checker.check_eligibility(user_profile, scheme)
    
    assert result.is_eligible == False, "Student should NOT be eligible for farmer-only scheme"


def test_eligibility_multiple_criteria_all_met(test_db_session):
    """
    Specific example: User meeting all criteria (age, income, occupation) should be eligible.
    """
    user_profile = {
        'age': 30,
        'income_bracket': '0-50000',
        'occupation': 'Farmer',
        'gender': 'Male'
    }
    
    criteria = {
        'age_min': 18,
        'age_max': 60,
        'income_max': 100000,
        'occupation': ['Farmer', 'Agricultural Worker']
    }
    
    scheme = Scheme(
        scheme_id=uuid.uuid4(),
        name='Comprehensive Farmer Scheme',
        category='agriculture',
        description='Scheme with multiple criteria',
        benefits=['Multiple benefits'],
        eligibility_criteria=criteria,
        required_documents=[],
        application_process=[],
        application_url=None,
        department='Agriculture',
        state=None,
        source_url=None,
        last_updated=datetime.utcnow(),
        created_at=datetime.utcnow()
    )
    
    checker = EligibilityChecker(test_db_session)
    result = checker.check_eligibility(user_profile, scheme)
    
    assert result.is_eligible == True, "User meeting all criteria should be eligible"
    assert len(result.missing_criteria) == 0, "Should have no missing criteria"


def test_eligibility_multiple_criteria_one_fails(test_db_session):
    """
    Specific example: User failing one criterion should be ineligible even if others pass.
    """
    user_profile = {
        'age': 30,
        'income_bracket': '200000-500000',  # Too high
        'occupation': 'Farmer',
        'gender': 'Male'
    }
    
    criteria = {
        'age_min': 18,
        'age_max': 60,
        'income_max': 100000,  # User exceeds this
        'occupation': ['Farmer', 'Agricultural Worker']
    }
    
    scheme = Scheme(
        scheme_id=uuid.uuid4(),
        name='Low Income Farmer Scheme',
        category='agriculture',
        description='Scheme for low income farmers',
        benefits=['Financial assistance'],
        eligibility_criteria=criteria,
        required_documents=[],
        application_process=[],
        application_url=None,
        department='Agriculture',
        state=None,
        source_url=None,
        last_updated=datetime.utcnow(),
        created_at=datetime.utcnow()
    )
    
    checker = EligibilityChecker(test_db_session)
    result = checker.check_eligibility(user_profile, scheme)
    
    assert result.is_eligible == False, "User with high income should be ineligible"
    assert len(result.missing_criteria) > 0, "Should have missing criteria"
    assert any('income' in criterion.lower() for criterion in result.missing_criteria), \
        "Missing criteria should mention income"


def test_eligibility_missing_required_field(test_db_session):
    """
    Edge case: User missing a required field should be ineligible.
    """
    user_profile = {
        'age': 30,
        # Missing occupation field
    }
    
    criteria = {
        'occupation': ['Farmer', 'Agricultural Worker']
    }
    
    scheme = Scheme(
        scheme_id=uuid.uuid4(),
        name='Farmer Scheme',
        category='agriculture',
        description='Scheme requiring occupation',
        benefits=['Support'],
        eligibility_criteria=criteria,
        required_documents=[],
        application_process=[],
        application_url=None,
        department='Agriculture',
        state=None,
        source_url=None,
        last_updated=datetime.utcnow(),
        created_at=datetime.utcnow()
    )
    
    checker = EligibilityChecker(test_db_session)
    result = checker.check_eligibility(user_profile, scheme)
    
    assert result.is_eligible == False, "User missing required field should be ineligible"
    assert 'occupation' in result.missing_criteria, "Should indicate occupation is missing"


def test_eligibility_empty_criteria(test_db_session):
    """
    Edge case: Scheme with no eligibility criteria should accept all users.
    """
    user_profile = {
        'age': 30,
        'occupation': 'Student'
    }
    
    criteria = {}  # No criteria
    
    scheme = Scheme(
        scheme_id=uuid.uuid4(),
        name='Universal Scheme',
        category='social_welfare',
        description='Scheme for everyone',
        benefits=['Universal benefit'],
        eligibility_criteria=criteria,
        required_documents=[],
        application_process=[],
        application_url=None,
        department='Social Welfare',
        state=None,
        source_url=None,
        last_updated=datetime.utcnow(),
        created_at=datetime.utcnow()
    )
    
    checker = EligibilityChecker(test_db_session)
    result = checker.check_eligibility(user_profile, scheme)
    
    assert result.is_eligible == True, "User should be eligible for scheme with no criteria"
    assert len(result.missing_criteria) == 0, "Should have no missing criteria"


def test_eligibility_explanation_generated(test_db_session):
    """
    Test that eligibility result includes a human-readable explanation.
    """
    user_profile = {
        'age': 30,
        'occupation': 'Farmer'
    }
    
    criteria = {
        'age_min': 18,
        'occupation': ['Farmer']
    }
    
    scheme = Scheme(
        scheme_id=uuid.uuid4(),
        name='Test Scheme',
        category='agriculture',
        description='Test',
        benefits=[],
        eligibility_criteria=criteria,
        required_documents=[],
        application_process=[],
        application_url=None,
        department='Test',
        state=None,
        source_url=None,
        last_updated=datetime.utcnow(),
        created_at=datetime.utcnow()
    )
    
    checker = EligibilityChecker(test_db_session)
    result = checker.check_eligibility(user_profile, scheme)
    
    assert result.explanation is not None, "Should include explanation"
    assert len(result.explanation) > 0, "Explanation should not be empty"
    assert 'Test Scheme' in result.explanation, "Explanation should mention scheme name"
