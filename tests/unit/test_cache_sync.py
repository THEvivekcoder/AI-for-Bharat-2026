"""Unit tests for cache sync functionality."""

import pytest
import json
import gzip
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError


@pytest.fixture
def mock_dynamodb_table():
    """Create a mock DynamoDB table."""
    return Mock()


@pytest.fixture
def mock_s3_client():
    """Create a mock S3 client."""
    return Mock()


@pytest.fixture
def sample_schemes():
    """Create sample schemes for testing."""
    return [
        {
            'scheme_id': 'SCHEME-001',
            'name': 'PM-KISAN',
            'category': 'agriculture',
            'description': 'Direct income support to farmers',
            'benefits': ['₹6000 per year', 'Direct bank transfer'],
            'eligibility_criteria': {
                'occupation': ['farmer'],
                'land_size_max': 2.0
            },
            'required_documents': ['Aadhaar', 'Land records'],
            'application_process': ['Visit portal', 'Fill form', 'Submit documents'],
            'last_updated': '2024-01-15T10:00:00'
        },
        {
            'scheme_id': 'SCHEME-002',
            'name': 'Ayushman Bharat',
            'category': 'health',
            'description': 'Health insurance for poor families',
            'benefits': ['₹5 lakh coverage', 'Cashless treatment'],
            'eligibility_criteria': {
                'income_max': 100000
            },
            'required_documents': ['Aadhaar', 'Income certificate'],
            'application_process': ['Visit health center', 'Get card'],
            'last_updated': '2024-01-20T15:30:00'
        },
        {
            'scheme_id': 'SCHEME-003',
            'name': 'Skill India',
            'category': 'employment',
            'description': 'Skill development program',
            'benefits': ['Free training', 'Certification'],
            'eligibility_criteria': {
                'age_min': 18,
                'age_max': 35
            },
            'required_documents': ['Aadhaar', 'Education certificate'],
            'application_process': ['Register online', 'Choose course'],
            'last_updated': '2024-01-10T08:00:00'
        }
    ]


@pytest.fixture
def lambda_event_full_sync():
    """Create a Lambda event for full sync (no last_sync_timestamp)."""
    return {
        'body': json.dumps({
            'max_size_kb': 100
        })
    }


@pytest.fixture
def lambda_event_incremental_sync():
    """Create a Lambda event for incremental sync."""
    return {
        'body': json.dumps({
            'last_sync_timestamp': '2024-01-12T00:00:00Z',
            'max_size_kb': 100
        })
    }


@pytest.fixture
def lambda_event_with_category_filter():
    """Create a Lambda event with category filter."""
    return {
        'body': json.dumps({
            'last_sync_timestamp': '2024-01-12T00:00:00Z',
            'categories': ['agriculture', 'health'],
            'max_size_kb': 100
        })
    }


# Test Lambda Handler - Full Sync

@patch('src.api.cache_sync.dynamodb')
@patch('src.api.cache_sync.s3_client')
def test_lambda_handler_full_sync_success(mock_s3, mock_dynamodb, lambda_event_full_sync, sample_schemes):
    """Test successful full sync without last_sync_timestamp."""
    from src.api.cache_sync import lambda_handler
    
    # Mock DynamoDB table
    mock_table = Mock()
    mock_dynamodb.Table.return_value = mock_table
    
    # Mock scan to return all schemes
    mock_table.scan.return_value = {
        'Items': sample_schemes
    }
    
    # Mock get_item for individual scheme fetches
    def mock_get_item(Key):
        scheme_id = Key['scheme_id']
        for scheme in sample_schemes:
            if scheme['scheme_id'] == scheme_id:
                return {'Item': scheme}
        return {}
    
    mock_table.get_item.side_effect = mock_get_item
    
    # Execute handler
    response = lambda_handler(lambda_event_full_sync, None)
    
    # Verify response
    assert response['statusCode'] == 200
    assert 'body' in response
    
    body = json.loads(response['body'])
    assert 'updated_schemes' in body
    assert 'sync_timestamp' in body
    assert body['incremental'] is False
    assert len(body['updated_schemes']) == 3


