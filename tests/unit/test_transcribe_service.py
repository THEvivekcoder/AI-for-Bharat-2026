"""Unit tests for Amazon Transcribe service."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError
from src.services.transcribe_service import TranscribeService


@pytest.fixture
def transcribe_service():
    """Create TranscribeService instance with mocked clients."""
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
        
        service = TranscribeService(s3_bucket='test-bucket', region='ap-south-1')
        service.transcribe_client = mock_transcribe
        service.s3_client = mock_s3
        
        yield service


def test_transcribe_audio_with_language_code(transcribe_service):
    """Test transcribing audio with specified language code."""
    # Mock S3 upload
    transcribe_service.s3_client.put_object = Mock()
    
    # Mock transcription job
    transcribe_service.transcribe_client.start_transcription_job = Mock()
    transcribe_service.transcribe_client.get_transcription_job = Mock(
        return_value={
            'TranscriptionJob': {
                'TranscriptionJobStatus': 'COMPLETED',
                'Transcript': {
                    'TranscriptFileUri': 'https://example.com/transcript.json'
                }
            }
        }
    )
    
    # Mock transcript fetch
    mock_transcript = {
        'jobName': 'test-job',
        'results': {
            'transcripts': [{'transcript': 'नमस्ते'}],
            'items': [
                {'type': 'pronunciation', 'alternatives': [{'confidence': '0.95'}]}
            ],
            'language_code': 'hi-IN'
        }
    }
    
    with patch('src.services.transcribe_service.TranscribeService._fetch_transcript', return_value={
        'text': 'नमस्ते',
        'confidence': 0.95,
        'detected_language': 'hi-IN',
        'job_name': 'test-job'
    }):
        with patch('src.services.transcribe_service.TranscribeService._cleanup_s3_file'):
            result = transcribe_service.transcribe_audio(
                audio_data=b'fake-audio-data',
                language_code='hi-IN',
                audio_format='wav'
            )
    
    assert result['text'] == 'नमस्ते'
    assert result['confidence'] == 0.95
    assert result['detected_language'] == 'hi-IN'
    
    # Verify S3 upload was called
    transcribe_service.s3_client.put_object.assert_called_once()
    
    # Verify transcription job was started
    transcribe_service.transcribe_client.start_transcription_job.assert_called_once()


def test_transcribe_audio_with_auto_detect(transcribe_service):
    """Test transcribing audio with automatic language detection."""
    transcribe_service.s3_client.put_object = Mock()
    transcribe_service.transcribe_client.start_transcription_job = Mock()
    transcribe_service.transcribe_client.get_transcription_job = Mock(
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
        'text': 'Hello',
        'confidence': 0.92,
        'detected_language': 'en-IN',
        'job_name': 'test-job'
    }):
        with patch('src.services.transcribe_service.TranscribeService._cleanup_s3_file'):
            result = transcribe_service.transcribe_audio(
                audio_data=b'fake-audio-data',
                language_code=None,  # Auto-detect
                audio_format='mp3'
            )
    
    assert result['detected_language'] == 'en-IN'
    
    # Verify IdentifyLanguage was enabled
    call_args = transcribe_service.transcribe_client.start_transcription_job.call_args
    assert call_args[1]['IdentifyLanguage'] is True
    assert 'LanguageOptions' in call_args[1]


def test_transcribe_audio_job_failed(transcribe_service):
    """Test handling of failed transcription job."""
    transcribe_service.s3_client.put_object = Mock()
    transcribe_service.transcribe_client.start_transcription_job = Mock()
    transcribe_service.transcribe_client.get_transcription_job = Mock(
        return_value={
            'TranscriptionJob': {
                'TranscriptionJobStatus': 'FAILED',
                'FailureReason': 'Invalid audio format'
            }
        }
    )
    
    with patch('src.services.transcribe_service.TranscribeService._cleanup_s3_file'):
        with pytest.raises(Exception, match='Transcription failed'):
            transcribe_service.transcribe_audio(
                audio_data=b'fake-audio-data',
                language_code='hi-IN'
            )


def test_transcribe_audio_timeout(transcribe_service):
    """Test handling of transcription job timeout."""
    transcribe_service.s3_client.put_object = Mock()
    transcribe_service.transcribe_client.start_transcription_job = Mock()
    
    # Always return IN_PROGRESS status
    transcribe_service.transcribe_client.get_transcription_job = Mock(
        return_value={
            'TranscriptionJob': {
                'TranscriptionJobStatus': 'IN_PROGRESS'
            }
        }
    )
    
    with patch('src.services.transcribe_service.TranscribeService._cleanup_s3_file'):
        with patch('time.sleep'):  # Speed up test
            with pytest.raises(TimeoutError, match='timed out'):
                transcribe_service.transcribe_audio(
                    audio_data=b'fake-audio-data',
                    language_code='hi-IN'
                )


def test_get_supported_languages(transcribe_service):
    """Test getting list of supported languages."""
    languages = transcribe_service.get_supported_languages()
    
    assert 'hi-IN' in languages
    assert 'en-IN' in languages
    assert 'ta-IN' in languages
    assert languages['hi-IN'] == 'Hindi'
    assert languages['en-IN'] == 'English (India)'


def test_fetch_transcript_success(transcribe_service):
    """Test fetching and parsing transcript from S3."""
    mock_transcript_json = {
        'jobName': 'test-job',
        'results': {
            'transcripts': [{'transcript': 'Test transcript'}],
            'items': [
                {'type': 'pronunciation', 'alternatives': [{'confidence': '0.98'}]},
                {'type': 'pronunciation', 'alternatives': [{'confidence': '0.95'}]}
            ],
            'language_code': 'en-IN'
        }
    }
    
    import json
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(mock_transcript_json).encode('utf-8')
    mock_response.__enter__.return_value = mock_response
    mock_response.__exit__.return_value = None
    
    with patch('urllib.request.urlopen', return_value=mock_response):
        result = transcribe_service._fetch_transcript('https://example.com/transcript.json')
    
    assert result['text'] == 'Test transcript'
    assert result['confidence'] == pytest.approx(0.965, rel=0.01)  # Average of 0.98 and 0.95
    assert result['detected_language'] == 'en-IN'
    assert result['job_name'] == 'test-job'


def test_fetch_transcript_empty(transcribe_service):
    """Test fetching transcript with no results."""
    mock_transcript_json = {
        'jobName': 'test-job',
        'results': {}
    }
    
    import json
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(mock_transcript_json).encode('utf-8')
    mock_response.__enter__.return_value = mock_response
    mock_response.__exit__.return_value = None
    
    with patch('urllib.request.urlopen', return_value=mock_response):
        result = transcribe_service._fetch_transcript('https://example.com/transcript.json')
    
    assert result['text'] == ''
    assert result['confidence'] == 0.0
    assert result['detected_language'] == 'unknown'


def test_cleanup_s3_file(transcribe_service):
    """Test S3 file cleanup."""
    transcribe_service.s3_client.delete_object = Mock()
    
    transcribe_service._cleanup_s3_file('test-key.wav')
    
    transcribe_service.s3_client.delete_object.assert_called_once_with(
        Bucket='test-bucket',
        Key='test-key.wav'
    )


def test_cleanup_s3_file_error_ignored(transcribe_service):
    """Test that S3 cleanup errors are ignored."""
    transcribe_service.s3_client.delete_object = Mock(
        side_effect=ClientError({'Error': {'Code': 'NoSuchKey'}}, 'DeleteObject')
    )
    
    # Should not raise exception
    transcribe_service._cleanup_s3_file('test-key.wav')
