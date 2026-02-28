"""
Property-Based Test: Analytics Data Anonymization
Feature: bharatsahayak, Property 25: Analytics Data Anonymization

For any analytics query result, the returned data should not contain personally 
identifiable information (phone numbers, exact locations, names).

Validates: Requirements 9.4
"""
import pytest
import os
import re
from hypothesis import given, settings, strategies as st, HealthCheck
from hypothesis.strategies import composite
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.services.impact_tracker import ImpactTracker
from app.models.impact import InteractionEvent, OutcomeEvent
from app.models.user import User, UserProfile
from app.models.location import Location
from app.schemas.impact import (
    InteractionEventCreate, 
    OutcomeEventCreate,
    MetricFilters,
    InteractionEventType,
    OutcomeEventType,
    ReportType,
    DateRange
)
from datetime import datetime, timedelta
import uuid
import json


# Use test database URL from environment or default
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://bharatsahayak:password@localhost:5432/bharatsahayak")


# PII detection patterns
PHONE_NUMBER_PATTERN = re.compile(r'\+?\d{10,15}')  # Phone numbers
COORDINATE_PATTERN = re.compile(r'\d+\.\d{6,}')  # Precise coordinates (lat/long with 6+ decimals)
EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')  # Email addresses


def contains_pii(data: any) -> tuple[bool, str]:
    """
    Check if data contains PII (Personally Identifiable Information)
    
    Returns: (has_pii, pii_type) where pii_type describes what PII was found
    """
    if data is None:
        return False, ""
    
    # Convert data to string for pattern matching
    data_str = json.dumps(data) if isinstance(data, (dict, list)) else str(data)
    
    # Check for phone numbers
    if PHONE_NUMBER_PATTERN.search(data_str):
        return True, "phone_number"
    
    # Check for precise coordinates (latitude/longitude with high precision)
    # Note: We allow state/district names, but not precise GPS coordinates
    if COORDINATE_PATTERN.search(data_str):
        # Check if it's actually a coordinate (not just a decimal number)
        matches = COORDINATE_PATTERN.findall(data_str)
        for match in matches:
            # Coordinates typically have 6+ decimal places
            if len(match.split('.')[1]) >= 6:
                return True, "precise_coordinates"
    
    # Check for email addresses
    if EMAIL_PATTERN.search(data_str):
        return True, "email_address"
    
    # Check for common PII field names in dictionaries
    if isinstance(data, dict):
        pii_fields = ['phone_number', 'phone', 'email', 'full_name', 'name', 
                      'address', 'latitude', 'longitude', 'lat', 'lon', 'gps']
        for field in pii_fields:
            if field in data:
                # Allow None values or empty strings
                if data[field] is not None and data[field] != "":
                    return True, f"pii_field_{field}"
    
    return False, ""


def check_metrics_for_pii(metrics) -> tuple[bool, str, str]:
    """
    Check ImpactMetrics object for PII
    
    Returns: (has_pii, location, pii_type)
    """
    # Check aggregated counts (should be fine)
    # These are just numbers, no PII
    
    # Check languages_used dictionary
    has_pii, pii_type = contains_pii(metrics.languages_used)
    if has_pii:
        return True, "languages_used", pii_type
    
    # Check events_by_type dictionary
    has_pii, pii_type = contains_pii(metrics.events_by_type)
    if has_pii:
        return True, "events_by_type", pii_type
    
    # Check outcomes_by_type dictionary
    has_pii, pii_type = contains_pii(metrics.outcomes_by_type)
    if has_pii:
        return True, "outcomes_by_type", pii_type
    
    return False, "", ""


def check_report_for_pii(report) -> tuple[bool, str, str]:
    """
    Check ImpactReport object for PII
    
    Returns: (has_pii, location, pii_type)
    """
    # Check metrics
    has_pii, location, pii_type = check_metrics_for_pii(report.metrics)
    if has_pii:
        return True, f"metrics.{location}", pii_type
    
    # Check regional breakdown
    has_pii, pii_type = contains_pii(report.regional_breakdown)
    if has_pii:
        return True, "regional_breakdown", pii_type
    
    # Check language breakdown
    has_pii, pii_type = contains_pii(report.language_breakdown)
    if has_pii:
        return True, "language_breakdown", pii_type
    
    # Check service breakdown
    has_pii, pii_type = contains_pii(report.service_breakdown)
    if has_pii:
        return True, "service_breakdown", pii_type
    
    return False, "", ""


# Strategy for generating safe text
def safe_text_strategy(min_size=1, max_size=200):
    """Generate text that is safe for PostgreSQL"""
    return st.text(
        min_size=min_size,
        max_size=max_size,
        alphabet=st.characters(
            min_codepoint=32,
            max_codepoint=126,
            blacklist_categories=('Cs',)
        )
    )


