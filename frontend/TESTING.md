# Frontend Testing Guide

This guide provides comprehensive testing procedures for the BharatSahayak web interface.

## Test Environment Setup

### Prerequisites

1. Backend infrastructure deployed and running
2. Frontend deployed to S3
3. Sample schemes loaded in DynamoDB
4. Browser with developer tools (Chrome/Firefox recommended)

### Configuration

1. Get configuration values:
   ```bash
   cd frontend
   ./get-config.sh dev
   ```

2. Open the frontend URL in your browser

3. Configure API settings in the web interface

## Test Cases

### Test 1: API Configuration

**Objective:** Verify API configuration can be saved and persisted

**Steps:**
1. Open the frontend URL
2. In "API Configuration" section, enter:
   - API Endpoint (from CloudFormation outputs)
   - User Pool ID (from CloudFormation outputs)
   - Client ID (from CloudFormation outputs)
3. Click "Save Configuration"

**Expected Results:**
- ✅ Success message appears
- ✅ Configuration persists after page reload
- ✅ Values are stored in browser localStorage

**Troubleshooting:**
- If save fails, check browser console for errors
- Verify all fields are filled correctly
- Try clearing browser cache and retry

---

### Test 2: User Registration

**Objective:** Verify new user can register successfully

**Steps:**
1. In "Authentication" section, find "Register New User"
2. Enter phone number (format: +919876543210)
3. Select preferred language (e.g., Hindi)
4. Click "Register"

**Expected Results:**
- ✅ Success message: "Registration successful! Check your phone for OTP"
- ✅ User created in Cognito User Pool
- ✅ User record created in DynamoDB Users table
- ✅ OTP sent (check CloudWatch logs in dev environment)

**Verification:**
```bash
# Check Cognito user
aws cognito-idp list-users \
  --user-pool-id <USER_POOL_ID> \
  --filter "phone_number = \"+919876543210\""

# Check DynamoDB
aws dynamodb scan \
  --table-name bharatsahayak-users-dev \
  --filter-expression "phone_number = :phone" \
  --expression-attribute-values '{":phone":{"S":"+919876543210"}}'
```

**Troubleshooting:**
- If registration fails, check Lambda logs:
  ```bash
  aws logs tail /aws/lambda/bharatsahayak-register-dev --follow
  ```
- Verify Cognito SMS configuration is set up
- Check IAM permissions for Lambda function

---

### Test 3: OTP Verification and Login

**Objective:** Verify user can login with OTP

**Steps:**
1. Get OTP from CloudWatch logs:
   ```bash
   aws logs tail /aws/lambda/bharatsahayak-register-dev --since 5m
   ```
2. In "Login" section, enter:
   - Phone number (same as registration)
   - OTP code
3. Click "Verify & Login"

**Expected Results:**
- ✅ Success message: "Login successful!"
- ✅ Auth info box appears showing logged-in user
- ✅ Profile, Eligibility, and Analytics sections become visible
- ✅ JWT token stored in localStorage

**Verification:**
- Check browser localStorage for 'bharatsahayak-token'
- Verify token is valid JWT format
- Check browser console for no errors

**Troubleshooting:**
- If OTP is invalid, check CloudWatch logs for correct OTP
- Verify OTP hasn't expired (usually 5 minutes)
- Try registering again to get new OTP

---

### Test 4: Profile Management - Update

**Objective:** Verify user can update their profile

**Steps:**
1. Ensure you're logged in
2. In "User Profile" section, fill in:
   - Age: 30
   - Gender: Male
   - Education: Graduate
   - Occupation: Farmer
   - Income: Below 1 Lakh
   - State: Maharashtra
   - District: Pune
   - Pincode: 411001
3. Click "Update Profile"

**Expected Results:**
- ✅ Success message: "Profile updated successfully!"
- ✅ Profile data saved to DynamoDB
- ✅ No errors in browser console

**Verification:**
```bash
# Check DynamoDB profile
aws dynamodb get-item \
  --table-name bharatsahayak-user-profiles-dev \
  --key '{"user_id":{"S":"<USER_ID>"}}'
```

**Troubleshooting:**
- Check Lambda logs for update function
- Verify JWT token is valid
- Check DynamoDB table permissions

