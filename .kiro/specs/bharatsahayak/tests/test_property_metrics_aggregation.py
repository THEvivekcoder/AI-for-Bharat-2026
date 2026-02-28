"""
Property-Based Test: Impact Metrics Aggregation
Feature: bharatsahayak, Property 24: Impact Metrics Aggregation

For any set of recorded interactions, aggregating by region, language, or service category 
should produce counts that sum to the total number of interactions.

Validates: Requirements 9.2
"""
import pytest
import os
from hypothesis import given, settings, strategies as st, HealthCheck, assume
from hypothesis.strategies import composite
from app.database import Base
from app.services.impact_tracker import ImpactTracker
from app.models.impact import InteractionEvent
from app.models.user import User
from app.schemas.impact import InteractionEventCreate, InteractionEventType, MetricFilters
from datetime import datetime, timedelta
import uuid


# Database fixtures are provided by conftest.py


# Strategy for generating valid text without null bytes (PostgreSQL incompatible)
def safe_text_strategy(min_size=1, max_size=50):
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


# Strategy for generating valid event data with region information
@composite
def event_data_with_region_strategy(draw):
    """Generate valid event data dictionary with region information"""
    data = {}
    
    # Always include region information for aggregation testing
    data['state'] = draw(st.sampled_from([
        'Maharashtra', 'Karnataka', 'Tamil Nadu', 'Uttar Pradesh', 
        'Bihar', 'West Bengal', 'Madhya Pradesh', 'Rajasthan'
    ]))
    
    # Optionally add district
    if draw(st.booleans()):
        data['district'] = draw(safe_text_strategy(min_size=3, max_size=30))
    
    # Optionally add other fields
    if draw(st.booleans()):
        data['query'] = draw(safe_text_strategy(min_size=5, max_size=100))
    
    if draw(st.booleans()):
        data['scheme_id'] = str(uuid.uuid4())
    
    return data


# Strategy for generating interaction events with consistent structure
@composite
def interaction_event_with_metadata_strategy(draw):
    """Generate interaction event with metadata for aggregation testing"""
    # Generate language (required for language aggregation)
    language = draw(st.sampled_from(['hi', 'en', 'bn', 'te', 'mr', 'ta', 'gu', 'kn']))
    
    # Generate event type (required for service category aggregation)
    event_type = draw(st.sampled_from(list(InteractionEventType)))
    
    # Generate event data with region
    event_data = draw(event_data_with_region_strategy())
    
    return InteractionEventCreate(
        user_id=None,  # Anonymous for simplicity
        event_type=event_type,
        event_data=event_data,
        language=language
    )


@pytest.fixture(scope="function")
def impact_tracker(test_db):
    """Create ImpactTracker instance with test database"""
    return ImpactTracker(test_db)


@settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(events=st.lists(interaction_event_with_metadata_strategy(), min_size=5, max_size=30))
def test_metrics_aggregation_by_language(events, impact_tracker, test_db):
    """
    Feature: bharatsahayak, Property 24: Impact Metrics Aggregation
    
    For any set of recorded interactions, aggregating by language should produce 
    counts that sum to the total number of interactions.
    
    This property ensures that metrics aggregation is accurate and complete.
    """
    # Record all events
    for event in events:
        impact_tracker.record_interaction(event)
    
    # Get overall metrics (no filters)
    overall_filters = MetricFilters()
    overall_metrics = impact_tracker.get_metrics(overall_filters)
    
    total_interactions = overall_metrics.queries_resolved
    
    # Verify we have interactions
    assume(total_interactions > 0)
    
    # Get language breakdown from overall metrics
    languages_used = overall_metrics.languages_used
    
    # Sum of language counts should equal total interactions
    language_sum = sum(languages_used.values())
    
    assert language_sum == total_interactions, (
        f"Sum of language counts ({language_sum}) should equal total interactions ({total_interactions}). "
        f"Language breakdown: {languages_used}"
    )
    
    # Verify each language filter produces correct count
    for language, expected_count in languages_used.items():
        language_filters = MetricFilters(language=language)
        language_metrics = impact_tracker.get_metrics(language_filters)
        
        assert language_metrics.queries_resolved == expected_count, (
            f"Language filter for '{language}' returned {language_metrics.queries_resolved} "
            f"but expected {expected_count}"
        )


@settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(events=st.lists(interaction_event_with_metadata_strategy(), min_size=5, max_size=30))
def test_metrics_aggregation_by_event_type(events, impact_tracker, test_db):
    """
    Feature: bharatsahayak, Property 24: Impact Metrics Aggregation
    
    For any set of recorded interactions, aggregating by event type should produce 
    counts that sum to the total number of interactions.
    """
    # Record all events
    for event in events:
        impact_tracker.record_interaction(event)
    
    # Get overall metrics
    overall_filters = MetricFilters()
    overall_metrics = impact_tracker.get_metrics(overall_filters)
    
    total_interactions = overall_metrics.queries_resolved
    
    # Verify we have interactions
    assume(total_interactions > 0)
    
    # Get event type breakdown
    events_by_type = overall_metrics.events_by_type
    
    # Sum of event type counts should equal total interactions
    event_type_sum = sum(events_by_type.values())
    
    assert event_type_sum == total_interactions, (
        f"Sum of event type counts ({event_type_sum}) should equal total interactions ({total_interactions}). "
        f"Event type breakdown: {events_by_type}"
    )
    
    # Verify each event type filter produces correct count
    for event_type, expected_count in events_by_type.items():
        event_type_filters = MetricFilters(event_type=event_type)
        event_type_metrics = impact_tracker.get_metrics(event_type_filters)
        
        assert event_type_metrics.queries_resolved == expected_count, (
            f"Event type filter for '{event_type}' returned {event_type_metrics.queries_resolved} "
            f"but expected {expected_count}"
        )


@settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(events=st.lists(interaction_event_with_metadata_strategy(), min_size=5, max_size=30))
def test_metrics_aggregation_by_region(events, impact_tracker, test_db):
    """
    Feature: bharatsahayak, Property 24: Impact Metrics Aggregation
    
    For any set of recorded interactions, aggregating by region should produce 
    counts that sum to the total number of interactions.
    """
    # Record all events
    for event in events:
        impact_tracker.record_interaction(event)
    
    # Get overall metrics
    overall_filters = MetricFilters()
    overall_metrics = impact_tracker.get_metrics(overall_filters)
    
    total_interactions = overall_metrics.queries_resolved
    
    # Verify we have interactions
    assume(total_interactions > 0)
    
    # Get all unique regions from recorded events
    recorded_events = test_db.query(InteractionEvent).all()
    regions = set()
    for event in recorded_events:
        if event.event_data and 'state' in event.event_data:
            regions.add(event.event_data['state'])
    
    # Aggregate counts by region manually
    region_counts = {}
    for region in regions:
        region_filters = MetricFilters(region=region)
        region_metrics = impact_tracker.get_metrics(region_filters)
        region_counts[region] = region_metrics.queries_resolved
    
    # Sum of region counts should equal total interactions
    region_sum = sum(region_counts.values())
    
    assert region_sum == total_interactions, (
        f"Sum of region counts ({region_sum}) should equal total interactions ({total_interactions}). "
        f"Region breakdown: {region_counts}"
    )


@settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(events=st.lists(interaction_event_with_metadata_strategy(), min_size=5, max_size=30))
def test_metrics_aggregation_by_service_category(events, impact_tracker, test_db):
    """
    Feature: bharatsahayak, Property 24: Impact Metrics Aggregation
    
    For any set of recorded interactions, aggregating by service category should produce 
    counts that sum to the total number of interactions (for categorized events).
    """
    # Record all events
    for event in events:
        impact_tracker.record_interaction(event)
    
    # Get overall metrics
    overall_filters = MetricFilters()
    overall_metrics = impact_tracker.get_metrics(overall_filters)
    
    total_interactions = overall_metrics.queries_resolved
    
    # Verify we have interactions
    assume(total_interactions > 0)
    
    # Define service categories and their event types
    service_categories = {
        'schemes': ['scheme_accessed'],
        'farmer': ['crop_advice_requested', 'fertilizer_advice_requested', 'market_price_checked'],
        'skills': ['skill_program_viewed', 'job_discovered'],
        'health': ['health_check_performed', 'facility_located']
    }
    
    # Aggregate counts by service category
    category_counts = {}
    for category in service_categories.keys():
        category_filters = MetricFilters(service_category=category)
        category_metrics = impact_tracker.get_metrics(category_filters)
        category_counts[category] = category_metrics.queries_resolved
    
    # Count events that belong to a service category
    categorized_event_types = set()
    for event_types in service_categories.values():
        categorized_event_types.update(event_types)
    
    # Count how many events are categorized
    categorized_count = sum(
        count for event_type, count in overall_metrics.events_by_type.items()
        if event_type in categorized_event_types
    )
    
    # Sum of category counts should equal categorized events
    category_sum = sum(category_counts.values())
    
    assert category_sum == categorized_count, (
        f"Sum of service category counts ({category_sum}) should equal categorized events ({categorized_count}). "
        f"Category breakdown: {category_counts}"
    )


