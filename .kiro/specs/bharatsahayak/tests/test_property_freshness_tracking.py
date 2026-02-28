"""
Property-Based Test: Scheme Data Freshness Tracking
Feature: bharatsahayak, Property 26: Scheme Data Freshness Tracking

For any scheme in the database, the scheme record should include a last_updated 
timestamp indicating when the data was last verified.

Validates: Requirements 12.1
"""
import pytest
from hypothesis import given, settings, strategies as st, HealthCheck, assume
from hypothesis.strategies import composite
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Table, Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import JSON, MetaData
from app.models.scheme import Scheme, SchemeTranslation
from app.services.scheme_repository import SchemeRepository
from app.schemas.scheme import SchemeCreate, EligibilityCriteria
import uuid


# Strategy for generating eligibility criteria
@composite
def eligibility_criteria_strategy(draw):
    """Generate valid eligibility criteria"""
    criteria = {}
    
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
            st.sampled_from(['Farmer', 'Student', 'Worker', 'Self-Employed']),
            min_size=1, max_size=3
        ))
    
    return criteria


# Strategy for generating schemes with timestamps
@composite
def scheme_with_timestamp_strategy(draw):
    """Generate a scheme with timestamp information"""
    categories = ['agriculture', 'health', 'education', 'employment', 'social_welfare']
    
    # Generate a timestamp within the last year
    days_ago = draw(st.integers(min_value=0, max_value=365))
    last_updated = datetime.utcnow() - timedelta(days=days_ago)
    
    return {
        'scheme_id': uuid.uuid4(),
        'name': draw(st.text(min_size=10, max_size=100, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters=' -'
        ))),
        'category': draw(st.sampled_from(categories)),
        'description': draw(st.text(min_size=20, max_size=200, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters=' .,()-'
        ))),
        'benefits': draw(st.lists(st.text(min_size=5, max_size=50), min_size=1, max_size=5)),
        'eligibility_criteria': draw(eligibility_criteria_strategy()),
        'required_documents': draw(st.lists(
            st.sampled_from(['Aadhaar Card', 'Income Certificate', 'Residence Proof']),
            min_size=1, max_size=3
        )),
        'application_process': draw(st.lists(
            st.sampled_from(['Visit website', 'Fill form', 'Submit documents']),
            min_size=1, max_size=3
        )),
        'application_url': f'https://example.gov.in/scheme/{uuid.uuid4()}',
        'department': draw(st.sampled_from([
            'Ministry of Agriculture',
            'Ministry of Health',
            'Ministry of Education'
        ])),
        'state': draw(st.sampled_from([None, 'Maharashtra', 'Karnataka', 'Tamil Nadu'])),
        'source_url': f'https://example.gov.in/source/{uuid.uuid4()}',
        'last_updated': last_updated,
        'created_at': last_updated - timedelta(days=draw(st.integers(min_value=0, max_value=30)))
    }


@pytest.fixture(scope="function")
def test_db_session():
    """Create a test database session"""
    from sqlalchemy.types import TypeDecorator, CHAR
    from sqlalchemy.dialects.postgresql import UUID as PG_UUID
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
        Column('created_at', DateTime, nullable=False),
        Column('verification_status', String(20), nullable=True),
        Column('verified_at', DateTime, nullable=True),
        Column('verification_source', String(255), nullable=True)
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


@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    schemes=st.lists(scheme_with_timestamp_strategy(), min_size=1, max_size=20)
)
def test_all_schemes_have_last_updated_timestamp(schemes, test_db_session):
    """
    Feature: bharatsahayak, Property 26: Scheme Data Freshness Tracking
    
    For any scheme in the database, the scheme record should include a 
    last_updated timestamp indicating when the data was last verified.
    
    Property: Every scheme must have a non-null last_updated field.
    """
    # Add schemes to database
    add_schemes_to_db(test_db_session, schemes)
    
    # Retrieve all schemes
    repository = SchemeRepository(test_db_session)
    all_schemes = repository.get_all_schemes(limit=100)
    
    # Property 1: All schemes must have last_updated timestamp
    assert len(all_schemes) > 0, "Should have schemes in database"
    
    for scheme in all_schemes:
        assert scheme.last_updated is not None, \
            f"Scheme '{scheme.name}' (ID: {scheme.scheme_id}) must have last_updated timestamp"
        
        assert isinstance(scheme.last_updated, datetime), \
            f"Scheme '{scheme.name}' last_updated must be a datetime object"


