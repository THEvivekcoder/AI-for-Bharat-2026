"""
Property-Based Test: Complete Information Display
Feature: bharatsahayak, Property 5: Complete Information Display

For any scheme, skill program, or job posting displayed to the user, the output 
should contain all required fields (name, description, eligibility, application 
process, contact information) with no null or missing critical fields.

Validates: Requirements 2.2, 4.2
"""
import pytest
from hypothesis import given, settings, strategies as st, HealthCheck, assume
from hypothesis.strategies import composite
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.scheme import Scheme, SchemeTranslation
from app.services.scheme_repository import SchemeRepository
from app.schemas.scheme import SchemeFilters
import uuid


# Strategy for generating eligibility criteria
@composite
def eligibility_criteria_strategy(draw):
    """Generate valid eligibility criteria"""
    criteria = {}
    
    # Randomly include various criteria
    if draw(st.booleans()):
        criteria['age_min'] = draw(st.integers(min_value=0, max_value=18))
    if draw(st.booleans()):
        criteria['age_max'] = draw(st.integers(min_value=18, max_value=100))
    if draw(st.booleans()):
        criteria['income_max'] = draw(st.integers(min_value=50000, max_value=500000))
    if draw(st.booleans()):
        criteria['gender'] = draw(st.sampled_from(['Male', 'Female', 'Any']))
    if draw(st.booleans()):
        criteria['occupation'] = draw(st.lists(
            st.sampled_from(['Farmer', 'Student', 'Worker', 'Self-Employed', 'Unemployed']),
            min_size=1, max_size=3
        ))
    if draw(st.booleans()):
        criteria['location'] = draw(st.lists(
            st.sampled_from(['Maharashtra', 'Karnataka', 'Tamil Nadu', 'Uttar Pradesh', 'Bihar']),
            min_size=1, max_size=3
        ))
    
    return criteria


# Strategy for generating complete schemes (all required fields populated)
@composite
def complete_scheme_strategy(draw):
    """Generate a scheme with all required fields populated"""
    categories = ['agriculture', 'health', 'education', 'employment', 'social_welfare']
    category = draw(st.sampled_from(categories))
    
    # Generate realistic content based on category
    scheme_templates = {
        'agriculture': {
            'names': ['PM-KISAN Scheme', 'Crop Insurance Scheme', 'Soil Health Card Scheme'],
            'descriptions': ['Provides financial assistance to farmers for agricultural activities'],
            'benefits': [['Direct income support', 'Rs 6000 per year', 'Three installments']],
            'documents': [['Aadhaar Card', 'Land records', 'Bank account details']],
            'process': [['Visit official website', 'Fill application form', 'Upload documents', 'Submit application']],
            'departments': ['Ministry of Agriculture', 'Department of Agriculture']
        },
        'health': {
            'names': ['Ayushman Bharat Scheme', 'Pradhan Mantri Jan Arogya Yojana'],
            'descriptions': ['Provides health insurance coverage for poor and vulnerable families'],
            'benefits': [['Health insurance', 'Rs 5 lakh coverage', 'Cashless treatment']],
            'documents': [['Aadhaar Card', 'Income certificate', 'Residence proof']],
            'process': [['Visit empaneled hospital', 'Show Ayushman card', 'Get cashless treatment']],
            'departments': ['Ministry of Health', 'Department of Health Services']
        },
        'education': {
            'names': ['Mid-Day Meal Scheme', 'Scholarship for Students'],
            'descriptions': ['Provides nutritious meals to school children'],
            'benefits': [['Free meals', 'Improved nutrition', 'Better attendance']],
            'documents': [['School enrollment certificate', 'Aadhaar Card']],
            'process': [['Enroll in school', 'Automatic enrollment in scheme']],
            'departments': ['Ministry of Education', 'Department of School Education']
        },
        'employment': {
            'names': ['MGNREGA Employment Scheme', 'Pradhan Mantri Rozgar Yojana'],
            'descriptions': ['Guarantees 100 days of wage employment in rural areas'],
            'benefits': [['Guaranteed employment', 'Minimum wages', 'Asset creation']],
            'documents': [['Aadhaar Card', 'Job card', 'Bank account']],
            'process': [['Apply at gram panchayat', 'Get job card', 'Request work']],
            'departments': ['Ministry of Rural Development', 'Department of Rural Development']
        },
        'social_welfare': {
            'names': ['Pension Scheme for Elderly', 'Widow Pension Scheme'],
            'descriptions': ['Provides monthly pension to senior citizens'],
            'benefits': [['Monthly pension', 'Financial security', 'Social protection']],
            'documents': [['Aadhaar Card', 'Age proof', 'Bank account details']],
            'process': [['Visit district office', 'Submit application', 'Verification', 'Pension approval']],
            'departments': ['Ministry of Social Justice', 'Department of Social Welfare']
        }
    }
    
    template = scheme_templates[category]
    
    return {
        'scheme_id': uuid.uuid4(),
        'name': draw(st.sampled_from(template['names'])),
        'category': category,
        'description': draw(st.sampled_from(template['descriptions'])),
        'benefits': draw(st.sampled_from(template['benefits'])),
        'eligibility_criteria': draw(eligibility_criteria_strategy()),
        'required_documents': draw(st.sampled_from(template['documents'])),
        'application_process': draw(st.sampled_from(template['process'])),
        'application_url': f'https://example.gov.in/scheme/{uuid.uuid4()}',
        'department': draw(st.sampled_from(template['departments'])),
        'state': draw(st.sampled_from([None, 'Maharashtra', 'Karnataka', 'Tamil Nadu'])),
        'source_url': f'https://example.gov.in/source/{uuid.uuid4()}',
        'last_updated': datetime.utcnow(),
        'created_at': datetime.utcnow()
    }


