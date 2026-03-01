"""Property-based tests for interaction event recording.

Feature: bharatsahayak, Property 23: Interaction Event Recording
**Validates: Requirements 9.1, 9.3**

This test verifies that all user interactions are recorded with required fields
(user_id, event_type, timestamp, event_data), ensuring complete impact tracking.
"""

import pytest
from hypothesis import given, settings, strategies as st
from datetime import datetime
from unittest.mock import Mock, patch

from src.core.impact_repository import ImpactRepository
from src.models.impact import InteractionEvent, OutcomeEvent


# Custom strategies for generating valid test data
@st.composite
def interaction_event_strategy(draw):
    """Generate valid InteractionEvent instances."""
    # Valid event types
    event_types = [
        "query_submitted",
        "scheme_accessed",
        "scheme_applied",
        "job_discovered",
        "facility_located",
        "voice_interaction",
        "language_used"
    ]
    
    # Generate user_id
    user_id = f"user_{draw(st.integers(min_value=100000, max_value=999999))}"
    
    # Select event type
    event_type = draw(st.sampled_from(event_types))
    
    # Generate event_data based on event type
    event_data = {}
    if event_type == "query_submitted":
        event_data = {
            "query": draw(st.text(min_size=5, max_size=200)),
            "category": draw(st.sampled_from(["agriculture", "health", "education", "employment", "social_welfare"])),
            "response_time_ms": draw(st.integers(min_value=100, max_value=5000))
        }
    elif event_type == "scheme_accessed":
        event_data = {
            "scheme_id": f"scheme_{draw(st.integers(min_value=1000, max_value=9999))}",
            "scheme_name": draw(st.text(min_size=10, max_size=100)),
            "category": draw(st.sampled_from(["agriculture", "health", "education", "employment", "social_welfare"]))
        }
    elif event_type == "scheme_applied":
        event_data = {
            "scheme_id": f"scheme_{draw(st.integers(min_value=1000, max_value=9999))}",
            "application_method": draw(st.sampled_from(["online", "offline", "csc"]))
        }
    elif event_type == "job_discovered":
        event_data = {
            "job_id": f"job_{draw(st.integers(min_value=1000, max_value=9999))}",
            "job_title": draw(st.text(min_size=10, max_size=100)),
            "department": draw(st.text(min_size=5, max_size=50))
        }
    elif event_type == "facility_located":
        event_data = {
            "facility_id": f"facility_{draw(st.integers(min_value=1000, max_value=9999))}",
            "facility_type": draw(st.sampled_from(["PHC", "CHC", "District Hospital"])),
            "distance_km": draw(st.floats(min_value=0.1, max_value=50.0, allow_nan=False, allow_infinity=False))
        }
    elif event_type == "voice_interaction":
        event_data = {
            "duration_seconds": draw(st.integers(min_value=5, max_value=300)),
            "audio_quality": draw(st.sampled_from(["good", "fair", "poor"]))
        }
    elif event_type == "language_used":
        event_data = {
            "language": draw(st.sampled_from(["hi", "en", "bn", "te", "mr", "ta", "gu", "kn"])),
            "interaction_count": draw(st.integers(min_value=1, max_value=100))
        }
    
    # Optional language field
    language = draw(st.none() | st.sampled_from(["hi", "en", "bn", "te", "mr", "ta", "gu", "kn"]))
    
    # Use current timestamp
    timestamp = datetime.utcnow()
    
    return InteractionEvent(
        user_id=user_id,
        event_type=event_type,
        event_data=event_data,
        language=language,
        timestamp=timestamp
    )


