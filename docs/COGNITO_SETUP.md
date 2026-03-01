# AWS Cognito Setup for BharatSahayak

This document describes the AWS Cognito User Pool configuration for user authentication in BharatSahayak. The system uses phone number-based authentication with OTP verification, designed for rural users who may not have email addresses.

## Overview

The `bharatsahayak-users-{environment}` Cognito User Pool provides:

1. **Phone Number Authentication**: Phone number as primary username (no email required)
2. **OTP-Based Verification**: SMS-based one-time password authentication
3. **Custom User Attributes**: preferred_language, location for personalization
4. **Security Compliance**: Meets Requirements 11.1 and 11.2 for data security and privacy

## User Pool Configuration

### Features

- **Username**: Phone number (e.g., +919876543210)
- **Auto-Verification**: Phone numbers are automatically verified via SMS OTP
- **MFA**: Optional SMS-based multi-factor authentication
- **Custom Attributes**:
  - `preferred_language`: User's preferred language (2-10 characters)
  - `location`: User's location information (1-100 characters)
- **Token Validity**:
  - Refresh Token: 30 days
  - Access Token: 60 minutes
  - ID Token: 60 minutes
- **Account Recovery**: Phone number-based recovery

### Authentication Flows

The user pool supports the following authentication flows:

1. **ALLOW_CUSTOM_AUTH**: Custom authentication challenges (for OTP flow)
2. **ALLOW_USER_SRP_AUTH**: Secure Remote Password protocol
3. **ALLOW_REFRESH_TOKEN_AUTH**: Token refresh without re-authentication

### User Attributes Schema

| Attribute | Type | Required | Mutable | Description |
|-----------|------|----------|---------|-------------|
| phone_number | String | Yes | No | User's phone number (username) |
| preferred_language | String | No | Yes | Preferred language code (e.g., "hi", "en") |
| location | String | No | Yes | User's location (state, district, village) |

## Deployment

### Prerequisites

1. **AWS Account** with appropriate permissions
2. **IAM Role for SMS**: Create role `bharatsahayak-cognito-sms-role-{environment}`
3. **SNS SMS Configuration**: Configure SMS spending limits and origination numbers

### 1. Create IAM Role for Cognito SMS

Create an IAM role that allows Cognito to send SMS messages:

```bash
# Create trust policy for Cognito
cat > cognito-sms-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "cognito-idp.amazonaws.com"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "sts:ExternalId": "bharatsahayak-dev"
        }
      }
    }
  ]
}
EOF

# Create the role
aws iam create-role \
  --role-name bharatsahayak-cognito-sms-role-dev \
  --assume-role-policy-document file://cognito-sms-trust-policy.json

# Attach the Cognito SMS policy
aws iam attach-role-policy \
  --role-name bharatsahayak-cognito-sms-role-dev \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonCognitoSMSRole
```

### 2. Configure SNS SMS Settings

```bash
# Set SMS spending limit (optional)
aws sns set-sms-attributes \
  --attributes MonthlySpendLimit=100

# Set default SMS type to Transactional
aws sns set-sms-attributes \
  --attributes DefaultSMSType=Transactional
```

### 3. Create User Pool

Run the setup script to create the Cognito User Pool:

```bash
# Basic setup (creates user pool only)
python infrastructure/scripts/setup_cognito.py --environment dev

# Full setup with app client
python infrastructure/scripts/setup_cognito.py \
  --environment dev \
  --create-app-client

# Display user pool information
python infrastructure/scripts/setup_cognito.py \
  --environment dev \
  --info
```

### 4. Verify Setup

Check that the user pool is properly configured:

```bash
# List user pools
aws cognito-idp list-user-pools --max-results 10

# Describe specific user pool
aws cognito-idp describe-user-pool \
  --user-pool-id ap-south-1_XXXXXXXXX

# List app clients
aws cognito-idp list-user-pool-clients \
  --user-pool-id ap-south-1_XXXXXXXXX
```

## Usage

### User Registration Flow

1. **Initiate Registration**: User provides phone number
2. **Send OTP**: Cognito sends SMS with verification code
3. **Verify OTP**: User enters code to verify phone number
4. **Create Profile**: User sets preferred_language and location
5. **Complete Registration**: User account is created and verified

### Authentication Flow

1. **Initiate Auth**: User provides phone number
2. **Send OTP**: System sends SMS with one-time password
3. **Verify OTP**: User enters OTP code
4. **Issue Tokens**: System issues access, ID, and refresh tokens
5. **Access Resources**: User can access protected resources

### Example: User Registration

