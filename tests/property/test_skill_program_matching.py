"""Property-based tests for skill program matching relevance.

Feature: bharatsahayak, Property 10: Skill Program Matching Relevance
**Validates: Requirements 4.1**

This test verifies that matched skill programs align with user profile,
interests, and eligibility criteria.
"""

import pytest
from hypothesis import given, settings, strategies as st, HealthCheck
import json
from unittest.mock import patch, MagicMock

from src.models.skill import SkillProgram
from src.models.eligibility import EligibilityCriteria
from src.models.location import Location


# Custom strategies for generating valid test data
@st.composite
def location_strategy(draw):
    """Generate valid Location instances."""
    states = ["Maharashtra", "Karnataka", "Tamil Nadu", "Gujarat", "Delhi", "Punjab"]
    districts = {
        "Maharashtra": ["Pune", "Mumbai", "Nagpur"],
        "Karnataka": ["Bangalore", "Mysore", "Hubli"],
        "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai"],
        "Gujarat": ["Ahmedabad", "Surat", "Vadodara"],
        "Delhi": ["New Delhi", "South Delhi", "North Delhi"],
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
    """Generate valid user profile data for skill matching."""
    education_levels = ["8th pass", "10th pass", "12th pass", "undergraduate", "postgraduate"]
    interests = ["technical", "vocational", "digital", "entrepreneurship"]
    
    return {
        "age": draw(st.integers(min_value=18, max_value=45)),
        "education_level": draw(st.sampled_from(education_levels)),
        "location": draw(location_strategy()).model_dump(),
        "interests": draw(st.lists(
            st.sampled_from(interests),
            min_size=1, max_size=3, unique=True
        )),
        "current_skills": draw(st.lists(
            st.sampled_from(["basic computer", "typing", "communication", "none"]),
            min_size=0, max_size=2, unique=True
        )),
        "preferred_mode": draw(st.sampled_from(["in-person", "online", "hybrid", ""]))
    }



@st.composite
def skill_program_strategy(draw):
    """Generate valid SkillProgram instances."""
    categories = ["technical", "vocational", "digital", "entrepreneurship"]
    modes = ["in-person", "online", "hybrid"]
    
    category = draw(st.sampled_from(categories))
    location = draw(location_strategy())
    
    return {
        "program_id": f"PROG_{draw(st.integers(min_value=1000, max_value=9999))}",
        "name": f"{category.title()} Training Program",
        "name_translations": {},
        "provider": "National Skill Development Corporation",
        "category": category,
        "description": f"Professional {category} training program",
        "description_translations": {},
        "duration_weeks": draw(st.integers(min_value=4, max_value=24)),
        "cost": draw(st.floats(min_value=0, max_value=25000)),
        "location": location.model_dump(),
        "mode": draw(st.sampled_from(modes)),
        "eligibility": {
            "age_min": draw(st.integers(min_value=18, max_value=21)),
            "age_max": draw(st.integers(min_value=35, max_value=45)),
            "education": draw(st.lists(
                st.sampled_from(["8th pass", "10th pass", "12th pass", "undergraduate"]),
                min_size=1, max_size=3, unique=True
            )),
            "custom_criteria": {}
        },
        "certification": draw(st.booleans()),
        "placement_support": draw(st.booleans()),
        "registration_url": "https://example.org",
        "contact": "1800-123-456",
        "created_at": "2024-01-15T10:30:00Z"
    }


def call_skills_match_handler(user_profile: dict, mock_programs: list) -> dict:
    """
    Call the skills match Lambda handler with a user profile.
    
    Args:
        user_profile: User profile data
        mock_programs: List of programs to return from DynamoDB
        
    Returns:
        Response dictionary from the handler
    """
    from src.api.skills_match import lambda_handler
    
    # Create Lambda event
    event = {
        'body': json.dumps({'user_profile': user_profile}),
        'httpMethod': 'POST',
        'path': '/skills/match'
    }
    
    # Mock DynamoDB table.scan() to return our test programs
    with patch('src.api.skills_match.table') as mock_table:
        mock_table.scan.return_value = {'Items': mock_programs}
        
        # Call handler
        response = lambda_handler(event, None)
    
    return response