---

### Test 5: Profile Management - Load

**Objective:** Verify user can load their saved profile

**Steps:**
1. After updating profile, refresh the page
2. Login again if needed
3. Click "Load Profile" button

**Expected Results:**
- ✅ All previously saved profile fields are populated
- ✅ Success message appears
- ✅ Data matches what was saved

**Troubleshooting:**
- If profile doesn't load, check if update was successful
- Verify user_id in JWT token matches profile record
- Check Lambda logs for get profile function

---

### Test 6: Scheme Search - By Keywords

**Objective:** Verify scheme search works with keywords

**Steps:**
1. In "Search Government Schemes" section
2. Enter search query: "agriculture"
3. Leave category and state empty
4. Click "Search Schemes"

**Expected Results:**
- ✅ Success message showing number of schemes found
- ✅ Scheme cards displayed with relevant information
- ✅ Each card shows: name, category, department, description
- ✅ "View Details" and "Check Eligibility" buttons present

**Verification:**
- Verify schemes are related to agriculture
- Check that scheme data is complete
- Verify no duplicate schemes

**Troubleshooting:**
- If no schemes found, check if schemes are loaded in DynamoDB:
  ```bash
  aws dynamodb scan --table-name bharatsahayak-schemes-dev --select COUNT
  ```
- Load sample schemes if needed:
  ```bash
  cd scripts && python load_schemes.py
  ```

---

### Test 7: Scheme Search - By Category

**Objective:** Verify filtering by category works

**Steps:**
1. Clear search query
2. Select category: "Agriculture"
3. Click "Search Schemes"

**Expected Results:**
- ✅ Only agriculture schemes displayed
- ✅ All results have category = "agriculture"
- ✅ Results count matches filter

**Troubleshooting:**
- Check DynamoDB GSI on category is working
- Verify scheme data has correct category values

---

### Test 8: Scheme Search - Browse All

**Objective:** Verify browsing all schemes works

**Steps:**
1. Click "Browse All" button

**Expected Results:**
- ✅ All schemes in database are displayed
- ✅ Schemes from different categories shown
- ✅ Pagination works if many schemes (future enhancement)

---

### Test 9: View Scheme Details

**Objective:** Verify detailed scheme information can be viewed

**Steps:**
1. Search for schemes
2. Click "View Details" on any scheme card

**Expected Results:**
- ✅ New window/modal opens with full scheme details
- ✅ Details include:
  - Name, category, department, state
  - Description
  - Benefits list
  - Eligibility criteria
  - Required documents
  - Application process
  - Application URL (if available)
- ✅ Information is well-formatted and readable

**Troubleshooting:**
- If popup is blocked, allow popups for the site
- Check if scheme data is complete in DynamoDB

---

### Test 10: Check Eligibility - Single Scheme

**Objective:** Verify eligibility checking for a specific scheme

**Steps:**
1. Ensure profile is filled with test data (age: 30, occupation: Farmer, etc.)
2. Search for schemes
3. Click "Check Eligibility" on a scheme (or enter scheme ID manually)
4. Click "Check Eligibility" button

**Expected Results:**
- ✅ Eligibility result displayed
- ✅ Shows "ELIGIBLE" or "NOT ELIGIBLE" clearly
- ✅ Provides reasoning for decision
- ✅ Lists matched criteria (if eligible)
- ✅ Lists missing criteria (if not eligible)

**Test Cases:**

**Case A: Eligible User**
- Profile: Farmer, age 30, income < 1 Lakh, Maharashtra
- Scheme: PM-KISAN (farmer scheme)
- Expected: ELIGIBLE

**Case B: Not Eligible User**
- Profile: Student, age 20, income < 1 Lakh
- Scheme: PM-KISAN (farmer scheme)
- Expected: NOT ELIGIBLE (occupation mismatch)

**Verification:**
```bash
# Check eligibility logic in Lambda logs
aws logs tail /aws/lambda/bharatsahayak-check-eligibility-dev --follow
```

**Troubleshooting:**
- If eligibility seems wrong, check scheme criteria in DynamoDB
- Verify profile data is complete
- Check eligibility checker logic in Lambda function

---

### Test 11: Get All Eligible Schemes

