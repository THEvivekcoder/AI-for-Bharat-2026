"""
Integration tests for conversational query endpoint (POST /ask)
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.api.conversational_query import lambda_handler


@pytest.fixture
def mock_rag_engine():
    """Mock RAG engine"""
    with patch('src.api.conversational_query.RAGEngine') as mock:
        instance = Mock()
        mock.return_value = instance
        yield instance


@pytest.fixture
def mock_conversation_manager():
    """Mock conversation manager"""
    with patch('src.api.conversational_query.ConversationManager') as mock:
        instance = Mock()
        mock.return_value = instance
        yield instance


@pytest.fixture
def mock_extract_user_id():
    """Mock user ID extraction"""
    with patch('src.api.conversational_query.extract_user_id') as mock:
        mock.return_value = 'test-user-123'
        yield mock


@pytest.fixture
def valid_event():
    """Valid API Gateway event"""
    return {
        'body': json.dumps({
            'query': 'What schemes are available for farmers?',
            'language': 'hi'
        }),
        'headers': {
            'Authorization': 'Bearer valid-token'
        }
    }


def test_conversational_query_success(valid_event, mock_rag_engine, 
                                     mock_conversation_manager, mock_extract_user_id):
    """Test successful conversational query"""
    # Setup mocks
    session_id = 'session-123'
    mock_conversation_manager.create_session.return_value = session_id
    
    mock_context = Mock()
    mock_context.session_id = session_id
    mock_context.user_id = 'test-user-123'
    mock_context.language = 'hi'
    mock_context.history = []
    mock_conversation_manager.get_context.return_value = mock_context
    
    mock_rag_response = Mock()
    mock_rag_response.answer = 'Here are some schemes for farmers...'
    mock_rag_response.sources = [
        {
            'scheme_id': 'scheme-1',
            'name': 'PM-KISAN',
            'category': 'agriculture',
            'relevance_score': 0.95,
            'source_type': 'official'
        }
    ]
    mock_rag_response.confidence = 0.92
    mock_rag_response.session_id = session_id
    mock_rag_engine.query.return_value = mock_rag_response
    
    # Execute
    response = lambda_handler(valid_event, None)
    
    # Verify
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert 'answer' in body
    assert 'sources' in body
    assert 'confidence' in body
    assert 'session_id' in body
    assert body['session_id'] == session_id
    assert len(body['sources']) > 0
    assert body['sources'][0]['source_type'] == 'official'
    
    # Verify conversation was updated
    mock_conversation_manager.add_turn.assert_called_once()


def test_conversational_query_with_existing_session(valid_event, mock_rag_engine,
                                                    mock_conversation_manager, mock_extract_user_id):
    """Test query with existing session"""
    # Add session_id to request
    body = json.loads(valid_event['body'])
    body['session_id'] = 'existing-session-123'
    valid_event['body'] = json.dumps(body)
    
    # Setup mocks
    mock_context = Mock()
    mock_context.session_id = 'existing-session-123'
    mock_context.user_id = 'test-user-123'
    mock_context.language = 'hi'
    mock_context.history = [
        Mock(user_message='Previous question', assistant_message='Previous answer')
    ]
    mock_conversation_manager.get_context.return_value = mock_context
    
    mock_rag_response = Mock()
    mock_rag_response.answer = 'Based on our previous conversation...'
    mock_rag_response.sources = []
    mock_rag_response.confidence = 0.85
    mock_rag_response.session_id = 'existing-session-123'
    mock_rag_engine.query.return_value = mock_rag_response
    
    # Execute
    response = lambda_handler(valid_event, None)
    
    # Verify
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['session_id'] == 'existing-session-123'
    
    # Verify existing session was used
    mock_conversation_manager.get_context.assert_called_with('existing-session-123')
    mock_conversation_manager.create_session.assert_not_called()


def test_conversational_query_missing_query(mock_extract_user_id):
    """Test request with missing query"""
    event = {
        'body': json.dumps({
            'language': 'hi'
        }),
        'headers': {
            'Authorization': 'Bearer valid-token'
        }
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert body['error'] == 'INVALID_REQUEST'
    assert 'Query is required' in body['message']


def test_conversational_query_empty_query(mock_extract_user_id):
    """Test request with empty query"""
    event = {
        'body': json.dumps({
            'query': '   ',
            'language': 'hi'
        }),
        'headers': {
            'Authorization': 'Bearer valid-token'
        }
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert body['error'] == 'INVALID_REQUEST'


def test_conversational_query_unauthorized():
    """Test request without authentication"""
    with patch('src.api.conversational_query.extract_user_id') as mock_auth:
        mock_auth.return_value = None
        
        event = {
            'body': json.dumps({
                'query': 'What schemes are available?'
            }),
            'headers': {}
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 401
        body = json.loads(response['body'])
        assert body['error'] == 'UNAUTHORIZED'


def test_conversational_query_with_source_citations(valid_event, mock_rag_engine,
                                                    mock_conversation_manager, mock_extract_user_id):
    """Test that response includes source citations"""
    # Setup mocks
    session_id = 'session-123'
    mock_conversation_manager.create_session.return_value = session_id
    
    mock_context = Mock()
    mock_context.session_id = session_id
    mock_conversation_manager.get_context.return_value = mock_context
    
    mock_rag_response = Mock()
    mock_rag_response.answer = 'Response with citations'
    mock_rag_response.sources = [
        {
            'scheme_id': 'scheme-1',
            'name': 'PM-KISAN',
            'category': 'agriculture',
            'relevance_score': 0.95,
            'source_type': 'official'
        },
        {
            'scheme_id': 'scheme-2',
            'name': 'Kisan Credit Card',
            'category': 'agriculture',
            'relevance_score': 0.88,
            'source_type': 'official'
        }
    ]
    mock_rag_response.confidence = 0.91
    mock_rag_response.session_id = session_id
    mock_rag_engine.query.return_value = mock_rag_response
    
    # Execute
    response = lambda_handler(valid_event, None)
    
    # Verify
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert len(body['sources']) == 2
    
    # Verify source structure
    for source in body['sources']:
        assert 'scheme_id' in source
        assert 'name' in source
        assert 'category' in source
        assert 'relevance_score' in source
        assert 'source_type' in source


def test_conversational_query_session_creation_failure(valid_event, mock_rag_engine,
                                                       mock_conversation_manager, mock_extract_user_id):
    """Test handling of session creation failure"""
    # Setup mocks
    mock_conversation_manager.create_session.return_value = 'session-123'
    mock_conversation_manager.get_context.return_value = None  # Simulate failure
    
    # Execute
    response = lambda_handler(valid_event, None)
    
    # Verify
    assert response['statusCode'] == 500
    body = json.loads(response['body'])
    assert body['error'] == 'SESSION_ERROR'


def test_conversational_query_rag_error(valid_event, mock_rag_engine,
                                       mock_conversation_manager, mock_extract_user_id):
    """Test handling of RAG engine errors"""
    # Setup mocks
    session_id = 'session-123'
    mock_conversation_manager.create_session.return_value = session_id
    
    mock_context = Mock()
    mock_context.session_id = session_id
    mock_conversation_manager.get_context.return_value = mock_context
    
    # Simulate RAG error
    mock_rag_engine.query.side_effect = Exception('RAG processing failed')
    
    # Execute
    response = lambda_handler(valid_event, None)
    
    # Verify
    assert response['statusCode'] == 500
    body = json.loads(response['body'])
    assert body['error'] == 'INTERNAL_ERROR'


def test_conversational_query_default_language(mock_rag_engine, mock_conversation_manager, 
                                               mock_extract_user_id):
    """Test that default language is Hindi when not specified"""
    event = {
        'body': json.dumps({
            'query': 'What schemes are available?'
        }),
        'headers': {
            'Authorization': 'Bearer valid-token'
        }
    }
    
    # Setup mocks
    session_id = 'session-123'
    mock_conversation_manager.create_session.return_value = session_id
    
    mock_context = Mock()
    mock_context.session_id = session_id
    mock_context.language = 'hi'
    mock_conversation_manager.get_context.return_value = mock_context
    
    mock_rag_response = Mock()
    mock_rag_response.answer = 'Response'
    mock_rag_response.sources = []
    mock_rag_response.confidence = 0.8
    mock_rag_response.session_id = session_id
    mock_rag_engine.query.return_value = mock_rag_response
    
    # Execute
    response = lambda_handler(event, None)
    
    # Verify
    assert response['statusCode'] == 200
    
    # Verify session was created with Hindi as default
    mock_conversation_manager.create_session.assert_called_once_with('test-user-123', 'hi')


def test_conversational_query_cors_headers(valid_event, mock_rag_engine,
                                           mock_conversation_manager, mock_extract_user_id):
    """Test that CORS headers are included in response"""
    # Setup mocks
    session_id = 'session-123'
    mock_conversation_manager.create_session.return_value = session_id
    
    mock_context = Mock()
    mock_context.session_id = session_id
    mock_conversation_manager.get_context.return_value = mock_context
    
    mock_rag_response = Mock()
    mock_rag_response.answer = 'Response'
    mock_rag_response.sources = []
    mock_rag_response.confidence = 0.8
    mock_rag_response.session_id = session_id
    mock_rag_engine.query.return_value = mock_rag_response
    
    # Execute
    response = lambda_handler(valid_event, None)
    
    # Verify CORS headers
    assert 'Access-Control-Allow-Origin' in response['headers']
    assert response['headers']['Access-Control-Allow-Origin'] == '*'
    assert response['headers']['Content-Type'] == 'application/json'