# Strategy for generating incomplete schemes (missing some critical fields)
@composite
def incomplete_scheme_strategy(draw):
    """Generate a scheme with some required fields missing or null"""
    categories = ['agriculture', 'health', 'education', 'employment', 'social_welfare']
    category = draw(st.sampled_from(categories))
    
    # Ensure at least one critical field is missing
    # Choose which field(s) to make null/empty
    missing_field = draw(st.sampled_from(['benefits', 'documents', 'process', 'multiple']))
    
    if missing_field == 'benefits':
        benefits = None
        documents = ['Aadhaar']
        process = ['Apply online']
    elif missing_field == 'documents':
        benefits = ['Some benefit']
        documents = None
        process = ['Apply online']
    elif missing_field == 'process':
        benefits = ['Some benefit']
        documents = ['Aadhaar']
        process = None
    else:  # multiple
        # Make multiple fields null
        benefits = None if draw(st.booleans()) else ['Some benefit']
        documents = None if draw(st.booleans()) else ['Aadhaar']
        process = None if draw(st.booleans()) else ['Apply online']
        # Ensure at least one is None
        if benefits is not None and documents is not None and process is not None:
            benefits = None
    
    return {
        'scheme_id': uuid.uuid4(),
        'name': f'Incomplete Scheme {uuid.uuid4().hex[:8]}',
        'category': category,
        'description': 'Some description',
        'benefits': benefits,
        'eligibility_criteria': draw(eligibility_criteria_strategy()),
        'required_documents': documents,
        'application_process': process,
        'application_url': f'https://example.gov.in/scheme/{uuid.uuid4()}',
        'department': 'Some Department',
        'state': None,
        'source_url': f'https://example.gov.in/source/{uuid.uuid4()}',
        'last_updated': datetime.utcnow(),
        'created_at': datetime.utcnow()
    }


@pytest.fixture(scope="function")
def test_db_session():
    """Create a test database session"""
    from sqlalchemy.types import TypeDecorator, CHAR
    from sqlalchemy.dialects.postgresql import UUID as PG_UUID
    from sqlalchemy import Table, Column, String, DateTime, Text, ForeignKey, JSON
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
    
    # Create scheme tables manually for SQLite compatibility
    from sqlalchemy import MetaData
    metadata = MetaData()
    
    schemes_table = Table(
        'schemes', metadata,
        Column('scheme_id', UUID(), primary_key=True),
        Column('name', String(255), nullable=False),
        Column('category', String(50), nullable=False),
        Column('description', Text, nullable=True),
        Column('benefits', JSON, nullable=True),
        Column('eligibility_criteria', JSON, nullable=False),
        Column('required_documents', JSON, nullable=True),
        Column('application_process', JSON, nullable=True),
        Column('application_url', String(500), nullable=True),
        Column('department', String(100), nullable=True),
        Column('state', String(50), nullable=True),
        Column('last_updated', DateTime, nullable=True),
        Column('source_url', String(500), nullable=True),
        Column('created_at', DateTime, nullable=False)
    )
    
    scheme_translations_table = Table(
        'scheme_translations', metadata,
        Column('translation_id', UUID(), primary_key=True),
        Column('scheme_id', UUID(), ForeignKey('schemes.scheme_id'), nullable=False),
        Column('language', String(10), nullable=False),
        Column('name', String(255), nullable=True),
        Column('description', Text, nullable=True),
        Column('benefits', JSON, nullable=True)
    )
    
    metadata.create_all(engine)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()


