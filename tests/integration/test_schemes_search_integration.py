"""Integration tests for scheme search Lambda function with DynamoDB."""

import json
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from decimal import Decimal

from src.api.schemes_search import lambda_handler
from src.models.scheme import Scheme
from src.models.eligibility import EligibilityCriteria


@pytest.fixture
def mock_dynamodb_table():
    """Create a mock DynamoDB table."""
    table = MagicMock()
    return table


@pytest.fixture
def sample_dynamodb_items():
    """Create sample DynamoDB items."""
    items = []
    
    # Agriculture schemes
    for i in range(3):
        items.append({
            'scheme_id': f'AGR-{i:03d}',
            'name': f'Agriculture Scheme {i}',
            'name_translations': {},
            'category': 'agriculture',
            'description': f'Scheme for farmers {i}',
            'description_translations': {},
            'benefits': ['Benefit 1', 'Benefit 2'],
            'eligibility_criteria': {
                'age_min': Decimal('18'),
                'occupation': ['farmer']
            },
            'required_documents': ['Aadhaar'],
            'application_process': ['Step 1'],
            'application_url': 'https://example.com',
            'department': 'Agriculture Department',
            'state': 'Maharashtra',
            'last_updated': '2024-01-15T10:30:00',
            'source_url': 'https://example.com/source'
        })
    
    # Health schemes
    for i in range(2):
        items.append({
            'scheme_id': f'HLT-{i:03d}',
            'name': f'Health Scheme {i}',
            'name_translations': {},
            'category': 'health',
            'description': f'Health insurance scheme {i}',
            'description_translations': {},
            'benefits': ['Free treatment'],
            'eligibility_criteria': {
                'age_min': Decimal('0'),
                'income_max': Decimal('500000')
            },
            'required_documents': ['Aadhaar', 'Income certificate'],
            'application_process': ['Step 1', 'Step 2'],
            'application_url': 'https://health.example.com',
            'department': 'Health Department',
            'state': None,  # Central scheme
            'last_updated': '2024-01-20T15:00:00',
            'source_url': 'https://health.example.com/source'
        })
    
    return items


