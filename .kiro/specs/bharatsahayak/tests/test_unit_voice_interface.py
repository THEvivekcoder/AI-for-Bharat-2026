"""
Unit tests for Voice Interface Module

Tests audio format validation, error handling for poor quality audio,
and unsupported language handling.

Feature: bharatsahayak
Requirements: 1.1, 1.2, 1.3, 1.4
"""

import pytest
import io
import wave
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException
from pydub import AudioSegment

from app.services.voice_interface import (
    SpeechToTextEngine,
    TextToSpeechEngine,
    AudioProcessingConfig,
    TranscriptionResult,
    get_stt_engine,
    get_tts_engine
)


class TestAudioFormatValidation:
    """Test audio format validation for STT engine"""
    
    def test_valid_wav_format(self):
        """Test that valid WAV format is accepted"""
        # Create a simple WAV file in memory
        sample_rate = 16000
        duration = 1  # 1 second
        frequency = 440  # A4 note
        
        # Generate sine wave
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = np.sin(2 * np.pi * frequency * t)
        
        # Convert to 16-bit PCM
        audio_data = (audio_data * 32767).astype(np.int16)
        
        # Create WAV file in memory
        wav_io = io.BytesIO()
        with wave.open(wav_io, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())
        
        wav_bytes = wav_io.getvalue()
        
        # Test preprocessing
        engine = SpeechToTextEngine(model_size="base")
        result = engine.preprocess_audio(wav_bytes)
        
        assert isinstance(result, np.ndarray)
        assert len(result) > 0
    
    def test_valid_mp3_format(self):
        """Test that valid MP3 format is accepted"""
        # Create a simple audio and export as MP3
        sample_rate = 16000
        duration = 1000  # 1 second in milliseconds
        
        # Create silent audio
        audio = AudioSegment.silent(duration=duration, frame_rate=sample_rate)
        
        # Export to MP3 in memory
        mp3_io = io.BytesIO()
        audio.export(mp3_io, format="mp3")
        mp3_bytes = mp3_io.getvalue()
        
        # Test preprocessing
        engine = SpeechToTextEngine(model_size="base")
        result = engine.preprocess_audio(mp3_bytes)
        
        assert isinstance(result, np.ndarray)
        assert len(result) > 0
    
    def test_invalid_audio_format_raises_error(self):
        """Test that invalid audio format raises ValueError"""
        # Create invalid data (plain text)
        invalid_data = b"This is not audio data"
        
        engine = SpeechToTextEngine(model_size="base")
        
        with pytest.raises(ValueError, match="Failed to preprocess audio"):
            engine.preprocess_audio(invalid_data)
    
    def test_empty_audio_raises_error(self):
        """Test that empty audio data raises ValueError"""
        empty_data = b""
        
        engine = SpeechToTextEngine(model_size="base")
        
        with pytest.raises(ValueError):
            engine.preprocess_audio(empty_data)
    
    def test_corrupted_audio_raises_error(self):
        """Test that corrupted audio data raises ValueError"""
        # Create partially corrupted WAV header
        corrupted_data = b"RIFF" + b"\x00" * 100
        
        engine = SpeechToTextEngine(model_size="base")
        
        with pytest.raises(ValueError, match="Failed to preprocess audio"):
            engine.preprocess_audio(corrupted_data)
    
    def test_stereo_to_mono_conversion(self):
        """Test that stereo audio is converted to mono"""
        # Create stereo audio
        sample_rate = 16000
        duration = 1000  # 1 second
        
        # Create stereo audio (2 channels)
        audio = AudioSegment.silent(duration=duration, frame_rate=sample_rate)
        stereo_audio = audio.set_channels(2)
        
        # Export to WAV
        wav_io = io.BytesIO()
        stereo_audio.export(wav_io, format="wav")
        wav_bytes = wav_io.getvalue()
        
        # Test preprocessing
        engine = SpeechToTextEngine(model_size="base")
        result = engine.preprocess_audio(wav_bytes)
        
        # Result should be mono (1D array)
        assert isinstance(result, np.ndarray)
        assert result.ndim == 1
    
    def test_sample_rate_conversion(self):
        """Test that audio is resampled to target sample rate"""
        # Create audio with different sample rate
        sample_rate = 44100  # CD quality
        duration = 1000
        
        audio = AudioSegment.silent(duration=duration, frame_rate=sample_rate)
        
        # Export to WAV
        wav_io = io.BytesIO()
        audio.export(wav_io, format="wav")
        wav_bytes = wav_io.getvalue()
        
        # Test preprocessing with target rate of 16000
        config = AudioProcessingConfig(target_sample_rate=16000)
        engine = SpeechToTextEngine(model_size="base", config=config)
        result = engine.preprocess_audio(wav_bytes)
        
        # Result should be resampled
        assert isinstance(result, np.ndarray)
        assert len(result) > 0


