#!/usr/bin/env python3
"""
Test script for Language Processing Service

Tests translation, language detection, and transliteration endpoints.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.language_processor import get_language_processor


def test_language_detection():
    """Test language detection functionality."""
    print("\n=== Testing Language Detection ===")
    
    processor = get_language_processor()
    
    test_cases = [
        ("Hello, how are you?", "en"),
        ("नमस्ते, आप कैसे हैं?", "hi"),
        ("This is a test", "en"),
    ]
    
    for text, expected_lang in test_cases:
        try:
            detected = processor.detect_language(text)
            status = "✓" if detected == expected_lang else "✗"
            print(f"{status} Text: '{text[:30]}...' -> Detected: {detected} (Expected: {expected_lang})")
        except Exception as e:
            print(f"✗ Error detecting language for '{text[:30]}...': {e}")


def test_translation():
    """Test translation functionality."""
    print("\n=== Testing Translation ===")
    
    processor = get_language_processor()
    
    test_cases = [
        ("Hello", "en", "hi"),
        ("Thank you", "en", "hi"),
        ("Good morning", "en", "hi"),
    ]
    
    for text, source, target in test_cases:
        try:
            translated = processor.translate(text, source, target)
            print(f"✓ '{text}' ({source} -> {target}): '{translated}'")
        except Exception as e:
            print(f"✗ Error translating '{text}': {e}")


def test_romanization():
    """Test romanization functionality."""
    print("\n=== Testing Romanization ===")
    
    processor = get_language_processor()
    
    test_cases = [
        "नमस्ते",
        "धन्यवाद",
        "सरकार",
    ]
    
    for text in test_cases:
        try:
            romanized = processor.romanize(text, 'devanagari')
            print(f"✓ '{text}' -> '{romanized}'")
        except Exception as e:
            print(f"✗ Error romanizing '{text}': {e}")


def test_supported_languages():
    """Test getting supported languages."""
    print("\n=== Testing Supported Languages ===")
    
    processor = get_language_processor()
    
    try:
        languages = processor.get_supported_languages()
        print(f"✓ Supported languages ({len(languages)}):")
        for code, name in languages.items():
            print(f"  - {code}: {name}")
    except Exception as e:
        print(f"✗ Error getting supported languages: {e}")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Language Processing Service Test")
    print("=" * 60)
    
    try:
        test_supported_languages()
        test_language_detection()
        test_translation()
        test_romanization()
        
        print("\n" + "=" * 60)
        print("Test completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
