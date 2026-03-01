#!/usr/bin/env python3
"""
Test script for BharatSahayak API endpoints.
This script validates that all API endpoints are properly configured and responding.
"""

import json
import sys
import time
from typing import Dict, Optional
import requests


class APITester:
    def __init__(self, api_endpoint: str, jwt_token: Optional[str] = None):
        """Initialize API tester with endpoint and optional JWT token."""
        self.api_endpoint = api_endpoint.rstrip('/')
        self.jwt_token = jwt_token
        self.results = []
    
    def _make_request(self, method: str, path: str, data: Optional[Dict] = None, 
                     auth_required: bool = False) -> Dict:
        """Make HTTP request to API endpoint."""
        url = f"{self.api_endpoint}{path}"
        headers = {"Content-Type": "application/json"}
        
        if auth_required and self.jwt_token:
            headers["Authorization"] = f"Bearer {self.jwt_token}"
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=10)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=10)
            elif method == "PUT":
                response = requests.put(url, headers=headers, json=data, timeout=10)
            else:
                return {"error": f"Unsupported method: {method}"}
            
            return {
                "status_code": response.status_code,
                "response": response.json() if response.content else {},
                "headers": dict(response.headers)
            }
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
    
    def test_endpoint(self, name: str, method: str, path: str, 
                     data: Optional[Dict] = None, auth_required: bool = False,
                     expected_status: int = 200):
        """Test a single endpoint and record results."""
        print(f"\nTesting: {name}")
        print(f"  {method} {path}")
        
        result = self._make_request(method, path, data, auth_required)
        
        if "error" in result:
            print(f"  ❌ Error: {result['error']}")
            self.results.append({
                "name": name,
                "method": method,
                "path": path,
                "success": False,
                "error": result["error"]
            })
            return False
        
        status_code = result["status_code"]
        success = status_code == expected_status
        
        if success:
            print(f"  ✅ Success: {status_code}")
        else:
            print(f"  ❌ Failed: Expected {expected_status}, got {status_code}")
            print(f"     Response: {json.dumps(result['response'], indent=2)}")
        
        self.results.append({
            "name": name,
            "method": method,
            "path": path,
            "success": success,
            "status_code": status_code,
            "response": result["response"]
        })
        
        return success
    
    def test_cors(self):
        """Test CORS configuration."""
        print("\nTesting: CORS Configuration")
        url = f"{self.api_endpoint}/schemes"
        
        try:
            response = requests.options(url, headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            }, timeout=10)
            
            cors_headers = {
                "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
                "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
                "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers")
            }
            
            if cors_headers["Access-Control-Allow-Origin"]:
                print(f"  ✅ CORS enabled")
                print(f"     Origin: {cors_headers['Access-Control-Allow-Origin']}")
                print(f"     Methods: {cors_headers['Access-Control-Allow-Methods']}")
                return True
            else:
                print(f"  ❌ CORS not properly configured")
                return False
        except Exception as e:
            print(f"  ❌ Error testing CORS: {e}")
            return False
    
    def test_rate_limiting(self):
        """Test rate limiting by making rapid requests."""
        print("\nTesting: Rate Limiting")
        print("  Making 60 rapid requests to test throttling...")
        
        throttled = False
        for i in range(60):
            result = self._make_request("GET", "/schemes")
            if result.get("status_code") == 429:
                throttled = True
                print(f"  ✅ Rate limiting working (throttled at request {i+1})")
                break
        
        if not throttled:
            print(f"  ⚠️  Rate limiting not triggered (may need higher request volume)")
        
        return True
    
    def run_all_tests(self):
        """Run all API endpoint tests."""
        print("=" * 60)
        print("BharatSahayak API Endpoint Tests")
        print("=" * 60)
        print(f"API Endpoint: {self.api_endpoint}")
        print(f"JWT Token: {'Provided' if self.jwt_token else 'Not provided'}")
        
        # Test public endpoints
        self.test_endpoint(
            "Search Schemes",
            "GET",
            "/schemes?category=agriculture",
            expected_status=200
        )
        
        self.test_endpoint(
            "Get Scheme Details (Invalid ID)",
            "GET",
            "/schemes/invalid-id",
            expected_status=404
        )
        
        # Test authentication endpoints
        test_phone = f"+91{int(time.time()) % 10000000000}"
        self.test_endpoint(
            "Register User",
            "POST",
            "/auth/register",
            data={
                "phone_number": test_phone,
                "language": "hi"
            },
            expected_status=200
        )
        
        # Test authenticated endpoints (will fail without valid token)
        if self.jwt_token:
            self.test_endpoint(
                "Get User Profile",
                "GET",
                "/user/profile",
                auth_required=True,
                expected_status=200
            )
            
            self.test_endpoint(
                "Update User Profile",
                "PUT",
                "/user/profile",
                data={
                    "age": 30,
                    "occupation": "farmer",
                    "location": {
                        "state": "Maharashtra",
                        "district": "Pune",
                        "pincode": "411001"
                    }
                },
                auth_required=True,
                expected_status=200
            )
            
            self.test_endpoint(
                "Check Eligibility",
                "POST",
                "/schemes/check-eligibility",
                data={
                    "scheme_id": "test-scheme-id",
                    "user_profile": {
                        "phone_number": test_phone,
                        "language": "hi",
                        "age": 30,
                        "occupation": "farmer"
                    }
                },
                auth_required=True,
                expected_status=200
            )
            
            self.test_endpoint(
                "Get Eligible Schemes",
                "POST",
                "/schemes/eligible",
                data={
                    "user_profile": {
                        "phone_number": test_phone,
                        "language": "hi",
                        "age": 30,
                        "occupation": "farmer",
                        "location": {
                            "state": "Maharashtra",
                            "district": "Pune"
                        }
                    }
                },
                auth_required=True,
                expected_status=200
            )
        else:
            print("\n⚠️  Skipping authenticated endpoint tests (no JWT token provided)")
        
        # Test CORS
        self.test_cors()
        
        # Test rate limiting (optional, can be slow)
        # self.test_rate_limiting()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test results summary."""
        print("\n" + "=" * 60)
        print("Test Summary")
        print("=" * 60)
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r["success"])
        failed = total - passed
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed} ✅")
        print(f"Failed: {failed} ❌")
        
        if failed > 0:
            print("\nFailed Tests:")
            for result in self.results:
                if not result["success"]:
                    print(f"  - {result['name']}: {result.get('error', f'Status {result.get('status_code')}')}")
        
        print("=" * 60)
        
        return failed == 0


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python test_api_endpoints.py <API_ENDPOINT> [JWT_TOKEN]")
        print("\nExample:")
        print("  python test_api_endpoints.py https://abc123.execute-api.us-east-1.amazonaws.com/dev")
        print("  python test_api_endpoints.py https://abc123.execute-api.us-east-1.amazonaws.com/dev eyJhbGc...")
        sys.exit(1)
    
    api_endpoint = sys.argv[1]
    jwt_token = sys.argv[2] if len(sys.argv) > 2 else None
    
    tester = APITester(api_endpoint, jwt_token)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