@st.composite
def outcome_event_strategy(draw):
    """Generate valid OutcomeEvent instances."""
    # Valid outcome types
    outcome_types = [
        "scheme_applied",
        "job_applied",
        "facility_visited",
        "skill_enrolled",
        "recommendation_followed"
    ]
    
    # Generate user_id
    user_id = f"user_{draw(st.integers(min_value=100000, max_value=999999))}"
    
    # Select outcome type
    outcome_type = draw(st.sampled_from(outcome_types))
    
    # Generate outcome_data based on outcome type
    outcome_data = {}
    if outcome_type == "scheme_applied":
        outcome_data = {
            "scheme_id": f"scheme_{draw(st.integers(min_value=1000, max_value=9999))}",
            "scheme_name": draw(st.text(min_size=10, max_size=100)),
            "application_method": draw(st.sampled_from(["online", "offline", "csc"])),
            "success": draw(st.booleans())
        }
    elif outcome_type == "job_applied":
        outcome_data = {
            "job_id": f"job_{draw(st.integers(min_value=1000, max_value=9999))}",
            "job_title": draw(st.text(min_size=10, max_size=100)),
            "department": draw(st.text(min_size=5, max_size=50))
        }
    elif outcome_type == "facility_visited":
        outcome_data = {
            "facility_id": f"facility_{draw(st.integers(min_value=1000, max_value=9999))}",
            "facility_type": draw(st.sampled_from(["PHC", "CHC", "District Hospital"])),
            "visit_date": datetime.utcnow().isoformat()
        }
    elif outcome_type == "skill_enrolled":
        outcome_data = {
            "program_id": f"program_{draw(st.integers(min_value=1000, max_value=9999))}",
            "program_name": draw(st.text(min_size=10, max_size=100)),
            "duration_weeks": draw(st.integers(min_value=4, max_value=52))
        }
    elif outcome_type == "recommendation_followed":
        outcome_data = {
            "recommendation_type": draw(st.sampled_from(["scheme", "job", "skill", "health"])),
            "item_id": f"item_{draw(st.integers(min_value=1000, max_value=9999))}",
            "action_taken": draw(st.text(min_size=10, max_size=100))
        }
    
    # Use current timestamp
    timestamp = datetime.utcnow()
    
    return OutcomeEvent(
        user_id=user_id,
        outcome_type=outcome_type,
        outcome_data=outcome_data,
        timestamp=timestamp
    )


@settings(max_examples=100, deadline=None)
@given(event=interaction_event_strategy())
def test_interaction_event_recording_required_fields(event):
    """
    Feature: bharatsahayak, Property 23: Interaction Event Recording
    
    For any user interaction, the Impact_Tracker should record an event with
    required fields: user_id, event_type, timestamp, and event_data.
    
    This test verifies:
    1. All required fields are present in recorded events
    2. user_id is non-empty and valid
    3. event_type is one of the valid types
    4. timestamp is a valid datetime
    5. event_data is a dictionary (can be empty but must exist)
    6. Generated event_id is returned and valid
    """
    # Create mock table
    mock_table = Mock()
    
    # Create repository with mocked table
    with patch('boto3.resource') as mock_resource:
        mock_dynamodb = Mock()
        mock_dynamodb.Table.return_value = mock_table
        mock_resource.return_value = mock_dynamodb
        
        with patch('boto3.client'):
            repo = ImpactRepository(table_name="TestInteractions")
            repo.table = mock_table
            
            # Mock the put_item operation
            mock_table.put_item.return_value = {}
            
            # Record the interaction event
            event_id = repo.record_interaction(event)
            
            # Verify event_id was generated
            assert event_id is not None
            assert isinstance(event_id, str)
            assert len(event_id) > 0
            assert event_id.startswith("evt_")
            
            # Verify put_item was called
            assert mock_table.put_item.called
            
            # Get the item that was stored
            call_args = mock_table.put_item.call_args
            stored_item = call_args.kwargs['Item']
            
            # Verify all required fields are present
            assert 'event_id' in stored_item
            assert 'user_id' in stored_item
            assert 'event_type' in stored_item
            assert 'timestamp' in stored_item
            assert 'event_data' in stored_item
            assert 'record_type' in stored_item
            
            # Verify field values
            assert stored_item['user_id'] == event.user_id
            assert len(stored_item['user_id']) > 0
            
            assert stored_item['event_type'] == event.event_type
            assert stored_item['event_type'] in [
                "query_submitted", "scheme_accessed", "scheme_applied",
                "job_discovered", "facility_located", "voice_interaction", "language_used"
            ]
            
            assert stored_item['timestamp'] is not None
            assert isinstance(stored_item['timestamp'], str)  # ISO format
            
            assert stored_item['event_data'] is not None
            assert isinstance(stored_item['event_data'], dict)
            
            assert stored_item['record_type'] == 'interaction'
            
            # Verify optional language field if present
            if event.language:
                assert 'language' in stored_item
                assert stored_item['language'] == event.language