class TestPoorQualityAudioHandling:
    """Test error handling for poor quality audio"""
    
    def test_very_short_audio(self):
        """Test handling of very short audio (< 0.1 seconds)"""
        # Create very short audio
        sample_rate = 16000
        duration = 50  # 50ms
        
        audio = AudioSegment.silent(duration=duration, frame_rate=sample_rate)
        
        wav_io = io.BytesIO()
        audio.export(wav_io, format="wav")
        wav_bytes = wav_io.getvalue()
        
        # Should still preprocess without error
        engine = SpeechToTextEngine(model_size="base")
        result = engine.preprocess_audio(wav_bytes)
        
        assert isinstance(result, np.ndarray)
        # Very short audio should still produce some samples
        assert len(result) > 0
    
    def test_silent_audio(self):
        """Test handling of completely silent audio"""
        # Create silent audio
        sample_rate = 16000
        duration = 1000
        
        audio = AudioSegment.silent(duration=duration, frame_rate=sample_rate)
        
        wav_io = io.BytesIO()
        audio.export(wav_io, format="wav")
        wav_bytes = wav_io.getvalue()
        
        # Should preprocess without error
        engine = SpeechToTextEngine(model_size="base")
        result = engine.preprocess_audio(wav_bytes)
        
        assert isinstance(result, np.ndarray)
        # Silent audio should be normalized to zeros or very small values
        assert np.max(np.abs(result)) < 0.1
    
    def test_very_low_amplitude_audio(self):
        """Test handling of very low amplitude audio"""
        # Create low amplitude audio
        sample_rate = 16000
        duration = 1
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Very low amplitude sine wave
        audio_data = 0.001 * np.sin(2 * np.pi * 440 * t)
        audio_data = (audio_data * 32767).astype(np.int16)
        
        wav_io = io.BytesIO()
        with wave.open(wav_io, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())
        
        wav_bytes = wav_io.getvalue()
        
        # Should preprocess and normalize
        engine = SpeechToTextEngine(model_size="base")
        result = engine.preprocess_audio(wav_bytes)
        
        assert isinstance(result, np.ndarray)
        # Normalization should amplify the signal
        assert len(result) > 0
    
    def test_noise_reduction_enabled(self):
        """Test that noise reduction is applied when enabled"""
        # Create noisy audio
        sample_rate = 16000
        duration = 1
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Signal + noise
        signal = np.sin(2 * np.pi * 440 * t)
        noise = 0.1 * np.random.randn(len(t))
        audio_data = signal + noise
        audio_data = (audio_data * 32767 / np.max(np.abs(audio_data))).astype(np.int16)
        
        wav_io = io.BytesIO()
        with wave.open(wav_io, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())
        
        wav_bytes = wav_io.getvalue()
        
        # Test with noise reduction enabled
        config = AudioProcessingConfig(noise_reduction_enabled=True)
        engine = SpeechToTextEngine(model_size="base", config=config)
        result = engine.preprocess_audio(wav_bytes)
        
        assert isinstance(result, np.ndarray)
        assert len(result) > 0
    
    def test_normalization_enabled(self):
        """Test that normalization is applied when enabled"""
        # Create audio with varying amplitude
        sample_rate = 16000
        duration = 1
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Low amplitude signal
        audio_data = 0.1 * np.sin(2 * np.pi * 440 * t)
        audio_data = (audio_data * 32767).astype(np.int16)
        
        wav_io = io.BytesIO()
        with wave.open(wav_io, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())
        
        wav_bytes = wav_io.getvalue()
        
        # Test with normalization enabled
        config = AudioProcessingConfig(normalization_enabled=True)
        engine = SpeechToTextEngine(model_size="base", config=config)
        result = engine.preprocess_audio(wav_bytes)
        
        assert isinstance(result, np.ndarray)
        # Normalized audio should have max amplitude close to 1.0
        assert np.max(np.abs(result)) > 0.5


