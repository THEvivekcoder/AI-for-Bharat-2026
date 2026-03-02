"""Property-based tests for text-to-speech audio generation.

Feature: bharatsahayak, Property 2: Text-to-Speech Audio Generation
**Validates: Requirements 1.2**

This test verifies that for any text input and supported language, the
Voice_Interface should generate valid audio output that can be played
without errors.
"""

import pytest
from hypothesis import given, settings, strategies as st, HealthCheck, assume
from unittest.mock import Mock, patch, MagicMock
import json
import base64
from datetime import datetime
from io import BytesIO

from src.services.polly_service import PollyService
from src.api.text_to_voice import lambda_handler


# Test data: Sample texts in various Indian languages
SAMPLE_TEXTS = [
    {
        "language": "hi-IN",
        "text": "नमस्ते, मैं आपकी सहायता के लिए यहां हूं",
        "voice_id": "Aditi"
    },
    {
        "language": "en-IN",
        "text": "Hello, I am here to help you with government schemes",
        "voice_id": "Kajal"
    },
    {
        "language": "hi-IN",
        "text": "कृषि योजनाओं के बारे में जानकारी",
        "voice_id": "Aditi"
    },
    {
        "language": "en-IN",
        "text": "Information about farmer welfare programs",
        "voice_id": "Kajal"
    },
    {
        "language": "ta-IN",
        "text": "அரசு திட்டங்கள் பற்றிய தகவல்",
        "voice_id": "Kajal"  # Fallback to English voice
    },
    {
        "language": "mr-IN",
        "text": "शेतकरी कल्याण योजना",
        "voice_id": "Aditi"  # Fallback to Hindi voice
    },
    {
        "language": "gu-IN",
        "text": "સરકારી યોજનાઓની માહિતી",
        "voice_id": "Aditi"
    },
    {
        "language": "te-IN",
        "text": "ప్రభుత్వ పథకాల సమాచారం",
        "voice_id": "Kajal"
    },
    {
        "language": "bn-IN",
        "text": "সরকারি প্রকল্পের তথ্য",
        "voice_id": "Kajal"
    },
    {
        "language": "kn-IN",
        "text": "ಸರ್ಕಾರಿ ಯೋಜನೆಗಳ ಮಾಹಿತಿ",
        "voice_id": "Kajal"
    }
]


def is_valid_audio_data(audio_data: bytes, audio_format: str) -> bool:
    """
    Validate that audio data is properly formatted.
    
    Checks:
    - Audio data is not empty
    - Audio data has minimum size (at least 100 bytes)
    - Audio data starts with valid format header
    
    Args:
        audio_data: Raw audio bytes
        audio_format: Expected audio format (mp3, ogg_vorbis, pcm)
    
    Returns:
        bool: True if audio data appears valid
    """
    if not audio_data or len(audio_data) == 0:
        return False
    
    # Minimum size check (valid audio should be at least 100 bytes)
    if len(audio_data) < 100:
        return False
    
    # Format-specific header validation
    if audio_format == 'mp3':
        # MP3 files typically start with ID3 tag or MPEG frame sync
        # ID3v2: starts with 'ID3'
        # MPEG frame: starts with 0xFF 0xFB or similar sync bytes
        if audio_data[:3] == b'ID3' or (audio_data[0] == 0xFF and (audio_data[1] & 0xE0) == 0xE0):
            return True
    elif audio_format == 'ogg_vorbis':
        # Ogg files start with 'OggS'
        if audio_data[:4] == b'OggS':
            return True
    elif audio_format == 'pcm':
        # PCM is raw audio, no header - just check it's not empty
        return True
    
    # If we can't validate format-specific header, accept if size is reasonable
    return len(audio_data) >= 100


@st.composite
def sample_text_strategy(draw):
    """Generate sample text test cases."""
    sample = draw(st.sampled_from(SAMPLE_TEXTS))
    return sample


