"""Unit tests for SchemeRepository."""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from botocore.exceptions import ClientError

from src.core.scheme_repository import SchemeRepository, SchemeFilters
from src.core.base_repository import ItemNotFoundError, DynamoDBRepositoryError
from src.models.scheme import Scheme
from src.models.eligibility import EligibilityCriteria


@pytest.fixture
def mock_table():
    """Create a mock DynamoDB table."""
    return Mock()


@pytest.fixture
def scheme_repository(mock_table):
    """Create a SchemeRepository with mocked DynamoDB table."""
    with patch('boto3.resource') as mock_resource:
        mock_dynamodb = Mock()
        mock_dynamodb.Table.return_value = mock_table
        mock_resource.return_value = mock_dynamodb
        
        with patch('boto3.client'):
            repo = SchemeRepository(table_name="TestSchemes")
            repo.table = mock_table
            return repo


@pytest.fixture
def sample_scheme():
    """Create a sample scheme for testing."""
    return Scheme(
        scheme_id="PM-KISAN-2024",
        name="Pradhan Mantri Kisan Samman Nidhi",
        category="agriculture",
        description="Income support scheme for farmers",
        eligibility_criteria=EligibilityCriteria(
            age_min=18,
            occupation=["farmer"]
        ),
        department="Ministry of Agriculture",
        last_updated=datetime.utcnow(),
        source_url="https://pmkisan.gov.in"
    )


def test_create_scheme_success(scheme_repository, mock_table, sample_scheme):
    """Test successful scheme creation."""
    mock_table.put_item.return_value = {}
    
    result = scheme_repository.create(sample_scheme)
    
    assert result == sample_scheme
    mock_table.put_item.assert_called_once()


def test_create_scheme_already_exists(scheme_repository, mock_table, sample_scheme):
    """Test creating a scheme that already exists."""
    mock_table.put_item.side_effect = ClientError(
        {'Error': {'Code': 'ConditionalCheckFailedException', 'Message': 'Item exists'}},
        'PutItem'
    )
    
    with pytest.raises(DynamoDBRepositoryError, match="already exists"):
        scheme_repository.create(sample_scheme)


def test_get_scheme_success(scheme_repository, mock_table):
    """Test successful scheme retrieval."""
    mock_table.get_item.return_value = {
        'Item': {
            'scheme_id': 'PM-KISAN-2024',
            'name': 'Pradhan Mantri Kisan Samman Nidhi',
            'name_translations': {},
            'category': 'agriculture',
            'description': 'Income support scheme for farmers',
            'description_translations': {},
            'benefits': [],
            'eligibility_criteria': {
                'age_min': 18,
                'occupation': ['farmer'],
                'custom_criteria': {}
            },
            'required_documents': [],
            'application_process': [],
            'department': 'Ministry of Agriculture',
            'last_updated': '2024-01-01T00:00:00',
            'source_url': 'https://pmkisan.gov.in'
        }
    }
    
    result = scheme_repository.get('PM-KISAN-2024')
    
    assert result.scheme_id == 'PM-KISAN-2024'
    assert result.category == 'agriculture'
    mock_table.get_item.assert_called_once_with(Key={'scheme_id': 'PM-KISAN-2024'})


def test_get_scheme_not_found(scheme_repository, mock_table):
    """Test retrieving a non-existent scheme."""
    mock_table.get_item.return_value = {}
    
    with pytest.raises(ItemNotFoundError, match="not found"):
        scheme_repository.get('nonexistent_scheme')


def test_update_scheme_success(scheme_repository, mock_table, sample_scheme):
    """Test successful scheme update."""
    mock_table.put_item.return_value = {}
    
    sample_scheme.description = "Updated description"
    result = scheme_repository.update(sample_scheme)
    
    assert result.description == "Updated description"
    mock_table.put_item.assert_called_once()


def test_delete_scheme_success(scheme_repository, mock_table):
    """Test successful scheme deletion."""
    mock_table.delete_item.return_value = {}
    
    scheme_repository.delete('PM-KISAN-2024')
    
    mock_table.delete_item.assert_called_once()


