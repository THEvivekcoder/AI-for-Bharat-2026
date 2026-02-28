"""Test authentication endpoints"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine
from app.models.user import User, UserProfile
from app.models.location import Location

# Create test client
client = TestClient(app)


def test_register_endpoint():
    """Test user registration endpoint"""
    print("\n=== Testing POST /api/auth/register ===")
    
    response = client.post(
        "/api/auth/register",
        json={
            "phone_number": "+919876543210",
            "language": "hi"
        }
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 201
    data = response.json()
    assert "user_id" in data
    assert data["phone_number"] == "+919876543210"
    assert data["otp_sent"] is True
    
    print("✓ Registration endpoint works!")
    return data["user_id"]


def test_verify_endpoint():
    """Test OTP verification endpoint"""
    print("\n=== Testing POST /api/auth/verify ===")
    
    # First register to get OTP
    register_response = client.post(
        "/api/auth/register",
        json={
            "phone_number": "+919876543211",
            "language": "hi"
        }
    )
    
    # For testing, we need to get the OTP from logs or Redis
    # In a real test, you'd mock the OTP or retrieve it from Redis
    # For now, let's test with an invalid OTP to verify error handling
    
    response = client.post(
        "/api/auth/verify",
        json={
            "phone_number": "+919876543211",
            "otp": "123456"
        }
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Should fail with invalid OTP
    assert response.status_code == 401
    print("✓ Verify endpoint works (correctly rejects invalid OTP)!")


def test_profile_endpoints_without_auth():
    """Test profile endpoints without authentication"""
    print("\n=== Testing GET /api/user/profile (without auth) ===")
    
    response = client.get("/api/user/profile")
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Should fail without authentication
    assert response.status_code == 403
    print("✓ Profile endpoint correctly requires authentication!")


def test_update_profile_without_auth():
    """Test update profile endpoint without authentication"""
    print("\n=== Testing PUT /api/user/profile (without auth) ===")
    
    response = client.put(
        "/api/user/profile",
        json={
            "age": 30,
            "gender": "male"
        }
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Should fail without authentication
    assert response.status_code == 403
    print("✓ Update profile endpoint correctly requires authentication!")


def test_delete_user_without_auth():
    """Test delete user endpoint without authentication"""
    print("\n=== Testing DELETE /api/user/data (without auth) ===")
    
    response = client.delete("/api/user/data")
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Should fail without authentication
    assert response.status_code == 403
    print("✓ Delete user endpoint correctly requires authentication!")


def test_health_check():
    """Test health check endpoint"""
    print("\n=== Testing GET /health ===")
    
    response = client.get("/health")
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 200
    print("✓ Health check works!")


if __name__ == "__main__":
    print("Starting authentication endpoint tests...")
    
    try:
        # Test health check first
        test_health_check()
        
        # Test registration
        test_register_endpoint()
        
        # Test OTP verification
        test_verify_endpoint()
        
        # Test protected endpoints without auth
        test_profile_endpoints_without_auth()
        test_update_profile_without_auth()
        test_delete_user_without_auth()
        
        print("\n" + "="*50)
        print("✓ All authentication endpoint tests passed!")
        print("="*50)
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
