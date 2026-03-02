"""Lambda function for text-to-speech synthesis."""
import json
import os
from datetime import datetime
from typing import Dict, Any
from src.services.polly_service import PollyService
from src.models.voice import SynthesisResult


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for text-to-speech synthesis.
    
    Expects:
        - text: Text to convert to speech
        - language_code: Language code (default: 'hi-IN')
        - output_format: Audio format (default: 'mp3')
    
    Returns:
        SynthesisResult with audio URL and metadata
    """
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Extract parameters
        text = body.get('text')
        language_code = body.get('language_code', 'hi-IN')
        output_format = body.get('output_format', 'mp3')
        
        if not text:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'text is required'})
            }
        
        # Validate text length (Polly has limits)
        if len(text) > 3000:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'text exceeds maximum length of 3000 characters'})
            }
        
        # Initialize Polly service
        s3_bucket = os.environ.get('S3_BUCKET_NAME')
        if not s3_bucket:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'S3_BUCKET_NAME not configured'})
            }
        
        polly_service = PollyService(s3_bucket=s3_bucket)
        
        # Synthesize speech
        result = polly_service.synthesize_speech(
            text=text,
            language_code=language_code,
            output_format=output_format
        )
        
        # Create synthesis result
        synthesis = SynthesisResult(
            audio_url=result['audio_url'],
            audio_format=result['audio_format'],
            language=result['language'],
            voice_id=result['voice_id'],
            timestamp=datetime.utcnow(),
            audio_duration_seconds=result['duration_seconds']
        )
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'audio_url': synthesis.audio_url,
                'audio_format': synthesis.audio_format,
                'language': synthesis.language,
                'voice_id': synthesis.voice_id,
                'timestamp': synthesis.timestamp.isoformat(),
                'audio_duration_seconds': synthesis.audio_duration_seconds
            })
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }
