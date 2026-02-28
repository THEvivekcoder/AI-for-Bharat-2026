"""
Voice Interface Module for BharatSahayak

Provides Speech-to-Text (STT) and Text-to-Speech (TTS) functionality
for multilingual voice interactions.
"""

import io
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum

# Try to import Whisper, fall back to SpeechRecognition if not available
try:
    import whisper
    import torch
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logging.warning("Whisper not available. Install with: pip install openai-whisper torch torchaudio")

# Try to import SpeechRecognition as fallback
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False

import librosa
import soundfile as sf
import numpy as np
from pydub import AudioSegment

logger = logging.getLogger(__name__)


class SupportedLanguage(str, Enum):
    """Supported languages for voice interface"""
    HINDI = "hi"
    ENGLISH = "en"
    BENGALI = "bn"
    TELUGU = "te"
    MARATHI = "mr"
    TAMIL = "ta"
    GUJARATI = "gu"
    KANNADA = "kn"
    MALAYALAM = "ml"
    PUNJABI = "pa"


@dataclass
class TranscriptionResult:
    """Result of speech-to-text transcription"""
    text: str
    confidence: float
    detected_language: str
    language_probability: float
    segments: Optional[List[Dict[str, Any]]] = None


@dataclass
class AudioProcessingConfig:
    """Configuration for audio preprocessing"""
    target_sample_rate: int = 16000
    noise_reduction_enabled: bool = True
    normalization_enabled: bool = True
    min_confidence_threshold: float = 0.5


