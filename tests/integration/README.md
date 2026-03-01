# Integration Tests for BharatSahayak API

This directory contains integration tests that validate the complete request/response flow for all API endpoints.

## Prerequisites

1. **Deploy the API to AWS:**
   ```bash
   sam build
   sam deploy --parameter-overrides Environment=dev --guided
   ```

2. **Install test dependencies:**
   ```bash
   pip install pytest requests
   ```

3. **Set environment variables:**
   ```bash
   export API_ENDPOINT=https://your-api-id.execute-api.region.amazonaws.com/dev
   export JWT_TOKEN=your_jwt_token  # Optional, for authenticated endpoint tests
   ```

## Running Tests

### Run all integration tests:
```bash
pytest tests/integration/test_api_integration.py -v
```

### Run specific test class:
```bash
# Test only public endpoints
pytest tests/integration/test_api_integration.py::TestPublicEndpoints -v

# Test only authentication endpoints
pytest tests/integration/test_api_integration.py::TestAuthenticationEndpoints -v

# Test only authenticated endpoints (requires JWT_TOKEN)
pytest tests/integration/test_api_integration.py::TestAuthenticatedEndpoints -v

# Test error handling
pytest tests/integration/test_api_integration.py::TestErrorHandling -v
```

### Run specific test:
```bash
pytest tests/integration/test_api_integration.py::TestPublicEndpoints::test_search_schemes_success -v
```

### Run with detailed output:
```bash
pytest tests/integration/test_api_integration.py -v -s
```

## Test Coverage

### Public Endpoints (No Authentication Required)
- ✅ Search schemes with filters
- ✅ Search schemes without filters
- ✅ Get scheme details
- ✅ Handle invalid scheme IDs
- ✅ CORS configuration

### Authentication Endpoints
- ✅ User registration with valid data
- ✅ User registration with invalid phone number
- ✅ User registration with missing fields
- ✅ OTP verification with invalid OTP

### Authenticated Endpoints (Requires JWT Token)
- ✅ Get user profile
- ✅ Update user profile
- ✅ Check eligibility for specific scheme
- ✅ Get all eligible schemes
- ✅ Authorization validation (401/403 without token)

### Error Handling
- ✅ 404 for invalid endpoints
- ✅ 405 for invalid HTTP methods
- ✅ 400 for malformed JSON
- ✅ 429 for rate limiting
- ✅ Consistent error response format

### Response Format
- ✅ Valid JSON responses
- ✅ Correct Content-Type headers
- ✅ Consistent error format

## Getting API Endpoint

After deploying with SAM, get your API endpoint:

```bash
aws cloudformation describe-stacks \
  --stack-name bharatsahayak-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text
```

Or from SAM deployment output:
```bash
sam deploy --parameter-overrides Environment=dev
# Look for "ApiEndpoint" in the Outputs section
```

## Getting JWT Token

To test authenticated endpoints, you need a JWT token:

1. Register a user:
   ```bash
   curl -X POST https://YOUR_API_ENDPOINT/auth/register \
     -H "Content-Type: application/json" \
     -d '{"phone_number": "+919876543210", "language": "hi"}'
   ```

2. Verify OTP (you'll receive OTP via SMS):
   ```bash
   curl -X POST https://YOUR_API_ENDPOINT/auth/verify \
     -H "Content-Type: application/json" \
     -d '{"phone_number": "+919876543210", "otp": "123456"}'
   ```

3. Extract the JWT token from the response and set it:
   ```bash
   export JWT_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

## Continuous Integration

To run these tests in CI/CD pipeline:

```yaml
# Example GitHub Actions workflow
- name: Run Integration Tests
  env:
    API_ENDPOINT: ${{ secrets.API_ENDPOINT }}
    JWT_TOKEN: ${{ secrets.JWT_TOKEN }}
  run: |
    pip install pytest requests
    pytest tests/integration/test_api_integration.py -v
```

## Troubleshooting

### Tests are skipped
- **Cause**: `API_ENDPOINT` environment variable not set
- **Solution**: Set the environment variable before running tests

### Authentication tests fail
- **Cause**: Invalid or expired JWT token
- **Solution**: Generate a new JWT token using the registration/verification flow

### Rate limiting tests don't trigger
- **Cause**: Test environment may have different rate limits
- **Solution**: This is expected; rate limiting is still configured in API Gateway

### Connection timeout
- **Cause**: API Gateway or Lambda cold start
- **Solution**: Increase timeout in test configuration or retry the test

## Best Practices

1. **Run tests after each deployment** to ensure API is working correctly
2. **Use separate test user accounts** to avoid interfering with production data
3. **Monitor test execution time** to detect performance regressions
4. **Review failed tests immediately** to catch deployment issues early
5. **Keep JWT tokens secure** and rotate them regularly