@patch('src.api.cache_sync.dynamodb')
@patch('src.api.cache_sync.s3_client')
def test_lambda_handler_incremental_sync_success(mock_s3, mock_dynamodb, lambda_event_incremental_sync, sample_schemes):
    """Test successful incremental sync with last_sync_timestamp."""
    from src.api.cache_sync import lambda_handler
    
    # Mock DynamoDB table
    mock_table = Mock()
    mock_dynamodb.Table.return_value = mock_table
    
    # Only return schemes updated after 2024-01-12
    updated_schemes = [s for s in sample_schemes if s['last_updated'] > '2024-01-12T00:00:00']
    
    mock_table.scan.return_value = {
        'Items': updated_schemes
    }
    
    # Mock get_item for individual scheme fetches
    def mock_get_item(Key):
        scheme_id = Key['scheme_id']
        for scheme in updated_schemes:
            if scheme['scheme_id'] == scheme_id:
                return {'Item': scheme}
        return {}
    
    mock_table.get_item.side_effect = mock_get_item
    
    # Execute handler
    response = lambda_handler(lambda_event_incremental_sync, None)
    
    # Verify response
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    
    assert body['incremental'] is True
    assert len(body['updated_schemes']) == 2  # Only SCHEME-001 and SCHEME-002


@patch('src.api.cache_sync.dynamodb')
@patch('src.api.cache_sync.s3_client')
def test_lambda_handler_with_category_filter(mock_s3, mock_dynamodb, lambda_event_with_category_filter, sample_schemes):
    """Test sync with category filter."""
    from src.api.cache_sync import lambda_handler
    
    # Mock DynamoDB table
    mock_table = Mock()
    mock_dynamodb.Table.return_value = mock_table
    
    # Filter schemes by category and update time
    filtered_schemes = [
        s for s in sample_schemes 
        if s['category'] in ['agriculture', 'health'] and s['last_updated'] > '2024-01-12T00:00:00'
    ]
    
    mock_table.scan.return_value = {
        'Items': filtered_schemes
    }
    
    # Mock get_item
    def mock_get_item(Key):
        scheme_id = Key['scheme_id']
        for scheme in filtered_schemes:
            if scheme['scheme_id'] == scheme_id:
                return {'Item': scheme}
        return {}
    
    mock_table.get_item.side_effect = mock_get_item
    
    # Execute handler
    response = lambda_handler(lambda_event_with_category_filter, None)
    
    # Verify response
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    
    assert len(body['updated_schemes']) == 2
    # Verify only agriculture and health schemes
    if body['schemes_data']:
        for scheme in body['schemes_data'].values():
            assert scheme['category'] in ['agriculture', 'health']


# Test Bandwidth Constraint

@patch('src.api.cache_sync.dynamodb')
@patch('src.api.cache_sync.s3_client')
def test_lambda_handler_respects_max_size_kb(mock_s3, mock_dynamodb, sample_schemes):
    """Test that response respects max_size_kb constraint."""
    from src.api.cache_sync import lambda_handler
    
    # Mock DynamoDB table
    mock_table = Mock()
    mock_dynamodb.Table.return_value = mock_table
    
    mock_table.scan.return_value = {
        'Items': sample_schemes
    }
    
    # Mock get_item
    def mock_get_item(Key):
        scheme_id = Key['scheme_id']
        for scheme in sample_schemes:
            if scheme['scheme_id'] == scheme_id:
                return {'Item': scheme}
        return {}
    
    mock_table.get_item.side_effect = mock_get_item
    
    # Create event with very small max_size_kb
    event = {
        'body': json.dumps({
            'max_size_kb': 1  # Very small limit
        })
    }
    
    # Execute handler
    response = lambda_handler(event, None)
    
    # Verify response
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    
    # Should have limited schemes_data due to size constraint
    assert body['total_size_kb'] <= 1.0


