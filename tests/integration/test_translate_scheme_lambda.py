"""Integration test for translate_scheme Lambda function."""

import json
import pytest
from unittest.mock import Mock, patch

from src.api.translate_scheme import lambda_handler


@pytest.fixture
def mock_translate_service():
    """Mock TranslateService."""
    with patch('src.api.translate_scheme.TranslateService') as mock_service_class:
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        
        # Mock get_supported_languages
        mock_service.get_supported_languages.return_value = ['hi', 'en', 'ta', 'te', 'bn']
        
        # Mock translate_scheme_content
        mock_service.translate_scheme_content.return_value = {
            'name_translations': {
                'hi': 'प्रधानमंत्री किसान सम्मान निधि',
                'ta': 'பிரதம மந்திரி கிசான் சம்மான் நிதி',
                'te': 'ప్రధాన మంత్రి కిసాన్ సమ్మాన్ నిధి',
                'bn': 'প্রধানমন্ত্রী কিষাণ সম্মান নিধি'
            },
            'description_translations': {
                'hi': 'किसानों के लिए आय सहायता योजना',
                'ta': 'விவசாயிகளுக்கு வருமான ஆதரவு திட்டம்',
                'te': 'రైతులకు ఆదాయ మద్దతు పథకం',
                'bn': 'কৃষকদের জন্য আয় সহায়তা প্রকল্প'
            }
        }
        
        yield mock_service


class TestTranslateSchemeLambda:
    """Test cases for translate_scheme Lambda function."""
    
    def test_translate_scheme_success(self, mock_translate_service):
        """Test successful scheme translation."""
        event = {
            'body': json.dumps({
                'scheme_id': 'PM-KISAN-2024',
                'name': 'Pradhan Mantri Kisan Samman Nidhi',
                'description': 'Income support scheme for farmers',
                'target_languages': ['hi', 'ta', 'te', 'bn']
            })
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        
        assert body['scheme_id'] == 'PM-KISAN-2024'
        assert 'name_translations' in body
        assert 'description_translations' in body
        assert 'hi' in body['name_translations']
        assert 'ta' in body['name_translations']
        assert 'te' in body['name_translations']
        assert 'bn' in body['name_translations']
        
        # Verify service was called correctly
        mock_translate_service.translate_scheme_content.assert_called_once()
        call_args = mock_translate_service.translate_scheme_content.call_args
        assert call_args[0][0]['name'] == 'Pradhan Mantri Kisan Samman Nidhi'
        assert call_args[0][0]['description'] == 'Income support scheme for farmers'
        assert call_args[0][1] == ['hi', 'ta', 'te', 'bn']
    
    def test_translate_scheme_missing_scheme_id(self, mock_translate_service):
        """Test translation with missing scheme_id."""
        event = {
            'body': json.dumps({
                'name': 'Test Scheme',
                'description': 'Test Description',
                'target_languages': ['hi']
            })
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'scheme_id is required' in body['error']
    
    def test_translate_scheme_missing_name(self, mock_translate_service):
        """Test translation with missing name."""
        event = {
            'body': json.dumps({
                'scheme_id': 'TEST-001',
                'description': 'Test Description',
                'target_languages': ['hi']
            })
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'name and description are required' in body['error']
    
    def test_translate_scheme_missing_description(self, mock_translate_service):
        """Test translation with missing description."""
        event = {
            'body': json.dumps({
                'scheme_id': 'TEST-001',
                'name': 'Test Scheme',
                'target_languages': ['hi']
            })
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'name and description are required' in body['error']
    
    def test_translate_scheme_unsupported_language(self, mock_translate_service):
        """Test translation with unsupported language."""
        event = {
            'body': json.dumps({
                'scheme_id': 'TEST-001',
                'name': 'Test Scheme',
                'description': 'Test Description',
                'target_languages': ['fr', 'de']  # Unsupported languages
            })
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'Unsupported languages' in body['error']
        assert 'supported_languages' in body
    
    def test_translate_scheme_default_languages(self, mock_translate_service):
        """Test translation with default target languages."""
        event = {
            'body': json.dumps({
                'scheme_id': 'TEST-001',
                'name': 'Test Scheme',
                'description': 'Test Description'
                # No target_languages specified
            })
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 200
        
        # Verify default languages were used
        call_args = mock_translate_service.translate_scheme_content.call_args
        assert call_args[0][1] == ['hi', 'ta', 'te', 'bn']
    
    def test_translate_scheme_with_string_body(self, mock_translate_service):
        """Test translation when body is already a string."""
        event = {
            'body': json.dumps({
                'scheme_id': 'TEST-001',
                'name': 'Test Scheme',
                'description': 'Test Description',
                'target_languages': ['hi']
            })
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['scheme_id'] == 'TEST-001'
    
    def test_translate_scheme_with_dict_body(self, mock_translate_service):
        """Test translation when body is already a dict."""
        event = {
            'body': {
                'scheme_id': 'TEST-001',
                'name': 'Test Scheme',
                'description': 'Test Description',
                'target_languages': ['hi']
            }
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['scheme_id'] == 'TEST-001'
    
    def test_translate_scheme_service_error(self, mock_translate_service):
        """Test handling of service errors."""
        mock_translate_service.translate_scheme_content.side_effect = Exception("Translation service error")
        
        event = {
            'body': json.dumps({
                'scheme_id': 'TEST-001',
                'name': 'Test Scheme',
                'description': 'Test Description',
                'target_languages': ['hi']
            })
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert 'error' in body
        assert body['error'] == 'Internal server error'
    
    def test_translate_scheme_partial_language_list(self, mock_translate_service):
        """Test translation with partial language list."""
        event = {
            'body': json.dumps({
                'scheme_id': 'TEST-001',
                'name': 'Test Scheme',
                'description': 'Test Description',
                'target_languages': ['hi', 'ta']  # Only 2 languages
            })
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 200
        
        # Verify only requested languages were used
        call_args = mock_translate_service.translate_scheme_content.call_args
        assert call_args[0][1] == ['hi', 'ta']
    
    @patch.dict('os.environ', {'UPDATE_DYNAMODB': 'true'})
    @patch('src.api.translate_scheme._update_scheme_translations')
    def test_translate_scheme_updates_dynamodb(self, mock_update, mock_translate_service):
        """Test that translations are updated in DynamoDB when enabled."""
        event = {
            'body': json.dumps({
                'scheme_id': 'TEST-001',
                'name': 'Test Scheme',
                'description': 'Test Description',
                'target_languages': ['hi']
            })
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 200
        
        # Verify DynamoDB update was called
        mock_update.assert_called_once()
        call_args = mock_update.call_args
        assert call_args[0][0] == 'TEST-001'
        assert 'name_translations' in call_args[0][1]
        assert 'description_translations' in call_args[0][1]