@settings(max_examples=100, deadline=None)
@given(outcome=outcome_event_strategy())
def test_outcome_event_recording_required_fields(outcome):
    """
    Feature: bharatsahayak, Property 23: Interaction Event Recording (Outcomes)
    
    For any successful outcome, the Impact_Tracker should record an event with
    required fields: user_id, outcome_type, timestamp, and outcome_data.
    
    This test verifies outcome events are recorded with all required fields.
    """
    # Create mock table
    mock_table = Mock()
    
    # Create repository with mocked table
    with patch('boto3.resource') as mock_resource:
        mock_dynamodb = Mock()
        mock_dynamodb.Table.return_value = mock_table
        mock_resource.return_value = mock_dynamodb
        
        with patch('boto3.client'):
            repo = ImpactRepository(table_name="TestInteractions")
            repo.table = mock_table
            
            # Mock the put_item operation
            mock_table.put_item.return_value = {}
            
            # Record the outcome event
            outcome_id = repo.record_outcome(outcome)
            
            # Verify outcome_id was generated
            assert outcome_id is not None
            assert isinstance(outcome_id, str)
            assert len(outcome_id) > 0
            assert outcome_id.startswith("out_")
            
            # Verify put_item was called
            assert mock_table.put_item.called
            
            # Get the item that was stored
            call_args = mock_table.put_item.call_args
            stored_item = call_args.kwargs['Item']
            
            # Verify all required fields are present
            assert 'event_id' in stored_item  # Using event_id as partition key
            assert 'user_id' in stored_item
            assert 'outcome_type' in stored_item
            assert 'timestamp' in stored_item
            assert 'outcome_data' in stored_item
            assert 'record_type' in stored_item
            
            # Verify field values
            assert stored_item['user_id'] == outcome.user_id
            assert len(stored_item['user_id']) > 0
            
            assert stored_item['outcome_type'] == outcome.outcome_type
            assert stored_item['outcome_type'] in [
                "scheme_applied", "job_applied", "facility_visited",
                "skill_enrolled", "recommendation_followed"
            ]
            
            assert stored_item['timestamp'] is not None
            assert isinstance(stored_item['timestamp'], str)  # ISO format
            
            assert stored_item['outcome_data'] is not None
            assert isinstance(stored_item['outcome_data'], dict)
            
            assert stored_item['record_type'] == 'outcome'


@settings(max_examples=50, deadline=None)
@given(events=st.lists(interaction_event_strategy(), min_size=1, max_size=10))
def test_multiple_events_recording(events):
    """
    Test that multiple events can be recorded sequentially and each gets a unique ID.
    
    This verifies that the system can handle multiple event recordings and
    generates unique identifiers for each event.
    """
    # Create mock table
    mock_table = Mock()
    
    with patch('boto3.resource') as mock_resource:
        mock_dynamodb = Mock()
        mock_dynamodb.Table.return_value = mock_table
        mock_resource.return_value = mock_dynamodb
        
        with patch('boto3.client'):
            repo = ImpactRepository(table_name="TestInteractions")
            repo.table = mock_table
            
            # Mock the put_item operation
            mock_table.put_item.return_value = {}
            
            # Record all events
            event_ids = []
            for event in events:
                event_id = repo.record_interaction(event)
                event_ids.append(event_id)
            
            # Verify all event IDs are unique
            assert len(event_ids) == len(set(event_ids))
            
            # Verify all event IDs are valid
            for event_id in event_ids:
                assert event_id is not None
                assert isinstance(event_id, str)
                assert event_id.startswith("evt_")
            
            # Verify put_item was called for each event
            assert mock_table.put_item.call_count == len(events)