class TestSchemesSearchIntegration:
    """Integration tests for scheme search with mocked DynamoDB."""
    
    @patch('src.core.scheme_repository.boto3')
    def test_search_agriculture_schemes(self, mock_boto3, mock_dynamodb_table, sample_dynamodb_items):
        """Test searching for agriculture schemes."""
        # Setup mock
        mock_boto3.resource.return_value.Table.return_value = mock_dynamodb_table
        
        # Filter agriculture schemes
        agr_items = [item for item in sample_dynamodb_items if item['category'] == 'agriculture']
        mock_dynamodb_table.query.return_value = {'Items': agr_items}
        
        # Execute
        event = {
            'queryStringParameters': {
                'category': 'agriculture'
            }
        }
        
        response = lambda_handler(event, None)
        
        # Verify
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert len(body['schemes']) == 3
        assert all(s['category'] == 'agriculture' for s in body['schemes'])
    
    @patch('src.core.scheme_repository.boto3')
    def test_search_central_schemes(self, mock_boto3, mock_dynamodb_table, sample_dynamodb_items):
        """Test searching for central schemes (state is None)."""
        # Setup mock
        mock_boto3.resource.return_value.Table.return_value = mock_dynamodb_table
        
        # Filter central schemes
        central_items = [item for item in sample_dynamodb_items if item['state'] is None]
        mock_dynamodb_table.scan.return_value = {'Items': central_items}
        
        # Execute
        event = {
            'queryStringParameters': {
                'state': ''  # Empty string means central schemes
            }
        }
        
        response = lambda_handler(event, None)
        
        # Verify
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert len(body['schemes']) == 2
        assert all(s['state'] is None for s in body['schemes'])
    
    @patch('src.core.scheme_repository.boto3')
    def test_search_with_keyword(self, mock_boto3, mock_dynamodb_table, sample_dynamodb_items):
        """Test keyword search across schemes."""
        # Setup mock
        mock_boto3.resource.return_value.Table.return_value = mock_dynamodb_table
        
        # Filter schemes containing 'farmer'
        farmer_items = [item for item in sample_dynamodb_items if 'farmer' in item['description'].lower()]
        mock_dynamodb_table.scan.return_value = {'Items': farmer_items}
        
        # Execute
        event = {
            'queryStringParameters': {
                'q': 'farmer'
            }
        }
        
        response = lambda_handler(event, None)
        
        # Verify
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert len(body['schemes']) == 3
        assert all('farmer' in s['description'].lower() for s in body['schemes'])
    
    @patch('src.core.scheme_repository.boto3')
    def test_pagination_with_real_data(self, mock_boto3, mock_dynamodb_table, sample_dynamodb_items):
        """Test pagination with multiple pages."""
        # Setup mock
        mock_boto3.resource.return_value.Table.return_value = mock_dynamodb_table
        mock_dynamodb_table.scan.return_value = {'Items': sample_dynamodb_items}
        
        # Execute - Get page 1 with limit 2
        event = {
            'queryStringParameters': {
                'page': '1',
                'limit': '2'
            }
        }
        
        response = lambda_handler(event, None)
        
        # Verify
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert len(body['schemes']) == 2
        assert body['pagination']['page'] == 1
        assert body['pagination']['limit'] == 2
        assert body['pagination']['total'] == 5
        assert body['pagination']['has_more'] is True
        
        # Execute - Get page 2
        event['queryStringParameters']['page'] = '2'
        response = lambda_handler(event, None)
        
        # Verify page 2
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert len(body['schemes']) == 2
        assert body['pagination']['page'] == 2
        assert body['pagination']['has_more'] is True
        
        # Execute - Get page 3 (last page)
        event['queryStringParameters']['page'] = '3'
        response = lambda_handler(event, None)
        
        # Verify page 3
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert len(body['schemes']) == 1
        assert body['pagination']['page'] == 3
        assert body['pagination']['has_more'] is False
    
    @patch('src.core.scheme_repository.boto3')
    def test_combined_filters(self, mock_boto3, mock_dynamodb_table, sample_dynamodb_items):
        """Test combining multiple filters."""
        # Setup mock
        mock_boto3.resource.return_value.Table.return_value = mock_dynamodb_table
        
        # Filter: agriculture + Maharashtra
        filtered_items = [
            item for item in sample_dynamodb_items
            if item['category'] == 'agriculture' and item['state'] == 'Maharashtra'
        ]
        mock_dynamodb_table.query.return_value = {'Items': filtered_items}
        
        # Execute
        event = {
            'queryStringParameters': {
                'category': 'agriculture',
                'state': 'Maharashtra'
            }
        }
        
        response = lambda_handler(event, None)
        
        # Verify
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert len(body['schemes']) == 3
        assert all(s['category'] == 'agriculture' for s in body['schemes'])
        assert all(s['state'] == 'Maharashtra' for s in body['schemes'])
    
    @patch('src.core.scheme_repository.boto3')
    def test_response_format(self, mock_boto3, mock_dynamodb_table, sample_dynamodb_items):
        """Test that response format matches API specification."""
        # Setup mock
        mock_boto3.resource.return_value.Table.return_value = mock_dynamodb_table
        mock_dynamodb_table.scan.return_value = {'Items': sample_dynamodb_items[:1]}
        
        # Execute
        event = {
            'queryStringParameters': None
        }
        
        response = lambda_handler(event, None)
        
        # Verify response structure
        assert response['statusCode'] == 200
        assert 'headers' in response
        assert response['headers']['Content-Type'] == 'application/json'
        assert 'Access-Control-Allow-Origin' in response['headers']
        
        body = json.loads(response['body'])
        assert 'schemes' in body
        assert 'pagination' in body
        
        # Verify scheme structure
        scheme = body['schemes'][0]
        assert 'scheme_id' in scheme
        assert 'name' in scheme
        assert 'category' in scheme
        assert 'description' in scheme
        assert 'department' in scheme
        assert 'benefits' in scheme
        assert 'application_url' in scheme
        assert 'last_updated' in scheme
        
        # Verify pagination structure
        pagination = body['pagination']
        assert 'page' in pagination
        assert 'limit' in pagination
        assert 'total' in pagination
        assert 'has_more' in pagination
