"""
Property-Based Test: Recommendation Explanation Presence
Feature: bharatsahayak, Property 22: Recommendation Explanation Presence

For any personalized recommendation, the output should include an explanation field
describing why the item was recommended based on user profile attributes.

Validates: Requirements 8.4
"""
import pytest
from hypothesis import given, settings, strategies as st
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
        'experience_years': draw(st.integers(min_value=0, max_value=20)),
        'career_goals': draw(st.lists(
            st.sampled_from(['software development', 'agriculture', 'teaching', 'business']),
            min_size=0, max_size=2, unique=True
        ))
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
    profile=user_profile_strategy(),
    schemes=st.lists(scheme_strategy(), min_size=1, max_size=10)
)
def test_scheme_recommendations_have_explanations(profile, schemes):
    """
    Feature: bharatsahayak, Property 22: Recommendation Explanation Presence
    
    For any personalized scheme recommendation, the output should include an
    explanation field describing why the scheme was recommended.
    
    Tests scheme recommendation explanations.
    """
    engine = PersonalizationEngine()
    
    # Get personalized recommendations
    ranked = engine.rank_recommendations(schemes, profile, 'scheme')
    
    # Property: Every recommendation must have a non-empty explanation
    for item, score, explanation in ranked:
        # Explanation must exist
        assert explanation is not None, \
            f"Scheme {item['name']} recommendation missing explanation"
        
        # Explanation must be a string
        assert isinstance(explanation, str), \
            f"Scheme {item['name']} explanation must be a string, got {type(explanation)}"
        
        # Explanation must not be empty
        assert len(explanation.strip()) > 0, \
            f"Scheme {item['name']} explanation is empty"
        
        # Explanation should be reasonably descriptive (at least 10 characters)
        assert len(explanation) >= 10, \
            f"Scheme {item['name']} explanation too short: '{explanation}'"
        
        # Explanation should reference why it was recommended
        # (should contain words like "because", "recommended", "matches", etc.)
        explanation_lower = explanation.lower()
        has_reasoning_words = any(
            word in explanation_lower
            for word in ['because', 'recommended', 'match', 'suitable', 'available', 
                        'designed', 'your', 'you', 'level', 'location', 'occupation']
        )
        assert has_reasoning_words, \
            f"Scheme {item['name']} explanation lacks reasoning context: '{explanation}'"


@settings(max_examples=100, deadline=None)
@given(
    profile=user_profile_strategy(),
    jobs=st.lists(job_strategy(), min_size=1, max_size=10)
)
def test_job_recommendations_have_explanations(profile, jobs):
    """
    Feature: bharatsahayak, Property 22: Recommendation Explanation Presence
    
    For any personalized job recommendation, the output should include an
    explanation field describing why the job was recommended.
    
    Tests job recommendation explanations.
    """
    engine = PersonalizationEngine()
    
    # Get personalized recommendations
    ranked = engine.rank_recommendations(jobs, profile, 'job')
    
    # Property: Every recommendation must have a non-empty explanation
    for item, score, explanation in ranked:
        # Explanation must exist
        assert explanation is not None, \
            f"Job {item['title']} recommendation missing explanation"
        
        # Explanation must be a string
        assert isinstance(explanation, str), \
            f"Job {item['title']} explanation must be a string, got {type(explanation)}"
        
        # Explanation must not be empty
        assert len(explanation.strip()) > 0, \
            f"Job {item['title']} explanation is empty"
        
        # Explanation should be reasonably descriptive
        assert len(explanation) >= 10, \
            f"Job {item['title']} explanation too short: '{explanation}'"
        
        # Explanation should reference why it was recommended
        explanation_lower = explanation.lower()
        has_reasoning_words = any(
            word in explanation_lower
            for word in ['because', 'recommended', 'match', 'suitable', 'meet',
                        'education', 'experience', 'skills', 'your', 'you', 'qualification']
        )
        assert has_reasoning_words, \
            f"Job {item['title']} explanation lacks reasoning context: '{explanation}'"


