"""Unit tests for scheme search Lambda function."""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.api.schemes_search import lambda_handler, _scheme_to_summary
from src.models.scheme import Scheme
from src.models.eligibility import EligibilityCriteria
from src.core.scheme_repository import SchemeFilters, DynamoDBRepositoryError


@pytest.fixture
def sample_scheme():
    """Create a sample scheme for testing."""
    return Scheme(
        scheme_id="TEST-001",
        name="Test Scheme",
        name_translations={"hi": "परीक्षण योजना"},
        category="agriculture",
        description="A test scheme for farmers",
        description_translations={"hi": "किसानों के लिए एक परीक्षण योजना"},
        benefits=["Benefit 1", "Benefit 2"],
        eligibility_criteria=EligibilityCriteria(
            age_min=18,
            occupation=["farmer"]
        ),
        required_documents=["Aadhaar", "Bank details"],
        application_process=["Step 1", "Step 2"],
        application_url="https://example.com",
        department="Agriculture Department",
        state="Maharashtra",
        last_updated=datetime(2024, 1, 15, 10, 30, 0),
        source_url="https://example.com/source"
    )


@pytest.fixture
def sample_schemes(sample_scheme):
    """Create a list of sample schemes."""
    schemes = []
    for i in range(5):
        scheme = sample_scheme.model_copy()
        scheme.scheme_id = f"TEST-{i:03d}"
        scheme.name = f"Test Scheme {i}"
        schemes.append(scheme)
    return schemes


