"""Property-based tests for language detection accuracy.

Feature: bharatsahayak, Property 3: Language Detection Accuracy
**Validates: Requirements 1.3**

This test verifies that for any audio/text input in a supported Indian language,
the System should correctly identify the language with at least 90% accuracy.
"""

import pytest
from hypothesis import given, settings, strategies as st, HealthCheck, assume
from unittest.mock import Mock, patch, MagicMock
import json
import base64
from datetime import datetime

from src.services.comprehend_service import ComprehendService
from src.api.detect_language import lambda_handler


# Test data: Sample texts in various Indian languages with known language codes
# These represent typical user queries in different languages
SAMPLE_TEXTS = [
    {
        "language": "hi-IN",
        "text": "नमस्ते मैं सरकारी योजनाओं के बारे में जानना चाहता हूं",
        "confidence": 0.95
    },
    {
        "language": "en-IN",
        "text": "Hello I want to know about government schemes",
        "confidence": 0.98
    },
    {
        "language": "hi-IN",
        "text": "मुझे कृषि योजनाओं की जानकारी चाहिए",
        "confidence": 0.93
    },
    {
        "language": "en-IN",
        "text": "What are the eligibility criteria for farmer schemes",
        "confidence": 0.97
    },
    {
        "language": "ta-IN",
        "text": "நான் அரசு திட்டங்கள் பற்றி தெரிந்து கொள்ள விரும்புகிறேன்",
        "confidence": 0.92
    },
    {
        "language": "mr-IN",
        "text": "मला शेतकरी योजनांबद्दल माहिती हवी आहे",
        "confidence": 0.91
    },
    {
        "language": "gu-IN",
        "text": "મને સરકારી યોજનાઓ વિશે જાણવું છે",
        "confidence": 0.90
    },
    {
        "language": "te-IN",
        "text": "నాకు ప్రభుత్వ పథకాల గురించి తెలుసుకోవాలి",
        "confidence": 0.94
    },
    {
        "language": "bn-IN",
        "text": "আমি সরকারি প্রকল্প সম্পর্কে জানতে চাই",
        "confidence": 0.93
    },
    {
        "language": "kn-IN",
        "text": "ನನಗೆ ಸರ್ಕಾರಿ ಯೋಜನೆಗಳ ಬಗ್ಗೆ ತಿಳಿಯಬೇಕು",
        "confidence": 0.91
    },
    {
        "language": "ml-IN",
        "text": "എനിക്ക് സർക്കാർ പദ്ധതികളെക്കുറിച്ച് അറിയണം",
        "confidence": 0.92
    },
    {
        "language": "pa-IN",
        "text": "ਮੈਨੂੰ ਸਰਕਾਰੀ ਯੋਜਨਾਵਾਂ ਬਾਰੇ ਜਾਣਨਾ ਹੈ",
        "confidence": 0.90
    },
    {
        "language": "hi-IN",
        "text": "मुझे स्वास्थ्य योजनाओं की जानकारी चाहिए",
        "confidence": 0.94
    },
    {
        "language": "en-IN",
        "text": "I need information about health insurance schemes",
        "confidence": 0.96
    },
    {
        "language": "ta-IN",
        "text": "எனக்கு விவசாய திட்டங்கள் பற்றி தெரிந்து கொள்ள வேண்டும்",
        "confidence": 0.91
    }
]


@st.composite
def sample_text_strategy(draw):
    """Generate sample text test cases with known languages."""
    sample = draw(st.sampled_from(SAMPLE_TEXTS))
    return sample


@st.composite
def multilingual_batch_strategy(draw):
    """Generate batch of texts in different languages."""
    # Select 2-10 random samples for batch testing
    batch_size = draw(st.integers(min_value=2, max_value=10))
    samples = draw(st.lists(
        st.sampled_from(SAMPLE_TEXTS),
        min_size=batch_size,
        max_size=batch_size
    ))
    return samples


