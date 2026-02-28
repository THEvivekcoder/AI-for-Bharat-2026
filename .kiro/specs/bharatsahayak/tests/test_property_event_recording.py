"""
Property-Based Test: Interaction Event Recording
Feature: bharatsahayak, Property 23: Interaction Event Recording

For any user interaction (query, scheme access, job discovery), the Impact_Tracker 
should record an event with required fields: user_id, event_type, timestamp, and event_data.

Validates: Requirements 9.1, 9.3
"""
import pytest
import os
from hypothesis import given, settings, strategies as st, HealthCheck
from hypothesis.strategies import composite
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.services.impact_tracker import ImpactTracker
from app.models.impact import InteractionEvent
from app.models.user import User
from app.schemas.impact import InteractionEventCreate, InteractionEventType
from datetime import datetime
import uuid


# Use test database URL from environment or default
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://bharatsahayak:password@localhost:5432/bharatsahayak")


# Strategy for generating valid text without null bytes (PostgreSQL incompatible)
def safe_text_strategy(min_size=1, max_size=200):
    """Generate text that is safe for PostgreSQL (no null bytes or invalid Unicode)"""
    return st.text(
        min_size=min_size,
        max_size=max_size,
        alphabet=st.characters(
            min_codepoint=32,  # Start from space character
            max_codepoint=126,  # ASCII printable characters
            blacklist_categories=('Cs',)  # Exclude surrogates
        )
    )


# Strategy for generating valid event data
@composite
def event_data_strategy(draw):
    """Generate valid event data dictionary"""
    # Generate random event data with common fields
    data = {}
    
    # Optionally add common fields
    if draw(st.booleans()):
        data['query'] = draw(safe_text_strategy(min_size=1, max_size=200))
    
    if draw(st.booleans()):
        data['scheme_id'] = str(uuid.uuid4())
    
    if draw(st.booleans()):
        data['state'] = draw(st.sampled_from([
            'Maharashtra', 'Karnataka', 'Tamil Nadu', 'Uttar Pradesh', 
            'Bihar', 'West Bengal', 'Madhya Pradesh', 'Rajasthan'
        ]))
    
    if draw(st.booleans()):
        data['district'] = draw(safe_text_strategy(min_size=1, max_size=50))
    
    if draw(st.booleans()):
        data['region'] = draw(safe_text_strategy(min_size=1, max_size=50))
    
    if draw(st.booleans()):
        data['crop_name'] = draw(st.sampled_from(['Rice', 'Wheat', 'Cotton', 'Sugarcane', 'Maize']))
    
    if draw(st.booleans()):
        data['job_id'] = str(uuid.uuid4())
    
    if draw(st.booleans()):
        data['facility_id'] = str(uuid.uuid4())
    
    return data if data else None


