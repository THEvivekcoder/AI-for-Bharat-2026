#!/usr/bin/env python3
"""
Test script for Language Processing API endpoints

Tests the REST API endpoints for translation, detection, and transliteration.
"""

import requests
import json
import sys


BASE_URL = "http://localhost:8000"


def test_supported_languages():
    """Test GET /api/languages endpoint."""
    print("\n=== Testing GET /api/languages ===")
    
    try:
        response = requests.get(f"{BASE_URL}/api/languages")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Status: {response.status_code}")
            print(f"✓ Supported languages count: {data['count']}")
            print(f"✓ Languages: {list(data['languages'].keys())}")
            return True
        else:
            print(f"✗ Status: {response.status_code}")
            print(f"✗ Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_language_detection():
    """Test POST /api/detect-language endpoint."""
    print("\n=== Testing POST /api/detect-language ===")
    
    test_cases = [
        {"text": "Hello, how are you?", "expected": "en"},
        {"text": "नमस्ते, आप कैसे हैं?", "expected": "hi"},
        {"text": "This is a test message", "expected": "en"},
    ]
    
    success_count = 0
    
    for test_case in test_cases:
        try:
            response = requests.post(
                f"{BASE_URL}/api/detect-language",
                json={"text": test_case["text"]}
            )
            
            if response.status_code == 200:
                data = response.json()
                detected = data["detected_language"]
                expected = test_case["expected"]
                
                if detected == expected:
                    print(f"✓ Text: '{test_case['text'][:30]}...' -> {detected}")
                    success_count += 1
                else:
                    print(f"✗ Text: '{test_case['text'][:30]}...' -> {detected} (expected {expected})")
            else:
                print(f"✗ Status: {response.status_code} for text: '{test_case['text'][:30]}...'")
        except Exception as e:
            print(f"✗ Error: {e}")
    
    return success_count == len(test_cases)


def test_translation():
    """Test POST /api/translate endpoint."""
    print("\n=== Testing POST /api/translate ===")
    
    test_cases = [
        {"text": "Hello", "source_lang": "en", "target_lang": "hi"},
        {"text": "Thank you", "source_lang": "en", "target_lang": "hi"},
        {"text": "Good morning", "source_lang": "en", "target_lang": "hi"},
    ]
    
    success_count = 0
    
    for test_case in test_cases:
        try:
            response = requests.post(
                f"{BASE_URL}/api/translate",
                json=test_case
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ '{test_case['text']}' ({test_case['source_lang']} -> {test_case['target_lang']}): '{data['translated_text']}'")
                success_count += 1
            else:
                print(f"✗ Status: {response.status_code} for text: '{test_case['text']}'")
                print(f"  Response: {response.text}")
        except Exception as e:
            print(f"✗ Error: {e}")
    
    return success_count == len(test_cases)


def test_romanization():
    """Test POST /api/romanize endpoint."""
    print("\n=== Testing POST /api/romanize ===")
    
    test_cases = [
        {"text": "नमस्ते", "source_script": "devanagari"},
        {"text": "धन्यवाद", "source_script": "devanagari"},
        {"text": "सरकार", "source_script": "devanagari"},
    ]
    
    success_count = 0
    
    for test_case in test_cases:
        try:
            response = requests.post(
                f"{BASE_URL}/api/romanize",
                json=test_case
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ '{test_case['text']}' -> '{data['romanized_text']}'")
                success_count += 1
            else:
                print(f"✗ Status: {response.status_code} for text: '{test_case['text']}'")
                print(f"  Response: {response.text}")
        except Exception as e:
            print(f"✗ Error: {e}")
    
    return success_count == len(test_cases)


def test_transliteration():
    """Test POST /api/transliterate endpoint."""
    print("\n=== Testing POST /api/transliterate ===")
    
    test_cases = [
        {
            "text": "नमस्ते",
            "source_script": "devanagari",
            "target_script": "roman"
        },
    ]
    
    success_count = 0
    
    for test_case in test_cases:
        try:
            response = requests.post(
                f"{BASE_URL}/api/transliterate",
                json=test_case
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ '{test_case['text']}' ({test_case['source_script']} -> {test_case['target_script']}): '{data['transliterated_text']}'")
                success_count += 1
            else:
                print(f"✗ Status: {response.status_code}")
                print(f"  Response: {response.text}")
        except Exception as e:
            print(f"✗ Error: {e}")
    
    return success_count == len(test_cases)


def test_error_handling():
    """Test error handling for invalid inputs."""
    print("\n=== Testing Error Handling ===")
    
    # Test unsupported language
    try:
        response = requests.post(
            f"{BASE_URL}/api/translate",
            json={"text": "Hello", "source_lang": "xx", "target_lang": "hi"}
        )
        
        if response.status_code == 400:
            print(f"✓ Unsupported language correctly rejected (400)")
        else:
            print(f"✗ Expected 400, got {response.status_code}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test empty text
    try:
        response = requests.post(
            f"{BASE_URL}/api/detect-language",
            json={"text": ""}
        )
        
        if response.status_code == 422:  # Validation error
            print(f"✓ Empty text correctly rejected (422)")
        else:
            print(f"✗ Expected 422, got {response.status_code}")
    except Exception as e:
        print(f"✗ Error: {e}")


def main():
    """Run all endpoint tests."""
    print("=" * 60)
    print("Language Processing API Endpoint Tests")
    print("=" * 60)
    print("\nMake sure the server is running on http://localhost:8000")
    
    try:
        # Check if server is running
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("\n✗ Server is not responding. Please start the server first.")
            sys.exit(1)
        
        print("✓ Server is running")
        
        # Run tests
        results = []
        results.append(("Supported Languages", test_supported_languages()))
        results.append(("Language Detection", test_language_detection()))
        results.append(("Translation", test_translation()))
        results.append(("Romanization", test_romanization()))
        results.append(("Transliteration", test_transliteration()))
        test_error_handling()
        
        # Summary
        print("\n" + "=" * 60)
        print("Test Summary")
        print("=" * 60)
        
        for test_name, passed in results:
            status = "✓ PASSED" if passed else "✗ FAILED"
            print(f"{status}: {test_name}")
        
        all_passed = all(result[1] for result in results)
        
        if all_passed:
            print("\n✓ All tests passed!")
            sys.exit(0)
        else:
            print("\n✗ Some tests failed")
            sys.exit(1)
        
    except requests.exceptions.ConnectionError:
        print("\n✗ Cannot connect to server. Please start the server first:")
        print("  python -m uvicorn app.main:app --reload")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
