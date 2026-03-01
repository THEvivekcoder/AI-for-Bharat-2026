"""Unit tests for impact tracking functionality."""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from botocore.exceptions import ClientError

from src.core.impact_repository import ImpactRepository, DynamoDBRepositoryError
from src.models.impact import InteractionEvent, OutcomeEvent


@pytest.fixture
def mock_table():
    """Create a mock DynamoDB table."""
    return Mock()


@pytest.fixture
def impact_repository(mock_table):
    """Create an ImpactRepository with mocked DynamoDB table."""
    with patch('boto3.resource') as mock_resource:
        mock_dynamodb = Mock()
        mock_dynamodb.Table.return_value = mock_table
        mock_resource.return_value = mock_dynamodb
        
        with patch('boto3.client'):
            repo = ImpactRepository(table_name="TestInteractions")
            repo.table = mock_table
            return repo


@pytest.fixture
def sample_interaction_event():
    """Create a sample interaction event for testing."""
    return InteractionEvent(
        user_id="user_123456",
        event_type="query_submitted",
        event_data={
            "query": "What schemes are available for farmers?",
            "category": "agriculture",
            "response_time_ms": 1250
        },
        language="hi",
        timestamp=datetime.utcnow()
    )


@pytest.fixture
def sample_outcome_event():
    """Create a sample outcome event for testing."""
    return OutcomeEvent(
        user_id="user_123456",
        outcome_type="scheme_applied",
        outcome_data={
            "scheme_id": "PM-KISAN-2024",
            "scheme_name": "Pradhan Mantri Kisan Samman Nidhi",
            "application_method": "online",
            "success": True
        },
        timestamp=datetime.utcnow()
    )


# Test Event Recording

def test_record_interaction_success(impact_repository, mock_table, sample_interaction_event):
    """Test successful interaction event recording."""
    mock_table.put_item.return_value = {}
    
    event_id = impact_repository.record_interaction(sample_interaction_event)
    
    assert event_id is not None
    assert event_id.startswith("evt_")
    mock_table.put_item.assert_called_once()
    
    # Verify the stored item structure
    call_args = mock_table.put_item.call_args
    stored_item = call_args.kwargs['Item']
    
    assert stored_item['user_id'] == "user_123456"
    assert stored_item['event_type'] == "query_submitted"
    assert stored_item['record_type'] == "interaction"
    assert 'timestamp' in stored_item


def test_record_interaction_with_various_event_types(impact_repository, mock_table):
    """Test recording different types of interaction events."""
    mock_table.put_item.return_value = {}
    
    event_types = [
        "query_submitted",
        "scheme_accessed",
        "scheme_applied",
        "job_discovered",
        "facility_located",
        "voice_interaction",
        "language_used"
    ]
    
    for event_type in event_types:
        event = InteractionEvent(
            user_id="user_123456",
            event_type=event_type,
            event_data={"test": "data"},
            timestamp=datetime.utcnow()
        )
        
        event_id = impact_repository.record_interaction(event)
        
        assert event_id is not None
        assert event_id.startswith("evt_")


def test_record_outcome_success(impact_repository, mock_table, sample_outcome_event):
    """Test successful outcome event recording."""
    mock_table.put_item.return_value = {}
    
    outcome_id = impact_repository.record_outcome(sample_outcome_event)
    
    assert outcome_id is not None
    assert outcome_id.startswith("out_")
    mock_table.put_item.assert_called_once()
    
    # Verify the stored item structure
    call_args = mock_table.put_item.call_args
    stored_item = call_args.kwargs['Item']
    
    assert stored_item['user_id'] == "user_123456"
    assert stored_item['outcome_type'] == "scheme_applied"
    assert stored_item['record_type'] == "outcome"
    assert 'timestamp' in stored_item


def test_record_outcome_with_various_outcome_types(impact_repository, mock_table):
    """Test recording different types of outcome events."""
    mock_table.put_item.return_value = {}
    
    outcome_types = [
        "scheme_applied",
        "job_applied",
        "facility_visited",
        "skill_enrolled",
        "recommendation_followed"
    ]
    
    for outcome_type in outcome_types:
        outcome = OutcomeEvent(
            user_id="user_123456",
            outcome_type=outcome_type,
            outcome_data={"test": "data"},
            timestamp=datetime.utcnow()
        )
        
        outcome_id = impact_repository.record_outcome(outcome)
        
        assert outcome_id is not None
        assert outcome_id.startswith("out_")


