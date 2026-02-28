"""
Pydantic schemas for Language Processing API
"""

from pydantic import BaseModel, Field
from typing import Dict, Optional


class TranslationRequest(BaseModel):
    """Request model for text translation."""
    text: str = Field(..., description="Text to translate", min_length=1)
    source_lang: str = Field(..., description="Source language code (e.g., 'hi', 'en')")
    target_lang: str = Field(..., description="Target language code (e.g., 'hi', 'en')")


class TranslationResponse(BaseModel):
    """Response model for text translation."""
    translated_text: str = Field(..., description="Translated text")
    source_lang: str = Field(..., description="Source language code")
    target_lang: str = Field(..., description="Target language code")
    original_text: str = Field(..., description="Original input text")


class LanguageDetectionRequest(BaseModel):
    """Request model for language detection."""
    text: str = Field(..., description="Text to analyze", min_length=1)


class LanguageDetectionResponse(BaseModel):
    """Response model for language detection."""
    detected_language: str = Field(..., description="Detected language code (e.g., 'hi', 'en')")
    language_name: str = Field(..., description="Full language name (e.g., 'Hindi', 'English')")
    confidence: Optional[float] = Field(None, description="Detection confidence (0-1)")


class TransliterationRequest(BaseModel):
    """Request model for script transliteration."""
    text: str = Field(..., description="Text to transliterate", min_length=1)
    source_script: str = Field(..., description="Source script name (e.g., 'devanagari')")
    target_script: str = Field(..., description="Target script name (e.g., 'roman', 'bengali')")


class TransliterationResponse(BaseModel):
    """Response model for script transliteration."""
    transliterated_text: str = Field(..., description="Transliterated text")
    source_script: str = Field(..., description="Source script name")
    target_script: str = Field(..., description="Target script name")
    original_text: str = Field(..., description="Original input text")


class RomanizationRequest(BaseModel):
    """Request model for romanization."""
    text: str = Field(..., description="Text in Indic script", min_length=1)
    source_script: str = Field(
        default='devanagari',
        description="Source script name (default: 'devanagari')"
    )


class RomanizationResponse(BaseModel):
    """Response model for romanization."""
    romanized_text: str = Field(..., description="Romanized text")
    source_script: str = Field(..., description="Source script name")
    original_text: str = Field(..., description="Original input text")


class SupportedLanguagesResponse(BaseModel):
    """Response model for supported languages list."""
    languages: Dict[str, str] = Field(
        ...,
        description="Dictionary mapping language codes to language names"
    )
    count: int = Field(..., description="Total number of supported languages")
