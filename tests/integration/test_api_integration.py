"""
Integration tests for BharatSahayak API endpoints.

These tests validate the complete request/response flow for all API endpoints,
including authentication, authorization, error handling, and status codes.

Prerequisites:
- API must be deployed to AWS
- Set environment variable API_ENDPOINT to the deployed API URL
- Set environment variable JWT_TOKEN for authenticated endpoint tests (optional)

Usage:
    export API_ENDPOINT=https://your-api.execute-api.region.amazonaws.com/dev
    export JWT_TOKEN=your_jwt_token  # Optional, for authenticated tests
    pytest tests/integration/test_api_integration.py -v
"""

import os
import time
import pytest
import requests
from typing import Dict, Optional


# Configuration
API_ENDPOINT = os.environ.get("API_ENDPOINT", "").rstrip("/")
JWT_TOKEN = os.environ.get("JWT_TOKEN")

# Skip all tests if API_ENDPOINT is not set
pytestmark = pytest.mark.skipif(
    not API_ENDPOINT,
    reason="API_ENDPOINT environment variable not set"
)


class TestPublicEndpoints:
    """Test public endpoints that don't require authentication."""
    
    def test_search_schemes_success(self):
        """Test scheme search with valid parameters."""
        response = requests.get(
            f"{API_ENDPOINT}/schemes",
            params={"category": "agriculture"},
            timeout=10
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "schemes" in data or isinstance(data, list)
    
    def test_search_schemes_no_params(self):
        """Test scheme search without parameters returns all schemes."""
        response = requests.get(
            f"{API_ENDPOINT}/schemes",
            timeout=10
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "schemes" in data or isinstance(data, list)
    
    def test_search_schemes_invalid_category(self):
        """Test scheme search with invalid category."""
        response = requests.get(
            f"{API_ENDPOINT}/schemes",
            params={"category": "invalid_category_xyz"},
            timeout=10
        )
        
        # Should return 200 with empty results, not an error
        assert response.status_code in [200, 404]
    
    def test_get_scheme_details_invalid_id(self):
        """Test getting scheme details with invalid ID."""
        response = requests.get(
            f"{API_ENDPOINT}/schemes/invalid-scheme-id-12345",
            timeout=10
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "error" in data or "message" in data
    
    def test_cors_headers_present(self):
        """Test that CORS headers are properly configured."""
        response = requests.options(
            f"{API_ENDPOINT}/schemes",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            },
            timeout=10
        )
        
        # Check CORS headers
        assert "Access-Control-Allow-Origin" in response.headers
        assert "Access-Control-Allow-Methods" in response.headers
        assert "Access-Control-Allow-Headers" in response.headers


class TestAuthenticationEndpoints:
    """Test authentication and user registration endpoints."""
    
    def test_register_user_success(self):
        """Test user registration with valid phone number."""
        # Use timestamp to generate unique phone number
        test_phone = f"+91{int(time.time()) % 10000000000}"
        
        response = requests.post(
            f"{API_ENDPOINT}/auth/register",
            json={
                "phone_number": test_phone,
                "language": "hi"
            },
            timeout=10
        )
        
        assert response.status_code in [200, 201]
        data = response.json()
        # Should return some indication of success
        assert "user_id" in data or "message" in data or "session" in data
    
    def test_register_user_invalid_phone(self):
        """Test user registration with invalid phone number."""
        response = requests.post(
            f"{API_ENDPOINT}/auth/register",
            json={
                "phone_number": "invalid",
                "language": "hi"
            },
            timeout=10
        )
        
        assert response.status_code in [400, 422]
        data = response.json()
        assert "error" in data or "message" in data
    
    def test_register_user_missing_language(self):
        """Test user registration without required language field."""
        response = requests.post(
            f"{API_ENDPOINT}/auth/register",
            json={
                "phone_number": "+919876543210"
            },
            timeout=10
        )
        
        assert response.status_code in [400, 422]
        data = response.json()
        assert "error" in data or "message" in data
    
    def test_verify_otp_invalid(self):
        """Test OTP verification with invalid OTP."""
        response = requests.post(
            f"{API_ENDPOINT}/auth/verify",
            json={
                "phone_number": "+919876543210",
                "otp": "000000"
            },
            timeout=10
        )
        
        # Should return error for invalid OTP
        assert response.status_code in [400, 401, 403]
        data = response.json()
        assert "error" in data or "message" in data


@pytest.mark.skipif(not JWT_TOKEN, reason="JWT_TOKEN not provided")
class TestAuthenticatedEndpoints:
    """Test endpoints that require authentication."""
    
    @pytest.fixture
    def auth_headers(self):
        """Provide authentication headers for requests."""
        return {
            "Authorization": f"Bearer {JWT_TOKEN}",
            "Content-Type": "application/json"
        }
    
    def test_get_user_profile_success(self, auth_headers):
        """Test getting user profile with valid token."""
        response = requests.get(
            f"{API_ENDPOINT}/user/profile",
            headers=auth_headers,
            timeout=10
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data or "phone_number" in data
    
    def test_get_user_profile_no_auth(self):
        """Test getting user profile without authentication."""
        response = requests.get(
            f"{API_ENDPOINT}/user/profile",
            timeout=10
        )
        
        assert response.status_code in [401, 403]
        data = response.json()
        assert "error" in data or "message" in data
    
    def test_update_user_profile_success(self, auth_headers):
        """Test updating user profile with valid data."""
        response = requests.put(
            f"{API_ENDPOINT}/user/profile",
            headers=auth_headers,
            json={
                "age": 30,
                "occupation": "farmer",
                "location": {
                    "state": "Maharashtra",
                    "district": "Pune",
                    "pincode": "411001"
                }
            },
            timeout=10
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data or "message" in data
    
    def test_update_user_profile_invalid_age(self, auth_headers):
        """Test updating user profile with invalid age."""
        response = requests.put(
            f"{API_ENDPOINT}/user/profile",
            headers=auth_headers,
            json={
                "age": -5  # Invalid age
            },
            timeout=10
        )
        
        assert response.status_code in [400, 422]
        data = response.json()
        assert "error" in data or "message" in data
    
    def test_check_eligibility_success(self, auth_headers):
        """Test eligibility check with valid data."""
        response = requests.post(
            f"{API_ENDPOINT}/schemes/check-eligibility",
            headers=auth_headers,
            json={
                "scheme_id": "test-scheme-id",
                "user_profile": {
                    "phone_number": "+919876543210",
                    "language": "hi",
                    "age": 30,
                    "occupation": "farmer",
                    "location": {
                        "state": "Maharashtra",
                        "district": "Pune"
                    }
                }
            },
            timeout=10
        )
        
        # May return 200 with eligibility result or 404 if scheme not found
        assert response.status_code in [200, 404]
        data = response.json()
        if response.status_code == 200:
            assert "is_eligible" in data or "eligible" in data
    
    def test_check_eligibility_missing_profile(self, auth_headers):
        """Test eligibility check without user profile."""
        response = requests.post(
            f"{API_ENDPOINT}/schemes/check-eligibility",
            headers=auth_headers,
            json={
                "scheme_id": "test-scheme-id"
            },
            timeout=10
        )
        
        assert response.status_code in [400, 422]
        data = response.json()
        assert "error" in data or "message" in data
    
    def test_get_eligible_schemes_success(self, auth_headers):
        """Test getting all eligible schemes for user."""
        response = requests.post(
            f"{API_ENDPOINT}/schemes/eligible",
            headers=auth_headers,
            json={
                "user_profile": {
                    "phone_number": "+919876543210",
                    "language": "hi",
                    "age": 30,
                    "occupation": "farmer",
                    "location": {
                        "state": "Maharashtra",
                        "district": "Pune"
                    }
                }
            },
            timeout=10
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "schemes" in data or isinstance(data, list)
    
    def test_get_eligible_schemes_no_auth(self):
        """Test getting eligible schemes without authentication."""
        response = requests.post(
            f"{API_ENDPOINT}/schemes/eligible",
            json={
                "user_profile": {
                    "phone_number": "+919876543210",
                    "language": "hi",
                    "age": 30
                }
            },
            timeout=10
        )
        
        assert response.status_code in [401, 403]


class TestErrorHandling:
    """Test error handling and status codes."""
    
    def test_invalid_endpoint_404(self):
        """Test that invalid endpoints return 404."""
        response = requests.get(
            f"{API_ENDPOINT}/invalid/endpoint/path",
            timeout=10
        )
        
        assert response.status_code == 404
    
    def test_invalid_method_405(self):
        """Test that invalid HTTP methods return 405."""
        response = requests.delete(
            f"{API_ENDPOINT}/schemes",
            timeout=10
        )
        
        # Should return 405 Method Not Allowed or 403 Forbidden
        assert response.status_code in [403, 405]
    
    def test_malformed_json_400(self):
        """Test that malformed JSON returns 400."""
        response = requests.post(
            f"{API_ENDPOINT}/auth/register",
            data="invalid json {{{",
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        assert response.status_code in [400, 422]
    
    def test_rate_limiting_headers(self):
        """Test that rate limiting is configured (check for throttle response)."""
        # Make multiple rapid requests
        responses = []
        for _ in range(60):
            response = requests.get(
                f"{API_ENDPOINT}/schemes",
                timeout=10
            )
            responses.append(response)
            
            # If we get throttled, verify the response
            if response.status_code == 429:
                data = response.json()
                assert "error" in data or "message" in data
                assert "Retry-After" in response.headers or "retry_after" in data
                break
        
        # Note: May not trigger throttling in test environment
        # This is informational rather than a hard requirement


class TestResponseFormat:
    """Test response format and structure."""
    
    def test_error_response_format(self):
        """Test that error responses follow consistent format."""
        response = requests.get(
            f"{API_ENDPOINT}/schemes/invalid-id-12345",
            timeout=10
        )
        
        assert response.status_code == 404
        data = response.json()
        
        # Error responses should have error and/or message fields
        assert "error" in data or "message" in data
        
        # Should be valid JSON
        assert isinstance(data, dict)
    
    def test_success_response_format(self):
        """Test that success responses are valid JSON."""
        response = requests.get(
            f"{API_ENDPOINT}/schemes",
            timeout=10
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should be valid JSON (dict or list)
        assert isinstance(data, (dict, list))
    
    def test_content_type_header(self):
        """Test that responses have correct Content-Type header."""
        response = requests.get(
            f"{API_ENDPOINT}/schemes",
            timeout=10
        )
        
        assert "application/json" in response.headers.get("Content-Type", "")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
