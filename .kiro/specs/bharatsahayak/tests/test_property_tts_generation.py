"""
Property-Based Test: Text-to-Speech Audio Generation
Feature: bharatsahayak, Property 2: Text-to-Speech Audio Generation

For any text input and supported language, the Voice_Interface should generate 
valid audio output that can be played without errors.

Validates: Requirements 1.2

Testing Strategy:
1. Generate audio from various text inputs in supported languages
2. Verify audio is valid and playable (not corrupted)
3. Verify audio has reasonable duration relative to text length
4. Test edge cases (empty text, very long text, special characters)
"""
import pytest
import io
import wave
from pathlib import Path
from hypothesis import given, settings, strategies as st, HealthCheck, assume
from hypothesis.strategies import composite
from pydub import AudioSegment

from app.services.voice_interface import (
    TextToSpeechEngine,
    SupportedLanguage
)


# Supported languages for TTS testing (only those supported by gTTS)
TTS_LANGUAGES = ["hi", "en", "bn", "te", "mr", "ta", "gu", "kn", "ml"]


def is_valid_audio(audio_bytes: bytes) -> bool:
    """
    Check if audio bytes represent valid, playable audio.
    
    Args:
        audio_bytes: Audio data in MP3 format
        
    Returns:
        True if audio is valid and playable, False otherwise
    """
    try:
        # Try to load audio with pydub
        audio = AudioSegment.from_mp3(io.BytesIO(audio_bytes))
        
        # Check basic properties
        if audio.duration_seconds <= 0:
            return False
        
        if audio.frame_rate <= 0:
            return False
        
        if len(audio.raw_data) == 0:
            return False
        
        return True
        
    except Exception:
        return False


def get_audio_duration(audio_bytes: bytes) -> float:
    """
    Get duration of audio in seconds.
    
    Args:
        audio_bytes: Audio data in MP3 format
        
    Returns:
        Duration in seconds
    """
    try:
        audio = AudioSegment.from_mp3(io.BytesIO(audio_bytes))
        return audio.duration_seconds
    except Exception:
        return 0.0


def estimate_speech_duration(text: str, language: str) -> tuple[float, float]:
    """
    Estimate expected speech duration for text.
    
    Average speaking rates:
    - English: ~150 words per minute (2.5 words/sec)
    - Hindi/Indic: ~120 words per minute (2 words/sec)
    
    Args:
        text: Text to be spoken
        language: Language code
        
    Returns:
        Tuple of (min_duration, max_duration) in seconds
    """
    word_count = len(text.split())
    
    if word_count == 0:
        return 0.0, 0.5  # Empty text might produce minimal audio
    
    # Determine speaking rate based on language
    if language == "en":
        words_per_second = 2.5
    else:
        words_per_second = 2.0
    
    # Calculate expected duration
    expected_duration = word_count / words_per_second
    
    # Allow 100% variance (TTS can be faster or slower, especially for short texts)
    min_duration = expected_duration * 0.3
    max_duration = expected_duration * 3.0
    
    # Minimum duration of 0.3 seconds for any non-empty text
    min_duration = max(0.3, min_duration)
    
    # Maximum duration should be at least 2 seconds for very short texts
    max_duration = max(2.0, max_duration)
    
    return min_duration, max_duration