def add_schemes_to_db(session, schemes_data):
    """Helper to add schemes to test database"""
    session.query(Scheme).delete()
    session.commit()
    
    schemes = []
    for scheme_data in schemes_data:
        scheme = Scheme(**scheme_data)
        session.add(scheme)
        schemes.append(scheme)
    
    session.commit()
    return schemes


def check_scheme_completeness(scheme):
    """
    Check if a scheme has all required fields populated.
    
    Required fields per Requirement 2.2:
    - name (always required)
    - benefits
    - eligibility_criteria
    - required_documents
    - application_process
    
    Returns: (is_complete, missing_fields)
    """
    missing_fields = []
    
    # Name is always required (enforced by database)
    if not scheme.name or scheme.name.strip() == '':
        missing_fields.append('name')
    
    # Benefits should be present and non-empty
    if not scheme.benefits or len(scheme.benefits) == 0:
        missing_fields.append('benefits')
    
    # Eligibility criteria should be present (can be empty dict)
    if scheme.eligibility_criteria is None:
        missing_fields.append('eligibility_criteria')
    
    # Required documents should be present and non-empty
    if not scheme.required_documents or len(scheme.required_documents) == 0:
        missing_fields.append('required_documents')
    
    # Application process should be present and non-empty
    if not scheme.application_process or len(scheme.application_process) == 0:
        missing_fields.append('application_process')
    
    is_complete = len(missing_fields) == 0
    return is_complete, missing_fields


@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    schemes=st.lists(complete_scheme_strategy(), min_size=5, max_size=15)
)
def test_complete_information_display_all_fields_present(schemes, test_db_session):
    """
    Feature: bharatsahayak, Property 5: Complete Information Display
    
    For any scheme displayed to the user, the output should contain all 
    required fields with no null or missing critical fields.
    
    This tests that complete schemes pass the completeness check.
    """
    # Add schemes to database
    add_schemes_to_db(test_db_session, schemes)
    
    # Retrieve all schemes
    repository = SchemeRepository(test_db_session)
    filters = SchemeFilters()
    results = repository.search_schemes(filters, limit=100)
    
    # Property: All schemes should have complete information
    for scheme in results:
        is_complete, missing_fields = check_scheme_completeness(scheme)
        
        assert is_complete, \
            f"Scheme '{scheme.name}' is missing required fields: {missing_fields}"
        
        # Verify specific fields are not null
        assert scheme.name is not None and scheme.name.strip() != '', \
            f"Scheme name should not be null or empty"
        
        assert scheme.benefits is not None and len(scheme.benefits) > 0, \
            f"Scheme '{scheme.name}' should have benefits listed"
        
        assert scheme.eligibility_criteria is not None, \
            f"Scheme '{scheme.name}' should have eligibility criteria"
        
        assert scheme.required_documents is not None and len(scheme.required_documents) > 0, \
            f"Scheme '{scheme.name}' should have required documents listed"
        
        assert scheme.application_process is not None and len(scheme.application_process) > 0, \
            f"Scheme '{scheme.name}' should have application process steps"


@settings(
    max_examples=30,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    schemes=st.lists(incomplete_scheme_strategy(), min_size=3, max_size=10)
)
def test_complete_information_display_detects_missing_fields(schemes, test_db_session):
    """
    Feature: bharatsahayak, Property 5: Complete Information Display
    
    For any scheme with missing critical fields, the completeness check 
    should correctly identify which fields are missing.
    
    This tests that incomplete schemes are properly detected.
    """
    # Add schemes to database
    add_schemes_to_db(test_db_session, schemes)
    
    # Retrieve all schemes
    repository = SchemeRepository(test_db_session)
    filters = SchemeFilters()
    results = repository.search_schemes(filters, limit=100)
    
    # Property: Schemes with null/empty critical fields should be detected
    for scheme in results:
        is_complete, missing_fields = check_scheme_completeness(scheme)
        
        # If benefits is null, it should be in missing_fields
        if scheme.benefits is None or len(scheme.benefits) == 0:
            assert 'benefits' in missing_fields, \
                f"Missing benefits should be detected for scheme '{scheme.name}'"
        
        # If required_documents is null, it should be in missing_fields
        if scheme.required_documents is None or len(scheme.required_documents) == 0:
            assert 'required_documents' in missing_fields, \
                f"Missing required_documents should be detected for scheme '{scheme.name}'"
        
        # If application_process is null, it should be in missing_fields
        if scheme.application_process is None or len(scheme.application_process) == 0:
            assert 'application_process' in missing_fields, \
                f"Missing application_process should be detected for scheme '{scheme.name}'"


