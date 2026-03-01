# BharatSahayak - Deployment Checklist

## Project Status Summary

✅ **Completed:**
- Core Python backend with Lambda functions
- DynamoDB data models and repositories
- User authentication with Cognito
- Eligibility checking engine
- Scheme search and filtering
- Impact tracking and analytics
- Frontend web interface
- 313 unit and property tests passing (100%)
- 79% code coverage

⚠️ **Pending Manual Steps:**
- AWS infrastructure deployment
- DynamoDB table creation
- Cognito User Pool configuration
- S3 bucket setup
- API Gateway deployment
- Environment configuration
- Integration test fixes

---

## Prerequisites

Before starting, ensure you have:

1. **AWS Account** with appropriate permissions
2. **AWS CLI** installed and configured
   ```bash
   # Install AWS CLI
   # Windows: Download from https://aws.amazon.com/cli/
   # Linux/Mac: pip install awscli
   
   # Configure credentials
   aws configure
   # Enter: Access Key ID, Secret Access Key, Region (us-east-1), Output format (json)
   ```

3. **AWS SAM CLI** installed
   ```bash
   # Windows: Download from https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html
   # Linux/Mac: brew install aws-sam-cli
   ```

4. **Python 3.11** installed
5. **Node.js** (for frontend deployment)

---

## Step 1: Configure Environment Variables

### 1.1 Create `.env` file from template

```bash
cp .env.example .env
```

### 1.2 Edit `.env` with your values

```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=your-account-id-here

# DynamoDB Tables
USERS_TABLE=BharatSahayak-Users
SCHEMES_TABLE=BharatSahayak-Schemes
USER_PROFILES_TABLE=BharatSahayak-UserProfiles
INTERACTIONS_TABLE=BharatSahayak-Interactions

# Cognito
COGNITO_USER_POOL_ID=your-user-pool-id
COGNITO_CLIENT_ID=your-client-id

# S3
S3_BUCKET_NAME=bharatsahayak-content
S3_REGION=us-east-1

# Security
JWT_SECRET=your-secure-random-string-here-min-32-chars
ENCRYPTION_KEY=your-base64-encoded-32-byte-key-here

# API Gateway
API_GATEWAY_URL=https://your-api-id.execute-api.us-east-1.amazonaws.com/prod
```

**Generate secure keys:**
```bash
# Generate JWT Secret
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate Encryption Key
python -c "import base64, os; print(base64.b64encode(os.urandom(32)).decode())"
```

---

## Step 2: Deploy AWS Infrastructure

### 2.1 Create DynamoDB Tables

Run the following AWS CLI commands:

```bash
# Create Users Table
aws dynamodb create-table \
    --table-name BharatSahayak-Users \
    --attribute-definitions \
        AttributeName=user_id,AttributeType=S \
    --key-schema \
        AttributeName=user_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region us-east-1

# Create Schemes Table
aws dynamodb create-table \
    --table-name BharatSahayak-Schemes \
    --attribute-definitions \
        AttributeName=scheme_id,AttributeType=S \
        AttributeName=category,AttributeType=S \
    --key-schema \
        AttributeName=scheme_id,KeyType=HASH \
    --global-secondary-indexes \
        "[{\"IndexName\":\"category-index\",\"KeySchema\":[{\"AttributeName\":\"category\",\"KeyType\":\"HASH\"}],\"Projection\":{\"ProjectionType\":\"ALL\"}}]" \
    --billing-mode PAY_PER_REQUEST \
    --region us-east-1

# Create UserProfiles Table
aws dynamodb create-table \
    --table-name BharatSahayak-UserProfiles \
    --attribute-definitions \
        AttributeName=user_id,AttributeType=S \
    --key-schema \
        AttributeName=user_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region us-east-1

# Create Interactions Table
aws dynamodb create-table \
    --table-name BharatSahayak-Interactions \
    --attribute-definitions \
        AttributeName=user_id,AttributeType=S \
        AttributeName=timestamp,AttributeType=S \
    --key-schema \
        AttributeName=user_id,KeyType=HASH \
        AttributeName=timestamp,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST \
    --region us-east-1
```

**Verify tables created:**
```bash
aws dynamodb list-tables --region us-east-1
```

### 2.2 Create S3 Bucket