# Strategy for generating test sentences in different languages
@composite
def _test_text_strategy(draw):
    """Generate test text for TTS testing (internal use only - not a test)"""
    # Select a language from supported TTS languages
    language = draw(st.sampled_from(TTS_LANGUAGES))
    
    # Define sample texts for each language
    texts_by_language = {
        "hi": [
            "नमस्ते",
            "मुझे सरकारी योजनाओं के बारे में जानकारी चाहिए",
            "मैं एक किसान हूं और मुझे फसल की सलाह चाहिए",
            "आज मौसम कैसा है",
            "मुझे स्वास्थ्य सेवाओं की जानकारी चाहिए",
        ],
        "en": [
            "Hello",
            "I need information about government schemes",
            "I am a farmer and need crop advice",
            "What is the weather today",
            "I need health services information",
        ],
        "bn": [
            "আমার নাম রাজ",
            "আমি একজন কৃষক",
            "আমার স্বাস্থ্য সেবা প্রয়োজন",
        ],
        "te": [
            "నా పేరు రాజ్",
            "నేను ఒక రైతును",
            "నాకు ఆరోగ్య సేవలు కావాలి",
        ],
        "mr": [
            "माझे नाव राज आहे",
            "मी एक शेतकरी आहे",
            "मला आरोग्य सेवा हवी आहे",
        ],
        "ta": [
            "என் பெயர் ராஜ்",
            "நான் ஒரு விவசாயி",
            "எனக்கு சுகாதார சேவைகள் தேவை",
        ],
        "gu": [
            "મારું નામ રાજ છે",
            "હું એક ખેડૂત છું",
            "મને આરોગ્य સેવાઓની જરૂર છે",
        ],
        "kn": [
            "ನನ್ನ ಹೆಸರು ರಾಜ್",
            "ನಾನು ಒಬ್ಬ ರೈತ",
            "ನನಗೆ ಆರೋಗ್ಯ ಸೇವೆಗಳು ಬೇಕು",
        ],
        "ml": [
            "എന്റെ പേര് രാജ്",
            "ഞാൻ ഒരു കർഷകനാണ്",
            "എനിക്ക് ആരോഗ്യ സേവനങ്ങൾ വേണം",
        ],
    }
    
    # Get texts for the selected language
    texts = texts_by_language.get(language, ["Hello", "Test"])
    
    # Select a text
    text = draw(st.sampled_from(texts))
    
    return language, text


@pytest.fixture(scope="module")
def tts_engine():
    """Create TTS engine for testing"""
    return TextToSpeechEngine()


@settings(
    max_examples=5,  # Reduced for faster checkpoint testing
    deadline=30000,  # 30 seconds per test (TTS can be slow)
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow]
)
@given(test_data=_test_text_strategy())
def test_tts_audio_generation(test_data, tts_engine):
    """
    Feature: bharatsahayak, Property 2: Text-to-Speech Audio Generation
    
    For any text input and supported language, the Voice_Interface should generate 
    valid audio output that can be played without errors.
    
    This property ensures the TTS engine can reliably convert text to speech
    for users receiving voice responses from the system.
    """
    language, text = test_data
    
    # Assume non-empty text
    assume(len(text.strip()) > 0)
    
    try:
        # Synthesize speech
        audio_bytes = tts_engine.synthesize(text=text, language=language)
        
        # Assert audio was generated
        assert audio_bytes is not None, "TTS should return audio data"
        assert len(audio_bytes) > 0, "Audio data should not be empty"
        
        # Assert audio is valid and playable
        assert is_valid_audio(audio_bytes), (
            f"Generated audio is not valid or playable. "
            f"Language: {language}, Text: '{text}'"
        )
        
        # Get audio duration
        duration = get_audio_duration(audio_bytes)
        assert duration > 0, "Audio duration should be positive"
        
        # Verify duration is reasonable for the text length
        min_duration, max_duration = estimate_speech_duration(text, language)
        assert min_duration <= duration <= max_duration, (
            f"Audio duration {duration:.2f}s is outside expected range "
            f"[{min_duration:.2f}s, {max_duration:.2f}s] for text: '{text}' "
            f"(language: {language})"
        )
        
        # Verify audio has reasonable size (not too small or too large)
        # MP3 bitrate is typically 32-320 kbps, so size should be proportional to duration
        min_size = int(duration * 1000)  # ~8 kbps minimum
        max_size = int(duration * 50000)  # ~400 kbps maximum
        assert min_size <= len(audio_bytes) <= max_size, (
            f"Audio size {len(audio_bytes)} bytes is outside expected range "
            f"[{min_size}, {max_size}] for duration {duration:.2f}s"
        )
        
    except ImportError as e:
        pytest.skip(f"Required dependencies not available: {str(e)}")
    except Exception as e:
        pytest.fail(
            f"TTS test failed for language {language} with text '{text}': {str(e)}"
        )


