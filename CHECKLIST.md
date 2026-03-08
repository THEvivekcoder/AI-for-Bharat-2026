# BharatSahayak - Deployment Checklist

## 📋 Pre-Deployment Checklist

### One-Time Setup
- [ ] AWS CLI installed (`aws --version`)
- [ ] SAM CLI installed (`sam --version`)
- [ ] Python 3.11 installed (`python --version`)
- [ ] AWS credentials configured (`aws sts get-caller-identity`)
- [ ] Project dependencies installed (`make install`)

### Pre-Deployment Tasks
- [ ] All unit tests passing (`make test-unit`)
- [ ] Code coverage acceptable (`make coverage`)
- [ ] JWT secret created (`python scripts/pre_deployment_setup.py`)
- [ ] OpenSearch decision made (keep or disable in template.yaml)
- [ ] SAM template validated (`sam validate`)

---

## 🚀 Deployment Checklist

### Build Phase
- [ ] SAM build successful (`sam build`)
- [ ] No build errors in output
- [ ] All Lambda packages created

### Deploy Phase
- [ ] SAM deploy started (`sam deploy --guided`)
- [ ] Stack name: bharatsahayak-stack
- [ ] Region: ap-south-1
- [ ] Environment: dev
- [ ] IAM role creation confirmed
- [ ] Changeset reviewed and confirmed
- [ ] Deployment completed successfully
- [ ] No errors in CloudFormation events

### Post-Deployment Phase
- [ ] CloudFormation outputs retrieved
- [ ] Frontend config updated (`python scripts/post_deployment_config.py`)
- [ ] Sample data loaded (`python scripts/load_schemes.py`)
- [ ] Frontend deployed to S3 (`make deploy-frontend`)

---

## 🧪 Testing Checklist

### API Testing
- [ ] API endpoint accessible
- [ ] Scheme search works (`curl API_URL/schemes`)
- [ ] Scheme details works (`curl API_URL/schemes/PM-KISAN-2024`)
- [ ] No CORS errors
- [ ] Response format correct (JSON)

### Frontend Testing
- [ ] Frontend URL accessible
- [ ] Configuration page loads
- [ ] API URL pre-filled correctly
- [ ] User Pool ID pre-filled correctly
- [ ] Client ID pre-filled correctly

### Authentication Testing
- [ ] User registration form works
- [ ] Phone number validation works
- [ ] OTP sent successfully (if SMS configured)
- [ ] OTP verification works
- [ ] JWT token generated
- [ ] Token stored in localStorage

### Profile Testing
- [ ] Profile form loads
- [ ] Profile data can be entered
- [ ] Profile saves to DynamoDB
- [ ] Profile retrieval works
- [ ] Profile updates work

### Scheme Testing
- [ ] Scheme search works
- [ ] Category filter works
- [ ] State filter works
- [ ] Keyword search works
- [ ] Scheme details display correctly
- [ ] All 8 sample schemes visible

### Eligibility Testing
- [ ] Eligibility check form works
- [ ] Single scheme eligibility check works
- [ ] Bulk eligibility check works
- [ ] Results display correctly
- [ ] Reasoning provided
- [ ] Missing criteria shown

### Analytics Testing
- [ ] Event recording works
- [ ] Analytics dashboard loads
- [ ] Metrics display correctly
- [ ] User data anonymized

---

## 🔍 Verification Checklist

### AWS Resources Created
- [ ] 10 DynamoDB tables exist
- [ ] 3 S3 buckets exist
- [ ] 1 Cognito User Pool exists
- [ ] 25 Lambda functions deployed
- [ ] 1 API Gateway created
- [ ] IAM roles created
- [ ] CloudWatch log groups created

### Data Verification
- [ ] 8 schemes loaded in DynamoDB
- [ ] Schemes table has data
- [ ] Users table exists (empty initially)
- [ ] Profiles table exists (empty initially)
- [ ] Interactions table exists (empty initially)

### Security Verification
- [ ] JWT secret exists in Secrets Manager
- [ ] API Gateway has CORS configured
- [ ] Cognito authentication working
- [ ] Lambda functions have proper IAM roles
- [ ] S3 buckets have appropriate policies

---

## 🐛 Bug Fix Checklist

### Critical Bugs (Must Fix Before Deployment)
- [ ] Bug #1: JWT secret created in Secrets Manager

### High Priority Bugs (Should Fix)
- [ ] Bug #3: OpenSearch disabled or budget confirmed

### Medium Priority Bugs (Can Fix Post-Deployment)
- [ ] Bug #2: Integration test mocking fixed
- [ ] Bug #5: Frontend config updated (automated by script)
- [ ] Bug #6: SNS spending limit increased (if using SMS)

### Low Priority Bugs (Fix Later)
- [ ] Bug #4: Property test collection errors fixed

---

## 💰 Cost Checklist