@settings(
    max_examples=30,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    complete_schemes=st.lists(complete_scheme_strategy(), min_size=3, max_size=8),
    incomplete_schemes=st.lists(incomplete_scheme_strategy(), min_size=2, max_size=5)
)
def test_complete_information_display_mixed_schemes(complete_schemes, incomplete_schemes, test_db_session):
    """
    Feature: bharatsahayak, Property 5: Complete Information Display
    
    When displaying a mix of complete and incomplete schemes, the system 
    should correctly identify which schemes have complete information.
    
    This tests the completeness check with mixed data.
    """
    # Combine complete and incomplete schemes
    all_schemes = complete_schemes + incomplete_schemes
    
    # Add schemes to database
    add_schemes_to_db(test_db_session, all_schemes)
    
    # Retrieve all schemes
    repository = SchemeRepository(test_db_session)
    filters = SchemeFilters()
    results = repository.search_schemes(filters, limit=100)
    
    complete_count = 0
    incomplete_count = 0
    
    # Property: Each scheme should be correctly classified as complete or incomplete
    for scheme in results:
        is_complete, missing_fields = check_scheme_completeness(scheme)
        
        if is_complete:
            complete_count += 1
            # Complete schemes should have all required fields
            assert scheme.benefits is not None and len(scheme.benefits) > 0
            assert scheme.required_documents is not None and len(scheme.required_documents) > 0
            assert scheme.application_process is not None and len(scheme.application_process) > 0
        else:
            incomplete_count += 1
            # Incomplete schemes should have at least one missing field
            assert len(missing_fields) > 0, \
                f"Incomplete scheme should have missing fields identified"
    
    # Should have both complete and incomplete schemes
    assert complete_count > 0, "Should have some complete schemes"
    assert incomplete_count > 0, "Should have some incomplete schemes"
    assert complete_count + incomplete_count == len(results), \
        "All schemes should be classified as either complete or incomplete"


def test_complete_information_display_specific_scheme(test_db_session):
    """
    Specific example test: A well-formed scheme should pass completeness check.
    
    This complements property-based tests with a concrete example.
    """
    # Create a specific complete scheme
    scheme_data = {
        'scheme_id': uuid.uuid4(),
        'name': 'PM-KISAN Scheme',
        'category': 'agriculture',
        'description': 'Provides Rs 6000 per year to farmers',
        'benefits': ['Direct income support', 'Rs 6000 per year', 'Three installments'],
        'eligibility_criteria': {'occupation': ['Farmer']},
        'required_documents': ['Aadhaar Card', 'Land records', 'Bank account details'],
        'application_process': ['Visit official website', 'Fill application form', 'Upload documents', 'Submit application'],
        'application_url': 'https://pmkisan.gov.in',
        'department': 'Ministry of Agriculture',
        'state': None,
        'source_url': 'https://pmkisan.gov.in',
        'last_updated': datetime.utcnow(),
        'created_at': datetime.utcnow()
    }
    
    add_schemes_to_db(test_db_session, [scheme_data])
    
    # Retrieve the scheme
    repository = SchemeRepository(test_db_session)
    filters = SchemeFilters(query='PM-KISAN')
    results = repository.search_schemes(filters)
    
    assert len(results) == 1, "Should find the PM-KISAN scheme"
    
    scheme = results[0]
    is_complete, missing_fields = check_scheme_completeness(scheme)
    
    assert is_complete, f"PM-KISAN scheme should be complete, missing: {missing_fields}"
    assert len(missing_fields) == 0, "Should have no missing fields"
    
    # Verify all required fields are present
    assert scheme.name == 'PM-KISAN Scheme'
    assert len(scheme.benefits) == 3
    assert 'Aadhaar Card' in scheme.required_documents
    assert len(scheme.application_process) == 4


