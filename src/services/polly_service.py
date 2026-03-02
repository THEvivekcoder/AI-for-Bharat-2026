"""Amazon Polly service for text-to-speech conversion."""
import boto3
import uuid
from typing import Optional
from botocore.exceptions import ClientError


class PollyService:
    """Service for converting text to speech using Amazon Polly."""
    
    def __init__(self, s3_bucket: str, region: str = "ap-south-1"):
        """
        Initialize Polly service.
        
        Args:
            s3_bucket: S3 bucket name for storing generated audio files
            region: AWS region (default: ap-south-1 for India)
        """
        self.polly_client = boto3.client('polly', region_name=region)
        self.s3_client = boto3.client('s3', region_name=region)
        self.s3_bucket = s3_bucket
        self.region = region
        
        # Voice mappings for Indian languages
        self.voice_profiles = {
            'hi-IN': {'VoiceId': 'Aditi', 'LanguageCode': 'hi-IN', 'Engine': 'neural'},
            'en-IN': {'VoiceId': 'Kajal', 'LanguageCode': 'en-IN', 'Engine': 'neural'},
            'ta-IN': {'VoiceId': 'Kajal', 'LanguageCode': 'en-IN', 'Engine': 'neural'},  # Fallback
            'te-IN': {'VoiceId': 'Kajal', 'LanguageCode': 'en-IN', 'Engine': 'neural'},  # Fallback
            'bn-IN': {'VoiceId': 'Kajal', 'LanguageCode': 'en-IN', 'Engine': 'neural'},  # Fallback
            'mr-IN': {'VoiceId': 'Aditi', 'LanguageCode': 'hi-IN', 'Engine': 'neural'},  # Fallback
            'gu-IN': {'VoiceId': 'Aditi', 'LanguageCode': 'hi-IN', 'Engine': 'neural'},  # Fallback
            'kn-IN': {'VoiceId': 'Kajal', 'LanguageCode': 'en-IN', 'Engine': 'neural'},  # Fallback
            'ml-IN': {'VoiceId': 'Kajal', 'LanguageCode': 'en-IN', 'Engine': 'neural'},  # Fallback
            'pa-IN': {'VoiceId': 'Aditi', 'LanguageCode': 'hi-IN', 'Engine': 'neural'},  # Fallback
        }
    
    def synthesize_speech(
        self,
        text: str,
        language_code: str = 'hi-IN',
        output_format: str = 'mp3'
    ) -> dict:
        """
        Convert text to speech using Amazon Polly.
        
        Args:
            text: Text to convert to speech
            language_code: Language code (e.g., 'hi-IN', 'en-IN')
            output_format: Audio format (mp3, ogg_vorbis, pcm)
        
        Returns:
            dict with synthesis result containing:
                - audio_url: S3 URL of generated audio file
                - audio_format: Audio format
                - language: Language code
                - voice_id: Voice ID used
                - duration_seconds: Estimated audio duration
        """
        try:
            # Get voice profile for language
            voice_profile = self.voice_profiles.get(
                language_code,
                self.voice_profiles['hi-IN']  # Default to Hindi
            )
            
            # Synthesize speech
            response = self.polly_client.synthesize_speech(
                Text=text,
                OutputFormat=output_format,
                VoiceId=voice_profile['VoiceId'],
                LanguageCode=voice_profile['LanguageCode'],
                Engine=voice_profile['Engine']
            )
            
            # Read audio stream
            audio_data = response['AudioStream'].read()
            
            # Generate unique filename
            file_id = str(uuid.uuid4())
            s3_key = f"audio-output/{file_id}.{output_format}"
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=s3_key,
                Body=audio_data,
                ContentType=response['ContentType']
            )
            
            # Generate presigned URL (valid for 1 hour)
            audio_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.s3_bucket, 'Key': s3_key},
                ExpiresIn=3600
            )
            
            # Estimate duration (rough estimate: ~150 words per minute)
            word_count = len(text.split())
            estimated_duration = (word_count / 150) * 60  # seconds
            
            return {
                'audio_url': audio_url,
                'audio_format': output_format,
                'language': language_code,
                'voice_id': voice_profile['VoiceId'],
                'duration_seconds': estimated_duration,
                's3_key': s3_key
            }
        
        except ClientError as e:
            raise Exception(f"AWS Polly error: {str(e)}")
        except Exception as e:
            raise Exception(f"Speech synthesis error: {str(e)}")
    
    def get_supported_languages(self) -> dict:
        """
        Get list of supported languages with voice profiles.
        
        Returns:
            dict mapping language codes to voice information
        """
        return {
            lang: {
                'voice_id': profile['VoiceId'],
                'language_code': profile['LanguageCode'],
                'engine': profile['Engine']
            }
            for lang, profile in self.voice_profiles.items()
        }
    
    def cleanup_audio_file(self, s3_key: str) -> None:
        """
        Delete audio file from S3.
        
        Args:
            s3_key: S3 key of audio file to delete
        """
        try:
            self.s3_client.delete_object(Bucket=self.s3_bucket, Key=s3_key)
        except ClientError:
            # Ignore cleanup errors
            pass
