# Testing Guide - BharatSahayak Modern UI

## Quick Start Testing

### Step 1: Start Local Server

```bash
cd modern-ui
node server.js
```

Open browser: http://localhost:3000

---

## Test Scenarios

### Scenario 1: Guest User Flow (Fastest)

1. **Landing Page**
   - Open http://localhost:3000
   - Click "Try as Guest" button
   - ✅ Should redirect to dashboard immediately

2. **Dashboard**
   - ✅ Should see "Welcome back, Guest User!"
   - ✅ Should see 3,400+ schemes in "Eligible Schemes"
   - ✅ Should see 6 recommended scheme cards
   - ✅ Click any scheme card → should open details page

3. **Search**
   - Click "Search Schemes" in sidebar
   - ✅ Should see all schemes loaded
   - Type "education" in search box
   - ✅ Should filter to education schemes only
   - Change category filter to "Health"
   - ✅ Should show only health schemes

4. **Scheme Details**
   - Click "View Details" on any scheme
   - ✅ Should show full scheme information
   - Click "☆ Save Scheme" button
   - ✅ Should change to "⭐ Saved"
   - ✅ Should show success alert

5. **Saved Schemes**
   - Click "Saved Schemes" in sidebar
   - ✅ Should show the scheme you just saved
   - ✅ Saved count should be "1"

6. **Logout**
   - Click "Logout" in sidebar
   - ✅ Should redirect to landing page
   - ✅ Session should be cleared

**Expected Time**: 2-3 minutes

---

### Scenario 2: Registration Flow (Demo Mode)

1. **Landing Page**
   - Open http://localhost:3000
   - Click "Get Started" or "Sign Up"

2. **Registration**
   - ✅ Should see "Demo Mode Active" banner
   - Fill in form:
     - Full Name: "Test User"
     - Phone: "+919876543210"
     - Email: "test@example.com"
     - Password: "password123"
     - Confirm Password: "password123"
   - Check "I agree to terms"
   - Click "Create Account"
   - ✅ Should show success message
   - ✅ Should redirect to profile setup

3. **Profile Setup**
   - Fill in profile:
     - Name: "Test User"
     - State: "Maharashtra"
     - District: "Mumbai"
     - Language: "English"
     - Interests: Check "Education" and "Health"
   - Click "Complete Setup"
   - ✅ Should redirect to dashboard

4. **Dashboard**
   - ✅ Should see "Welcome back, Test User!"
   - ✅ All features should work as in Scenario 1

**Expected Time**: 3-4 minutes

---

### Scenario 3: Login Flow (Demo Mode)

1. **Landing Page**
   - Open http://localhost:3000
   - Click "Login"

2. **Login**
   - ✅ Should see "Demo Mode Active" banner
   - Enter credentials:
     - Email: "test@example.com"
     - Password: "password123"
   - Click "Login"
   - ✅ Should redirect to dashboard (or profile setup if first time)

**Expected Time**: 1 minute

---

## Feature Testing Checklist

### Navigation
- [ ] Landing page loads correctly
- [ ] All navbar links work
- [ ] Sidebar navigation works
- [ ] Mobile hamburger menu works
- [ ] Back buttons work
- [ ] Logout works

### Search & Filters
- [ ] Search input filters schemes
- [ ] Category filter works
- [ ] Level filter (Central/State) works
- [ ] State filter works
- [ ] Reset filters button works
- [ ] Results count updates correctly

### Scheme Cards
- [ ] Scheme cards display correctly
- [ ] Category badges show correct colors
- [ ] Hover effects work
- [ ] Click opens details page
- [ ] Truncated text shows "..."

### Scheme Details
- [ ] All scheme information displays
- [ ] Save button works
- [ ] Save button toggles state
- [ ] Share button works
- [ ] Apply button shows message
- [ ] Back button works

### Saved Schemes
- [ ] Saved schemes list displays
- [ ] Empty state shows when no saves
- [ ] Saved count is accurate
- [ ] Clicking scheme opens details
- [ ] Unsaving updates the list

### Authentication
- [ ] Registration form validation works
- [ ] Password matching validation works
- [ ] Login form works
- [ ] Guest login works
- [ ] Session persists on refresh
- [ ] Logout clears session