**Objective:** Verify getting all schemes user is eligible for

**Steps:**
1. Ensure profile is complete
2. In "Check Eligibility" section
3. Click "Get All Eligible Schemes"

**Expected Results:**
- ✅ List of all eligible schemes displayed
- ✅ Each scheme shows why user is eligible
- ✅ Only schemes matching user profile are shown
- ✅ "View Full Details" button works for each scheme

**Test Profiles:**

**Profile 1: Farmer**
- Age: 35, Occupation: Farmer, Income: < 1 Lakh, State: Maharashtra
- Expected: Agriculture schemes, rural schemes, low-income schemes

**Profile 2: Student**
- Age: 20, Occupation: Student, Education: 12th Pass
- Expected: Education schemes, scholarship schemes, skill development

**Profile 3: Senior Citizen**
- Age: 65, Occupation: Retired, Income: < 2 Lakhs
- Expected: Senior citizen schemes, pension schemes, health schemes

**Troubleshooting:**
- If no schemes found, verify profile data is complete
- Check if schemes in database have proper eligibility criteria
- Review eligibility checker logic

---

### Test 12: Analytics - Record Event

**Objective:** Verify events can be recorded

**Steps:**
1. Ensure logged in
2. In "Analytics & Impact Tracking" section
3. Select event type: "Scheme Accessed"
4. Click "Record Event"

**Expected Results:**
- ✅ Success message appears
- ✅ Event recorded in DynamoDB Interactions table

**Verification:**
```bash
# Check interactions table
aws dynamodb scan \
  --table-name bharatsahayak-interactions-dev \
  --limit 10
```

**Troubleshooting:**
- Check Lambda logs for impact event function
- Verify DynamoDB table permissions

---

### Test 13: Analytics - View Metrics

**Objective:** Verify analytics data can be viewed

**Steps:**
1. After recording some events
2. Click "View Analytics"

**Expected Results:**
- ✅ Analytics card displayed with metrics:
  - Total events
  - Unique users
  - Schemes accessed
  - Eligibility checks
- ✅ Recent events list shown
- ✅ Data is anonymized (no PII)

**Verification:**
- Verify metrics match actual usage
- Check that no phone numbers or personal data is shown

**Troubleshooting:**
- If no data shown, record some events first
- Check Lambda logs for analytics function

---

### Test 14: Session Persistence

**Objective:** Verify user session persists across page reloads

**Steps:**
1. Login successfully
2. Refresh the page
3. Check if still logged in

**Expected Results:**
- ✅ User remains logged in after refresh
- ✅ Auth info box still shows user
- ✅ Profile, eligibility, analytics sections still visible
- ✅ Token still valid in localStorage

**Troubleshooting:**
- If logged out, check token expiration
- Verify localStorage is not being cleared
- Check JWT token validity period

---

### Test 15: Logout

**Objective:** Verify logout functionality works

**Steps:**
1. While logged in, click "Logout" button

**Expected Results:**
- ✅ Success message: "Logged out successfully"
- ✅ Auth info box hidden
- ✅ Profile, eligibility, analytics sections hidden
- ✅ Token removed from localStorage
- ✅ User info removed from localStorage

**Troubleshooting:**
- Check browser console for errors
- Verify localStorage is cleared

---

### Test 16: Error Handling - Invalid API Endpoint

**Objective:** Verify error handling for invalid configuration

**Steps:**
1. Configure with invalid API endpoint
2. Try to search schemes

**Expected Results:**
- ✅ Error message displayed
- ✅ User-friendly error description
- ✅ No application crash

---

### Test 17: Error Handling - Unauthorized Access

**Objective:** Verify protected endpoints require authentication

**Steps:**
1. Without logging in, try to update profile or check eligibility

**Expected Results:**
- ✅ Error message: "Please login first"
- ✅ No API call made
- ✅ User prompted to login

---

### Test 18: Mobile Responsiveness

**Objective:** Verify interface works on mobile devices

**Steps:**
1. Open frontend on mobile device or use browser dev tools mobile view
2. Test all features

**Expected Results:**
- ✅ Layout adapts to mobile screen
- ✅ All buttons are clickable
- ✅ Forms are usable
- ✅ Text is readable
- ✅ No horizontal scrolling

