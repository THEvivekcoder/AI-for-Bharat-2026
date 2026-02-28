"""
Property-Based Test: Personalized Recommendation Filtering
Feature: bharatsahayak, Property 21: Personalized Recommendation Filtering

For any two user profiles with different locations, occupations, or education levels,
the recommended schemes, jobs, or programs should differ to reflect the profile differences.

Validates: Requirements 8.2
"""
import pytest
from hypothesis import given, settings, strategies as st, assume
from hypothesis.strategies import composite
from app.services.personalization import PersonalizationEngine
import uuid


# Strategy for generating user profiles
@composite
def user_profile_strategy(draw):
    """Generate a valid user profile"""
    states = ['Maharashtra', 'Karnataka', 'Tamil Nadu', 'Uttar Pradesh', 'Bihar', 'Gujarat']
    districts = {
        'Maharashtra': ['Mumbai', 'Pune', 'Nagpur'],
        'Karnataka': ['Bangalore', 'Mysore', 'Hubli'],
        'Tamil Nadu': ['Chennai', 'Coimbatore', 'Madurai'],
        'Uttar Pradesh': ['Lucknow', 'Kanpur', 'Varanasi'],
        'Bihar': ['Patna', 'Gaya', 'Muzaffarpur'],
        'Gujarat': ['Ahmedabad', 'Surat', 'Vadodara']
    }
    
    state = draw(st.sampled_from(states))
    district = draw(st.sampled_from(districts[state]))
    
    occupations = ['Farmer', 'Student', 'Worker', 'Self-Employed', 'Unemployed', 'Teacher']
    education_levels = ['below_10th', '10th', '12th', 'diploma', 'graduate', 'postgraduate']
    
    profile = {
        'user_id': str(uuid.uuid4()),
        'state': state,
        'district': district,
        'occupation': draw(st.sampled_from(occupations)),
        'education_level': draw(st.sampled_from(education_levels)),
        'age': draw(st.integers(min_value=18, max_value=65)),
        'income_bracket': draw(st.sampled_from(['0-50000', '50000-100000', '100000-200000', '200000-500000'])),
        'interests': draw(st.lists(
            st.sampled_from(['technology', 'agriculture', 'healthcare', 'education', 'business']),
            min_size=1, max_size=3, unique=True
        )),
        'skills': draw(st.lists(
            st.sampled_from(['python', 'java', 'farming', 'teaching', 'accounting', 'driving']),
            min_size=0, max_size=3, unique=True
        )),
        'experience_years': draw(st.integers(min_value=0, max_value=20))
    }
    
    return profile


# Strategy for generating schemes
@composite
def scheme_strategy(draw):
    """Generate a government scheme"""
    categories = ['agriculture', 'health', 'education', 'employment', 'social_welfare']
    states = [None, 'Maharashtra', 'Karnataka', 'Tamil Nadu', 'Uttar Pradesh', 'Bihar', 'Gujarat']
    
    scheme = {
        'scheme_id': str(uuid.uuid4()),
        'name': f"Scheme {draw(st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))))}",
        'category': draw(st.sampled_from(categories)),
        'description': 'Government scheme for citizens',
        'benefits': ['Benefit 1', 'Benefit 2'],
        'state': draw(st.sampled_from(states)),
        'eligibility_criteria': {
            'occupation': draw(st.one_of(
                st.none(),
                st.lists(st.sampled_from(['Farmer', 'Student', 'Worker', 'Self-Employed']), min_size=1, max_size=2)
            )),
            'age_min': draw(st.one_of(st.none(), st.integers(min_value=18, max_value=30))),
            'age_max': draw(st.one_of(st.none(), st.integers(min_value=40, max_value=65))),
            'income_max': draw(st.one_of(st.none(), st.integers(min_value=50000, max_value=300000))),
            'education': draw(st.one_of(
                st.none(),
                st.lists(st.sampled_from(['10th', '12th', 'graduate']), min_size=1, max_size=2)
            ))
        },
        'department': 'Government Department',
        'application_url': 'https://example.gov.in'
    }
    
    return scheme