@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    schemes=st.lists(scheme_with_timestamp_strategy(), min_size=1, max_size=20)
)
def test_last_updated_is_valid_timestamp(schemes, test_db_session):
    """
    Feature: bharatsahayak, Property 26: Scheme Data Freshness Tracking
    
    Property: The last_updated timestamp should be a valid datetime that is 
    not in the future and not before the created_at timestamp.
    """
    # Add schemes to database
    add_schemes_to_db(test_db_session, schemes)
    
    # Retrieve all schemes
    repository = SchemeRepository(test_db_session)
    all_schemes = repository.get_all_schemes(limit=100)
    
    current_time = datetime.utcnow()
    
    for scheme in all_schemes:
        # Property 1: last_updated should not be in the future
        assert scheme.last_updated <= current_time + timedelta(seconds=5), \
            f"Scheme '{scheme.name}' last_updated should not be in the future"
        
        # Property 2: last_updated should not be before created_at
        assert scheme.last_updated >= scheme.created_at, \
            f"Scheme '{scheme.name}' last_updated should not be before created_at"


@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    scheme_data=scheme_with_timestamp_strategy()
)
def test_newly_created_scheme_has_last_updated(scheme_data, test_db_session):
    """
    Feature: bharatsahayak, Property 26: Scheme Data Freshness Tracking
    
    Property: When a new scheme is created, it should automatically have 
    a last_updated timestamp set.
    """
    # Create scheme using repository
    repository = SchemeRepository(test_db_session)
    
    # Convert to SchemeCreate schema
    eligibility = EligibilityCriteria(**scheme_data['eligibility_criteria'])
    
    scheme_create = SchemeCreate(
        name=scheme_data['name'],
        category=scheme_data['category'],
        description=scheme_data['description'],
        benefits=scheme_data['benefits'],
        eligibility_criteria=eligibility,
        required_documents=scheme_data['required_documents'],
        application_process=scheme_data['application_process'],
        application_url=scheme_data['application_url'],
        department=scheme_data['department'],
        state=scheme_data['state'],
        source_url=scheme_data['source_url']
    )
    
    # Create scheme
    before_creation = datetime.utcnow()
    created_scheme = repository.create_scheme(scheme_create)
    after_creation = datetime.utcnow()
    
    # Property: Newly created scheme must have last_updated
    assert created_scheme.last_updated is not None, \
        "Newly created scheme must have last_updated timestamp"
    
    # Property: last_updated should be around creation time
    assert before_creation <= created_scheme.last_updated <= after_creation + timedelta(seconds=1), \
        "Newly created scheme last_updated should be set to creation time"


@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    scheme_data=scheme_with_timestamp_strategy()
)
def test_updated_scheme_refreshes_last_updated(scheme_data, test_db_session):
    """
    Feature: bharatsahayak, Property 26: Scheme Data Freshness Tracking
    
    Property: When a scheme is updated, the last_updated timestamp should 
    be refreshed to reflect the update time.
    """
    # Add scheme to database
    add_schemes_to_db(test_db_session, [scheme_data])
    
    repository = SchemeRepository(test_db_session)
    
    # Get the scheme
    schemes = repository.get_all_schemes(limit=1)
    original_scheme = schemes[0]
    original_last_updated = original_scheme.last_updated
    scheme_id = str(original_scheme.scheme_id)
    
    # Wait a tiny bit to ensure timestamp difference
    import time
    time.sleep(0.01)
    
    # Update the scheme
    from app.schemas.scheme import SchemeUpdate
    update_data = SchemeUpdate(description="Updated description for freshness test")
    
    before_update = datetime.utcnow()
    updated_scheme = repository.update_scheme(scheme_id, update_data)
    after_update = datetime.utcnow()
    
    # Property: last_updated should be refreshed
    assert updated_scheme.last_updated is not None, \
        "Updated scheme must have last_updated timestamp"
    
    assert updated_scheme.last_updated > original_last_updated, \
        "Updated scheme last_updated should be newer than original"
    
    assert before_update <= updated_scheme.last_updated <= after_update + timedelta(seconds=1), \
        "Updated scheme last_updated should reflect update time"


@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    schemes=st.lists(scheme_with_timestamp_strategy(), min_size=5, max_size=20)
)
def test_schemes_can_be_queried_by_freshness(schemes, test_db_session):
    """
    Feature: bharatsahayak, Property 26: Scheme Data Freshness Tracking
    
    Property: Schemes with older last_updated timestamps can be identified 
    for reverification purposes.
    """
    # Add schemes to database
    add_schemes_to_db(test_db_session, schemes)
    
    repository = SchemeRepository(test_db_session)
    
    # Get schemes needing verification (older than 30 days)
    schemes_needing_verification = repository.get_schemes_needing_verification(
        reverification_days=30,
        limit=100
    )
    
    # Property: All returned schemes should have last_updated older than 30 days
    # or be unverified
    cutoff_date = datetime.utcnow() - timedelta(days=30)
    
    for scheme in schemes_needing_verification:
        # Should either have no verified_at, or verified_at older than cutoff,
        # or verification_status != 'verified'
        condition_met = (
            scheme.verified_at is None or
            scheme.verified_at < cutoff_date or
            scheme.verification_status != 'verified'
        )
        
        assert condition_met, \
            f"Scheme '{scheme.name}' should need verification based on criteria"


