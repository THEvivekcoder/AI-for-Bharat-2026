# 🏗️ System Architecture - BharatSahayak

## Complete System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER DEVICES                            │
│                  (Browser / Mobile Browser)                     │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ HTTPS
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FRONTEND (Static)                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  HTML Pages:                                             │  │
│  │  • login.html          • dashboard.html                  │  │
│  │  • schemes.html        • voice-assistant.html            │  │
│  │  • profile.html        • agriculture.html                │  │
│  │  • eligible-schemes.html • scheme-details.html           │  │
│  │  • profile-setup.html  • settings.html                   │  │
│  │  • test-quick.html     • debug-test.html                 │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  JavaScript:                                             │  │
│  │  • api-client.js (Centralized API communication)         │  │
│  │  • app.js (Common utilities)                             │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Configuration:                                          │  │
│  │  • config.json (API endpoint, settings)                  │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ REST API (HTTPS)
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AWS API GATEWAY                              │
│  Endpoint: dvt82zj0c4.execute-api.ap-south-1.amazonaws.com/dev  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Routes:                                                 │  │
│  │  POST   /auth/register                                   │  │
│  │  POST   /auth/login          ← NEW                       │  │
│  │  POST   /auth/verify                                     │  │
│  │  GET    /schemes                                         │  │
│  │  GET    /schemes/search                                  │  │
│  │  GET    /schemes/{id}                                    │  │
│  │  GET    /schemes/eligible                                │  │
│  │  POST   /schemes/check-eligibility                       │  │
│  │  GET    /user/profile                                    │  │
│  │  PUT    /user/profile                                    │  │
│  │  GET    /user/stats                                      │  │
│  │  POST   /voice-to-text                                   │  │
│  │  POST   /conversational-query                            │  │
│  │  GET    /crop-advice                                     │  │
│  │  GET    /market-prices                                   │  │
│  │  GET    /health-check        ← NEW                       │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Features:                                               │  │
│  │  • CORS enabled                                          │  │
│  │  • Throttling (optional)                                 │  │
│  │  • Caching (optional)                                    │  │
│  │  • WAF (optional)                                        │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ Invoke
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AWS LAMBDA FUNCTIONS                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Authentication:                                         │  │
│  │  • auth_register.py    - Register new user               │  │
│  │  • auth_login.py       - Login existing user ← NEW       │  │
│  │  • auth_verify.py      - Verify OTP                      │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Schemes:                                                │  │
│  │  • schemes_search.py   - Search/list schemes             │  │
│  │  • scheme_details.py   - Get scheme details              │  │
│  │  • eligible_schemes.py - Get eligible schemes            │  │
│  │  • check_eligibility.py - Check eligibility              │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  User:                                                   │  │
│  │  • user_profile_get.py - Get user profile                │  │
│  │  • user_profile_update.py - Update profile               │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Voice:                                                  │  │
│  │  • voice_to_text.py    - Voice to text conversion        │  │
│  │  • conversational_query.py - AI conversational query     │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Agriculture:                                            │  │
│  │  • crop_advice.py      - Get crop advice                 │  │
│  │  • market_price.py     - Get market prices               │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Monitoring:                                             │  │
│  │  • health_check.py     - Health monitoring ← NEW         │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ Access
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AWS SERVICES                               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  AWS Cognito (Authentication)                            │  │
│  │  • User Pool: ap-south-1_KSJ0FKz20                       │  │
│  │  • Client ID: 10emq71eioca5qkns6on0l22om                 │  │
│  │  • Features: OTP via SMS, JWT tokens                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  DynamoDB (Database)                                     │  │
│  │  • bharatsahayak-users-dev                               │  │
│  │  • bharatsahayak-user-profiles-dev                       │  │
│  │  • bharatsahayak-schemes-dev                             │  │
│  │  • bharatsahayak-conversations-dev                       │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  AWS SNS (SMS Service)                                   │  │
│  │  • OTP delivery via SMS                                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  CloudWatch (Monitoring)                                 │  │
│  │  • Logs: Lambda execution logs                           │  │
│  │  • Metrics: Invocations, errors, duration                │  │
│  │  • Alarms: Error rate, throttles                         │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Authentication Flow

### Registration (New Users)

```
User                Frontend            API Gateway         Lambda              Cognito         DynamoDB
 │                     │                     │                 │                   │               │
 │  Fill Form          │                     │                 │                   │               │
 ├────────────────────>│                     │                 │                   │               │
 │                     │  POST /auth/register│                 │                   │               │
 │                     ├────────────────────>│                 │                   │               │
 │                     │                     │  Invoke         │                   │               │
 │                     │                     ├────────────────>│                   │               │
 │                     │                     │                 │  Create User      │               │
 │                     │                     │                 ├──────────────────>│               │
 │                     │                     │                 │  Send OTP         │               │
 │                     │                     │                 │<──────────────────┤               │
 │                     │                     │                 │  Save Profile     │               │
 │                     │                     │                 ├──────────────────────────────────>│
 │                     │  Response (session) │                 │                   │               │
 │                     │<────────────────────┤<────────────────┤                   │               │
 │  OTP Sent           │                     │                 │                   │               │
 │<────────────────────┤                     │                 │                   │               │
 │                     │                     │                 │                   │               │
 │  Enter OTP          │                     │                 │                   │               │
 ├────────────────────>│                     │                 │                   │               │
 │                     │  POST /auth/verify  │                 │                   │               │
 │                     ├────────────────────>│                 │                   │               │
 │                     │                     │  Invoke         │                   │               │
 │                     │                     ├────────────────>│                   │               │
 │                     │                     │                 │  Verify OTP       │               │
 │                     │                     │                 ├──────────────────>│               │
 │                     │                     │                 │  JWT Token        │               │
 │                     │                     │                 │<──────────────────┤               │
 │                     │  Response (token)   │                 │                   │               │
 │                     │<────────────────────┤<────────────────┤                   │               │
 │  Logged In          │                     │                 │                   │               │
 │<────────────────────┤                     │                 │                   │               │
```

