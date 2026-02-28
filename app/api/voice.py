"""
Voice Interface API endpoints for BharatSahayak

Provides endpoints for:
- Speech-to-Text (voice-to-text)
- Text-to-Speech (text-to-voice)
- Supported languages listing
"""

import logging
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import Response

from app.schemas.voice import (
    TranscriptionResponse,
    TextToSpeechRequest,
    SupportedLanguagesResponse,
    LanguageInfo,
    VoiceErrorResponse
)
from app.services.voice_interface import (
    get_stt_engine,
    get_tts_engine,
    SupportedLanguage
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["voice"])


# Language name mapping
LANGUAGE_NAMES = {
    "hi": "Hindi",
    "en": "English",
    "bn": "Bengali",
    "te": "Telugu",
    "mr": "Marathi",
    "ta": "Tamil",
    "gu": "Gujarati",
    "kn": "Kannada",
    "ml": "Malayalam",
    "pa": "Punjabi",
}


@router.post(
    "/voice-to-text",
    response_model=TranscriptionResponse,
    responses={
        400: {"model": VoiceErrorResponse},
        500: {"model": VoiceErrorResponse}
    },
    summary="Convert speech to text",
    description="Upload audio file and receive transcription with language detection"
)
async def voice_to_text(
    audio: UploadFile = File(..., description="Audio file (WAV, MP3, OGG, etc.)"),
    language: Optional[str] = None
) -> TranscriptionResponse:
    """
    Convert speech to text using Whisper STT engine
    
    Args:
        audio: Audio file upload
        language: Optional language code (auto-detected if not provided)
        
    Returns:
        TranscriptionResponse with text and metadata
        
    Raises:
        HTTPException: If audio processing fails
    """
    try:
        # Validate file
        if not audio.content_type or not audio.content_type.startswith("audio/"):
            logger.warning(f"Invalid content type: {audio.content_type}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "INVALID_AUDIO_FORMAT",
                    "message": "Please upload a valid audio file (WAV, MP3, OGG, etc.)",
                    "message_translations": {
                        "hi": "कृपया एक मान्य ऑडियो फ़ाइल अपलोड करें (WAV, MP3, OGG, आदि)"
                    },
                    "retry_allowed": True
                }
            )
        
        # Read audio data
        audio_data = await audio.read()
        
        if len(audio_data) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "EMPTY_AUDIO_FILE",
                    "message": "Audio file is empty",
                    "message_translations": {
                        "hi": "ऑडियो फ़ाइल खाली है"
                    },
                    "retry_allowed": True
                }
            )
        
        # Get STT engine
        stt_engine = get_stt_engine()
        
        # Validate language if provided
        if language and language not in stt_engine.get_supported_languages():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "UNSUPPORTED_LANGUAGE",
                    "message": f"Language '{language}' is not supported",
                    "message_translations": {
                        "hi": f"भाषा '{language}' समर्थित नहीं है"
                    },
                    "supported_languages": stt_engine.get_supported_languages(),
                    "retry_allowed": True
                }
            )
        
        # Transcribe audio
        logger.info(f"Processing audio file: {audio.filename} ({len(audio_data)} bytes)")
        result = stt_engine.transcribe(audio_data, language=language)
        
        return TranscriptionResponse(
            text=result.text,
            confidence=result.confidence,
            detected_language=result.detected_language,
            language_probability=result.language_probability,
            segments=result.segments
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Audio processing error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "VOICE_PROCESSING_ERROR",
                "message": "Unable to process audio. Please try speaking clearly in a supported language.",
                "message_translations": {
                    "hi": "ऑडियो प्रोसेस नहीं हो सका। कृपया समर्थित भाषा में स्पष्ट रूप से बोलें।"
                },
                "retry_allowed": True
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error in voice-to-text: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred. Please try again.",
                "message_translations": {
                    "hi": "एक अप्रत्याशित त्रुटि हुई। कृपया पुनः प्रयास करें।"
                },
                "retry_allowed": True
            }
        )


@router.post(
    "/text-to-voice",
    response_class=Response,
    responses={
        200: {
            "content": {"audio/mpeg": {}},
            "description": "Audio file in MP3 format"
        },
        400: {"model": VoiceErrorResponse},
        500: {"model": VoiceErrorResponse}
    },
    summary="Convert text to speech",
    description="Send text and receive audio in the specified language"
)
async def text_to_voice(request: TextToSpeechRequest) -> Response:
    """
    Convert text to speech using TTS engine
    
    Args:
        request: TextToSpeechRequest with text and language
        
    Returns:
        Audio file in MP3 format
        
    Raises:
        HTTPException: If TTS synthesis fails
    """
    try:
        # Get TTS engine
        tts_engine = get_tts_engine()
        
        # Validate language
        if request.language not in tts_engine.get_supported_languages():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "UNSUPPORTED_LANGUAGE",
                    "message": f"Language '{request.language}' is not supported for TTS",
                    "message_translations": {
                        "hi": f"भाषा '{request.language}' TTS के लिए समर्थित नहीं है"
                    },
                    "supported_languages": tts_engine.get_supported_languages(),
                    "retry_allowed": True
                }
            )
        
        # Validate text
        if not tts_engine.validate_text(request.text):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "INVALID_TEXT",
                    "message": "Text is empty or too long (max 5000 characters)",
                    "message_translations": {
                        "hi": "टेक्स्ट खाली है या बहुत लंबा है (अधिकतम 5000 वर्ण)"
                    },
                    "retry_allowed": True
                }
            )
        
        # Synthesize speech
        logger.info(f"Synthesizing speech in {request.language}: '{request.text[:50]}...'")
        audio_bytes = tts_engine.synthesize(
            text=request.text,
            language=request.language,
            slow=request.slow
        )
        
        # Return audio as MP3
        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f"attachment; filename=speech_{request.language}.mp3"
            }
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"TTS synthesis error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "TTS_SYNTHESIS_ERROR",
                "message": "Unable to synthesize speech. Please try again.",
                "message_translations": {
                    "hi": "भाषण संश्लेषण नहीं हो सका। कृपया पुनः प्रयास करें।"
                },
                "retry_allowed": True
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error in text-to-voice: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred. Please try again.",
                "message_translations": {
                    "hi": "एक अप्रत्याशित त्रुटि हुई। कृपया पुनः प्रयास करें।"
                },
                "retry_allowed": True
            }
        )


@router.get(
    "/languages",
    response_model=SupportedLanguagesResponse,
    summary="List supported languages",
    description="Get list of all supported languages for voice interface"
)
async def get_supported_languages() -> SupportedLanguagesResponse:
    """
    Get list of supported languages for STT and TTS
    
    Returns:
        SupportedLanguagesResponse with language information
    """
    try:
        # Get engines
        stt_engine = get_stt_engine()
        tts_engine = get_tts_engine()
        
        # Get supported languages
        stt_languages = set(stt_engine.get_supported_languages())
        tts_languages = set(tts_engine.get_supported_languages())
        
        # Combine all languages
        all_languages = stt_languages.union(tts_languages)
        
        # Build language info list
        languages = []
        for lang_code in sorted(all_languages):
            languages.append(
                LanguageInfo(
                    code=lang_code,
                    name=LANGUAGE_NAMES.get(lang_code, lang_code.upper()),
                    stt_supported=lang_code in stt_languages,
                    tts_supported=lang_code in tts_languages
                )
            )
        
        return SupportedLanguagesResponse(languages=languages)
        
    except Exception as e:
        logger.error(f"Error getting supported languages: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_ERROR",
                "message": "Unable to retrieve supported languages",
                "retry_allowed": True
            }
        )