def test_complete_information_display_missing_benefits(test_db_session):
    """
    Edge case test: Scheme with missing benefits should be detected.
    """
    scheme_data = {
        'scheme_id': uuid.uuid4(),
        'name': 'Incomplete Scheme',
        'category': 'agriculture',
        'description': 'Some description',
        'benefits': None,  # Missing benefits
        'eligibility_criteria': {},
        'required_documents': ['Aadhaar'],
        'application_process': ['Apply online'],
        'application_url': 'https://example.gov.in',
        'department': 'Agriculture',
        'state': None,
        'source_url': 'https://example.gov.in',
        'last_updated': datetime.utcnow(),
        'created_at': datetime.utcnow()
    }
    
    add_schemes_to_db(test_db_session, [scheme_data])
    
    repository = SchemeRepository(test_db_session)
    filters = SchemeFilters()
    results = repository.search_schemes(filters)
    
    assert len(results) == 1
    scheme = results[0]
    
    is_complete, missing_fields = check_scheme_completeness(scheme)
    
    assert not is_complete, "Scheme should be incomplete"
    assert 'benefits' in missing_fields, "Should detect missing benefits"


def test_complete_information_display_empty_application_process(test_db_session):
    """
    Edge case test: Scheme with empty application process should be detected.
    """
    scheme_data = {
        'scheme_id': uuid.uuid4(),
        'name': 'Scheme Without Process',
        'category': 'health',
        'description': 'Health scheme',
        'benefits': ['Health coverage'],
        'eligibility_criteria': {},
        'required_documents': ['Aadhaar'],
        'application_process': [],  # Empty application process
        'application_url': 'https://example.gov.in',
        'department': 'Health',
        'state': None,
        'source_url': 'https://example.gov.in',
        'last_updated': datetime.utcnow(),
        'created_at': datetime.utcnow()
    }
    
    add_schemes_to_db(test_db_session, [scheme_data])
    
    repository = SchemeRepository(test_db_session)
    filters = SchemeFilters()
    results = repository.search_schemes(filters)
    
    assert len(results) == 1
    scheme = results[0]
    
    is_complete, missing_fields = check_scheme_completeness(scheme)
    
    assert not is_complete, "Scheme should be incomplete"
    assert 'application_process' in missing_fields, "Should detect empty application process"


def test_complete_information_display_multiple_missing_fields(test_db_session):
    """
    Edge case test: Scheme with multiple missing fields should detect all of them.
    """
    scheme_data = {
        'scheme_id': uuid.uuid4(),
        'name': 'Very Incomplete Scheme',
        'category': 'education',
        'description': 'Education scheme',
        'benefits': None,  # Missing
        'eligibility_criteria': {},
        'required_documents': None,  # Missing
        'application_process': [],  # Empty (missing)
        'application_url': 'https://example.gov.in',
        'department': 'Education',
        'state': None,
        'source_url': 'https://example.gov.in',
        'last_updated': datetime.utcnow(),
        'created_at': datetime.utcnow()
    }
    
    add_schemes_to_db(test_db_session, [scheme_data])
    
    repository = SchemeRepository(test_db_session)
    filters = SchemeFilters()
    results = repository.search_schemes(filters)
    
    assert len(results) == 1
    scheme = results[0]
    
    is_complete, missing_fields = check_scheme_completeness(scheme)
    
    assert not is_complete, "Scheme should be incomplete"
    assert 'benefits' in missing_fields, "Should detect missing benefits"
    assert 'required_documents' in missing_fields, "Should detect missing documents"
    assert 'application_process' in missing_fields, "Should detect missing process"
    assert len(missing_fields) == 3, "Should detect all three missing fields"


def test_complete_information_display_minimal_complete_scheme(test_db_session):
    """
    Test that a scheme with minimal but complete information passes the check.
    """
    scheme_data = {
        'scheme_id': uuid.uuid4(),
        'name': 'Minimal Complete Scheme',
        'category': 'social_welfare',
        'description': 'A minimal scheme',
        'benefits': ['One benefit'],  # Minimal but present
        'eligibility_criteria': {},  # Empty but present
        'required_documents': ['Aadhaar'],  # Minimal but present
        'application_process': ['Apply'],  # Minimal but present
        'application_url': 'https://example.gov.in',
        'department': 'Welfare',
        'state': None,
        'source_url': 'https://example.gov.in',
        'last_updated': datetime.utcnow(),
        'created_at': datetime.utcnow()
    }
    
    add_schemes_to_db(test_db_session, [scheme_data])
    
    repository = SchemeRepository(test_db_session)
    filters = SchemeFilters()
    results = repository.search_schemes(filters)
    
    assert len(results) == 1
    scheme = results[0]
    
    is_complete, missing_fields = check_scheme_completeness(scheme)
    
    assert is_complete, f"Minimal complete scheme should pass, missing: {missing_fields}"
    assert len(missing_fields) == 0, "Should have no missing fields"