def test_search_schemes_with_category_filter(scheme_repository, mock_table):
    """Test searching schemes with category filter."""
    mock_table.query.return_value = {
        'Items': [{
            'scheme_id': 'PM-KISAN-2024',
            'name': 'Pradhan Mantri Kisan Samman Nidhi',
            'name_translations': {},
            'category': 'agriculture',
            'description': 'Income support scheme for farmers',
            'description_translations': {},
            'benefits': [],
            'eligibility_criteria': {
                'age_min': 18,
                'occupation': ['farmer'],
                'custom_criteria': {}
            },
            'required_documents': [],
            'application_process': [],
            'department': 'Ministry of Agriculture',
            'last_updated': '2024-01-01T00:00:00',
            'source_url': 'https://pmkisan.gov.in'
        }]
    }
    
    filters = SchemeFilters(category="agriculture")
    results = scheme_repository.search_schemes(filters=filters)
    
    assert len(results) == 1
    assert results[0].category == "agriculture"


def test_search_schemes_with_query(scheme_repository, mock_table):
    """Test searching schemes with keyword query."""
    mock_table.scan.return_value = {
        'Items': [{
            'scheme_id': 'PM-KISAN-2024',
            'name': 'Pradhan Mantri Kisan Samman Nidhi',
            'name_translations': {},
            'category': 'agriculture',
            'description': 'Income support scheme for farmers',
            'description_translations': {},
            'benefits': [],
            'eligibility_criteria': {
                'age_min': 18,
                'occupation': ['farmer'],
                'custom_criteria': {}
            },
            'required_documents': [],
            'application_process': [],
            'department': 'Ministry of Agriculture',
            'last_updated': '2024-01-01T00:00:00',
            'source_url': 'https://pmkisan.gov.in'
        }]
    }
    
    results = scheme_repository.search_schemes(query="farmer")
    
    assert len(results) == 1
    assert "farmer" in results[0].description.lower()


def test_search_schemes_with_state_filter(scheme_repository, mock_table):
    """Test searching schemes with state filter."""
    mock_table.scan.return_value = {
        'Items': [{
            'scheme_id': 'MH-SCHEME-2024',
            'name': 'Maharashtra Scheme',
            'name_translations': {},
            'category': 'agriculture',
            'description': 'State scheme',
            'description_translations': {},
            'benefits': [],
            'eligibility_criteria': {
                'custom_criteria': {}
            },
            'required_documents': [],
            'application_process': [],
            'department': 'State Agriculture',
            'state': 'Maharashtra',
            'last_updated': '2024-01-01T00:00:00',
            'source_url': 'https://example.com'
        }]
    }
    
    filters = SchemeFilters(state="Maharashtra")
    results = scheme_repository.search_schemes(filters=filters)
    
    assert len(results) == 1
    assert results[0].state == "Maharashtra"


def test_search_schemes_fallback_to_scan(scheme_repository, mock_table):
    """Test fallback to scan when GSI is not available."""
    # Query raises ValidationException (GSI not found)
    mock_table.query.side_effect = ClientError(
        {'Error': {'Code': 'ValidationException', 'Message': 'GSI not found'}},
        'Query'
    )
    
    # Scan should be called as fallback
    mock_table.scan.return_value = {
        'Items': [{
            'scheme_id': 'PM-KISAN-2024',
            'name': 'Pradhan Mantri Kisan Samman Nidhi',
            'name_translations': {},
            'category': 'agriculture',
            'description': 'Income support scheme for farmers',
            'description_translations': {},
            'benefits': [],
            'eligibility_criteria': {
                'age_min': 18,
                'occupation': ['farmer'],
                'custom_criteria': {}
            },
            'required_documents': [],
            'application_process': [],
            'department': 'Ministry of Agriculture',
            'last_updated': '2024-01-01T00:00:00',
            'source_url': 'https://pmkisan.gov.in'
        }]
    }
    
    filters = SchemeFilters(category="agriculture")
    results = scheme_repository.search_schemes(filters=filters)
    
    assert len(results) == 1
    mock_table.scan.assert_called_once()


