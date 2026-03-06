# BharatSahayak Frontend - Page Structure Documentation

## Overview
The frontend has been restructured into a proper multi-page application with clear user flow and separation of concerns.

## Page Flow

```
Landing Page (landing.html)
    ↓
Login/Register (login.html)
    ↓
Profile Setup (profile-setup.html) [Optional - can skip]
    ↓
Dashboard (dashboard.html)
    ↓
Feature Pages (schemes.html, voice-assistant.html, etc.)
```

## Page Descriptions

### 1. Landing Page (`landing.html`)
**Purpose**: Marketing page to attract and inform users

**Sections**:
- Hero section with value proposition
- Statistics (400+ schemes, 10+ languages, 50K+ users)
- Features showcase (6 key features)
- How it works (3-step process)
- Testimonials from real users
- Call-to-action sections
- Footer with links

**CTAs**:
- "Start Free Today" → login.html?mode=register
- "Browse as Guest" → login.html?guest=true

**Target Users**: New visitors, potential users

---

### 2. Login/Register Page (`login.html`)
**Purpose**: Authentication and guest access

**Features**:
- Tabbed interface (Login/Register)
- OTP-based authentication
- Guest access option
- Collapsible API configuration
- Phone number validation
- Terms acceptance for registration

**User Flow**:
- **Login**: Phone → OTP → Dashboard
- **Register**: Phone + Language + Terms → OTP → Profile Setup
- **Guest**: Direct → Dashboard (limited features)

**Target Users**: Returning users, new registrations

---

### 3. Profile Setup (`profile-setup.html`)
**Purpose**: Collect user information for personalization

**Steps** (4-step wizard):
1. **Basic Info**: Age, Gender, Education
2. **Location**: State, District, Pincode, Area Type
3. **Occupation**: Occupation, Income, Social Category
4. **Complete**: Success message and next steps

**Features**:
- Progress bar showing current step
- Form validation
- Skip option (can complete later)
- Back/Next navigation
- Auto-save on completion

**Target Users**: New users after registration

---

### 4. Dashboard (`dashboard.html`)
**Purpose**: Central hub for all features

**Layout**:
- **Sidebar**: Navigation menu (collapsible)
- **Top Bar**: Theme toggle, language, user menu
- **Main Content**:
  - Welcome banner with eligible schemes count
  - Quick stats (4 cards)
  - Quick actions (4 cards)
  - Popular schemes (3 cards)
  - Recent activity list

**Navigation Items**:
- Dashboard (current)
- Search Schemes
- My Eligible Schemes
- Voice Assistant
- Agriculture
- My Profile
- Settings
- Logout

**Target Users**: All authenticated users

---

### 5. Schemes Page (`schemes.html`)
**Purpose**: Search and browse government schemes

**Features**:
- Large search bar
- Advanced filters (Category, State, Sort)
- Grid/List view toggle
- Scheme cards with:
  - Category badge
  - Bookmark button
  - Description
  - Department and state info
  - View details button
  - Check eligibility button
- Pagination
- Results count
- Empty state

**Target Users**: Users looking for specific schemes

---

## Additional Pages to Create

### 6. Eligible Schemes Page (`eligible-schemes.html`)
**Purpose**: Show schemes user qualifies for
**Features**:
- Personalized recommendations
- Eligibility score
- Application guidance
- Save for later

### 7. Voice Assistant Page (`voice-assistant.html`)
**Purpose**: Voice-based interaction
**Features**:
- Microphone button with animation
- Real-time transcription
- Voice response playback
- Language selector
- Example prompts

### 8. Agriculture Page (`agriculture.html`)
**Purpose**: Farming advisory
**Features**:
- Crop recommendations
- Market prices (mandi)
- Weather information
- Farming tips

### 9. Profile Page (`profile.html`)
**Purpose**: View and edit user profile
**Features**:
- Profile information display
- Edit mode
- Profile completion percentage
- Account settings

### 10. Settings Page (`settings.html`)
**Purpose**: App configuration
**Features**:
- Language preference
- Theme selection
- Notifications
- API configuration
- Privacy settings
- About/Help

---

## Common Components

### Sidebar Navigation
**Used in**: Dashboard and all feature pages
**Features**:
- Brand logo
- Navigation links with icons
- Active state highlighting
- Collapsible on mobile
- Logout button

### Top Bar
**Used in**: Dashboard and all feature pages
**Features**:
- Menu toggle (mobile)
- Page title
- Theme toggle
- Language selector
- User menu dropdown

### Toast Notifications
**Used in**: All pages
**Features**:
- Success, error, warning, info types
- Auto-dismiss after 3 seconds
- Slide-in animation
- Icon based on type

---

## Responsive Behavior

### Desktop (>1024px)
- Sidebar always visible
- Grid layouts (3-4 columns)
- Full navigation menu

### Tablet (768px - 1024px)
- Collapsible sidebar
- Grid layouts (2-3 columns)
- Compact navigation

### Mobile (<768px)
- Hidden sidebar (toggle button)
- Single column layouts
- Bottom navigation (optional)
- Touch-optimized buttons

---

## User Roles & Access

### Guest User
**Access**:
- ✅ Landing page
- ✅ Browse schemes (read-only)
- ✅ Search schemes
- ❌ Check eligibility
- ❌ Save schemes
- ❌ Voice assistant
- ❌ Profile features