@settings(max_examples=100, deadline=None)
@given(
    profile=user_profile_strategy(),
    programs=st.lists(skill_program_strategy(), min_size=1, max_size=10)
)
def test_skill_program_recommendations_have_explanations(profile, programs):
    """
    Feature: bharatsahayak, Property 22: Recommendation Explanation Presence
    
    For any personalized skill program recommendation, the output should include
    an explanation field describing why the program was recommended.
    
    Tests skill program recommendation explanations.
    """
    engine = PersonalizationEngine()
    
    # Get personalized recommendations
    ranked = engine.rank_recommendations(programs, profile, 'skill_program')
    
    # Property: Every recommendation must have a non-empty explanation
    for item, score, explanation in ranked:
        # Explanation must exist
        assert explanation is not None, \
            f"Program {item['name']} recommendation missing explanation"
        
        # Explanation must be a string
        assert isinstance(explanation, str), \
            f"Program {item['name']} explanation must be a string, got {type(explanation)}"
        
        # Explanation must not be empty
        assert len(explanation.strip()) > 0, \
            f"Program {item['name']} explanation is empty"
        
        # Explanation should be reasonably descriptive
        assert len(explanation) >= 10, \
            f"Program {item['name']} explanation too short: '{explanation}'"
        
        # Explanation should reference why it was recommended
        explanation_lower = explanation.lower()
        has_reasoning_words = any(
            word in explanation_lower
            for word in ['because', 'recommended', 'match', 'suitable', 'aligns',
                        'interests', 'skills', 'your', 'you', 'available', 'builds']
        )
        assert has_reasoning_words, \
            f"Program {item['name']} explanation lacks reasoning context: '{explanation}'"


def test_explanation_references_user_profile_attributes():
    """
    Specific test: Explanations should reference specific user profile attributes
    that influenced the recommendation.
    """
    engine = PersonalizationEngine()
    
    # Create a profile with specific attributes
    profile = {
        'user_id': str(uuid.uuid4()),
        'state': 'Maharashtra',
        'district': 'Pune',
        'occupation': 'Farmer',
        'education_level': '10th',
        'age': 35,
        'income_bracket': '0-50000',
        'interests': ['agriculture', 'technology'],
        'skills': ['farming'],
        'experience_years': 10
    }
    
    # Scheme that matches the farmer profile
    scheme = {
        'scheme_id': str(uuid.uuid4()),
        'name': 'Maharashtra Farmer Support Scheme',
        'category': 'agriculture',
        'state': 'Maharashtra',
        'eligibility_criteria': {
            'occupation': ['Farmer'],
            'income_max': 100000,
            'age_min': 18,
            'age_max': 60
        },
        'benefits': ['Financial support for farmers'],
        'department': 'Agriculture'
    }
    
    # Get recommendation
    score, explanation = engine.score_scheme_relevance(scheme, profile)
    
    # Explanation should reference at least one profile attribute
    explanation_lower = explanation.lower()
    
    # Should mention occupation, location, or income
    profile_references = [
        'farmer' in explanation_lower,
        'maharashtra' in explanation_lower,
        'income' in explanation_lower,
        'age' in explanation_lower,
        'occupation' in explanation_lower,
        'location' in explanation_lower
    ]
    
    assert any(profile_references), \
        f"Explanation should reference user profile attributes: '{explanation}'"
    
    # Explanation should be informative
    assert len(explanation) > 20, \
        "Explanation should be reasonably detailed"


def test_explanation_differs_for_different_matches():
    """
    Specific test: Explanations should differ based on which profile attributes
    match the recommendation criteria.
    """
    engine = PersonalizationEngine()
    
    # Profile 1: Matches on occupation
    profile1 = {
        'user_id': str(uuid.uuid4()),
        'state': 'Karnataka',
        'occupation': 'Farmer',
        'education_level': '10th',
        'age': 35,
        'income_bracket': '0-50000'
    }
    
    # Profile 2: Matches on location
    profile2 = {
        'user_id': str(uuid.uuid4()),
        'state': 'Maharashtra',
        'occupation': 'Worker',
        'education_level': '10th',
        'age': 35,
        'income_bracket': '0-50000'
    }
    
    # Scheme for Maharashtra farmers
    scheme = {
        'scheme_id': str(uuid.uuid4()),
        'name': 'Maharashtra Farmer Scheme',
        'category': 'agriculture',
        'state': 'Maharashtra',
        'eligibility_criteria': {
            'occupation': ['Farmer']
        },
        'benefits': ['Support'],
        'department': 'Agriculture'
    }
    
    # Get explanations
    score1, explanation1 = engine.score_scheme_relevance(scheme, profile1)
    score2, explanation2 = engine.score_scheme_relevance(scheme, profile2)
    
    # Explanations should be different (different matching attributes)
    assert explanation1 != explanation2, \
        "Explanations should differ when different profile attributes match"
    
    # Profile 1 explanation should mention occupation (farmer)
    assert 'farmer' in explanation1.lower(), \
        "Explanation for farmer should mention occupation"
    
    # Profile 2 explanation should mention location (Maharashtra)
    assert 'maharashtra' in explanation2.lower(), \
        "Explanation for Maharashtra resident should mention location"


