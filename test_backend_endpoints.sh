#!/bin/bash

# Backend Endpoint Testing Script for BharatSahayak
# This script tests all backend endpoints to verify they're working correctly

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# API Configuration
API_BASE_URL="${API_BASE_URL:-https://dvt82zj0c4.execute-api.ap-south-1.amazonaws.com/dev}"
TEST_PHONE="+919876543210"

# Counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to print colored output
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Function to test an endpoint
test_endpoint() {
    local name=$1
    local method=$2
    local endpoint=$3
    local data=$4
    local expected_status=$5
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    print_info "Testing: $name"
    
    if [ "$method" == "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" -X GET "$API_BASE_URL$endpoint" \
            -H "Content-Type: application/json")
    else
        response=$(curl -s -w "\n%{http_code}" -X POST "$API_BASE_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" == "$expected_status" ]; then
        print_success "$name - Status: $http_code"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        echo "Response: $body" | jq '.' 2>/dev/null || echo "$body"
    else
        print_error "$name - Expected: $expected_status, Got: $http_code"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        echo "Response: $body"
    fi
    
    echo ""
}

# Start testing
print_header "BharatSahayak Backend Endpoint Tests"
print_info "API Base URL: $API_BASE_URL"
print_info "Test Phone: $TEST_PHONE"

# Test 1: Health Check
print_header "Test 1: Health Check"
test_endpoint "Health Check" "GET" "/health-check" "" "200"

# Test 2: Register New User
print_header "Test 2: User Registration"
REGISTER_DATA='{
  "phone_number": "'$TEST_PHONE'",
  "language": "hi",
  "location": {
    "state": "Maharashtra",
    "district": "Pune",
    "pincode": "411014"
  }
}'
test_endpoint "Register User" "POST" "/auth/register" "$REGISTER_DATA" "200"

# Test 3: Login Existing User
print_header "Test 3: User Login"
LOGIN_DATA='{"phone_number": "'$TEST_PHONE'"}'
test_endpoint "Login User" "POST" "/auth/login" "$LOGIN_DATA" "200"

# Test 4: Get All Schemes
print_header "Test 4: Get Schemes"
test_endpoint "Get All Schemes" "GET" "/schemes?limit=5" "" "200"

# Test 5: Search Schemes
print_header "Test 5: Search Schemes"
test_endpoint "Search Schemes" "GET" "/schemes/search?q=agriculture&limit=5" "" "200"

# Test 6: Get Scheme Details (using a sample ID)
print_header "Test 6: Get Scheme Details"
test_endpoint "Get Scheme Details" "GET" "/schemes/PM-KISAN" "" "200"

# Test 7: Voice to Text (without actual audio)
print_header "Test 7: Voice to Text API"
VOICE_DATA='{
  "audio_data": "base64_encoded_audio_data",
  "language": "hi"
}'
print_warning "Skipping Voice to Text test (requires actual audio data)"

# Test 8: Conversational Query
print_header "Test 8: Conversational Query"
QUERY_DATA='{
  "query": "What schemes are available for farmers?",
  "language": "en"
}'
test_endpoint "Conversational Query" "POST" "/conversational-query" "$QUERY_DATA" "200"

# Test 9: CORS Preflight
print_header "Test 9: CORS Preflight"
print_info "Testing CORS headers..."
cors_response=$(curl -s -I -X OPTIONS "$API_BASE_URL/health-check" \
    -H "Origin: http://localhost:3000" \
    -H "Access-Control-Request-Method: GET")

if echo "$cors_response" | grep -q "Access-Control-Allow-Origin"; then
    print_success "CORS headers present"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    print_error "CORS headers missing"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo ""

# Test 10: Invalid Endpoint
print_header "Test 10: Invalid Endpoint (404)"
test_endpoint "Invalid Endpoint" "GET" "/invalid-endpoint" "" "404"

# Summary
print_header "Test Summary"
echo -e "Total Tests: ${BLUE}$TOTAL_TESTS${NC}"
echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed: ${RED}$FAILED_TESTS${NC}"

if [ $FAILED_TESTS -eq 0 ]; then
    print_success "All tests passed! 🎉"
    exit 0
else
    print_error "Some tests failed. Please check the output above."
    exit 1
fi