def test_tts_english_example(tts_engine):
    """
    Example test: Verify TTS generates valid audio for English text.
    
    This is a concrete example to complement the property-based test.
    """
    text = "Hello, I need information about government schemes"
    language = "en"
    
    try:
        # Synthesize speech
        audio_bytes = tts_engine.synthesize(text=text, language=language)
        
        # Verify audio is valid
        assert audio_bytes is not None
        assert len(audio_bytes) > 0
        assert is_valid_audio(audio_bytes), "Audio should be valid and playable"
        
        # Verify duration
        duration = get_audio_duration(audio_bytes)
        assert duration > 0, "Audio should have positive duration"
        
        # For this specific text (~8 words), expect 2-6 seconds
        assert 2.0 <= duration <= 6.0, (
            f"Duration {duration:.2f}s is outside expected range for English text"
        )
        
    except ImportError:
        pytest.skip("Required dependencies not available")


def test_tts_hindi_example(tts_engine):
    """
    Example test: Verify TTS generates valid audio for Hindi text.
    
    This is a concrete example to complement the property-based test.
    """
    text = "नमस्ते मुझे सरकारी योजनाओं के बारे में जानकारी चाहिए"
    language = "hi"
    
    try:
        # Synthesize speech
        audio_bytes = tts_engine.synthesize(text=text, language=language)
        
        # Verify audio is valid
        assert audio_bytes is not None
        assert len(audio_bytes) > 0
        assert is_valid_audio(audio_bytes), "Audio should be valid and playable"
        
        # Verify duration
        duration = get_audio_duration(audio_bytes)
        assert duration > 0, "Audio should have positive duration"
        
        # For this specific text (~7 words), expect 2-7 seconds
        assert 2.0 <= duration <= 7.0, (
            f"Duration {duration:.2f}s is outside expected range for Hindi text"
        )
        
    except ImportError:
        pytest.skip("Required dependencies not available")


def test_tts_empty_text_handling(tts_engine):
    """
    Edge case test: Verify TTS handles empty text gracefully.
    """
    text = ""
    language = "en"
    
    # TTS should reject empty text
    is_valid = tts_engine.validate_text(text)
    assert not is_valid, "Empty text should not be valid for TTS"


def test_tts_very_long_text_handling(tts_engine):
    """
    Edge case test: Verify TTS handles very long text appropriately.
    """
    # Create text longer than 5000 characters
    text = "This is a test sentence. " * 250  # ~6250 characters
    language = "en"
    
    # TTS should reject text that's too long
    is_valid = tts_engine.validate_text(text)
    assert not is_valid, "Text longer than 5000 characters should not be valid"


def test_tts_special_characters(tts_engine):
    """
    Edge case test: Verify TTS handles special characters and punctuation.
    """
    text = "Hello! How are you? I'm fine, thank you."
    language = "en"
    
    try:
        # Should handle punctuation gracefully
        audio_bytes = tts_engine.synthesize(text=text, language=language)
        
        assert audio_bytes is not None
        assert len(audio_bytes) > 0
        assert is_valid_audio(audio_bytes), "Should handle punctuation"
        
    except ImportError:
        pytest.skip("Required dependencies not available")


def test_tts_numbers_and_digits(tts_engine):
    """
    Edge case test: Verify TTS handles numbers correctly.
    """
    text = "The price is 1500 rupees per quintal"
    language = "en"
    
    try:
        # Should convert numbers to spoken form
        audio_bytes = tts_engine.synthesize(text=text, language=language)
        
        assert audio_bytes is not None
        assert len(audio_bytes) > 0
        assert is_valid_audio(audio_bytes), "Should handle numbers"
        
    except ImportError:
        pytest.skip("Required dependencies not available")


def test_tts_mixed_script(tts_engine):
    """
    Edge case test: Verify TTS handles mixed script (English + Hindi).
    """
    text = "Hello नमस्ते"
    language = "hi"
    
    try:
        # Should handle mixed script gracefully
        audio_bytes = tts_engine.synthesize(text=text, language=language)
        
        assert audio_bytes is not None
        assert len(audio_bytes) > 0
        assert is_valid_audio(audio_bytes), "Should handle mixed script"
        
    except ImportError:
        pytest.skip("Required dependencies not available")