class SpeechToTextEngine:
    """
    Speech-to-Text engine using OpenAI Whisper model
    
    Supports multiple Indian languages with automatic language detection,
    audio preprocessing, and confidence scoring.
    """
    
    def __init__(
        self,
        model_size: str = "base",
        supported_languages: Optional[List[str]] = None,
        config: Optional[AudioProcessingConfig] = None
    ):
        """
        Initialize STT engine with Whisper model
        
        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
            supported_languages: List of supported language codes
            config: Audio processing configuration
        """
        self.model_size = model_size
        self.supported_languages = supported_languages or [lang.value for lang in SupportedLanguage]
        self.config = config or AudioProcessingConfig()
        
        if not WHISPER_AVAILABLE:
            logger.warning("Whisper not available. STT functionality will be limited.")
            logger.warning("Install with: pip install openai-whisper torch torchaudio")
            self.model = None
            self.device = "cpu"
            return
        
        logger.info(f"Loading Whisper model: {model_size}")
        self.model = whisper.load_model(model_size)
        
        # Check if CUDA is available for GPU acceleration
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {self.device}")
    
    def preprocess_audio(self, audio_data: bytes) -> np.ndarray:
        """
        Preprocess audio data: noise reduction and normalization
        
        Args:
            audio_data: Raw audio bytes
            
        Returns:
            Preprocessed audio as numpy array
        """
        try:
            # Convert bytes to AudioSegment
            audio = AudioSegment.from_file(io.BytesIO(audio_data))
            
            # Convert to mono if stereo
            if audio.channels > 1:
                audio = audio.set_channels(1)
            
            # Resample to target sample rate
            if audio.frame_rate != self.config.target_sample_rate:
                audio = audio.set_frame_rate(self.config.target_sample_rate)
            
            # Export to wav format in memory
            wav_io = io.BytesIO()
            audio.export(wav_io, format="wav")
            wav_io.seek(0)
            
            # Load with librosa for advanced processing
            audio_array, sr = librosa.load(wav_io, sr=self.config.target_sample_rate)
            
            # Apply noise reduction if enabled
            if self.config.noise_reduction_enabled:
                audio_array = self._reduce_noise(audio_array)
            
            # Apply normalization if enabled
            if self.config.normalization_enabled:
                audio_array = self._normalize_audio(audio_array)
            
            return audio_array
            
        except Exception as e:
            logger.error(f"Audio preprocessing failed: {str(e)}")
            raise ValueError(f"Failed to preprocess audio: {str(e)}")
    
    def _reduce_noise(self, audio: np.ndarray) -> np.ndarray:
        """
        Simple noise reduction using spectral gating
        
        Args:
            audio: Audio array
            
        Returns:
            Noise-reduced audio array
        """
        # Simple noise reduction: remove very low amplitude signals
        # This is a basic implementation; production would use more sophisticated methods
        threshold = np.percentile(np.abs(audio), 10)
        audio_denoised = np.where(np.abs(audio) < threshold, 0, audio)
        return audio_denoised
    
    def _normalize_audio(self, audio: np.ndarray) -> np.ndarray:
        """
        Normalize audio amplitude
        
        Args:
            audio: Audio array
            
        Returns:
            Normalized audio array
        """
        # Normalize to [-1, 1] range
        max_val = np.max(np.abs(audio))
        if max_val > 0:
            audio = audio / max_val
        return audio
    
    def detect_language(self, audio_data: bytes) -> tuple[str, float]:
        """
        Detect spoken language from audio
        
        Args:
            audio_data: Raw audio bytes
            
        Returns:
            Tuple of (language_code, confidence)
        """
        if not WHISPER_AVAILABLE or self.model is None:
            logger.warning("Whisper not available, defaulting to Hindi")
            return "hi", 0.5
        
        try:
            # Preprocess audio
            audio_array = self.preprocess_audio(audio_data)
            
            # Use Whisper's language detection
            # Load audio into Whisper format
            audio_tensor = whisper.pad_or_trim(audio_array)
            
            # Make log-Mel spectrogram
            mel = whisper.log_mel_spectrogram(audio_tensor).to(self.device)
            
            # Detect language
            _, probs = self.model.detect_language(mel)
            
            # Get the most probable language
            detected_lang = max(probs, key=probs.get)
            confidence = probs[detected_lang]
            
            # Check if detected language is in supported languages
            if detected_lang not in self.supported_languages:
                logger.warning(f"Detected unsupported language: {detected_lang}")
                # Default to Hindi if unsupported
                detected_lang = "hi"
                confidence = 0.5
            
            logger.info(f"Detected language: {detected_lang} (confidence: {confidence:.2f})")
            return detected_lang, confidence
            
        except Exception as e:
            logger.error(f"Language detection failed: {str(e)}")
            # Default to Hindi on error
            return "hi", 0.5
    
    def transcribe(
        self,
        audio_data: bytes,
        language: Optional[str] = None
    ) -> TranscriptionResult:
        """
        Convert audio to text with confidence scoring
        
        Args:
            audio_data: Raw audio bytes
            language: Optional language code (auto-detected if None)
            
        Returns:
            TranscriptionResult with text, confidence, and metadata
        """
        if not WHISPER_AVAILABLE or self.model is None:
            raise ValueError(
                "Whisper not available. Install with: pip install openai-whisper torch torchaudio"
            )
        
        try:
            # Preprocess audio
            audio_array = self.preprocess_audio(audio_data)
            
            # Detect language if not provided
            if language is None:
                detected_lang, lang_prob = self.detect_language(audio_data)
            else:
                detected_lang = language
                lang_prob = 1.0
            
            # Transcribe with Whisper
            logger.info(f"Transcribing audio in language: {detected_lang}")
            
            result = self.model.transcribe(
                audio_array,
                language=detected_lang,
                task="transcribe",
                verbose=False
            )
            
            # Extract transcription text
            text = result["text"].strip()
            
            # Calculate average confidence from segments
            segments = result.get("segments", [])
            if segments:
                # Whisper doesn't provide direct confidence, use no_speech_prob as proxy
                confidences = [1.0 - seg.get("no_speech_prob", 0.5) for seg in segments]
                avg_confidence = sum(confidences) / len(confidences)
            else:
                avg_confidence = 0.7  # Default confidence
            
            # Check minimum confidence threshold
            if avg_confidence < self.config.min_confidence_threshold:
                logger.warning(f"Low confidence transcription: {avg_confidence:.2f}")
            
            logger.info(f"Transcription successful: '{text[:50]}...' (confidence: {avg_confidence:.2f})")
            
            return TranscriptionResult(
                text=text,
                confidence=avg_confidence,
                detected_language=detected_lang,
                language_probability=lang_prob,
                segments=segments
            )
            
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            raise ValueError(f"Failed to transcribe audio: {str(e)}")
    
    def get_supported_languages(self) -> List[str]:
        """
        Get list of supported language codes
        
        Returns:
            List of language codes
        """
        return self.supported_languages


# Global STT engine instance (singleton pattern)
_stt_engine: Optional[SpeechToTextEngine] = None


def get_stt_engine() -> SpeechToTextEngine:
    """
    Get or create the global STT engine instance
    
    Returns:
        SpeechToTextEngine instance
    """
    global _stt_engine
    if _stt_engine is None:
        _stt_engine = SpeechToTextEngine(model_size="base")
    return _stt_engine



class TextToSpeechEngine:
    """
    Text-to-Speech engine supporting Hindi and regional Indian languages
    
    Uses gTTS for simplicity and broad language support. For production,
    consider Coqui TTS or Indic TTS for better quality.
    """
    
    def __init__(self, voice_profiles: Optional[Dict[str, str]] = None):
        """
        Initialize TTS engine
        
        Args:
            voice_profiles: Optional mapping of language to voice profile
        """
        self.voice_profiles = voice_profiles or {}
        
        # Language mapping for gTTS
        self.language_map = {
            "hi": "hi",  # Hindi
            "en": "en",  # English
            "bn": "bn",  # Bengali
            "te": "te",  # Telugu
            "mr": "mr",  # Marathi
            "ta": "ta",  # Tamil
            "gu": "gu",  # Gujarati
            "kn": "kn",  # Kannada
            "ml": "ml",  # Malayalam
            "pa": "pa",  # Punjabi
        }
        
        logger.info("TTS engine initialized")
    
    def synthesize(
        self,
        text: str,
        language: str,
        voice_profile: str = "default",
        slow: bool = False
    ) -> bytes:
        """
        Convert text to natural-sounding speech
        
        Args:
            text: Text to convert to speech
            language: Language code (e.g., 'hi', 'en')
            voice_profile: Voice profile to use (currently unused with gTTS)
            slow: Whether to speak slowly (useful for clarity)
            
        Returns:
            Audio data in MP3 format as bytes
        """
        try:
            from gtts import gTTS
            
            # Validate language
            if language not in self.language_map:
                logger.warning(f"Unsupported language for TTS: {language}, defaulting to Hindi")
                language = "hi"
            
            # Get gTTS language code
            gtts_lang = self.language_map[language]
            
            logger.info(f"Synthesizing speech in {language}: '{text[:50]}...'")
            
            # Create TTS object
            tts = gTTS(text=text, lang=gtts_lang, slow=slow)
            
            # Save to bytes buffer
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            
            audio_bytes = audio_buffer.read()
            
            logger.info(f"Speech synthesis successful, generated {len(audio_bytes)} bytes")
            
            return audio_bytes
            
        except Exception as e:
            logger.error(f"TTS synthesis failed: {str(e)}")
            raise ValueError(f"Failed to synthesize speech: {str(e)}")
    
    def get_supported_languages(self) -> List[str]:
        """
        Get list of supported language codes for TTS
        
        Returns:
            List of language codes
        """
        return list(self.language_map.keys())
    
    def validate_text(self, text: str) -> bool:
        """
        Validate text for TTS synthesis
        
        Args:
            text: Text to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not text or not text.strip():
            return False
        
        # Check text length (gTTS has limits)
        if len(text) > 5000:
            logger.warning(f"Text too long for TTS: {len(text)} characters")
            return False
        
        return True


# Global TTS engine instance (singleton pattern)
_tts_engine: Optional[TextToSpeechEngine] = None


def get_tts_engine() -> TextToSpeechEngine:
    """
    Get or create the global TTS engine instance
    
    Returns:
        TextToSpeechEngine instance
    """
    global _tts_engine
    if _tts_engine is None:
        _tts_engine = TextToSpeechEngine()
    return _tts_engine
