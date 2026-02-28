"""
Property-Based Test: Skill Program Matching Relevance
Feature: bharatsahayak, Property 10: Skill Program Matching Relevance

For any user profile with specified skills and interests, returned skill programs 
should match at least one of the user's interests or build upon their current skills.

Validates: Requirements 4.1
"""
import pytest
import os
from hypothesis import given, settings, strategies as st, HealthCheck, assume
from hypothesis.strategies import composite
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.skills import SkillProgram
from app.services.skills_matcher import SkillsMatcher
from app.schemas.skills import SkillPreferences
import uuid


# Strategy for generating eligibility criteria
@composite
def eligibility_criteria_strategy(draw):
    """Generate valid eligibility criteria for skill programs"""
    criteria = {}
    
    if draw(st.booleans()):
        criteria['age_min'] = draw(st.integers(min_value=16, max_value=18))
    if draw(st.booleans()):
        criteria['age_max'] = draw(st.integers(min_value=25, max_value=60))
    if draw(st.booleans()):
        criteria['education'] = draw(st.lists(
            st.sampled_from(['10th', '12th', 'Graduate', 'Postgraduate', 'Any']),
            min_size=1, max_size=3
        ))
    
    return criteria


# Strategy for generating skill programs
@composite
def skill_program_strategy(draw):
    """Generate a valid skill development program"""
    categories = ['technical', 'vocational', 'digital', 'entrepreneurship', 'agriculture']
    category = draw(st.sampled_from(categories))
    
    # Generate category-specific content
    program_templates = {
        'technical': {
            'names': [
                'Computer Programming Course',
                'Web Development Training',
                'Mobile App Development',
                'Data Science Bootcamp',
                'Software Testing Course'
            ],
            'descriptions': [
                'Learn programming fundamentals and build software applications',
                'Master web technologies including HTML, CSS, JavaScript, and frameworks',
                'Develop mobile applications for Android and iOS platforms',
                'Learn data analysis, machine learning, and statistical modeling',
                'Understand software testing methodologies and quality assurance'
            ],
            'skills': ['programming', 'coding', 'software', 'technology', 'computer']
        },
        'vocational': {
            'names': [
                'Electrician Training Program',
                'Plumbing Skills Course',
                'Carpentry Workshop',
                'Welding Certification',
                'Tailoring and Stitching'
            ],
            'descriptions': [
                'Learn electrical installation, maintenance, and repair skills',
                'Master plumbing techniques for residential and commercial settings',
                'Develop woodworking and furniture making skills',
                'Learn welding techniques and metal fabrication',
                'Master garment construction and tailoring techniques'
            ],
            'skills': ['electrician', 'plumbing', 'carpentry', 'welding', 'tailoring']
        },
        'digital': {
            'names': [
                'Digital Marketing Course',
                'Graphic Design Training',
                'Video Editing Workshop',
                'Social Media Management',
                'E-commerce Skills'
            ],
            'descriptions': [
                'Learn online marketing strategies, SEO, and digital advertising',
                'Master graphic design tools and visual communication',
                'Learn video production and editing techniques',
                'Understand social media platforms and content strategy',
                'Learn to set up and manage online stores'
            ],
            'skills': ['marketing', 'design', 'video', 'social media', 'ecommerce']
        },
        'entrepreneurship': {
            'names': [
                'Start Your Business Program',
                'Small Business Management',
                'Entrepreneurship Development',
                'Business Planning Workshop',
                'Financial Management for Entrepreneurs'
            ],
            'descriptions': [
                'Learn how to start and run your own business',
                'Master small business operations and management',
                'Develop entrepreneurial mindset and business skills',
                'Create comprehensive business plans and strategies',
                'Understand financial planning and business accounting'
            ],
            'skills': ['business', 'entrepreneurship', 'management', 'finance', 'startup']
        },
        'agriculture': {
            'names': [
                'Modern Farming Techniques',
                'Organic Farming Training',
                'Agricultural Machinery Operation',
                'Horticulture Skills',
                'Dairy Farming Management'
            ],
            'descriptions': [
                'Learn modern agricultural practices and crop management',
                'Master organic farming methods and sustainable agriculture',
                'Operate and maintain agricultural machinery and equipment',
                'Develop skills in fruit and vegetable cultivation',
                'Learn dairy farm management and animal husbandry'
            ],
            'skills': ['farming', 'agriculture', 'crops', 'livestock', 'horticulture']
        }
    }
    
    template = program_templates[category]
    name = draw(st.sampled_from(template['names']))
    description = draw(st.sampled_from(template['descriptions']))
    
    providers = [
        'National Skill Development Corporation',
        'Ministry of Skill Development',
        'State Skill Development Mission',
        'Industrial Training Institute',
        'Vocational Training Center'
    ]
    
    states = ['Maharashtra', 'Karnataka', 'Tamil Nadu', 'Uttar Pradesh', 'Bihar', 'Gujarat']
    districts = ['District A', 'District B', 'District C', 'District D']
    modes = ['in-person', 'online', 'hybrid']
    
    return {
        'program_id': uuid.uuid4(),
        'name': name,
        'provider': draw(st.sampled_from(providers)),
        'category': category,
        'description': description,
        'duration_weeks': draw(st.integers(min_value=4, max_value=52)),
        'cost': draw(st.decimals(min_value=0, max_value=50000, places=2)),
        'state': draw(st.sampled_from(states)),
        'district': draw(st.sampled_from(districts)),
        'mode': draw(st.sampled_from(modes)),
        'eligibility_criteria': draw(eligibility_criteria_strategy()),
        'certification': draw(st.booleans()),
        'placement_support': draw(st.booleans()),
        'registration_url': f'https://example.gov.in/program/{uuid.uuid4()}',
        'contact': draw(st.sampled_from(['1800-123-4567', '1800-987-6543', 'contact@example.gov.in'])),
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow()
    }