```bash
# Create bucket
aws s3 mb s3://bharatsahayak-content --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
    --bucket bharatsahayak-content \
    --versioning-configuration Status=Enabled

# Create folder structure
aws s3api put-object --bucket bharatsahayak-content --key schemes/
aws s3api put-object --bucket bharatsahayak-content --key documents/
aws s3api put-object --bucket bharatsahayak-content --key cache/
```

### 2.3 Configure Cognito User Pool

```bash
# Create User Pool
aws cognito-idp create-user-pool \
    --pool-name BharatSahayak-Users \
    --username-attributes phone_number \
    --auto-verified-attributes phone_number \
    --mfa-configuration OFF \
    --sms-authentication-message "Your BharatSahayak verification code is {####}" \
    --region us-east-1

# Note the UserPoolId from output, then create app client
aws cognito-idp create-user-pool-client \
    --user-pool-id YOUR_USER_POOL_ID \
    --client-name BharatSahayak-Client \
    --no-generate-secret \
    --explicit-auth-flows ALLOW_USER_SRP_AUTH ALLOW_REFRESH_TOKEN_AUTH ALLOW_CUSTOM_AUTH \
    --region us-east-1

# Note the ClientId from output
```

**Update `.env` file with the UserPoolId and ClientId**

---

## Step 3: Deploy Lambda Functions with SAM

### 3.1 Build the SAM application

```bash
sam build
```

### 3.2 Deploy to AWS

```bash
# First deployment (guided)
sam deploy --guided

# Follow prompts:
# - Stack Name: bharatsahayak-stack
# - AWS Region: us-east-1
# - Confirm changes before deploy: Y
# - Allow SAM CLI IAM role creation: Y
# - Save arguments to configuration file: Y
```

### 3.3 Get API Gateway URL

```bash
# After deployment, get the API URL
aws cloudformation describe-stacks \
    --stack-name bharatsahayak-stack \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
    --output text
```

**Update `.env` file with the API_GATEWAY_URL**

---

## Step 4: Load Sample Scheme Data

### 4.1 Create scheme loader script

Create `scripts/load_schemes.py`:

```python
import boto3
import json
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('BharatSahayak-Schemes')

# Sample schemes
schemes = [
    {
        'scheme_id': 'PM-KISAN-2024',
        'name': 'Pradhan Mantri Kisan Samman Nidhi',
        'category': 'agriculture',
        'description': 'Income support for farmers',
        'benefits': ['Rs. 6000 per year', 'Direct bank transfer'],
        'eligibility_criteria': {
            'age_min': 18,
            'occupation': ['farmer']
        },
        'required_documents': ['Aadhaar', 'Bank account'],
        'application_process': ['Visit portal', 'Fill form', 'Submit'],
        'department': 'Agriculture',
        'last_updated': datetime.now().isoformat()
    },
    # Add more schemes...
]

# Load schemes
for scheme in schemes:
    table.put_item(Item=scheme)
    print(f"Loaded: {scheme['name']}")
```

### 4.2 Run the loader

```bash
python scripts/load_schemes.py
```

---

## Step 5: Deploy Frontend

### 5.1 Update frontend configuration

Edit `frontend/app.js` and update the API URL:

```javascript
const API_BASE_URL = 'https://your-api-id.execute-api.us-east-1.amazonaws.com/prod';
```

### 5.2 Deploy to S3

```bash
cd frontend

# Create S3 bucket for frontend
aws s3 mb s3://bharatsahayak-frontend --region us-east-1

# Enable static website hosting
aws s3 website s3://bharatsahayak-frontend \
    --index-document index.html \
    --error-document index.html

# Upload files
aws s3 sync . s3://bharatsahayak-frontend --exclude "*.sh" --exclude "*.md"

# Make bucket public
aws s3api put-bucket-policy \
    --bucket bharatsahayak-frontend \
    --policy file://bucket-policy.json
```

Create `frontend/bucket-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::bharatsahayak-frontend/*"
    }
  ]
}
```

### 5.3 (Optional) Set up CloudFront

```bash
# Run the CloudFront setup script
bash frontend/setup-cloudfront.sh
```

---

## Step 6: Test End-to-End

### 6.1 Test API endpoints

```bash
# Test health check
curl https://your-api-id.execute-api.us-east-1.amazonaws.com/prod/health

# Test scheme search
curl https://your-api-id.execute-api.us-east-1.amazonaws.com/prod/schemes?category=agriculture
```

### 6.2 Test frontend