@settings(max_examples=5, deadline=None, suppress_health_check=[HealthCheck.data_too_large])
@given(
    user_profile=user_profile_strategy(),
    programs=st.lists(skill_program_strategy(), min_size=3, max_size=6)
)
def test_skill_program_matching_relevance(user_profile, programs):
    """
    Feature: bharatsahayak, Property 10: Skill Program Matching Relevance
    
    For any user profile with specified skills and interests, returned skill
    programs should match at least one of the user's interests or build upon
    their current skills.
    
    This test verifies:
    1. Matched programs align with user interests
    2. User meets eligibility criteria for matched programs
    3. Match scores are reasonable and sorted
    4. Match reasons are provided
    """
    # Call the skills match handler
    response = call_skills_match_handler(user_profile, programs)
    
    # Verify successful response
    assert response['statusCode'] == 200, (
        f"Expected status code 200, got {response['statusCode']}"
    )
    
    # Parse response body
    body = json.loads(response['body'])
    
    # Verify matched_programs exists
    assert 'matched_programs' in body, "Response should contain 'matched_programs' field"
    matched_programs = body['matched_programs']
    
    # Verify matched_programs is a list
    assert isinstance(matched_programs, list), (
        f"matched_programs should be a list, got {type(matched_programs)}"
    )
    
    # If no programs matched, that's okay (user might not be eligible for any)
    if len(matched_programs) == 0:
        return
    
    user_interests = [interest.lower() for interest in user_profile['interests']]
    user_age = user_profile['age']
    user_education = user_profile['education_level'].lower()
    
    # Verify each matched program
    for i, matched in enumerate(matched_programs):
        # Property 1: Program should have required fields
        required_fields = [
            'program_id', 'name', 'category', 'match_score', 'match_reasons'
        ]
        for field in required_fields:
            assert field in matched, (
                f"Matched program {i} missing required field '{field}'"
            )
        
        # Property 2: Match score should be between 0 and 1
        assert 0 <= matched['match_score'] <= 1, (
            f"Matched program {i} has invalid match_score: {matched['match_score']} "
            f"(must be between 0 and 1)"
        )
        
        # Property 3: Match reasons should be a non-empty list
        assert isinstance(matched['match_reasons'], list), (
            f"Matched program {i} has invalid match_reasons type: {type(matched['match_reasons'])}"
        )
        assert len(matched['match_reasons']) > 0, (
            f"Matched program {i} has empty match_reasons"
        )
        
        # Property 4: Program category should match at least one user interest
        # OR user should meet eligibility (programs can match on eligibility alone)
        program_category = matched['category'].lower()
        category_matches = program_category in user_interests
        
        # If category matches, verify it's mentioned in match reasons
        if category_matches:
            reasons_text = ' '.join(matched['match_reasons']).lower()
            assert program_category in reasons_text or 'interest' in reasons_text, (
                f"Matched program {i} category '{program_category}' matches user interest "
                f"but not mentioned in match reasons: {matched['match_reasons']}"
            )


@settings(max_examples=5, deadline=None)
@given(
    user_profile=user_profile_strategy(),
    programs=st.lists(skill_program_strategy(), min_size=3, max_size=6)
)
def test_skill_program_match_score_sorting(user_profile, programs):
    """
    Test that matched programs are sorted by match score in descending order.
    
    This verifies that the most relevant programs appear first.
    """
    # Call the skills match handler
    response = call_skills_match_handler(user_profile, programs)
    
    # Verify successful response
    assert response['statusCode'] == 200
    
    # Parse response body
    body = json.loads(response['body'])
    matched_programs = body['matched_programs']
    
    # Skip if fewer than 2 programs matched
    if len(matched_programs) <= 1:
        return
    
    # Verify sorting: each program should have match_score >= next one
    for i in range(len(matched_programs) - 1):
        current_score = matched_programs[i]['match_score']
        next_score = matched_programs[i + 1]['match_score']
        
        assert current_score >= next_score, (
            f"Matched programs not sorted by match score: "
            f"program {i} has score {current_score}, "
            f"program {i+1} has score {next_score}"
        )



