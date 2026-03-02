"""Unit tests for TranslateService."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError

from src.services.translate_service import TranslateService


@pytest.fixture
def mock_translate_client():
    """Mock boto3 translate client."""
    with patch('boto3.client') as mock_client:
        translate_mock = Mock()
        mock_client.return_value = translate_mock
        yield translate_mock


@pytest.fixture
def mock_dynamodb():
    """Mock boto3 DynamoDB resource."""
    with patch('boto3.resource') as mock_resource:
        dynamodb_mock = Mock()
        table_mock = Mock()
        dynamodb_mock.Table.return_value = table_mock
        mock_resource.return_value = dynamodb_mock
        yield table_mock


@pytest.fixture
def translate_service(mock_translate_client, mock_dynamodb):
    """Create TranslateService instance with mocked dependencies."""
    service = TranslateService()
    service.translate_client = mock_translate_client
    service.cache_table = mock_dynamodb
    return service


class TestTranslateService:
    """Test cases for TranslateService."""
    
    def test_translate_text_success(self, translate_service, mock_translate_client, mock_dynamodb):
        """Test successful text translation."""
        # Mock translate response
        mock_translate_client.translate_text.return_value = {
            'TranslatedText': 'प्रधानमंत्री किसान सम्मान निधि'
        }
        
        # Mock cache miss
        mock_dynamodb.get_item.return_value = {}
        
        result = translate_service.translate_text(
            'Pradhan Mantri Kisan Samman Nidhi',
            source_lang='en',
            target_lang='hi'
        )
        
        assert result == 'प्रधानमंत्री किसान सम्मान निधि'
        mock_translate_client.translate_text.assert_called_once()
        mock_dynamodb.put_item.assert_called_once()
    
    def test_translate_text_from_cache(self, translate_service, mock_translate_client, mock_dynamodb):
        """Test translation retrieved from cache."""
        # Mock cache hit
        mock_dynamodb.get_item.return_value = {
            'Item': {
                'cache_key': 'test_key',
                'translated_text': 'प्रधानमंत्री किसान सम्मान निधि'
            }
        }
        
        result = translate_service.translate_text(
            'Pradhan Mantri Kisan Samman Nidhi',
            source_lang='en',
            target_lang='hi'
        )
        
        assert result == 'प्रधानमंत्री किसान सम्मान निधि'
        # Should not call translate API if cached
        mock_translate_client.translate_text.assert_not_called()
    
    def test_translate_text_same_language(self, translate_service, mock_translate_client):
        """Test translation with same source and target language."""
        text = 'Hello World'
        result = translate_service.translate_text(text, source_lang='en', target_lang='en')
        
        assert result == text
        mock_translate_client.translate_text.assert_not_called()
    
    def test_translate_text_empty_input(self, translate_service):
        """Test translation with empty text."""
        with pytest.raises(ValueError, match="Text cannot be empty"):
            translate_service.translate_text('', source_lang='en', target_lang='hi')
    
    def test_translate_text_unsupported_source_language(self, translate_service):
        """Test translation with unsupported source language."""
        with pytest.raises(ValueError, match="Source language 'fr' not supported"):
            translate_service.translate_text('Hello', source_lang='fr', target_lang='hi')
    
    def test_translate_text_unsupported_target_language(self, translate_service):
        """Test translation with unsupported target language."""
        with pytest.raises(ValueError, match="Target language 'de' not supported"):
            translate_service.translate_text('Hello', source_lang='en', target_lang='de')
    
    def test_translate_text_api_error(self, translate_service, mock_translate_client, mock_dynamodb):
        """Test handling of API errors."""
        # Mock cache miss
        mock_dynamodb.get_item.return_value = {}
        
        # Mock API error
        error_response = {'Error': {'Code': 'UnsupportedLanguagePairException'}}
        mock_translate_client.translate_text.side_effect = ClientError(error_response, 'TranslateText')
        
        with pytest.raises(ValueError, match="Translation from en to hi not supported"):
            translate_service.translate_text('Hello', source_lang='en', target_lang='hi')
    
    def test_translate_text_size_limit_error(self, translate_service, mock_translate_client, mock_dynamodb):
        """Test handling of text size limit error."""
        # Mock cache miss
        mock_dynamodb.get_item.return_value = {}
        
        # Mock size limit error
        error_response = {'Error': {'Code': 'TextSizeLimitExceededException'}}
        mock_translate_client.translate_text.side_effect = ClientError(error_response, 'TranslateText')
        
        with pytest.raises(ValueError, match="Text is too long for translation"):
            translate_service.translate_text('Very long text...', source_lang='en', target_lang='hi')
    
    def test_translate_scheme_content(self, translate_service, mock_translate_client, mock_dynamodb):
        """Test translating scheme content to multiple languages."""
        # Mock cache miss
        mock_dynamodb.get_item.return_value = {}
        
        # Mock translate responses
        def translate_side_effect(*args, **kwargs):
            text = kwargs['Text']
            target = kwargs['TargetLanguageCode']
            
            translations = {
                'hi': f'{text}_hindi',
                'ta': f'{text}_tamil',
                'te': f'{text}_telugu'
            }
            return {'TranslatedText': translations.get(target, text)}
        
        mock_translate_client.translate_text.side_effect = translate_side_effect
        
        scheme_data = {
            'name': 'Test Scheme',
            'description': 'Test Description'
        }
        
        result = translate_service.translate_scheme_content(
            scheme_data,
            target_languages=['hi', 'ta', 'te']
        )
        
        assert 'name_translations' in result
        assert 'description_translations' in result
        assert result['name_translations']['hi'] == 'Test Scheme_hindi'
        assert result['name_translations']['ta'] == 'Test Scheme_tamil'
        assert result['description_translations']['hi'] == 'Test Description_hindi'
    
    def test_translate_scheme_content_partial_failure(self, translate_service, mock_translate_client, mock_dynamodb):
        """Test scheme translation with partial failures."""
        # Mock cache miss
        mock_dynamodb.get_item.return_value = {}
        
        # Mock translate with one failure
        call_count = [0]
        def translate_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 2:  # Fail on second call
                raise Exception("Translation failed")
            return {'TranslatedText': 'Translated'}
        
        mock_translate_client.translate_text.side_effect = translate_side_effect
        
        scheme_data = {
            'name': 'Test Scheme',
            'description': 'Test Description'
        }
        
        result = translate_service.translate_scheme_content(
            scheme_data,
            target_languages=['hi', 'ta']
        )
        
        # Should have some translations despite partial failure
        assert 'name_translations' in result
        assert 'description_translations' in result
    
    def test_get_supported_languages(self, translate_service):
        """Test getting list of supported languages."""
        languages = translate_service.get_supported_languages()
        
        assert isinstance(languages, list)
        assert 'hi' in languages
        assert 'en' in languages
        assert 'ta' in languages
        assert 'te' in languages
        assert 'bn' in languages
    
    def test_cache_key_generation(self, translate_service):
        """Test cache key generation is consistent."""
        key1 = translate_service._generate_cache_key('Hello', 'en', 'hi')
        key2 = translate_service._generate_cache_key('Hello', 'en', 'hi')
        key3 = translate_service._generate_cache_key('Hello', 'en', 'ta')
        
        assert key1 == key2  # Same input should generate same key
        assert key1 != key3  # Different target language should generate different key