Open your browser to:
- S3 website: `http://bharatsahayak-frontend.s3-website-us-east-1.amazonaws.com`
- CloudFront (if configured): `https://your-distribution-id.cloudfront.net`

### 6.3 Test user flow

1. Register a new user with phone number
2. Verify OTP
3. Create user profile
4. Search for schemes
5. Check eligibility

---

## Step 7: Fix Integration Tests

The 12 failing integration tests need proper moto mocking. Update test setup:

### 7.1 Create `tests/integration/conftest.py`

```python
import pytest
import boto3
from moto import mock_dynamodb

@pytest.fixture(scope='function')
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    import os
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

@pytest.fixture(scope='function')
def dynamodb_mock(aws_credentials):
    """Create mocked DynamoDB."""
    with mock_dynamodb():
        yield boto3.resource('dynamodb', region_name='us-east-1')
```

### 7.2 Run integration tests

```bash
python -m pytest tests/integration/ -v
```

---

## Step 8: Monitor and Maintain

### 8.1 Set up CloudWatch alarms

```bash
# Lambda error alarm
aws cloudwatch put-metric-alarm \
    --alarm-name bharatsahayak-lambda-errors \
    --alarm-description "Alert on Lambda errors" \
    --metric-name Errors \
    --namespace AWS/Lambda \
    --statistic Sum \
    --period 300 \
    --threshold 5 \
    --comparison-operator GreaterThanThreshold

# DynamoDB throttle alarm
aws cloudwatch put-metric-alarm \
    --alarm-name bharatsahayak-dynamodb-throttles \
    --alarm-description "Alert on DynamoDB throttles" \
    --metric-name UserErrors \
    --namespace AWS/DynamoDB \
    --statistic Sum \
    --period 300 \
    --threshold 10 \
    --comparison-operator GreaterThanThreshold
```

### 8.2 Enable AWS X-Ray tracing

Update `template.yaml` to add:

```yaml
Globals:
  Function:
    Tracing: Active
```

Redeploy:
```bash
sam build && sam deploy
```

---

## Troubleshooting

### Issue: Lambda timeout
**Solution:** Increase timeout in `template.yaml`:
```yaml
Timeout: 30
```

### Issue: DynamoDB access denied
**Solution:** Check IAM role has DynamoDB permissions in `template.yaml`

### Issue: CORS errors in frontend
**Solution:** Verify API Gateway CORS configuration in `template.yaml`

### Issue: Cognito OTP not sending
**Solution:** 
1. Verify SNS permissions in IAM role
2. Check phone number format (+91XXXXXXXXXX)
3. Verify SMS spending limit in AWS account

---

## Cost Estimation

**Monthly costs (estimated for development/testing):**

- DynamoDB: $0-5 (PAY_PER_REQUEST with low traffic)
- Lambda: $0-2 (1M free tier requests)
- API Gateway: $0-3 (1M free tier requests)
- S3: $0-1 (minimal storage)
- Cognito: $0 (free tier up to 50,000 MAUs)
- CloudFront: $0-5 (optional)

**Total: ~$0-15/month for development**

---

## Next Steps After Deployment

1. **Load production scheme data** from government sources
2. **Implement optional features** (Tasks 12-18 in tasks.md)
3. **Set up CI/CD pipeline** with GitHub Actions
4. **Configure custom domain** for API and frontend
5. **Implement monitoring dashboard** with CloudWatch
6. **Add rate limiting** to prevent abuse
7. **Set up backup strategy** for DynamoDB
8. **Conduct security audit** and penetration testing

---

## Support and Documentation

- **AWS Documentation:** https://docs.aws.amazon.com/
- **SAM Documentation:** https://docs.aws.amazon.com/serverless-application-model/
- **Project README:** See `README.md` for architecture details
- **API Documentation:** See `docs/` folder for detailed API specs

---

## Quick Reference Commands

```bash
# Deploy everything
sam build && sam deploy

# View logs
sam logs -n AuthRegisterFunction --tail

# Run tests
python -m pytest tests/ -v

# Update frontend
cd frontend && aws s3 sync . s3://bharatsahayak-frontend

# Check DynamoDB tables
aws dynamodb list-tables

# Delete stack (cleanup)
sam delete --stack-name bharatsahayak-stack
```

---

**Last Updated:** March 1, 2026
**Project:** BharatSahayak - AI Public Assistant for Rural India
**Status:** Ready for deployment
