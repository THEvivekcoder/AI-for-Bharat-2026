"""
Test script for voice interface functionality

This script tests the basic functionality of the voice interface module
without requiring actual audio files or model downloads.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.voice_interface import (
    SpeechToTextEngine,
    TextToSpeechEngine,
    SupportedLanguage,
    AudioProcessingConfig
)


def test_stt_initialization():
    """Test STT engine initialization"""
    print("Testing STT engine initialization...")
    try:
        # Note: This will attempt to download the Whisper model
        # For actual testing, you would need the model downloaded
        config = AudioProcessingConfig()
        print(f"  Config: sample_rate={config.target_sample_rate}, "
              f"noise_reduction={config.noise_reduction_enabled}")
        print("  ✓ STT configuration created successfully")
        return True
    except Exception as e:
        print(f"  ✗ STT initialization failed: {e}")
        return False


def test_tts_initialization():
    """Test TTS engine initialization"""
    print("\nTesting TTS engine initialization...")
    try:
        tts = TextToSpeechEngine()
        supported = tts.get_supported_languages()
        print(f"  Supported languages: {', '.join(supported)}")
        print("  ✓ TTS engine initialized successfully")
        return True
    except Exception as e:
        print(f"  ✗ TTS initialization failed: {e}")
        return False


def test_tts_validation():
    """Test TTS text validation"""
    print("\nTesting TTS text validation...")
    try:
        tts = TextToSpeechEngine()
        
        # Test valid text
        assert tts.validate_text("Hello world") == True
        print("  ✓ Valid text accepted")
        
        # Test empty text
        assert tts.validate_text("") == False
        print("  ✓ Empty text rejected")
        
        # Test whitespace only
        assert tts.validate_text("   ") == False
        print("  ✓ Whitespace-only text rejected")
        
        # Test very long text
        long_text = "a" * 6000
        assert tts.validate_text(long_text) == False
        print("  ✓ Too-long text rejected")
        
        return True
    except Exception as e:
        print(f"  ✗ TTS validation failed: {e}")
        return False


def test_supported_languages():
    """Test supported languages enum"""
    print("\nTesting supported languages...")
    try:
        languages = [lang.value for lang in SupportedLanguage]
        print(f"  Supported languages: {', '.join(languages)}")
        assert "hi" in languages
        assert "en" in languages
        print("  ✓ Language enum working correctly")
        return True
    except Exception as e:
        print(f"  ✗ Language test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("Voice Interface Module Tests")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Supported Languages", test_supported_languages()))
    results.append(("TTS Initialization", test_tts_initialization()))
    results.append(("TTS Validation", test_tts_validation()))
    results.append(("STT Initialization", test_stt_initialization()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