# Strategy for generating job postings
@composite
def job_strategy(draw):
    """Generate a job posting"""
    job = {
        'job_id': str(uuid.uuid4()),
        'title': f"Job {draw(st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))))}",
        'department': draw(st.sampled_from(['Education', 'Health', 'Agriculture', 'Transport'])),
        'description': 'Government job opportunity',
        'location': {
            'state': draw(st.sampled_from(['Maharashtra', 'Karnataka', 'Tamil Nadu', 'Uttar Pradesh'])),
            'district': draw(st.sampled_from(['Mumbai', 'Bangalore', 'Chennai', 'Lucknow']))
        },
        'qualifications': {
            'education_level': draw(st.sampled_from(['10th', '12th', 'graduate', 'postgraduate'])),
            'experience_years': draw(st.integers(min_value=0, max_value=10)),
            'skills': draw(st.lists(
                st.sampled_from(['python', 'java', 'teaching', 'accounting']),
                min_size=0, max_size=3, unique=True
            ))
        },
        'application_deadline': '2026-12-31',
        'application_url': 'https://example.gov.in/jobs'
    }
    
    return job


# Strategy for generating skill programs
@composite
def skill_program_strategy(draw):
    """Generate a skill development program"""
    program = {
        'program_id': str(uuid.uuid4()),
        'name': f"Program {draw(st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))))}",
        'provider': 'Government Training Institute',
        'category': draw(st.sampled_from(['technical', 'vocational', 'digital', 'entrepreneurship'])),
        'description': 'Skill development program',
        'duration_weeks': draw(st.integers(min_value=4, max_value=52)),
        'cost': draw(st.floats(min_value=0, max_value=10000)),
        'state': draw(st.sampled_from(['Maharashtra', 'Karnataka', 'Tamil Nadu', 'Uttar Pradesh', None])),
        'district': draw(st.one_of(st.none(), st.sampled_from(['Mumbai', 'Bangalore', 'Chennai']))),
        'mode': draw(st.sampled_from(['in-person', 'online', 'hybrid'])),
        'eligibility_criteria': {
            'education': draw(st.one_of(
                st.none(),
                st.lists(st.sampled_from(['10th', '12th', 'graduate']), min_size=1, max_size=2)
            ))
        },
        'certification': draw(st.booleans()),
        'placement_support': draw(st.booleans())
    }
    
    return program


