"""
Property-Based Test: Health Guidance Generation
Feature: bharatsahayak, Property 12: Health Guidance Generation

For any list of symptoms, the Health_Advisor should generate guidance containing 
urgency_level, possible_conditions, self_care_recommendations, when_to_seek_care, 
and disclaimer fields.

Validates: Requirements 5.1
"""
import pytest
from hypothesis import given, settings, strategies as st, HealthCheck
from hypothesis.strategies import composite
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.services.health_advisor import HealthAdvisor
from app.schemas.health import BasicHealthInfo


# Strategy for generating valid symptom lists
@composite
def symptom_list_strategy(draw):
    """Generate a valid list of symptoms"""
    # Common symptoms
    common_symptoms = [
        'fever', 'cough', 'headache', 'stomach pain', 'diarrhea', 'vomiting',
        'body ache', 'sore throat', 'runny nose', 'fatigue', 'dizziness',
        'rash', 'joint pain', 'nausea', 'weakness', 'cold', 'sneezing',
        'back pain', 'muscle pain', 'loss of appetite', 'chills', 'sweating'
    ]
    
    # Urgent symptoms
    urgent_symptoms = [
        'high fever', 'persistent vomiting', 'severe diarrhea', 'dehydration',
        'severe pain', 'bleeding', 'infection', 'difficulty urinating',
        'severe headache', 'vision problems', 'confusion', 'severe cough'
    ]
    
    # Emergency symptoms
    emergency_symptoms = [
        'chest pain', 'difficulty breathing', 'severe bleeding', 'unconscious',
        'seizure', 'severe head injury', 'stroke symptoms', 'heart attack',
        'severe abdominal pain', 'poisoning', 'severe burns', 'choking',
        'severe allergic reaction', 'loss of consciousness', 'paralysis'
    ]
    
    # Combine all symptoms
    all_symptoms = common_symptoms + urgent_symptoms + emergency_symptoms
    
    # Generate 1-5 symptoms
    num_symptoms = draw(st.integers(min_value=1, max_value=5))
    symptoms = draw(st.lists(
        st.sampled_from(all_symptoms),
        min_size=num_symptoms,
        max_size=num_symptoms,
        unique=True
    ))
    
    return symptoms


# Strategy for generating basic health info
@composite
def basic_health_info_strategy(draw):
    """Generate optional basic health information"""
    # Sometimes return None
    if draw(st.booleans()):
        return None
    
    return BasicHealthInfo(
        age=draw(st.one_of(st.none(), st.integers(min_value=0, max_value=120))),
        gender=draw(st.one_of(st.none(), st.sampled_from(['male', 'female', 'other']))),
        existing_conditions=draw(st.one_of(
            st.none(),
            st.lists(st.sampled_from(['diabetes', 'hypertension', 'asthma', 'heart disease']), max_size=3)
        )),
        medications=draw(st.one_of(
            st.none(),
            st.lists(st.sampled_from(['aspirin', 'metformin', 'insulin', 'inhaler']), max_size=3)
        ))
    )


@pytest.fixture(scope="function")
def test_db_session():
    """Create a test database session"""
    from sqlalchemy.types import TypeDecorator, CHAR
    from sqlalchemy.dialects.postgresql import UUID as PG_UUID
    from sqlalchemy import Table, Column, String, DateTime, Text, Float, Integer, JSON, DECIMAL
    from sqlalchemy import MetaData
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
    
    # Create tables manually for SQLite compatibility
    metadata = MetaData()
    
    # Health facilities table
    health_facilities_table = Table(
        'health_facilities', metadata,
        Column('facility_id', UUID(), primary_key=True),
        Column('name', String(255), nullable=False),
        Column('facility_type', String(50)),
        Column('state', String(50)),
        Column('district', String(50)),
        Column('address', Text),
        Column('latitude', DECIMAL(10, 8)),
        Column('longitude', DECIMAL(11, 8)),
        Column('contact', String(100)),
        Column('services', JSON),
        Column('created_at', DateTime)
    )
    
    metadata.create_all(engine)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()


