"""Lambda function for voice-to-text transcription."""
import json
import os
import base64
from datetime import datetime
from typing import Dict, Any
from src.services.transcribe_service import TranscribeService
from src.models.voice import TranscriptionResult


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for voice-to-text transcription.
    
    Expects:
        - audio_data: Base64-encoded audio file
        - language_code: Optional language code (e.g., 'hi-IN', 'en-IN')
        - audio_format: Audio format (default: 'wav')
    
    Returns:
        TranscriptionResult with text, confidence, and detected language
    """
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Extract parameters
        audio_base64 = body.get('audio_data')
        language_code = body.get('language_code')
        audio_format = body.get('audio_format', 'wav')
        
        if not audio_base64:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'audio_data is required'})
            }
        
        # Decode audio data
        audio_data = base64.b64decode(audio_base64)
        
        # Initialize transcribe service
        s3_bucket = os.environ.get('S3_BUCKET_NAME')
        if not s3_bucket:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'S3_BUCKET_NAME not configured'})
            }
        
        transcribe_service = TranscribeService(s3_bucket=s3_bucket)
        
        # Transcribe audio
        result = transcribe_service.transcribe_audio(
            audio_data=audio_data,
            language_code=language_code,
            audio_format=audio_format
        )
        
        # Create transcription result
        transcription = TranscriptionResult(
            text=result['text'],
            confidence=result['confidence'],
            detected_language=result['detected_language'],
            timestamp=datetime.utcnow()
        )
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'text': transcription.text,
                'confidence': transcription.confidence,
                'detected_language': transcription.detected_language,
                'timestamp': transcription.timestamp.isoformat()
            })
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }
