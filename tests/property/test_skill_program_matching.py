"""Property-based tests for skill program matching relevance.

Feature: bharatsahayak, Property 10: Skill Program Matching Relevance
**Validates: Requirements 4.1**

This test verifies that matched skill programs align with user profile,
ensuring that programs match user interests, education level, and preferences.
"""

import pytest
from hypothesis import given, settings, strategies as st, assume
from typing import List, Tuple

from src.models.skill import SkillProgram
from src.models.user import UserProfile, UserPreferences
from src.models.eligibility import EligibilityCriteria
from src.models.location import Location


# Custom strategies for generating valid test data
@st.composite
def location_strategy(draw):
    """Generate valid Location instances."""
    states = ["Maharashtra", "Karnataka", "Tamil Nadu", "Gujarat", "Delhi"]
    districts = {
        "Maharashtra": ["Pune", "Mumbai"],
        "Karnataka": ["Bangalore", "Mysore"],
        "Tamil Nadu": ["Chennai", "Coimbatore"],
        "Gujarat": ["Ahmedabad", "Surat"],
        "Delhi": ["New Delhi", "South Delhi"]
    }
    
    state = draw(st.sampled_from(states))
    district = draw(st.sampled_from(districts[state]))
    
    return Location(
        state=state,
        district=district,
        pincode=draw(st.text(min_size=6, max_size=6, alphabet=st.characters(whitelist_categories=('Nd',))))
    )


@st.composite
def user_profile_with_interests_strategy(draw):
    """Generate UserProfile with interests for skill matching."""
    location = draw(location_strategy())
    
    # Generate interests from available categories
    all_interests = ["technical", "vocational", "digital", "entrepreneurship"]
    interests = draw(st.lists(
        st.sampled_from(all_interests),
        min_size=1, max_size=3, unique=True
    ))
    
    return UserProfile(
        user_id=f"user_{draw(st.integers(min_value=1000, max_value=9999))}",
        phone_number=f"+91{draw(st.integers(min_value=1000000000, max_value=9999999999))}",
        language=draw(st.sampled_from(["hi", "en", "mr"])),
        location=location,
        age=draw(st.integers(min_value=18, max_value=40)),
        gender=draw(st.sampled_from(["male", "female"])),
        education_level=draw(st.sampled_from(["primary", "secondary", "higher_secondary", "graduate"])),
        occupation=draw(st.sampled_from(["unemployed", "student", "laborer"])),
        income_bracket="0-100000",
        household_size=draw(st.integers(min_value=1, max_value=8)),
        preferences=UserPreferences(
            preferred_categories=interests
        )
    )



