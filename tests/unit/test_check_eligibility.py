"""Unit tests for check_eligibility Lambda function."""

import json
import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from src.api.check_eligibility import lambda_handler
from src.models.scheme import Scheme
from src.models.eligibility import EligibilityCriteria
from src.core.scheme_repository import ItemNotFoundError, DynamoDBRepositoryError


@pytest.fixture
def sample_event():
    """Create a sample API Gateway event."""
    return {
        'body': json.dumps({
            'scheme_id': 'TEST-SCHEME-001',
            'user_profile': {
                'user_id': 'test_user_123',
                'phone_number': '+919876543210',
                'language': 'hi',
                'location': {
                    'state': 'Maharashtra',
                    'district': 'Pune',
                    'pincode': '411014'
                },
                'age': 35,
                'gender': 'male',
                'education_level': 'secondary',
                'occupation': 'farmer',
                'income_bracket': '100000-300000'
            }
        }),
        'headers': {
            'Content-Type': 'application/json'
        }
    }


@pytest.fixture
def sample_scheme():
    """Create a sample scheme."""
    return Scheme(
        scheme_id='TEST-SCHEME-001',
        name='Test Farmer Scheme',
        category='agriculture',
        description='Test scheme for farmers',
        eligibility_criteria=EligibilityCriteria(
            age_min=18,
            age_max=60,
            income_max=500000,
            occupation=['farmer', 'agricultural_worker'],
            location=['Maharashtra', 'Karnataka']
        ),
        department='Test Department',
        last_updated=datetime.utcnow(),
        source_url='https://example.com'
    )


class TestCheckEligibilitySuccess:
    """Test successful eligibility check scenarios."""
    
    @patch('src.api.check_eligibility.scheme_repo')
    def test_eligible_user(self, mock_repo, sample_event, sample_scheme):
        """Test eligible user receives positive result."""
        mock_repo.get.return_value = sample_scheme
        
        response = lambda_handler(sample_event, None)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['is_eligible'] is True
        assert body['scheme_id'] == 'TEST-SCHEME-001'
        assert body['scheme_name'] == 'Test Farmer Scheme'
        assert len(body['reasoning']) > 0
        assert body['confidence'] == 1.0
    
    @patch('src.api.check_eligibility.scheme_repo')
    def test_ineligible_user_age(self, mock_repo, sample_event, sample_scheme):
        """Test ineligible user (age) receives negative result."""
        mock_repo.get.return_value = sample_scheme
        
        # Modify user age to be ineligible
        event_body = json.loads(sample_event['body'])
        event_body['user_profile']['age'] = 70
        sample_event['body'] = json.dumps(event_body)
        
        response = lambda_handler(sample_event, None)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['is_eligible'] is False
        assert any('exceeds maximum limit' in reason for reason in body['reasoning'])
    
    @patch('src.api.check_eligibility.scheme_repo')
    def test_ineligible_user_occupation(self, mock_repo, sample_event, sample_scheme):
        """Test ineligible user (occupation) receives negative result."""
        mock_repo.get.return_value = sample_scheme
        
        # Modify user occupation to be ineligible
        event_body = json.loads(sample_event['body'])
        event_body['user_profile']['occupation'] = 'teacher'
        sample_event['body'] = json.dumps(event_body)
        
        response = lambda_handler(sample_event, None)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['is_eligible'] is False
        assert any('not eligible' in reason for reason in body['reasoning'])
    
    @patch('src.api.check_eligibility.scheme_repo')
    def test_missing_profile_data(self, mock_repo, sample_event, sample_scheme):
        """Test user with missing profile data."""
        mock_repo.get.return_value = sample_scheme
        
        # Remove age from profile
        event_body = json.loads(sample_event['body'])
        del event_body['user_profile']['age']
        sample_event['body'] = json.dumps(event_body)
        
        response = lambda_handler(sample_event, None)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['is_eligible'] is False
        assert len(body['missing_criteria']) > 0
        assert body['confidence'] < 1.0