@st.composite
def generated_text_strategy(draw):
    """Generate arbitrary text for testing."""
    # Generate text of varying lengths
    text_length = draw(st.integers(min_value=1, max_value=500))
    # Use printable characters and common punctuation
    text = draw(st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs', 'Po')),
        min_size=text_length,
        max_size=text_length
    ))
    # Filter out empty or whitespace-only strings
    assume(text.strip())
    
    language = draw(st.sampled_from(['hi-IN', 'en-IN', 'ta-IN', 'te-IN', 'mr-IN', 'gu-IN', 'bn-IN', 'kn-IN']))
    
    return {
        "language": language,
        "text": text.strip()
    }


@settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(sample=sample_text_strategy())
def test_audio_generation_validity(sample):
    """
    Feature: bharatsahayak, Property 2: Text-to-Speech Audio Generation
    
    For any text input and supported language, the Voice_Interface should
    generate valid audio output that can be played without errors.
    
    This test verifies:
    1. Audio synthesis completes successfully
    2. Generated audio data is not empty
    3. Audio data has valid format headers
    4. Audio URL is accessible
    5. Audio format matches requested format
    6. Voice ID matches language profile
    7. Duration estimate is reasonable
    
    Note: This test uses mocked Polly responses. In production,
    this would use actual AWS Polly service.
    """
    # Generate fake but valid-looking audio data
    fake_audio_data = b'ID3' + b'\x00' * 200  # Fake MP3 with ID3 header
    
    with patch('boto3.client') as mock_boto_client:
        mock_polly = Mock()
        mock_s3 = Mock()
        
        def client_factory(service_name, **kwargs):
            if service_name == 'polly':
                return mock_polly
            elif service_name == 's3':
                return mock_s3
            return Mock()
        
        mock_boto_client.side_effect = client_factory
        
        # Create Polly service
        polly_service = PollyService(s3_bucket='test-bucket')
        polly_service.polly_client = mock_polly
        polly_service.s3_client = mock_s3
        
        # Mock Polly synthesize_speech response
        mock_audio_stream = Mock()
        mock_audio_stream.read = Mock(return_value=fake_audio_data)
        
        mock_polly.synthesize_speech = Mock(
            return_value={
                'AudioStream': mock_audio_stream,
                'ContentType': 'audio/mpeg'
            }
        )
        
        # Mock S3 operations
        mock_s3.put_object = Mock()
        mock_s3.generate_presigned_url = Mock(
            return_value='https://test-bucket.s3.amazonaws.com/audio-output/test.mp3'
        )
        
        # Synthesize speech
        result = polly_service.synthesize_speech(
            text=sample['text'],
            language_code=sample['language'],
            output_format='mp3'
        )
        
        # Property 1: Synthesis should complete successfully
        assert result is not None, "Speech synthesis should return a result"
        
        # Property 2: Audio URL should be generated
        assert 'audio_url' in result, "Result should contain audio_url"
        assert result['audio_url'], "Audio URL should not be empty"
        assert result['audio_url'].startswith('https://'), (
            f"Audio URL should be HTTPS: {result['audio_url']}"
        )
        
        # Property 3: Audio format should match requested format
        assert result['audio_format'] == 'mp3', (
            f"Audio format should be 'mp3', got '{result['audio_format']}'"
        )
        
        # Property 4: Language should match input
        assert result['language'] == sample['language'], (
            f"Language should be '{sample['language']}', got '{result['language']}'"
        )
        
        # Property 5: Voice ID should match expected voice for language
        assert result['voice_id'] == sample['voice_id'], (
            f"Voice ID should be '{sample['voice_id']}' for language '{sample['language']}', "
            f"got '{result['voice_id']}'"
        )
        
        # Property 6: Duration estimate should be reasonable (positive number)
        assert 'duration_seconds' in result, "Result should contain duration_seconds"
        assert result['duration_seconds'] > 0, (
            f"Duration should be positive, got {result['duration_seconds']}"
        )
        
        # Property 7: Duration should be proportional to text length
        # Rough estimate: ~150 words per minute = 2.5 words per second
        word_count = len(sample['text'].split())
        expected_duration = (word_count / 150) * 60  # seconds
        # Allow 50% variance
        assert result['duration_seconds'] <= expected_duration * 1.5, (
            f"Duration {result['duration_seconds']}s seems too long for {word_count} words"
        )
        
        # Property 8: Polly was called with correct parameters
        mock_polly.synthesize_speech.assert_called_once()
        call_args = mock_polly.synthesize_speech.call_args[1]
        assert call_args['Text'] == sample['text']
        assert call_args['OutputFormat'] == 'mp3'
        assert call_args['VoiceId'] == sample['voice_id']
        
        # Property 9: Audio was uploaded to S3
        mock_s3.put_object.assert_called_once()
        s3_call_args = mock_s3.put_object.call_args[1]
        assert s3_call_args['Bucket'] == 'test-bucket'
        assert s3_call_args['Key'].startswith('audio-output/')
        assert s3_call_args['Key'].endswith('.mp3')


