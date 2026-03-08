#!/usr/bin/env python3
"""
Backend Endpoint Testing Script for BharatSahayak
Tests all backend endpoints to verify they're working correctly
"""

import requests
import json
import sys
from typing import Dict, Any, Tuple
from colorama import init, Fore, Style

# Initialize colorama for Windows support
init(autoreset=True)

# Configuration
API_BASE_URL = "https://dvt82zj0c4.execute-api.ap-south-1.amazonaws.com/dev"
TEST_PHONE = "+919876543210"

# Test counters
total_tests = 0
passed_tests = 0
failed_tests = 0


def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{Fore.BLUE}{'=' * 60}")
    print(f"{Fore.BLUE}{text}")
    print(f"{Fore.BLUE}{'=' * 60}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{Fore.GREEN}✅ {text}")


def print_error(text: str):
    """Print error message"""
    print(f"{Fore.RED}❌ {text}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{Fore.YELLOW}⚠️  {text}")


def print_info(text: str):
    """Print info message"""
    print(f"{Fore.CYAN}ℹ️  {text}")


def test_endpoint(
    name: str,
    method: str,
    endpoint: str,
    data: Dict[str, Any] = None,
    expected_status: int = 200,
    headers: Dict[str, str] = None
) -> Tuple[bool, Any]:
    """Test an API endpoint"""
    global total_tests, passed_tests, failed_tests
    
    total_tests += 1
    print_info(f"Testing: {name}")
    
    url = f"{API_BASE_URL}{endpoint}"
    default_headers = {"Content-Type": "application/json"}
    if headers:
        default_headers.update(headers)
    
    try:
        if method == "GET":
            response = requests.get(url, headers=default_headers, timeout=30)
        elif method == "POST":
            response = requests.post(url, json=data, headers=default_headers, timeout=30)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=default_headers, timeout=30)
        elif method == "DELETE":
            response = requests.delete(url, headers=default_headers, timeout=30)
        elif method == "OPTIONS":
            response = requests.options(url, headers=default_headers, timeout=30)
        else:
            print_error(f"Unsupported method: {method}")
            failed_tests += 1
            return False, None
        
        # Check status code
        if response.status_code == expected_status:
            print_success(f"{name} - Status: {response.status_code}")
            passed_tests += 1
            
            # Try to parse JSON response
            try:
                response_data = response.json()
                print(f"Response: {json.dumps(response_data, indent=2)}")
                return True, response_data
            except json.JSONDecodeError:
                print(f"Response: {response.text}")
                return True, response.text
        else:
            print_error(f"{name} - Expected: {expected_status}, Got: {response.status_code}")
            failed_tests += 1
            print(f"Response: {response.text}")
            return False, None
            
    except requests.exceptions.RequestException as e:
        print_error(f"{name} - Request failed: {str(e)}")
        failed_tests += 1
        return False, None
    
    finally:
        print()


def test_cors(endpoint: str) -> bool:
    """Test CORS headers"""
    global total_tests, passed_tests, failed_tests
    
    total_tests += 1
    print_info("Testing CORS headers...")
    
    url = f"{API_BASE_URL}{endpoint}"
    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "GET"
    }
    
    try:
        response = requests.options(url, headers=headers, timeout=30)
        
        # Check for CORS headers
        cors_headers = [
            "Access-Control-Allow-Origin",
            "Access-Control-Allow-Methods",
            "Access-Control-Allow-Headers"
        ]
        
        has_cors = all(header in response.headers for header in cors_headers)
        
        if has_cors:
            print_success("CORS headers present")
            for header in cors_headers:
                print(f"  {header}: {response.headers.get(header)}")
            passed_tests += 1
            return True
        else:
            print_error("CORS headers missing")
            print(f"Response headers: {dict(response.headers)}")
            failed_tests += 1
            return False
            
    except requests.exceptions.RequestException as e:
        print_error(f"CORS test failed: {str(e)}")
        failed_tests += 1
        return False
    
    finally:
        print()


def main():
    """Run all tests"""
    print_header("BharatSahayak Backend Endpoint Tests")
    print_info(f"API Base URL: {API_BASE_URL}")
    print_info(f"Test Phone: {TEST_PHONE}")
    
    # Test 1: Health Check
    print_header("Test 1: Health Check")
    test_endpoint("Health Check", "GET", "/health-check")
    
    # Test 2: Register New User
    print_header("Test 2: User Registration")
    register_data = {
        "phone_number": TEST_PHONE,
        "language": "hi",
        "location": {
            "state": "Maharashtra",
            "district": "Pune",
            "pincode": "411014"
        }
    }
    success, response = test_endpoint("Register User", "POST", "/auth/register", register_data)
    
    # Store session for later use
    session = None
    if success and response:
        session = response.get("session")
    
    # Test 3: Login Existing User
    print_header("Test 3: User Login")
    login_data = {"phone_number": TEST_PHONE}
    test_endpoint("Login User", "POST", "/auth/login", login_data)
    
    # Test 4: Get All Schemes
    print_header("Test 4: Get Schemes")
    test_endpoint("Get All Schemes", "GET", "/schemes?limit=5")
    
    # Test 5: Search Schemes
    print_header("Test 5: Search Schemes")
    test_endpoint("Search Schemes", "GET", "/schemes/search?q=agriculture&limit=5")
    
    # Test 6: Get Scheme Details
    print_header("Test 6: Get Scheme Details")
    test_endpoint("Get Scheme Details", "GET", "/schemes/PM-KISAN")
    
    # Test 7: Voice to Text
    print_header("Test 7: Voice to Text API")
    print_warning("Skipping Voice to Text test (requires actual audio data)")
    
    # Test 8: Conversational Query
    print_header("Test 8: Conversational Query")
    query_data = {
        "query": "What schemes are available for farmers?",
        "language": "en"
    }
    test_endpoint("Conversational Query", "POST", "/conversational-query", query_data)
    
    # Test 9: CORS Preflight
    print_header("Test 9: CORS Preflight")
    test_cors("/health-check")
    
    # Test 10: Invalid Endpoint
    print_header("Test 10: Invalid Endpoint (404)")
    test_endpoint("Invalid Endpoint", "GET", "/invalid-endpoint", expected_status=404)
    
    # Summary
    print_header("Test Summary")
    print(f"Total Tests: {Fore.CYAN}{total_tests}")
    print(f"Passed: {Fore.GREEN}{passed_tests}")
    print(f"Failed: {Fore.RED}{failed_tests}")
    
    if failed_tests == 0:
        print_success("All tests passed! 🎉")
        return 0
    else:
        print_error("Some tests failed. Please check the output above.")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        sys.exit(1)