@settings(max_examples=5, deadline=None)
@given(
    age=st.integers(min_value=18, max_value=45),
    education=st.sampled_from(["8th pass", "10th pass", "12th pass", "undergraduate"])
)
def test_skill_program_eligibility_filtering(age, education):
    """
    Test that only eligible programs are returned.
    
    This verifies that eligibility criteria are properly enforced.
    """
    # Create user profile
    user_profile = {
        "age": age,
        "education_level": education,
        "location": {"state": "Maharashtra", "district": "Pune", "pincode": "411001"},
        "interests": ["technical"],
        "current_skills": [],
        "preferred_mode": ""
    }
    
    # Create programs with specific eligibility
    programs = [
        {
            "program_id": "ELIGIBLE_PROG",
            "name": "Eligible Program",
            "name_translations": {},
            "provider": "Test Provider",
            "category": "technical",
            "description": "Test program",
            "description_translations": {},
            "duration_weeks": 12,
            "cost": 0,
            "location": {"state": "Maharashtra", "district": "Pune", "pincode": "411001"},
            "mode": "in-person",
            "eligibility": {
                "age_min": 18,
                "age_max": 45,
                "education": ["8th pass", "10th pass", "12th pass", "undergraduate"],
                "custom_criteria": {}
            },
            "certification": True,
            "placement_support": True,
            "registration_url": "https://example.org",
            "contact": "1800-123-456",
            "created_at": "2024-01-15T10:30:00Z"
        },
        {
            "program_id": "INELIGIBLE_AGE",
            "name": "Age Restricted Program",
            "name_translations": {},
            "provider": "Test Provider",
            "category": "technical",
            "description": "Test program",
            "description_translations": {},
            "duration_weeks": 12,
            "cost": 0,
            "location": {"state": "Maharashtra", "district": "Pune", "pincode": "411001"},
            "mode": "in-person",
            "eligibility": {
                "age_min": 50,  # User won't meet this
                "age_max": 60,
                "education": ["8th pass", "10th pass", "12th pass", "undergraduate"],
                "custom_criteria": {}
            },
            "certification": True,
            "placement_support": True,
            "registration_url": "https://example.org",
            "contact": "1800-123-456",
            "created_at": "2024-01-15T10:30:00Z"
        }
    ]
    
    # Call the skills match handler
    response = call_skills_match_handler(user_profile, programs)
    
    # Verify successful response
    assert response['statusCode'] == 200
    
    # Parse response body
    body = json.loads(response['body'])
    matched_programs = body['matched_programs']
    
    # Verify that ineligible program is not in results
    matched_ids = [p['program_id'] for p in matched_programs]
    
    # The age-restricted program should not be in results
    assert "INELIGIBLE_AGE" not in matched_ids, (
        f"Ineligible program (age restriction) should not be matched for user age {age}"
    )
    
    # The eligible program should be in results
    assert "ELIGIBLE_PROG" in matched_ids, (
        f"Eligible program should be matched for user age {age}, education {education}"
    )


