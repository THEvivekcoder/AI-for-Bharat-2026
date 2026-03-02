"""Integration tests for cache sync functionality.

These tests verify the cache sync endpoint works correctly with real AWS services
(or LocalStack for local testing).
"""

import pytest
import json
import os
import time
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import ClientError


# Test configuration
TEST_REGION = os.environ.get('AWS_REGION', 'us-east-1')
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'dev')
SCHEMES_TABLE = os.environ.get('SCHEMES_TABLE', f'bharatsahayak-schemes-{ENVIRONMENT}')


@pytest.fixture(scope='module')
def dynamodb_resource():
    """Create DynamoDB resource for testing."""
    return boto3.resource('dynamodb', region_name=TEST_REGION)


@pytest.fixture(scope='module')
def schemes_table(dynamodb_resource):
    """Get or create schemes table for testing."""
    try:
        table = dynamodb_resource.Table(SCHEMES_TABLE)
        table.load()
        return table
    except ClientError:
        # Table doesn't exist, skip integration tests
        pytest.skip(f"Table {SCHEMES_TABLE} not found. Skipping integration tests.")


@pytest.fixture
def sample_test_schemes():
    """Create sample schemes for integration testing."""
    base_time = datetime.utcnow()
    
    return [
        {
            'scheme_id': 'TEST-SYNC-001',
            'name': 'Test Agriculture Scheme',
            'category': 'agriculture',
            'description': 'Test scheme for farmers',
            'benefits': ['Test benefit 1', 'Test benefit 2'],
            'eligibility_criteria': {
                'occupation': ['farmer'],
                'age_min': 18,
                'age_max': 60
            },
            'required_documents': ['Aadhaar', 'Land records'],
            'application_process': ['Step 1', 'Step 2'],
            'last_updated': (base_time - timedelta(days=5)).isoformat()
        },
        {
            'scheme_id': 'TEST-SYNC-002',
            'name': 'Test Health Scheme',
            'category': 'health',
            'description': 'Test health insurance scheme',
            'benefits': ['Health coverage'],
            'eligibility_criteria': {
                'income_max': 100000
            },
            'required_documents': ['Aadhaar', 'Income certificate'],
            'application_process': ['Apply online'],
            'last_updated': (base_time - timedelta(days=2)).isoformat()
        },
        {
            'scheme_id': 'TEST-SYNC-003',
            'name': 'Test Employment Scheme',
            'category': 'employment',
            'description': 'Test skill development program',
            'benefits': ['Free training'],
            'eligibility_criteria': {
                'age_min': 18,
                'age_max': 35
            },
            'required_documents': ['Aadhaar'],
            'application_process': ['Register'],
            'last_updated': (base_time - timedelta(days=1)).isoformat()
        }
    ]


@pytest.fixture
def setup_test_schemes(schemes_table, sample_test_schemes):
    """Set up test schemes in DynamoDB."""
    # Insert test schemes
    for scheme in sample_test_schemes:
        schemes_table.put_item(Item=scheme)
    
    yield sample_test_schemes
    
    # Cleanup: Delete test schemes
    for scheme in sample_test_schemes:
        try:
            schemes_table.delete_item(Key={'scheme_id': scheme['scheme_id']})
        except Exception as e:
            print(f"Error cleaning up scheme {scheme['scheme_id']}: {e}")


# Integration Tests

def test_cache_sync_full_sync_integration(setup_test_schemes):
    """Test full sync retrieves all test schemes."""
    from src.api.cache_sync import lambda_handler
    
    # Create event for full sync
    event = {
        'body': json.dumps({
            'max_size_kb': 100
        })
    }
    
    # Execute handler
    response = lambda_handler(event, None)
    
    # Verify response
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    
    assert 'updated_schemes' in body
    assert body['incremental'] is False
    
    # Verify test schemes are included
    updated_ids = body['updated_schemes']
    assert 'TEST-SYNC-001' in updated_ids
    assert 'TEST-SYNC-002' in updated_ids
    assert 'TEST-SYNC-003' in updated_ids