### Before Deployment
- [ ] Reviewed cost estimation
- [ ] Decided on OpenSearch (keep or disable)
- [ ] Understood monthly costs
- [ ] Budget approved

### After Deployment
- [ ] AWS billing alerts configured
- [ ] Cost Explorer reviewed
- [ ] Free tier usage monitored
- [ ] Unnecessary resources cleaned up

---

## 📚 Documentation Checklist

### Read Before Deployment
- [ ] DEPLOYMENT_CHECKLIST.md (complete guide)
- [ ] BUGS_AND_FIXES.md (bug analysis)
- [ ] MANUAL_STEPS_REQUIRED.md (what's manual)

### Reference During Deployment
- [ ] QUICK_START.md (quick commands)
- [ ] Makefile (automation commands)
- [ ] DEPLOYMENT_SUMMARY.txt (this file)

### Review After Deployment
- [ ] PROJECT_STATUS.md (status report)
- [ ] README.md (project overview)
- [ ] docs/ folder (API documentation)

---

## ✅ Success Criteria

Deployment is successful when ALL of these are true:

### Backend Success
- [ ] CloudFormation stack status: CREATE_COMPLETE or UPDATE_COMPLETE
- [ ] All Lambda functions deployed
- [ ] API Gateway returns 200 for /schemes endpoint
- [ ] DynamoDB tables contain data
- [ ] No errors in CloudWatch logs

### Frontend Success
- [ ] Frontend loads in browser
- [ ] No JavaScript errors in console
- [ ] Configuration saves successfully
- [ ] API calls work from frontend

### End-to-End Success
- [ ] Can register new user
- [ ] Can verify OTP (if SMS configured)
- [ ] Can update profile
- [ ] Can search schemes
- [ ] Can check eligibility
- [ ] Can view analytics

---

## 🎯 Quick Reference

### Essential Commands
```bash
# Pre-deployment
python scripts/pre_deployment_setup.py

# Deployment
sam build && sam deploy --guided

# Post-deployment
python scripts/post_deployment_config.py
python scripts/load_schemes.py
make deploy-frontend

# Testing
curl https://YOUR_API_ID.execute-api.ap-south-1.amazonaws.com/dev/schemes
```

### Essential Files to Edit
1. template.yaml - Comment out OpenSearch (lines 1000-1200) if disabling
2. frontend/app.js - Auto-updated by post_deployment_config.py

### Essential URLs
- Frontend: http://bharatsahayak-frontend-dev.s3-website.ap-south-1.amazonaws.com
- API: https://YOUR_API_ID.execute-api.ap-south-1.amazonaws.com/dev
- AWS Console: https://console.aws.amazon.com

---

## 🆘 Troubleshooting Checklist

If deployment fails:
- [ ] Check AWS credentials: `aws sts get-caller-identity`
- [ ] Check JWT secret exists: `aws secretsmanager describe-secret --secret-id bharatsahayak-jwt-secret-dev`
- [ ] Check CloudFormation events: `aws cloudformation describe-stack-events --stack-name bharatsahayak-stack`
- [ ] Check Lambda logs: `sam logs -n RegisterFunction --tail`
- [ ] Validate template: `sam validate`

If tests fail:
- [ ] Install dependencies: `make install`
- [ ] Check Python version: `python --version`
- [ ] Run specific test: `python -m pytest tests/unit/test_eligibility_checker.py -v`

If frontend doesn't work:
- [ ] Check API URL in app.js
- [ ] Check browser console for errors
- [ ] Verify CORS configuration
- [ ] Test API directly with curl

---

## 📊 Progress Tracking

### Phase 1: Setup (One-Time)
- [ ] Tools installed
- [ ] Credentials configured
- [ ] Dependencies installed
- [ ] Tests passing locally

### Phase 2: Pre-Deployment
- [ ] Pre-deployment script run
- [ ] JWT secret created
- [ ] OpenSearch decision made
- [ ] Template validated

### Phase 3: Deployment
- [ ] SAM build completed
- [ ] SAM deploy completed
- [ ] No CloudFormation errors
- [ ] All resources created

### Phase 4: Post-Deployment
- [ ] Post-deployment script run
- [ ] Frontend config updated
- [ ] Sample data loaded
- [ ] Frontend deployed

### Phase 5: Validation
- [ ] API tested
- [ ] Frontend tested
- [ ] End-to-end flow tested
- [ ] All features working

---

## 🎉 Completion Checklist

You're done when:
- [ ] All checkboxes above are checked ✅
- [ ] Frontend loads without errors
- [ ] Can search for schemes
- [ ] Can check eligibility
- [ ] Data persists in DynamoDB
- [ ] No critical errors in logs

---

**Last Updated:** March 7, 2026
**Project:** BharatSahayak
**Status:** Ready for Deployment
**Estimated Time:** 30 minutes (first time), 7 minutes (updates)

================================================================================
                    PRINT THIS AND CHECK OFF AS YOU GO!
================================================================================