# Strategy for generating user profiles with skills and interests
@composite
def user_profile_with_preferences_strategy(draw):
    """Generate user profile and preferences for skill matching"""
    
    # Define skill and interest categories
    all_skills = [
        'programming', 'coding', 'software', 'technology', 'computer',
        'electrician', 'plumbing', 'carpentry', 'welding', 'tailoring',
        'marketing', 'design', 'video', 'social media', 'ecommerce',
        'business', 'entrepreneurship', 'management', 'finance', 'startup',
        'farming', 'agriculture', 'crops', 'livestock', 'horticulture'
    ]
    
    all_interests = [
        'technical', 'vocational', 'digital', 'entrepreneurship', 'agriculture',
        'programming', 'web development', 'mobile apps', 'data science',
        'electrical work', 'construction', 'crafts',
        'marketing', 'design', 'content creation',
        'business', 'startups', 'self-employment',
        'farming', 'organic farming', 'animal husbandry'
    ]
    
    all_career_goals = [
        'software developer', 'web developer', 'data analyst',
        'electrician', 'plumber', 'carpenter',
        'digital marketer', 'graphic designer', 'content creator',
        'entrepreneur', 'business owner', 'manager',
        'farmer', 'agricultural expert', 'farm manager'
    ]
    
    # Generate user profile
    user_profile = {
        'user_id': str(uuid.uuid4()),
        'state': draw(st.sampled_from(['Maharashtra', 'Karnataka', 'Tamil Nadu', 'Uttar Pradesh', 'Bihar'])),
        'district': draw(st.sampled_from(['District A', 'District B', 'District C'])),
        'education_level': draw(st.sampled_from(['10th', '12th', 'Graduate', 'Postgraduate'])),
        'occupation': draw(st.sampled_from(['Student', 'Unemployed', 'Self-Employed', 'Worker', 'Farmer']))
    }
    
    # Generate preferences with at least one interest or skill
    current_skills = draw(st.lists(
        st.sampled_from(all_skills),
        min_size=0, max_size=3, unique=True
    ))
    
    interests = draw(st.lists(
        st.sampled_from(all_interests),
        min_size=1, max_size=3, unique=True  # At least one interest
    ))
    
    career_goals = draw(st.lists(
        st.sampled_from(all_career_goals),
        min_size=0, max_size=2, unique=True
    ))
    
    preferences = SkillPreferences(
        current_skills=current_skills,
        interests=interests,
        career_goals=career_goals,
        max_duration_weeks=draw(st.one_of(st.none(), st.integers(min_value=12, max_value=52))),
        max_cost=draw(st.one_of(st.none(), st.decimals(min_value=5000, max_value=30000, places=2))),
        preferred_mode=draw(st.one_of(st.none(), st.sampled_from(['in-person', 'online', 'hybrid']))),
        location_state=user_profile['state'],
        location_district=user_profile['district']
    )
    
    return user_profile, preferences


