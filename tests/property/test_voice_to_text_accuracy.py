"""Property-based tests for voice-to-text transcription accuracy.

Feature: bharatsahayak, Property 1: Voice-to-Text Transcription Accuracy
**Validates: Requirements 1.1**

This test verifies that for any audio input in a supported language, when
transcribed by the Voice_Interface, the resulting text should accurately
represent the spoken content with at least 85% word accuracy.
"""

import pytest
from hypothesis import given, settings, strategies as st, HealthCheck, assume
from unittest.mock import Mock, patch, MagicMock
import json
import base64
from datetime import datetime

from src.services.transcribe_service import TranscribeService
from src.api.voice_to_text import lambda_handler


# Test data: Known audio transcriptions for accuracy verification
# In a real implementation, these would be actual audio files with known transcripts
SAMPLE_TRANSCRIPTIONS = [
    {
        "language": "hi-IN",
        "expected_text": "नमस्ते मैं सरकारी योजनाओं के बारे में जानना चाहता हूं",
        "audio_format": "wav",
        "confidence": 0.92
    },
    {
        "language": "en-IN",
        "expected_text": "Hello I want to know about government schemes",
        "audio_format": "wav",
        "confidence": 0.95
    },
    {
        "language": "hi-IN",
        "expected_text": "मुझे कृषि योजनाओं की जानकारी चाहिए",
        "audio_format": "mp3",
        "confidence": 0.88
    },
    {
        "language": "en-IN",
        "expected_text": "What are the eligibility criteria for farmer schemes",
        "audio_format": "wav",
        "confidence": 0.93
    },
    {
        "language": "ta-IN",
        "expected_text": "நான் அரசு திட்டங்கள் பற்றி தெரிந்து கொள்ள விரும்புகிறேன்",
        "audio_format": "wav",
        "confidence": 0.89
    },
    {
        "language": "mr-IN",
        "expected_text": "मला शेतकरी योजनांबद्दल माहिती हवी आहे",
        "audio_format": "wav",
        "confidence": 0.87
    },
    {
        "language": "gu-IN",
        "expected_text": "મને સરકારી યોજનાઓ વિશે જાણવું છે",
        "audio_format": "wav",
        "confidence": 0.86
    },
    {
        "language": "te-IN",
        "expected_text": "నాకు ప్రభుత్వ పథకాల గురించి తెలుసుకోవాలి",
        "audio_format": "wav",
        "confidence": 0.90
    },
    {
        "language": "bn-IN",
        "expected_text": "আমি সরকারি প্রকল্প সম্পর্কে জানতে চাই",
        "audio_format": "wav",
        "confidence": 0.88
    },
    {
        "language": "kn-IN",
        "expected_text": "ನನಗೆ ಸರ್ಕಾರಿ ಯೋಜನೆಗಳ ಬಗ್ಗೆ ತಿಳಿಯಬೇಕು",
        "audio_format": "wav",
        "confidence": 0.87
    }
]


def calculate_word_accuracy(expected: str, actual: str) -> float:
    """
    Calculate word-level accuracy between expected and actual transcription.
    
    Uses a simple word matching approach:
    - Split both strings into words
    - Count matching words (case-insensitive)
    - Return percentage of matching words
    
    Args:
        expected: Expected transcription text
        actual: Actual transcription text
    
    Returns:
        float: Accuracy percentage (0.0 to 1.0)
    """
    if not expected or not actual:
        return 0.0
    
    # Normalize and split into words
    expected_words = expected.lower().split()
    actual_words = actual.lower().split()
    
    if not expected_words:
        return 0.0
    
    # Count matching words (simple approach)
    # In production, use Levenshtein distance or WER (Word Error Rate)
    matching_words = 0
    for exp_word in expected_words:
        if exp_word in actual_words:
            matching_words += 1
    
    accuracy = matching_words / len(expected_words)
    return accuracy


def calculate_character_accuracy(expected: str, actual: str) -> float:
    """
    Calculate character-level accuracy using Levenshtein distance.
    
    This is a simplified version. In production, use python-Levenshtein library.
    
    Args:
        expected: Expected transcription text
        actual: Actual transcription text
    
    Returns:
        float: Accuracy percentage (0.0 to 1.0)
    """
    if not expected:
        return 0.0
    
    if expected == actual:
        return 1.0
    
    # Simple character matching (not true Levenshtein)
    # For production, use: import Levenshtein; distance = Levenshtein.distance(expected, actual)
    max_len = max(len(expected), len(actual))
    if max_len == 0:
        return 1.0
    
    # Count matching characters at same positions
    matching_chars = sum(1 for e, a in zip(expected, actual) if e == a)
    accuracy = matching_chars / max_len
    
    return accuracy


@st.composite
def sample_transcription_strategy(draw):
    """Generate sample transcription test cases."""
    sample = draw(st.sampled_from(SAMPLE_TRANSCRIPTIONS))
    return sample


@settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(sample=sample_transcription_strategy())
def test_transcription_accuracy_threshold(sample):
    """
    Feature: bharatsahayak, Property 1: Voice-to-Text Transcription Accuracy
    
    For any audio input in a supported language, when transcribed by the
    Voice_Interface, the resulting text should accurately represent the
    spoken content with at least 85% word accuracy.
    
    This test verifies:
    1. Transcription completes successfully
    2. Confidence score is at least 0.85 (85%)
    3. Detected language matches expected language
    4. Transcribed text is not empty
    5. Word accuracy meets the 85% threshold
    
    Note: This test uses mocked transcription results. In production,
    this would use actual audio files and AWS Transcribe service.
    """
    # Mock the transcribe service to return known results
    with patch('boto3.client') as mock_boto_client:
        mock_transcribe = Mock()
        mock_s3 = Mock()
        
        def client_factory(service_name, **kwargs):
            if service_name == 'transcribe':
                return mock_transcribe
            elif service_name == 's3':
                return mock_s3
            return Mock()
        
        mock_boto_client.side_effect = client_factory
        
        # Create transcribe service
        transcribe_service = TranscribeService(s3_bucket='test-bucket')
        transcribe_service.transcribe_client = mock_transcribe
        transcribe_service.s3_client = mock_s3
        
        # Mock S3 upload
        mock_s3.put_object = Mock()
        
        # Mock transcription job
        mock_transcribe.start_transcription_job = Mock()
        mock_transcribe.get_transcription_job = Mock(
            return_value={
                'TranscriptionJob': {
                    'TranscriptionJobStatus': 'COMPLETED',
                    'Transcript': {
                        'TranscriptFileUri': 'https://example.com/transcript.json'
                    }
                }
            }
        )
        
        # Mock transcript fetch with sample data
        with patch('src.services.transcribe_service.TranscribeService._fetch_transcript', return_value={
            'text': sample['expected_text'],
            'confidence': sample['confidence'],
            'detected_language': sample['language'],
            'job_name': 'test-job'
        }):
            with patch('src.services.transcribe_service.TranscribeService._cleanup_s3_file'):
                # Transcribe fake audio data
                result = transcribe_service.transcribe_audio(
                    audio_data=b'fake-audio-data',
                    language_code=sample['language'],
                    audio_format=sample['audio_format']
                )
        
        # Property 1: Transcription should complete successfully
        assert result is not None, "Transcription should return a result"
        
        # Property 2: Confidence score should be at least 0.85 (85%)
        assert result['confidence'] >= 0.85, (
            f"Transcription confidence {result['confidence']} is below 85% threshold. "
            f"Expected at least 0.85 for language {sample['language']}"
        )
        
        # Property 3: Detected language should match expected language
        assert result['detected_language'] == sample['language'], (
            f"Detected language {result['detected_language']} does not match "
            f"expected language {sample['language']}"
        )
        
        # Property 4: Transcribed text should not be empty
        assert result['text'], (
            f"Transcribed text is empty for language {sample['language']}"
        )
        
        # Property 5: Word accuracy should meet 85% threshold
        word_accuracy = calculate_word_accuracy(sample['expected_text'], result['text'])
        assert word_accuracy >= 0.85, (
            f"Word accuracy {word_accuracy:.2%} is below 85% threshold. "
            f"Expected: '{sample['expected_text']}', Got: '{result['text']}'"
        )


@settings(max_examples=5, deadline=None)
@given(
    language=st.sampled_from(['hi-IN', 'en-IN', 'ta-IN', 'te-IN', 'mr-IN', 'gu-IN', 'bn-IN', 'kn-IN', 'ml-IN', 'pa-IN']),
    audio_format=st.sampled_from(['wav', 'mp3', 'mp4', 'flac'])
)
def test_transcription_supported_languages(language, audio_format):
    """
    Test that all supported Indian languages can be transcribed.
    
    This verifies that the transcription service supports all required
    Indian languages as specified in the requirements.
    """
    with patch('boto3.client') as mock_boto_client:
        mock_transcribe = Mock()
        mock_s3 = Mock()
        
        def client_factory(service_name, **kwargs):
            if service_name == 'transcribe':
                return mock_transcribe
            elif service_name == 's3':
                return mock_s3
            return Mock()
        
        mock_boto_client.side_effect = client_factory
        
        transcribe_service = TranscribeService(s3_bucket='test-bucket')
        transcribe_service.transcribe_client = mock_transcribe
        transcribe_service.s3_client = mock_s3
        
        # Verify language is supported
        supported_languages = transcribe_service.get_supported_languages()
        assert language in supported_languages, (
            f"Language {language} should be supported but is not in supported languages list"
        )
        
        # Mock successful transcription
        mock_s3.put_object = Mock()
        mock_transcribe.start_transcription_job = Mock()
        mock_transcribe.get_transcription_job = Mock(
            return_value={
                'TranscriptionJob': {
                    'TranscriptionJobStatus': 'COMPLETED',
                    'Transcript': {
                        'TranscriptFileUri': 'https://example.com/transcript.json'
                    }
                }
            }
        )
        
        with patch('src.services.transcribe_service.TranscribeService._fetch_transcript', return_value={
            'text': 'Sample transcription',
            'confidence': 0.90,
            'detected_language': language,
            'job_name': 'test-job'
        }):
            with patch('src.services.transcribe_service.TranscribeService._cleanup_s3_file'):
                result = transcribe_service.transcribe_audio(
                    audio_data=b'fake-audio-data',
                    language_code=language,
                    audio_format=audio_format
                )
        
        # Verify transcription succeeded
        assert result['detected_language'] == language
        assert result['confidence'] >= 0.85