@settings(max_examples=100, deadline=None)
@given(
    profile1=user_profile_strategy(),
    profile2=user_profile_strategy(),
    schemes=st.lists(scheme_strategy(), min_size=5, max_size=10)
)
def test_personalized_scheme_filtering_differs_by_profile(profile1, profile2, schemes):
    """
    Feature: bharatsahayak, Property 21: Personalized Recommendation Filtering
    
    For any two user profiles with different attributes, the recommended schemes
    should differ to reflect the profile differences.
    
    Tests scheme personalization.
    """
    # Ensure profiles are actually different in at least one key attribute
    assume(
        profile1['state'] != profile2['state'] or
        profile1['occupation'] != profile2['occupation'] or
        profile1['education_level'] != profile2['education_level']
    )
    
    # Ensure schemes have some variety (not all identical)
    unique_schemes = len(set(
        (s['state'], tuple(s['eligibility_criteria'].get('occupation', []) or []))
        for s in schemes
    ))
    assume(unique_schemes > 1)
    
    engine = PersonalizationEngine()
    
    # Get personalized recommendations for both profiles
    ranked1 = engine.rank_recommendations(schemes, profile1, 'scheme')
    ranked2 = engine.rank_recommendations(schemes, profile2, 'scheme')
    
    # Extract scores for each scheme
    scores1 = {item[0]['scheme_id']: item[1] for item in ranked1}
    scores2 = {item[0]['scheme_id']: item[1] for item in ranked2}
    
    # Property 1: At least one scheme should have different scores
    # (unless all schemes are completely generic with no personalization criteria)
    has_difference = False
    for scheme_id in scores1.keys():
        if scheme_id in scores2:
            if abs(scores1[scheme_id] - scores2[scheme_id]) > 0.01:  # Allow small floating point differences
                has_difference = True
                break
    
    # Count schemes with personalization criteria
    schemes_with_criteria = sum(
        1 for s in schemes
        if (s['eligibility_criteria'].get('occupation') or
            s['state'] is not None or
            s['eligibility_criteria'].get('education'))
    )
    
    # Only assert difference if there are schemes with personalization criteria
    if schemes_with_criteria > 0:
        assert has_difference, \
            "Schemes should have different scores for different user profiles when personalization criteria exist"
    
    # Property 2: Rankings should be ordered by score descending
    for i in range(len(ranked1) - 1):
        assert ranked1[i][1] >= ranked1[i+1][1], \
            "Profile 1 rankings should be in descending order by score"
    
    for i in range(len(ranked2) - 1):
        assert ranked2[i][1] >= ranked2[i+1][1], \
            "Profile 2 rankings should be in descending order by score"
    
    # Property 3: All scores should be between 0 and 1
    for item, score, _ in ranked1:
        assert 0 <= score <= 1, f"Score should be between 0 and 1, got {score}"
    
    for item, score, _ in ranked2:
        assert 0 <= score <= 1, f"Score should be between 0 and 1, got {score}"


@settings(max_examples=100, deadline=None)
@given(
    profile1=user_profile_strategy(),
    profile2=user_profile_strategy(),
    jobs=st.lists(job_strategy(), min_size=5, max_size=10)
)
def test_personalized_job_filtering_differs_by_profile(profile1, profile2, jobs):
    """
    Feature: bharatsahayak, Property 21: Personalized Recommendation Filtering
    
    For any two user profiles with different education or location, the recommended
    jobs should differ to reflect the profile differences.
    
    Tests job personalization.
    """
    # Ensure profiles are different in education or location
    assume(
        profile1['education_level'] != profile2['education_level'] or
        profile1['state'] != profile2['state'] or
        profile1['experience_years'] != profile2['experience_years']
    )
    
    # Ensure jobs have some variety in qualifications
    unique_jobs = len(set(
        (j['qualifications']['education_level'], j['qualifications']['experience_years'])
        for j in jobs
    ))
    assume(unique_jobs > 1)
    
    engine = PersonalizationEngine()
    
    # Get personalized recommendations for both profiles
    ranked1 = engine.rank_recommendations(jobs, profile1, 'job')
    ranked2 = engine.rank_recommendations(jobs, profile2, 'job')
    
    # Extract scores
    scores1 = {item[0]['job_id']: item[1] for item in ranked1}
    scores2 = {item[0]['job_id']: item[1] for item in ranked2}
    
    # Property 1: At least one job should have different scores
    has_difference = False
    for job_id in scores1.keys():
        if job_id in scores2:
            if abs(scores1[job_id] - scores2[job_id]) > 0.01:
                has_difference = True
                break
    
    # Jobs always have qualifications, so we should see differences
    assert has_difference, \
        "Jobs should have different scores for different user profiles"
    
    # Property 2: Rankings should be ordered by score descending
    for i in range(len(ranked1) - 1):
        assert ranked1[i][1] >= ranked1[i+1][1], \
            "Profile 1 job rankings should be in descending order by score"
    
    for i in range(len(ranked2) - 1):
        assert ranked2[i][1] >= ranked2[i+1][1], \
            "Profile 2 job rankings should be in descending order by score"
    
    # Property 3: All scores should be between 0 and 1
    for item, score, _ in ranked1:
        assert 0 <= score <= 1, f"Job score should be between 0 and 1, got {score}"
    
    for item, score, _ in ranked2:
        assert 0 <= score <= 1, f"Job score should be between 0 and 1, got {score}"