@pytest.fixture(scope="function")
def test_db_session():
    """Create a test database session"""
    from sqlalchemy.types import TypeDecorator, CHAR
    from sqlalchemy.dialects.postgresql import UUID as PG_UUID
    from sqlalchemy import Table, Column, String, DateTime, Text, Integer, Boolean, Numeric
    from sqlalchemy import JSON
    import uuid as uuid_module
    
    class UUID(TypeDecorator):
        """Platform-independent UUID type."""
        impl = CHAR
        cache_ok = True
        
        def load_dialect_impl(self, dialect):
            if dialect.name == 'postgresql':
                return dialect.type_descriptor(PG_UUID())
            else:
                return dialect.type_descriptor(CHAR(36))
        
        def process_bind_param(self, value, dialect):
            if value is None:
                return value
            elif not isinstance(value, uuid_module.UUID):
                return str(uuid_module.UUID(value)) if value else None
            else:
                return str(value)
        
        def process_result_value(self, value, dialect):
            if value is None:
                return value
            return uuid_module.UUID(value) if value else None
    
    # Create engine
    engine = create_engine('sqlite:///:memory:', echo=False)
    
    # Create skill programs table manually for SQLite compatibility
    from sqlalchemy import MetaData
    metadata = MetaData()
    
    skill_programs_table = Table(
        'skill_programs', metadata,
        Column('program_id', UUID(), primary_key=True),
        Column('name', String(255), nullable=False),
        Column('provider', String(100), nullable=True),
        Column('category', String(50), nullable=False),
        Column('description', Text, nullable=True),
        Column('duration_weeks', Integer, nullable=True),
        Column('cost', Numeric(10, 2), nullable=True),
        Column('state', String(50), nullable=True),
        Column('district', String(50), nullable=True),
        Column('mode', String(20), nullable=True),
        Column('eligibility_criteria', JSON, nullable=True),
        Column('certification', Boolean, default=False),
        Column('placement_support', Boolean, default=False),
        Column('registration_url', String(500), nullable=True),
        Column('contact', String(100), nullable=True),
        Column('created_at', DateTime, nullable=False),
        Column('updated_at', DateTime, nullable=False)
    )
    
    metadata.create_all(engine)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()


def add_programs_to_db(session, programs_data):
    """Helper to add skill programs to test database"""
    # Clear existing programs first
    session.query(SkillProgram).delete()
    session.commit()
    
    programs = []
    for program_data in programs_data:
        program = SkillProgram(**program_data)
        session.add(program)
        programs.append(program)
    
    session.commit()
    return programs