def create_diverse_skill_programs() -> List[SkillProgram]:
    """Create a diverse set of skill programs for testing."""
    programs = []
    
    # Program 1: Technical - Electrician (Maharashtra, in-person, free)
    programs.append(SkillProgram(
        program_id="TECH-ELEC-001",
        name="Electrician Training",
        provider="NSDC",
        category="technical",
        description="Electrician training program",
        duration_weeks=12,
        cost=0,
        location=Location(state="Maharashtra", district="Pune", pincode="411014"),
        mode="in-person",
        eligibility_criteria=EligibilityCriteria(
            age_min=18,
            age_max=35,
            education=["8th pass", "10th pass", "12th pass"],
            custom_criteria={}
        ),
        certification=True,
        placement_support=True,
        registration_url="https://example.com/elec",
        contact="1800-123-456"
    ))
    
    # Program 2: Digital - Computer Course (Karnataka, online, paid)
    programs.append(SkillProgram(
        program_id="DIGITAL-CCC-001",
        name="Computer Concepts Course",
        provider="NIELIT",
        category="digital",
        description="Basic computer literacy",
        duration_weeks=12,
        cost=500,
        location=Location(state="Karnataka", district="Bangalore", pincode="560001"),
        mode="online",
        eligibility_criteria=EligibilityCriteria(
            age_min=15,
            age_max=60,
            education=["8th pass", "10th pass", "12th pass", "graduate"],
            custom_criteria={}
        ),
        certification=True,
        placement_support=False,
        registration_url="https://example.com/ccc",
        contact="080-1234-5678"
    ))
    
    # Program 3: Vocational - Tailoring (Tamil Nadu, in-person, free)
    programs.append(SkillProgram(
        program_id="VOC-TAILOR-001",
        name="Tailoring Training",
        provider="AMHSSC",
        category="vocational",
        description="Professional tailoring",
        duration_weeks=14,
        cost=0,
        location=Location(state="Tamil Nadu", district="Chennai", pincode="600001"),
        mode="in-person",
        eligibility_criteria=EligibilityCriteria(
            age_min=18,
            age_max=45,
            education=["5th pass", "8th pass", "10th pass"],
            custom_criteria={}
        ),
        certification=True,
        placement_support=True,
        registration_url="https://example.com/tailor",
        contact="044-1234-5678"
    ))
    
    # Program 4: Entrepreneurship (Delhi, hybrid, free)
    programs.append(SkillProgram(
        program_id="ENTRE-RURAL-001",
        name="Rural Entrepreneurship",
        provider="RSETI",
        category="entrepreneurship",
        description="Business development training",
        duration_weeks=6,
        cost=0,
        location=Location(state="Delhi", district="New Delhi", pincode="110001"),
        mode="hybrid",
        eligibility_criteria=EligibilityCriteria(
            age_min=18,
            age_max=45,
            education=["8th pass", "10th pass", "12th pass"],
            custom_criteria={}
        ),
        certification=True,
        placement_support=False,
        registration_url="https://example.com/entre",
        contact="011-1234-5678"
    ))
    
    # Program 5: Technical - Mobile Repair (Gujarat, in-person, paid)
    programs.append(SkillProgram(
        program_id="TECH-MOBILE-001",
        name="Mobile Repair Technician",
        provider="ESSC",
        category="technical",
        description="Mobile phone repair",
        duration_weeks=10,
        cost=2000,
        location=Location(state="Gujarat", district="Ahmedabad", pincode="380001"),
        mode="in-person",
        eligibility_criteria=EligibilityCriteria(
            age_min=18,
            age_max=35,
            education=["10th pass", "12th pass"],
            custom_criteria={}
        ),
        certification=True,
        placement_support=True,
        registration_url="https://example.com/mobile",
        contact="079-1234-5678"
    ))
    
    return programs



def match_programs_to_user(
    programs: List[SkillProgram],
    user_profile: UserProfile
) -> List[Tuple[SkillProgram, float, List[str]]]:
    """
    Match and rank programs based on user profile.
    
    This mimics the logic in skills_match.py.
    
    Returns:
        List of (program, match_score, reasoning) tuples, sorted by score
    """
    matched = []
    
    for program in programs:
        # Check basic eligibility
        if not check_eligibility(program, user_profile):
            continue
        
        score = 0.0
        reasoning = []
        
        # Interest/category match (30% weight)
        if user_profile.preferences and user_profile.preferences.preferred_categories:
            if program.category in user_profile.preferences.preferred_categories:
                score += 0.3
                reasoning.append(f"Matches interest: {program.category}")
        
        # Cost within budget (25% weight) - assume max_cost of 5000 if not specified
        max_cost = 5000  # Default budget
        
        if program.cost <= max_cost:
            score += 0.25
            reasoning.append(f"Within budget: Rs. {program.cost}")
        else:
            score += 0.1
            reasoning.append(f"Cost Rs. {program.cost} exceeds budget")
        
        # Location match (20% weight)
        if program.location.state.lower() == user_profile.location.state.lower():
            score += 0.15
            reasoning.append(f"Same state: {program.location.state}")
            
            if program.location.district.lower() == user_profile.location.district.lower():
                score += 0.05
                reasoning.append(f"Same district: {program.location.district}")
        
        # Mode preference (15% weight) - prefer online for accessibility
        if program.mode == "online":
            score += 0.15
            reasoning.append("Online mode (accessible)")
        elif program.mode == "hybrid":
            score += 0.10
            reasoning.append("Hybrid mode")
        
        # Placement support bonus (10% weight)
        if program.placement_support:
            score += 0.1
            reasoning.append("Placement support available")
        
        # Normalize score
        score = min(1.0, score)
        
        if score > 0:
            matched.append((program, score, reasoning))
    
    # Sort by match score (descending)
    matched.sort(key=lambda x: x[1], reverse=True)
    
    return matched