def test_tts_slow_mode(tts_engine):
    """
    Test: Verify TTS slow mode produces longer audio.
    """
    text = "Hello this is a test"
    language = "en"
    
    try:
        # Generate normal speed audio
        normal_audio = tts_engine.synthesize(text=text, language=language, slow=False)
        normal_duration = get_audio_duration(normal_audio)
        
        # Generate slow speed audio
        slow_audio = tts_engine.synthesize(text=text, language=language, slow=True)
        slow_duration = get_audio_duration(slow_audio)
        
        # Slow audio should be longer
        assert slow_duration > normal_duration, (
            f"Slow mode audio ({slow_duration:.2f}s) should be longer than "
            f"normal mode ({normal_duration:.2f}s)"
        )
        
        # Both should be valid
        assert is_valid_audio(normal_audio)
        assert is_valid_audio(slow_audio)
        
    except ImportError:
        pytest.skip("Required dependencies not available")


def test_tts_all_supported_languages(tts_engine):
    """
    Test: Verify TTS works for all supported languages.
    """
    supported_languages = tts_engine.get_supported_languages()
    
    # Should support at least Hindi and English
    assert "hi" in supported_languages, "Hindi should be supported"
    assert "en" in supported_languages, "English should be supported"
    
    # Test a simple phrase in each supported language
    test_phrase = "Hello"
    
    # Languages that gTTS actually supports (pa/Punjabi is not supported by gTTS)
    gtts_supported = ["hi", "en", "bn", "te", "mr", "ta", "gu", "kn", "ml"]
    
    for lang in supported_languages:
        # Skip languages not supported by gTTS
        if lang not in gtts_supported:
            continue
            
        try:
            audio_bytes = tts_engine.synthesize(text=test_phrase, language=lang)
            assert audio_bytes is not None, f"TTS should work for language: {lang}"
            assert len(audio_bytes) > 0, f"Audio should not be empty for language: {lang}"
            assert is_valid_audio(audio_bytes), f"Audio should be valid for language: {lang}"
        except ImportError:
            pytest.skip(f"Required dependencies not available for language: {lang}")


def test_tts_unsupported_language_handling(tts_engine):
    """
    Edge case test: Verify TTS handles unsupported languages gracefully.
    """
    text = "Hello"
    unsupported_language = "xyz"  # Invalid language code
    
    try:
        # Should either raise an error or default to a supported language
        audio_bytes = tts_engine.synthesize(text=text, language=unsupported_language)
        
        # If it doesn't raise an error, it should still produce valid audio
        # (likely defaulted to Hindi or English)
        if audio_bytes is not None:
            assert is_valid_audio(audio_bytes), "Should produce valid audio even with unsupported language"
            
    except (ValueError, KeyError):
        # Expected behavior: raise an error for unsupported language
        pass
    except ImportError:
        pytest.skip("Required dependencies not available")


def test_audio_validation_function():
    """
    Unit test: Verify audio validation function works correctly.
    """
    # Test with invalid audio data
    assert not is_valid_audio(b""), "Empty bytes should not be valid audio"
    assert not is_valid_audio(b"not audio data"), "Random bytes should not be valid audio"
    
    # Note: We can't easily create valid MP3 data without external tools,
    # so we rely on the TTS engine tests to validate real audio


def test_duration_estimation():
    """
    Unit test: Verify speech duration estimation is reasonable.
    """
    # Short text
    min_dur, max_dur = estimate_speech_duration("Hello", "en")
    assert 0.3 <= min_dur <= 1.0, "Short text should have short minimum duration"
    assert 2.0 <= max_dur <= 5.0, "Short text should have reasonable maximum duration"
    
    # Longer text
    text = "This is a longer sentence with multiple words"
    min_dur, max_dur = estimate_speech_duration(text, "en")
    assert min_dur > 0.5, "Longer text should have longer minimum duration"
    assert max_dur > min_dur, "Maximum duration should be greater than minimum"
    
    # Empty text
    min_dur, max_dur = estimate_speech_duration("", "en")
    assert min_dur == 0.0, "Empty text should have zero minimum duration"
    assert max_dur >= 0.0, "Empty text should have non-negative maximum duration"