def test_record_interaction_without_language(impact_repository, mock_table):
    """Test recording interaction event without optional language field."""
    mock_table.put_item.return_value = {}
    
    event = InteractionEvent(
        user_id="user_123456",
        event_type="query_submitted",
        event_data={"query": "test"},
        language=None,
        timestamp=datetime.utcnow()
    )
    
    event_id = impact_repository.record_interaction(event)
    
    assert event_id is not None
    mock_table.put_item.assert_called_once()


def test_record_interaction_with_empty_event_data(impact_repository, mock_table):
    """Test recording interaction event with empty event_data."""
    mock_table.put_item.return_value = {}
    
    event = InteractionEvent(
        user_id="user_123456",
        event_type="query_submitted",
        event_data={},
        timestamp=datetime.utcnow()
    )
    
    event_id = impact_repository.record_interaction(event)
    
    assert event_id is not None
    mock_table.put_item.assert_called_once()


# Test Analytics Aggregation

def test_get_analytics_data_basic(impact_repository, mock_table):
    """Test basic analytics data aggregation."""
    mock_table.scan.return_value = {
        'Items': [
            {
                'event_id': 'evt_1',
                'user_id': 'user_1',
                'event_type': 'query_submitted',
                'event_data': {'category': 'agriculture'},
                'language': 'hi',
                'timestamp': datetime.utcnow().isoformat(),
                'record_type': 'interaction'
            },
            {
                'event_id': 'evt_2',
                'user_id': 'user_2',
                'event_type': 'scheme_accessed',
                'event_data': {'category': 'health'},
                'language': 'en',
                'timestamp': datetime.utcnow().isoformat(),
                'record_type': 'interaction'
            },
            {
                'event_id': 'out_1',
                'user_id': 'user_1',
                'outcome_type': 'scheme_applied',
                'outcome_data': {'scheme_id': 'SCHEME-1'},
                'timestamp': datetime.utcnow().isoformat(),
                'record_type': 'outcome'
            }
        ]
    }
    
    metrics = impact_repository.get_analytics_data()
    
    assert metrics['total_users'] == 2
    assert metrics['total_queries'] == 1
    assert metrics['schemes_accessed'] == 1
    assert metrics['schemes_applied'] == 1
    assert 'by_category' in metrics
    assert 'by_language' in metrics


def test_get_analytics_data_with_date_filters(impact_repository, mock_table):
    """Test analytics data with date range filters."""
    mock_table.scan.return_value = {'Items': []}
    
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 1, 31)
    
    metrics = impact_repository.get_analytics_data(
        start_date=start_date,
        end_date=end_date
    )
    
    # Verify scan was called with date filters
    call_kwargs = mock_table.scan.call_args.kwargs
    assert 'FilterExpression' in call_kwargs
    assert 'ExpressionAttributeValues' in call_kwargs


def test_get_analytics_data_with_category_filter(impact_repository, mock_table):
    """Test analytics data with category filter."""
    mock_table.scan.return_value = {
        'Items': [
            {
                'event_id': 'evt_1',
                'user_id': 'user_1',
                'event_type': 'query_submitted',
                'event_data': {'category': 'agriculture'},
                'language': 'hi',
                'timestamp': datetime.utcnow().isoformat(),
                'record_type': 'interaction'
            },
            {
                'event_id': 'evt_2',
                'user_id': 'user_2',
                'event_type': 'query_submitted',
                'event_data': {'category': 'health'},
                'language': 'en',
                'timestamp': datetime.utcnow().isoformat(),
                'record_type': 'interaction'
            }
        ]
    }
    
    metrics = impact_repository.get_analytics_data(category='agriculture')
    
    # Only agriculture events should be counted
    assert metrics['total_queries'] == 1
    assert 'agriculture' in metrics['by_category']


