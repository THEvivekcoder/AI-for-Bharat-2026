"""Unit tests for eligible_schemes Lambda function."""

import json
import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from src.api.eligible_schemes import lambda_handler
from src.models.scheme import Scheme
from src.models.eligibility import EligibilityCriteria
from src.core.scheme_repository import DynamoDBRepositoryError


@pytest.fixture
def sample_event():
    """Create a sample API Gateway event."""
    return {
        'body': json.dumps({
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
                'income_bracket': '100000-300000',
                'preferences': {
                    'preferred_categories': ['agriculture']
                }
            }
        }),
        'headers': {
            'Content-Type': 'application/json'
        }
    }


@pytest.fixture
def sample_schemes():
    """Create sample schemes for testing."""
    return [
        Scheme(
            scheme_id='SCHEME-001',
            name='Farmer Support Scheme',
            category='agriculture',
            description='Support for farmers',
            eligibility_criteria=EligibilityCriteria(
                age_min=18,
                age_max=60,
                occupation=['farmer'],
                location=['Maharashtra']
            ),
            department='Agriculture Department',
            state='Maharashtra',
            last_updated=datetime.utcnow(),
            source_url='https://example.com'
        ),
        Scheme(
            scheme_id='SCHEME-002',
            name='National Farmer Scheme',
            category='agriculture',
            description='National scheme for all farmers',
            eligibility_criteria=EligibilityCriteria(
                age_min=18,
                occupation=['farmer']
            ),
            department='Central Agriculture',
            state=None,  # Central scheme
            last_updated=datetime.utcnow(),
            source_url='https://example.com'
        ),
        Scheme(
            scheme_id='SCHEME-003',
            name='Teacher Training Scheme',
            category='education',
            description='Training for teachers',
            eligibility_criteria=EligibilityCriteria(
                occupation=['teacher']
            ),
            department='Education Department',
            state='Maharashtra',
            last_updated=datetime.utcnow(),
            source_url='https://example.com'
        )
    ]


class TestEligibleSchemesSuccess:
    """Test successful eligible schemes retrieval."""
    
    @patch('src.api.eligible_schemes.scheme_repo')
    def test_returns_eligible_schemes(self, mock_repo, sample_event, sample_schemes):
        """Test returns only eligible schemes."""
        mock_repo.get_all_schemes.return_value = sample_schemes
        
        response = lambda_handler(sample_event, None)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        
        # Should return 2 schemes (farmer schemes), not the teacher scheme
        assert body['total_count'] == 2
        assert len(body['eligible_schemes']) == 2
        
        scheme_ids = [s['scheme_id'] for s in body['eligible_schemes']]
        assert 'SCHEME-001' in scheme_ids
        assert 'SCHEME-002' in scheme_ids
        assert 'SCHEME-003' not in scheme_ids
    
    @patch('src.api.eligible_schemes.scheme_repo')
    def test_schemes_ranked_by_relevance(self, mock_repo, sample_event, sample_schemes):
        """Test schemes are ranked by relevance."""
        mock_repo.get_all_schemes.return_value = sample_schemes
        
        response = lambda_handler(sample_event, None)
        body = json.loads(response['body'])
        
        # State-specific scheme should rank higher than central scheme
        # (assuming user is from Maharashtra)
        schemes = body['eligible_schemes']
        assert schemes[0]['scheme_id'] == 'SCHEME-001'  # State scheme
        assert schemes[0]['relevance_score'] > schemes[1]['relevance_score']
    
    @patch('src.api.eligible_schemes.scheme_repo')
    def test_includes_eligibility_explanation(self, mock_repo, sample_event, sample_schemes):
        """Test each scheme includes eligibility explanation."""
        mock_repo.get_all_schemes.return_value = sample_schemes
        
        response = lambda_handler(sample_event, None)
        body = json.loads(response['body'])
        
        for scheme in body['eligible_schemes']:
            assert 'eligibility_explanation' in scheme
            explanation = scheme['eligibility_explanation']
            assert 'is_eligible' in explanation
            assert 'reasoning' in explanation
            assert 'confidence' in explanation
            assert explanation['is_eligible'] is True
    
    @patch('src.api.eligible_schemes.scheme_repo')
    def test_includes_scheme_details(self, mock_repo, sample_event, sample_schemes):
        """Test each scheme includes complete details."""
        mock_repo.get_all_schemes.return_value = sample_schemes
        
        response = lambda_handler(sample_event, None)
        body = json.loads(response['body'])
        
        for scheme in body['eligible_schemes']:
            assert 'scheme_id' in scheme
            assert 'name' in scheme
            assert 'category' in scheme
            assert 'description' in scheme
            assert 'benefits' in scheme
            assert 'required_documents' in scheme
            assert 'application_process' in scheme
            assert 'department' in scheme
    
    @patch('src.api.eligible_schemes.scheme_repo')
    def test_category_filter(self, mock_repo, sample_event, sample_schemes):
        """Test filtering by category."""
        mock_repo.get_all_schemes.return_value = sample_schemes
        
        # Add category filter
        event_body = json.loads(sample_event['body'])
        event_body['category'] = 'agriculture'
        sample_event['body'] = json.dumps(event_body)
        
        response = lambda_handler(sample_event, None)
        
        # Verify get_all_schemes was called with category filter
        mock_repo.get_all_schemes.assert_called_once()
        call_kwargs = mock_repo.get_all_schemes.call_args[1]
        assert call_kwargs['category'] == 'agriculture'
    
    @patch('src.api.eligible_schemes.scheme_repo')
    def test_limit_parameter(self, mock_repo, sample_event, sample_schemes):
        """Test limit parameter restricts results."""
        # Create more schemes
        many_schemes = sample_schemes * 10  # 30 schemes
        mock_repo.get_all_schemes.return_value = many_schemes
        
        # Set limit to 5
        event_body = json.loads(sample_event['body'])
        event_body['limit'] = 5
        sample_event['body'] = json.dumps(event_body)
        
        response = lambda_handler(sample_event, None)
        body = json.loads(response['body'])
        
        # Should return at most 5 schemes
        assert len(body['eligible_schemes']) <= 5
    
    @patch('src.api.eligible_schemes.scheme_repo')
    def test_no_eligible_schemes(self, mock_repo, sample_event):
        """Test when no schemes are eligible."""
        # Return schemes that user is not eligible for
        ineligible_scheme = Scheme(
            scheme_id='SCHEME-999',
            name='Teacher Only Scheme',
            category='education',
            description='Only for teachers',
            eligibility_criteria=EligibilityCriteria(
                occupation=['teacher']
            ),
            department='Education',
            last_updated=datetime.utcnow(),
            source_url='https://example.com'
        )
        mock_repo.get_all_schemes.return_value = [ineligible_scheme]
        
        response = lambda_handler(sample_event, None)
        body = json.loads(response['body'])
        
        assert body['total_count'] == 0
        assert len(body['eligible_schemes']) == 0


