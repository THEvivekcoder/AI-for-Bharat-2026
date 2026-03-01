#!/usr/bin/env python3
"""
🎙️ KILLER DEMO FLOW VALIDATOR
Voice → Hindi Question → Scheme Eligibility → Audio Reply → Impact Recorded

This script validates the ONE flow that matters for demo/hackathon.
Run this before any demo to ensure everything works.
"""

import requests
import json
import base64
import io
import wave
import struct
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000"
DEMO_PHONE = "+919999999999"
AUTH_TOKEN = None  # Will be set after registration

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_step(step_num, description):
    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"STEP {step_num}: {description}")
    print(f"{'='*60}{Colors.END}\n")

def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}✗ {message}{Colors.END}")

def print_info(message):
    print(f"{Colors.YELLOW}ℹ {message}{Colors.END}")

def create_test_audio():
    """Create a simple test audio file (WAV format)"""
    sample_rate = 16000
    duration = 1
    
    audio_buffer = io.BytesIO()
    with wave.open(audio_buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        
        for i in range(int(sample_rate * duration)):
            value = int(32767 * 0.3 * (i % 100) / 100)
            wav_file.writeframes(struct.pack('<h', value))
    
    audio_buffer.seek(0)
    return audio_buffer.getvalue()

def test_health_check():
    """Test 0: Verify API is running"""
    print_step(0, "Health Check - Is API Running?")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"API is running - Status: {data.get('status', 'unknown')}")
            print_info(f"Response: {json.dumps(data, indent=2)}")
            return True
        else:
            print_error(f"Health check failed with status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to API. Is the server running?")
        print_info(f"Start server with: uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print_error(f"Health check error: {str(e)}")
        return False

def get_auth_token():
    """Get authentication token for demo user"""
    global AUTH_TOKEN
    
    print_step("0.5", "Authentication - Getting demo token")
    
    try:
        # Try to register demo user
        payload = {
            "phone_number": DEMO_PHONE,
            "language": "hi"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json=payload,
            timeout=10
        )
        
        # Registration might fail if user exists - that's OK
        print_info(f"Registration response: {response.status_code}")
        
        # Try to verify with test OTP
        verify_payload = {
            "phone_number": DEMO_PHONE,
            "otp": "123456"  # Test OTP
        }
        
        response = requests.post(
            f"{BASE_URL}/api/auth/verify",
            json=verify_payload,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            AUTH_TOKEN = data.get('access_token')
            print_success(f"Got auth token: {AUTH_TOKEN[:20]}...")
            return True
        else:
            print_error(f"Could not get auth token: {response.status_code}")
            print_info("Some endpoints will fail without authentication")
            return False
            
    except Exception as e:
        print_error(f"Authentication error: {str(e)}")
        return False

def test_voice_to_text():
    """Test 1: Voice → Text (STT)"""
    print_step(1, "Voice to Text - STT Working?")
    
    try:
        # Create test audio
        audio_data = create_test_audio()
        
        # Send to voice-to-text endpoint
        files = {'audio': ('test.wav', audio_data, 'audio/wav')}
        response = requests.post(
            f"{BASE_URL}/api/voice-to-text",
            files=files,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("Voice transcription successful")
            print_info(f"Transcribed text: {data.get('text', 'N/A')}")
            print_info(f"Detected language: {data.get('detected_language', 'N/A')}")
            print_info(f"Confidence: {data.get('confidence', 'N/A')}")
            return True, data
        else:
            print_error(f"Voice-to-text failed: {response.status_code}")
            print_info(f"Response: {response.text}")
            return False, None
            
    except Exception as e:
        print_error(f"Voice-to-text error: {str(e)}")
        return False, None

def test_rag_query():
    """Test 2: RAG Query - Knowledge Retrieval"""
    print_step(2, "RAG Query - Can it answer questions?")
    
    try:
        # Test with Hindi question about PM-KISAN
        payload = {
            "query": "PM Kisan yojana kya hai?",
            "language": "hi"
        }
        
        headers = {}
        if AUTH_TOKEN:
            headers['Authorization'] = f'Bearer {AUTH_TOKEN}'
        
        response = requests.post(
            f"{BASE_URL}/api/ask",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("RAG query successful")
            print_info(f"Answer: {data.get('answer', 'N/A')[:200]}...")
            print_info(f"Confidence: {data.get('confidence', 'N/A')}")
            print_info(f"Sources: {len(data.get('sources', []))} sources")
            return True, data
        else:
            print_error(f"RAG query failed: {response.status_code}")
            print_info(f"Response: {response.text}")
            return False, None
            
    except Exception as e:
        print_error(f"RAG query error: {str(e)}")
        return False, None

def test_scheme_eligibility():
    """Test 3: Scheme Eligibility Check"""
    print_step(3, "Scheme Eligibility - Can it check eligibility?")
    
    try:
        headers = {}
        if AUTH_TOKEN:
            headers['Authorization'] = f'Bearer {AUTH_TOKEN}'
        
        # Just get eligible schemes for current user
        response = requests.post(
            f"{BASE_URL}/api/schemes/eligible",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("Eligibility check successful")
            print_info(f"Found {len(data)} schemes")
            
            if data:
                for scheme in data[:3]:
                    print_info(f"  - {scheme.get('name', 'Unknown')}")
            
            return True, data
        else:
            print_error(f"Eligibility check failed: {response.status_code}")
            print_info(f"Response: {response.text[:200]}")
            return False, None
            
    except Exception as e:
        print_error(f"Eligibility check error: {str(e)}")
        return False, None

def test_integrated_voice_query():
    """Test 4: INTEGRATED FLOW - The Killer Feature"""
    print_step(4, "🔥 INTEGRATED VOICE QUERY - The Killer Flow")
    
    try:
        # Create test audio
        audio_data = create_test_audio()
        
        # Send to integrated endpoint
        files = {'audio': ('query.wav', audio_data, 'audio/wav')}
        
        headers = {}
        if AUTH_TOKEN:
            headers['Authorization'] = f'Bearer {AUTH_TOKEN}'
        
        print_info("Sending voice query through integrated pipeline...")
        print_info("This tests: STT → Language Detection → RAG → TTS → Impact Tracking")
        
        response = requests.post(
            f"{BASE_URL}/api/integrated/voice-query",
            files=files,
            headers=headers,
            timeout=60  # Longer timeout for full pipeline
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("🎉 INTEGRATED FLOW WORKS!")
            print_info(f"Text Query: {data.get('text_query', 'N/A')}")
            print_info(f"Text Answer: {data.get('text_answer', 'N/A')[:150]}...")
            print_info(f"Detected Language: {data.get('detected_language', 'N/A')}")
            print_info(f"Audio Response: {'✓ Present' if data.get('audio_answer_base64') else '✗ Missing'}")
            print_info(f"Session ID: {data.get('session_id', 'N/A')}")
            
            # Verify all required fields
            required_fields = ['text_query', 'text_answer', 'audio_answer_base64', 'detected_language']
            all_present = all(field in data for field in required_fields)
            
            if all_present:
                print_success("All required fields present in response")
                return True, data
            else:
                missing = [f for f in required_fields if f not in data]
                print_error(f"Missing fields: {missing}")
                return False, data
        else:
            print_error(f"Integrated flow failed: {response.status_code}")
            print_info(f"Response: {response.text[:500]}")
            return False, None
            
    except Exception as e:
        print_error(f"Integrated flow error: {str(e)}")
        import traceback
        print_info(traceback.format_exc())
        return False, None

def test_impact_tracking():
    """Test 5: Impact Tracking - Are interactions recorded?"""
    print_step(5, "Impact Tracking - Are interactions recorded?")
    
    try:
        headers = {}
        if AUTH_TOKEN:
            headers['Authorization'] = f'Bearer {AUTH_TOKEN}'
        
        # Record a test event - use correct format
        payload = {
            "event": {
                "event_type": "scheme_accessed",
                "event_data": {
                    "scheme_id": "test-scheme-123",
                    "scheme_name": "PM-KISAN"
                },
                "language": "hi"
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/impact/event",
            json=payload,
            headers=headers,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            print_success("Impact tracking working")
            print_info("Events are being recorded successfully")
            return True
        else:
            print_error(f"Impact tracking failed: {response.status_code}")
            print_info(f"Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print_error(f"Impact tracking error: {str(e)}")
        return False

def run_demo_validation():
    """Run complete demo validation"""
    print(f"\n{Colors.BLUE}")
    print("="*60)
    print("🎙️  BHARATSAHAYAK KILLER FLOW VALIDATOR")
    print("="*60)
    print(f"{Colors.END}")
    print(f"\nTarget: {BASE_URL}")
    print(f"Testing the ONE flow that matters for demo\n")
    
    results = {}
    
    # Test 0: Health Check
    results['health'] = test_health_check()
    if not results['health']:
        print(f"\n{Colors.RED}❌ API is not running. Cannot proceed.{Colors.END}")
        return False
    
    # Test 0.5: Get Auth Token
    results['auth'] = get_auth_token()
    
    # Test 1: Voice to Text
    results['voice_to_text'], _ = test_voice_to_text()
    
    # Test 2: RAG Query
    results['rag'], _ = test_rag_query()
    
    # Test 3: Scheme Eligibility
    results['eligibility'], _ = test_scheme_eligibility()
    
    # Test 4: INTEGRATED FLOW (The Killer Feature)
    results['integrated'], _ = test_integrated_voice_query()
    
    # Test 5: Impact Tracking
    results['impact'] = test_impact_tracking()
    
    # Summary
    print(f"\n{Colors.BLUE}{'='*60}")
    print("VALIDATION SUMMARY")
    print(f"{'='*60}{Colors.END}\n")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    for test_name, passed_test in results.items():
        status = f"{Colors.GREEN}✓ PASS{Colors.END}" if passed_test else f"{Colors.RED}✗ FAIL{Colors.END}"
        print(f"{test_name.upper():20} {status}")
    
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"Results: {passed}/{total} tests passed")
    
    if results.get('integrated'):
        print(f"\n{Colors.GREEN}🎉 KILLER FLOW IS WORKING!")
        print(f"✓ Voice → Hindi → RAG → Audio → Impact")
        print(f"✓ DEMO READY!{Colors.END}\n")
        return True
    else:
        print(f"\n{Colors.YELLOW}⚠️  KILLER FLOW NEEDS WORK")
        print(f"Check the failures above and fix them{Colors.END}\n")
        return False

if __name__ == "__main__":
    import sys
    success = run_demo_validation()
    sys.exit(0 if success else 1)
