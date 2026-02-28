"""
Pydantic schemas for voice interface endpoints
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class TranscriptionResponse(BaseModel):
    """Response model for voice-to-text transcription"""
    text: str = Field(..., description="Transcribed text from audio")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Transcription confidence score")
    detected_language: str = Field(..., description="Detected language code")
    language_probability: float = Field(..., ge=0.0, le=1.0, description="Language detection confidence")
    segments: Optional[List[Dict[str, Any]]] = Field(None, description="Detailed transcription segments")


class TextToSpeechRequest(BaseModel):
    """Request model for text-to-speech conversion"""
    text: str = Field(..., min_length=1, max_length=5000, description="Text to convert to speech")
    language: str = Field(..., description="Language code (e.g., 'hi', 'en')")
    slow: bool = Field(False, description="Whether to speak slowly for clarity")


class LanguageInfo(BaseModel):
    """Information about a supported language"""
    code: str = Field(..., description="Language code (e.g., 'hi')")
    name: str = Field(..., description="Language name (e.g., 'Hindi')")
    stt_supported: bool = Field(..., description="Whether STT is supported")
    tts_supported: bool = Field(..., description="Whether TTS is supported")


class SupportedLanguagesResponse(BaseModel):
    """Response model for supported languages"""
    languages: List[LanguageInfo] = Field(..., description="List of supported languages")


class VoiceErrorResponse(BaseModel):
    """Error response for voice processing failures"""
    error: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message in English")
    message_translations: Dict[str, str] = Field(default_factory=dict, description="Error message translations")
    supported_languages: Optional[List[str]] = Field(None, description="List of supported language codes")
    retry_allowed: bool = Field(True, description="Whether retry is allowed")
