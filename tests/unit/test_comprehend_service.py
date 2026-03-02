"""Unit tests for Amazon Comprehend service."""
import pytest
from unittest.mock import Mock, patch
from botocore.exceptions import ClientError
from src.services.comprehend_service import ComprehendService


@pytest.fixture
def comprehend_service():
    """Create ComprehendService instance with mocked client."""
    with patch('boto3.client') as mock_boto_client:
        mock_comprehend = Mock()
        mock_boto_client.return_value = mock_comprehend
        
        service = ComprehendService(region='ap-south-1')
        service.comprehend_client = mock_comprehend
        
        yield service


def test_detect_language_hindi(comprehend_service):
    """Test detecting Hindi language."""
    comprehend_service.comprehend_client.detect_dominant_language = Mock(
        return_value={
            'Languages': [
                {'LanguageCode': 'hi', 'Score': 0.98},
                {'LanguageCode': 'en', 'Score': 0.02}
            ]
        }
    )
    
    result = comprehend_service.detect_language('नमस्ते, आप कैसे हैं?')
    
    assert result['language_code'] == 'hi-IN'
    assert result['confidence'] == 0.98
    assert len(result['all_languages']) == 2
    assert result['all_languages'][0]['language_code'] == 'hi-IN'
    assert result['all_languages'][0]['confidence'] == 0.98


def test_detect_language_english(comprehend_service):
    """Test detecting English language."""
    comprehend_service.comprehend_client.detect_dominant_language = Mock(
        return_value={
            'Languages': [
                {'LanguageCode': 'en', 'Score': 0.99}
            ]
        }
    )
    
    result = comprehend_service.detect_language('Hello, how are you?')
    
    assert result['language_code'] == 'en-IN'
    assert result['confidence'] == 0.99


def test_detect_language_empty_text(comprehend_service):
    """Test detecting language with empty text."""
    result = comprehend_service.detect_language('')
    
    assert result['language_code'] == 'unknown'
    assert result['confidence'] == 0.0
    assert result['all_languages'] == []


def test_detect_language_whitespace_only(comprehend_service):
    """Test detecting language with whitespace-only text."""
    result = comprehend_service.detect_language('   ')
    
    assert result['language_code'] == 'unknown'
    assert result['confidence'] == 0.0


def test_detect_language_long_text_truncated(comprehend_service):
    """Test that long text is truncated to 5000 characters."""
    comprehend_service.comprehend_client.detect_dominant_language = Mock(
        return_value={
            'Languages': [
                {'LanguageCode': 'en', 'Score': 0.95}
            ]
        }
    )
    
    long_text = 'a' * 10000  # 10,000 characters
    result = comprehend_service.detect_language(long_text)
    
    # Verify the call was made with truncated text
    call_args = comprehend_service.comprehend_client.detect_dominant_language.call_args
    assert len(call_args[1]['Text']) == 5000


def test_detect_language_no_results(comprehend_service):
    """Test handling when Comprehend returns no languages."""
    comprehend_service.comprehend_client.detect_dominant_language = Mock(
        return_value={'Languages': []}
    )
    
    result = comprehend_service.detect_language('Test text')
    
    assert result['language_code'] == 'unknown'
    assert result['confidence'] == 0.0
    assert result['all_languages'] == []


def test_detect_language_unmapped_code(comprehend_service):
    """Test handling of language codes not in mapping."""
    comprehend_service.comprehend_client.detect_dominant_language = Mock(
        return_value={
            'Languages': [
                {'LanguageCode': 'fr', 'Score': 0.90}  # French, not in mapping
            ]
        }
    )
    
    result = comprehend_service.detect_language('Bonjour')
    
    # Should append -IN to unmapped codes
    assert result['language_code'] == 'fr-IN'
    assert result['confidence'] == 0.90


def test_detect_language_comprehend_error(comprehend_service):
    """Test handling of Comprehend service errors."""
    comprehend_service.comprehend_client.detect_dominant_language = Mock(
        side_effect=ClientError(
            {'Error': {'Code': 'InvalidRequestException', 'Message': 'Invalid text'}},
            'DetectDominantLanguage'
        )
    )
    
    with pytest.raises(Exception, match='AWS Comprehend error'):
        comprehend_service.detect_language('Test text')