---

### Test 19: Browser Compatibility

**Objective:** Verify interface works across browsers

**Browsers to Test:**
- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

**Expected Results:**
- ✅ All features work in all browsers
- ✅ Styling is consistent
- ✅ No JavaScript errors

---

### Test 20: Performance

**Objective:** Verify acceptable performance

**Metrics to Check:**
- Page load time: < 3 seconds
- API response time: < 2 seconds
- Search results display: < 1 second
- No memory leaks after extended use

**Tools:**
- Browser DevTools Network tab
- Browser DevTools Performance tab
- Lighthouse audit

---

## Complete End-to-End Test Flow

This is the complete user journey from start to finish:

### Scenario: Farmer Looking for Agricultural Schemes

**User Profile:**
- Name: Ramesh Kumar
- Phone: +919876543210
- Age: 35
- Gender: Male
- Occupation: Farmer
- Education: 10th Pass
- Income: Below 1 Lakh
- Location: Pune, Maharashtra

**Test Flow:**

1. **Configure API** ✅
   - Enter API endpoint, User Pool ID, Client ID
   - Save configuration

2. **Register** ✅
   - Enter phone number: +919876543210
   - Select language: Hindi
   - Click Register
   - Verify success message

3. **Login** ✅
   - Get OTP from CloudWatch logs
   - Enter phone and OTP
   - Click Verify & Login
   - Verify logged in

4. **Update Profile** ✅
   - Fill in all profile fields
   - Click Update Profile
   - Verify success

5. **Search Schemes** ✅
   - Search for "agriculture"
   - View results
   - Click "View Details" on PM-KISAN
   - Review scheme information

6. **Check Eligibility** ✅
   - From search results, click "Check Eligibility" on PM-KISAN
   - Verify ELIGIBLE result
   - Review reasoning

7. **Get All Eligible Schemes** ✅
   - Click "Get All Eligible Schemes"
   - Review list of eligible schemes
   - Verify all are relevant to farmer profile

8. **Record Analytics** ✅
   - Record "Scheme Accessed" event
   - Record "Eligibility Checked" event
   - View analytics
   - Verify metrics updated

9. **Logout** ✅
   - Click Logout
   - Verify logged out

**Expected Duration:** 10-15 minutes

**Success Criteria:**
- All steps complete without errors
- Data persists correctly
- Eligibility results are accurate
- Analytics are recorded

---

## Automated Testing Script

For automated testing, see `test-frontend.js` (to be created with Selenium/Playwright)

---

## Test Results Template

Use this template to document test results:

```
Test Date: YYYY-MM-DD
Tester: [Name]
Environment: [dev/staging/prod]
Browser: [Chrome/Firefox/Safari/Edge]
Device: [Desktop/Mobile]

Test Results:
- Test 1: API Configuration - [PASS/FAIL]
- Test 2: User Registration - [PASS/FAIL]
- Test 3: OTP Verification - [PASS/FAIL]
- Test 4: Profile Update - [PASS/FAIL]
- Test 5: Profile Load - [PASS/FAIL]
- Test 6: Scheme Search - [PASS/FAIL]
- Test 7: Category Filter - [PASS/FAIL]
- Test 8: Browse All - [PASS/FAIL]
- Test 9: View Details - [PASS/FAIL]
- Test 10: Check Eligibility - [PASS/FAIL]
- Test 11: All Eligible Schemes - [PASS/FAIL]
- Test 12: Record Event - [PASS/FAIL]
- Test 13: View Analytics - [PASS/FAIL]
- Test 14: Session Persistence - [PASS/FAIL]
- Test 15: Logout - [PASS/FAIL]

Issues Found:
1. [Description]
2. [Description]

Overall Result: [PASS/FAIL]
```

---

## Reporting Issues

When reporting issues, include:
1. Test case number and name
2. Steps to reproduce
3. Expected vs actual result
4. Browser and device information
5. Screenshots or screen recordings
6. Browser console errors
7. Network tab information
8. CloudWatch logs (if applicable)

---

## Next Steps After Testing

1. Document all test results
2. Fix any issues found
3. Retest failed cases
4. Get user feedback
5. Iterate on improvements
6. Prepare for production deployment