@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    programs=st.lists(skill_program_strategy(), min_size=5, max_size=20),
    profile_and_prefs=user_profile_with_preferences_strategy()
)
def test_skill_program_matching_relevance(programs, profile_and_prefs, test_db_session):
    """
    Feature: bharatsahayak, Property 10: Skill Program Matching Relevance
    
    For any user profile with specified skills and interests, returned skill 
    programs should match at least one of the user's interests or build upon 
    their current skills.
    
    This is the core property test validating that all matched programs are relevant.
    """
    user_profile, preferences = profile_and_prefs
    
    # Add programs to database
    add_programs_to_db(test_db_session, programs)
    
    # Create matcher and get recommendations
    matcher = SkillsMatcher(test_db_session)
    results = matcher.match_programs(user_profile, preferences, limit=50)
    
    # Property: All returned programs should match at least one interest or skill
    for program_response in results:
        # Check if program matches any interest
        interest_match = False
        for interest in preferences.interests:
            interest_lower = interest.lower()
            if (interest_lower in program_response.category.lower() or
                (program_response.description and interest_lower in program_response.description.lower())):
                interest_match = True
                break
        
        # Check if program builds on current skills
        skill_match = False
        if preferences.current_skills:
            for skill in preferences.current_skills:
                skill_lower = skill.lower()
                if (skill_lower in program_response.category.lower() or
                    (program_response.description and skill_lower in program_response.description.lower())):
                    skill_match = True
                    break
        
        # Check if program aligns with career goals
        career_match = False
        if preferences.career_goals:
            for goal in preferences.career_goals:
                goal_lower = goal.lower()
                if (goal_lower in program_response.category.lower() or
                    (program_response.description and goal_lower in program_response.description.lower())):
                    career_match = True
                    break
        
        # At least one type of match should exist
        assert interest_match or skill_match or career_match, \
            f"Program '{program_response.name}' (category: {program_response.category}) " \
            f"should match at least one interest {preferences.interests}, " \
            f"skill {preferences.current_skills}, or career goal {preferences.career_goals}"


@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    programs=st.lists(skill_program_strategy(), min_size=5, max_size=15),
    profile_and_prefs=user_profile_with_preferences_strategy()
)
def test_skill_program_matching_respects_filters(programs, profile_and_prefs, test_db_session):
    """
    Feature: bharatsahayak, Property 10: Skill Program Matching Relevance
    
    Returned programs should respect user's filter preferences (cost, duration, mode).
    """
    user_profile, preferences = profile_and_prefs
    
    # Add programs to database
    add_programs_to_db(test_db_session, programs)
    
    # Create matcher and get recommendations
    matcher = SkillsMatcher(test_db_session)
    results = matcher.match_programs(user_profile, preferences, limit=50)
    
    # Property: All programs should respect cost filter
    if preferences.max_cost is not None:
        for program in results:
            if program.cost is not None:
                assert program.cost <= preferences.max_cost, \
                    f"Program cost {program.cost} should be <= max_cost {preferences.max_cost}"
    
    # Property: All programs should respect duration filter
    if preferences.max_duration_weeks is not None:
        for program in results:
            if program.duration_weeks is not None:
                assert program.duration_weeks <= preferences.max_duration_weeks, \
                    f"Program duration {program.duration_weeks} should be <= max_duration {preferences.max_duration_weeks}"
    
    # Property: All programs should respect mode filter
    if preferences.preferred_mode is not None:
        for program in results:
            assert program.mode == preferences.preferred_mode, \
                f"Program mode {program.mode} should match preferred_mode {preferences.preferred_mode}"


@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    programs=st.lists(skill_program_strategy(), min_size=5, max_size=15),
    profile_and_prefs=user_profile_with_preferences_strategy()
)
def test_skill_program_matching_location_handling(programs, profile_and_prefs, test_db_session):
    """
    Feature: bharatsahayak, Property 10: Skill Program Matching Relevance
    
    Returned programs should be in user's location OR be available online.
    """
    user_profile, preferences = profile_and_prefs
    
    # Add programs to database
    add_programs_to_db(test_db_session, programs)
    
    # Create matcher and get recommendations
    matcher = SkillsMatcher(test_db_session)
    results = matcher.match_programs(user_profile, preferences, limit=50)
    
    # Property: All programs should be in user's state or be online
    for program in results:
        in_user_state = program.state == preferences.location_state
        is_online = program.mode == 'online'
        
        assert in_user_state or is_online, \
            f"Program should be in user's state ({preferences.location_state}) or be online, " \
            f"but program is in {program.state} with mode {program.mode}"