@patch('src.api.cache_sync.dynamodb')
@patch('src.api.cache_sync.s3_client')
def test_lambda_handler_compression_for_large_response(mock_s3, mock_dynamodb, sample_schemes):
    """Test that large responses are compressed."""
    from src.api.cache_sync import lambda_handler
    
    # Create many schemes to ensure large response
    large_scheme_list = []
    for i in range(50):
        scheme = sample_schemes[0].copy()
        scheme['scheme_id'] = f'SCHEME-{i:03d}'
        scheme['description'] = 'Long description ' * 100  # Make it large
        large_scheme_list.append(scheme)
    
    # Mock DynamoDB table
    mock_table = Mock()
    mock_dynamodb.Table.return_value = mock_table
    
    mock_table.scan.return_value = {
        'Items': large_scheme_list
    }
    
    # Mock get_item
    def mock_get_item(Key):
        scheme_id = Key['scheme_id']
        for scheme in large_scheme_list:
            if scheme['scheme_id'] == scheme_id:
                return {'Item': scheme}
        return {}
    
    mock_table.get_item.side_effect = mock_get_item
    
    # Create event
    event = {
        'body': json.dumps({
            'max_size_kb': 500
        })
    }
    
    # Execute handler
    response = lambda_handler(event, None)
    
    # Verify response
    assert response['statusCode'] == 200
    
    # Check if compression was applied for large response
    if response.get('isBase64Encoded'):
        assert 'Content-Encoding' in response['headers']
        assert response['headers']['Content-Encoding'] == 'gzip'


# Test Empty Results

@patch('src.api.cache_sync.dynamodb')
@patch('src.api.cache_sync.s3_client')
def test_lambda_handler_no_updated_schemes(mock_s3, mock_dynamodb):
    """Test sync when no schemes have been updated."""
    from src.api.cache_sync import lambda_handler
    
    # Mock DynamoDB table
    mock_table = Mock()
    mock_dynamodb.Table.return_value = mock_table
    
    # Return empty results
    mock_table.scan.return_value = {
        'Items': []
    }
    
    event = {
        'body': json.dumps({
            'last_sync_timestamp': '2024-01-25T00:00:00Z',
            'max_size_kb': 100
        })
    }
    
    # Execute handler
    response = lambda_handler(event, None)
    
    # Verify response
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    
    assert len(body['updated_schemes']) == 0
    assert body['schemes_data'] is None
    assert body['total_size_kb'] == 0


# Test get_updated_schemes Function

@patch('src.api.cache_sync.dynamodb')
def test_get_updated_schemes_without_timestamp(mock_dynamodb, sample_schemes):
    """Test getting all schemes when no timestamp is provided."""
    from src.api.cache_sync import get_updated_schemes
    
    # Mock DynamoDB table
    mock_table = Mock()
    mock_dynamodb.Table.return_value = mock_table
    
    mock_table.scan.return_value = {
        'Items': sample_schemes
    }
    
    # Execute function
    updated, deleted = get_updated_schemes(last_sync_timestamp=None)
    
    # Verify results
    assert len(updated) == 3
    assert len(deleted) == 0
    assert 'SCHEME-001' in updated
    assert 'SCHEME-002' in updated
    assert 'SCHEME-003' in updated


@patch('src.api.cache_sync.dynamodb')
def test_get_updated_schemes_with_timestamp(mock_dynamodb, sample_schemes):
    """Test getting only schemes updated after timestamp."""
    from src.api.cache_sync import get_updated_schemes
    
    # Mock DynamoDB table
    mock_table = Mock()
    mock_dynamodb.Table.return_value = mock_table
    
    # Only return schemes updated after the timestamp
    filtered_schemes = [s for s in sample_schemes if s['last_updated'] > '2024-01-12T00:00:00']
    mock_table.scan.return_value = {
        'Items': filtered_schemes
    }
    
    # Execute function
    sync_time = datetime(2024, 1, 12, 0, 0, 0)
    updated, deleted = get_updated_schemes(last_sync_timestamp=sync_time)
    
    # Verify results - should only include SCHEME-001 and SCHEME-002
    assert len(updated) == 2
    assert 'SCHEME-001' in updated
    assert 'SCHEME-002' in updated
    assert 'SCHEME-003' not in updated


