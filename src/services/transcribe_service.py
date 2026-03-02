"""Amazon Transcribe service for speech-to-text conversion."""
import boto3
import time
import uuid
from typing import Optional
from datetime import datetime
from botocore.exceptions import ClientError


class TranscribeService:
    """Service for converting speech to text using Amazon Transcribe."""
    
    def __init__(self, s3_bucket: str, region: str = "ap-south-1"):
        """
        Initialize Transcribe service.
        
        Args:
            s3_bucket: S3 bucket name for storing audio files
            region: AWS region (default: ap-south-1 for India)
        """
        self.transcribe_client = boto3.client('transcribe', region_name=region)
        self.s3_client = boto3.client('s3', region_name=region)
        self.s3_bucket = s3_bucket
        self.region = region
        
        # Supported languages for Indian context
        self.supported_languages = {
            'hi-IN': 'Hindi',
            'en-IN': 'English (India)',
            'ta-IN': 'Tamil',
            'te-IN': 'Telugu',
            'bn-IN': 'Bengali',
            'mr-IN': 'Marathi',
            'gu-IN': 'Gujarati',
            'kn-IN': 'Kannada',
            'ml-IN': 'Malayalam',
            'pa-IN': 'Punjabi'
        }
    
    def transcribe_audio(
        self,
        audio_data: bytes,
        language_code: Optional[str] = None,
        audio_format: str = 'wav'
    ) -> dict:
        """
        Transcribe audio to text using Amazon Transcribe.
        
        Args:
            audio_data: Audio file bytes
            language_code: Language code (e.g., 'hi-IN', 'en-IN'). If None, auto-detect
            audio_format: Audio format (wav, mp3, mp4, flac)
        
        Returns:
            dict with transcription result containing:
                - text: Transcribed text
                - confidence: Confidence score (0-1)
                - detected_language: Detected language code
                - job_name: Transcription job name
        """
        # Generate unique job name
        job_name = f"transcribe-{uuid.uuid4()}"
        s3_key = f"audio-uploads/{job_name}.{audio_format}"
        
        try:
            # Upload audio to S3
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=s3_key,
                Body=audio_data
            )
            
            # Construct S3 URI
            audio_uri = f"s3://{self.s3_bucket}/{s3_key}"
            
            # Start transcription job
            transcription_params = {
                'TranscriptionJobName': job_name,
                'Media': {'MediaFileUri': audio_uri},
                'MediaFormat': audio_format,
                'OutputBucketName': self.s3_bucket
            }
            
            # Add language settings
            if language_code:
                transcription_params['LanguageCode'] = language_code
            else:
                # Enable automatic language identification for Indian languages
                transcription_params['IdentifyLanguage'] = True
                transcription_params['LanguageOptions'] = list(self.supported_languages.keys())
            
            self.transcribe_client.start_transcription_job(**transcription_params)
            
            # Wait for job completion (with timeout)
            max_wait_time = 300  # 5 minutes
            wait_interval = 5  # Check every 5 seconds
            elapsed_time = 0
            
            while elapsed_time < max_wait_time:
                response = self.transcribe_client.get_transcription_job(
                    TranscriptionJobName=job_name
                )
                status = response['TranscriptionJob']['TranscriptionJobStatus']
                
                if status == 'COMPLETED':
                    # Extract transcription results
                    transcript_uri = response['TranscriptionJob']['Transcript']['TranscriptFileUri']
                    transcript_data = self._fetch_transcript(transcript_uri)
                    
                    # Clean up S3 audio file
                    self._cleanup_s3_file(s3_key)
                    
                    return transcript_data
                
                elif status == 'FAILED':
                    failure_reason = response['TranscriptionJob'].get('FailureReason', 'Unknown error')
                    self._cleanup_s3_file(s3_key)
                    raise Exception(f"Transcription failed: {failure_reason}")
                
                time.sleep(wait_interval)
                elapsed_time += wait_interval
            
            # Timeout reached
            self._cleanup_s3_file(s3_key)
            raise TimeoutError(f"Transcription job timed out after {max_wait_time} seconds")
        
        except ClientError as e:
            raise Exception(f"AWS service error: {str(e)}")
    
    def _fetch_transcript(self, transcript_uri: str) -> dict:
        """
        Fetch and parse transcript from S3 URI.
        
        Args:
            transcript_uri: S3 URI of transcript JSON file
        
        Returns:
            dict with parsed transcript data
        """
        import json
        import urllib.request
        
        with urllib.request.urlopen(transcript_uri) as response:
            transcript_json = json.loads(response.read().decode('utf-8'))
        
        # Extract transcript text and confidence
        results = transcript_json.get('results', {})
        transcripts = results.get('transcripts', [])
        items = results.get('items', [])
        
        if not transcripts:
            return {
                'text': '',
                'confidence': 0.0,
                'detected_language': 'unknown',
                'job_name': transcript_json.get('jobName', '')
            }
        
        text = transcripts[0].get('transcript', '')
        
        # Calculate average confidence from items
        confidences = [
            float(item.get('alternatives', [{}])[0].get('confidence', 0))
            for item in items
            if item.get('type') == 'pronunciation'
        ]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        # Get detected language
        language_code = results.get('language_code', 'unknown')
        
        return {
            'text': text,
            'confidence': avg_confidence,
            'detected_language': language_code,
            'job_name': transcript_json.get('jobName', '')
        }
    
    def _cleanup_s3_file(self, s3_key: str) -> None:
        """Delete temporary audio file from S3."""
        try:
            self.s3_client.delete_object(Bucket=self.s3_bucket, Key=s3_key)
        except ClientError:
            # Ignore cleanup errors
            pass
    
    def get_supported_languages(self) -> dict:
        """
        Get list of supported languages.
        
        Returns:
            dict mapping language codes to language names
        """
        return self.supported_languages.copy()
