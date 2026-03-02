"""Unit tests for Amazon Polly service."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError
from src.services.polly_service import PollyService


@pytest.fixture
def polly_service():
    """Create PollyService instance with mocked clients."""
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
        
        service = PollyService(s3_bucket='test-bucket', region='ap-south-1')
        service.polly_client = mock_polly
        service.s3_client = mock_s3
        
        yield service


def test_synthesize_speech_hindi(polly_service):
    """Test synthesizing speech in Hindi."""
    # Mock Polly response
    mock_audio_stream = MagicMock()
    mock_audio_stream.read.return_value = b'fake-audio-data'
    
    polly_service.polly_client.synthesize_speech = Mock(
        return_value={
            'AudioStream': mock_audio_stream,
            'ContentType': 'audio/mpeg'
        }
    )
    
    # Mock S3 upload
    polly_service.s3_client.put_object = Mock()
    polly_service.s3_client.generate_presigned_url = Mock(
        return_value='https://example.com/audio.mp3'
    )
    
    result = polly_service.synthesize_speech(
        text='नमस्ते, आप कैसे हैं?',
        language_code='hi-IN',
        output_format='mp3'
    )
    
    assert result['audio_url'] == 'https://example.com/audio.mp3'
    assert result['audio_format'] == 'mp3'
    assert result['language'] == 'hi-IN'
    assert result['voice_id'] == 'Aditi'
    assert result['duration_seconds'] > 0
    assert 's3_key' in result
    
    # Verify Polly was called with correct parameters
    call_args = polly_service.polly_client.synthesize_speech.call_args
    assert call_args[1]['VoiceId'] == 'Aditi'
    assert call_args[1]['LanguageCode'] == 'hi-IN'
    assert call_args[1]['Engine'] == 'neural'
    assert call_args[1]['OutputFormat'] == 'mp3'


def test_synthesize_speech_english(polly_service):
    """Test synthesizing speech in English."""
    mock_audio_stream = MagicMock()
    mock_audio_stream.read.return_value = b'fake-audio-data'
    
    polly_service.polly_client.synthesize_speech = Mock(
        return_value={
            'AudioStream': mock_audio_stream,
            'ContentType': 'audio/mpeg'
        }
    )
    
    polly_service.s3_client.put_object = Mock()
    polly_service.s3_client.generate_presigned_url = Mock(
        return_value='https://example.com/audio.mp3'
    )
    
    result = polly_service.synthesize_speech(
        text='Hello, how are you?',
        language_code='en-IN',
        output_format='mp3'
    )
    
    assert result['voice_id'] == 'Kajal'
    
    call_args = polly_service.polly_client.synthesize_speech.call_args
    assert call_args[1]['VoiceId'] == 'Kajal'
    assert call_args[1]['LanguageCode'] == 'en-IN'


def test_synthesize_speech_fallback_language(polly_service):
    """Test synthesizing speech with unsupported language falls back to Hindi."""
    mock_audio_stream = MagicMock()
    mock_audio_stream.read.return_value = b'fake-audio-data'
    
    polly_service.polly_client.synthesize_speech = Mock(
        return_value={
            'AudioStream': mock_audio_stream,
            'ContentType': 'audio/mpeg'
        }
    )
    
    polly_service.s3_client.put_object = Mock()
    polly_service.s3_client.generate_presigned_url = Mock(
        return_value='https://example.com/audio.mp3'
    )
    
    result = polly_service.synthesize_speech(
        text='Test text',
        language_code='xx-XX',  # Unsupported language
        output_format='mp3'
    )
    
    # Should fall back to Hindi (Aditi)
    assert result['voice_id'] == 'Aditi'
    
    call_args = polly_service.polly_client.synthesize_speech.call_args
    assert call_args[1]['VoiceId'] == 'Aditi'
    assert call_args[1]['LanguageCode'] == 'hi-IN'


def test_synthesize_speech_ogg_format(polly_service):
    """Test synthesizing speech in OGG format."""
    mock_audio_stream = MagicMock()
    mock_audio_stream.read.return_value = b'fake-audio-data'
    
    polly_service.polly_client.synthesize_speech = Mock(
        return_value={
            'AudioStream': mock_audio_stream,
            'ContentType': 'audio/ogg'
        }
    )
    
    polly_service.s3_client.put_object = Mock()
    polly_service.s3_client.generate_presigned_url = Mock(
        return_value='https://example.com/audio.ogg'
    )
    
    result = polly_service.synthesize_speech(
        text='Test text',
        language_code='hi-IN',
        output_format='ogg_vorbis'
    )
    
    assert result['audio_format'] == 'ogg_vorbis'
    assert 'audio.ogg' in result['audio_url']
    
    call_args = polly_service.polly_client.synthesize_speech.call_args
    assert call_args[1]['OutputFormat'] == 'ogg_vorbis'


def test_synthesize_speech_duration_estimation(polly_service):
    """Test that audio duration is estimated correctly."""
    mock_audio_stream = MagicMock()
    mock_audio_stream.read.return_value = b'fake-audio-data'
    
    polly_service.polly_client.synthesize_speech = Mock(
        return_value={
            'AudioStream': mock_audio_stream,
            'ContentType': 'audio/mpeg'
        }
    )
    
    polly_service.s3_client.put_object = Mock()
    polly_service.s3_client.generate_presigned_url = Mock(
        return_value='https://example.com/audio.mp3'
    )
    
    # Text with approximately 150 words (should be ~60 seconds)
    text = ' '.join(['word'] * 150)
    
    result = polly_service.synthesize_speech(
        text=text,
        language_code='hi-IN'
    )
    
    # Duration should be approximately 60 seconds (150 words / 150 words per minute * 60)
    assert result['duration_seconds'] == pytest.approx(60, rel=0.1)


def test_synthesize_speech_s3_upload(polly_service):
    """Test that audio is uploaded to S3 correctly."""
    mock_audio_stream = MagicMock()
    mock_audio_stream.read.return_value = b'fake-audio-data'
    
    polly_service.polly_client.synthesize_speech = Mock(
        return_value={
            'AudioStream': mock_audio_stream,
            'ContentType': 'audio/mpeg'
        }
    )
    
    polly_service.s3_client.put_object = Mock()
    polly_service.s3_client.generate_presigned_url = Mock(
        return_value='https://example.com/audio.mp3'
    )
    
    result = polly_service.synthesize_speech(
        text='Test',
        language_code='hi-IN'
    )
    
    # Verify S3 upload was called
    polly_service.s3_client.put_object.assert_called_once()
    call_args = polly_service.s3_client.put_object.call_args
    assert call_args[1]['Bucket'] == 'test-bucket'
    assert call_args[1]['Body'] == b'fake-audio-data'
    assert call_args[1]['ContentType'] == 'audio/mpeg'
    assert 'audio-output/' in call_args[1]['Key']


def test_synthesize_speech_presigned_url(polly_service):
    """Test that presigned URL is generated correctly."""
    mock_audio_stream = MagicMock()
    mock_audio_stream.read.return_value = b'fake-audio-data'
    
    polly_service.polly_client.synthesize_speech = Mock(
        return_value={
            'AudioStream': mock_audio_stream,
            'ContentType': 'audio/mpeg'
        }
    )
    
    polly_service.s3_client.put_object = Mock()
    polly_service.s3_client.generate_presigned_url = Mock(
        return_value='https://example.com/audio.mp3?signature=xyz'
    )
    
    result = polly_service.synthesize_speech(
        text='Test',
        language_code='hi-IN'
    )
    
    # Verify presigned URL was generated
    polly_service.s3_client.generate_presigned_url.assert_called_once()
    call_args = polly_service.s3_client.generate_presigned_url.call_args
    assert call_args[0][0] == 'get_object'
    assert call_args[1]['Params']['Bucket'] == 'test-bucket'
    assert call_args[1]['ExpiresIn'] == 3600  # 1 hour


def test_synthesize_speech_polly_error(polly_service):
    """Test handling of Polly service errors."""
    polly_service.polly_client.synthesize_speech = Mock(
        side_effect=ClientError(
            {'Error': {'Code': 'InvalidParameterValue', 'Message': 'Invalid text'}},
            'SynthesizeSpeech'
        )
    )
    
    with pytest.raises(Exception, match='AWS Polly error'):
        polly_service.synthesize_speech(
            text='Test',
            language_code='hi-IN'
        )


def test_get_supported_languages(polly_service):
    """Test getting list of supported languages."""
    languages = polly_service.get_supported_languages()
    
    assert 'hi-IN' in languages
    assert 'en-IN' in languages
    assert languages['hi-IN']['voice_id'] == 'Aditi'
    assert languages['en-IN']['voice_id'] == 'Kajal'
    assert languages['hi-IN']['engine'] == 'neural'


def test_cleanup_audio_file(polly_service):
    """Test audio file cleanup."""
    polly_service.s3_client.delete_object = Mock()
    
    polly_service.cleanup_audio_file('audio-output/test.mp3')
    
    polly_service.s3_client.delete_object.assert_called_once_with(
        Bucket='test-bucket',
        Key='audio-output/test.mp3'
    )


def test_cleanup_audio_file_error_ignored(polly_service):
    """Test that cleanup errors are ignored."""
    polly_service.s3_client.delete_object = Mock(
        side_effect=ClientError({'Error': {'Code': 'NoSuchKey'}}, 'DeleteObject')
    )
    
    # Should not raise exception
    polly_service.cleanup_audio_file('audio-output/test.mp3')