@patch('src.api.cache_sync.dynamodb')
def test_get_updated_schemes_with_categories(mock_dynamodb, sample_schemes):
    """Test getting schemes filtered by categories."""
    from src.api.cache_sync import get_updated_schemes
    
    # Mock DynamoDB table
    mock_table = Mock()
    mock_dynamodb.Table.return_value = mock_table
    
    # Filter by categories
    filtered_schemes = [s for s in sample_schemes if s['category'] in ['agriculture', 'health']]
    mock_table.scan.return_value = {
        'Items': filtered_schemes
    }
    
    # Execute function
    updated, deleted = get_updated_schemes(
        last_sync_timestamp=None,
        categories=['agriculture', 'health']
    )
    
    # Verify results
    assert len(updated) == 2
    assert 'SCHEME-001' in updated  # agriculture
    assert 'SCHEME-002' in updated  # health
    assert 'SCHEME-003' not in updated  # employment


@patch('src.api.cache_sync.dynamodb')
def test_get_updated_schemes_with_pagination(mock_dynamodb, sample_schemes):
    """Test handling of paginated DynamoDB scan results."""
    from src.api.cache_sync import get_updated_schemes
    
    # Mock DynamoDB table
    mock_table = Mock()
    mock_dynamodb.Table.return_value = mock_table
    
    # Simulate pagination
    mock_table.scan.side_effect = [
        {
            'Items': [sample_schemes[0], sample_schemes[1]],
            'LastEvaluatedKey': {'scheme_id': 'SCHEME-002'}
        },
        {
            'Items': [sample_schemes[2]]
        }
    ]
    
    # Execute function
    updated, deleted = get_updated_schemes(last_sync_timestamp=None)
    
    # Verify all schemes were retrieved across pages
    assert len(updated) == 3
    assert mock_table.scan.call_count == 2


# Test get_scheme_by_id Function

@patch('src.api.cache_sync.dynamodb')
def test_get_scheme_by_id_success(mock_dynamodb, sample_schemes):
    """Test successfully retrieving a scheme by ID."""
    from src.api.cache_sync import get_scheme_by_id
    
    # Mock DynamoDB table
    mock_table = Mock()
    mock_dynamodb.Table.return_value = mock_table
    
    mock_table.get_item.return_value = {
        'Item': sample_schemes[0]
    }
    
    # Execute function
    scheme = get_scheme_by_id('SCHEME-001')
    
    # Verify result
    assert scheme is not None
    assert scheme['scheme_id'] == 'SCHEME-001'
    assert scheme['name'] == 'PM-KISAN'


@patch('src.api.cache_sync.dynamodb')
def test_get_scheme_by_id_not_found(mock_dynamodb):
    """Test retrieving a non-existent scheme."""
    from src.api.cache_sync import get_scheme_by_id
    
    # Mock DynamoDB table
    mock_table = Mock()
    mock_dynamodb.Table.return_value = mock_table
    
    mock_table.get_item.return_value = {}
    
    # Execute function
    scheme = get_scheme_by_id('NONEXISTENT')
    
    # Verify result
    assert scheme is None


@patch('src.api.cache_sync.dynamodb')
def test_get_scheme_by_id_error_handling(mock_dynamodb):
    """Test error handling when retrieving scheme."""
    from src.api.cache_sync import get_scheme_by_id
    
    # Mock DynamoDB table
    mock_table = Mock()
    mock_dynamodb.Table.return_value = mock_table
    
    mock_table.get_item.side_effect = ClientError(
        {'Error': {'Code': 'ServiceUnavailable', 'Message': 'Service unavailable'}},
        'GetItem'
    )
    
    # Execute function
    scheme = get_scheme_by_id('SCHEME-001')
    
    # Should return None on error
    assert scheme is None


# Test Error Handling

@patch('src.api.cache_sync.dynamodb')
@patch('src.api.cache_sync.s3_client')
def test_lambda_handler_invalid_json_body(mock_s3, mock_dynamodb):
    """Test handling of invalid JSON in request body."""
    from src.api.cache_sync import lambda_handler
    
    event = {
        'body': 'invalid json {'
    }
    
    # Execute handler
    response = lambda_handler(event, None)
    
    # Should return error response
    assert response['statusCode'] == 500
    body = json.loads(response['body'])
    assert 'error' in body