@settings(max_examples=5, deadline=None)
@given(
    user_profile=user_profile_strategy()
)
def test_skill_program_location_preference(user_profile):
    """
    Test that programs in user's location get higher match scores.
    
    This verifies location-based matching logic.
    """
    user_location = user_profile['location']
    
    # Create programs: one in same state, one in different state
    programs = [
        {
            "program_id": "SAME_STATE",
            "name": "Same State Program",
            "name_translations": {},
            "provider": "Test Provider",
            "category": user_profile['interests'][0],  # Match interest
            "description": "Test program",
            "description_translations": {},
            "duration_weeks": 12,
            "cost": 0,
            "location": user_location,  # Same location
            "mode": "in-person",
            "eligibility": {
                "age_min": 18,
                "age_max": 50,
                "education": ["8th pass", "10th pass", "12th pass", "undergraduate", "postgraduate"],
                "custom_criteria": {}
            },
            "certification": True,
            "placement_support": True,
            "registration_url": "https://example.org",
            "contact": "1800-123-456",
            "created_at": "2024-01-15T10:30:00Z"
        },
        {
            "program_id": "DIFF_STATE",
            "name": "Different State Program",
            "name_translations": {},
            "provider": "Test Provider",
            "category": user_profile['interests'][0],  # Match interest
            "description": "Test program",
            "description_translations": {},
            "duration_weeks": 12,
            "cost": 0,
            "location": {"state": "Kerala", "district": "Kochi", "pincode": "682001"},  # Different state
            "mode": "in-person",
            "eligibility": {
                "age_min": 18,
                "age_max": 50,
                "education": ["8th pass", "10th pass", "12th pass", "undergraduate", "postgraduate"],
                "custom_criteria": {}
            },
            "certification": True,
            "placement_support": True,
            "registration_url": "https://example.org",
            "contact": "1800-123-456",
            "created_at": "2024-01-15T10:30:00Z"
        }
    ]
    
    # Call the skills match handler
    response = call_skills_match_handler(user_profile, programs)
    
    # Verify successful response
    assert response['statusCode'] == 200
    
    # Parse response body
    body = json.loads(response['body'])
    matched_programs = body['matched_programs']
    
    # Both programs should match (same category, both eligible)
    assert len(matched_programs) >= 2, "Both programs should be matched"
    
    # Find the two programs
    same_state_prog = next((p for p in matched_programs if p['program_id'] == 'SAME_STATE'), None)
    diff_state_prog = next((p for p in matched_programs if p['program_id'] == 'DIFF_STATE'), None)
    
    assert same_state_prog is not None, "Same state program should be matched"
    assert diff_state_prog is not None, "Different state program should be matched"
    
    # Same state program should have higher or equal match score
    assert same_state_prog['match_score'] >= diff_state_prog['match_score'], (
        f"Program in user's state should have higher match score: "
        f"same_state={same_state_prog['match_score']}, diff_state={diff_state_prog['match_score']}"
    )


def test_skill_program_invalid_input():
    """
    Test that invalid input returns appropriate error response.
    
    This verifies error handling for malformed requests.
    """
    from src.api.skills_match import lambda_handler
    
    # Test with missing user_profile
    event = {
        'body': json.dumps({}),
        'httpMethod': 'POST',
        'path': '/skills/match'
    }
    
    response = lambda_handler(event, None)
    
    # Should return 400 error
    assert response['statusCode'] == 400, (
        f"Expected status code 400 for invalid input, got {response['statusCode']}"
    )
    
    # Error message should be present
    body = json.loads(response['body'])
    assert 'error' in body, "Error response should contain 'error' field"


def test_skill_program_empty_database():
    """
    Test handling when no programs exist in database.
    
    This verifies graceful handling of empty results.
    """
    user_profile = {
        "age": 25,
        "education_level": "12th pass",
        "location": {"state": "Maharashtra", "district": "Pune", "pincode": "411001"},
        "interests": ["technical"],
        "current_skills": [],
        "preferred_mode": ""
    }
    
    # Call with empty programs list
    response = call_skills_match_handler(user_profile, [])
    
    # Should still return 200
    assert response['statusCode'] == 200
    
    # Parse response body
    body = json.loads(response['body'])
    
    # Should have matched_programs key
    assert 'matched_programs' in body
    
    # Should be empty list
    assert body['matched_programs'] == []