class TestLambdaHandler:
    """Test cases for the lambda_handler function."""
    
    @patch('src.api.schemes_search.scheme_repo')
    def test_search_without_filters(self, mock_repo, sample_schemes):
        """Test basic search without any filters."""
        # Setup
        mock_repo.search_schemes.return_value = sample_schemes
        
        event = {
            'queryStringParameters': None
        }
        
        # Execute
        response = lambda_handler(event, None)
        
        # Verify
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert 'schemes' in body
        assert 'pagination' in body
        assert len(body['schemes']) == 5
        assert body['pagination']['page'] == 1
        assert body['pagination']['limit'] == 20
        assert body['pagination']['total'] == 5
        assert body['pagination']['has_more'] is False
        
        # Verify repository was called correctly
        mock_repo.search_schemes.assert_called_once()
        call_args = mock_repo.search_schemes.call_args
        assert call_args[1]['query'] is None
        assert call_args[1]['limit'] == 20
    
    @patch('src.api.schemes_search.scheme_repo')
    def test_search_with_keyword(self, mock_repo, sample_schemes):
        """Test search with keyword query."""
        # Setup
        mock_repo.search_schemes.return_value = sample_schemes[:2]
        
        event = {
            'queryStringParameters': {
                'q': 'farmer'
            }
        }
        
        # Execute
        response = lambda_handler(event, None)
        
        # Verify
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert len(body['schemes']) == 2
        
        # Verify repository was called with query
        call_args = mock_repo.search_schemes.call_args
        assert call_args[1]['query'] == 'farmer'
    
    @patch('src.api.schemes_search.scheme_repo')
    def test_search_with_category_filter(self, mock_repo, sample_schemes):
        """Test search with category filter."""
        # Setup
        mock_repo.search_schemes.return_value = sample_schemes
        
        event = {
            'queryStringParameters': {
                'category': 'agriculture'
            }
        }
        
        # Execute
        response = lambda_handler(event, None)
        
        # Verify
        assert response['statusCode'] == 200
        
        # Verify filters were passed correctly
        call_args = mock_repo.search_schemes.call_args
        filters = call_args[1]['filters']
        assert filters.category == 'agriculture'
    
    @patch('src.api.schemes_search.scheme_repo')
    def test_search_with_state_filter(self, mock_repo, sample_schemes):
        """Test search with state filter."""
        # Setup
        mock_repo.search_schemes.return_value = sample_schemes
        
        event = {
            'queryStringParameters': {
                'state': 'Maharashtra'
            }
        }
        
        # Execute
        response = lambda_handler(event, None)
        
        # Verify
        assert response['statusCode'] == 200
        
        # Verify filters were passed correctly
        call_args = mock_repo.search_schemes.call_args
        filters = call_args[1]['filters']
        assert filters.state == 'Maharashtra'
    
    @patch('src.api.schemes_search.scheme_repo')
    def test_search_with_department_filter(self, mock_repo, sample_schemes):
        """Test search with department filter."""
        # Setup
        mock_repo.search_schemes.return_value = sample_schemes
        
        event = {
            'queryStringParameters': {
                'department': 'Agriculture Department'
            }
        }
        
        # Execute
        response = lambda_handler(event, None)
        
        # Verify
        assert response['statusCode'] == 200
        
        # Verify filters were passed correctly
        call_args = mock_repo.search_schemes.call_args
        filters = call_args[1]['filters']
        assert filters.department == 'Agriculture Department'
    
    @patch('src.api.schemes_search.scheme_repo')
    def test_search_with_multiple_filters(self, mock_repo, sample_schemes):
        """Test search with multiple filters combined."""
        # Setup
        mock_repo.search_schemes.return_value = sample_schemes[:1]
        
        event = {
            'queryStringParameters': {
                'q': 'farmer',
                'category': 'agriculture',
                'state': 'Maharashtra',
                'department': 'Agriculture Department'
            }
        }
        
        # Execute
        response = lambda_handler(event, None)
        
        # Verify
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert len(body['schemes']) == 1
        
        # Verify all filters were passed
        call_args = mock_repo.search_schemes.call_args
        assert call_args[1]['query'] == 'farmer'
        filters = call_args[1]['filters']
        assert filters.category == 'agriculture'
        assert filters.state == 'Maharashtra'
        assert filters.department == 'Agriculture Department'
    
    @patch('src.api.schemes_search.scheme_repo')
    def test_pagination_first_page(self, mock_repo, sample_schemes):
        """Test pagination on first page."""
        # Setup - create 25 schemes
        many_schemes = []
        for i in range(25):
            scheme = sample_schemes[0].model_copy()
            scheme.scheme_id = f"TEST-{i:03d}"
            many_schemes.append(scheme)
        
        mock_repo.search_schemes.return_value = many_schemes
        
        event = {
            'queryStringParameters': {
                'page': '1',
                'limit': '10'
            }
        }
        
        # Execute
        response = lambda_handler(event, None)
        
        # Verify
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert len(body['schemes']) == 10
        assert body['pagination']['page'] == 1
        assert body['pagination']['limit'] == 10
        assert body['pagination']['total'] == 25
        assert body['pagination']['has_more'] is True
    
    @patch('src.api.schemes_search.scheme_repo')
    def test_pagination_second_page(self, mock_repo, sample_schemes):
        """Test pagination on second page."""
        # Setup - create 25 schemes
        many_schemes = []
        for i in range(25):
            scheme = sample_schemes[0].model_copy()
            scheme.scheme_id = f"TEST-{i:03d}"
            many_schemes.append(scheme)
        
        mock_repo.search_schemes.return_value = many_schemes
        
        event = {
            'queryStringParameters': {
                'page': '2',
                'limit': '10'
            }
        }
        
        # Execute
        response = lambda_handler(event, None)
        
        # Verify
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert len(body['schemes']) == 10
        assert body['pagination']['page'] == 2
        assert body['pagination']['has_more'] is True
    
    @patch('src.api.schemes_search.scheme_repo')
    def test_pagination_last_page(self, mock_repo, sample_schemes):
        """Test pagination on last page with partial results."""
        # Setup - create 25 schemes
        many_schemes = []
        for i in range(25):
            scheme = sample_schemes[0].model_copy()
            scheme.scheme_id = f"TEST-{i:03d}"
            many_schemes.append(scheme)
        
        mock_repo.search_schemes.return_value = many_schemes
        
        event = {
            'queryStringParameters': {
                'page': '3',
                'limit': '10'
            }
        }
        
        # Execute
        response = lambda_handler(event, None)
        
        # Verify
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert len(body['schemes']) == 5  # Only 5 remaining
        assert body['pagination']['page'] == 3
        assert body['pagination']['has_more'] is False
    
    @patch('src.api.schemes_search.scheme_repo')
    def test_invalid_page_number(self, mock_repo):
        """Test error handling for invalid page number."""
        event = {
            'queryStringParameters': {
                'page': '0'
            }
        }
        
        # Execute
        response = lambda_handler(event, None)
        
        # Verify
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'Page number must be >= 1' in body['error']
    
    @patch('src.api.schemes_search.scheme_repo')
    def test_invalid_limit(self, mock_repo):
        """Test error handling for invalid limit."""
        event = {
            'queryStringParameters': {
                'limit': '150'
            }
        }
        
        # Execute
        response = lambda_handler(event, None)
        
        # Verify
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'between 1 and 100' in body['error']
    
    @patch('src.api.schemes_search.scheme_repo')
    def test_invalid_limit_negative(self, mock_repo):
        """Test error handling for negative limit."""
        event = {
            'queryStringParameters': {
                'limit': '-5'
            }
        }
        
        # Execute
        response = lambda_handler(event, None)
        
        # Verify
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
    
    @patch('src.api.schemes_search.scheme_repo')
    def test_database_error(self, mock_repo):
        """Test error handling for database errors."""
        # Setup
        mock_repo.search_schemes.side_effect = DynamoDBRepositoryError("Database connection failed")
        
        event = {
            'queryStringParameters': None
        }
        
        # Execute
        response = lambda_handler(event, None)
        
        # Verify
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'Failed to search schemes' in body['error']
    
    @patch('src.api.schemes_search.scheme_repo')
    def test_unexpected_error(self, mock_repo):
        """Test error handling for unexpected errors."""
        # Setup
        mock_repo.search_schemes.side_effect = Exception("Unexpected error")
        
        event = {
            'queryStringParameters': None
        }
        
        # Execute
        response = lambda_handler(event, None)
        
        # Verify
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'Internal server error' in body['error']
    
    @patch('src.api.schemes_search.scheme_repo')
    def test_empty_results(self, mock_repo):
        """Test handling of empty search results."""
        # Setup
        mock_repo.search_schemes.return_value = []
        
        event = {
            'queryStringParameters': {
                'q': 'nonexistent'
            }
        }
        
        # Execute
        response = lambda_handler(event, None)
        
        # Verify
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert len(body['schemes']) == 0
        assert body['pagination']['total'] == 0
        assert body['pagination']['has_more'] is False