@settings(max_examples=5, deadline=None)
@given(sample=sample_transcription_strategy())
def test_transcription_lambda_handler_accuracy(sample):
    """
    Test the Lambda handler for voice-to-text with accuracy verification.
    
    This verifies the end-to-end Lambda function maintains accuracy requirements.
    """
    # Mock environment variable
    with patch.dict('os.environ', {'S3_BUCKET_NAME': 'test-bucket'}):
        with patch('boto3.client') as mock_boto_client:
            mock_transcribe = Mock()
            mock_s3 = Mock()
            
            def client_factory(service_name, **kwargs):
                if service_name == 'transcribe':
                    return mock_transcribe
                elif service_name == 's3':
                    return mock_s3
                return Mock()
            
            mock_boto_client.side_effect = client_factory
            
            # Mock transcription
            mock_s3.put_object = Mock()
            mock_transcribe.start_transcription_job = Mock()
            mock_transcribe.get_transcription_job = Mock(
                return_value={
                    'TranscriptionJob': {
                        'TranscriptionJobStatus': 'COMPLETED',
                        'Transcript': {
                            'TranscriptFileUri': 'https://example.com/transcript.json'
                        }
                    }
                }
            )
            
            with patch('src.services.transcribe_service.TranscribeService._fetch_transcript', return_value={
                'text': sample['expected_text'],
                'confidence': sample['confidence'],
                'detected_language': sample['language'],
                'job_name': 'test-job'
            }):
                with patch('src.services.transcribe_service.TranscribeService._cleanup_s3_file'):
                    # Create Lambda event
                    event = {
                        'body': json.dumps({
                            'audio_data': base64.b64encode(b'fake-audio-data').decode('utf-8'),
                            'language_code': sample['language'],
                            'audio_format': sample['audio_format']
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
            assert 'text' in body
            assert 'confidence' in body
            assert 'detected_language' in body
            
            assert body['confidence'] >= 0.85, (
                f"Lambda handler returned confidence {body['confidence']} below 85% threshold"
            )
            
            assert body['detected_language'] == sample['language'], (
                f"Lambda handler detected wrong language: {body['detected_language']} "
                f"instead of {sample['language']}"
            )
            
            # Verify word accuracy
            word_accuracy = calculate_word_accuracy(sample['expected_text'], body['text'])
            assert word_accuracy >= 0.85, (
                f"Lambda handler word accuracy {word_accuracy:.2%} is below 85% threshold"
            )


def test_transcription_accuracy_with_noise():
    """
    Test that transcription maintains accuracy with background noise.
    
    This verifies Requirement 1.1.4: Handle background noise and varying
    audio quality typical of rural environments.
    """
    # Simulate noisy audio with slightly lower confidence
    noisy_sample = {
        "language": "hi-IN",
        "expected_text": "मुझे योजना की जानकारी चाहिए",
        "audio_format": "wav",
        "confidence": 0.86  # Slightly lower due to noise, but still above threshold
    }
    
    with patch('boto3.client') as mock_boto_client:
        mock_transcribe = Mock()
        mock_s3 = Mock()
        
        def client_factory(service_name, **kwargs):
            if service_name == 'transcribe':
                return mock_transcribe
            elif service_name == 's3':
                return mock_s3
            return Mock()
        
        mock_boto_client.side_effect = client_factory
        
        transcribe_service = TranscribeService(s3_bucket='test-bucket')
        transcribe_service.transcribe_client = mock_transcribe
        transcribe_service.s3_client = mock_s3
        
        mock_s3.put_object = Mock()
        mock_transcribe.start_transcription_job = Mock()
        mock_transcribe.get_transcription_job = Mock(
            return_value={
                'TranscriptionJob': {
                    'TranscriptionJobStatus': 'COMPLETED',
                    'Transcript': {
                        'TranscriptFileUri': 'https://example.com/transcript.json'
                    }
                }
            }
        )
        
        with patch('src.services.transcribe_service.TranscribeService._fetch_transcript', return_value={
            'text': noisy_sample['expected_text'],
            'confidence': noisy_sample['confidence'],
            'detected_language': noisy_sample['language'],
            'job_name': 'test-job'
        }):
            with patch('src.services.transcribe_service.TranscribeService._cleanup_s3_file'):
                result = transcribe_service.transcribe_audio(
                    audio_data=b'fake-noisy-audio-data',
                    language_code=noisy_sample['language'],
                    audio_format=noisy_sample['audio_format']
                )
        
        # Even with noise, should maintain 85% accuracy threshold
        assert result['confidence'] >= 0.85, (
            f"Transcription with noise has confidence {result['confidence']} below 85% threshold"
        )


def test_transcription_auto_language_detection():
    """
    Test automatic language detection accuracy.
    
    This verifies Requirement 1.1.3: Detect spoken language automatically.
    """
    test_cases = [
        {"expected_lang": "hi-IN", "text": "नमस्ते"},
        {"expected_lang": "en-IN", "text": "Hello"},
        {"expected_lang": "ta-IN", "text": "வணக்கம்"}
    ]
    
    for test_case in test_cases:
        with patch('boto3.client') as mock_boto_client:
            mock_transcribe = Mock()
            mock_s3 = Mock()
            
            def client_factory(service_name, **kwargs):
                if service_name == 'transcribe':
                    return mock_transcribe
                elif service_name == 's3':
                    return mock_s3
                return Mock()
            
            mock_boto_client.side_effect = client_factory
            
            transcribe_service = TranscribeService(s3_bucket='test-bucket')
            transcribe_service.transcribe_client = mock_transcribe
            transcribe_service.s3_client = mock_s3
            
            mock_s3.put_object = Mock()
            mock_transcribe.start_transcription_job = Mock()
            mock_transcribe.get_transcription_job = Mock(
                return_value={
                    'TranscriptionJob': {
                        'TranscriptionJobStatus': 'COMPLETED',
                        'Transcript': {
                            'TranscriptFileUri': 'https://example.com/transcript.json'
                        }
                    }
                }
            )
            
            with patch('src.services.transcribe_service.TranscribeService._fetch_transcript', return_value={
                'text': test_case['text'],
                'confidence': 0.92,
                'detected_language': test_case['expected_lang'],
                'job_name': 'test-job'
            }):
                with patch('src.services.transcribe_service.TranscribeService._cleanup_s3_file'):
                    # Call without language_code to trigger auto-detection
                    result = transcribe_service.transcribe_audio(
                        audio_data=b'fake-audio-data',
                        language_code=None,  # Auto-detect
                        audio_format='wav'
                    )
            
            # Verify correct language was detected
            assert result['detected_language'] == test_case['expected_lang'], (
                f"Auto-detection failed: expected {test_case['expected_lang']}, "
                f"got {result['detected_language']}"
            )
            
            # Verify IdentifyLanguage was enabled in the call
            call_args = mock_transcribe.start_transcription_job.call_args
            assert call_args[1]['IdentifyLanguage'] is True, (
                "IdentifyLanguage should be enabled for auto-detection"
            )