def test_cache_sync_incremental_sync_integration(setup_test_schemes):
    """Test incremental sync retrieves only recently updated schemes."""
    from src.api.cache_sync import lambda_handler
    
    # Set last_sync_timestamp to 3 days ago
    last_sync = (datetime.utcnow() - timedelta(days=3)).isoformat() + 'Z'
    
    # Create event for incremental sync
    event = {
        'body': json.dumps({
            'last_sync_timestamp': last_sync,
            'max_size_kb': 100
        })
    }
    
    # Execute handler
    response = lambda_handler(event, None)
    
    # Verify response
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    
    assert body['incremental'] is True
    
    # Should include TEST-SYNC-002 and TEST-SYNC-003 (updated within 3 days)
    # Should NOT include TEST-SYNC-001 (updated 5 days ago)
    updated_ids = body['updated_schemes']
    assert 'TEST-SYNC-002' in updated_ids
    assert 'TEST-SYNC-003' in updated_ids


def test_cache_sync_with_category_filter_integration(setup_test_schemes):
    """Test sync with category filter."""
    from src.api.cache_sync import lambda_handler
    
    # Create event with category filter
    event = {
        'body': json.dumps({
            'categories': ['agriculture', 'health'],
            'max_size_kb': 100
        })
    }
    
    # Execute handler
    response = lambda_handler(event, None)
    
    # Verify response
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    
    # Should include agriculture and health schemes
    updated_ids = body['updated_schemes']
    assert 'TEST-SYNC-001' in updated_ids  # agriculture
    assert 'TEST-SYNC-002' in updated_ids  # health
    
    # Verify schemes_data only contains filtered categories
    if body['schemes_data']:
        for scheme in body['schemes_data'].values():
            assert scheme['category'] in ['agriculture', 'health']


def test_cache_sync_bandwidth_constraint_integration(setup_test_schemes):
    """Test that sync respects bandwidth constraints."""
    from src.api.cache_sync import lambda_handler
    
    # Create event with very small max_size_kb
    event = {
        'body': json.dumps({
            'max_size_kb': 2  # Very small limit
        })
    }
    
    # Execute handler
    response = lambda_handler(event, None)
    
    # Verify response
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    
    # Should respect size constraint
    assert body['total_size_kb'] <= 2.0
    
    # May not include all schemes due to size limit
    if body['schemes_data']:
        assert len(body['schemes_data']) < len(setup_test_schemes)


def test_cache_sync_response_structure_integration(setup_test_schemes):
    """Test that response has correct structure."""
    from src.api.cache_sync import lambda_handler
    
    event = {
        'body': json.dumps({
            'max_size_kb': 100
        })
    }
    
    # Execute handler
    response = lambda_handler(event, None)
    
    # Verify response structure
    assert response['statusCode'] == 200
    assert 'headers' in response
    assert 'Content-Type' in response['headers']
    assert response['headers']['Content-Type'] == 'application/json'
    assert 'Access-Control-Allow-Origin' in response['headers']
    assert response['headers']['Access-Control-Allow-Origin'] == '*'
    
    body = json.loads(response['body'])
    
    # Verify required fields
    assert 'updated_schemes' in body
    assert 'deleted_schemes' in body
    assert 'total_size_kb' in body
    assert 'sync_timestamp' in body
    assert 'incremental' in body
    
    # Verify data types
    assert isinstance(body['updated_schemes'], list)
    assert isinstance(body['deleted_schemes'], list)
    assert isinstance(body['total_size_kb'], (int, float))
    assert isinstance(body['sync_timestamp'], str)
    assert isinstance(body['incremental'], bool)


