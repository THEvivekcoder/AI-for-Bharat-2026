"""Test complete authentication flow"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import requests
import time
from app.redis_client import RedisCache

# Base URL
BASE_URL = "http://localhost:8000"

def test_complete_auth_flow():
    """Test complete authentication flow"""
    
    print("\n" + "="*60)
    print("Testing Complete Authentication Flow")
    print("="*60)
    
    # Test 1: Register user
    print("\n1. Registering new user...")
    phone = "+919988776655"
    register_data = {
        "phone_number": phone,
        "language": "hi"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    assert response.status_code == 201, "Registration failed"
    user_id = response.json()["user_id"]
    print(f"   ✓ User registered: {user_id}")
    
    # Test 2: Get OTP from Redis
    print("\n2. Getting OTP from Redis...")
    redis = RedisCache()
    otp_key = f"otp:{phone}"
    otp = redis.get(otp_key)
    print(f"   OTP: {otp}")
    assert otp is not None, "OTP not found in Redis"
    print(f"   ✓ OTP retrieved: {otp}")
    
    # Test 3: Verify OTP
    print("\n3. Verifying OTP...")
    verify_data = {
        "phone_number": phone,
        "otp": otp
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/verify", json=verify_data)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    assert response.status_code == 200, "OTP verification failed"
    token = response.json()["access_token"]
    print(f"   ✓ Token received")
    
    # Test 4: Get user profile (should have no profile data yet)
    print("\n4. Getting user profile...")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/api/user/profile", headers=headers)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    assert response.status_code == 200, "Get profile failed"
    assert response.json()["profile"] is None, "Profile should be None initially"
    print(f"   ✓ Profile retrieved (no profile data yet)")
    
    # Test 5: Update user profile
    print("\n5. Updating user profile...")
    profile_data = {
        "age": 35,
        "gender": "male",
        "education_level": "graduate",
        "occupation": "farmer",
        "income_bracket": "50000-100000",
        "household_size": 5,
        "location": {
            "state": "Maharashtra",
            "district": "Pune",
            "block": "Haveli",
            "village": "Kharadi",
            "pincode": "411014",
            "latitude": 18.5679,
            "longitude": 73.9143
        }
    }
    
    response = requests.put(f"{BASE_URL}/api/user/profile", json=profile_data, headers=headers)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    assert response.status_code == 200, "Update profile failed"
    print(f"   ✓ Profile updated")
    
    # Test 6: Get updated profile
    print("\n6. Getting updated profile...")
    response = requests.get(f"{BASE_URL}/api/user/profile", headers=headers)
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   User ID: {data['user_id']}")
    print(f"   Phone: {data['phone_number']}")
    print(f"   Language: {data['language']}")
    if data['profile']:
        print(f"   Age: {data['profile']['age']}")
        print(f"   Gender: {data['profile']['gender']}")
        print(f"   Occupation: {data['profile']['occupation']}")
        if data['profile']['location']:
            print(f"   Location: {data['profile']['location']['village']}, {data['profile']['location']['district']}")
    assert response.status_code == 200, "Get updated profile failed"
    assert data["profile"] is not None, "Profile should exist"
    assert data["profile"]["age"] == 35, "Age should be 35"
    print(f"   ✓ Profile retrieved with all data")
    
    # Test 7: Update profile again (should update, not create)
    print("\n7. Updating profile again...")
    update_data = {
        "age": 36,
        "household_size": 6
    }
    
    response = requests.put(f"{BASE_URL}/api/user/profile", json=update_data, headers=headers)
    print(f"   Status: {response.status_code}")
    assert response.status_code == 200, "Second update failed"
    assert response.json()["age"] == 36, "Age should be updated to 36"
    print(f"   ✓ Profile updated successfully")
    
    # Test 8: Delete user data
    print("\n8. Deleting user data...")
    response = requests.delete(f"{BASE_URL}/api/user/data", headers=headers)
    print(f"   Status: {response.status_code}")
    assert response.status_code == 204, "Delete user failed"
    print(f"   ✓ User data deleted")
    
    # Test 9: Try to get profile after deletion (should fail with 401)
    print("\n9. Trying to get profile after deletion...")
    response = requests.get(f"{BASE_URL}/api/user/profile", headers=headers)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    assert response.status_code == 401, "Should fail with 401 after user deletion"
    print(f"   ✓ Correctly returns 401 after user deletion")
    
    print("\n" + "="*60)
    print("✓ All authentication flow tests passed!")
    print("="*60)


if __name__ == "__main__":
    try:
        # Wait a moment for server to be ready
        time.sleep(2)
        
        # Run tests
        test_complete_auth_flow()
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Could not connect to server. Make sure the server is running on port 8000")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