@settings(max_examples=100, deadline=None)
@given(
    profile1=user_profile_strategy(),
    profile2=user_profile_strategy(),
    programs=st.lists(skill_program_strategy(), min_size=5, max_size=10)
)
def test_personalized_skill_program_filtering_differs_by_profile(profile1, profile2, programs):
    """
    Feature: bharatsahayak, Property 21: Personalized Recommendation Filtering
    
    For any two user profiles with different interests or location, the recommended
    skill programs should differ to reflect the profile differences.
    
    Tests skill program personalization.
    """
    # Ensure profiles are different in interests or location
    assume(
        set(profile1['interests']) != set(profile2['interests']) or
        profile1['state'] != profile2['state'] or
        profile1['education_level'] != profile2['education_level']
    )
    
    # Ensure programs have some variety
    unique_programs = len(set(
        (p['category'], p['state'], p['mode'])
        for p in programs
    ))
    assume(unique_programs > 1)
    
    engine = PersonalizationEngine()
    
    # Get personalized recommendations for both profiles
    ranked1 = engine.rank_recommendations(programs, profile1, 'skill_program')
    ranked2 = engine.rank_recommendations(programs, profile2, 'skill_program')
    
    # Extract scores
    scores1 = {item[0]['program_id']: item[1] for item in ranked1}
    scores2 = {item[0]['program_id']: item[1] for item in ranked2}
    
    # Property 1: At least one program should have different scores
    has_difference = False
    for program_id in scores1.keys():
        if program_id in scores2:
            if abs(scores1[program_id] - scores2[program_id]) > 0.01:
                has_difference = True
                break
    
    # Count programs with location or category criteria
    programs_with_criteria = sum(
        1 for p in programs
        if p['state'] is not None or p['mode'] != 'online'
    )
    
    # Only assert difference if there are programs with personalization criteria
    if programs_with_criteria > 0 or any(profile1['interests']) or any(profile2['interests']):
        assert has_difference, \
            "Skill programs should have different scores for different user profiles"
    
    # Property 2: Rankings should be ordered by score descending
    for i in range(len(ranked1) - 1):
        assert ranked1[i][1] >= ranked1[i+1][1], \
            "Profile 1 program rankings should be in descending order by score"
    
    for i in range(len(ranked2) - 1):
        assert ranked2[i][1] >= ranked2[i+1][1], \
            "Profile 2 program rankings should be in descending order by score"
    
    # Property 3: All scores should be between 0 and 1
    for item, score, _ in ranked1:
        assert 0 <= score <= 1, f"Program score should be between 0 and 1, got {score}"
    
    for item, score, _ in ranked2:
        assert 0 <= score <= 1, f"Program score should be between 0 and 1, got {score}"