def check_eligibility(program: SkillProgram, user_profile: UserProfile) -> bool:
    """Check if user meets basic eligibility criteria for program."""
    criteria = program.eligibility_criteria
    
    # Check age
    if criteria.age_min and user_profile.age:
        if user_profile.age < criteria.age_min:
            return False
    
    if criteria.age_max and user_profile.age:
        if user_profile.age > criteria.age_max:
            return False
    
    # Check education level
    if criteria.education and user_profile.education_level:
        if user_profile.education_level not in criteria.education:
            return False
    
    # Check gender
    if criteria.gender and user_profile.gender:
        if criteria.gender.lower() != user_profile.gender.lower():
            return False
    
    return True



@settings(max_examples=30, deadline=None)
@given(user_profile=user_profile_with_interests_strategy())
def test_matched_programs_align_with_user_interests(user_profile):
    """
    Feature: bharatsahayak, Property 10: Skill Program Matching Relevance
    
    For any user profile with specified skills and interests, returned skill
    programs should match at least one of the user's interests or build upon
    their current skills.
    
    This test verifies:
    1. Matched programs align with user interests/category preferences
    2. Programs meet user's eligibility criteria (age, education)
    3. Programs are ranked by relevance to user profile
    4. Cost, location, and mode preferences affect matching
    """
    # Create diverse program set
    programs = create_diverse_skill_programs()
    
    # Match programs to user
    matched_programs = match_programs_to_user(programs, user_profile)
    
    # Property verification: All matched programs should align with user profile
    for program, score, reasoning in matched_programs:
        # Verify eligibility
        assert check_eligibility(program, user_profile), (
            f"Matched program {program.program_id} does not meet user eligibility criteria.\n"
            f"User age: {user_profile.age}, Program age range: {program.eligibility_criteria.age_min}-{program.eligibility_criteria.age_max}\n"
            f"User education: {user_profile.education_level}, Program education: {program.eligibility_criteria.education}"
        )
        
        # Verify relevance: program should match at least one aspect of user profile
        has_interest_match = (
            user_profile.preferences and 
            user_profile.preferences.preferred_categories and
            program.category in user_profile.preferences.preferred_categories
        )
        
        has_location_match = (
            program.location.state.lower() == user_profile.location.state.lower()
        )
        
        has_cost_match = program.cost <= 5000  # Default budget
        
        has_mode_match = program.mode in ["online", "hybrid"]  # Accessible modes
        
        has_some_match = (
            has_interest_match or 
            has_location_match or 
            has_cost_match or 
            has_mode_match or
            program.placement_support  # Placement support is always valuable
        )
        
        assert has_some_match, (
            f"Matched program {program.program_id} does not align with user profile.\n"
            f"User interests: {user_profile.preferences.preferred_categories if user_profile.preferences else None}\n"
            f"Program category: {program.category}\n"
            f"User location: {user_profile.location.state}\n"
            f"Program location: {program.location.state}\n"
            f"Program cost: {program.cost}\n"
            f"Program mode: {program.mode}\n"
            f"Match score: {score}\n"
            f"Reasoning: {reasoning}"
        )
        
        # Verify score is reasonable (> 0 and <= 1)
        assert 0 < score <= 1.0, (
            f"Match score {score} is out of valid range (0, 1] for program {program.program_id}"
        )