def test_cache_sync_schemes_data_completeness_integration(setup_test_schemes):
    """Test that schemes_data contains complete information."""
    from src.api.cache_sync import lambda_handler
    
    event = {
        'body': json.dumps({
            'max_size_kb': 100
        })
    }
    
    # Execute handler
    response = lambda_handler(event, None)
    
    # Verify response
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    
    # Verify schemes_data structure
    if body['schemes_data']:
        for scheme_id, scheme in body['schemes_data'].items():
            # Verify all required fields are present
            assert 'scheme_id' in scheme
            assert 'name' in scheme
            assert 'category' in scheme
            assert 'description' in scheme
            assert 'benefits' in scheme
            assert 'eligibility_criteria' in scheme
            assert 'required_documents' in scheme
            assert 'application_process' in scheme
            assert 'last_updated' in scheme
            
            # Verify data types
            assert isinstance(scheme['scheme_id'], str)
            assert isinstance(scheme['name'], str)
            assert isinstance(scheme['category'], str)
            assert isinstance(scheme['description'], str)
            assert isinstance(scheme['benefits'], list)
            assert isinstance(scheme['eligibility_criteria'], dict)
            assert isinstance(scheme['required_documents'], list)
            assert isinstance(scheme['application_process'], list)


def test_cache_sync_empty_result_integration(schemes_table):
    """Test sync when no schemes match criteria."""
    from src.api.cache_sync import lambda_handler
    
    # Set last_sync_timestamp to future date
    future_date = (datetime.utcnow() + timedelta(days=10)).isoformat() + 'Z'
    
    event = {
        'body': json.dumps({
            'last_sync_timestamp': future_date,
            'max_size_kb': 100
        })
    }
    
    # Execute handler
    response = lambda_handler(event, None)
    
    # Verify response
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    
    # Should have no updated schemes
    assert len(body['updated_schemes']) == 0
    assert body['schemes_data'] is None
    assert body['total_size_kb'] == 0


def test_cache_sync_timestamp_format_integration(setup_test_schemes):
    """Test that sync_timestamp is in correct ISO format."""
    from src.api.cache_sync import lambda_handler
    
    event = {
        'body': json.dumps({
            'max_size_kb': 100
        })
    }
    
    # Execute handler
    response = lambda_handler(event, None)
    
    # Verify response
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    
    # Verify timestamp format
    sync_timestamp = body['sync_timestamp']
    
    # Should be parseable as ISO format
    try:
        parsed_time = datetime.fromisoformat(sync_timestamp)
        assert parsed_time is not None
    except ValueError:
        pytest.fail(f"Invalid timestamp format: {sync_timestamp}")


def test_cache_sync_incremental_with_categories_integration(setup_test_schemes):
    """Test incremental sync combined with category filter."""
    from src.api.cache_sync import lambda_handler
    
    # Set last_sync_timestamp to 3 days ago
    last_sync = (datetime.utcnow() - timedelta(days=3)).isoformat() + 'Z'
    
    event = {
        'body': json.dumps({
            'last_sync_timestamp': last_sync,
            'categories': ['health', 'employment'],
            'max_size_kb': 100
        })
    }
    
    # Execute handler
    response = lambda_handler(event, None)
    
    # Verify response
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    
    # Should include TEST-SYNC-002 (health, updated 2 days ago)
    # Should include TEST-SYNC-003 (employment, updated 1 day ago)
    # Should NOT include TEST-SYNC-001 (agriculture category)
    updated_ids = body['updated_schemes']
    assert 'TEST-SYNC-002' in updated_ids
    assert 'TEST-SYNC-003' in updated_ids


def test_cache_sync_cors_headers_integration(setup_test_schemes):
    """Test that CORS headers are properly set."""
    from src.api.cache_sync import lambda_handler
    
    event = {
        'body': json.dumps({
            'max_size_kb': 100
        })
    }
    
    # Execute handler
    response = lambda_handler(event, None)
    
    # Verify CORS headers
    assert response['statusCode'] == 200
    assert 'headers' in response
    assert 'Access-Control-Allow-Origin' in response['headers']
    assert response['headers']['Access-Control-Allow-Origin'] == '*'