def test_specific_location_based_filtering():
    """
    Specific example test: Users from different states should get different
    state-specific scheme recommendations.
    """
    engine = PersonalizationEngine()
    
    # Profile 1: Maharashtra farmer
    profile1 = {
        'user_id': str(uuid.uuid4()),
        'state': 'Maharashtra',
        'district': 'Pune',
        'occupation': 'Farmer',
        'education_level': '10th',
        'age': 35,
        'income_bracket': '0-50000'
    }
    
    # Profile 2: Karnataka farmer (same occupation, different state)
    profile2 = {
        'user_id': str(uuid.uuid4()),
        'state': 'Karnataka',
        'district': 'Bangalore',
        'occupation': 'Farmer',
        'education_level': '10th',
        'age': 35,
        'income_bracket': '0-50000'
    }
    
    # Schemes: one for Maharashtra, one for Karnataka, one central
    schemes = [
        {
            'scheme_id': str(uuid.uuid4()),
            'name': 'Maharashtra Farmer Scheme',
            'category': 'agriculture',
            'state': 'Maharashtra',
            'eligibility_criteria': {'occupation': ['Farmer']},
            'benefits': ['Support for farmers'],
            'department': 'Agriculture'
        },
        {
            'scheme_id': str(uuid.uuid4()),
            'name': 'Karnataka Farmer Scheme',
            'category': 'agriculture',
            'state': 'Karnataka',
            'eligibility_criteria': {'occupation': ['Farmer']},
            'benefits': ['Support for farmers'],
            'department': 'Agriculture'
        },
        {
            'scheme_id': str(uuid.uuid4()),
            'name': 'PM-KISAN (Central)',
            'category': 'agriculture',
            'state': None,  # Central scheme
            'eligibility_criteria': {'occupation': ['Farmer']},
            'benefits': ['Income support'],
            'department': 'Agriculture'
        }
    ]
    
    # Get recommendations
    ranked1 = engine.rank_recommendations(schemes, profile1, 'scheme')
    ranked2 = engine.rank_recommendations(schemes, profile2, 'scheme')
    
    # Maharashtra user should rank Maharashtra scheme higher
    mh_scheme_score_p1 = next(score for item, score, _ in ranked1 if 'Maharashtra' in item['name'])
    ka_scheme_score_p1 = next(score for item, score, _ in ranked1 if 'Karnataka' in item['name'])
    
    assert mh_scheme_score_p1 > ka_scheme_score_p1, \
        "Maharashtra user should rank Maharashtra scheme higher than Karnataka scheme"
    
    # Karnataka user should rank Karnataka scheme higher
    mh_scheme_score_p2 = next(score for item, score, _ in ranked2 if 'Maharashtra' in item['name'])
    ka_scheme_score_p2 = next(score for item, score, _ in ranked2 if 'Karnataka' in item['name'])
    
    assert ka_scheme_score_p2 > mh_scheme_score_p2, \
        "Karnataka user should rank Karnataka scheme higher than Maharashtra scheme"
    
    # Both should rank central scheme reasonably high
    central_score_p1 = next(score for item, score, _ in ranked1 if 'Central' in item['name'])
    central_score_p2 = next(score for item, score, _ in ranked2 if 'Central' in item['name'])
    
    assert central_score_p1 > 0.5, "Central scheme should have good score for profile 1"
    assert central_score_p2 > 0.5, "Central scheme should have good score for profile 2"


def test_specific_occupation_based_filtering():
    """
    Specific example test: Users with different occupations should get different
    occupation-specific recommendations.
    """
    engine = PersonalizationEngine()
    
    # Profile 1: Farmer
    profile1 = {
        'user_id': str(uuid.uuid4()),
        'state': 'Maharashtra',
        'occupation': 'Farmer',
        'education_level': '10th',
        'age': 35,
        'income_bracket': '0-50000'
    }
    
    # Profile 2: Student
    profile2 = {
        'user_id': str(uuid.uuid4()),
        'state': 'Maharashtra',
        'occupation': 'Student',
        'education_level': '12th',
        'age': 20,
        'income_bracket': '0-50000'
    }
    
    # Schemes: one for farmers, one for students
    schemes = [
        {
            'scheme_id': str(uuid.uuid4()),
            'name': 'Farmer Support Scheme',
            'category': 'agriculture',
            'state': None,
            'eligibility_criteria': {'occupation': ['Farmer']},
            'benefits': ['Agricultural support'],
            'department': 'Agriculture'
        },
        {
            'scheme_id': str(uuid.uuid4()),
            'name': 'Student Scholarship',
            'category': 'education',
            'state': None,
            'eligibility_criteria': {'occupation': ['Student']},
            'benefits': ['Educational support'],
            'department': 'Education'
        }
    ]
    
    # Get recommendations
    ranked1 = engine.rank_recommendations(schemes, profile1, 'scheme')
    ranked2 = engine.rank_recommendations(schemes, profile2, 'scheme')
    
    # Farmer should rank farmer scheme higher
    farmer_score_p1 = next(score for item, score, _ in ranked1 if 'Farmer' in item['name'])
    student_score_p1 = next(score for item, score, _ in ranked1 if 'Student' in item['name'])
    
    assert farmer_score_p1 > student_score_p1, \
        "Farmer should rank farmer scheme higher than student scheme"
    
    # Student should rank student scheme higher
    farmer_score_p2 = next(score for item, score, _ in ranked2 if 'Farmer' in item['name'])
    student_score_p2 = next(score for item, score, _ in ranked2 if 'Student' in item['name'])
    
    assert student_score_p2 > farmer_score_p2, \
        "Student should rank student scheme higher than farmer scheme"


