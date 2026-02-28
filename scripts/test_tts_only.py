"""
Test TTS functionality without requiring Whisper

This demonstrates that the voice interface module works
for Text-to-Speech even without Whisper installed.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

print("=" * 60)
print("Testing Text-to-Speech (TTS) Functionality")
print("=" * 60)

# Test 1: Import TTS engine
print("\n1. Testing TTS engine import...")
try:
    from app.services.voice_interface import TextToSpeechEngine
    print("   ✓ TTS engine imported successfully")
except ImportError as e:
    print(f"   ✗ Failed to import TTS engine: {e}")
    sys.exit(1)

# Test 2: Initialize TTS engine
print("\n2. Testing TTS engine initialization...")
try:
    tts = TextToSpeechEngine()
    print("   ✓ TTS engine initialized")
except Exception as e:
    print(f"   ✗ Failed to initialize TTS engine: {e}")
    sys.exit(1)

# Test 3: Get supported languages
print("\n3. Testing supported languages...")
try:
    languages = tts.get_supported_languages()
    print(f"   ✓ Supported languages: {', '.join(languages)}")
except Exception as e:
    print(f"   ✗ Failed to get languages: {e}")
    sys.exit(1)

# Test 4: Validate text
print("\n4. Testing text validation...")
try:
    assert tts.validate_text("Hello world") == True
    print("   ✓ Valid text accepted")
    
    assert tts.validate_text("") == False
    print("   ✓ Empty text rejected")
    
    assert tts.validate_text("a" * 6000) == False
    print("   ✓ Too-long text rejected")
except Exception as e:
    print(f"   ✗ Text validation failed: {e}")
    sys.exit(1)

# Test 5: Synthesize speech (requires gTTS)
print("\n5. Testing speech synthesis...")
try:
    text = "नमस्ते, यह एक परीक्षण है"
    audio_bytes = tts.synthesize(text=text, language="hi")
    print(f"   ✓ Speech synthesized: {len(audio_bytes)} bytes")
    
    # Save to file
    output_file = "test_output.mp3"
    with open(output_file, "wb") as f:
        f.write(audio_bytes)
    print(f"   ✓ Audio saved to: {output_file}")
    print(f"   ℹ Play with: open {output_file}")
    
except Exception as e:
    print(f"   ✗ Speech synthesis failed: {e}")
    print(f"   ℹ Make sure gTTS is installed: pip install gTTS")
    sys.exit(1)

# Test 6: Test English synthesis
print("\n6. Testing English synthesis...")
try:
    text = "Hello from BharatSahayak"
    audio_bytes = tts.synthesize(text=text, language="en")
    print(f"   ✓ English speech synthesized: {len(audio_bytes)} bytes")
    
    output_file = "test_english.mp3"
    with open(output_file, "wb") as f:
        f.write(audio_bytes)
    print(f"   ✓ Audio saved to: {output_file}")
    
except Exception as e:
    print(f"   ✗ English synthesis failed: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("✓ All TTS tests passed!")
print("=" * 60)
print("\nThe Text-to-Speech functionality is working correctly.")
print("You can use the TTS API endpoints without installing Whisper.")
print("\nTo test the API:")
print("  1. Start server: uvicorn app.main:app --reload")
print("  2. Test TTS: curl -X POST http://localhost:8000/api/text-to-voice \\")
print("               -H 'Content-Type: application/json' \\")
print("               -d '{\"text\": \"नमस्ते\", \"language\": \"hi\"}' \\")
print("               --output output.mp3")
print("\nNote: STT (Speech-to-Text) requires Whisper installation.")
print("      See VOICE_SETUP_HELP.md for installation instructions.")