def test_detect_language_batch_success(comprehend_service):
    """Test batch language detection."""
    comprehend_service.comprehend_client.batch_detect_dominant_language = Mock(
        return_value={
            'ResultList': [
                {
                    'Languages': [
                        {'LanguageCode': 'hi', 'Score': 0.98}
                    ]
                },
                {
                    'Languages': [
                        {'LanguageCode': 'en', 'Score': 0.95}
                    ]
                },
                {
                    'Languages': [
                        {'LanguageCode': 'ta', 'Score': 0.92}
                    ]
                }
            ]
        }
    )
    
    texts = ['नमस्ते', 'Hello', 'வணக்கம்']
    results = comprehend_service.detect_language_batch(texts)
    
    assert len(results) == 3
    assert results[0]['language_code'] == 'hi-IN'
    assert results[0]['confidence'] == 0.98
    assert results[1]['language_code'] == 'en-IN'
    assert results[1]['confidence'] == 0.95
    assert results[2]['language_code'] == 'ta-IN'
    assert results[2]['confidence'] == 0.92


def test_detect_language_batch_empty_list(comprehend_service):
    """Test batch detection with empty list."""
    results = comprehend_service.detect_language_batch([])
    
    assert results == []


def test_detect_language_batch_max_limit(comprehend_service):
    """Test that batch detection limits to 25 texts."""
    comprehend_service.comprehend_client.batch_detect_dominant_language = Mock(
        return_value={
            'ResultList': [
                {'Languages': [{'LanguageCode': 'en', 'Score': 0.95}]}
            ] * 25
        }
    )
    
    # Try to send 30 texts
    texts = ['Test'] * 30
    results = comprehend_service.detect_language_batch(texts)
    
    # Verify only 25 were sent
    call_args = comprehend_service.comprehend_client.batch_detect_dominant_language.call_args
    assert len(call_args[1]['TextList']) == 25


def test_detect_language_batch_truncates_long_texts(comprehend_service):
    """Test that batch detection truncates long texts."""
    comprehend_service.comprehend_client.batch_detect_dominant_language = Mock(
        return_value={
            'ResultList': [
                {'Languages': [{'LanguageCode': 'en', 'Score': 0.95}]}
            ]
        }
    )
    
    long_text = 'a' * 10000
    results = comprehend_service.detect_language_batch([long_text])
    
    # Verify text was truncated
    call_args = comprehend_service.comprehend_client.batch_detect_dominant_language.call_args
    assert len(call_args[1]['TextList'][0]) == 5000


def test_detect_language_batch_no_results(comprehend_service):
    """Test batch detection when a text has no language results."""
    comprehend_service.comprehend_client.batch_detect_dominant_language = Mock(
        return_value={
            'ResultList': [
                {'Languages': []},  # No languages detected
                {'Languages': [{'LanguageCode': 'en', 'Score': 0.95}]}
            ]
        }
    )
    
    results = comprehend_service.detect_language_batch(['', 'Hello'])
    
    assert len(results) == 2
    assert results[0]['language_code'] == 'unknown'
    assert results[0]['confidence'] == 0.0
    assert results[1]['language_code'] == 'en-IN'


def test_detect_language_batch_error(comprehend_service):
    """Test handling of batch detection errors."""
    comprehend_service.comprehend_client.batch_detect_dominant_language = Mock(
        side_effect=ClientError(
            {'Error': {'Code': 'InvalidRequestException'}},
            'BatchDetectDominantLanguage'
        )
    )
    
    with pytest.raises(Exception, match='AWS Comprehend batch error'):
        comprehend_service.detect_language_batch(['Test'])


def test_get_supported_languages(comprehend_service):
    """Test getting list of supported languages."""
    languages = comprehend_service.get_supported_languages()
    
    assert 'hi-IN' in languages
    assert 'en-IN' in languages
    assert 'ta-IN' in languages
    assert 'te-IN' in languages
    assert 'bn-IN' in languages
    assert len(languages) == 10  # All mapped languages