@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    programs=st.lists(skill_program_strategy(), min_size=5, max_size=15),
    profile_and_prefs=user_profile_with_preferences_strategy()
)
def test_skill_program_matching_relevance_scoring(programs, profile_and_prefs, test_db_session):
    """
    Feature: bharatsahayak, Property 10: Skill Program Matching Relevance
    
    Programs should be ranked by relevance score, with higher scores appearing first.
    """
    user_profile, preferences = profile_and_prefs
    
    # Add programs to database
    add_programs_to_db(test_db_session, programs)
    
    # Create matcher and get recommendations
    matcher = SkillsMatcher(test_db_session)
    results = matcher.match_programs(user_profile, preferences, limit=50)
    
    # Property: Results should be sorted by relevance_score descending
    for i in range(len(results) - 1):
        assert results[i].relevance_score >= results[i+1].relevance_score, \
            f"Programs should be sorted by relevance score descending. " \
            f"Program {i} score: {results[i].relevance_score}, " \
            f"Program {i+1} score: {results[i+1].relevance_score}"
    
    # Property: All relevance scores should be between 0 and 1
    for program in results:
        assert 0.0 <= program.relevance_score <= 1.0, \
            f"Relevance score should be between 0 and 1, got {program.relevance_score}"


@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    programs=st.lists(skill_program_strategy(), min_size=5, max_size=15),
    profile_and_prefs=user_profile_with_preferences_strategy()
)
def test_skill_program_matching_explanation_presence(programs, profile_and_prefs, test_db_session):
    """
    Feature: bharatsahayak, Property 10: Skill Program Matching Relevance
    
    All matched programs should include a match_reason explaining why they were recommended.
    """
    user_profile, preferences = profile_and_prefs
    
    # Add programs to database
    add_programs_to_db(test_db_session, programs)
    
    # Create matcher and get recommendations
    matcher = SkillsMatcher(test_db_session)
    results = matcher.match_programs(user_profile, preferences, limit=50)
    
    # Property: All results should have a match_reason
    for program in results:
        assert program.match_reason is not None, \
            f"Program '{program.name}' should have a match_reason"
        assert len(program.match_reason) > 0, \
            f"Program '{program.name}' match_reason should not be empty"
        assert isinstance(program.match_reason, str), \
            f"Program '{program.name}' match_reason should be a string"


# Concrete example tests to complement property-based tests

