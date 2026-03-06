# BharatSahayak - Immediate Action Plan

**Date:** March 6, 2026  
**Priority:** Start These Today  
**Time Required:** 2-3 hours for quick wins

---

## 🔴 CRITICAL: Do These First (Today)

### 1. Fix Integration Tests (30 minutes)
**Problem:** 12 tests failing due to DynamoDB mocking
**Impact:** Blocks production deployment
**File:** `tests/integration/conftest.py`

**Action:**
```bash
# Open the file
code tests/integration/conftest.py

# Add proper moto fixtures (see COMPREHENSIVE_ENHANCEMENT_PLAN.md section 7.1)
```

**Verification:**
```bash
pytest tests/integration/ -v
# Should see 12/12 passing instead of 0/12
```

---

### 2. Add Performance Optimizations (45 minutes)

#### 2a. Lazy Load Images (15 min)
**File:** `frontend/app.js`
**Add at line 1226 (end of file):**

```javascript
// Lazy load images
function initLazyLoading() {
    const images = document.querySelectorAll('img[data-src]');
    
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
                observer.unobserve(img);
            }
        });
    });
    
    images.forEach(img => imageObserver.observe(img));
}

// Call on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initLazyLoading);
} else {
    initLazyLoading();
}
```

**Then update HTML images:**
```html
<!-- Change from: -->
<img src="image.jpg" alt="Description">

<!-- To: -->
<img data-src="image.jpg" src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 400 300'%3E%3C/svg%3E" alt="Description">
```

#### 2b. Debounce Search (15 min)
**File:** `frontend/app.js`
**Find the searchSchemes function (around line 450) and add:**

```javascript
// Add debounce utility
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Wrap searchSchemes
const debouncedSearchSchemes = debounce(searchSchemes, 300);

// Update event listener
document.getElementById('search-input')?.addEventListener('input', (e) => {
    debouncedSearchSchemes();
});
```

#### 2c. Throttle Scroll (15 min)
**File:** `frontend/app.js`
**Add after debounce function:**

```javascript
// Add throttle utility
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Throttle scroll events
const throttledScroll = throttle(() => {
    // Handle scroll animations
    const scrolled = window.pageYOffset;
    document.querySelectorAll('.fade-in-on-scroll').forEach(el => {
        const elementTop = el.getBoundingClientRect().top;
        if (elementTop < window.innerHeight - 100) {
            el.classList.add('visible');
        }
    });
}, 100);

window.addEventListener('scroll', throttledScroll);
```

---

### 3. Add Security Headers (10 minutes)

**Files:** All 17 HTML files in `frontend/`
**Add in `<head>` section of each file:**

```html
<!-- Security Headers -->
<meta http-equiv="Content-Security-Policy" 
      content="default-src 'self'; 
               script-src 'self' 'unsafe-inline' 'unsafe-eval'; 
               style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; 
               font-src 'self' https://fonts.gstatic.com;
               img-src 'self' data: https:;
               connect-src 'self' https://*.amazonaws.com https://*.execute-api.*.amazonaws.com;">

<meta http-equiv="X-Content-Type-Options" content="nosniff">
<meta http-equiv="X-Frame-Options" content="DENY">
<meta http-equiv="X-XSS-Protection" content="1; mode=block">
<meta name="referrer" content="strict-origin-when-cross-origin">
```

**Quick way to add to all files:**
```bash
# Create a script
cat > add-security-headers.sh << 'EOF'
#!/bin/bash
for file in frontend/*.html; do
    # Add after <head> tag
    sed -i '/<head>/a\    <!-- Security Headers -->\n    <meta http-equiv="Content-Security-Policy" content="default-src '\''self'\''; script-src '\''self'\'' '\''unsafe-inline'\'' '\''unsafe-eval'\''; style-src '\''self'\'' '\''unsafe-inline'\'' https://fonts.googleapis.com; font-src '\''self'\'' https://fonts.gstatic.com; img-src '\''self'\'' data: https:; connect-src '\''self'\'' https://*.amazonaws.com https://*.execute-api.*.amazonaws.com;">\n    <meta http-equiv="X-Content-Type-Options" content="nosniff">\n    <meta http-equiv="X-Frame-Options" content="DENY">\n    <meta http-equiv="X-XSS-Protection" content="1; mode=block">\n    <meta name="referrer" content="strict-origin-when-cross-origin">' "$file"
done
EOF

chmod +x add-security-headers.sh
./add-security-headers.sh
```

---

### 4. Add Input Sanitization (15 minutes)

**File:** `frontend/app.js`
**Add at line 50 (after utility functions):**

```javascript
// XSS Protection - Sanitize user input
function sanitizeHTML(str) {
    if (!str) return '';
    const temp = document.createElement('div');
    temp.textContent = str;
    return temp.innerHTML;
}

function sanitizeObject(obj) {
    const sanitized = {};
    for (const key in obj) {
        if (typeof obj[key] === 'string') {
            sanitized[key] = sanitizeHTML(obj[key]);
        } else if (typeof obj[key] === 'object' && obj[key] !== null) {
            sanitized[key] = sanitizeObject(obj[key]);
        } else {
            sanitized[key] = obj[key];
        }
    }
    return sanitized;
}
```

