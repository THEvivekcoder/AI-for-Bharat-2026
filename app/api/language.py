"""
Language Processing API endpoints for BharatSahayak

Provides translation, language detection, and transliteration services.
"""

from fastapi import APIRouter, HTTPException, status
from typing import Dict
import logging

from app.schemas.language import (
    TranslationRequest,
    TranslationResponse,
    LanguageDetectionRequest,
    LanguageDetectionResponse,
    TransliterationRequest,
    TransliterationResponse,
    RomanizationRequest,
    RomanizationResponse,
    SupportedLanguagesResponse
)
from app.services.language_processor import get_language_processor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["language"])


@router.post("/translate", response_model=TranslationResponse)
async def translate_text(request: TranslationRequest):
    """
    Translate text from source language to target language.
    
    Supports translation between Hindi, English, and other Indian languages.
    
    Args:
        request: Translation request with text and language codes
    
    Returns:
        TranslationResponse with translated text
    
    Raises:
        HTTPException: If translation fails or languages not supported
    """
    try:
        processor = get_language_processor()
        
        # Validate language codes
        supported = processor.get_supported_languages()
        if request.source_lang not in supported:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Source language '{request.source_lang}' not supported. "
                       f"Supported languages: {list(supported.keys())}"
            )
        
        if request.target_lang not in supported:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Target language '{request.target_lang}' not supported. "
                       f"Supported languages: {list(supported.keys())}"
            )
        
        # Perform translation
        translated = processor.translate(
            text=request.text,
            source_lang=request.source_lang,
            target_lang=request.target_lang
        )
        
        return TranslationResponse(
            translated_text=translated,
            source_lang=request.source_lang,
            target_lang=request.target_lang,
            original_text=request.text
        )
    
    except ValueError as e:
        logger.error(f"Translation validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Translation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Translation service temporarily unavailable"
        )


@router.post("/detect-language", response_model=LanguageDetectionResponse)
async def detect_language(request: LanguageDetectionRequest):
    """
    Detect the language of input text.
    
    Supports detection of Hindi, English, and other Indian languages.
    
    Args:
        request: Language detection request with text
    
    Returns:
        LanguageDetectionResponse with detected language code and name
    
    Raises:
        HTTPException: If detection fails
    """
    try:
        processor = get_language_processor()
        
        # Detect language
        detected_code = processor.detect_language(request.text)
        
        # Get language name
        supported = processor.get_supported_languages()
        language_name = supported.get(detected_code, "Unknown")
        
        return LanguageDetectionResponse(
            detected_language=detected_code,
            language_name=language_name,
            confidence=None  # langdetect doesn't provide confidence in simple detect()
        )
    
    except ValueError as e:
        logger.error(f"Language detection validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Language detection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Language detection service temporarily unavailable"
        )


@router.post("/transliterate", response_model=TransliterationResponse)
async def transliterate_text(request: TransliterationRequest):
    """
    Convert text between Indic scripts.
    
    Currently supports basic transliteration from Devanagari to Roman script.
    For production use, consider using specialized libraries like indic-transliteration.
    
    Args:
        request: Transliteration request with text and script names
    
    Returns:
        TransliterationResponse with transliterated text
    
    Raises:
        HTTPException: If transliteration fails or scripts not supported
    """
    try:
        processor = get_language_processor()
        
        # Perform transliteration
        transliterated = processor.transliterate(
            text=request.text,
            source_script=request.source_script,
            target_script=request.target_script
        )
        
        return TransliterationResponse(
            transliterated_text=transliterated,
            source_script=request.source_script,
            target_script=request.target_script,
            original_text=request.text
        )
    
    except ValueError as e:
        logger.error(f"Transliteration validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Transliteration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Transliteration service temporarily unavailable"
        )


@router.post("/romanize", response_model=RomanizationResponse)
async def romanize_text(request: RomanizationRequest):
    """
    Convert Indic script to Roman script (Latin alphabet).
    
    Currently supports Devanagari to Roman conversion.
    
    Args:
        request: Romanization request with text and source script
    
    Returns:
        RomanizationResponse with romanized text
    
    Raises:
        HTTPException: If romanization fails or script not supported
    """
    try:
        processor = get_language_processor()
        
        # Perform romanization
        romanized = processor.romanize(
            text=request.text,
            source_script=request.source_script
        )
        
        return RomanizationResponse(
            romanized_text=romanized,
            source_script=request.source_script,
            original_text=request.text
        )
    
    except ValueError as e:
        logger.error(f"Romanization validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Romanization error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Romanization service temporarily unavailable"
        )


@router.get("/languages", response_model=SupportedLanguagesResponse)
async def get_supported_languages():
    """
    Get list of supported languages for translation and detection.
    
    Returns:
        SupportedLanguagesResponse with language codes and names
    """
    try:
        processor = get_language_processor()
        languages = processor.get_supported_languages()
        
        return SupportedLanguagesResponse(
            languages=languages,
            count=len(languages)
        )
    
    except Exception as e:
        logger.error(f"Error retrieving supported languages: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve supported languages"
        )
