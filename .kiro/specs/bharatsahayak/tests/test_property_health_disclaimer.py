"""
Property-Based Test: Health Disclaimer Presence
Feature: bharatsahayak, Property 14: Health Disclaimer Presence

For any health guidance output, the response should contain a disclaimer stating 
that the advice is informational and not a substitute for professional medical 
consultation.

Validates: Requirements 5.3
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
def test_health_disclaimer_always_present(symptoms, user_info, test_db_session):
    """
    Feature: bharatsahayak, Property 14: Health Disclaimer Presence
    
    For any health guidance output, the response should contain a disclaimer 
    stating that the advice is informational and not a substitute for 
    professional medical consultation.
    
    This is the core property test validating Requirement 5.3.
    """
    # Create health advisor
    advisor = HealthAdvisor(test_db_session)
    
    # Analyze symptoms
    guidance = advisor.analyze_symptoms(symptoms, user_info)
    
    # Property 1: Disclaimer field must exist
    assert hasattr(guidance, 'disclaimer'), \
        "Health guidance must have a 'disclaimer' field"
    
    # Property 2: Disclaimer must not be None
    assert guidance.disclaimer is not None, \
        "Disclaimer field must not be None"
    
    # Property 3: Disclaimer must be a non-empty string
    assert isinstance(guidance.disclaimer, str), \
        "Disclaimer must be a string"
    assert len(guidance.disclaimer) > 0, \
        "Disclaimer must not be an empty string"
    
    # Property 4: Disclaimer must be meaningful (minimum length)
    assert len(guidance.disclaimer) >= 50, \
        f"Disclaimer should be meaningful (at least 50 characters), got {len(guidance.disclaimer)} characters"


@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    symptoms=symptom_list_strategy(),
    user_info=basic_health_info_strategy()
)
def test_health_disclaimer_content_requirements(symptoms, user_info, test_db_session):
    """
    Feature: bharatsahayak, Property 14: Health Disclaimer Presence
    
    The disclaimer should contain specific key phrases indicating it's 
    informational and not a substitute for professional medical advice.
    
    This validates the content quality of the disclaimer.
    """
    # Create health advisor
    advisor = HealthAdvisor(test_db_session)
    
    # Analyze symptoms
    guidance = advisor.analyze_symptoms(symptoms, user_info)
    
    disclaimer_lower = guidance.disclaimer.lower()
    
    # Property 1: Must mention informational purpose
    assert 'informational' in disclaimer_lower or 'information' in disclaimer_lower, \
        "Disclaimer must mention that advice is informational"
    
    # Property 2: Must state it's not a substitute
    assert 'not a substitute' in disclaimer_lower or 'not substitute' in disclaimer_lower, \
        "Disclaimer must state it's not a substitute for professional medical advice"
    
    # Property 3: Must mention medical advice/consultation
    assert 'medical' in disclaimer_lower, \
        "Disclaimer must mention medical advice or consultation"
    
    assert 'advice' in disclaimer_lower or 'consultation' in disclaimer_lower, \
        "Disclaimer must mention advice or consultation"


@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    symptoms=symptom_list_strategy(),
    user_info=basic_health_info_strategy()
)
def test_health_disclaimer_professional_reference(symptoms, user_info, test_db_session):
    """
    Feature: bharatsahayak, Property 14: Health Disclaimer Presence
    
    The disclaimer should reference seeking professional medical help.
    
    This ensures users are directed to qualified healthcare providers.
    """
    # Create health advisor
    advisor = HealthAdvisor(test_db_session)
    
    # Analyze symptoms
    guidance = advisor.analyze_symptoms(symptoms, user_info)
    
    disclaimer_lower = guidance.disclaimer.lower()
    
    # Property: Must reference seeking professional help
    professional_keywords = [
        'physician', 'doctor', 'health provider', 'qualified health',
        'medical professional', 'healthcare provider'
    ]
    
    has_professional_reference = any(keyword in disclaimer_lower for keyword in professional_keywords)
    
    assert has_professional_reference, \
        f"Disclaimer must reference seeking help from qualified healthcare professionals. " \
        f"Expected one of {professional_keywords} in disclaimer"


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
def test_health_disclaimer_present_for_emergency_symptoms(symptoms, user_info, test_db_session):
    """
    Feature: bharatsahayak, Property 14: Health Disclaimer Presence
    
    Even for emergency symptoms, the disclaimer must be present.
    
    This ensures legal protection and user awareness in all cases.
    """
    # Create health advisor
    advisor = HealthAdvisor(test_db_session)
    
    # Analyze emergency symptoms
    guidance = advisor.analyze_symptoms(symptoms, user_info)
    
    # Property: Disclaimer must be present even for emergencies
    assert hasattr(guidance, 'disclaimer'), \
        "Disclaimer must be present even for emergency symptoms"
    
    assert guidance.disclaimer is not None and len(guidance.disclaimer) > 0, \
        "Disclaimer must be non-empty even for emergency symptoms"
    
    # Verify it's still a proper disclaimer
    disclaimer_lower = guidance.disclaimer.lower()
    assert 'informational' in disclaimer_lower or 'information' in disclaimer_lower, \
        "Emergency guidance must still have informational disclaimer"


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
def test_health_disclaimer_present_for_routine_symptoms(symptoms, user_info, test_db_session):
    """
    Feature: bharatsahayak, Property 14: Health Disclaimer Presence
    
    For routine symptoms, the disclaimer must be present.
    
    This ensures consistency across all urgency levels.
    """
    # Create health advisor
    advisor = HealthAdvisor(test_db_session)
    
    # Analyze routine symptoms
    guidance = advisor.analyze_symptoms(symptoms, user_info)
    
    # Property: Disclaimer must be present for routine symptoms
    assert hasattr(guidance, 'disclaimer'), \
        "Disclaimer must be present for routine symptoms"
    
    assert guidance.disclaimer is not None and len(guidance.disclaimer) > 0, \
        "Disclaimer must be non-empty for routine symptoms"
    
    # Verify it's a proper disclaimer
    disclaimer_lower = guidance.disclaimer.lower()
    assert 'not a substitute' in disclaimer_lower or 'not substitute' in disclaimer_lower, \
        "Routine guidance must have proper disclaimer"


@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    symptoms=symptom_list_strategy(),
    user_info=basic_health_info_strategy()
)
def test_health_disclaimer_consistency(symptoms, user_info, test_db_session):
    """
    Feature: bharatsahayak, Property 14: Health Disclaimer Presence
    
    The disclaimer should be consistent across all health guidance outputs.
    
    This ensures users receive the same legal protection message.
    """
    # Create health advisor
    advisor = HealthAdvisor(test_db_session)
    
    # Analyze symptoms
    guidance = advisor.analyze_symptoms(symptoms, user_info)
    
    # Property: Disclaimer should match the standard disclaimer
    # (or at least contain the key elements)
    expected_disclaimer = advisor.HEALTH_DISCLAIMER
    
    # The disclaimer should either be exactly the standard one,
    # or contain all its key elements
    if guidance.disclaimer != expected_disclaimer:
        # If not exact match, verify it contains key elements
        disclaimer_lower = guidance.disclaimer.lower()
        expected_lower = expected_disclaimer.lower()
        
        # Extract key phrases from expected disclaimer
        key_phrases = [
            'informational',
            'not a substitute',
            'professional medical advice',
            'physician',
            'qualified health provider'
        ]
        
        # At least 3 out of 5 key phrases should be present
        matches = sum(1 for phrase in key_phrases if phrase in disclaimer_lower)
        
        assert matches >= 3, \
            f"Disclaimer should contain at least 3 key phrases from standard disclaimer. " \
            f"Found {matches}/5 key phrases"


def test_health_disclaimer_specific_example_fever(test_db_session):
    """
    Specific example test: Fever should have disclaimer.
    
    This complements property-based tests with a concrete example.
    """
    # Create health advisor
    advisor = HealthAdvisor(test_db_session)
    
    # Analyze fever symptom
    symptoms = ['fever']
    guidance = advisor.analyze_symptoms(symptoms)
    
    # Should have disclaimer
    assert hasattr(guidance, 'disclaimer')
    assert guidance.disclaimer is not None
    assert len(guidance.disclaimer) > 0
    
    # Should contain key phrases
    disclaimer_lower = guidance.disclaimer.lower()
    assert 'informational' in disclaimer_lower or 'information' in disclaimer_lower
    assert 'not a substitute' in disclaimer_lower or 'not substitute' in disclaimer_lower
    assert 'medical' in disclaimer_lower


def test_health_disclaimer_specific_example_chest_pain(test_db_session):
    """
    Specific example test: Emergency symptom (chest pain) should have disclaimer.
    """
    # Create health advisor
    advisor = HealthAdvisor(test_db_session)
    
    # Analyze emergency symptom
    symptoms = ['chest pain']
    guidance = advisor.analyze_symptoms(symptoms)
    
    # Should have disclaimer even for emergency
    assert hasattr(guidance, 'disclaimer')
    assert guidance.disclaimer is not None
    assert len(guidance.disclaimer) > 0
    
    # Should be the standard disclaimer
    assert guidance.disclaimer == advisor.HEALTH_DISCLAIMER


def test_health_disclaimer_specific_example_multiple_symptoms(test_db_session):
    """
    Specific example test: Multiple symptoms should have disclaimer.
    """
    # Create health advisor
    advisor = HealthAdvisor(test_db_session)
    
    # Analyze multiple symptoms
    symptoms = ['fever', 'cough', 'headache', 'body ache']
    guidance = advisor.analyze_symptoms(symptoms)
    
    # Should have disclaimer
    assert hasattr(guidance, 'disclaimer')
    assert guidance.disclaimer is not None
    assert len(guidance.disclaimer) > 0
    
    # Should match standard disclaimer
    assert guidance.disclaimer == advisor.HEALTH_DISCLAIMER


def test_health_disclaimer_with_user_info(test_db_session):
    """
    Test that disclaimer is present even when user info is provided.
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
    
    # Should have disclaimer
    assert hasattr(guidance, 'disclaimer')
    assert guidance.disclaimer is not None
    assert len(guidance.disclaimer) > 0
    assert guidance.disclaimer == advisor.HEALTH_DISCLAIMER


