#!/bin/bash

# Test authentication endpoints using curl

echo "=== Starting FastAPI server in background ==="
python -m uvicorn app.main:app --port 8000 &
SERVER_PID=$!
echo "Server PID: $SERVER_PID"

# Wait for server to start
echo "Waiting for server to start..."
sleep 5

echo ""
echo "=== Testing POST /api/auth/register ==="
REGISTER_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+919876543210", "language": "hi"}')
echo "Response: $REGISTER_RESPONSE"

echo ""
echo "=== Testing POST /api/auth/verify (with invalid OTP) ==="
VERIFY_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/auth/verify" \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+919876543210", "otp": "123456"}')
echo "Response: $VERIFY_RESPONSE"

echo ""
echo "=== Testing GET /api/user/profile (without auth) ==="
PROFILE_RESPONSE=$(curl -s -X GET "http://localhost:8000/api/user/profile")
echo "Response: $PROFILE_RESPONSE"

echo ""
echo "=== Testing PUT /api/user/profile (without auth) ==="
UPDATE_RESPONSE=$(curl -s -X PUT "http://localhost:8000/api/user/profile" \
  -H "Content-Type: application/json" \
  -d '{"age": 30, "gender": "male"}')
echo "Response: $UPDATE_RESPONSE"

echo ""
echo "=== Testing DELETE /api/user/data (without auth) ==="
DELETE_RESPONSE=$(curl -s -X DELETE "http://localhost:8000/api/user/data")
echo "Response: $DELETE_RESPONSE"

echo ""
echo "=== Testing GET /health ==="
HEALTH_RESPONSE=$(curl -s -X GET "http://localhost:8000/health")
echo "Response: $HEALTH_RESPONSE"

# Stop server
echo ""
echo "=== Stopping server ==="
kill $SERVER_PID
wait $SERVER_PID 2>/dev/null

echo ""
echo "=== Tests completed ==="