```python
import boto3

cognito = boto3.client('cognito-idp', region_name='ap-south-1')

# Sign up new user
response = cognito.sign_up(
    ClientId='your-app-client-id',
    Username='+919876543210',
    Password='temporary-password',  # Optional, can use custom auth
    UserAttributes=[
        {'Name': 'phone_number', 'Value': '+919876543210'},
        {'Name': 'custom:preferred_language', 'Value': 'hi'},
        {'Name': 'custom:location', 'Value': 'Uttar Pradesh, Lucknow'},
    ]
)

# Confirm sign up with OTP
cognito.confirm_sign_up(
    ClientId='your-app-client-id',
    Username='+919876543210',
    ConfirmationCode='123456'
)
```

### Example: User Authentication

```python
# Initiate authentication
response = cognito.initiate_auth(
    ClientId='your-app-client-id',
    AuthFlow='CUSTOM_AUTH',
    AuthParameters={
        'USERNAME': '+919876543210'
    }
)

# Respond to custom challenge (OTP)
response = cognito.respond_to_auth_challenge(
    ClientId='your-app-client-id',
    ChallengeName='CUSTOM_CHALLENGE',
    Session=response['Session'],
    ChallengeResponses={
        'USERNAME': '+919876543210',
        'ANSWER': '123456'  # OTP code
    }
)

# Extract tokens
access_token = response['AuthenticationResult']['AccessToken']
id_token = response['AuthenticationResult']['IdToken']
refresh_token = response['AuthenticationResult']['RefreshToken']
```

### Example: Update User Attributes

```python
# Update user's preferred language
cognito.update_user_attributes(
    AccessToken='user-access-token',
    UserAttributes=[
        {'Name': 'custom:preferred_language', 'Value': 'bn'},
        {'Name': 'custom:location', 'Value': 'West Bengal, Kolkata'},
    ]
)
```

### Example: Token Refresh

```python
# Refresh access token
response = cognito.initiate_auth(
    ClientId='your-app-client-id',
    AuthFlow='REFRESH_TOKEN_AUTH',
    AuthParameters={
        'REFRESH_TOKEN': 'user-refresh-token'
    }
)

new_access_token = response['AuthenticationResult']['AccessToken']
new_id_token = response['AuthenticationResult']['IdToken']
```

## Security Considerations

### Requirement 11.1: Data Encryption

- **In Transit**: All Cognito API calls use TLS 1.3+ encryption
- **At Rest**: User data is encrypted using AWS-managed keys (AES-256)
- **Token Security**: JWT tokens are signed and can be verified

### Requirement 11.2: Access Control and Consent

- **Explicit Consent**: Users must verify phone number before account activation
- **Role-Based Access**: Use Cognito groups for role-based access control
- **Attribute Verification**: Phone number changes require re-verification
- **Token Revocation**: Tokens can be revoked if compromised

### Best Practices

1. **Secure Token Storage**: Store tokens securely on client devices
2. **Token Validation**: Always validate tokens on the backend
3. **Rate Limiting**: Implement rate limiting for OTP requests
4. **Monitoring**: Monitor failed authentication attempts
5. **User Privacy**: Never log or expose user phone numbers in plain text

## OTP Configuration

### SMS Message Template

```
Your BharatSahayak verification code is {####}
```

### OTP Settings

- **Code Length**: 6 digits
- **Validity**: 3 minutes (Cognito default)
- **Retry Limit**: 3 attempts per code
- **Resend Delay**: 60 seconds between resend requests

### SMS Delivery

- **Provider**: Amazon SNS
- **Type**: Transactional (high priority)
- **Origination**: Shared short code or dedicated number
- **Cost**: ~$0.00645 per SMS in India (varies by region)

## Cost Optimization

### Cognito Pricing (as of 2024)

- **MAU (Monthly Active Users)**:
  - First 50,000 MAU: Free
  - Next 50,000 MAU: $0.0055 per MAU
  - Beyond 100,000 MAU: $0.0046 per MAU

- **SMS Costs**:
  - India: ~$0.00645 per SMS
  - Estimate: 2 SMS per user per month (login + verification)

### Cost Reduction Strategies

1. **Token Refresh**: Use refresh tokens to avoid re-authentication
2. **Session Management**: Implement long-lived sessions where appropriate
3. **OTP Alternatives**: Consider app-based OTP for frequent users
4. **Batch Operations**: Use batch APIs for administrative operations

## Monitoring and Logging

### CloudWatch Metrics

Monitor these Cognito metrics:

- `UserAuthentication`: Successful authentications
- `UserAuthenticationFailed`: Failed authentication attempts
- `SignUpSuccesses`: Successful registrations
- `SignUpThrottles`: Throttled registration attempts
- `TokenRefreshSuccesses`: Successful token refreshes

### CloudWatch Logs

