# BharatSahayak Frontend Test Checklist

Quick checklist for testing the complete user flow end-to-end.

## Pre-Test Setup

- [ ] Backend infrastructure deployed
- [ ] Frontend deployed to S3
- [ ] Sample schemes loaded in DynamoDB
- [ ] Configuration values retrieved (API endpoint, User Pool ID, Client ID)
- [ ] Browser with developer tools open

## Test Execution

### 1. Configuration
- [ ] Open frontend URL
- [ ] Enter API endpoint
- [ ] Enter User Pool ID
- [ ] Enter Client ID
- [ ] Click "Save Configuration"
- [ ] Verify success message
- [ ] Refresh page and verify config persists

### 2. User Registration
- [ ] Enter phone number (format: +919876543210)
- [ ] Select language
- [ ] Click "Register"
- [ ] Verify success message
- [ ] Check CloudWatch logs for OTP

### 3. Authentication
- [ ] Copy OTP from CloudWatch logs
- [ ] Enter phone number
- [ ] Enter OTP
- [ ] Click "Verify & Login"
- [ ] Verify success message
- [ ] Verify auth info box appears
- [ ] Verify profile/eligibility/analytics sections appear

### 4. Profile Management
- [ ] Fill in age: 30
- [ ] Select gender: Male
- [ ] Enter education: Graduate
- [ ] Enter occupation: Farmer
- [ ] Enter income: Below 1 Lakh
- [ ] Enter state: Maharashtra
- [ ] Enter district: Pune
- [ ] Enter pincode: 411001
- [ ] Click "Update Profile"
- [ ] Verify success message
- [ ] Click "Load Profile"
- [ ] Verify all fields populated correctly

### 5. Scheme Search
- [ ] Enter search query: "agriculture"
- [ ] Click "Search Schemes"
- [ ] Verify schemes displayed
- [ ] Verify scheme cards show: name, category, department, description
- [ ] Click "View Details" on a scheme
- [ ] Verify detailed information displayed
- [ ] Close details window

### 6. Category Filter
- [ ] Clear search query
- [ ] Select category: "Agriculture"
- [ ] Click "Search Schemes"
- [ ] Verify only agriculture schemes shown

### 7. Browse All
- [ ] Click "Browse All"
- [ ] Verify all schemes displayed
- [ ] Verify schemes from different categories

### 8. Check Single Scheme Eligibility
- [ ] From search results, click "Check Eligibility" on a scheme
- [ ] Verify scheme ID populated
- [ ] Click "Check Eligibility"
- [ ] Verify eligibility result displayed
- [ ] Verify reasoning provided
- [ ] Verify matched/missing criteria shown

### 9. Get All Eligible Schemes
- [ ] Click "Get All Eligible Schemes"
- [ ] Verify list of eligible schemes displayed
- [ ] Verify each shows eligibility reasoning
- [ ] Click "View Full Details" on one scheme
- [ ] Verify details displayed

### 10. Analytics - Record Event
- [ ] Select event type: "Scheme Accessed"
- [ ] Click "Record Event"
- [ ] Verify success message

### 11. Analytics - View Metrics
- [ ] Click "View Analytics"
- [ ] Verify metrics displayed:
  - [ ] Total events
  - [ ] Unique users
  - [ ] Schemes accessed
  - [ ] Eligibility checks
- [ ] Verify recent events list shown
- [ ] Verify no PII displayed

### 12. Session Persistence
- [ ] Refresh the page
- [ ] Verify still logged in
- [ ] Verify profile data still available

### 13. Logout
- [ ] Click "Logout"
- [ ] Verify success message
- [ ] Verify auth info hidden
- [ ] Verify profile/eligibility/analytics sections hidden

### 14. Error Handling
- [ ] Try to check eligibility without logging in
- [ ] Verify error message: "Please login first"
- [ ] Try to update profile without logging in
- [ ] Verify error message displayed

### 15. Mobile Responsiveness (Optional)
- [ ] Open in mobile view (DevTools)
- [ ] Verify layout adapts
- [ ] Verify all buttons clickable
- [ ] Verify forms usable

## Test Results

**Date:** _______________
**Tester:** _______________
**Environment:** _______________
**Browser:** _______________

**Overall Result:** [ ] PASS  [ ] FAIL

**Issues Found:**
1. _______________________________________________
2. _______________________________________________
3. _______________________________________________

**Notes:**
_____________________________________________________
_____________________________________________________
_____________________________________________________

## Sign-off

**Tested by:** _______________  **Date:** _______________
**Reviewed by:** _______________  **Date:** _______________

---

## Quick Commands Reference

### Get Configuration
```bash
cd frontend
./get-config.sh dev
```

### Deploy Frontend
```bash
cd frontend
./deploy.sh dev
```

### View Lambda Logs (for OTP)
```bash
aws logs tail /aws/lambda/bharatsahayak-register-dev --follow
```

### Check Schemes Count
```bash
aws dynamodb scan --table-name bharatsahayak-schemes-dev --select COUNT
```

### Load Sample Schemes
```bash
cd scripts
python load_schemes.py
```

### Check User in Cognito
```bash
aws cognito-idp list-users --user-pool-id <USER_POOL_ID>
```

### Check DynamoDB Tables
```bash
# Users
aws dynamodb scan --table-name bharatsahayak-users-dev --limit 5

# Profiles
aws dynamodb scan --table-name bharatsahayak-user-profiles-dev --limit 5

# Schemes
aws dynamodb scan --table-name bharatsahayak-schemes-dev --limit 5

# Interactions
aws dynamodb scan --table-name bharatsahayak-interactions-dev --limit 5
```

---

## Common Issues and Solutions

### Issue: "Please configure API endpoint first"
**Solution:** Save configuration with valid values

### Issue: "Failed to fetch"
**Solution:** Check API Gateway CORS, verify endpoint URL

### Issue: OTP not received
**Solution:** Check CloudWatch logs for OTP code

### Issue: "Authentication failed"
**Solution:** Verify OTP is correct and not expired

### Issue: No schemes found
**Solution:** Load sample schemes into DynamoDB

### Issue: Eligibility check fails
**Solution:** Ensure profile is complete, check Lambda logs

---

## Success Criteria

All tests must pass for successful completion:
- ✅ Configuration saves and persists
- ✅ User can register and login
- ✅ Profile can be updated and loaded
- ✅ Schemes can be searched and filtered
- ✅ Scheme details can be viewed
- ✅ Eligibility checking works correctly
- ✅ All eligible schemes can be retrieved
- ✅ Analytics events can be recorded
- ✅ Analytics metrics can be viewed
- ✅ Session persists across page reloads
- ✅ Logout works correctly
- ✅ Error handling works properly
- ✅ No console errors
- ✅ No broken functionality
