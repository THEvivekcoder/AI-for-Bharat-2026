# BharatSahayak Scripts

This directory contains utility scripts for testing and managing the BharatSahayak API.

## test_api_endpoints.py

A comprehensive test script that validates all API Gateway endpoints.

### Prerequisites

```bash
pip install requests
```

### Usage

**Basic usage (test public endpoints only):**
```bash
python scripts/test_api_endpoints.py https://YOUR_API_ENDPOINT/dev
```

**With JWT token (test authenticated endpoints):**
```bash
python scripts/test_api_endpoints.py https://YOUR_API_ENDPOINT/dev YOUR_JWT_TOKEN
```

### What it tests

- ✅ Public endpoints (scheme search, scheme details)
- ✅ Authentication endpoints (register, verify)
- ✅ Authenticated endpoints (profile get/update, eligibility checking)
- ✅ CORS configuration
- ✅ Rate limiting (optional)

### Example Output

```
============================================================
BharatSahayak API Endpoint Tests
============================================================
API Endpoint: https://abc123.execute-api.us-east-1.amazonaws.com/dev
JWT Token: Not provided

Testing: Search Schemes
  GET /schemes?category=agriculture
  ✅ Success: 200

Testing: Get Scheme Details (Invalid ID)
  GET /schemes/invalid-id
  ❌ Failed: Expected 404, got 200

Testing: Register User
  POST /auth/register
  ✅ Success: 200

Testing: CORS Configuration
  ✅ CORS enabled
     Origin: *
     Methods: GET,POST,PUT,DELETE,OPTIONS

============================================================
Test Summary
============================================================
Total Tests: 4
Passed: 3 ✅
Failed: 1 ❌
============================================================
```

## Getting the API Endpoint

After deploying with SAM, get your API endpoint:

```bash
aws cloudformation describe-stacks \
  --stack-name bharatsahayak-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text
```

Or check the SAM deployment output:

```bash
sam deploy --parameter-overrides Environment=dev
# Look for "Outputs" section in the output
```
