"""Voice interface data models."""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class TranscriptionResult:
    """Result from speech-to-text transcription."""
    text: str
    confidence: float
    detected_language: str
    timestamp: datetime
    audio_duration_seconds: Optional[float] = None


@dataclass
class SynthesisResult:
    """Result from text-to-speech synthesis."""
    audio_url: str
    audio_format: str
    language: str
    voice_id: str
    timestamp: datetime
    audio_duration_seconds: Optional[float] = None