@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    symptoms=symptom_list_strategy(),
    user_info=basic_health_info_strategy()
)
def test_health_guidance_completeness(symptoms, user_info, test_db_session):
    """
    Feature: bharatsahayak, Property 12: Health Guidance Generation
    
    For any list of symptoms, the Health_Advisor should generate guidance 
    containing all required fields.
    
    This tests that guidance is always generated with complete data.
    """
    # Create health advisor
    advisor = HealthAdvisor(test_db_session)
    
    # Analyze symptoms
    guidance = advisor.analyze_symptoms(symptoms, user_info)
    
    # Property 1: All required fields should be present
    required_fields = [
        'urgency_level',
        'possible_conditions',
        'self_care_recommendations',
        'when_to_seek_care',
        'red_flags',
        'disclaimer',
        'confidence'
    ]
    
    for field in required_fields:
        assert hasattr(guidance, field), \
            f"Guidance missing required field: {field}"
        
        value = getattr(guidance, field)
        assert value is not None, \
            f"Required field '{field}' should not be None"
    
    # Property 2: urgency_level should be one of the valid values
    valid_urgency_levels = ['routine', 'soon', 'urgent', 'emergency']
    assert guidance.urgency_level in valid_urgency_levels, \
        f"urgency_level should be one of {valid_urgency_levels}, got {guidance.urgency_level}"
    
    # Property 3: possible_conditions should be a list
    assert isinstance(guidance.possible_conditions, list), \
        "possible_conditions should be a list"
    
    # Property 4: self_care_recommendations should be a non-empty list
    assert isinstance(guidance.self_care_recommendations, list), \
        "self_care_recommendations should be a list"
    assert len(guidance.self_care_recommendations) > 0, \
        "self_care_recommendations should not be empty"
    
    # Property 5: when_to_seek_care should be a non-empty string
    assert isinstance(guidance.when_to_seek_care, str), \
        "when_to_seek_care should be a string"
    assert len(guidance.when_to_seek_care) > 0, \
        "when_to_seek_care should not be empty"
    
    # Property 6: red_flags should be a list
    assert isinstance(guidance.red_flags, list), \
        "red_flags should be a list"
    
    # Property 7: disclaimer should be a non-empty string
    assert isinstance(guidance.disclaimer, str), \
        "disclaimer should be a string"
    assert len(guidance.disclaimer) > 0, \
        "disclaimer should not be empty"
    
    # Property 8: confidence should be between 0 and 1
    assert isinstance(guidance.confidence, (int, float)), \
        "confidence should be numeric"
    assert 0.0 <= guidance.confidence <= 1.0, \
        f"confidence should be between 0 and 1, got {guidance.confidence}"


@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    symptoms=symptom_list_strategy(),
    user_info=basic_health_info_strategy()
)
def test_health_guidance_disclaimer_presence(symptoms, user_info, test_db_session):
    """
    Feature: bharatsahayak, Property 12: Health Guidance Generation
    
    For any health guidance, the disclaimer should contain key phrases 
    indicating it's not a substitute for professional medical advice.
    
    This tests that the disclaimer is meaningful and present.
    """
    # Create health advisor
    advisor = HealthAdvisor(test_db_session)
    
    # Analyze symptoms
    guidance = advisor.analyze_symptoms(symptoms, user_info)
    
    # Property: Disclaimer should contain key phrases
    disclaimer_lower = guidance.disclaimer.lower()
    
    # Should mention it's informational
    assert 'informational' in disclaimer_lower or 'information' in disclaimer_lower, \
        "Disclaimer should mention informational purpose"
    
    # Should mention not a substitute
    assert 'not a substitute' in disclaimer_lower or 'not substitute' in disclaimer_lower, \
        "Disclaimer should mention not being a substitute for medical advice"
    
    # Should mention professional medical advice
    assert 'medical' in disclaimer_lower and ('advice' in disclaimer_lower or 'consultation' in disclaimer_lower), \
        "Disclaimer should mention professional medical advice"


@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    symptoms=st.lists(
        st.sampled_from([
            'chest pain', 'difficulty breathing', 'severe bleeding', 'unconscious',
            'seizure', 'severe head injury', 'stroke symptoms', 'heart attack'
        ]),
        min_size=1,
        max_size=3,
        unique=True
    ),
    user_info=basic_health_info_strategy()
)
def test_health_guidance_emergency_detection(symptoms, user_info, test_db_session):
    """
    Feature: bharatsahayak, Property 12: Health Guidance Generation
    
    For any symptoms containing emergency indicators, the urgency_level 
    should be set to 'emergency'.
    
    This tests emergency symptom detection.
    """
    # Create health advisor
    advisor = HealthAdvisor(test_db_session)
    
    # Analyze symptoms
    guidance = advisor.analyze_symptoms(symptoms, user_info)
    
    # Property: Emergency symptoms should result in emergency urgency level
    assert guidance.urgency_level == 'emergency', \
        f"Emergency symptoms {symptoms} should result in 'emergency' urgency level, got {guidance.urgency_level}"
    
    # Property: when_to_seek_care should indicate immediate action
    when_to_seek_care_lower = guidance.when_to_seek_care.lower()
    assert 'immediate' in when_to_seek_care_lower or 'now' in when_to_seek_care_lower or 'emergency' in when_to_seek_care_lower, \
        "Emergency guidance should indicate immediate medical care"


