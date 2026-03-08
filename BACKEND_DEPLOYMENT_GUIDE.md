# 🚀 Backend Deployment Guide - BharatSahayak

## New Endpoints Added

### 1. POST /auth/login
**Purpose**: Login existing users (send OTP)  
**File**: `src/api/auth_login.py`  
**Status**: ✅ Created

**Request**:
```json
{
  "phone_number": "+919876543210"
}
```

**Response**:
```json
{
  "message": "OTP sent to your phone number",
  "session": "cognito_session_token",
  "user_exists": true,
  "user_id": "uuid"
}
```

### 2. GET /health-check
**Purpose**: Health monitoring endpoint  
**File**: `src/api/health_check.py`  
**Status**: ✅ Created

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-20T10:00:00Z",
  "environment": "development",
  "version": "1.0.0",
  "region": "ap-south-1",
  "services": {
    "dynamodb": "healthy",
    "cognito": "healthy"
  }
}
```

## Deployment Steps

### Option 1: Serverless Framework (Recommended)

#### Step 1: Update serverless.yml
Add the contents of `serverless-additions.yml` to your existing `serverless.yml` file.

```bash
# Merge the new functions into your serverless.yml
cat serverless-additions.yml >> serverless.yml
```

#### Step 2: Deploy
```bash
# Deploy to development
serverless deploy --stage dev

# Deploy to production
serverless deploy --stage prod
```

#### Step 3: Verify Deployment
```bash
# Test health check
curl https://YOUR-API-GATEWAY-URL/dev/health-check

# Test login endpoint
curl -X POST https://YOUR-API-GATEWAY-URL/dev/auth/login \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+919876543210"}'
```

### Option 2: AWS Console Manual Deployment

#### Step 1: Create Lambda Functions

**For auth_login:**
1. Go to AWS Lambda Console
2. Click "Create function"
3. Name: `bharatsahayak-auth-login-dev`
4. Runtime: Python 3.9 or higher
5. Upload code from `src/api/auth_login.py`
6. Set environment variables:
   - `USER_POOL_ID`: Your Cognito User Pool ID
   - `USER_POOL_CLIENT_ID`: Your Cognito Client ID
   - `USERS_TABLE`: `bharatsahayak-users-dev`
   - `AWS_REGION`: `ap-south-1`
   - `LOG_LEVEL`: `INFO`

**For health_check:**
1. Create another function
2. Name: `bharatsahayak-health-check-dev`
3. Runtime: Python 3.9 or higher
4. Upload code from `src/api/health_check.py`
5. Set environment variables:
   - `ENVIRONMENT`: `development`
   - `VERSION`: `1.0.0`
   - `AWS_REGION`: `ap-south-1`
   - `USER_POOL_ID`: Your Cognito User Pool ID
   - `LOG_LEVEL`: `INFO`

#### Step 2: Configure IAM Permissions

**For auth_login Lambda:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cognito-idp:InitiateAuth",
        "cognito-idp:AdminInitiateAuth"
      ],
      "Resource": "arn:aws:cognito-idp:ap-south-1:ACCOUNT_ID:userpool/USER_POOL_ID"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:Query"
      ],
      "Resource": [
        "arn:aws:dynamodb:ap-south-1:ACCOUNT_ID:table/bharatsahayak-users-dev",
        "arn:aws:dynamodb:ap-south-1:ACCOUNT_ID:table/bharatsahayak-users-dev/index/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

**For health_check Lambda:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:ListTables"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "cognito-idp:DescribeUserPool"
      ],
      "Resource": "arn:aws:cognito-idp:ap-south-1:ACCOUNT_ID:userpool/USER_POOL_ID"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

#### Step 3: Configure API Gateway

1. Go to API Gateway Console
2. Select your API: `bharatsahayak-api-dev`
3. Create new resources:

**For /auth/login:**
- Resource path: `/auth/login`
- Method: `POST`
- Integration type: Lambda Function
- Lambda Function: `bharatsahayak-auth-login-dev`
- Enable CORS

**For /health-check:**
- Resource path: `/health-check`
- Method: `GET`
- Integration type: Lambda Function
- Lambda Function: `bharatsahayak-health-check-dev`
- Enable CORS

#### Step 4: Enable CORS

For each endpoint, add these headers:
```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization
```

#### Step 5: Deploy API
1. Click "Actions" → "Deploy API"
2. Stage: `dev`
3. Note the Invoke URL

### Option 3: AWS SAM

#### Step 1: Create SAM Template
```yaml
# template.yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Resources:
  AuthLoginFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: bharatsahayak-auth-login-dev
      CodeUri: src/api/
      Handler: auth_login.lambda_handler
      Runtime: python3.9
      Environment:
        Variables:
          USER_POOL_ID: !Ref UserPoolId
          USER_POOL_CLIENT_ID: !Ref UserPoolClientId
          USERS_TABLE: bharatsahayak-users-dev
          AWS_REGION: ap-south-1
      Events:
        LoginApi:
          Type: Api
          Properties:
            Path: /auth/login
            Method: post
            RestApiId: !Ref ApiGateway

  HealthCheckFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: bharatsahayak-health-check-dev
      CodeUri: src/api/
      Handler: health_check.lambda_handler
      Runtime: python3.9
      Environment:
        Variables:
          ENVIRONMENT: development
          VERSION: 1.0.0
          AWS_REGION: ap-south-1
      Events:
        HealthApi:
          Type: Api
          Properties:
            Path: /health-check
            Method: get
            RestApiId: !Ref ApiGateway