class TestEligibleSchemesErrors:
    """Test error handling scenarios."""
    
    def test_missing_body(self):
        """Test request with missing body."""
        event = {'headers': {}}
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
    
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
    
    def test_invalid_limit_too_small(self, sample_event):
        """Test invalid limit (too small)."""
        event_body = json.loads(sample_event['body'])
        event_body['limit'] = 0
        sample_event['body'] = json.dumps(event_body)
        
        response = lambda_handler(sample_event, None)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'limit' in body['error'].lower()
    
    def test_invalid_limit_too_large(self, sample_event):
        """Test invalid limit (too large)."""
        event_body = json.loads(sample_event['body'])
        event_body['limit'] = 200
        sample_event['body'] = json.dumps(event_body)
        
        response = lambda_handler(sample_event, None)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'limit' in body['error'].lower()
    
    def test_invalid_limit_type(self, sample_event):
        """Test invalid limit type."""
        event_body = json.loads(sample_event['body'])
        event_body['limit'] = 'invalid'
        sample_event['body'] = json.dumps(event_body)
        
        response = lambda_handler(sample_event, None)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
    
    @patch('src.api.eligible_schemes.scheme_repo')
    def test_database_error(self, mock_repo, sample_event):
        """Test database error handling."""
        mock_repo.get_all_schemes.side_effect = DynamoDBRepositoryError("Database error")
        
        response = lambda_handler(sample_event, None)
        
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert 'error' in body
    
    @patch('src.api.eligible_schemes.scheme_repo')
    def test_unexpected_error(self, mock_repo, sample_event):
        """Test unexpected error handling."""
        mock_repo.get_all_schemes.side_effect = Exception("Unexpected error")
        
        response = lambda_handler(sample_event, None)
        
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert 'error' in body


class TestResponseFormat:
    """Test response format and structure."""
    
    @patch('src.api.eligible_schemes.scheme_repo')
    def test_response_has_cors_headers(self, mock_repo, sample_event, sample_schemes):
        """Test response includes CORS headers."""
        mock_repo.get_all_schemes.return_value = sample_schemes
        
        response = lambda_handler(sample_event, None)
        
        assert 'headers' in response
        assert 'Access-Control-Allow-Origin' in response['headers']
        assert response['headers']['Access-Control-Allow-Origin'] == '*'
    
    @patch('src.api.eligible_schemes.scheme_repo')
    def test_response_structure(self, mock_repo, sample_event, sample_schemes):
        """Test response has all required fields."""
        mock_repo.get_all_schemes.return_value = sample_schemes
        
        response = lambda_handler(sample_event, None)
        body = json.loads(response['body'])
        
        assert 'eligible_schemes' in body
        assert 'total_count' in body
        assert 'user_location' in body
        
        assert isinstance(body['eligible_schemes'], list)
        assert isinstance(body['total_count'], int)
        assert isinstance(body['user_location'], str)
    
    @patch('src.api.eligible_schemes.scheme_repo')
    def test_user_location_format(self, mock_repo, sample_event, sample_schemes):
        """Test user_location is formatted correctly."""
        mock_repo.get_all_schemes.return_value = sample_schemes
        
        response = lambda_handler(sample_event, None)
        body = json.loads(response['body'])
        
        assert body['user_location'] == 'Maharashtra/Pune'
    
    @patch('src.api.eligible_schemes.scheme_repo')
    def test_relevance_score_format(self, mock_repo, sample_event, sample_schemes):
        """Test relevance_score is properly formatted."""
        mock_repo.get_all_schemes.return_value = sample_schemes
        
        response = lambda_handler(sample_event, None)
        body = json.loads(response['body'])
        
        for scheme in body['eligible_schemes']:
            assert 'relevance_score' in scheme
            assert isinstance(scheme['relevance_score'], (int, float))
            assert 0.0 <= scheme['relevance_score'] <= 1.0