**Limitations**:
- Banner: "Browsing as guest. Create account for full access"
- Disabled features show "Login required" message

### Authenticated User
**Access**:
- ✅ All pages
- ✅ Full features
- ✅ Personalized recommendations
- ✅ Save and bookmark
- ✅ Application tracking

---

## Navigation Patterns

### Primary Navigation
- Sidebar menu (desktop/tablet)
- Hamburger menu (mobile)

### Secondary Navigation
- Breadcrumbs (on detail pages)
- Back buttons
- Tab navigation (within pages)

### Quick Actions
- Dashboard quick action cards
- Floating action button (mobile)
- Context menus

---

## State Management

### Local Storage Keys
```javascript
{
  'bharatsahayak-config': {...},      // API configuration
  'bharatsahayak-token': 'jwt_token',  // Auth token
  'bharatsahayak-user': '+91...',      // Phone number
  'bharatsahayak-guest': 'true',       // Guest mode flag
  'bharatsahayak-theme': 'dark',       // Theme preference
  'bharatsahayak-language': 'hi',      // Language preference
  'bharatsahayak-profile': {...}       // User profile cache
}
```

---

## URL Structure

```
/                           → landing.html
/login                      → login.html
/login?mode=register        → login.html (register tab)
/login?guest=true           → login.html (guest access)
/profile-setup              → profile-setup.html
/dashboard                  → dashboard.html
/schemes                    → schemes.html
/schemes?category=agriculture → schemes.html (filtered)
/eligible-schemes           → eligible-schemes.html
/voice-assistant            → voice-assistant.html
/agriculture                → agriculture.html
/profile                    → profile.html
/settings                   → settings.html
```

---

## Next Steps

### Immediate (Phase 1)
1. ✅ Create landing page
2. ✅ Create login page
3. ✅ Create profile setup
4. ✅ Create dashboard
5. ✅ Create schemes page
6. ⏳ Update CSS for new pages
7. ⏳ Update JavaScript functions

### Short-term (Phase 2)
1. Create remaining feature pages
2. Implement API integration
3. Add loading states
4. Add error handling
5. Test responsive design

### Long-term (Phase 3)
1. Add PWA features
2. Implement offline mode
3. Add push notifications
4. Performance optimization
5. Accessibility improvements

---

## File Structure

```
frontend/
├── landing.html              # Landing/marketing page
├── login.html                # Authentication page
├── profile-setup.html        # Profile wizard
├── dashboard.html            # Main dashboard
├── schemes.html              # Scheme search
├── eligible-schemes.html     # Personalized schemes
├── voice-assistant.html      # Voice interface
├── agriculture.html          # Farm advisory
├── profile.html              # User profile
├── settings.html             # App settings
├── styles.css                # Global styles
├── app.js                    # Global JavaScript
├── manifest.json             # PWA manifest
├── service-worker.js         # Offline support
└── assets/
    ├── icons/                # App icons
    ├── images/               # Images
    └── fonts/                # Custom fonts
```

---

## Design System

### Colors
- Primary: #667eea (Purple-blue)
- Secondary: #764ba2 (Purple)
- Success: #10b981 (Green)
- Danger: #ef4444 (Red)
- Warning: #f59e0b (Orange)
- Info: #3b82f6 (Blue)

### Typography
- Font Family: Inter
- Headings: 600-700 weight
- Body: 400 weight
- Small text: 300 weight

### Spacing
- Base unit: 8px
- Small: 8px
- Medium: 16px
- Large: 24px
- XLarge: 32px

### Border Radius
- Small: 4px
- Medium: 8px
- Large: 12px
- XLarge: 16px
- Full: 9999px

---

## Accessibility

### WCAG 2.1 AA Compliance
- ✅ Color contrast ratios
- ✅ Keyboard navigation
- ✅ Screen reader support
- ✅ Focus indicators
- ✅ Alt text for images
- ✅ ARIA labels
- ✅ Form labels

### Keyboard Shortcuts
- `Tab`: Navigate forward
- `Shift+Tab`: Navigate backward
- `Enter`: Activate button/link
- `Esc`: Close modal/dropdown
- `/`: Focus search bar

---

## Performance Targets

- First Contentful Paint: < 1.5s
- Time to Interactive: < 3.5s
- Lighthouse Score: > 90
- Bundle Size: < 500KB
- API Response: < 2s

---

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+
- Mobile browsers (iOS Safari, Chrome Mobile)

---

## Testing Checklist

### Functional Testing
- [ ] All links work
- [ ] Forms validate correctly
- [ ] API calls succeed
- [ ] Error handling works
- [ ] Navigation flows correctly

### Visual Testing
- [ ] Responsive on all devices
- [ ] Dark mode works
- [ ] Animations smooth
- [ ] Icons display correctly
- [ ] Images load properly

### Accessibility Testing
- [ ] Keyboard navigation
- [ ] Screen reader compatible
- [ ] Color contrast passes
- [ ] Focus indicators visible
- [ ] ARIA labels present

---

## Deployment

### Build Process
1. Minify CSS and JavaScript
2. Optimize images
3. Generate service worker
4. Create manifest.json
5. Test on staging

### Hosting
- AWS S3 + CloudFront
- Enable HTTPS
- Configure CORS
- Set cache headers
- Enable compression

---

This structure provides a clear, scalable foundation for the BharatSahayak frontend application!
