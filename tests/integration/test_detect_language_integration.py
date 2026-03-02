"""Integration tests for language detection API."""
import json
import pytest
from unittest.mock import Mock, patch
from src.api.detect_language import lambda_handler


@pytest.fixture
def mock_comprehend_service():
    """Mock ComprehendService for integration tests."""
    with patch('src.api.detect_language.ComprehendService') as mock_service_class:
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        yield mock_service


def test_detect_language_single_text_success(mock_comprehend_service):
    """Test language detection API with single text."""
    # Mock service response
    mock_comprehend_service.detect_language.return_value = {
        'language_code': 'hi-IN',
        'confidence': 0.98,
        'all_languages': [
            {'language_code': 'hi-IN', 'confidence': 0.98},
            {'language_code': 'en-IN', 'confidence': 0.02}
        ]
    }
    
    # Create API event
    event = {
        'body': json.dumps({
            'text': 'नमस्ते, आप कैसे हैं?'
        })
    }
    
    # Call Lambda handler
    response = lambda_handler(event, None)
    
    # Verify response
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['language_code'] == 'hi-IN'
    assert body['confidence'] == 0.98
    assert len(body['all_languages']) == 2


def test_detect_language_batch_texts_success(mock_comprehend_service):
    """Test language detection API with batch texts."""
    # Mock service response
    mock_comprehend_service.detect_language_batch.return_value = [
        {
            'language_code': 'hi-IN',
            'confidence': 0.98,
            'all_languages': [{'language_code': 'hi-IN', 'confidence': 0.98}]
        },
        {
            'language_code': 'en-IN',
            'confidence': 0.95,
            'all_languages': [{'language_code': 'en-IN', 'confidence': 0.95}]
        }
    ]
    
    # Create API event
    event = {
        'body': json.dumps({
            'texts': ['नमस्ते', 'Hello']
        })
    }
    
    # Call Lambda handler
    response = lambda_handler(event, None)
    
    # Verify response
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert 'results' in body
    assert len(body['results']) == 2
    assert body['results'][0]['language_code'] == 'hi-IN'
    assert body['results'][1]['language_code'] == 'en-IN'


def test_detect_language_missing_text(mock_comprehend_service):
    """Test API with missing text parameter."""
    event = {
        'body': json.dumps({})
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert 'error' in body
    assert 'text or texts is required' in body['error']


def test_detect_language_invalid_texts_type(mock_comprehend_service):
    """Test API with invalid texts parameter type."""
    event = {
        'body': json.dumps({
            'texts': 'not a list'
        })
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert 'error' in body
    assert 'texts must be a list' in body['error']


def test_detect_language_too_many_texts(mock_comprehend_service):
    """Test API with more than 25 texts."""
    event = {
        'body': json.dumps({
            'texts': ['text'] * 30
        })
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert 'error' in body
    assert 'maximum 25 texts' in body['error']


def test_detect_language_service_error(mock_comprehend_service):
    """Test API handling of service errors."""
    mock_comprehend_service.detect_language.side_effect = Exception('Service error')
    
    event = {
        'body': json.dumps({
            'text': 'Test text'
        })
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 500
    body = json.loads(response['body'])
    assert 'error' in body


def test_detect_language_empty_body(mock_comprehend_service):
    """Test API with empty request body."""
    event = {}
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert 'error' in body