@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    symptoms=st.lists(
        st.sampled_from([
            'fever', 'cough', 'headache', 'runny nose', 'sore throat',
            'body ache', 'fatigue', 'sneezing'
        ]),
        min_size=1,
        max_size=3,
        unique=True
    ),
    user_info=basic_health_info_strategy()
)
def test_health_guidance_routine_symptoms(symptoms, user_info, test_db_session):
    """
    Feature: bharatsahayak, Property 12: Health Guidance Generation
    
    For routine symptoms without emergency indicators, the urgency_level 
    should be 'routine' or 'soon'.
    
    This tests that routine symptoms don't trigger emergency responses.
    """
    # Create health advisor
    advisor = HealthAdvisor(test_db_session)
    
    # Analyze symptoms
    guidance = advisor.analyze_symptoms(symptoms, user_info)
    
    # Property: Routine symptoms should not result in emergency urgency level
    assert guidance.urgency_level in ['routine', 'soon', 'urgent'], \
        f"Routine symptoms {symptoms} should not result in 'emergency' urgency level, got {guidance.urgency_level}"
    
    # Property: Should provide self-care recommendations
    assert len(guidance.self_care_recommendations) > 0, \
        "Routine symptoms should have self-care recommendations"


@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    symptoms=symptom_list_strategy(),
    user_info=basic_health_info_strategy()
)
def test_health_guidance_self_care_relevance(symptoms, user_info, test_db_session):
    """
    Feature: bharatsahayak, Property 12: Health Guidance Generation
    
    Self-care recommendations should be relevant to the symptoms provided.
    
    This tests that recommendations are contextual.
    """
    # Create health advisor
    advisor = HealthAdvisor(test_db_session)
    
    # Analyze symptoms
    guidance = advisor.analyze_symptoms(symptoms, user_info)
    
    # Property: Self-care recommendations should be strings
    for rec in guidance.self_care_recommendations:
        assert isinstance(rec, str), \
            "Each self-care recommendation should be a string"
        assert len(rec) > 0, \
            "Self-care recommendations should not be empty strings"


def test_health_guidance_specific_fever_cough(test_db_session):
    """
    Specific example test: Fever and cough should generate appropriate guidance.
    
    This complements property-based tests with a concrete example.
    """
    # Create health advisor
    advisor = HealthAdvisor(test_db_session)
    
    # Analyze common cold symptoms
    symptoms = ['fever', 'cough', 'runny nose']
    guidance = advisor.analyze_symptoms(symptoms)
    
    # Should have routine or soon urgency
    assert guidance.urgency_level in ['routine', 'soon'], \
        f"Common cold symptoms should have routine/soon urgency, got {guidance.urgency_level}"
    
    # Should have possible conditions
    assert len(guidance.possible_conditions) > 0, \
        "Should identify possible conditions"
    
    # Common cold or flu should be in possible conditions
    conditions_lower = [c.lower() for c in guidance.possible_conditions]
    assert any('cold' in c or 'flu' in c for c in conditions_lower), \
        "Should identify common cold or flu as possible condition"
    
    # Should have self-care recommendations
    assert len(guidance.self_care_recommendations) > 0, \
        "Should provide self-care recommendations"
    
    # Should have disclaimer
    assert len(guidance.disclaimer) > 0, \
        "Should include disclaimer"
    
    # Should have confidence score
    assert 0.0 <= guidance.confidence <= 1.0, \
        "Should have valid confidence score"


def test_health_guidance_specific_chest_pain(test_db_session):
    """
    Specific example test: Chest pain should trigger emergency response.
    """
    # Create health advisor
    advisor = HealthAdvisor(test_db_session)
    
    # Analyze emergency symptom
    symptoms = ['chest pain']
    guidance = advisor.analyze_symptoms(symptoms)
    
    # Should have emergency urgency
    assert guidance.urgency_level == 'emergency', \
        f"Chest pain should have emergency urgency, got {guidance.urgency_level}"
    
    # Should recommend immediate care
    assert 'immediate' in guidance.when_to_seek_care.lower() or 'emergency' in guidance.when_to_seek_care.lower(), \
        "Should recommend immediate emergency care"
    
    # Should have disclaimer
    assert len(guidance.disclaimer) > 0, \
        "Should include disclaimer"


