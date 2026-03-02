"""Amazon Comprehend service for language detection."""
import boto3
from typing import List, Dict
from botocore.exceptions import ClientError


class ComprehendService:
    """Service for language detection using Amazon Comprehend."""
    
    def __init__(self, region: str = "ap-south-1"):
        """
        Initialize Comprehend service.
        
        Args:
            region: AWS region (default: ap-south-1 for India)
        """
        self.comprehend_client = boto3.client('comprehend', region_name=region)
        self.region = region
        
        # Map Comprehend language codes to our internal codes
        self.language_mapping = {
            'hi': 'hi-IN',
            'en': 'en-IN',
            'ta': 'ta-IN',
            'te': 'te-IN',
            'bn': 'bn-IN',
            'mr': 'mr-IN',
            'gu': 'gu-IN',
            'kn': 'kn-IN',
            'ml': 'ml-IN',
            'pa': 'pa-IN'
        }
    
    def detect_language(self, text: str) -> dict:
        """
        Detect the dominant language in text.
        
        Args:
            text: Text to analyze
        
        Returns:
            dict with:
                - language_code: Detected language code (e.g., 'hi-IN')
                - confidence: Confidence score (0-1)
                - all_languages: List of all detected languages with scores
        """
        try:
            # Validate text length
            if not text or len(text.strip()) == 0:
                return {
                    'language_code': 'unknown',
                    'confidence': 0.0,
                    'all_languages': []
                }
            
            # Truncate if too long (Comprehend has limits)
            if len(text) > 5000:
                text = text[:5000]
            
            # Detect dominant language
            response = self.comprehend_client.detect_dominant_language(Text=text)
            
            languages = response.get('Languages', [])
            
            if not languages:
                return {
                    'language_code': 'unknown',
                    'confidence': 0.0,
                    'all_languages': []
                }
            
            # Get dominant language (highest score)
            dominant = languages[0]
            lang_code = dominant['LanguageCode']
            confidence = dominant['Score']
            
            # Map to our internal language code
            internal_code = self.language_mapping.get(lang_code, f"{lang_code}-IN")
            
            # Format all detected languages
            all_languages = [
                {
                    'language_code': self.language_mapping.get(lang['LanguageCode'], f"{lang['LanguageCode']}-IN"),
                    'confidence': lang['Score']
                }
                for lang in languages
            ]
            
            return {
                'language_code': internal_code,
                'confidence': confidence,
                'all_languages': all_languages
            }
        
        except ClientError as e:
            raise Exception(f"AWS Comprehend error: {str(e)}")
        except Exception as e:
            raise Exception(f"Language detection error: {str(e)}")
    
    def detect_language_batch(self, texts: List[str]) -> List[dict]:
        """
        Detect languages for multiple texts in batch.
        
        Args:
            texts: List of texts to analyze (max 25)
        
        Returns:
            List of detection results for each text
        """
        try:
            if not texts or len(texts) == 0:
                return []
            
            # Comprehend batch API has a limit of 25 texts
            if len(texts) > 25:
                texts = texts[:25]
            
            # Truncate each text if needed
            truncated_texts = [
                text[:5000] if len(text) > 5000 else text
                for text in texts
            ]
            
            # Batch detect dominant language
            response = self.comprehend_client.batch_detect_dominant_language(
                TextList=truncated_texts
            )
            
            results = []
            for result in response.get('ResultList', []):
                languages = result.get('Languages', [])
                
                if not languages:
                    results.append({
                        'language_code': 'unknown',
                        'confidence': 0.0,
                        'all_languages': []
                    })
                    continue
                
                dominant = languages[0]
                lang_code = dominant['LanguageCode']
                confidence = dominant['Score']
                
                internal_code = self.language_mapping.get(lang_code, f"{lang_code}-IN")
                
                all_languages = [
                    {
                        'language_code': self.language_mapping.get(lang['LanguageCode'], f"{lang['LanguageCode']}-IN"),
                        'confidence': lang['Score']
                    }
                    for lang in languages
                ]
                
                results.append({
                    'language_code': internal_code,
                    'confidence': confidence,
                    'all_languages': all_languages
                })
            
            return results
        
        except ClientError as e:
            raise Exception(f"AWS Comprehend batch error: {str(e)}")
        except Exception as e:
            raise Exception(f"Batch language detection error: {str(e)}")
    
    def get_supported_languages(self) -> List[str]:
        """
        Get list of supported language codes.
        
        Returns:
            List of language codes
        """
        return list(self.language_mapping.values())