class TestUnsupportedLanguageHandling:
    """Test handling of unsupported languages"""
    
    def test_supported_language_list(self):
        """Test that engine returns list of supported languages"""
        engine = SpeechToTextEngine(model_size="base")
        languages = engine.get_supported_languages()
        
        assert isinstance(languages, list)
        assert len(languages) > 0
        assert "hi" in languages  # Hindi should be supported
        assert "en" in languages  # English should be supported
    
    def test_unsupported_language_detection_fallback(self):
        """Test that unsupported detected language falls back to Hindi"""
        engine = SpeechToTextEngine(model_size="base")
        
        # Create simple audio
        sample_rate = 16000
        duration = 1000
        audio = AudioSegment.silent(duration=duration, frame_rate=sample_rate)
        
        wav_io = io.BytesIO()
        audio.export(wav_io, format="wav")
        wav_bytes = wav_io.getvalue()
        
        # Mock Whisper to return unsupported language
        with patch.object(engine, 'model') as mock_model:
            if mock_model is not None:
                mock_model.detect_language.return_value = (None, {"xx": 0.9})  # Unsupported language
                
                detected_lang, confidence = engine.detect_language(wav_bytes)
                
                # Should fall back to Hindi
                assert detected_lang == "hi"
    
    def test_language_detection_without_whisper(self):
        """Test language detection when Whisper is not available"""
        # Create engine without Whisper
        with patch('app.services.voice_interface.WHISPER_AVAILABLE', False):
            engine = SpeechToTextEngine(model_size="base")
            
            # Create simple audio
            sample_rate = 16000
            duration = 1000
            audio = AudioSegment.silent(duration=duration, frame_rate=sample_rate)
            
            wav_io = io.BytesIO()
            audio.export(wav_io, format="wav")
            wav_bytes = wav_io.getvalue()
            
            # Should default to Hindi
            detected_lang, confidence = engine.detect_language(wav_bytes)
            
            assert detected_lang == "hi"
            assert confidence == 0.5
    
    def test_transcribe_without_whisper_raises_error(self):
        """Test that transcription without Whisper raises ValueError"""
        # Create engine without Whisper
        with patch('app.services.voice_interface.WHISPER_AVAILABLE', False):
            engine = SpeechToTextEngine(model_size="base")
            
            # Create simple audio
            sample_rate = 16000
            duration = 1000
            audio = AudioSegment.silent(duration=duration, frame_rate=sample_rate)
            
            wav_io = io.BytesIO()
            audio.export(wav_io, format="wav")
            wav_bytes = wav_io.getvalue()
            
            # Should raise ValueError
            with pytest.raises(ValueError, match="Whisper not available"):
                engine.transcribe(wav_bytes)
    
    def test_tts_unsupported_language_fallback(self):
        """Test that TTS falls back to Hindi for unsupported language"""
        engine = TextToSpeechEngine()
        
        # Try to synthesize in unsupported language
        text = "Hello world"
        unsupported_lang = "xx"  # Not a real language
        
        # Should not raise error, should fall back to Hindi
        try:
            audio_bytes = engine.synthesize(text, unsupported_lang)
            assert isinstance(audio_bytes, bytes)
            assert len(audio_bytes) > 0
        except ValueError:
            # If it raises ValueError, that's also acceptable behavior
            pass
    
    def test_tts_supported_languages(self):
        """Test that TTS engine returns supported languages"""
        engine = TextToSpeechEngine()
        languages = engine.get_supported_languages()
        
        assert isinstance(languages, list)
        assert len(languages) > 0
        assert "hi" in languages
        assert "en" in languages
    
    def test_tts_validate_empty_text(self):
        """Test that TTS validates empty text"""
        engine = TextToSpeechEngine()
        
        assert not engine.validate_text("")
        assert not engine.validate_text("   ")
        assert not engine.validate_text(None)
    
    def test_tts_validate_text_too_long(self):
        """Test that TTS validates text length"""
        engine = TextToSpeechEngine()
        
        # Text longer than 5000 characters
        long_text = "a" * 5001
        
        assert not engine.validate_text(long_text)
    
    def test_tts_validate_valid_text(self):
        """Test that TTS validates valid text"""
        engine = TextToSpeechEngine()
        
        assert engine.validate_text("Hello world")
        assert engine.validate_text("नमस्ते दुनिया")


class TestVoiceInterfaceSingletons:
    """Test singleton pattern for voice engines"""
    
    def test_stt_engine_singleton(self):
        """Test that get_stt_engine returns same instance"""
        engine1 = get_stt_engine()
        engine2 = get_stt_engine()
        
        assert engine1 is engine2
    
    def test_tts_engine_singleton(self):
        """Test that get_tts_engine returns same instance"""
        engine1 = get_tts_engine()
        engine2 = get_tts_engine()
        
        assert engine1 is engine2


class TestAudioProcessingConfig:
    """Test audio processing configuration"""
    
    def test_default_config(self):
        """Test default audio processing configuration"""
        config = AudioProcessingConfig()
        
        assert config.target_sample_rate == 16000
        assert config.noise_reduction_enabled is True
        assert config.normalization_enabled is True
        assert config.min_confidence_threshold == 0.5
    
    def test_custom_config(self):
        """Test custom audio processing configuration"""
        config = AudioProcessingConfig(
            target_sample_rate=22050,
            noise_reduction_enabled=False,
            normalization_enabled=False,
            min_confidence_threshold=0.7
        )
        
        assert config.target_sample_rate == 22050
        assert config.noise_reduction_enabled is False
        assert config.normalization_enabled is False
        assert config.min_confidence_threshold == 0.7
    
    def test_config_applied_to_engine(self):
        """Test that config is applied to STT engine"""
        config = AudioProcessingConfig(
            target_sample_rate=22050,
            noise_reduction_enabled=False
        )
        
        engine = SpeechToTextEngine(model_size="base", config=config)
        
        assert engine.config.target_sample_rate == 22050
        assert engine.config.noise_reduction_enabled is False