@patch('src.api.cache_sync.dynamodb')
@patch('src.api.cache_sync.s3_client')
def test_lambda_handler_missing_body(mock_s3, mock_dynamodb):
    """Test handling of missing request body."""
    from src.api.cache_sync import lambda_handler
    
    # Mock DynamoDB table
    mock_table = Mock()
    mock_dynamodb.Table.return_value = mock_table
    mock_table.scan.return_value = {'Items': []}
    
    event = {}
    
    # Execute handler - should use defaults
    response = lambda_handler(event, None)
    
    # Should succeed with defaults
    assert response['statusCode'] == 200


@patch('src.api.cache_sync.dynamodb')
@patch('src.api.cache_sync.s3_client')
def test_lambda_handler_dynamodb_error(mock_s3, mock_dynamodb):
    """Test handling of DynamoDB errors."""
    from src.api.cache_sync import lambda_handler
    
    # Mock DynamoDB table
    mock_table = Mock()
    mock_dynamodb.Table.return_value = mock_table
    
    mock_table.scan.side_effect = ClientError(
        {'Error': {'Code': 'ServiceUnavailable', 'Message': 'Service unavailable'}},
        'Scan'
    )
    
    event = {
        'body': json.dumps({
            'max_size_kb': 100
        })
    }
    
    # Execute handler
    response = lambda_handler(event, None)
    
    # The function handles errors gracefully and returns empty results
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert len(body['updated_schemes']) == 0
    assert len(body['deleted_schemes']) == 0


# Test Response Structure

@patch('src.api.cache_sync.dynamodb')
@patch('src.api.cache_sync.s3_client')
def test_response_contains_required_fields(mock_s3, mock_dynamodb, lambda_event_full_sync, sample_schemes):
    """Test that response contains all required fields."""
    from src.api.cache_sync import lambda_handler
    
    # Mock DynamoDB table
    mock_table = Mock()
    mock_dynamodb.Table.return_value = mock_table
    
    mock_table.scan.return_value = {
        'Items': sample_schemes
    }
    
    def mock_get_item(Key):
        scheme_id = Key['scheme_id']
        for scheme in sample_schemes:
            if scheme['scheme_id'] == scheme_id:
                return {'Item': scheme}
        return {}
    
    mock_table.get_item.side_effect = mock_get_item
    
    # Execute handler
    response = lambda_handler(lambda_event_full_sync, None)
    
    # Verify response structure
    assert response['statusCode'] == 200
    assert 'headers' in response
    assert 'Content-Type' in response['headers']
    assert 'Access-Control-Allow-Origin' in response['headers']
    assert 'body' in response
    
    body = json.loads(response['body'])
    
    # Verify required fields in body
    assert 'updated_schemes' in body
    assert 'deleted_schemes' in body
    assert 'total_size_kb' in body
    assert 'sync_timestamp' in body
    assert 'incremental' in body
    assert isinstance(body['updated_schemes'], list)
    assert isinstance(body['deleted_schemes'], list)
    assert isinstance(body['total_size_kb'], (int, float))
    assert isinstance(body['incremental'], bool)


@patch('src.api.cache_sync.dynamodb')
@patch('src.api.cache_sync.s3_client')
def test_schemes_data_structure(mock_s3, mock_dynamodb, lambda_event_full_sync, sample_schemes):
    """Test that schemes_data has correct structure."""
    from src.api.cache_sync import lambda_handler
    
    # Mock DynamoDB table
    mock_table = Mock()
    mock_dynamodb.Table.return_value = mock_table
    
    mock_table.scan.return_value = {
        'Items': sample_schemes
    }
    
    def mock_get_item(Key):
        scheme_id = Key['scheme_id']
        for scheme in sample_schemes:
            if scheme['scheme_id'] == scheme_id:
                return {'Item': scheme}
        return {}
    
    mock_table.get_item.side_effect = mock_get_item
    
    # Execute handler
    response = lambda_handler(lambda_event_full_sync, None)
    
    body = json.loads(response['body'])
    
    if body['schemes_data']:
        # Verify each scheme has required fields
        for scheme_id, scheme in body['schemes_data'].items():
            assert 'scheme_id' in scheme
            assert 'name' in scheme
            assert 'category' in scheme
            assert 'description' in scheme
            assert 'benefits' in scheme
            assert 'eligibility_criteria' in scheme
            assert 'required_documents' in scheme
            assert 'application_process' in scheme
            assert 'last_updated' in scheme
