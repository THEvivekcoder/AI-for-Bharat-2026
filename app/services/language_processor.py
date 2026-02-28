"""
Language Processing Module for BharatSahayak

Provides translation, language detection, romanization, and transliteration
for Indic languages.
"""

from typing import Optional, Dict, List
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)


class LanguageProcessor:
    """
    Handles multilingual NLP operations including translation,
    language detection, romanization, and transliteration.
    """
    
    # Supported languages with their codes
    SUPPORTED_LANGUAGES = {
        'hi': 'Hindi',
        'en': 'English',
        'bn': 'Bengali',
        'te': 'Telugu',
        'mr': 'Marathi',
        'ta': 'Tamil',
        'gu': 'Gujarati',
        'kn': 'Kannada',
        'ml': 'Malayalam',
        'pa': 'Punjabi',
        'or': 'Odia',
        'as': 'Assamese'
    }
    
    # Devanagari to Roman transliteration map (simplified)
    DEVANAGARI_TO_ROMAN = {
        'अ': 'a', 'आ': 'aa', 'इ': 'i', 'ई': 'ii', 'उ': 'u', 'ऊ': 'uu',
        'ऋ': 'ri', 'ए': 'e', 'ऐ': 'ai', 'ओ': 'o', 'औ': 'au',
        'क': 'ka', 'ख': 'kha', 'ग': 'ga', 'घ': 'gha', 'ङ': 'nga',
        'च': 'cha', 'छ': 'chha', 'ज': 'ja', 'झ': 'jha', 'ञ': 'nya',
        'ट': 'ta', 'ठ': 'tha', 'ड': 'da', 'ढ': 'dha', 'ण': 'na',
        'त': 'ta', 'थ': 'tha', 'द': 'da', 'ध': 'dha', 'न': 'na',
        'प': 'pa', 'फ': 'pha', 'ब': 'ba', 'भ': 'bha', 'म': 'ma',
        'य': 'ya', 'र': 'ra', 'ल': 'la', 'व': 'va', 'श': 'sha',
        'ष': 'sha', 'स': 'sa', 'ह': 'ha',
        'ा': 'aa', 'ि': 'i', 'ी': 'ii', 'ु': 'u', 'ू': 'uu',
        'ृ': 'ri', 'े': 'e', 'ै': 'ai', 'ो': 'o', 'ौ': 'au',
        '्': '', 'ं': 'm', 'ः': 'h', 'ँ': 'n'
    }
    
    def __init__(self):
        """Initialize the Language Processor with translation and detection models."""
        self._translator = None
        self._detector = None
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize translation and language detection models."""
        try:
            # Try to import googletrans for translation
            from googletrans import Translator
            self._translator = Translator()
            logger.info("Initialized Google Translate for translation")
        except (ImportError, AttributeError) as e:
            # Handle both ImportError and AttributeError (httpcore compatibility issue)
            logger.warning(f"googletrans not available ({e}). Translation will use fallback.")
            self._translator = None
        
        try:
            # Try to import langdetect for language detection
            from langdetect import detect, detect_langs
            self._detector = detect
            self._detector_langs = detect_langs
            logger.info("Initialized langdetect for language detection")
        except ImportError:
            logger.warning("langdetect not available. Language detection will use fallback.")
            self._detector = None
    
    def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str
    ) -> str:
        """
        Translate text from source language to target language.
        
        Args:
            text: Text to translate
            source_lang: Source language code (e.g., 'hi', 'en')
            target_lang: Target language code (e.g., 'hi', 'en')
        
        Returns:
            Translated text
        
        Raises:
            ValueError: If text is None or language codes are not supported
        """
        if text is None:
            raise ValueError("Text cannot be None")
        
        if source_lang not in self.SUPPORTED_LANGUAGES:
            raise ValueError(f"Source language '{source_lang}' not supported")
        
        if target_lang not in self.SUPPORTED_LANGUAGES:
            raise ValueError(f"Target language '{target_lang}' not supported")
        
        # If source and target are the same, return original text
        if source_lang == target_lang:
            return text
        
        try:
            if self._translator:
                # Use Google Translate
                result = self._translator.translate(
                    text,
                    src=source_lang,
                    dest=target_lang
                )
                return result.text
            else:
                # Fallback: return original text with note
                logger.warning(f"Translation not available. Returning original text.")
                return text
        except Exception as e:
            logger.error(f"Translation error: {e}")
            # Return original text on error
            return text
    
    def detect_language(self, text: str) -> str:
        """
        Detect the language of input text.
        
        Args:
            text: Text to analyze
        
        Returns:
            Language code (e.g., 'hi', 'en', 'bn')
        
        Raises:
            ValueError: If text is None or empty
        """
        if text is None:
            raise ValueError("Text cannot be None")
        
        if not text.strip():
            raise ValueError("Cannot detect language of empty text")
        
        try:
            if self._detector:
                # Use langdetect
                detected = self._detector(text)
                
                # Validate detected language is supported
                if detected in self.SUPPORTED_LANGUAGES:
                    return detected
                else:
                    # Default to English if unsupported language detected
                    logger.warning(f"Detected unsupported language: {detected}. Defaulting to 'en'")
                    return 'en'
            else:
                # Fallback: simple heuristic based on character ranges
                return self._detect_language_fallback(text)
        except Exception as e:
            logger.error(f"Language detection error: {e}")
            # Default to English on error
            return 'en'
    
    def _detect_language_fallback(self, text: str) -> str:
        """
        Fallback language detection using character range heuristics.
        
        Args:
            text: Text to analyze
        
        Returns:
            Language code
        """
        # Count characters in different scripts
        devanagari_count = sum(1 for c in text if '\u0900' <= c <= '\u097F')
        bengali_count = sum(1 for c in text if '\u0980' <= c <= '\u09FF')
        telugu_count = sum(1 for c in text if '\u0C00' <= c <= '\u0C7F')
        tamil_count = sum(1 for c in text if '\u0B80' <= c <= '\u0BFF')
        gujarati_count = sum(1 for c in text if '\u0A80' <= c <= '\u0AFF')
        kannada_count = sum(1 for c in text if '\u0C80' <= c <= '\u0CFF')
        malayalam_count = sum(1 for c in text if '\u0D00' <= c <= '\u0D7F')
        gurmukhi_count = sum(1 for c in text if '\u0A00' <= c <= '\u0A7F')
        
        # Determine language based on script
        if devanagari_count > 0:
            return 'hi'  # Hindi (could also be Marathi, but default to Hindi)
        elif bengali_count > 0:
            return 'bn'
        elif telugu_count > 0:
            return 'te'
        elif tamil_count > 0:
            return 'ta'
        elif gujarati_count > 0:
            return 'gu'
        elif kannada_count > 0:
            return 'kn'
        elif malayalam_count > 0:
            return 'ml'
        elif gurmukhi_count > 0:
            return 'pa'
        else:
            return 'en'  # Default to English
    
    def romanize(self, text: str, source_script: str = 'devanagari') -> str:
        """
        Convert Indic script to Roman script (Latin alphabet).
        
        Args:
            text: Text in Indic script
            source_script: Source script name (currently only 'devanagari' supported)
        
        Returns:
            Romanized text
        
        Raises:
            ValueError: If text is None or source script is not supported
        """
        if text is None:
            raise ValueError("Text cannot be None")
        
        if source_script != 'devanagari':
            raise ValueError(f"Source script '{source_script}' not supported for romanization")
        
        # Romanize using character mapping
        result = []
        for char in text:
            if char in self.DEVANAGARI_TO_ROMAN:
                result.append(self.DEVANAGARI_TO_ROMAN[char])
            else:
                result.append(char)
        
        return ''.join(result)
    
    def transliterate(
        self,
        text: str,
        source_script: str,
        target_script: str
    ) -> str:
        """
        Convert text between Indic scripts.
        
        Args:
            text: Text to transliterate
            source_script: Source script name
            target_script: Target script name
        
        Returns:
            Transliterated text
        
        Raises:
            ValueError: If text is None or source script is not supported
        
        Note:
            This is a simplified implementation. For production use,
            consider using libraries like indic-transliteration or Aksharamukha.
        """
        if text is None:
            raise ValueError("Text cannot be None")
        
        if not text:
            return ""
        
        # For now, implement basic transliteration through romanization
        # In production, use proper transliteration libraries
        
       
        
        # Simplified approach: romanize first, then convert to target script
        # This is not accurate for production but provides basic functionality
        if source_script == 'devanagari':
            romanized = self.romanize(text, source_script)
            # For now, return romanized version
            # In production, implement proper script conversion
            logger.warning(f"Transliteration from {source_script} to {target_script} not fully implemented")
            return romanized
        else:
            raise ValueError(f"Transliteration from '{source_script}' not supported")
    
    def get_supported_languages(self) -> Dict[str, str]:
        """
        Get list of supported languages.
        
        Returns:
            Dictionary mapping language codes to language names
        """
        return self.SUPPORTED_LANGUAGES.copy()
    
    @lru_cache(maxsize=1000)
    def translate_cached(
        self,
        text: str,
        source_lang: str,
        target_lang: str
    ) -> str:
        """
        Cached version of translate for frequently used translations.
        
        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code
        
        Returns:
            Translated text
        """
        return self.translate(text, source_lang, target_lang)


# Global instance
_language_processor = None


def get_language_processor() -> LanguageProcessor:
    """Get or create the global LanguageProcessor instance."""
    global _language_processor
    if _language_processor is None:
        _language_processor = LanguageProcessor()
    return _language_processor