def test_get_all_schemes(scheme_repository, mock_table):
    """Test getting all schemes."""
    mock_table.scan.return_value = {
        'Items': [
            {
                'scheme_id': 'SCHEME-1',
                'name': 'Scheme 1',
                'name_translations': {},
                'category': 'agriculture',
                'description': 'Description 1',
                'description_translations': {},
                'benefits': [],
                'eligibility_criteria': {'custom_criteria': {}},
                'required_documents': [],
                'application_process': [],
                'department': 'Dept 1',
                'last_updated': '2024-01-01T00:00:00',
                'source_url': 'https://example.com'
            },
            {
                'scheme_id': 'SCHEME-2',
                'name': 'Scheme 2',
                'name_translations': {},
                'category': 'health',
                'description': 'Description 2',
                'description_translations': {},
                'benefits': [],
                'eligibility_criteria': {'custom_criteria': {}},
                'required_documents': [],
                'application_process': [],
                'department': 'Dept 2',
                'last_updated': '2024-01-01T00:00:00',
                'source_url': 'https://example.com'
            }
        ]
    }
    
    results = scheme_repository.get_all_schemes()
    
    assert len(results) == 2


def test_get_schemes_by_state(scheme_repository, mock_table):
    """Test getting schemes by state."""
    mock_table.scan.return_value = {
        'Items': [{
            'scheme_id': 'MH-SCHEME-2024',
            'name': 'Maharashtra Scheme',
            'name_translations': {},
            'category': 'agriculture',
            'description': 'State scheme',
            'description_translations': {},
            'benefits': [],
            'eligibility_criteria': {'custom_criteria': {}},
            'required_documents': [],
            'application_process': [],
            'department': 'State Agriculture',
            'state': 'Maharashtra',
            'last_updated': '2024-01-01T00:00:00',
            'source_url': 'https://example.com'
        }]
    }
    
    results = scheme_repository.get_schemes_by_state("Maharashtra")
    
    assert len(results) == 1
    assert results[0].state == "Maharashtra"


# Error Handling Tests for Network Failures

def test_create_scheme_network_error(scheme_repository, mock_table, sample_scheme):
    """Test handling of network errors during scheme creation."""
    mock_table.put_item.side_effect = ClientError(
        {'Error': {'Code': 'RequestTimeout', 'Message': 'Request timed out'}},
        'PutItem'
    )
    
    with pytest.raises(DynamoDBRepositoryError, match="DynamoDB error"):
        scheme_repository.create(sample_scheme)


def test_get_scheme_network_error(scheme_repository, mock_table):
    """Test handling of network errors during scheme retrieval."""
    mock_table.get_item.side_effect = ClientError(
        {'Error': {'Code': 'ServiceUnavailable', 'Message': 'Service unavailable'}},
        'GetItem'
    )
    
    with pytest.raises(DynamoDBRepositoryError, match="DynamoDB error"):
        scheme_repository.get('PM-KISAN-2024')


def test_update_scheme_network_error(scheme_repository, mock_table, sample_scheme):
    """Test handling of network errors during scheme update."""
    mock_table.put_item.side_effect = ClientError(
        {'Error': {'Code': 'InternalServerError', 'Message': 'Internal server error'}},
        'PutItem'
    )
    
    with pytest.raises(DynamoDBRepositoryError, match="DynamoDB error"):
        scheme_repository.update(sample_scheme)


def test_delete_scheme_network_error(scheme_repository, mock_table):
    """Test handling of network errors during scheme deletion."""
    mock_table.delete_item.side_effect = ClientError(
        {'Error': {'Code': 'ProvisionedThroughputExceededException', 'Message': 'Throughput exceeded'}},
        'DeleteItem'
    )
    
    with pytest.raises(DynamoDBRepositoryError, match="DynamoDB error"):
        scheme_repository.delete('PM-KISAN-2024')


