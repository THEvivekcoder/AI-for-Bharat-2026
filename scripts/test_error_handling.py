#!/usr/bin/env python3
"""Test error handling and rate limiting"""
import requests
import time
import json
from typing import Dict, Any


BASE_URL = "http://localhost:8000"


def test_error_translations():
    """Test multilingual error messages"""
    print("\n=== Testing Error Translations ===")
    
    # Test with different Accept-Language headers
    languages = ["en", "hi", "bn", "te", "mr"]
    
    for lang in languages:
        print(f"\nTesting language: {lang}")
        
        # Make request to non-existent scheme
        response = requests.get(
            f"{BASE_URL}/api/schemes/00000000-0000-0000-0000-000000000000",
            headers={"Accept-Language": lang}
        )
        
        if response.status_code == 404 or response.status_code == 400:
            error_data = response.json()
            print(f"  Error code: {error_data.get('error')}")
            print(f"  Message: {error_data.get('message')}")
            print(f"  Has translations: {'message_translations' in error_data}")
            print(f"  Retry allowed: {error_data.get('retry_allowed')}")
        else:
            print(f"  Unexpected status: {response.status_code}")


def test_rate_limiting():
    """Test rate limiting functionality"""
    print("\n=== Testing Rate Limiting ===")
    
    # Make rapid requests to trigger rate limit
    endpoint = f"{BASE_URL}/api/schemes"
    success_count = 0
    rate_limited = False
    
    print("\nMaking rapid requests...")
    for i in range(70):  # Exceed the limit of 60 per minute
        response = requests.get(endpoint)
        
        if response.status_code == 200:
            success_count += 1
        elif response.status_code == 429:
            rate_limited = True
            error_data = response.json()
            print(f"\n✓ Rate limit triggered after {success_count} requests")
            print(f"  Error code: {error_data.get('error')}")
            print(f"  Message: {error_data.get('message')}")
            print(f"  Retry after: {error_data.get('retry_after_seconds')}s")
            print(f"  Quota limit: {error_data.get('quota_limit')}")
            print(f"  Reset time: {error_data.get('quota_reset_time')}")
            
            # Check rate limit headers
            print(f"\nRate limit headers:")
            print(f"  X-RateLimit-Limit: {response.headers.get('X-RateLimit-Limit')}")
            print(f"  Retry-After: {response.headers.get('Retry-After')}")
            break
        
        time.sleep(0.1)  # Small delay between requests
    
    if not rate_limited:
        print(f"\n✗ Rate limit not triggered after {success_count} requests")
    
    return rate_limited


def test_validation_errors():
    """Test validation error handling"""
    print("\n=== Testing Validation Errors ===")
    
    # Send invalid data to auth endpoint
    response = requests.post(
        f"{BASE_URL}/api/auth/register",
        json={"invalid_field": "test"}  # Missing required fields
    )
    
    if response.status_code == 422:
        error_data = response.json()
        print("✓ Validation error caught")
        print(f"  Error code: {error_data.get('error')}")
        print(f"  Message: {error_data.get('message')}")
        print(f"  Has details: {'details' in error_data}")
        print(f"  Retry allowed: {error_data.get('retry_allowed')}")
    else:
        print(f"✗ Unexpected status: {response.status_code}")


def test_error_response_structure():
    """Test error response structure"""
    print("\n=== Testing Error Response Structure ===")
    
    # Trigger an error
    response = requests.get(
        f"{BASE_URL}/api/schemes/invalid-uuid"
    )
    
    if response.status_code >= 400:
        error_data = response.json()
        
        # Check required fields
        required_fields = ["error", "message", "retry_allowed", "timestamp"]
        missing_fields = [f for f in required_fields if f not in error_data]
        
        if not missing_fields:
            print("✓ All required error fields present")
            print(f"  Error structure: {json.dumps(error_data, indent=2)}")
        else:
            print(f"✗ Missing fields: {missing_fields}")
    else:
        print(f"✗ No error triggered: {response.status_code}")


def test_graceful_degradation():
    """Test graceful degradation with health endpoint"""
    print("\n=== Testing Graceful Degradation ===")
    
    # Health endpoint should always work
    response = requests.get(f"{BASE_URL}/health")
    
    if response.status_code == 200:
        print("✓ Health endpoint accessible")
        print(f"  Response: {response.json()}")
    else:
        print(f"✗ Health endpoint failed: {response.status_code}")


def main():
    """Run all error handling tests"""
    print("=" * 60)
    print("Error Handling and Rate Limiting Tests")
    print("=" * 60)
    
    try:
        # Test error translations
        test_error_translations()
        
        # Test validation errors
        test_validation_errors()
        
        # Test error response structure
        test_error_response_structure()
        
        # Test graceful degradation
        test_graceful_degradation()
        
        # Test rate limiting (do this last as it may block requests)
        test_rate_limiting()
        
        print("\n" + "=" * 60)
        print("Tests completed!")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Could not connect to server")
        print("  Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"\n✗ Unexpected error: {str(e)}")


if __name__ == "__main__":
    main()