def test_health_disclaimer_standard_text(test_db_session):
    """
    Test that the standard disclaimer text is appropriate and complete.
    """
    # Create health advisor
    advisor = HealthAdvisor(test_db_session)
    
    # Get standard disclaimer
    disclaimer = advisor.HEALTH_DISCLAIMER
    
    # Should be non-empty
    assert len(disclaimer) > 0
    
    # Should contain all required elements
    disclaimer_lower = disclaimer.lower()
    
    # Must mention informational purpose
    assert 'informational' in disclaimer_lower or 'information' in disclaimer_lower
    
    # Must state not a substitute
    assert 'not a substitute' in disclaimer_lower
    
    # Must mention professional medical advice
    assert 'professional medical advice' in disclaimer_lower or \
           ('professional' in disclaimer_lower and 'medical' in disclaimer_lower and 'advice' in disclaimer_lower)
    
    # Must mention seeking advice from physician/provider
    assert 'physician' in disclaimer_lower or 'health provider' in disclaimer_lower
    
    # Must mention emergency situations
    assert 'emergency' in disclaimer_lower


def test_health_disclaimer_immutability(test_db_session):
    """
    Test that the disclaimer is consistent across multiple calls.
    """
    # Create health advisor
    advisor = HealthAdvisor(test_db_session)
    
    # Analyze different symptoms multiple times
    test_cases = [
        ['fever'],
        ['cough', 'headache'],
        ['chest pain'],
        ['stomach pain', 'nausea', 'vomiting']
    ]
    
    disclaimers = []
    for symptoms in test_cases:
        guidance = advisor.analyze_symptoms(symptoms)
        disclaimers.append(guidance.disclaimer)
    
    # All disclaimers should be identical
    assert all(d == disclaimers[0] for d in disclaimers), \
        "Disclaimer should be consistent across all health guidance outputs"
    
    # Should match the standard disclaimer
    assert disclaimers[0] == advisor.HEALTH_DISCLAIMER