def test_search_schemes_network_error(scheme_repository, mock_table):
    """Test handling of network errors during scheme search."""
    mock_table.scan.side_effect = ClientError(
        {'Error': {'Code': 'RequestTimeout', 'Message': 'Request timed out'}},
        'Scan'
    )
    
    with pytest.raises(DynamoDBRepositoryError, match="DynamoDB error"):
        scheme_repository.search_schemes(query="farmer")


def test_resource_not_found_error(scheme_repository, mock_table):
    """Test handling of ResourceNotFoundException (table doesn't exist)."""
    mock_table.get_item.side_effect = ClientError(
        {'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Table not found'}},
        'GetItem'
    )
    
    with pytest.raises(ItemNotFoundError, match="Table .* not found"):
        scheme_repository.get('PM-KISAN-2024')


# Pagination and Limit Tests

def test_search_schemes_with_limit(scheme_repository, mock_table):
    """Test searching schemes with custom limit."""
    mock_table.scan.return_value = {
        'Items': [
            {
                'scheme_id': f'SCHEME-{i}',
                'name': f'Scheme {i}',
                'name_translations': {},
                'category': 'agriculture',
                'description': f'Description {i}',
                'description_translations': {},
                'benefits': [],
                'eligibility_criteria': {'custom_criteria': {}},
                'required_documents': [],
                'application_process': [],
                'department': 'Dept',
                'last_updated': '2024-01-01T00:00:00',
                'source_url': 'https://example.com'
            }
            for i in range(10)
        ]
    }
    
    results = scheme_repository.search_schemes(query="scheme", limit=10)
    
    assert len(results) == 10
    # Verify limit was passed to scan
    call_kwargs = mock_table.scan.call_args.kwargs
    assert call_kwargs['Limit'] == 10


def test_get_all_schemes_with_limit(scheme_repository, mock_table):
    """Test getting all schemes with custom limit."""
    mock_table.scan.return_value = {
        'Items': [
            {
                'scheme_id': f'SCHEME-{i}',
                'name': f'Scheme {i}',
                'name_translations': {},
                'category': 'agriculture',
                'description': f'Description {i}',
                'description_translations': {},
                'benefits': [],
                'eligibility_criteria': {'custom_criteria': {}},
                'required_documents': [],
                'application_process': [],
                'department': 'Dept',
                'last_updated': '2024-01-01T00:00:00',
                'source_url': 'https://example.com'
            }
            for i in range(20)
        ]
    }
    
    results = scheme_repository.get_all_schemes(limit=20)
    
    assert len(results) == 20


def test_search_schemes_multiple_filters(scheme_repository, mock_table):
    """Test searching schemes with multiple filters combined."""
    mock_table.query.return_value = {
        'Items': [{
            'scheme_id': 'MH-AGRI-2024',
            'name': 'Maharashtra Agriculture Scheme',
            'name_translations': {},
            'category': 'agriculture',
            'description': 'State agriculture scheme',
            'description_translations': {},
            'benefits': [],
            'eligibility_criteria': {'custom_criteria': {}},
            'required_documents': [],
            'application_process': [],
            'department': 'State Agriculture',
            'state': 'Maharashtra',
            'last_updated': '2024-01-01T00:00:00',
            'source_url': 'https://example.com'
        }]
    }
    
    filters = SchemeFilters(
        category="agriculture",
        state="Maharashtra",
        department="State Agriculture"
    )
    results = scheme_repository.search_schemes(query="agriculture", filters=filters)
    
    assert len(results) == 1
    assert results[0].category == "agriculture"
    assert results[0].state == "Maharashtra"
    assert results[0].department == "State Agriculture"


def test_search_schemes_empty_results(scheme_repository, mock_table):
    """Test searching schemes with no matching results."""
    mock_table.scan.return_value = {'Items': []}
    
    results = scheme_repository.search_schemes(query="nonexistent")
    
    assert len(results) == 0
    assert results == []