def test_skill_program_matching_specific_technical_interest(test_db_session):
    """
    Specific example: User interested in programming should get technical programs.
    """
    programs_data = [
        {
            'program_id': uuid.uuid4(),
            'name': 'Web Development Bootcamp',
            'provider': 'NSDC',
            'category': 'technical',
            'description': 'Learn programming and web development',
            'duration_weeks': 12,
            'cost': 10000.00,
            'state': 'Maharashtra',
            'district': 'Mumbai',
            'mode': 'online',
            'eligibility_criteria': {},
            'certification': True,
            'placement_support': True,
            'registration_url': 'https://example.com',
            'contact': '1800-123-4567',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        },
        {
            'program_id': uuid.uuid4(),
            'name': 'Tailoring Course',
            'provider': 'State Skill Mission',
            'category': 'vocational',
            'description': 'Learn garment stitching and tailoring',
            'duration_weeks': 8,
            'cost': 5000.00,
            'state': 'Maharashtra',
            'district': 'Mumbai',
            'mode': 'in-person',
            'eligibility_criteria': {},
            'certification': True,
            'placement_support': False,
            'registration_url': 'https://example.com',
            'contact': '1800-123-4567',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
    ]
    
    add_programs_to_db(test_db_session, programs_data)
    
    # User interested in programming
    user_profile = {
        'user_id': str(uuid.uuid4()),
        'state': 'Maharashtra',
        'district': 'Mumbai',
        'education_level': '12th'
    }
    
    preferences = SkillPreferences(
        interests=['programming', 'technology'],
        current_skills=[],
        career_goals=['software developer'],
        location_state='Maharashtra',
        location_district='Mumbai'
    )
    
    matcher = SkillsMatcher(test_db_session)
    results = matcher.match_programs(user_profile, preferences, limit=10)
    
    # Should find web development program
    assert len(results) > 0, "Should find matching programs"
    
    # First result should be the technical program
    assert 'Web Development' in results[0].name, \
        "Should prioritize technical program for programming interest"
    assert results[0].category == 'technical', \
        "Should return technical category for programming interest"


def test_skill_program_matching_specific_vocational_interest(test_db_session):
    """
    Specific example: User interested in vocational skills should get vocational programs.
    """
    programs_data = [
        {
            'program_id': uuid.uuid4(),
            'name': 'Electrician Training',
            'provider': 'ITI',
            'category': 'vocational',
            'description': 'Learn electrical installation and repair',
            'duration_weeks': 16,
            'cost': 8000.00,
            'state': 'Karnataka',
            'district': 'Bangalore',
            'mode': 'in-person',
            'eligibility_criteria': {},
            'certification': True,
            'placement_support': True,
            'registration_url': 'https://example.com',
            'contact': '1800-987-6543',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        },
        {
            'program_id': uuid.uuid4(),
            'name': 'Digital Marketing',
            'provider': 'NSDC',
            'category': 'digital',
            'description': 'Learn online marketing strategies',
            'duration_weeks': 10,
            'cost': 12000.00,
            'state': 'Karnataka',
            'district': 'Bangalore',
            'mode': 'online',
            'eligibility_criteria': {},
            'certification': True,
            'placement_support': False,
            'registration_url': 'https://example.com',
            'contact': '1800-987-6543',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
    ]
    
    add_programs_to_db(test_db_session, programs_data)
    
    user_profile = {
        'user_id': str(uuid.uuid4()),
        'state': 'Karnataka',
        'district': 'Bangalore',
        'education_level': '10th'
    }
    
    preferences = SkillPreferences(
        interests=['electrician', 'vocational'],
        current_skills=[],
        career_goals=['electrician'],
        location_state='Karnataka',
        location_district='Bangalore'
    )
    
    matcher = SkillsMatcher(test_db_session)
    results = matcher.match_programs(user_profile, preferences, limit=10)
    
    assert len(results) > 0, "Should find matching programs"
    assert 'Electrician' in results[0].name, \
        "Should find electrician program for vocational interest"


def test_skill_program_matching_online_programs_available_everywhere(test_db_session):
    """
    Test that online programs are available regardless of user location.
    """
    programs_data = [
        {
            'program_id': uuid.uuid4(),
            'name': 'Online Data Science Course',
            'provider': 'NSDC',
            'category': 'technical',
            'description': 'Learn data science and machine learning online',
            'duration_weeks': 20,
            'cost': 15000.00,
            'state': 'Maharashtra',  # Program registered in Maharashtra
            'district': 'Mumbai',
            'mode': 'online',  # But available online
            'eligibility_criteria': {},
            'certification': True,
            'placement_support': True,
            'registration_url': 'https://example.com',
            'contact': '1800-123-4567',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
    ]
    
    add_programs_to_db(test_db_session, programs_data)
    
    # User from a different state
    user_profile = {
        'user_id': str(uuid.uuid4()),
        'state': 'Bihar',  # Different state
        'district': 'Patna',
        'education_level': 'Graduate'
    }
    
    preferences = SkillPreferences(
        interests=['data science', 'technology'],
        current_skills=['programming'],
        career_goals=['data analyst'],
        location_state='Bihar',
        location_district='Patna'
    )
    
    matcher = SkillsMatcher(test_db_session)
    results = matcher.match_programs(user_profile, preferences, limit=10)
    
    # Should find the online program even though user is in different state
    assert len(results) > 0, "Should find online programs regardless of location"
    assert 'Data Science' in results[0].name, "Should find online data science course"
    assert results[0].mode == 'online', "Program should be online"


def test_skill_program_matching_cost_filter(test_db_session):
    """
    Test that cost filter is respected.
    """
    programs_data = [
        {
            'program_id': uuid.uuid4(),
            'name': 'Expensive Program',
            'provider': 'NSDC',
            'category': 'technical',
            'description': 'High-cost technical training',
            'duration_weeks': 12,
            'cost': 50000.00,  # Expensive
            'state': 'Maharashtra',
            'district': 'Mumbai',
            'mode': 'online',
            'eligibility_criteria': {},
            'certification': True,
            'placement_support': True,
            'registration_url': 'https://example.com',
            'contact': '1800-123-4567',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        },
        {
            'program_id': uuid.uuid4(),
            'name': 'Affordable Program',
            'provider': 'State Mission',
            'category': 'technical',
            'description': 'Low-cost technical training',
            'duration_weeks': 12,
            'cost': 5000.00,  # Affordable
            'state': 'Maharashtra',
            'district': 'Mumbai',
            'mode': 'online',
            'eligibility_criteria': {},
            'certification': True,
            'placement_support': False,
            'registration_url': 'https://example.com',
            'contact': '1800-123-4567',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
    ]
    
    add_programs_to_db(test_db_session, programs_data)
    
    user_profile = {
        'user_id': str(uuid.uuid4()),
        'state': 'Maharashtra',
        'district': 'Mumbai',
        'education_level': '12th'
    }
    
    preferences = SkillPreferences(
        interests=['technical'],
        current_skills=[],
        career_goals=[],
        max_cost=10000.00,  # Budget constraint
        location_state='Maharashtra',
        location_district='Mumbai'
    )
    
    matcher = SkillsMatcher(test_db_session)
    results = matcher.match_programs(user_profile, preferences, limit=10)
    
    # Should only return affordable program
    assert len(results) == 1, "Should only return programs within budget"
    assert results[0].cost <= 10000.00, "Returned program should be within budget"
    assert 'Affordable' in results[0].name, "Should return the affordable program"


def test_skill_program_matching_no_results(test_db_session):
    """
    Edge case: No matching programs should return empty list.
    """
    programs_data = [
        {
            'program_id': uuid.uuid4(),
            'name': 'Carpentry Workshop',
            'provider': 'ITI',
            'category': 'vocational',
            'description': 'Learn woodworking skills',
            'duration_weeks': 12,
            'cost': 8000.00,
            'state': 'Maharashtra',
            'district': 'Mumbai',
            'mode': 'in-person',
            'eligibility_criteria': {},
            'certification': True,
            'placement_support': False,
            'registration_url': 'https://example.com',
            'contact': '1800-123-4567',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
    ]
    
    add_programs_to_db(test_db_session, programs_data)
    
    user_profile = {
        'user_id': str(uuid.uuid4()),
        'state': 'Bihar',  # Different state
        'district': 'Patna',
        'education_level': '12th'
    }
    
    preferences = SkillPreferences(
        interests=['programming'],  # Different interest
        current_skills=[],
        career_goals=[],
        preferred_mode='online',  # Program is in-person
        location_state='Bihar',
        location_district='Patna'
    )
    
    matcher = SkillsMatcher(test_db_session)
    results = matcher.match_programs(user_profile, preferences, limit=10)
    
    # Should return empty list when no programs match
    assert len(results) == 0, "Should return empty list when no programs match filters"
    assert isinstance(results, list), "Should return a list"


def test_skill_program_matching_limit_parameter(test_db_session):
    """
    Test that limit parameter is respected.
    """
    # Create 15 programs
    programs_data = []
    for i in range(15):
        programs_data.append({
            'program_id': uuid.uuid4(),
            'name': f'Technical Program {i}',
            'provider': 'NSDC',
            'category': 'technical',
            'description': 'Technical training program',
            'duration_weeks': 12,
            'cost': 10000.00,
            'state': 'Maharashtra',
            'district': 'Mumbai',
            'mode': 'online',
            'eligibility_criteria': {},
            'certification': True,
            'placement_support': False,
            'registration_url': 'https://example.com',
            'contact': '1800-123-4567',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        })
    
    add_programs_to_db(test_db_session, programs_data)
    
    user_profile = {
        'user_id': str(uuid.uuid4()),
        'state': 'Maharashtra',
        'district': 'Mumbai',
        'education_level': '12th'
    }
    
    preferences = SkillPreferences(
        interests=['technical'],
        current_skills=[],
        career_goals=[],
        location_state='Maharashtra',
        location_district='Mumbai'
    )
    
    matcher = SkillsMatcher(test_db_session)
    
    # Test with limit=5
    results = matcher.match_programs(user_profile, preferences, limit=5)
    assert len(results) == 5, "Should respect limit parameter"
    
    # Test with limit=10
    results = matcher.match_programs(user_profile, preferences, limit=10)
    assert len(results) == 10, "Should respect limit parameter"