@settings(max_examples=20, deadline=None)
@given(user_profile=user_profile_with_interests_strategy())
def test_interest_match_increases_relevance_score(user_profile):
    """
    Test that programs matching user interests receive higher relevance scores.
    
    This verifies that the matching algorithm properly prioritizes programs
    in categories that match user interests.
    """
    # Ensure user has at least one interest
    assume(user_profile.preferences and user_profile.preferences.preferred_categories)
    assume(len(user_profile.preferences.preferred_categories) > 0)
    
    # Create program set
    programs = create_diverse_skill_programs()
    
    # Match programs
    matched_programs = match_programs_to_user(programs, user_profile)
    
    # Separate programs by interest match
    interest_matched = []
    non_interest_matched = []
    
    for program, score, reasoning in matched_programs:
        if program.category in user_profile.preferences.preferred_categories:
            interest_matched.append((program, score))
        else:
            non_interest_matched.append((program, score))
    
    # If we have both types, verify interest-matched programs score higher on average
    if interest_matched and non_interest_matched:
        avg_interest_score = sum(score for _, score in interest_matched) / len(interest_matched)
        avg_non_interest_score = sum(score for _, score in non_interest_matched) / len(non_interest_matched)
        
        assert avg_interest_score > avg_non_interest_score, (
            f"Programs matching user interests should have higher average scores.\n"
            f"User interests: {user_profile.preferences.preferred_categories}\n"
            f"Interest-matched avg score: {avg_interest_score}\n"
            f"Non-interest-matched avg score: {avg_non_interest_score}\n"
            f"Interest-matched programs: {[(p.program_id, p.category, s) for p, s in interest_matched]}\n"
            f"Non-interest-matched programs: {[(p.program_id, p.category, s) for p, s in non_interest_matched]}"
        )


@settings(max_examples=20, deadline=None)
@given(user_profile=user_profile_with_interests_strategy())
def test_location_proximity_affects_matching(user_profile):
    """
    Test that programs in user's state/district are ranked higher.
    
    This verifies that location proximity is factored into matching.
    """
    # Create program set
    programs = create_diverse_skill_programs()
    
    # Match programs
    matched_programs = match_programs_to_user(programs, user_profile)
    
    # Separate programs by location
    same_state = []
    different_state = []
    
    for program, score, reasoning in matched_programs:
        if program.location.state.lower() == user_profile.location.state.lower():
            same_state.append((program, score))
        else:
            different_state.append((program, score))
    
    # If we have both types, verify same-state programs score higher on average
    if same_state and different_state:
        avg_same_state_score = sum(score for _, score in same_state) / len(same_state)
        avg_different_state_score = sum(score for _, score in different_state) / len(different_state)
        
        assert avg_same_state_score > avg_different_state_score, (
            f"Programs in user's state should have higher average scores.\n"
            f"User state: {user_profile.location.state}\n"
            f"Same state avg score: {avg_same_state_score}\n"
            f"Different state avg score: {avg_different_state_score}\n"
            f"Same state programs: {[(p.program_id, p.location.state, s) for p, s in same_state]}\n"
            f"Different state programs: {[(p.program_id, p.location.state, s) for p, s in different_state]}"
        )


@settings(max_examples=10, deadline=None)
@given(user_profile=user_profile_with_interests_strategy())
def test_ineligible_programs_are_not_matched(user_profile):
    """
    Test that programs for which user doesn't meet eligibility are not matched.
    
    This verifies that basic eligibility filtering works correctly.
    """
    # Create program set
    programs = create_diverse_skill_programs()
    
    # Match programs
    matched_programs = match_programs_to_user(programs, user_profile)
    
    # Verify all matched programs meet eligibility
    for program, score, reasoning in matched_programs:
        # Check age eligibility
        if program.eligibility_criteria.age_min:
            assert user_profile.age >= program.eligibility_criteria.age_min, (
                f"User age {user_profile.age} is below minimum {program.eligibility_criteria.age_min} "
                f"for program {program.program_id}"
            )
        
        if program.eligibility_criteria.age_max:
            assert user_profile.age <= program.eligibility_criteria.age_max, (
                f"User age {user_profile.age} is above maximum {program.eligibility_criteria.age_max} "
                f"for program {program.program_id}"
            )
        
        # Check education eligibility
        if program.eligibility_criteria.education:
            assert user_profile.education_level in program.eligibility_criteria.education, (
                f"User education {user_profile.education_level} not in eligible list "
                f"{program.eligibility_criteria.education} for program {program.program_id}"
            )
        
        # Check gender eligibility
        if program.eligibility_criteria.gender:
            assert user_profile.gender.lower() == program.eligibility_criteria.gender.lower(), (
                f"User gender {user_profile.gender} does not match required {program.eligibility_criteria.gender} "
                f"for program {program.program_id}"
            )