class TestCheckEligibilityErrors:
    """Test error handling scenarios."""
    
    def test_missing_body(self):
        """Test request with missing body."""
        event = {'headers': {}}
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'body is required' in body['error'].lower()
    
    def test_invalid_json(self):
        """Test request with invalid JSON."""
        event = {
            'body': 'invalid json {',
            'headers': {}
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'invalid json' in body['error'].lower()
    
    def test_missing_scheme_id(self, sample_event):
        """Test request with missing scheme_id."""
        event_body = json.loads(sample_event['body'])
        del event_body['scheme_id']
        sample_event['body'] = json.dumps(event_body)
        
        response = lambda_handler(sample_event, None)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'scheme_id' in body['error'].lower()
    
    def test_missing_user_profile(self, sample_event):
        """Test request with missing user_profile."""
        event_body = json.loads(sample_event['body'])
        del event_body['user_profile']
        sample_event['body'] = json.dumps(event_body)
        
        response = lambda_handler(sample_event, None)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'user_profile' in body['error'].lower()
    
    def test_invalid_user_profile(self, sample_event):
        """Test request with invalid user_profile."""
        event_body = json.loads(sample_event['body'])
        del event_body['user_profile']['location']
        sample_event['body'] = json.dumps(event_body)
        
        response = lambda_handler(sample_event, None)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'user_profile' in body['error'].lower()
    
    @patch('src.api.check_eligibility.scheme_repo')
    def test_scheme_not_found(self, mock_repo, sample_event):
        """Test request for non-existent scheme."""
        mock_repo.get.side_effect = ItemNotFoundError("Scheme not found")
        
        response = lambda_handler(sample_event, None)
        
        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'not found' in body['error'].lower()
    
    @patch('src.api.check_eligibility.scheme_repo')
    def test_database_error(self, mock_repo, sample_event):
        """Test database error handling."""
        mock_repo.get.side_effect = DynamoDBRepositoryError("Database error")
        
        response = lambda_handler(sample_event, None)
        
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert 'error' in body
    
    @patch('src.api.check_eligibility.scheme_repo')
    def test_unexpected_error(self, mock_repo, sample_event):
        """Test unexpected error handling."""
        mock_repo.get.side_effect = Exception("Unexpected error")
        
        response = lambda_handler(sample_event, None)
        
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert 'error' in body


class TestResponseFormat:
    """Test response format and structure."""
    
    @patch('src.api.check_eligibility.scheme_repo')
    def test_response_has_cors_headers(self, mock_repo, sample_event, sample_scheme):
        """Test response includes CORS headers."""
        mock_repo.get.return_value = sample_scheme
        
        response = lambda_handler(sample_event, None)
        
        assert 'headers' in response
        assert 'Access-Control-Allow-Origin' in response['headers']
        assert response['headers']['Access-Control-Allow-Origin'] == '*'
    
    @patch('src.api.check_eligibility.scheme_repo')
    def test_response_has_content_type(self, mock_repo, sample_event, sample_scheme):
        """Test response includes Content-Type header."""
        mock_repo.get.return_value = sample_scheme
        
        response = lambda_handler(sample_event, None)
        
        assert 'headers' in response
        assert 'Content-Type' in response['headers']
        assert response['headers']['Content-Type'] == 'application/json'
    
    @patch('src.api.check_eligibility.scheme_repo')
    def test_response_body_is_json(self, mock_repo, sample_event, sample_scheme):
        """Test response body is valid JSON."""
        mock_repo.get.return_value = sample_scheme
        
        response = lambda_handler(sample_event, None)
        
        assert 'body' in response
        # Should not raise exception
        body = json.loads(response['body'])
        assert isinstance(body, dict)
    
    @patch('src.api.check_eligibility.scheme_repo')
    def test_success_response_structure(self, mock_repo, sample_event, sample_scheme):
        """Test success response has all required fields."""
        mock_repo.get.return_value = sample_scheme
        
        response = lambda_handler(sample_event, None)
        body = json.loads(response['body'])
        
        assert 'is_eligible' in body
        assert 'reasoning' in body
        assert 'missing_criteria' in body
        assert 'confidence' in body
        assert 'scheme_id' in body
        assert 'scheme_name' in body
        
        assert isinstance(body['is_eligible'], bool)
        assert isinstance(body['reasoning'], list)
        assert isinstance(body['missing_criteria'], list)
        assert isinstance(body['confidence'], (int, float))
        assert isinstance(body['scheme_id'], str)
        assert isinstance(body['scheme_name'], str)