@settings(max_examples=15, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(sample=sample_text_strategy())
def test_language_detection_accuracy_threshold(sample):
    """
    Feature: bharatsahayak, Property 3: Language Detection Accuracy
    
    For any text input in a supported Indian language, the System should
    correctly identify the language with at least 90% accuracy.
    
    This test verifies:
    1. Language detection completes successfully
    2. Confidence score is at least 0.90 (90%)
    3. Detected language matches expected language
    4. All detected languages are returned with confidence scores
    5. Dominant language has highest confidence
    
    Note: This test uses mocked Comprehend responses. In production,
    this would use actual AWS Comprehend service.
    """
    with patch('boto3.client') as mock_boto_client:
        mock_comprehend = Mock()
        
        def client_factory(service_name, **kwargs):
            if service_name == 'comprehend':
                return mock_comprehend
            return Mock()
        
        mock_boto_client.side_effect = client_factory
        
        # Create Comprehend service
        comprehend_service = ComprehendService()
        comprehend_service.comprehend_client = mock_comprehend
        
        # Extract base language code (e.g., 'hi' from 'hi-IN')
        base_lang = sample['language'].split('-')[0]
        
        # Mock Comprehend detect_dominant_language response
        mock_comprehend.detect_dominant_language = Mock(
            return_value={
                'Languages': [
                    {
                        'LanguageCode': base_lang,
                        'Score': sample['confidence']
                    }
                ]
            }
        )
        
        # Detect language
        result = comprehend_service.detect_language(sample['text'])
        
        # Property 1: Detection should complete successfully
        assert result is not None, "Language detection should return a result"
        
        # Property 2: Confidence score should be at least 0.90 (90%)
        assert result['confidence'] >= 0.90, (
            f"Language detection confidence {result['confidence']} is below 90% threshold. "
            f"Expected at least 0.90 for language {sample['language']}"
        )
        
        # Property 3: Detected language should match expected language
        assert result['language_code'] == sample['language'], (
            f"Detected language {result['language_code']} does not match "
            f"expected language {sample['language']}"
        )
        
        # Property 4: All detected languages should be returned
        assert 'all_languages' in result, "Result should contain all_languages"
        assert len(result['all_languages']) > 0, "Should have at least one detected language"
        
        # Property 5: Dominant language should have highest confidence
        dominant_confidence = result['confidence']
        for lang_info in result['all_languages']:
            assert lang_info['confidence'] <= dominant_confidence, (
                f"Non-dominant language has higher confidence: {lang_info}"
            )
        
        # Property 6: Comprehend was called with correct text
        mock_comprehend.detect_dominant_language.assert_called_once()
        call_args = mock_comprehend.detect_dominant_language.call_args[1]
        assert call_args['Text'] == sample['text']


@settings(max_examples=10, deadline=None)
@given(
    language=st.sampled_from(['hi-IN', 'en-IN', 'ta-IN', 'te-IN', 'mr-IN', 'gu-IN', 'bn-IN', 'kn-IN', 'ml-IN', 'pa-IN'])
)
def test_language_detection_supported_languages(language):
    """
    Test that all supported Indian languages can be detected.
    
    This verifies that the language detection service supports all required
    Indian languages as specified in the requirements.
    """
    with patch('boto3.client') as mock_boto_client:
        mock_comprehend = Mock()
        
        def client_factory(service_name, **kwargs):
            if service_name == 'comprehend':
                return mock_comprehend
            return Mock()
        
        mock_boto_client.side_effect = client_factory
        
        comprehend_service = ComprehendService()
        
        # Verify language is supported
        supported_languages = comprehend_service.get_supported_languages()
        assert language in supported_languages, (
            f"Language {language} should be supported but is not in supported languages list"
        )


@settings(max_examples=10, deadline=None)
@given(samples=multilingual_batch_strategy())
def test_language_detection_batch_accuracy(samples):
    """
    Test batch language detection with multilingual samples.
    
    This verifies that batch detection maintains accuracy across
    multiple texts in different languages.
    """
    # Limit to 25 samples (Comprehend batch limit)
    samples = samples[:25]
    
    with patch('boto3.client') as mock_boto_client:
        mock_comprehend = Mock()
        
        def client_factory(service_name, **kwargs):
            if service_name == 'comprehend':
                return mock_comprehend
            return Mock()
        
        mock_boto_client.side_effect = client_factory
        
        comprehend_service = ComprehendService()
        comprehend_service.comprehend_client = mock_comprehend
        
        # Mock batch detection response
        mock_results = []
        for sample in samples:
            base_lang = sample['language'].split('-')[0]
            mock_results.append({
                'Languages': [
                    {
                        'LanguageCode': base_lang,
                        'Score': sample['confidence']
                    }
                ]
            })
        
        mock_comprehend.batch_detect_dominant_language = Mock(
            return_value={
                'ResultList': mock_results
            }
        )
        
        # Detect languages in batch
        texts = [sample['text'] for sample in samples]
        results = comprehend_service.detect_language_batch(texts)
        
        # Property 1: Should return results for all texts
        assert len(results) == len(samples), (
            f"Expected {len(samples)} results, got {len(results)}"
        )
        
        # Property 2: Each result should meet accuracy threshold
        for i, (result, sample) in enumerate(zip(results, samples)):
            assert result['confidence'] >= 0.90, (
                f"Batch result {i} has confidence {result['confidence']} below 90% threshold"
            )
            
            assert result['language_code'] == sample['language'], (
                f"Batch result {i}: detected {result['language_code']}, "
                f"expected {sample['language']}"
            )
        
        # Property 3: Batch API was called correctly
        mock_comprehend.batch_detect_dominant_language.assert_called_once()
        call_args = mock_comprehend.batch_detect_dominant_language.call_args[1]
        assert 'TextList' in call_args
        assert len(call_args['TextList']) == len(samples)


@settings(max_examples=10, deadline=None)
@given(sample=sample_text_strategy())
def test_language_detection_lambda_handler(sample):
    """
    Test the Lambda handler for language detection with accuracy verification.
    
    This verifies the end-to-end Lambda function maintains accuracy requirements.
    """
    with patch('boto3.client') as mock_boto_client:
        mock_comprehend = Mock()
        
        def client_factory(service_name, **kwargs):
            if service_name == 'comprehend':
                return mock_comprehend
            return Mock()
        
        mock_boto_client.side_effect = client_factory
        
        # Extract base language code
        base_lang = sample['language'].split('-')[0]
        
        # Mock Comprehend response
        mock_comprehend.detect_dominant_language = Mock(
            return_value={
                'Languages': [
                    {
                        'LanguageCode': base_lang,
                        'Score': sample['confidence']
                    }
                ]
            }
        )
        
        # Create Lambda event
        event = {
            'body': json.dumps({
                'text': sample['text']
            })
        }
        
        # Call Lambda handler
        response = lambda_handler(event, None)
        
        # Verify successful response
        assert response['statusCode'] == 200, (
            f"Expected status code 200, got {response['statusCode']}"
        )
        
        # Parse response body
        body = json.loads(response['body'])
        
        # Verify accuracy requirements
        assert 'language_code' in body, "Response should contain language_code"
        assert 'confidence' in body, "Response should contain confidence"
        assert 'all_languages' in body, "Response should contain all_languages"
        
        assert body['confidence'] >= 0.90, (
            f"Lambda handler returned confidence {body['confidence']} below 90% threshold"
        )
        
        assert body['language_code'] == sample['language'], (
            f"Lambda handler detected wrong language: {body['language_code']} "
            f"instead of {sample['language']}"
        )


@settings(max_examples=5, deadline=None)
@given(samples=multilingual_batch_strategy())
def test_language_detection_lambda_batch(samples):
    """
    Test the Lambda handler for batch language detection.
    
    This verifies batch processing maintains accuracy across multiple texts.
    """
    # Limit to 25 samples
    samples = samples[:25]
    
    with patch('boto3.client') as mock_boto_client:
        mock_comprehend = Mock()
        
        def client_factory(service_name, **kwargs):
            if service_name == 'comprehend':
                return mock_comprehend
            return Mock()
        
        mock_boto_client.side_effect = client_factory
        
        # Mock batch detection response
        mock_results = []
        for sample in samples:
            base_lang = sample['language'].split('-')[0]
            mock_results.append({
                'Languages': [
                    {
                        'LanguageCode': base_lang,
                        'Score': sample['confidence']
                    }
                ]
            })
        
        mock_comprehend.batch_detect_dominant_language = Mock(
            return_value={
                'ResultList': mock_results
            }
        )
        
        # Create Lambda event with batch
        texts = [sample['text'] for sample in samples]
        event = {
            'body': json.dumps({
                'texts': texts
            })
        }
        
        # Call Lambda handler
        response = lambda_handler(event, None)
        
        # Verify successful response
        assert response['statusCode'] == 200, (
            f"Expected status code 200, got {response['statusCode']}"
        )
        
        # Parse response body
        body = json.loads(response['body'])
        
        # Verify batch results
        assert 'results' in body, "Response should contain results"
        assert len(body['results']) == len(samples), (
            f"Expected {len(samples)} results, got {len(body['results'])}"
        )
        
        # Verify each result meets accuracy threshold
        for i, (result, sample) in enumerate(zip(body['results'], samples)):
            assert result['confidence'] >= 0.90, (
                f"Batch result {i} has confidence {result['confidence']} below 90% threshold"
            )
            
            assert result['language_code'] == sample['language'], (
                f"Batch result {i}: detected {result['language_code']}, "
                f"expected {sample['language']}"
            )


def test_language_detection_empty_text_handling():
    """
    Test that empty text is handled gracefully.
    
    This verifies error handling for invalid inputs.
    """
    with patch('boto3.client') as mock_boto_client:
        mock_comprehend = Mock()
        
        def client_factory(service_name, **kwargs):
            if service_name == 'comprehend':
                return mock_comprehend
            return Mock()
        
        mock_boto_client.side_effect = client_factory
        
        comprehend_service = ComprehendService()
        comprehend_service.comprehend_client = mock_comprehend
        
        # Detect language with empty text
        result = comprehend_service.detect_language('')
        
        # Should return unknown language with 0 confidence
        assert result['language_code'] == 'unknown', (
            f"Empty text should return 'unknown', got '{result['language_code']}'"
        )
        assert result['confidence'] == 0.0, (
            f"Empty text should have 0 confidence, got {result['confidence']}"
        )
        
        # Comprehend should not be called for empty text
        mock_comprehend.detect_dominant_language.assert_not_called()


def test_language_detection_whitespace_text_handling():
    """
    Test that whitespace-only text is handled gracefully.
    """
    with patch('boto3.client') as mock_boto_client:
        mock_comprehend = Mock()
        
        def client_factory(service_name, **kwargs):
            if service_name == 'comprehend':
                return mock_comprehend
            return Mock()
        
        mock_boto_client.side_effect = client_factory
        
        comprehend_service = ComprehendService()
        comprehend_service.comprehend_client = mock_comprehend
        
        # Detect language with whitespace-only text
        result = comprehend_service.detect_language('   \n\t  ')
        
        # Should return unknown language
        assert result['language_code'] == 'unknown'
        assert result['confidence'] == 0.0
        
        # Comprehend should not be called
        mock_comprehend.detect_dominant_language.assert_not_called()


def test_language_detection_long_text_truncation():
    """
    Test that long text is truncated to Comprehend's limit.
    
    Comprehend has a 5000 character limit per text.
    """
    with patch('boto3.client') as mock_boto_client:
        mock_comprehend = Mock()
        
        def client_factory(service_name, **kwargs):
            if service_name == 'comprehend':
                return mock_comprehend
            return Mock()
        
        mock_boto_client.side_effect = client_factory
        
        comprehend_service = ComprehendService()
        comprehend_service.comprehend_client = mock_comprehend
        
        # Mock Comprehend response
        mock_comprehend.detect_dominant_language = Mock(
            return_value={
                'Languages': [
                    {
                        'LanguageCode': 'hi',
                        'Score': 0.95
                    }
                ]
            }
        )
        
        # Create text longer than 5000 characters
        long_text = 'नमस्ते ' * 1000  # Much longer than 5000 chars
        
        # Detect language
        result = comprehend_service.detect_language(long_text)
        
        # Verify detection succeeded
        assert result['language_code'] == 'hi-IN'
        
        # Verify text was truncated to 5000 characters
        call_args = mock_comprehend.detect_dominant_language.call_args[1]
        assert len(call_args['Text']) <= 5000, (
            f"Text should be truncated to 5000 chars, got {len(call_args['Text'])}"
        )


def test_language_detection_mixed_language_text():
    """
    Test language detection with mixed language text.
    
    This verifies that the dominant language is correctly identified
    even when text contains multiple languages.
    """
    mixed_texts = [
        {
            "text": "Hello नमस्ते",  # English + Hindi
            "expected_dominant": "en-IN",
            "confidence": 0.92
        },
        {
            "text": "नमस्ते मैं government schemes के बारे में जानना चाहता हूं",  # Hindi dominant with English words
            "expected_dominant": "hi-IN",
            "confidence": 0.91
        }
    ]
    
    for test_case in mixed_texts:
        with patch('boto3.client') as mock_boto_client:
            mock_comprehend = Mock()
            
            def client_factory(service_name, **kwargs):
                if service_name == 'comprehend':
                    return mock_comprehend
                return Mock()
            
            mock_boto_client.side_effect = client_factory
            
            comprehend_service = ComprehendService()
            comprehend_service.comprehend_client = mock_comprehend
            
            # Extract base language code
            base_lang = test_case['expected_dominant'].split('-')[0]
            
            # Mock Comprehend response with multiple languages
            mock_comprehend.detect_dominant_language = Mock(
                return_value={
                    'Languages': [
                        {
                            'LanguageCode': base_lang,
                            'Score': test_case['confidence']
                        },
                        {
                            'LanguageCode': 'en' if base_lang == 'hi' else 'hi',
                            'Score': 0.08
                        }
                    ]
                }
            )
            
            # Detect language
            result = comprehend_service.detect_language(test_case['text'])
            
            # Verify dominant language is correct
            assert result['language_code'] == test_case['expected_dominant'], (
                f"Expected dominant language {test_case['expected_dominant']}, "
                f"got {result['language_code']}"
            )
            
            # Verify confidence meets threshold
            assert result['confidence'] >= 0.90, (
                f"Confidence {result['confidence']} below 90% threshold for mixed text"
            )
            
            # Verify multiple languages were detected
            assert len(result['all_languages']) > 1, (
                "Should detect multiple languages in mixed text"
            )


def test_language_detection_lambda_missing_text():
    """
    Test Lambda handler error handling for missing text parameter.
    """
    # Create Lambda event without text
    event = {
        'body': json.dumps({})
    }
    
    # Call Lambda handler
    response = lambda_handler(event, None)
    
    # Should return error
    assert response['statusCode'] == 400, (
        f"Expected status code 400 for missing text, got {response['statusCode']}"
    )
    
    body = json.loads(response['body'])
    assert 'error' in body
    assert 'text or texts is required' in body['error']


def test_language_detection_lambda_batch_size_limit():
    """
    Test Lambda handler enforces batch size limit.
    
    Comprehend batch API has a limit of 25 texts.
    """
    # Create Lambda event with too many texts
    texts = ['test text'] * 26
    event = {
        'body': json.dumps({
            'texts': texts
        })
    }
    
    # Call Lambda handler
    response = lambda_handler(event, None)
    
    # Should return error
    assert response['statusCode'] == 400, (
        f"Expected status code 400 for batch size limit, got {response['statusCode']}"
    )
    
    body = json.loads(response['body'])
    assert 'error' in body
    assert 'maximum 25 texts' in body['error']


def test_language_detection_lambda_invalid_texts_type():
    """
    Test Lambda handler validates texts parameter type.
    """
    # Create Lambda event with texts as non-list
    event = {
        'body': json.dumps({
            'texts': 'not a list'
        })
    }
    
    # Call Lambda handler
    response = lambda_handler(event, None)
    
    # Should return error
    assert response['statusCode'] == 400, (
        f"Expected status code 400 for invalid texts type, got {response['statusCode']}"
    )
    
    body = json.loads(response['body'])
    assert 'error' in body
    assert 'texts must be a list' in body['error']


def test_language_detection_all_supported_languages():
    """
    Test that all required Indian languages are supported.
    
    This verifies Requirement 1.3: Support for Hindi and regional Indian languages.
    """
    required_languages = [
        'hi-IN',  # Hindi
        'en-IN',  # English
        'ta-IN',  # Tamil
        'te-IN',  # Telugu
        'bn-IN',  # Bengali
        'mr-IN',  # Marathi
        'gu-IN',  # Gujarati
        'kn-IN',  # Kannada
        'ml-IN',  # Malayalam
        'pa-IN'   # Punjabi
    ]
    
    with patch('boto3.client') as mock_boto_client:
        mock_comprehend = Mock()
        
        def client_factory(service_name, **kwargs):
            if service_name == 'comprehend':
                return mock_comprehend
            return Mock()
        
        mock_boto_client.side_effect = client_factory
        
        comprehend_service = ComprehendService()
        
        # Get supported languages
        supported_languages = comprehend_service.get_supported_languages()
        
        # Verify all required languages are supported
        for lang in required_languages:
            assert lang in supported_languages, (
                f"Language {lang} should be supported but is not in supported languages list"
            )


def test_language_detection_confidence_ordering():
    """
    Test that detected languages are ordered by confidence score.
    
    This verifies that the dominant language has the highest confidence
    and all_languages list is properly ordered.
    """
    with patch('boto3.client') as mock_boto_client:
        mock_comprehend = Mock()
        
        def client_factory(service_name, **kwargs):
            if service_name == 'comprehend':
                return mock_comprehend
            return Mock()
        
        mock_boto_client.side_effect = client_factory
        
        comprehend_service = ComprehendService()
        comprehend_service.comprehend_client = mock_comprehend
        
        # Mock Comprehend response with multiple languages
        mock_comprehend.detect_dominant_language = Mock(
            return_value={
                'Languages': [
                    {'LanguageCode': 'hi', 'Score': 0.95},
                    {'LanguageCode': 'en', 'Score': 0.04},
                    {'LanguageCode': 'mr', 'Score': 0.01}
                ]
            }
        )
        
        # Detect language
        result = comprehend_service.detect_language('नमस्ते')
        
        # Verify dominant language has highest confidence
        assert result['language_code'] == 'hi-IN'
        assert result['confidence'] == 0.95
        
        # Verify all_languages is ordered by confidence
        all_langs = result['all_languages']
        assert len(all_langs) == 3
        
        for i in range(len(all_langs) - 1):
            assert all_langs[i]['confidence'] >= all_langs[i + 1]['confidence'], (
                f"Languages should be ordered by confidence: {all_langs}"
            )