def test_metrics_aggregation_specific_example(impact_tracker, test_db):
    """
    Specific example test: Record known events and verify aggregation.
    
    This complements the property-based tests with a concrete example.
    """
    # Create specific events with known distribution
    events = [
        # Hindi events in Maharashtra
        InteractionEventCreate(
            event_type=InteractionEventType.SCHEME_ACCESSED,
            event_data={'state': 'Maharashtra', 'scheme_id': str(uuid.uuid4())},
            language='hi'
        ),
        InteractionEventCreate(
            event_type=InteractionEventType.SCHEME_ACCESSED,
            event_data={'state': 'Maharashtra', 'scheme_id': str(uuid.uuid4())},
            language='hi'
        ),
        # English events in Karnataka
        InteractionEventCreate(
            event_type=InteractionEventType.CROP_ADVICE_REQUESTED,
            event_data={'state': 'Karnataka', 'crop': 'Rice'},
            language='en'
        ),
        InteractionEventCreate(
            event_type=InteractionEventType.JOB_DISCOVERED,
            event_data={'state': 'Karnataka', 'job_id': str(uuid.uuid4())},
            language='en'
        ),
        # Tamil events in Tamil Nadu
        InteractionEventCreate(
            event_type=InteractionEventType.HEALTH_CHECK_PERFORMED,
            event_data={'state': 'Tamil Nadu', 'symptoms': ['fever']},
            language='ta'
        ),
    ]
    
    # Record all events
    for event in events:
        impact_tracker.record_interaction(event)
    
    # Get overall metrics
    overall_metrics = impact_tracker.get_metrics(MetricFilters())
    
    # Verify total count
    assert overall_metrics.queries_resolved == 5
    
    # Verify language aggregation
    assert overall_metrics.languages_used['hi'] == 2
    assert overall_metrics.languages_used['en'] == 2
    assert overall_metrics.languages_used['ta'] == 1
    assert sum(overall_metrics.languages_used.values()) == 5
    
    # Verify event type aggregation
    assert overall_metrics.events_by_type['scheme_accessed'] == 2
    assert overall_metrics.events_by_type['crop_advice_requested'] == 1
    assert overall_metrics.events_by_type['job_discovered'] == 1
    assert overall_metrics.events_by_type['health_check_performed'] == 1
    assert sum(overall_metrics.events_by_type.values()) == 5
    
    # Verify region aggregation
    maharashtra_metrics = impact_tracker.get_metrics(MetricFilters(region='Maharashtra'))
    assert maharashtra_metrics.queries_resolved == 2
    
    karnataka_metrics = impact_tracker.get_metrics(MetricFilters(region='Karnataka'))
    assert karnataka_metrics.queries_resolved == 2
    
    tamil_nadu_metrics = impact_tracker.get_metrics(MetricFilters(region='Tamil Nadu'))
    assert tamil_nadu_metrics.queries_resolved == 1
    
    # Sum of regional counts equals total
    assert (maharashtra_metrics.queries_resolved + 
            karnataka_metrics.queries_resolved + 
            tamil_nadu_metrics.queries_resolved) == 5