Enable CloudWatch Logs for:

- User authentication events
- User registration events
- Token refresh events
- MFA challenges
- Account recovery attempts

### Alarms

Set up CloudWatch alarms for:

- High authentication failure rate (> 10% of attempts)
- Unusual OTP request volume (potential abuse)
- Token refresh failures (potential security issue)

## Troubleshooting

### User Pool Not Found

```bash
# Check if user pool exists
aws cognito-idp list-user-pools --max-results 60

# If not found, run setup script
python infrastructure/scripts/setup_cognito.py --environment dev
```

### SMS Not Delivered

```bash
# Check SNS SMS settings
aws sns get-sms-attributes

# Verify IAM role permissions
aws iam get-role --role-name bharatsahayak-cognito-sms-role-dev

# Check SMS spending limit
aws sns get-sms-attributes --attributes MonthlySpendLimit
```

### Invalid Token Errors

```python
# Verify token signature
from jose import jwt

try:
    claims = jwt.decode(
        token,
        key,
        algorithms=['RS256'],
        audience='your-app-client-id'
    )
except jwt.JWTError as e:
    print(f"Token validation failed: {e}")
```

### Custom Attribute Not Found

Custom attributes must be prefixed with `custom:` when accessing:

```python
# Correct
{'Name': 'custom:preferred_language', 'Value': 'hi'}

# Incorrect
{'Name': 'preferred_language', 'Value': 'hi'}
```

## Integration with Application

### Environment Variables

Add these to your application configuration:

```bash
# .env file
COGNITO_USER_POOL_ID=ap-south-1_XXXXXXXXX
COGNITO_APP_CLIENT_ID=your-app-client-id
COGNITO_REGION=ap-south-1
```

### Backend Integration

```python
# src/services/auth_service.py
import boto3
from typing import Dict, Optional

class AuthService:
    def __init__(self):
        self.cognito = boto3.client('cognito-idp', region_name='ap-south-1')
        self.user_pool_id = 'ap-south-1_XXXXXXXXX'
        self.client_id = 'your-app-client-id'
    
    def register_user(self, phone_number: str, language: str, location: str) -> Dict:
        """Register new user with phone number"""
        response = self.cognito.sign_up(
            ClientId=self.client_id,
            Username=phone_number,
            UserAttributes=[
                {'Name': 'phone_number', 'Value': phone_number},
                {'Name': 'custom:preferred_language', 'Value': language},
                {'Name': 'custom:location', 'Value': location},
            ]
        )
        return response
    
    def verify_otp(self, phone_number: str, otp_code: str) -> bool:
        """Verify OTP code"""
        try:
            self.cognito.confirm_sign_up(
                ClientId=self.client_id,
                Username=phone_number,
                ConfirmationCode=otp_code
            )
            return True
        except Exception:
            return False
```

### Frontend Integration

```typescript
// src/services/authService.ts
import { CognitoUserPool, CognitoUser, AuthenticationDetails } from 'amazon-cognito-identity-js';

const poolData = {
  UserPoolId: 'ap-south-1_XXXXXXXXX',
  ClientId: 'your-app-client-id'
};

const userPool = new CognitoUserPool(poolData);

export const registerUser = (phoneNumber: string, language: string, location: string) => {
  return new Promise((resolve, reject) => {
    const attributeList = [
      { Name: 'phone_number', Value: phoneNumber },
      { Name: 'custom:preferred_language', Value: language },
      { Name: 'custom:location', Value: location }
    ];
    
    userPool.signUp(phoneNumber, 'temp-password', attributeList, null, (err, result) => {
      if (err) reject(err);
      else resolve(result);
    });
  });
};
```

## Related Requirements

This Cognito setup addresses the following requirements:

- **Requirement 11.1**: Data encryption - TLS 1.3+ for transmission, AES-256 at rest
- **Requirement 11.2**: User consent and RBAC - Phone verification and attribute-based access control
- **Requirement 8.1**: Profile storage - Custom attributes for user preferences

## Next Steps

1. ✅ Create Cognito User Pool with phone number authentication
2. ✅ Configure custom attributes (preferred_language, location)
3. ✅ Set up OTP-based authentication flow
4. ⏳ Implement Lambda triggers for custom authentication logic
5. ⏳ Create API endpoints for registration and authentication
6. ⏳ Integrate with frontend Progressive Web App
7. ⏳ Set up monitoring and alerting
8. ⏳ Implement user profile management endpoints

## References

- [AWS Cognito Documentation](https://docs.aws.amazon.com/cognito/)
- [Cognito User Pools API Reference](https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/)
- [SMS Authentication Best Practices](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-sms-settings.html)
- [Custom Authentication Flow](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-authentication-flow.html)