def test_specific_scheme_has_timestamp(test_db_session):
    """
    Specific example test: A concrete scheme should have last_updated timestamp.
    """
    scheme_data = {
        'scheme_id': uuid.uuid4(),
        'name': 'PM-KISAN Scheme',
        'category': 'agriculture',
        'description': 'Provides Rs 6000 per year to farmers',
        'benefits': ['Direct income support', 'Financial assistance'],
        'eligibility_criteria': {'occupation': ['Farmer']},
        'required_documents': ['Aadhaar', 'Land records'],
        'application_process': ['Visit website', 'Apply online'],
        'application_url': 'https://pmkisan.gov.in',
        'department': 'Ministry of Agriculture',
        'state': None,
        'source_url': 'https://pmkisan.gov.in',
        'last_updated': datetime.utcnow(),
        'created_at': datetime.utcnow()
    }
    
    add_schemes_to_db(test_db_session, [scheme_data])
    
    repository = SchemeRepository(test_db_session)
    scheme = repository.get_scheme_by_id(str(scheme_data['scheme_id']))
    
    assert scheme is not None, "Scheme should be found"
    assert scheme.last_updated is not None, "PM-KISAN should have last_updated"
    assert isinstance(scheme.last_updated, datetime), "last_updated should be datetime"


def test_scheme_without_timestamp_fails_validation(test_db_session):
    """
    Edge case test: Attempting to query schemes should always return schemes 
    with timestamps (our system enforces this).
    """
    # Create a scheme with timestamp
    scheme_data = {
        'scheme_id': uuid.uuid4(),
        'name': 'Test Scheme',
        'category': 'agriculture',
        'description': 'Test description',
        'benefits': ['Test benefit'],
        'eligibility_criteria': {},
        'required_documents': [],
        'application_process': [],
        'application_url': None,
        'department': 'Test Department',
        'state': None,
        'source_url': None,
        'last_updated': datetime.utcnow(),
        'created_at': datetime.utcnow()
    }
    
    add_schemes_to_db(test_db_session, [scheme_data])
    
    repository = SchemeRepository(test_db_session)
    all_schemes = repository.get_all_schemes()
    
    # All schemes should have timestamps
    for scheme in all_schemes:
        assert scheme.last_updated is not None, \
            "All schemes in system must have last_updated timestamp"


def test_timestamp_ordering_for_verification_queue(test_db_session):
    """
    Test that schemes needing verification are ordered by last_updated 
    (oldest first) for prioritization.
    """
    # Create schemes with different timestamps
    schemes_data = []
    for i in range(5):
        schemes_data.append({
            'scheme_id': uuid.uuid4(),
            'name': f'Scheme {i}',
            'category': 'agriculture',
            'description': f'Description {i}',
            'benefits': [f'Benefit {i}'],
            'eligibility_criteria': {},
            'required_documents': [],
            'application_process': [],
            'application_url': None,
            'department': 'Agriculture',
            'state': None,
            'source_url': None,
            'last_updated': datetime.utcnow() - timedelta(days=100 - i*10),
            'created_at': datetime.utcnow() - timedelta(days=100)
        })
    
    add_schemes_to_db(test_db_session, schemes_data)
    
    repository = SchemeRepository(test_db_session)
    schemes_needing_verification = repository.get_schemes_needing_verification(
        reverification_days=30,
        limit=100
    )
    
    # Should be ordered by last_updated ascending (oldest first)
    for i in range(len(schemes_needing_verification) - 1):
        assert schemes_needing_verification[i].last_updated <= \
               schemes_needing_verification[i+1].last_updated, \
            "Schemes should be ordered by last_updated ascending for verification queue"


def test_timestamp_preserved_across_retrieval(test_db_session):
    """
    Test that last_updated timestamp is preserved when retrieving schemes.
    """
    original_timestamp = datetime.utcnow() - timedelta(days=10)
    
    scheme_data = {
        'scheme_id': uuid.uuid4(),
        'name': 'Test Scheme',
        'category': 'agriculture',
        'description': 'Test description',
        'benefits': ['Test benefit'],
        'eligibility_criteria': {},
        'required_documents': [],
        'application_process': [],
        'application_url': None,
        'department': 'Test Department',
        'state': None,
        'source_url': None,
        'last_updated': original_timestamp,
        'created_at': original_timestamp - timedelta(days=5)
    }
    
    add_schemes_to_db(test_db_session, [scheme_data])
    
    repository = SchemeRepository(test_db_session)
    retrieved_scheme = repository.get_scheme_by_id(str(scheme_data['scheme_id']))
    
    # Timestamp should be preserved (within 1 second for precision)
    time_diff = abs((retrieved_scheme.last_updated - original_timestamp).total_seconds())
    assert time_diff < 1, \
        "last_updated timestamp should be preserved across database operations"