```

#### Step 2: Deploy with SAM
```bash
sam build
sam deploy --guided
```

## Testing the Deployment

### Test Health Check
```bash
# Using curl
curl https://dvt82zj0c4.execute-api.ap-south-1.amazonaws.com/dev/health-check

# Expected response
{
  "status": "healthy",
  "timestamp": "2024-01-20T10:00:00Z",
  "environment": "development",
  "version": "1.0.0",
  "region": "ap-south-1",
  "services": {
    "dynamodb": "healthy",
    "cognito": "healthy"
  }
}
```

### Test Login Endpoint
```bash
# Using curl
curl -X POST https://dvt82zj0c4.execute-api.ap-south-1.amazonaws.com/dev/auth/login \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+919876543210"}'

# Expected response (if user exists)
{
  "message": "OTP sent to your phone number",
  "session": "cognito_session_token",
  "user_exists": true,
  "user_id": "uuid"
}

# Expected response (if user doesn't exist)
{
  "error": "User not found. Please register first."
}
```

### Test from Frontend
```javascript
// Open browser console on frontend/test-quick.html
await api.login('+919876543210')
```

## Monitoring & Logging

### CloudWatch Logs
```bash
# View logs for auth_login
aws logs tail /aws/lambda/bharatsahayak-auth-login-dev --follow

# View logs for health_check
aws logs tail /aws/lambda/bharatsahayak-health-check-dev --follow
```

### CloudWatch Metrics
Monitor these metrics:
- Invocations
- Errors
- Duration
- Throttles

### CloudWatch Alarms
Set up alarms for:
- Error rate > 5% (5 minutes)
- Duration > 3000ms (5 minutes)
- Throttles > 0 (1 minute)

## Environment Variables

### Required for auth_login
```bash
USER_POOL_ID=ap-south-1_KSJ0FKz20
USER_POOL_CLIENT_ID=10emq71eioca5qkns6on0l22om
USERS_TABLE=bharatsahayak-users-dev
AWS_REGION=ap-south-1
LOG_LEVEL=INFO
```

### Required for health_check
```bash
ENVIRONMENT=development
VERSION=1.0.0
AWS_REGION=ap-south-1
USER_POOL_ID=ap-south-1_KSJ0FKz20
LOG_LEVEL=INFO
```

## Troubleshooting

### Issue: "User not found"
**Cause**: User doesn't exist in DynamoDB  
**Solution**: User needs to register first using `/auth/register`

### Issue: "Account error. Please contact support."
**Cause**: User exists in DynamoDB but not in Cognito (data inconsistency)  
**Solution**: 
1. Check Cognito User Pool
2. Verify user exists
3. If not, delete from DynamoDB and re-register

### Issue: "Failed to send OTP"
**Cause**: Cognito SMS not configured or SNS issue  
**Solution**:
1. Check Cognito SMS configuration
2. Verify SNS permissions
3. Check AWS account SMS spending limit

### Issue: "Internal server error"
**Cause**: Lambda execution error  
**Solution**: Check CloudWatch Logs for detailed error

### Issue: CORS errors
**Cause**: CORS headers not configured  
**Solution**: Ensure all endpoints return proper CORS headers

## Security Considerations

### Production Checklist
- [ ] Change CORS origin from `*` to specific domain
- [ ] Enable API Gateway throttling
- [ ] Enable API Gateway caching
- [ ] Set up WAF rules
- [ ] Enable CloudTrail logging
- [ ] Rotate Cognito secrets
- [ ] Enable encryption at rest for DynamoDB
- [ ] Set up VPC for Lambda functions
- [ ] Enable X-Ray tracing
- [ ] Set up CloudWatch alarms

### Rate Limiting
Configure API Gateway throttling:
- Burst limit: 100 requests
- Rate limit: 50 requests/second

### Authentication
- All endpoints except `/auth/*` and `/health-check` require JWT token
- Token expiration: 24 hours
- Implement token refresh mechanism

## Cost Optimization

### Lambda
- Memory: 256 MB (adjust based on usage)
- Timeout: 30 seconds
- Reserved concurrency: Not set (use on-demand)

### API Gateway
- Enable caching for GET endpoints
- Cache TTL: 300 seconds
- Cache size: 0.5 GB

### DynamoDB
- Use on-demand billing for development
- Switch to provisioned for production with auto-scaling

## Rollback Plan

If deployment fails:
```bash
# Rollback to previous version
serverless rollback --stage dev

# Or manually in AWS Console:
# 1. Go to Lambda Console
# 2. Select function
# 3. Click "Versions"
# 4. Promote previous version
```

## Next Steps

1. ✅ Deploy new endpoints
2. ✅ Test with frontend
3. ✅ Monitor CloudWatch logs
4. ✅ Set up alarms
5. ✅ Update API documentation
6. ✅ Configure production environment

## Support

For deployment issues:
1. Check CloudWatch Logs
2. Verify IAM permissions
3. Test endpoints with curl
4. Check API Gateway configuration
5. Verify environment variables

## Summary

**New Endpoints**: 2  
**Deployment Time**: ~10 minutes  
**Testing Time**: ~5 minutes  
**Total Time**: ~15 minutes  

**Status**: Ready to deploy! 🚀