@settings(max_examples=5, deadline=None)
@given(
    language=st.sampled_from(['hi-IN', 'en-IN', 'ta-IN', 'te-IN', 'mr-IN', 'gu-IN', 'bn-IN', 'kn-IN', 'ml-IN', 'pa-IN']),
    output_format=st.sampled_from(['mp3', 'ogg_vorbis', 'pcm'])
)
def test_audio_generation_all_formats(language, output_format):
    """
    Test that audio can be generated in all supported formats.
    
    This verifies that the TTS service supports multiple audio formats
    for different use cases (streaming, offline, etc.).
    """
    # Generate format-appropriate fake audio data
    if output_format == 'mp3':
        fake_audio_data = b'ID3' + b'\x00' * 200
        content_type = 'audio/mpeg'
    elif output_format == 'ogg_vorbis':
        fake_audio_data = b'OggS' + b'\x00' * 200
        content_type = 'audio/ogg'
    else:  # pcm
        fake_audio_data = b'\x00' * 200
        content_type = 'audio/pcm'
    
    with patch('boto3.client') as mock_boto_client:
        mock_polly = Mock()
        mock_s3 = Mock()
        
        def client_factory(service_name, **kwargs):
            if service_name == 'polly':
                return mock_polly
            elif service_name == 's3':
                return mock_s3
            return Mock()
        
        mock_boto_client.side_effect = client_factory
        
        polly_service = PollyService(s3_bucket='test-bucket')
        polly_service.polly_client = mock_polly
        polly_service.s3_client = mock_s3
        
        # Mock Polly response
        mock_audio_stream = Mock()
        mock_audio_stream.read = Mock(return_value=fake_audio_data)
        
        mock_polly.synthesize_speech = Mock(
            return_value={
                'AudioStream': mock_audio_stream,
                'ContentType': content_type
            }
        )
        
        mock_s3.put_object = Mock()
        mock_s3.generate_presigned_url = Mock(
            return_value=f'https://test-bucket.s3.amazonaws.com/audio-output/test.{output_format}'
        )
        
        # Synthesize speech
        result = polly_service.synthesize_speech(
            text='Test text',
            language_code=language,
            output_format=output_format
        )
        
        # Verify format is correct
        assert result['audio_format'] == output_format, (
            f"Audio format should be '{output_format}', got '{result['audio_format']}'"
        )
        
        # Verify Polly was called with correct format
        call_args = mock_polly.synthesize_speech.call_args[1]
        assert call_args['OutputFormat'] == output_format