class TestSchemeToSummary:
    """Test cases for the _scheme_to_summary function."""
    
    def test_scheme_to_summary_includes_required_fields(self, sample_scheme):
        """Test that summary includes all required fields."""
        summary = _scheme_to_summary(sample_scheme)
        
        assert 'scheme_id' in summary
        assert 'name' in summary
        assert 'category' in summary
        assert 'description' in summary
        assert 'department' in summary
        assert 'state' in summary
        assert 'benefits' in summary
        assert 'application_url' in summary
        assert 'last_updated' in summary
    
    def test_scheme_to_summary_excludes_verbose_fields(self, sample_scheme):
        """Test that summary excludes verbose fields."""
        summary = _scheme_to_summary(sample_scheme)
        
        # These fields should not be in summary
        assert 'name_translations' not in summary
        assert 'description_translations' not in summary
        assert 'eligibility_criteria' not in summary
        assert 'required_documents' not in summary
        assert 'application_process' not in summary
    
    def test_scheme_to_summary_datetime_serialization(self, sample_scheme):
        """Test that datetime is properly serialized to ISO format."""
        summary = _scheme_to_summary(sample_scheme)
        
        assert summary['last_updated'] == '2024-01-15T10:30:00'
        assert isinstance(summary['last_updated'], str)
    
    def test_scheme_to_summary_with_none_state(self, sample_scheme):
        """Test summary with None state (central scheme)."""
        sample_scheme.state = None
        summary = _scheme_to_summary(sample_scheme)
        
        assert summary['state'] is None
    
    def test_scheme_to_summary_with_none_application_url(self, sample_scheme):
        """Test summary with None application URL."""
        sample_scheme.application_url = None
        summary = _scheme_to_summary(sample_scheme)
        
        assert summary['application_url'] is None