def test_metrics_aggregation_empty_set(impact_tracker, test_db):
    """
    Edge case: Aggregation with no events should return zero counts.
    """
    # Get metrics with no events recorded
    metrics = impact_tracker.get_metrics(MetricFilters())
    
    assert metrics.queries_resolved == 0
    assert metrics.users_served == 0
    assert metrics.schemes_accessed == 0
    assert len(metrics.languages_used) == 0
    assert len(metrics.events_by_type) == 0
    assert sum(metrics.languages_used.values()) == 0
    assert sum(metrics.events_by_type.values()) == 0


def test_metrics_aggregation_date_range(impact_tracker, test_db):
    """
    Test that date range filtering maintains aggregation consistency.
    """
    # Record events at different times
    now = datetime.utcnow()
    
    # Event 1: 5 days ago
    event1 = InteractionEventCreate(
        event_type=InteractionEventType.SCHEME_ACCESSED,
        event_data={'state': 'Maharashtra'},
        language='hi'
    )
    recorded1 = impact_tracker.record_interaction(event1)
    # Manually update timestamp
    test_db.query(InteractionEvent).filter(
        InteractionEvent.interaction_id == recorded1.interaction_id
    ).update({'timestamp': now - timedelta(days=5)}, synchronize_session=False)
    test_db.commit()
    
    # Event 2: 2 days ago
    event2 = InteractionEventCreate(
        event_type=InteractionEventType.JOB_DISCOVERED,
        event_data={'state': 'Karnataka'},
        language='en'
    )
    recorded2 = impact_tracker.record_interaction(event2)
    test_db.query(InteractionEvent).filter(
        InteractionEvent.interaction_id == recorded2.interaction_id
    ).update({'timestamp': now - timedelta(days=2)}, synchronize_session=False)
    test_db.commit()
    
    # Event 3: Today
    event3 = InteractionEventCreate(
        event_type=InteractionEventType.HEALTH_CHECK_PERFORMED,
        event_data={'state': 'Tamil Nadu'},
        language='ta'
    )
    impact_tracker.record_interaction(event3)
    
    # Get metrics for last 3 days (should include events 2 and 3)
    # Add a small buffer to end_date to ensure we capture today's event
    filters = MetricFilters(
        start_date=now - timedelta(days=3),
        end_date=now + timedelta(hours=1)
    )
    metrics = impact_tracker.get_metrics(filters)
    
    # Should have 2 events in this range
    assert metrics.queries_resolved == 2, (
        f"Expected 2 events in date range, got {metrics.queries_resolved}. "
        f"Events by type: {metrics.events_by_type}"
    )
    
    # Language aggregation should sum to 2
    assert sum(metrics.languages_used.values()) == 2
    assert metrics.languages_used.get('en', 0) == 1
    assert metrics.languages_used.get('ta', 0) == 1
    
    # Event type aggregation should sum to 2
    assert sum(metrics.events_by_type.values()) == 2


def test_metrics_aggregation_combined_filters(impact_tracker, test_db):
    """
    Test that combining filters maintains aggregation consistency.
    """
    # Record events with various attributes
    events = [
        InteractionEventCreate(
            event_type=InteractionEventType.SCHEME_ACCESSED,
            event_data={'state': 'Maharashtra'},
            language='hi'
        ),
        InteractionEventCreate(
            event_type=InteractionEventType.SCHEME_ACCESSED,
            event_data={'state': 'Maharashtra'},
            language='hi'
        ),
        InteractionEventCreate(
            event_type=InteractionEventType.SCHEME_ACCESSED,
            event_data={'state': 'Karnataka'},
            language='hi'
        ),
        InteractionEventCreate(
            event_type=InteractionEventType.JOB_DISCOVERED,
            event_data={'state': 'Maharashtra'},
            language='en'
        ),
    ]
    
    for event in events:
        impact_tracker.record_interaction(event)
    
    # Filter by language='hi' and region='Maharashtra'
    filters = MetricFilters(language='hi', region='Maharashtra')
    metrics = impact_tracker.get_metrics(filters)
    
    # Should have 2 events matching both filters
    assert metrics.queries_resolved == 2
    
    # All events should be in Hindi
    assert sum(metrics.languages_used.values()) == 2
    assert metrics.languages_used.get('hi', 0) == 2
    
    # All events should be scheme_accessed
    assert sum(metrics.events_by_type.values()) == 2
    assert metrics.events_by_type.get('scheme_accessed', 0) == 2