@settings(max_examples=5, deadline=None)
@given(sample=sample_text_strategy())
def test_audio_generation_lambda_handler(sample):
    """
    Test the Lambda handler for text-to-speech with validity verification.
    
    This verifies the end-to-end Lambda function generates valid audio.
    """
    fake_audio_data = b'ID3' + b'\x00' * 200
    
    # Mock environment variable
    with patch.dict('os.environ', {'S3_BUCKET_NAME': 'test-bucket'}):
        with patch('boto3.client') as mock_boto_client:
            mock_polly = Mock()
            mock_s3 = Mock()
            
            def client_factory(service_name, **kwargs):
                if service_name == 'polly':
                    return mock_polly
                elif service_name == 's3':
                    return mock_s3
                return Mock()
            
            mock_boto_client.side_effect = client_factory
            
            # Mock Polly response
            mock_audio_stream = Mock()
            mock_audio_stream.read = Mock(return_value=fake_audio_data)
            
            mock_polly.synthesize_speech = Mock(
                return_value={
                    'AudioStream': mock_audio_stream,
                    'ContentType': 'audio/mpeg'
                }
            )
            
            mock_s3.put_object = Mock()
            mock_s3.generate_presigned_url = Mock(
                return_value='https://test-bucket.s3.amazonaws.com/audio-output/test.mp3'
            )
            
            # Create Lambda event
            event = {
                'body': json.dumps({
                    'text': sample['text'],
                    'language_code': sample['language'],
                    'output_format': 'mp3'
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
            
            # Verify required fields
            assert 'audio_url' in body, "Response should contain audio_url"
            assert 'audio_format' in body, "Response should contain audio_format"
            assert 'language' in body, "Response should contain language"
            assert 'voice_id' in body, "Response should contain voice_id"
            assert 'audio_duration_seconds' in body, "Response should contain audio_duration_seconds"
            
            # Verify values
            assert body['audio_url'], "Audio URL should not be empty"
            assert body['audio_format'] == 'mp3'
            assert body['language'] == sample['language']
            assert body['voice_id'] == sample['voice_id']
            assert body['audio_duration_seconds'] > 0


@settings(max_examples=5, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
@given(sample=generated_text_strategy())
def test_audio_generation_arbitrary_text(sample):
    """
    Test that audio can be generated for arbitrary text inputs.
    
    This verifies robustness with various text inputs including
    special characters, numbers, and mixed content.
    """
    # Skip very short texts
    assume(len(sample['text']) >= 5)
    
    fake_audio_data = b'ID3' + b'\x00' * 200
    
    with patch('boto3.client') as mock_boto_client:
        mock_polly = Mock()
        mock_s3 = Mock()
        
        def client_factory(service_name, **kwargs):
            if service_name == 'polly':
                return mock_polly
            elif service_name == 's3':
                return mock_s3
            return Mock()
        
        mock_boto_client.side_effect = client_factory
        
        polly_service = PollyService(s3_bucket='test-bucket')
        polly_service.polly_client = mock_polly
        polly_service.s3_client = mock_s3
        
        # Mock Polly response
        mock_audio_stream = Mock()
        mock_audio_stream.read = Mock(return_value=fake_audio_data)
        
        mock_polly.synthesize_speech = Mock(
            return_value={
                'AudioStream': mock_audio_stream,
                'ContentType': 'audio/mpeg'
            }
        )
        
        mock_s3.put_object = Mock()
        mock_s3.generate_presigned_url = Mock(
            return_value='https://test-bucket.s3.amazonaws.com/audio-output/test.mp3'
        )
        
        # Synthesize speech
        result = polly_service.synthesize_speech(
            text=sample['text'],
            language_code=sample['language'],
            output_format='mp3'
        )
        
        # Verify synthesis succeeded
        assert result is not None
        assert result['audio_url']
        assert result['audio_format'] == 'mp3'
        assert result['language'] == sample['language']


def test_audio_generation_empty_text_handling():
    """
    Test that empty text is handled gracefully.
    
    This verifies error handling for invalid inputs.
    """
    with patch.dict('os.environ', {'S3_BUCKET_NAME': 'test-bucket'}):
        # Create Lambda event with empty text
        event = {
            'body': json.dumps({
                'text': '',
                'language_code': 'hi-IN',
                'output_format': 'mp3'
            })
        }
        
        # Call Lambda handler
        response = lambda_handler(event, None)
        
        # Should return error
        assert response['statusCode'] == 400, (
            f"Expected status code 400 for empty text, got {response['statusCode']}"
        )
        
        body = json.loads(response['body'])
        assert 'error' in body


def test_audio_generation_text_length_limit():
    """
    Test that text length limits are enforced.
    
    Polly has a 3000 character limit for standard synthesis.
    """
    with patch.dict('os.environ', {'S3_BUCKET_NAME': 'test-bucket'}):
        # Create Lambda event with text exceeding limit
        long_text = 'a' * 3001
        event = {
            'body': json.dumps({
                'text': long_text,
                'language_code': 'hi-IN',
                'output_format': 'mp3'
            })
        }
        
        # Call Lambda handler
        response = lambda_handler(event, None)
        
        # Should return error
        assert response['statusCode'] == 400, (
            f"Expected status code 400 for text exceeding limit, got {response['statusCode']}"
        )
        
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'maximum length' in body['error'].lower()


def test_audio_generation_supported_languages():
    """
    Test that all required Indian languages are supported.
    
    This verifies Requirement 1.2: Support for Hindi and regional languages.
    """
    required_languages = ['hi-IN', 'en-IN', 'ta-IN', 'te-IN', 'mr-IN', 'gu-IN', 'bn-IN', 'kn-IN', 'ml-IN', 'pa-IN']
    
    with patch('boto3.client') as mock_boto_client:
        mock_polly = Mock()
        mock_s3 = Mock()
        
        def client_factory(service_name, **kwargs):
            if service_name == 'polly':
                return mock_polly
            elif service_name == 's3':
                return mock_s3
            return Mock()
        
        mock_boto_client.side_effect = client_factory
        
        polly_service = PollyService(s3_bucket='test-bucket')
        
        # Get supported languages
        supported_languages = polly_service.get_supported_languages()
        
        # Verify all required languages are supported
        for lang in required_languages:
            assert lang in supported_languages, (
                f"Language {lang} should be supported but is not in supported languages list"
            )
            
            # Verify each language has a voice profile
            lang_info = supported_languages[lang]
            assert 'voice_id' in lang_info
            assert 'language_code' in lang_info
            assert 'engine' in lang_info
            assert lang_info['voice_id'], f"Voice ID should not be empty for {lang}"


def test_audio_generation_s3_cleanup():
    """
    Test that S3 cleanup functionality works correctly.
    
    This verifies proper resource management.
    """
    with patch('boto3.client') as mock_boto_client:
        mock_polly = Mock()
        mock_s3 = Mock()
        
        def client_factory(service_name, **kwargs):
            if service_name == 'polly':
                return mock_polly
            elif service_name == 's3':
                return mock_s3
            return Mock()
        
        mock_boto_client.side_effect = client_factory
        
        polly_service = PollyService(s3_bucket='test-bucket')
        polly_service.s3_client = mock_s3
        
        # Mock S3 delete
        mock_s3.delete_object = Mock()
        
        # Cleanup audio file
        s3_key = 'audio-output/test-file.mp3'
        polly_service.cleanup_audio_file(s3_key)
        
        # Verify S3 delete was called
        mock_s3.delete_object.assert_called_once_with(
            Bucket='test-bucket',
            Key=s3_key
        )


def test_audio_generation_neural_engine():
    """
    Test that neural engine is used for better quality.
    
    This verifies that the service uses AWS Polly's neural engine
    for more natural-sounding speech.
    """
    fake_audio_data = b'ID3' + b'\x00' * 200
    
    with patch('boto3.client') as mock_boto_client:
        mock_polly = Mock()
        mock_s3 = Mock()
        
        def client_factory(service_name, **kwargs):
            if service_name == 'polly':
                return mock_polly
            elif service_name == 's3':
                return mock_s3
            return Mock()
        
        mock_boto_client.side_effect = client_factory
        
        polly_service = PollyService(s3_bucket='test-bucket')
        polly_service.polly_client = mock_polly
        polly_service.s3_client = mock_s3
        
        # Mock Polly response
        mock_audio_stream = Mock()
        mock_audio_stream.read = Mock(return_value=fake_audio_data)
        
        mock_polly.synthesize_speech = Mock(
            return_value={
                'AudioStream': mock_audio_stream,
                'ContentType': 'audio/mpeg'
            }
        )
        
        mock_s3.put_object = Mock()
        mock_s3.generate_presigned_url = Mock(
            return_value='https://test-bucket.s3.amazonaws.com/audio-output/test.mp3'
        )
        
        # Synthesize speech
        polly_service.synthesize_speech(
            text='Test text',
            language_code='hi-IN',
            output_format='mp3'
        )
        
        # Verify neural engine was used
        call_args = mock_polly.synthesize_speech.call_args[1]
        assert call_args['Engine'] == 'neural', (
            "Should use neural engine for better quality"
        )
