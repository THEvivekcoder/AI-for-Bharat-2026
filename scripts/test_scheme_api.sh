#!/bin/bash

# Test script for Scheme Service API endpoints
# Make sure the server is running before executing this script

BASE_URL="http://localhost:8000"

echo "=========================================="
echo "Testing Scheme Service API Endpoints"
echo "=========================================="

# First, create a test scheme (you'll need admin access for this in production)
echo -e "\n1. Testing GET /api/schemes (list all schemes)"
curl -s -X GET "$BASE_URL/api/schemes" | python -m json.tool | head -20

echo -e "\n\n2. Testing GET /api/schemes with filters"
curl -s -X GET "$BASE_URL/api/schemes?category=agriculture&limit=5" | python -m json.tool | head -20

echo -e "\n\n3. Testing POST /api/schemes/check-eligibility"
curl -s -X POST "$BASE_URL/api/schemes/check-eligibility" \
  -H "Content-Type: application/json" \
  -d '{
    "scheme_id": "test-scheme-id",
    "user_profile": {
      "age": 45,
      "occupation": "farmer",
      "income_bracket": "50000-100000",
      "location": {"state": "Punjab", "district": "Ludhiana"}
    }
  }' | python -m json.tool

echo -e "\n\n4. Testing POST /api/schemes/eligible"
curl -s -X POST "$BASE_URL/api/schemes/eligible" \
  -H "Content-Type: application/json" \
  -d '{
    "user_profile": {
      "age": 45,
      "occupation": "farmer",
      "income_bracket": "50000-100000",
      "location": {"state": "Punjab", "district": "Ludhiana"}
    },
    "category": "agriculture"
  }' | python -m json.tool | head -30

echo -e "\n\n=========================================="
echo "API endpoint tests completed"
echo "=========================================="