def test_specific_education_based_job_filtering():
    """
    Specific example test: Users with different education levels should get
    different job recommendations based on qualifications.
    """
    engine = PersonalizationEngine()
    
    # Profile 1: Graduate
    profile1 = {
        'user_id': str(uuid.uuid4()),
        'state': 'Maharashtra',
        'education_level': 'graduate',
        'experience_years': 2,
        'skills': ['python', 'java']
    }
    
    # Profile 2: 12th pass
    profile2 = {
        'user_id': str(uuid.uuid4()),
        'state': 'Maharashtra',
        'education_level': '12th',
        'experience_years': 0,
        'skills': []
    }
    
    # Jobs: one requiring graduate, one requiring 12th
    jobs = [
        {
            'job_id': str(uuid.uuid4()),
            'title': 'Software Developer',
            'department': 'IT',
            'location': {'state': 'Maharashtra', 'district': 'Mumbai'},
            'qualifications': {
                'education_level': 'graduate',
                'experience_years': 1,
                'skills': ['python']
            }
        },
        {
            'job_id': str(uuid.uuid4()),
            'title': 'Clerk',
            'department': 'Administration',
            'location': {'state': 'Maharashtra', 'district': 'Mumbai'},
            'qualifications': {
                'education_level': '12th',
                'experience_years': 0,
                'skills': []
            }
        }
    ]
    
    # Get recommendations
    ranked1 = engine.rank_recommendations(jobs, profile1, 'job')
    ranked2 = engine.rank_recommendations(jobs, profile2, 'job')
    
    # Graduate should rank developer job higher
    dev_score_p1 = next(score for item, score, _ in ranked1 if 'Developer' in item['title'])
    clerk_score_p1 = next(score for item, score, _ in ranked1 if 'Clerk' in item['title'])
    
    assert dev_score_p1 > clerk_score_p1, \
        "Graduate should rank developer job higher than clerk job"
    
    # 12th pass should rank clerk job higher (or at least not much lower)
    dev_score_p2 = next(score for item, score, _ in ranked2 if 'Developer' in item['title'])
    clerk_score_p2 = next(score for item, score, _ in ranked2 if 'Clerk' in item['title'])
    
    assert clerk_score_p2 >= dev_score_p2, \
        "12th pass should rank clerk job at least as high as developer job"


def test_explanation_presence():
    """
    Test that all recommendations include explanations.
    """
    engine = PersonalizationEngine()
    
    profile = {
        'user_id': str(uuid.uuid4()),
        'state': 'Maharashtra',
        'occupation': 'Farmer',
        'education_level': '10th',
        'age': 35
    }
    
    schemes = [
        {
            'scheme_id': str(uuid.uuid4()),
            'name': 'Test Scheme',
            'category': 'agriculture',
            'state': 'Maharashtra',
            'eligibility_criteria': {'occupation': ['Farmer']},
            'benefits': ['Support'],
            'department': 'Agriculture'
        }
    ]
    
    ranked = engine.rank_recommendations(schemes, profile, 'scheme')
    
    # All recommendations should have explanations
    for item, score, explanation in ranked:
        assert explanation is not None, "Explanation should not be None"
        assert len(explanation) > 0, "Explanation should not be empty"
        assert isinstance(explanation, str), "Explanation should be a string"