### Login (Existing Users) - NEW

```
User                Frontend            API Gateway         Lambda              Cognito         DynamoDB
 │                     │                     │                 │                   │               │
 │  Enter Phone        │                     │                 │                   │               │
 ├────────────────────>│                     │                 │                   │               │
 │                     │  POST /auth/login   │                 │                   │               │
 │                     ├────────────────────>│                 │                   │               │
 │                     │                     │  Invoke         │                   │               │
 │                     │                     ├────────────────>│                   │               │
 │                     │                     │                 │  Check User       │               │
 │                     │                     │                 ├──────────────────────────────────>│
 │                     │                     │                 │  User Exists      │               │
 │                     │                     │                 │<──────────────────────────────────┤
 │                     │                     │                 │  Initiate Auth    │               │
 │                     │                     │                 ├──────────────────>│               │
 │                     │                     │                 │  Send OTP         │               │
 │                     │                     │                 │<──────────────────┤               │
 │                     │  Response (session) │                 │                   │               │
 │                     │<────────────────────┤<────────────────┤                   │               │
 │  OTP Sent           │                     │                 │                   │               │
 │<────────────────────┤                     │                 │                   │               │
 │                     │                     │                 │                   │               │
 │  Enter OTP          │                     │                 │                   │               │
 ├────────────────────>│                     │                 │                   │               │
 │                     │  POST /auth/verify  │                 │                   │               │
 │                     ├────────────────────>│                 │                   │               │
 │                     │                     │  Invoke         │                   │               │
 │                     │                     ├────────────────>│                   │               │
 │                     │                     │                 │  Verify OTP       │               │
 │                     │                     │                 ├──────────────────>│               │
 │                     │                     │                 │  JWT Token        │               │
 │                     │                     │                 │<──────────────────┤               │
 │                     │  Response (token)   │                 │                   │               │
 │                     │<────────────────────┤<────────────────┤                   │               │
 │  Logged In          │                     │                 │                   │               │
 │<────────────────────┤                     │                 │                   │               │
```

## Data Flow

### Schemes Search

```
User → Frontend → API Gateway → Lambda → DynamoDB
                                   ↓
                              Process & Filter
                                   ↓
User ← Frontend ← API Gateway ← Lambda
```

### Voice Assistant

```
User (Voice) → Frontend → API Gateway → Lambda → AI Service
                                          ↓
                                    Process Response
                                          ↓
User (Text/Voice) ← Frontend ← API Gateway ← Lambda
```

## Security Layers

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: HTTPS (Transport Security)                       │
│  • All communication encrypted                              │
│  • TLS 1.2+                                                 │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: CORS (Cross-Origin Security)                     │
│  • Configured origins                                       │
│  • Allowed methods and headers                              │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: API Gateway (Request Validation)                 │
│  • Throttling                                               │
│  • Request validation                                       │
│  • WAF rules (optional)                                     │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 4: JWT Authentication (User Identity)               │
│  • Token validation                                         │
│  • Expiration check                                         │
│  • User authorization                                       │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 5: IAM (Service Permissions)                        │
│  • Lambda execution role                                    │
│  • Service-to-service auth                                  │
│  • Least privilege principle                                │
└─────────────────────────────────────────────────────────────┘
```

## Monitoring & Logging

```
┌─────────────────────────────────────────────────────────────┐
│                    CloudWatch Logs                          │
│  • Lambda execution logs                                    │
│  • API Gateway access logs                                  │
│  • Error logs                                               │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                   CloudWatch Metrics                        │
│  • Invocations                                              │
│  • Errors                                                   │
│  • Duration                                                 │
│  • Throttles                                                │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                   CloudWatch Alarms                         │
│  • Error rate > 5%                                          │
│  • Duration > 3000ms                                        │
│  • Throttles > 0                                            │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                    SNS Notifications                        │
│  • Email alerts                                             │
│  • SMS alerts                                               │
│  • Slack/Teams integration                                  │
└─────────────────────────────────────────────────────────────┘
```

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Development                              │
│  • Stage: dev                                               │
│  • CORS: Allow all (*)                                      │
│  • Logging: Verbose                                         │
│  • Cost: ~$5/month                                          │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                     Staging                                 │
│  • Stage: staging                                           │
│  • CORS: Restricted                                         │
│  • Logging: Standard                                        │
│  • Cost: ~$20/month                                         │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                    Production                               │
│  • Stage: prod                                              │
│  • CORS: Specific domain                                    │
│  • Logging: Optimized                                       │
│  • WAF: Enabled                                             │
│  • Caching: Enabled                                         │
│  • Cost: ~$47/month (10K users)                             │
└─────────────────────────────────────────────────────────────┘
```

## Summary

**Frontend**: Static HTML/JS hosted on web server  
**Backend**: Serverless AWS Lambda functions  
**API**: AWS API Gateway with REST endpoints  
**Auth**: AWS Cognito with OTP via SMS  
**Database**: DynamoDB (NoSQL)  
**Monitoring**: CloudWatch Logs, Metrics, Alarms  

**New Additions**:
- `/auth/login` endpoint for existing users
- `/health-check` endpoint for monitoring

**Status**: Complete and ready to deploy! 🚀