# Strategy for generating event data that might contain PII
@composite
def event_data_with_potential_pii(draw):
    """Generate event data that might accidentally contain PII"""
    data = {}
    
    # Add safe fields
    if draw(st.booleans()):
        data['query'] = draw(safe_text_strategy(min_size=1, max_size=100))
    
    if draw(st.booleans()):
        data['scheme_id'] = str(uuid.uuid4())
    
    # Add region info (should be allowed - state/district level)
    if draw(st.booleans()):
        data['state'] = draw(st.sampled_from([
            'Maharashtra', 'Karnataka', 'Tamil Nadu', 'Uttar Pradesh'
        ]))
    
    if draw(st.booleans()):
        data['district'] = draw(st.sampled_from([
            'Pune', 'Mumbai', 'Bangalore', 'Chennai'
        ]))
    
    # Potentially add PII (this should NOT appear in analytics output)
    # We add it to test that the system filters it out
    if draw(st.booleans()):
        # Add a phone number to event_data (should be filtered in analytics)
        data['contact_phone'] = f"+91{draw(st.integers(min_value=1000000000, max_value=9999999999))}"
    
    return data if data else None


@composite
def metric_filters_strategy(draw):
    """Generate valid metric filters"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=draw(st.integers(min_value=1, max_value=90)))
    
    return MetricFilters(
        start_date=start_date,
        end_date=end_date,
        region=draw(st.one_of(
            st.none(),
            st.sampled_from(['Maharashtra', 'Karnataka', 'Tamil Nadu', 'Uttar Pradesh'])
        )),
        language=draw(st.one_of(
            st.none(),
            st.sampled_from(['hi', 'en', 'bn', 'te', 'mr'])
        )),
        event_type=draw(st.one_of(
            st.none(),
            st.sampled_from([e.value for e in InteractionEventType])
        )),
        service_category=draw(st.one_of(
            st.none(),
            st.sampled_from(['schemes', 'farmer', 'skills', 'health'])
        ))
    )


@pytest.fixture(scope="module")
def test_engine():
    """Create test database engine"""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def test_db(test_engine):
    """Create a test database session for each test"""
    TestingSessionLocal = sessionmaker(bind=test_engine)
    db = TestingSessionLocal()
    
    yield db
    
    db.rollback()
    # Clean up test data
    db.query(OutcomeEvent).delete()
    db.query(InteractionEvent).delete()
    db.query(UserProfile).delete()
    db.query(User).delete()
    db.query(Location).delete()
    db.commit()
    db.close()


@pytest.fixture(scope="function")
def impact_tracker(test_db):
    """Create ImpactTracker instance with test database"""
    return ImpactTracker(test_db)


@pytest.fixture(scope="function")
def test_users_with_pii(test_db):
    """Create test users with PII data"""
    users = []
    
    for i in range(5):
        # Create location with PII (precise coordinates)
        location = Location(
            id=uuid.uuid4(),
            state='Maharashtra',
            district='Pune',
            pincode='411001',
            latitude=18.520430 + (i * 0.001),  # Precise coordinates
            longitude=73.856743 + (i * 0.001)
        )
        test_db.add(location)
        test_db.flush()
        
        # Create user with PII (phone number)
        phone_number = f"+9198765{43210 + i}"
        user = User(
            user_id=uuid.uuid4(),
            phone_number=phone_number,
            language='hi'
        )
        test_db.add(user)
        test_db.flush()
        
        # Create profile with PII
        profile = UserProfile(
            profile_id=uuid.uuid4(),
            user_id=user.user_id,
            location_id=location.id,
            age=25 + i,
            gender='male' if i % 2 == 0 else 'female',
            education_level='graduate',
            occupation='farmer'
        )
        test_db.add(profile)
        
        users.append(user)
    
    test_db.commit()
    return users


@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    filters=metric_filters_strategy(),
    event_data=event_data_with_potential_pii()
)
def test_metrics_anonymization(filters, event_data, test_db, test_users_with_pii):
    """
    Feature: bharatsahayak, Property 25: Analytics Data Anonymization
    
    For any analytics query result, the returned data should not contain personally 
    identifiable information (phone numbers, exact locations, names).
    
    This property ensures user privacy is protected in all analytics outputs.
    """
    impact_tracker = ImpactTracker(test_db)
    
    # Record some interaction events with PII in event_data
    for user in test_users_with_pii[:3]:  # Use subset of users
        event = InteractionEventCreate(
            user_id=str(user.user_id),
            event_type=InteractionEventType.QUERY_SUBMITTED,
            event_data=event_data,
            language='hi'
        )
        impact_tracker.record_interaction(event)
    
    # Get metrics with filters
    metrics = impact_tracker.get_metrics(filters)
    
    # Assert metrics object exists
    assert metrics is not None, "Metrics should be returned"
    
    # Check for PII in metrics
    has_pii, location, pii_type = check_metrics_for_pii(metrics)
    
    assert not has_pii, (
        f"Analytics metrics contain PII at '{location}': {pii_type}. "
        f"Personal information must be anonymized in analytics data."
    )
    
    # Verify aggregated data is present (anonymized counts are OK)
    assert isinstance(metrics.users_served, int), "User count should be an integer"
    assert isinstance(metrics.queries_resolved, int), "Query count should be an integer"
    assert isinstance(metrics.languages_used, dict), "Language breakdown should be a dictionary"
    assert isinstance(metrics.events_by_type, dict), "Event type breakdown should be a dictionary"
    
    # Verify no user_id appears in the metrics output
    metrics_dict = metrics.model_dump()
    metrics_str = json.dumps(metrics_dict, default=str)
    
    # Check that no user IDs from our test users appear in the output
    for user in test_users_with_pii:
        assert str(user.user_id) not in metrics_str, (
            f"User ID {user.user_id} should not appear in anonymized metrics"
        )
        assert user.phone_number not in metrics_str, (
            f"Phone number {user.phone_number} should not appear in anonymized metrics"
        )


@settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(event_data=event_data_with_potential_pii())
def test_report_anonymization(event_data, test_db, test_users_with_pii):
    """
    Test that generated reports do not contain PII.
    
    This tests the generate_report method for anonymization.
    """
    impact_tracker = ImpactTracker(test_db)
    
    # Record events and outcomes with potential PII
    for user in test_users_with_pii:
        # Record interaction
        event = InteractionEventCreate(
            user_id=str(user.user_id),
            event_type=InteractionEventType.SCHEME_ACCESSED,
            event_data=event_data,
            language='hi'
        )
        impact_tracker.record_interaction(event)
        
        # Record outcome
        outcome = OutcomeEventCreate(
            user_id=str(user.user_id),
            outcome_type=OutcomeEventType.SCHEME_APPLIED,
            outcome_data={'scheme_id': str(uuid.uuid4())}
        )
        impact_tracker.record_outcome(outcome)
    
    # Generate report
    date_range = DateRange(
        start_date=datetime.utcnow() - timedelta(days=7),
        end_date=datetime.utcnow()
    )
    report = impact_tracker.generate_report(ReportType.WEEKLY, date_range)
    
    # Assert report exists
    assert report is not None, "Report should be generated"
    
    # Check for PII in report
    has_pii, location, pii_type = check_report_for_pii(report)
    
    assert not has_pii, (
        f"Analytics report contains PII at '{location}': {pii_type}. "
        f"Personal information must be anonymized in all reports."
    )
    
    # Verify report structure is intact
    assert report.metrics is not None, "Report should contain metrics"
    assert report.regional_breakdown is not None, "Report should contain regional breakdown"
    assert report.language_breakdown is not None, "Report should contain language breakdown"
    
    # Verify no user IDs or phone numbers appear in report
    report_dict = report.model_dump()
    report_str = json.dumps(report_dict, default=str)
    
    for user in test_users_with_pii:
        assert str(user.user_id) not in report_str, (
            f"User ID should not appear in anonymized report"
        )
        assert user.phone_number not in report_str, (
            f"Phone number should not appear in anonymized report"
        )


def test_anonymization_with_specific_pii(test_db, test_users_with_pii):
    """
    Test anonymization with specific PII examples.
    
    This is a concrete example test to complement the property-based test.
    """
    impact_tracker = ImpactTracker(test_db)
    user = test_users_with_pii[0]
    
    # Record event with PII in event_data
    event = InteractionEventCreate(
        user_id=str(user.user_id),
        event_type=InteractionEventType.QUERY_SUBMITTED,
        event_data={
            'query': 'farming schemes',
            'contact_phone': '+919876543210',  # PII
            'email': 'farmer@example.com',  # PII
            'state': 'Maharashtra',  # OK - aggregated level
            'district': 'Pune'  # OK - aggregated level
        },
        language='hi'
    )
    impact_tracker.record_interaction(event)
    
    # Get metrics
    filters = MetricFilters()
    metrics = impact_tracker.get_metrics(filters)
    
    # Verify PII is not in metrics
    metrics_dict = metrics.model_dump()
    # Convert to JSON-serializable format (handle datetime)
    metrics_str = json.dumps(metrics_dict, default=str)
    
    assert '+919876543210' not in metrics_str, "Phone number should not appear in metrics"
    assert 'farmer@example.com' not in metrics_str, "Email should not appear in metrics"
    assert user.phone_number not in metrics_str, "User phone number should not appear in metrics"
    
    # Verify aggregated data is present
    assert metrics.users_served >= 1, "Should count users"
    assert metrics.queries_resolved >= 1, "Should count queries"
    
    # Verify region info is OK (state/district level aggregation is allowed)
    # The metrics themselves don't return event_data, only aggregated counts
    assert isinstance(metrics.events_by_type, dict), "Should have event type breakdown"


def test_anonymization_preserves_aggregated_data(test_db, test_users_with_pii):
    """
    Test that anonymization preserves useful aggregated data.
    
    Anonymization should remove PII but keep aggregated statistics.
    """
    impact_tracker = ImpactTracker(test_db)
    
    # Record events from different regions
    regions = ['Maharashtra', 'Karnataka', 'Tamil Nadu']
    for i, user in enumerate(test_users_with_pii[:3]):
        event = InteractionEventCreate(
            user_id=str(user.user_id),
            event_type=InteractionEventType.SCHEME_ACCESSED,
            event_data={
                'state': regions[i],
                'scheme_id': str(uuid.uuid4())
            },
            language='hi'
        )
        impact_tracker.record_interaction(event)
    
    # Get metrics
    filters = MetricFilters()
    metrics = impact_tracker.get_metrics(filters)
    
    # Verify aggregated data is present
    assert metrics.users_served == 3, "Should count 3 unique users"
    assert metrics.queries_resolved == 3, "Should count 3 queries"
    assert metrics.schemes_accessed == 3, "Should count 3 scheme accesses"
    
    # Verify language breakdown is present
    assert 'hi' in metrics.languages_used, "Should have Hindi language count"
    assert metrics.languages_used['hi'] == 3, "Should count 3 Hindi interactions"
    
    # Verify event type breakdown is present
    assert 'scheme_accessed' in metrics.events_by_type, "Should have scheme_accessed count"
    assert metrics.events_by_type['scheme_accessed'] == 3, "Should count 3 scheme accesses"


def test_anonymization_with_no_user_id(test_db):
    """
    Test anonymization for anonymous events (no user_id).
    
    Anonymous events should also be included in analytics without PII.
    """
    impact_tracker = ImpactTracker(test_db)
    
    # Record anonymous event
    event = InteractionEventCreate(
        user_id=None,  # Anonymous
        event_type=InteractionEventType.QUERY_SUBMITTED,
        event_data={'query': 'government schemes'},
        language='en'
    )
    impact_tracker.record_interaction(event)
    
    # Get metrics
    filters = MetricFilters()
    metrics = impact_tracker.get_metrics(filters)
    
    # Verify metrics are generated
    assert metrics.queries_resolved >= 1, "Should count anonymous queries"
    
    # Verify no PII
    has_pii, location, pii_type = check_metrics_for_pii(metrics)
    assert not has_pii, f"Anonymous event metrics should not contain PII: {pii_type}"


def test_regional_aggregation_allowed(test_db, test_users_with_pii):
    """
    Test that regional aggregation (state/district level) is allowed.
    
    Anonymization should allow state/district level data but not user-level PII.
    """
    impact_tracker = ImpactTracker(test_db)
    
    # Record events with regional data
    for user in test_users_with_pii[:2]:
        event = InteractionEventCreate(
            user_id=str(user.user_id),
            event_type=InteractionEventType.CROP_ADVICE_REQUESTED,
            event_data={
                'state': 'Maharashtra',
                'district': 'Pune',
                'crop': 'Rice'
            },
            language='hi'
        )
        impact_tracker.record_interaction(event)
    
    # Generate report
    date_range = DateRange(
        start_date=datetime.utcnow() - timedelta(days=1),
        end_date=datetime.utcnow()
    )
    report = impact_tracker.generate_report(ReportType.DAILY, date_range)
    
    # Verify regional breakdown exists (this is allowed)
    assert report.regional_breakdown is not None, "Regional breakdown should be present"
    
    # Verify no user-level PII in report
    report_str = json.dumps(report.model_dump(), default=str)
    
    # Check that user IDs don't appear
    for user in test_users_with_pii:
        assert str(user.user_id) not in report_str, (
            f"User ID should not appear in report"
        )
        assert user.phone_number not in report_str, (
            f"Phone number should not appear in report"
        )
    
    # State/district names are OK (aggregated level)
    # The report should contain aggregated regional data
    assert isinstance(report.regional_breakdown, dict), (
        "Regional breakdown should be a dictionary"
    )