def test_analytics_success_rate_calculation(impact_repository, mock_table):
    """Test success rate calculation in analytics."""
    mock_table.scan.return_value = {
        'Items': [
            {
                'event_id': 'evt_1',
                'user_id': 'user_1',
                'event_type': 'scheme_accessed',
                'event_data': {},
                'timestamp': datetime.utcnow().isoformat(),
                'record_type': 'interaction'
            },
            {
                'event_id': 'evt_2',
                'user_id': 'user_2',
                'event_type': 'scheme_accessed',
                'event_data': {},
                'timestamp': datetime.utcnow().isoformat(),
                'record_type': 'interaction'
            },
            {
                'event_id': 'evt_3',
                'user_id': 'user_3',
                'event_type': 'scheme_accessed',
                'event_data': {},
                'timestamp': datetime.utcnow().isoformat(),
                'record_type': 'interaction'
            },
            {
                'event_id': 'evt_4',
                'user_id': 'user_4',
                'event_type': 'scheme_accessed',
                'event_data': {},
                'timestamp': datetime.utcnow().isoformat(),
                'record_type': 'interaction'
            },
            {
                'event_id': 'out_1',
                'user_id': 'user_1',
                'outcome_type': 'scheme_applied',
                'outcome_data': {},
                'timestamp': datetime.utcnow().isoformat(),
                'record_type': 'outcome'
            }
        ]
    }
    
    metrics = impact_repository.get_analytics_data()
    
    # 1 applied out of 4 accessed = 25% success rate
    assert metrics['schemes_accessed'] == 4
    assert metrics['schemes_applied'] == 1
    assert metrics['success_rate'] == 25.0


def test_analytics_category_aggregation(impact_repository, mock_table):
    """Test aggregation by category."""
    mock_table.scan.return_value = {
        'Items': [
            {
                'event_id': 'evt_1',
                'user_id': 'user_1',
                'event_type': 'query_submitted',
                'event_data': {'category': 'agriculture'},
                'timestamp': datetime.utcnow().isoformat(),
                'record_type': 'interaction'
            },
            {
                'event_id': 'evt_2',
                'user_id': 'user_2',
                'event_type': 'query_submitted',
                'event_data': {'category': 'agriculture'},
                'timestamp': datetime.utcnow().isoformat(),
                'record_type': 'interaction'
            },
            {
                'event_id': 'evt_3',
                'user_id': 'user_3',
                'event_type': 'query_submitted',
                'event_data': {'category': 'health'},
                'timestamp': datetime.utcnow().isoformat(),
                'record_type': 'interaction'
            }
        ]
    }
    
    metrics = impact_repository.get_analytics_data()
    
    assert metrics['by_category']['agriculture'] == 2
    assert metrics['by_category']['health'] == 1


def test_analytics_language_aggregation(impact_repository, mock_table):
    """Test aggregation by language."""
    mock_table.scan.return_value = {
        'Items': [
            {
                'event_id': 'evt_1',
                'user_id': 'user_1',
                'event_type': 'query_submitted',
                'event_data': {},
                'language': 'hi',
                'timestamp': datetime.utcnow().isoformat(),
                'record_type': 'interaction'
            },
            {
                'event_id': 'evt_2',
                'user_id': 'user_2',
                'event_type': 'query_submitted',
                'event_data': {},
                'language': 'hi',
                'timestamp': datetime.utcnow().isoformat(),
                'record_type': 'interaction'
            },
            {
                'event_id': 'evt_3',
                'user_id': 'user_3',
                'event_type': 'query_submitted',
                'event_data': {},
                'language': 'en',
                'timestamp': datetime.utcnow().isoformat(),
                'record_type': 'interaction'
            }
        ]
    }
    
    metrics = impact_repository.get_analytics_data()
    
    assert metrics['by_language']['hi'] == 2
    assert metrics['by_language']['en'] == 1


# Test Anonymization

def test_analytics_anonymizes_user_data(impact_repository, mock_table):
    """Test that analytics results don't contain individual user IDs."""
    mock_table.scan.return_value = {
        'Items': [
            {
                'event_id': 'evt_1',
                'user_id': 'user_123456',
                'event_type': 'query_submitted',
                'event_data': {},
                'timestamp': datetime.utcnow().isoformat(),
                'record_type': 'interaction'
            }
        ]
    }
    
    metrics = impact_repository.get_analytics_data()
    
    # Verify only count is present, not individual user_ids
    assert 'total_users' in metrics
    assert isinstance(metrics['total_users'], int)
    
    # Verify user_id is not in the metrics
    import json
    metrics_json = json.dumps(metrics)
    assert 'user_123456' not in metrics_json


def test_analytics_with_no_events(impact_repository, mock_table):
    """Test analytics with no events."""
    mock_table.scan.return_value = {'Items': []}
    
    metrics = impact_repository.get_analytics_data()
    
    assert metrics['total_users'] == 0
    assert metrics['total_queries'] == 0
    assert metrics['schemes_accessed'] == 0
    assert metrics['schemes_applied'] == 0
    assert metrics['success_rate'] == 0.0