def test_explanation_quality_for_high_vs_low_scores():
    """
    Specific test: Explanations should reflect the quality of the match
    (high score vs low score).
    """
    engine = PersonalizationEngine()
    
    profile = {
        'user_id': str(uuid.uuid4()),
        'state': 'Maharashtra',
        'occupation': 'Farmer',
        'education_level': 'graduate',
        'age': 35,
        'income_bracket': '0-50000',
        'interests': ['agriculture']
    }
    
    # High-match scheme (matches occupation, location, income, age)
    high_match_scheme = {
        'scheme_id': str(uuid.uuid4()),
        'name': 'Perfect Match Scheme',
        'category': 'agriculture',
        'state': 'Maharashtra',
        'eligibility_criteria': {
            'occupation': ['Farmer'],
            'income_max': 100000,
            'age_min': 18,
            'age_max': 60,
            'education': ['graduate']
        },
        'benefits': ['Support'],
        'department': 'Agriculture'
    }
    
    # Low-match scheme (different state, different occupation)
    low_match_scheme = {
        'scheme_id': str(uuid.uuid4()),
        'name': 'Poor Match Scheme',
        'category': 'health',
        'state': 'Karnataka',
        'eligibility_criteria': {
            'occupation': ['Student']
        },
        'benefits': ['Support'],
        'department': 'Health'
    }
    
    # Get scores and explanations
    high_score, high_explanation = engine.score_scheme_relevance(high_match_scheme, profile)
    low_score, low_explanation = engine.score_scheme_relevance(low_match_scheme, profile)
    
    # High score should be significantly higher
    assert high_score > low_score + 0.2, \
        "High-match scheme should have significantly higher score"
    
    # Both should have explanations
    assert len(high_explanation) > 0, "High-match scheme should have explanation"
    assert len(low_explanation) > 0, "Low-match scheme should have explanation"
    
    # High-match explanation should mention multiple matching attributes
    high_explanation_lower = high_explanation.lower()
    match_count = sum([
        'farmer' in high_explanation_lower or 'occupation' in high_explanation_lower,
        'maharashtra' in high_explanation_lower or 'location' in high_explanation_lower,
        'income' in high_explanation_lower,
        'age' in high_explanation_lower,
        'education' in high_explanation_lower
    ])
    
    assert match_count >= 2, \
        f"High-match explanation should mention multiple matching attributes: '{high_explanation}'"


def test_explanation_for_job_with_skills_match():
    """
    Specific test: Job explanations should mention skills when there's a skills match.
    """
    engine = PersonalizationEngine()
    
    profile = {
        'user_id': str(uuid.uuid4()),
        'state': 'Maharashtra',
        'education_level': 'graduate',
        'experience_years': 3,
        'skills': ['python', 'java', 'teaching']
    }
    
    job = {
        'job_id': str(uuid.uuid4()),
        'title': 'Software Developer',
        'department': 'IT',
        'location': {'state': 'Maharashtra', 'district': 'Mumbai'},
        'qualifications': {
            'education_level': 'graduate',
            'experience_years': 2,
            'skills': ['python', 'java']
        }
    }
    
    score, explanation = engine.score_job_relevance(job, profile)
    
    # Explanation should mention skills match
    explanation_lower = explanation.lower()
    assert 'skill' in explanation_lower, \
        f"Job explanation should mention skills match: '{explanation}'"
    
    # Should mention the number of matching skills
    assert '2' in explanation or 'two' in explanation_lower, \
        f"Job explanation should mention number of matching skills: '{explanation}'"


def test_explanation_for_skill_program_with_interests():
    """
    Specific test: Skill program explanations should mention interests when there's a match.
    """
    engine = PersonalizationEngine()
    
    profile = {
        'user_id': str(uuid.uuid4()),
        'state': 'Maharashtra',
        'education_level': '12th',
        'interests': ['technology', 'digital'],
        'skills': [],
        'career_goals': ['software development']
    }
    
    program = {
        'program_id': str(uuid.uuid4()),
        'name': 'Digital Skills Training',
        'provider': 'Government Institute',
        'category': 'digital',
        'description': 'Learn technology and digital skills',
        'duration_weeks': 12,
        'cost': 0,
        'state': 'Maharashtra',
        'district': 'Pune',
        'mode': 'online',
        'eligibility_criteria': {'education': ['12th']},
        'certification': True,
        'placement_support': True
    }
    
    score, explanation = engine.score_skill_program_relevance(program, profile)
    
    # Explanation should mention interests
    explanation_lower = explanation.lower()
    assert 'interest' in explanation_lower or 'match' in explanation_lower, \
        f"Skill program explanation should mention interests: '{explanation}'"
    
    # Should be reasonably detailed
    assert len(explanation) > 20, \
        "Skill program explanation should be detailed"