### Responsive Design
- [ ] Works on desktop (1920x1080)
- [ ] Works on tablet (768x1024)
- [ ] Works on mobile (375x667)
- [ ] Sidebar collapses on mobile
- [ ] Touch interactions work

---

## Browser Testing

Test in multiple browsers:

- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)
- [ ] Mobile Safari (iOS)
- [ ] Chrome Mobile (Android)

---

## Console Testing

Open browser console (F12) and check for:

1. **No JavaScript Errors**
   - ✅ No red error messages
   - ✅ No "undefined" errors
   - ✅ No "null" errors

2. **Expected Console Logs**
   - "Loaded schemes from window: 3400" (or similar)
   - "Initializing dashboard..."
   - "Rendering schemes..."
   - "Searching schemes..."

3. **Network Requests**
   - All CSS/JS files load (200 OK)
   - No 404 errors
   - No CORS errors

---

## Common Issues & Solutions

### Issue: "Failed to fetch" error
**Solution**: Use local server (node server.js) instead of opening HTML directly

### Issue: Schemes not showing
**Solution**: 
1. Check console for errors
2. Verify schemes-data.js is loaded
3. Wait 1-2 seconds for data to initialize
4. Refresh page

### Issue: Logout not working
**Solution**: 
1. Check console for errors
2. Clear browser cache
3. Try incognito mode

### Issue: Filters not working
**Solution**:
1. Check if schemes data is loaded
2. Verify filter values match scheme data
3. Check console for errors

### Issue: Save button not working
**Solution**:
1. Check if scheme ID is valid
2. Verify localStorage is enabled
3. Check console for errors

---

## Performance Testing

### Load Time
- Landing page: < 2 seconds
- Dashboard: < 3 seconds (includes data loading)
- Search results: < 1 second

### Interaction Speed
- Search filtering: < 100ms
- Page navigation: < 50ms
- Button clicks: Instant

### Memory Usage
- Initial load: ~50MB
- After browsing: ~100MB
- No memory leaks on navigation

---

## Accessibility Testing

- [ ] Keyboard navigation works
- [ ] Tab order is logical
- [ ] Form labels are present
- [ ] Buttons have descriptive text
- [ ] Color contrast is sufficient
- [ ] Focus indicators are visible

---

## Data Validation

### Schemes Data
- Total schemes: 3,400+
- Categories: Education, Health, Agriculture, Skill, Housing, Employment, Business, Social Welfare
- Levels: Central, State
- States: All major Indian states

### User Data
- Name: Required, min 2 chars
- Email: Valid email format
- Phone: 10-13 digits
- Password: Min 8 chars

---

## Security Testing

- [ ] Passwords are not logged
- [ ] Sensitive data not in localStorage (only tokens)
- [ ] XSS protection (no eval, innerHTML with user input)
- [ ] CSRF protection (tokens in API calls)
- [ ] Session timeout works

---

## Edge Cases

### Empty States
- [ ] No saved schemes → Shows empty state
- [ ] No search results → Shows "No schemes found"
- [ ] Invalid scheme ID → Shows "Scheme not found"

### Invalid Input
- [ ] Empty search → Shows all schemes
- [ ] Invalid email → Shows validation error
- [ ] Mismatched passwords → Shows error
- [ ] Invalid phone → Shows error

### Network Issues
- [ ] API failure → Falls back to local data
- [ ] Slow connection → Shows loading state
- [ ] Offline → Demo mode continues working

---

## Automated Testing (Future)

Consider adding:
- Unit tests (Jest)
- Integration tests (Cypress)
- E2E tests (Playwright)
- Visual regression tests (Percy)

---

## Reporting Issues

When reporting issues, include:
1. Browser and version
2. Device and OS
3. Steps to reproduce
4. Expected vs actual behavior
5. Console errors (if any)
6. Screenshots

---

## Success Criteria

✅ All pages load without errors
✅ All navigation works
✅ Search and filters work
✅ Save/unsave functionality works
✅ Authentication flows work
✅ Responsive on all devices
✅ No console errors
✅ Performance is acceptable

---

**Happy Testing! 🎉**
