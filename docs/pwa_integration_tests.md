# PWA Integration Tests Documentation

## Overview

This document describes the integration tests for the BharatSahayak Progressive Web App (PWA). The tests validate offline functionality, service worker caching, and voice interface integration.

**Requirements Validated:**
- Requirement 10.2: Multi-Channel Access and Progressive Web App
- Requirement 7.1: Offline Functionality and Low-Bandwidth Support

## Test Structure

### Test Files

1. **test_integration_pwa_simple.py**
   - Simplified integration tests that don't require browser automation
   - Tests service worker logic, offline queue, cache management
   - Can run in any Python environment with pytest

2. **test_integration_pwa.py**
   - Full browser-based integration tests using Playwright
   - Tests actual PWA behavior in a browser environment
   - Requires Playwright installation

### Test Categories

#### 1. Offline Functionality Tests

**TestOfflineFunctionality**
- Service worker installation
- Static asset caching
- Offline page loading
- API request fallback to cache
- Offline action queuing
- Sync on reconnection
- Cached data retrieval

**Key Scenarios:**
- App loads when offline using cached assets
- API requests fall back to cache when network unavailable
- User actions are queued when offline
- Queued actions sync automatically when connection restored

#### 2. Service Worker Caching Tests

**TestServiceWorkerCaching**
- Cache-first strategy for static assets
- Network-first strategy for API requests
- Cache versioning and cleanup
- Selective API endpoint caching

**Caching Strategies:**
- **Static Assets**: Cache-first (serve from cache, update in background)
- **API Requests**: Network-first (try network, fallback to cache)
- **Cacheable APIs**: `/api/schemes`, `/api/languages`, `/api/health/facilities`

#### 3. Voice Interface Integration Tests

**TestVoiceInterfaceIntegration**
- Microphone permission handling
- Voice recording UI state management
- Voice-to-text integration flow
- Text-to-voice integration flow
- Language selection
- Offline voice handling

**Voice Flow:**
1. User clicks voice button
2. Microphone permission requested
3. Audio recorded
4. Sent to backend for transcription
5. Text displayed in chat input
6. Response generated
7. Audio synthesized and played

#### 4. PWA Installability Tests

**TestPWAInstallability**
- Manifest presence and validity
- Required manifest fields
- Icon sizes and formats
- Installability criteria

**Manifest Requirements:**
- Name and short_name
- Start URL
- Display mode (standalone)
- Icons (192x192, 512x512)
- Theme colors

#### 5. Performance Tests

**TestPWAPerformance**
- Initial load time (< 3 seconds)
- Cached load time (< 2 seconds)
- Low bandwidth performance
- Low-end device support (1GB RAM)

## Running the Tests

### Quick Start

```bash
# Run all PWA integration tests
python scripts/test_pwa_integration.py
```

### Run Specific Test Suites

```bash
# Run simplified tests only
pytest .kiro/specs/bharatsahayak/tests/test_integration_pwa_simple.py -v

# Run browser tests (requires Playwright)
pytest .kiro/specs/bharatsahayak/tests/test_integration_pwa.py -v
```

### Run Specific Test Classes

```bash
# Test offline functionality
pytest .kiro/specs/bharatsahayak/tests/test_integration_pwa_simple.py::TestOfflineQueueManagement -v

# Test service worker caching
pytest .kiro/specs/bharatsahayak/tests/test_integration_pwa_simple.py::TestServiceWorkerLogic -v

# Test voice interface
pytest .kiro/specs/bharatsahayak/tests/test_integration_pwa_simple.py::TestVoiceInterfaceIntegration -v
```

## Prerequisites

### For Simplified Tests

```bash
pip install pytest
```

### For Browser Tests

```bash
pip install playwright pytest-asyncio
playwright install chromium
```

## Test Coverage

### Offline Functionality (Requirement 7.1)

✓ Service worker registration and activation
✓ Static asset caching on install
✓ Offline page loading from cache
✓ API request fallback to cache
✓ Offline action queuing
✓ Automatic sync on reconnection
✓ Cache expiration and cleanup
✓ Network status monitoring

### PWA Features (Requirement 10.2)

✓ Progressive Web App manifest
✓ Service worker lifecycle
✓ Installability criteria
✓ Offline-first architecture
✓ Cache versioning
✓ Background sync
✓ Low-bandwidth optimization
✓ Mobile viewport support

### Voice Interface Integration

