"""Amazon Translate service for multilingual support."""

import os
import json
import hashlib
from typing import Dict, List, Optional
import boto3
from botocore.exceptions import ClientError


class TranslateService:
    """Service for translating text using Amazon Translate with DynamoDB caching."""
    
    # Supported languages: Hindi, English, Tamil, Telugu, Bengali
    SUPPORTED_LANGUAGES = ['hi', 'en', 'ta', 'te', 'bn']
    
    def __init__(self):
        """Initialize Amazon Translate client and DynamoDB for caching."""
        self.translate_client = boto3.client('translate', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
        self.dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
        self.cache_table_name = os.environ.get('TRANSLATION_CACHE_TABLE', 'BharatSahayak-TranslationCache')
        
        try:
            self.cache_table = self.dynamodb.Table(self.cache_table_name)
        except Exception:
            # Table might not exist in test environment
            self.cache_table = None
    
    def _generate_cache_key(self, text: str, source_lang: str, target_lang: str) -> str:
        """Generate a unique cache key for translation."""
        content = f"{text}|{source_lang}|{target_lang}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _get_cached_translation(self, cache_key: str) -> Optional[str]:
        """Retrieve translation from DynamoDB cache."""
        if not self.cache_table:
            return None
        
        try:
            response = self.cache_table.get_item(Key={'cache_key': cache_key})
            if 'Item' in response:
                return response['Item'].get('translated_text')
        except ClientError:
            pass
        
        return None
    
    def _cache_translation(self, cache_key: str, text: str, source_lang: str, 
                          target_lang: str, translated_text: str) -> None:
        """Store translation in DynamoDB cache."""
        if not self.cache_table:
            return
        
        try:
            import time
            ttl = int(time.time()) + 2592000  # 30 days from now
            
            self.cache_table.put_item(
                Item={
                    'cache_key': cache_key,
                    'source_text': text[:1000],  # Store first 1000 chars for reference
                    'source_lang': source_lang,
                    'target_lang': target_lang,
                    'translated_text': translated_text,
                    'ttl': ttl
                }
            )
        except Exception:
            # Cache failure shouldn't break translation
            pass
    
    def translate_text(self, text: str, source_lang: str = 'en', 
                      target_lang: str = 'hi') -> str:
        """
        Translate text from source language to target language.
        
        Args:
            text: Text to translate
            source_lang: Source language code (default: 'en')
            target_lang: Target language code (default: 'hi')
        
        Returns:
            Translated text
        
        Raises:
            ValueError: If language not supported or text is empty
            Exception: If translation fails
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        if source_lang not in self.SUPPORTED_LANGUAGES:
            raise ValueError(f"Source language '{source_lang}' not supported. "
                           f"Supported: {', '.join(self.SUPPORTED_LANGUAGES)}")
        
        if target_lang not in self.SUPPORTED_LANGUAGES:
            raise ValueError(f"Target language '{target_lang}' not supported. "
                           f"Supported: {', '.join(self.SUPPORTED_LANGUAGES)}")
        
        # If source and target are the same, return original text
        if source_lang == target_lang:
            return text
        
        # Check cache first
        cache_key = self._generate_cache_key(text, source_lang, target_lang)
        cached = self._get_cached_translation(cache_key)
        if cached:
            return cached
        
        # Translate using Amazon Translate
        try:
            response = self.translate_client.translate_text(
                Text=text,
                SourceLanguageCode=source_lang,
                TargetLanguageCode=target_lang
            )
            
            translated_text = response['TranslatedText']
            
            # Cache the translation
            self._cache_translation(cache_key, text, source_lang, target_lang, translated_text)
            
            return translated_text
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'UnsupportedLanguagePairException':
                raise ValueError(f"Translation from {source_lang} to {target_lang} not supported")
            elif error_code == 'TextSizeLimitExceededException':
                raise ValueError("Text is too long for translation")
            else:
                raise Exception(f"Translation failed: {str(e)}")
    
    def translate_scheme_content(self, scheme_data: Dict, target_languages: List[str]) -> Dict:
        """
        Translate scheme name and description to multiple languages.
        
        Args:
            scheme_data: Dictionary containing 'name' and 'description'
            target_languages: List of target language codes
        
        Returns:
            Dictionary with 'name_translations' and 'description_translations'
        """
        name_translations = {}
        description_translations = {}
        
        source_lang = 'en'  # Assume source is English
        
        for target_lang in target_languages:
            if target_lang == source_lang:
                continue
            
            try:
                # Translate name
                if 'name' in scheme_data:
                    name_translations[target_lang] = self.translate_text(
                        scheme_data['name'], source_lang, target_lang
                    )
                
                # Translate description
                if 'description' in scheme_data:
                    description_translations[target_lang] = self.translate_text(
                        scheme_data['description'], source_lang, target_lang
                    )
            except Exception as e:
                # Log error but continue with other languages
                print(f"Translation to {target_lang} failed: {str(e)}")
                continue
        
        return {
            'name_translations': name_translations,
            'description_translations': description_translations
        }
    
    def get_supported_languages(self) -> List[str]:
        """Return list of supported language codes."""
        return self.SUPPORTED_LANGUAGES.copy()