**Then update display functions to use sanitization:**
```javascript
// Find displayScheme function (around line 600) and update:
function displayScheme(scheme) {
    // Sanitize all string fields
    const safe = sanitizeObject(scheme);
    
    document.getElementById('scheme-name').textContent = safe.name;
    document.getElementById('scheme-description').textContent = safe.description;
    // ... rest of function
}
```

---

### 5. Add Basic ARIA Labels (20 minutes)

**Priority Files:** `frontend/index.html`, `frontend/dashboard.html`, `frontend/schemes.html`

**Quick additions:**

```html
<!-- Navigation -->
<nav aria-label="Main navigation">
    <ul role="menubar">
        <li role="none"><a role="menuitem" href="#home">Home</a></li>
    </ul>
</nav>

<!-- Search -->
<div role="search">
    <input type="text" 
           id="search-input" 
           aria-label="Search government schemes"
           placeholder="Search schemes...">
    <button aria-label="Search" onclick="searchSchemes()">
        <i class="icon-search" aria-hidden="true"></i>
    </button>
</div>

<!-- Buttons with icons only -->
<button aria-label="Toggle theme" onclick="toggleTheme()">
    <i class="icon-moon" aria-hidden="true"></i>
</button>

<button aria-label="Open user menu" onclick="toggleUserMenu()">
    <i class="icon-user" aria-hidden="true"></i>
</button>

<!-- Toast notifications -->
<div role="alert" aria-live="polite" class="toast-container"></div>

<!-- Loading overlay -->
<div role="status" aria-live="polite" aria-label="Loading" class="loading-overlay">
    <div class="spinner"></div>
</div>
```

---

## 🟡 HIGH PRIORITY: Do These Tomorrow

### 6. Connect Voice Interface to Backend (2 hours)
**File:** `frontend/voice-assistant.html` and `frontend/app.js`
**See:** COMPREHENSIVE_ENHANCEMENT_PLAN.md Section 5.2

### 7. Implement Missing Animations (3 hours)
**File:** `frontend/styles.css`
**Add:** Bounce, shake, typewriter, particle effects
**See:** COMPREHENSIVE_ENHANCEMENT_PLAN.md Section 1

### 8. Add Scheme Comparison (2 hours)
**Files:** `frontend/schemes.html`, `frontend/app.js`
**See:** COMPREHENSIVE_ENHANCEMENT_PLAN.md Section 4.1

### 9. Add Favorites/Bookmarks (1 hour)
**Files:** `frontend/schemes.html`, `frontend/app.js`
**See:** COMPREHENSIVE_ENHANCEMENT_PLAN.md Section 4.2

---

## Verification Checklist

After completing today's tasks, verify:

```bash
# 1. Run tests
pytest tests/integration/ -v
# Should see 12/12 passing

# 2. Check for console errors
# Open browser DevTools, navigate through all pages
# Should see zero errors

# 3. Test performance
# Open Chrome DevTools > Lighthouse
# Run audit on landing.html
# Should see improved performance score

# 4. Test security
# Check browser console for CSP violations
# Should see no violations

# 5. Test accessibility
# Use browser extension (axe DevTools)
# Should see reduced accessibility issues
```

---

## Quick Commands

```bash
# Run all tests
make test

# Run only integration tests
pytest tests/integration/ -v

# Run with coverage
pytest --cov=src --cov-report=html

# Open coverage report
open htmlcov/index.html

# Check for syntax errors
python -m py_compile src/**/*.py

# Format code
black src/ tests/
isort src/ tests/

# Lint
flake8 src/ tests/
```

---

## Expected Results After Today

### Before
- ❌ 12 integration tests failing
- ❌ No performance optimization
- ❌ No security headers
- ❌ No input sanitization
- ❌ Minimal accessibility

### After (Today)
- ✅ 327/327 tests passing (100%)
- ✅ Lazy loading implemented
- ✅ Search debounced
- ✅ Scroll throttled
- ✅ CSP headers added
- ✅ XSS protection added
- ✅ Basic ARIA labels added

### Impact
- **Test Pass Rate:** 96.3% → 100% (+3.7%)
- **Performance:** ~75 → ~85 Lighthouse score (+10)
- **Security:** Vulnerable → Protected
- **Accessibility:** Partial → Improved

---

## Time Breakdown

| Task | Time | Priority |
|------|------|----------|
| Fix integration tests | 30 min | 🔴 Critical |
| Lazy load images | 15 min | 🔴 Critical |
| Debounce search | 15 min | 🔴 Critical |
| Throttle scroll | 15 min | 🔴 Critical |
| Add security headers | 10 min | 🔴 Critical |
| Add input sanitization | 15 min | 🔴 Critical |
| Add ARIA labels | 20 min | 🔴 Critical |
| **TOTAL** | **2 hours** | |

---

## Next Steps After Today

1. Review `COMPREHENSIVE_ENHANCEMENT_PLAN.md` for complete roadmap
2. Start Phase 2 (High Priority) tasks tomorrow
3. Schedule 2-week sprint for Phase 1 completion
4. Plan deployment after Phase 1

---

**Ready to start? Begin with Task 1 (Fix Integration Tests) and work through the list sequentially.**