✓ Microphone permission handling
✓ Audio recording and processing
✓ Voice-to-text transcription
✓ Text-to-voice synthesis
✓ Language selection
✓ Offline voice handling
✓ Audio format support

## Key Test Scenarios

### Scenario 1: First-Time User

1. User visits app for first time
2. Service worker installs
3. Static assets cached
4. App becomes available offline
5. User can use basic features without network

**Test:** `test_service_worker_installation`, `test_static_assets_cached`

### Scenario 2: Offline Usage

1. User loses network connection
2. Offline indicator appears
3. User can still browse cached content
4. User actions are queued
5. When online, actions sync automatically

**Test:** `test_offline_page_load`, `test_offline_queue_creation`, `test_offline_sync_on_reconnect`

### Scenario 3: Voice Interaction

1. User clicks voice button
2. Microphone permission granted
3. User speaks query
4. Audio transcribed to text
5. Response generated
6. Response played as audio

**Test:** `test_voice_to_text_integration`, `test_text_to_voice_integration`

### Scenario 4: Low Bandwidth

1. User on slow 3G connection
2. App loads from cache quickly
3. Only essential data fetched
4. Bandwidth usage < 100KB per query
5. App remains responsive

**Test:** `test_low_bandwidth_performance`, `test_cached_load_time`

## Debugging Failed Tests

### Service Worker Not Installing

**Symptoms:** `test_service_worker_installation` fails

**Possible Causes:**
- Service worker file not found
- Syntax error in sw.js
- HTTPS not enabled (required for service workers)

**Solutions:**
- Check `frontend/sw.js` exists
- Validate JavaScript syntax
- Ensure server uses HTTPS or localhost

### Offline Tests Failing

**Symptoms:** `test_offline_page_load` fails

**Possible Causes:**
- Assets not cached properly
- Cache names don't match
- Service worker not activated

**Solutions:**
- Check STATIC_ASSETS list in sw.js
- Verify cache naming convention
- Wait for service worker activation

### Voice Tests Failing

**Symptoms:** Voice integration tests fail

**Possible Causes:**
- Microphone permission denied
- Audio format not supported
- API endpoints not responding

**Solutions:**
- Grant microphone permission in browser
- Check supported audio formats
- Verify backend voice endpoints

## Performance Benchmarks

### Load Time Targets

- **Initial Load:** < 3 seconds
- **Cached Load:** < 2 seconds
- **API Response:** < 1 second
- **Voice Transcription:** < 2 seconds

### Bandwidth Targets

- **Initial Download:** < 500KB
- **Per Query:** < 100KB
- **Voice Audio:** < 50KB per message

### Device Support

- **Minimum RAM:** 1GB
- **Minimum Storage:** 50MB
- **Browser:** Chrome 80+, Firefox 75+, Safari 13+

## Continuous Integration

### CI Pipeline Integration

```yaml
# Example GitHub Actions workflow
name: PWA Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install pytest playwright pytest-asyncio
          playwright install chromium
      - name: Run PWA tests
        run: python scripts/test_pwa_integration.py
```

## Maintenance

### Adding New Tests

1. Identify the feature to test
2. Choose appropriate test file (simple vs browser)
3. Add test method to relevant test class
4. Follow naming convention: `test_<feature>_<scenario>`
5. Add docstring explaining what is tested
6. Run tests to verify

### Updating Tests

When PWA implementation changes:

1. Review affected test cases
2. Update test expectations
3. Add new tests for new features
4. Remove obsolete tests
5. Update documentation

## Troubleshooting

### Common Issues

**Issue:** Tests timeout
**Solution:** Increase timeout values, check network connectivity

**Issue:** Browser tests fail to launch
**Solution:** Install Playwright browsers: `playwright install`

**Issue:** Service worker not updating
**Solution:** Clear browser cache, use `skipWaiting()` in sw.js

**Issue:** Offline tests inconsistent
**Solution:** Add proper wait times, ensure service worker is ready

## References

- [Service Worker API](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API)
- [PWA Best Practices](https://web.dev/pwa/)
- [Playwright Documentation](https://playwright.dev/python/)
- [Offline First Architecture](https://offlinefirst.org/)

## Related Documentation

- [PWA Implementation Guide](./pwa_implementation.md)
- [Service Worker Guide](../frontend/README.md)
- [Voice Interface Documentation](./voice_interface_implementation.md)
- [Offline Cache Implementation](./offline_cache_implementation.md)
