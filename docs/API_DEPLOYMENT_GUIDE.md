# BharatSahayak API Deployment Guide

## Overview

This guide explains how to deploy and test the BharatSahayak API Gateway with Lambda functions.

## Prerequisites

- AWS CLI configured with appropriate credentials
- AWS SAM CLI installed
- Python 3.11 installed
- Access to AWS account with permissions for Lambda, API Gateway, DynamoDB, S3, and Cognito

## Deployment Stages

The API supports three deployment stages:
- **dev**: Development environment with debug logging and no caching
- **staging**: Pre-production environment for testing
- **prod**: Production environment with caching, optimized logging, and X-Ray tracing

## Deployment Steps

### 1. Build the SAM Application

```bash
sam build
```

### 2. Deploy to Dev Environment

```bash
sam deploy --parameter-overrides Environment=dev --guided
```

Follow the prompts to configure:
- Stack name: `bharatsahayak-dev`
- AWS Region: Your preferred region
- Confirm changes before deploy: Y
- Allow SAM CLI IAM role creation: Y
- Save arguments to configuration file: Y

### 3. Deploy to Prod Environment

```bash
sam deploy --parameter-overrides Environment=prod --config-env prod
```

## Stage Variables

Each stage has the following variables configured:

| Variable | Dev | Prod |
|----------|-----|------|
| Environment | dev | prod |
| LogLevel | DEBUG | INFO |
| EnableCaching | false | true |
| CacheTTL | 60 | 300 |
| EnableXRay | false | true |

## API Endpoints

After deployment, the following endpoints are available:

### Authentication (No Auth Required)
- `POST /auth/register` - Register new user
- `POST /auth/verify` - Verify OTP and get JWT token

### User Profile (Auth Required)
- `GET /user/profile` - Get user profile
- `PUT /user/profile` - Update user profile

### Schemes (Public)
- `GET /schemes` - Search schemes with filters
- `GET /schemes/{scheme_id}` - Get scheme details

### Eligibility (Auth Required)
- `POST /schemes/check-eligibility` - Check eligibility for a specific scheme
- `POST /schemes/eligible` - Get all eligible schemes for user

## Rate Limiting

The API implements the following rate limits:
- **Burst Limit**: 100 requests
- **Rate Limit**: 50 requests per second
- **Daily Quota**: 10,000 requests per day

When rate limit is exceeded, the API returns:
```json
{
  "error": "RATE_LIMIT_EXCEEDED",
  "message": "Too many requests. Please try again in 60 seconds.",
  "retry_after_seconds": 60
}
```

## Testing the API

### 1. Get API Endpoint

After deployment, get the API endpoint from CloudFormation outputs:

```bash
aws cloudformation describe-stacks \
  --stack-name bharatsahayak-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text
```

### 2. Test Registration

```bash
curl -X POST https://YOUR_API_ENDPOINT/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+919876543210",
    "language": "hi"
  }'
```

### 3. Test Scheme Search

```bash
curl -X GET "https://YOUR_API_ENDPOINT/schemes?category=agriculture" \
  -H "Content-Type: application/json"
```

### 4. Test Scheme Details

```bash
curl -X GET "https://YOUR_API_ENDPOINT/schemes/SCHEME_ID" \
  -H "Content-Type: application/json"
```

### 5. Test Eligibility Check (Requires Auth)

First, get a JWT token from registration/verification, then:

```bash
curl -X POST https://YOUR_API_ENDPOINT/schemes/check-eligibility \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "scheme_id": "SCHEME_ID",
    "user_profile": {
      "phone_number": "+919876543210",
      "language": "hi",
      "age": 30,
      "location": {
        "state": "Maharashtra",
        "district": "Pune",
        "pincode": "411001"
      },
      "occupation": "farmer",
      "income_bracket": "below_2_lakh"
    }
  }'
```

## Monitoring

### CloudWatch Logs

View Lambda function logs:

```bash
sam logs -n RegisterFunction --stack-name bharatsahayak-dev --tail
```

### API Gateway Metrics

Monitor API Gateway metrics in CloudWatch:
- Request count
- Latency (4xx, 5xx errors)
- Cache hit/miss ratio (prod only)
- Throttle count

### X-Ray Tracing (Prod Only)

View distributed traces in AWS X-Ray console to analyze:
- End-to-end request flow
- Lambda function performance
- DynamoDB query latency
- External API calls

## Troubleshooting

### Issue: 403 Forbidden on authenticated endpoints

**Solution**: Ensure you're passing a valid JWT token in the Authorization header:
```
Authorization: Bearer YOUR_JWT_TOKEN
```

### Issue: 429 Too Many Requests

**Solution**: You've exceeded the rate limit. Wait 60 seconds and retry.

### Issue: CORS errors in browser

**Solution**: The API is configured with CORS enabled. Ensure you're including the correct headers:
- `Content-Type: application/json`
- `Authorization: Bearer YOUR_JWT_TOKEN` (for authenticated endpoints)

### Issue: Lambda timeout

**Solution**: Check CloudWatch logs for the specific function. The timeout is set to 30 seconds. If operations take longer, consider:
- Optimizing DynamoDB queries
- Implementing pagination
- Increasing Lambda timeout (in template.yaml)

## Cleanup

To delete the stack and all resources:

```bash
sam delete --stack-name bharatsahayak-dev
```

**Warning**: This will delete all data in DynamoDB tables and S3 buckets.

## Next Steps

1. Set up CI/CD pipeline for automated deployments
2. Configure custom domain name for API
3. Implement API key authentication for public endpoints
4. Set up CloudWatch alarms for monitoring
5. Configure AWS WAF for additional security