# Strategy for generating valid interaction events
@composite
def interaction_event_strategy(draw):
    """Generate valid interaction event data"""
    # Optionally generate user_id (can be None for anonymous tracking)
    user_id = draw(st.one_of(
        st.none(),
        st.from_regex(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', fullmatch=True)
    ))
    
    return InteractionEventCreate(
        user_id=user_id,
        event_type=draw(st.sampled_from(list(InteractionEventType))),
        event_data=draw(event_data_strategy()),
        language=draw(st.one_of(
            st.none(),
            st.sampled_from(['hi', 'en', 'bn', 'te', 'mr', 'ta', 'gu', 'kn', 'ml', 'pa'])
        ))
    )


@pytest.fixture(scope="module")
def test_engine():
    """Create test database engine"""
    engine = create_engine(TEST_DATABASE_URL)
    # Create all tables
    Base.metadata.create_all(engine)
    yield engine
    # Drop all tables after tests
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def test_db(test_engine):
    """Create a test database session for each test"""
    TestingSessionLocal = sessionmaker(bind=test_engine)
    db = TestingSessionLocal()
    
    yield db
    
    # Rollback any uncommitted changes and close
    db.rollback()
    # Clean up test data
    db.query(InteractionEvent).delete()
    db.commit()
    db.close()


@pytest.fixture(scope="function")
def impact_tracker(test_db):
    """Create ImpactTracker instance with test database"""
    return ImpactTracker(test_db)


@pytest.fixture(scope="function")
def test_user(test_db):
    """Create a test user for events that need a valid user_id"""
    # Generate unique phone number for each test
    phone_number = f"+9198765{uuid.uuid4().hex[:5]}"
    user = User(
        user_id=uuid.uuid4(),
        phone_number=phone_number,
        language="hi"
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(event_data=interaction_event_strategy())
def test_interaction_event_recording(event_data, test_db, test_user):
    """
    Feature: bharatsahayak, Property 23: Interaction Event Recording
    
    For any user interaction (query, scheme access, job discovery), the Impact_Tracker 
    should record an event with required fields: user_id, event_type, timestamp, and event_data.
    
    This property ensures that all user interactions are properly tracked for impact measurement.
    """
    # Create ImpactTracker
    impact_tracker = ImpactTracker(test_db)
    
    # If event has a user_id, use the test user's ID to ensure it's valid
    if event_data.user_id:
        event_data.user_id = str(test_user.user_id)
    
    # Record the interaction event
    recorded_event = impact_tracker.record_interaction(event_data)
    
    # Assert event was recorded
    assert recorded_event is not None, "Event should be recorded"
    assert recorded_event.interaction_id is not None, "Event should have an interaction_id"
    
    # Assert required fields are present
    assert recorded_event.event_type is not None, "Event must have event_type"
    assert recorded_event.event_type == event_data.event_type.value, "Event type should match input"
    
    assert recorded_event.timestamp is not None, "Event must have timestamp"
    assert isinstance(recorded_event.timestamp, datetime), "Timestamp should be a datetime object"
    
    # Assert user_id is preserved (can be None for anonymous tracking)
    if event_data.user_id:
        assert recorded_event.user_id is not None, "User ID should be preserved when provided"
        assert str(recorded_event.user_id) == event_data.user_id, "User ID should match input"
    else:
        # Anonymous tracking is allowed
        assert recorded_event.user_id is None, "User ID should be None for anonymous events"
    
    # Assert event_data is preserved
    if event_data.event_data:
        assert recorded_event.event_data is not None, "Event data should be preserved when provided"
        # Verify all keys from input are present in recorded event
        for key, value in event_data.event_data.items():
            assert key in recorded_event.event_data, f"Event data key '{key}' should be preserved"
            assert recorded_event.event_data[key] == value, f"Event data value for '{key}' should match input"
    
    # Assert language is preserved
    if event_data.language:
        assert recorded_event.language == event_data.language, "Language should be preserved when provided"
    
    # Verify event can be retrieved from database
    retrieved_event = test_db.query(InteractionEvent).filter(
        InteractionEvent.interaction_id == recorded_event.interaction_id
    ).first()
    
    assert retrieved_event is not None, "Event should be retrievable from database"
    assert retrieved_event.event_type == event_data.event_type.value, "Retrieved event type should match"
    assert retrieved_event.timestamp is not None, "Retrieved event should have timestamp"


def test_event_recording_with_all_fields(test_db, test_user):
    """
    Test event recording with all fields populated.
    
    This is a specific example test to complement the property-based test.
    """
    impact_tracker = ImpactTracker(test_db)
    
    # Create event with all fields
    event = InteractionEventCreate(
        user_id=str(test_user.user_id),
        event_type=InteractionEventType.SCHEME_ACCESSED,
        event_data={
            'scheme_id': str(uuid.uuid4()),
            'scheme_name': 'PM-KISAN',
            'state': 'Maharashtra',
            'district': 'Pune',
            'query': 'agricultural schemes for farmers'
        },
        language='hi'
    )
    
    recorded_event = impact_tracker.record_interaction(event)
    
    assert recorded_event.interaction_id is not None
    assert str(recorded_event.user_id) == event.user_id
    assert recorded_event.event_type == 'scheme_accessed'
    assert recorded_event.event_data['scheme_id'] == event.event_data['scheme_id']
    assert recorded_event.event_data['scheme_name'] == 'PM-KISAN'
    assert recorded_event.event_data['state'] == 'Maharashtra'
    assert recorded_event.language == 'hi'
    assert recorded_event.timestamp is not None


def test_event_recording_anonymous(test_db):
    """
    Test event recording for anonymous users (no user_id).
    
    This is an edge case test for anonymous tracking.
    """
    impact_tracker = ImpactTracker(test_db)
    
    # Create anonymous event
    event = InteractionEventCreate(
        user_id=None,
        event_type=InteractionEventType.QUERY_SUBMITTED,
        event_data={'query': 'government schemes'},
        language='en'
    )
    
    recorded_event = impact_tracker.record_interaction(event)
    
    assert recorded_event.interaction_id is not None
    assert recorded_event.user_id is None, "Anonymous events should have no user_id"
    assert recorded_event.event_type == 'query_submitted'
    assert recorded_event.event_data['query'] == 'government schemes'
    assert recorded_event.timestamp is not None


def test_event_recording_minimal_data(test_db):
    """
    Test event recording with minimal data (only required fields).
    
    This is an edge case test.
    """
    impact_tracker = ImpactTracker(test_db)
    
    # Create event with only required field (event_type)
    event = InteractionEventCreate(
        user_id=None,
        event_type=InteractionEventType.VOICE_INTERACTION,
        event_data=None,
        language=None
    )
    
    recorded_event = impact_tracker.record_interaction(event)
    
    assert recorded_event.interaction_id is not None
    assert recorded_event.event_type == 'voice_interaction'
    assert recorded_event.timestamp is not None
    assert recorded_event.user_id is None
    assert recorded_event.event_data is None
    assert recorded_event.language is None


def test_multiple_events_same_user(test_db, test_user):
    """
    Test recording multiple events for the same user.
    
    This verifies that multiple events can be tracked for a single user.
    """
    impact_tracker = ImpactTracker(test_db)
    
    # Record multiple events
    events = [
        InteractionEventCreate(
            user_id=str(test_user.user_id),
            event_type=InteractionEventType.QUERY_SUBMITTED,
            event_data={'query': 'farming schemes'},
            language='hi'
        ),
        InteractionEventCreate(
            user_id=str(test_user.user_id),
            event_type=InteractionEventType.SCHEME_ACCESSED,
            event_data={'scheme_id': str(uuid.uuid4())},
            language='hi'
        ),
        InteractionEventCreate(
            user_id=str(test_user.user_id),
            event_type=InteractionEventType.CROP_ADVICE_REQUESTED,
            event_data={'crop': 'Rice', 'state': 'Punjab'},
            language='pa'
        )
    ]
    
    recorded_events = []
    for event in events:
        recorded = impact_tracker.record_interaction(event)
        recorded_events.append(recorded)
    
    # Verify all events were recorded
    assert len(recorded_events) == 3
    for recorded in recorded_events:
        assert recorded.interaction_id is not None
        assert str(recorded.user_id) == str(test_user.user_id)
        assert recorded.timestamp is not None
    
    # Verify events have different IDs
    event_ids = [str(e.interaction_id) for e in recorded_events]
    assert len(set(event_ids)) == 3, "Each event should have a unique ID"


def test_event_recording_all_event_types(test_db, test_user):
    """
    Test recording events for all supported event types.
    
    This ensures all event types can be recorded successfully.
    """
    impact_tracker = ImpactTracker(test_db)
    
    # Test each event type
    for event_type in InteractionEventType:
        event = InteractionEventCreate(
            user_id=str(test_user.user_id),
            event_type=event_type,
            event_data={'test': 'data'},
            language='en'
        )
        
        recorded_event = impact_tracker.record_interaction(event)
        
        assert recorded_event is not None
        assert recorded_event.event_type == event_type.value
        assert recorded_event.timestamp is not None
