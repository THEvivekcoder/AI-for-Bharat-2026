#!/bin/bash

# Comprehensive test for authentication endpoints

echo "=== Starting FastAPI server in background ==="
python -m uvicorn app.main:app --port 8000 &
SERVER_PID=$!
echo "Server PID: $SERVER_PID"

# Wait for server to start
echo "Waiting for server to start..."
sleep 5

# Test 1: Register a new user
echo ""
echo "=== Test 1: Register new user ==="
REGISTER_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+919999999999", "language": "hi"}')
echo "Response: $REGISTER_RESPONSE"

# Extract OTP from logs (in production, this would be sent via SMS)
# For testing, we'll use Redis to get the OTP
echo ""
echo "=== Getting OTP from Redis ==="
OTP=$(redis-cli GET "otp:+919999999999")
echo "OTP: $OTP"

# Test 2: Verify OTP and get token
echo ""
echo "=== Test 2: Verify OTP and get token ==="
VERIFY_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/auth/verify" \
  -H "Content-Type: application/json" \
  -d "{\"phone_number\": \"+919999999999\", \"otp\": \"$OTP\"}")
echo "Response: $VERIFY_RESPONSE"

# Extract token
TOKEN=$(echo $VERIFY_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))")
echo "Token: $TOKEN"

# Test 3: Get user profile (authenticated)
echo ""
echo "=== Test 3: Get user profile (authenticated) ==="
PROFILE_RESPONSE=$(curl -s -X GET "http://localhost:8000/api/user/profile" \
  -H "Authorization: Bearer $TOKEN")
echo "Response: $PROFILE_RESPONSE"

# Test 4: Update user profile (authenticated)
echo ""
echo "=== Test 4: Update user profile (authenticated) ==="
UPDATE_RESPONSE=$(curl -s -X PUT "http://localhost:8000/api/user/profile" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
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
  }')
echo "Response: $UPDATE_RESPONSE"

# Test 5: Get updated profile
echo ""
echo "=== Test 5: Get updated profile ==="
UPDATED_PROFILE=$(curl -s -X GET "http://localhost:8000/api/user/profile" \
  -H "Authorization: Bearer $TOKEN")
echo "Response: $UPDATED_PROFILE"

# Test 6: Delete user data (authenticated)
echo ""
echo "=== Test 6: Delete user data (authenticated) ==="
DELETE_RESPONSE=$(curl -s -w "\nHTTP Status: %{http_code}" -X DELETE "http://localhost:8000/api/user/data" \
  -H "Authorization: Bearer $TOKEN")
echo "Response: $DELETE_RESPONSE"

# Test 7: Try to get profile after deletion (should fail)
echo ""
echo "=== Test 7: Try to get profile after deletion ==="
DELETED_PROFILE=$(curl -s -X GET "http://localhost:8000/api/user/profile" \
  -H "Authorization: Bearer $TOKEN")
echo "Response: $DELETED_PROFILE"

# Stop server
echo ""
echo "=== Stopping server ==="
kill $SERVER_PID
wait $SERVER_PID 2>/dev/null

echo ""
echo "=== All tests completed ==="