# Test Error Handling

def test_record_interaction_network_error(impact_repository, mock_table, sample_interaction_event):
    """Test handling of network errors during interaction recording."""
    mock_table.put_item.side_effect = ClientError(
        {'Error': {'Code': 'RequestTimeout', 'Message': 'Request timed out'}},
        'PutItem'
    )
    
    with pytest.raises(DynamoDBRepositoryError, match="DynamoDB error during record_interaction"):
        impact_repository.record_interaction(sample_interaction_event)


def test_record_outcome_network_error(impact_repository, mock_table, sample_outcome_event):
    """Test handling of network errors during outcome recording."""
    mock_table.put_item.side_effect = ClientError(
        {'Error': {'Code': 'ServiceUnavailable', 'Message': 'Service unavailable'}},
        'PutItem'
    )
    
    with pytest.raises(DynamoDBRepositoryError, match="DynamoDB error during record_outcome"):
        impact_repository.record_outcome(sample_outcome_event)


def test_get_analytics_data_network_error(impact_repository, mock_table):
    """Test handling of network errors during analytics query."""
    mock_table.scan.side_effect = ClientError(
        {'Error': {'Code': 'InternalServerError', 'Message': 'Internal server error'}},
        'Scan'
    )
    
    with pytest.raises(DynamoDBRepositoryError, match="DynamoDB error during get_analytics_data"):
        impact_repository.get_analytics_data()


def test_get_user_interactions_network_error(impact_repository, mock_table):
    """Test handling of network errors during user interactions query."""
    mock_table.scan.side_effect = ClientError(
        {'Error': {'Code': 'ProvisionedThroughputExceededException', 'Message': 'Throughput exceeded'}},
        'Scan'
    )
    
    with pytest.raises(DynamoDBRepositoryError, match="DynamoDB error during get_user_interactions"):
        impact_repository.get_user_interactions("user_123456")


# Test User Interactions Query

def test_get_user_interactions_success(impact_repository, mock_table):
    """Test retrieving user interactions."""
    mock_table.scan.return_value = {
        'Items': [
            {
                'event_id': 'evt_1',
                'user_id': 'user_123456',
                'event_type': 'query_submitted',
                'event_data': {'query': 'test'},
                'language': 'hi',
                'timestamp': datetime.utcnow().isoformat(),
                'record_type': 'interaction'
            }
        ]
    }
    
    interactions = impact_repository.get_user_interactions("user_123456")
    
    assert len(interactions) == 1
    assert interactions[0].user_id == "user_123456"
    assert interactions[0].event_type == "query_submitted"


def test_get_user_interactions_with_date_range(impact_repository, mock_table):
    """Test retrieving user interactions with date range."""
    mock_table.scan.return_value = {'Items': []}
    
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 1, 31)
    
    interactions = impact_repository.get_user_interactions(
        "user_123456",
        start_date=start_date,
        end_date=end_date
    )
    
    assert len(interactions) == 0
    # Verify date filters were applied
    call_kwargs = mock_table.scan.call_args.kwargs
    assert 'FilterExpression' in call_kwargs


def test_get_all_events_success(impact_repository, mock_table):
    """Test retrieving all events."""
    mock_table.scan.return_value = {
        'Items': [
            {
                'event_id': 'evt_1',
                'user_id': 'user_1',
                'event_type': 'query_submitted',
                'event_data': {},
                'timestamp': datetime.utcnow().isoformat(),
                'record_type': 'interaction'
            },
            {
                'event_id': 'out_1',
                'user_id': 'user_1',
                'outcome_type': 'scheme_applied',
                'outcome_data': {},
                'timestamp': datetime.utcnow().isoformat(),
                'record_type': 'outcome'
            }
        ]
    }
    
    events = impact_repository.get_all_events()
    
    assert len(events) == 2


def test_get_all_events_with_type_filter(impact_repository, mock_table):
    """Test retrieving all events with event type filter."""
    mock_table.scan.return_value = {'Items': []}
    
    events = impact_repository.get_all_events(event_type="query_submitted")
    
    # Verify filter was applied
    call_kwargs = mock_table.scan.call_args.kwargs
    assert 'FilterExpression' in call_kwargs
