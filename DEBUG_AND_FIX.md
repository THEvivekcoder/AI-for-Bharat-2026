# Debug and Fix Guide

## Issues Reported
1. OTP authentication not working
2. Voice assistant not working
3. Schemes options not working
4. Many more options not working

## Root Cause Analysis

The main issue is likely:
1. **API client not initializing** - Scripts loading in wrong order
2. **API endpoint not configured** - config.json missing or incorrect
3. **CORS issues** - Backend not allowing frontend domain
4. **Network errors** - Backend not reachable

## Quick Fixes

### Fix 1: Ensure API Client Loads First

The api-client.js must load BEFORE any page scripts. Current issue: it's in `<head>` but page scripts run immediately.

**Solution:** Move api-client.js to load before inline scripts.

### Fix 2: Check API Configuration

Open browser console and run:
```javascript
// Check if API client exists
console.log('API exists:', typeof api !== 'undefined');
console.log('API initialized:', api?.initialized);
console.log('API endpoint:', api?.config?.apiEndpoint);
```

If API doesn't exist or isn't initialized, the scripts are loading in wrong order.

### Fix 3: Test API Endpoint

```javascript
// Test if backend is reachable
fetch('https://dvt82zj0c4.execute-api.ap-south-1.amazonaws.com/dev/health-check')
  .then(r => r.json())
  .then(d => console.log('Backend response:', d))
  .catch(e => console.error('Backend error:', e));
```

### Fix 4: Check for JavaScript Errors

Open Developer Tools (F12) → Console tab
Look for:
- "api is not defined"
- "Cannot read property of undefined"
- CORS errors
- Network errors

## Immediate Actions

### Action 1: Create Test Page

I'll create a simple test page that checks everything.

### Action 2: Fix Script Loading Order

Ensure api-client.js loads and initializes before page scripts run.

### Action 3: Add Fallback for Missing API

If API client fails to load, show user-friendly error.

## Testing Checklist

1. ☐ Open login.html
2. ☐ Open browser console (F12)
3. ☐ Check for errors
4. ☐ Try to send OTP
5. ☐ Check Network tab for API calls
6. ☐ Verify API endpoint is correct
7. ☐ Check if CORS is enabled on backend

## Common Errors and Solutions

### Error: "api is not defined"
**Cause:** api-client.js not loaded
**Fix:** Ensure `<script src="api-client.js"></script>` is present and loads first

### Error: "API not initialized"
**Cause:** Page script runs before API client initializes
**Fix:** Wrap code in `window.addEventListener('api-ready', function() { ... })`

### Error: "Network request failed"
**Cause:** Backend not reachable or CORS issue
**Fix:** 
1. Check backend is running
2. Verify API endpoint URL
3. Enable CORS on backend

### Error: "Failed to fetch"
**Cause:** CORS or network issue
**Fix:** Backend must allow requests from frontend domain

## Next Steps

1. Create comprehensive test page
2. Fix script loading order in all pages
3. Add better error messages
4. Test each page systematically