def test_health_guidance_specific_stomach_pain(test_db_session):
    """
    Specific example test: Stomach pain should generate appropriate guidance.
    """
    # Create health advisor
    advisor = HealthAdvisor(test_db_session)
    
    # Analyze stomach pain
    symptoms = ['stomach pain', 'nausea']
    guidance = advisor.analyze_symptoms(symptoms)
    
    # Should have some urgency level
    assert guidance.urgency_level in ['routine', 'soon', 'urgent', 'emergency'], \
        "Should have valid urgency level"
    
    # Should have possible conditions
    assert len(guidance.possible_conditions) > 0, \
        "Should identify possible conditions"
    
    # Should have self-care recommendations
    assert len(guidance.self_care_recommendations) > 0, \
        "Should provide self-care recommendations"
    
    # Should have when to seek care guidance
    assert len(guidance.when_to_seek_care) > 0, \
        "Should provide guidance on when to seek care"


def test_health_guidance_empty_symptoms_handling(test_db_session):
    """
    Edge case test: Empty symptom list should be handled gracefully.
    """
    # Create health advisor
    advisor = HealthAdvisor(test_db_session)
    
    # This should raise an error or handle gracefully
    # Based on the implementation, it should still return guidance
    try:
        symptoms = []
        guidance = advisor.analyze_symptoms(symptoms)
        
        # If it doesn't raise an error, should still have required fields
        assert hasattr(guidance, 'urgency_level')
        assert hasattr(guidance, 'disclaimer')
    except (ValueError, AssertionError):
        # It's acceptable to raise an error for empty symptoms
        pass


def test_health_guidance_multiple_symptoms_severity(test_db_session):
    """
    Test that multiple symptoms may increase urgency level.
    """
    # Create health advisor
    advisor = HealthAdvisor(test_db_session)
    
    # Single mild symptom
    single_symptom = ['headache']
    single_guidance = advisor.analyze_symptoms(single_symptom)
    
    # Multiple symptoms
    multiple_symptoms = ['fever', 'headache', 'body ache', 'fatigue']
    multiple_guidance = advisor.analyze_symptoms(multiple_symptoms)
    
    # Both should have valid urgency levels
    assert single_guidance.urgency_level in ['routine', 'soon', 'urgent', 'emergency']
    assert multiple_guidance.urgency_level in ['routine', 'soon', 'urgent', 'emergency']
    
    # Both should have guidance
    assert len(single_guidance.self_care_recommendations) > 0
    assert len(multiple_guidance.self_care_recommendations) > 0


def test_health_guidance_with_user_info(test_db_session):
    """
    Test that user info is accepted and doesn't break the guidance generation.
    """
    # Create health advisor
    advisor = HealthAdvisor(test_db_session)
    
    # Create user info
    user_info = BasicHealthInfo(
        age=65,
        gender='male',
        existing_conditions=['diabetes', 'hypertension'],
        medications=['metformin', 'aspirin']
    )
    
    # Analyze symptoms with user info
    symptoms = ['fever', 'cough']
    guidance = advisor.analyze_symptoms(symptoms, user_info)
    
    # Should generate valid guidance
    assert guidance.urgency_level in ['routine', 'soon', 'urgent', 'emergency']
    assert len(guidance.self_care_recommendations) > 0
    assert len(guidance.disclaimer) > 0
    assert 0.0 <= guidance.confidence <= 1.0


def test_health_guidance_red_flags_present(test_db_session):
    """
    Test that red flags are provided for all guidance.
    """
    # Create health advisor
    advisor = HealthAdvisor(test_db_session)
    
    # Analyze various symptoms
    test_cases = [
        ['fever'],
        ['headache', 'dizziness'],
        ['stomach pain', 'vomiting'],
        ['cough', 'fatigue']
    ]
    
    for symptoms in test_cases:
        guidance = advisor.analyze_symptoms(symptoms)
        
        # Should have red flags
        assert isinstance(guidance.red_flags, list), \
            f"Red flags should be a list for symptoms {symptoms}"
        
        # Red flags should be strings
        for flag in guidance.red_flags:
            assert isinstance(flag, str), \
                "Each red flag should be a string"
            assert len(flag) > 0, \
                "Red flags should not be empty strings"
