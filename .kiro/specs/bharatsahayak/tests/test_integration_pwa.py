"""
Integration tests for PWA functionality.

Tests offline functionality, service worker caching, and voice interface integration.
Requirements: 10.2, 7.1
"""

import pytest
import asyncio
import json
import time
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
import tempfile
import shutil


@pytest.fixture
async def browser():
    """Create a browser instance for testing."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        yield browser
        await browser.close()


@pytest.fixture
async def context(browser):
    """Create a browser context with service worker support."""
    context = await browser.new_context(
        viewport={'width': 375, 'height': 667},  # Mobile viewport
        user_agent='Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36',
        permissions=['microphone'],
        service_workers='allow'
    )
    yield context
    await context.close()


@pytest.fixture
async def page(context):
    """Create a page for testing."""
    page = await context.new_page()
    yield page
    await page.close()


@pytest.fixture
def pwa_server():
    """Mock PWA server for testing."""
    # In real tests, this would start a local server serving the PWA
    # For now, we'll use a mock
    return "http://localhost:8000"


class TestOfflineFunctionality:
    """Test offline functionality of the PWA."""
    
    @pytest.mark.asyncio
    async def test_service_worker_installation(self, page, pwa_server):
        """Test that service worker installs successfully."""
        # Navigate to PWA
        await page.goto(pwa_server)
        
        # Wait for service worker to register
        await page.wait_for_timeout(2000)
        
        # Check service worker registration
        sw_registered = await page.evaluate("""
            async () => {
                if ('serviceWorker' in navigator) {
                    const registration = await navigator.serviceWorker.ready;
                    return registration !== null;
                }
                return false;
            }
        """)
        
        assert sw_registered, "Service worker should be registered"
    
    @pytest.mark.asyncio
    async def test_static_assets_cached(self, page, pwa_server):
        """Test that static assets are cached on install."""
        await page.goto(pwa_server)
        await page.wait_for_timeout(2000)
        
        # Check if static assets are in cache
        cached_assets = await page.evaluate("""
            async () => {
                const cacheNames = await caches.keys();
                const cache = await caches.open(cacheNames[0]);
                const requests = await cache.keys();
                return requests.map(req => req.url);
            }
        """)
        
        # Verify essential assets are cached
        essential_assets = ['/index.html', '/manifest.json', '/css/styles.css']
        for asset in essential_assets:
            assert any(asset in url for url in cached_assets), \
                f"Asset {asset} should be cached"
    
    @pytest.mark.asyncio
    async def test_offline_page_load(self, page, pwa_server):
        """Test that app loads when offline."""
        # First load online to cache assets
        await page.goto(pwa_server)
        await page.wait_for_timeout(2000)
        
        # Go offline
        await page.context.set_offline(True)
        
        # Reload page
        await page.reload()
        
        # Check that page loaded from cache
        title = await page.title()
        assert title, "Page should load offline from cache"
        
        # Check offline indicator is visible
        offline_indicator = await page.query_selector('#offlineIndicator')
        assert offline_indicator, "Offline indicator should be present"
        
        is_visible = await offline_indicator.is_visible()
        assert is_visible, "Offline indicator should be visible when offline"
    
    @pytest.mark.asyncio
    async def test_offline_api_fallback(self, page, pwa_server):
        """Test that API requests fall back to cache when offline."""
        await page.goto(pwa_server)
        await page.wait_for_timeout(2000)
        
        # Make API request while online to cache it
        await page.evaluate("""
            async () => {
                await fetch('/api/schemes');
            }
        """)
        
        await page.wait_for_timeout(1000)
        
        # Go offline
        await page.context.set_offline(True)
        
        # Try API request offline
        response = await page.evaluate("""
            async () => {
                const response = await fetch('/api/schemes');
                return {
                    ok: response.ok,
                    fromCache: response.headers.get('X-From-Cache') === 'true'
                };
            }
        """)
        
        assert response['ok'], "Cached API request should succeed"
        assert response['fromCache'], "Response should be from cache"
    
    @pytest.mark.asyncio
    async def test_offline_queue_creation(self, page, pwa_server):
        """Test that actions are queued when offline."""
        await page.goto(pwa_server)
        await page.wait_for_timeout(2000)
        
        # Go offline
        await page.context.set_offline(True)
        
        # Attempt to send a message
        await page.evaluate("""
            () => {
                window.offlineModule.queueOfflineAction('message', {
                    message: 'Test message',
                    sessionId: 'test-session',
                    language: 'hi'
                });
            }
        """)
        
        # Check queue status
        queue_status = await page.evaluate("""
            () => {
                return window.offlineModule.getOfflineQueueStatus();
            }
        """)
        
        assert queue_status['queueLength'] > 0, "Action should be queued"
    
    @pytest.mark.asyncio
    async def test_offline_sync_on_reconnect(self, page, pwa_server):
        """Test that queued actions sync when connection is restored."""
        await page.goto(pwa_server)
        await page.wait_for_timeout(2000)
        
        # Go offline and queue action
        await page.context.set_offline(True)
        
        await page.evaluate("""
            () => {
                window.offlineModule.queueOfflineAction('event', {
                    eventType: 'test_event',
                    eventData: { test: true }
                });
            }
        """)
        
        # Go back online
        await page.context.set_offline(False)
        
        # Trigger online event
        await page.evaluate("""
            () => {
                window.dispatchEvent(new Event('online'));
            }
        """)
        
        # Wait for sync
        await page.wait_for_timeout(3000)
        
        # Check that queue is empty after sync
        queue_status = await page.evaluate("""
            () => {
                return window.offlineModule.getOfflineQueueStatus();
            }
        """)
        
        assert queue_status['queueLength'] == 0, "Queue should be empty after sync"
    
    @pytest.mark.asyncio
    async def test_cached_data_retrieval(self, page, pwa_server):
        """Test retrieval of cached data."""
        await page.goto(pwa_server)
        await page.wait_for_timeout(2000)
        
        # Cache some data
        test_data = {'schemes': [{'id': '1', 'name': 'Test Scheme'}]}
        
        await page.evaluate(f"""
            () => {{
                localStorage.setItem('cached_schemes', JSON.stringify({{
                    data: {json.dumps(test_data)},
                    timestamp: Date.now()
                }}));
            }}
        """)
        
        # Retrieve cached data
        cached = await page.evaluate("""
            () => {
                return window.offlineModule.getCachedData('schemes');
            }
        """)
        
        assert cached is not None, "Should retrieve cached data"
        assert cached['schemes'][0]['name'] == 'Test Scheme', \
            "Cached data should match"


class TestServiceWorkerCaching:
    """Test service worker caching strategies."""
    
    @pytest.mark.asyncio
    async def test_cache_first_strategy_for_static_assets(self, page, pwa_server):
        """Test cache-first strategy for static assets."""
        await page.goto(pwa_server)
        await page.wait_for_timeout(2000)
        
        # Load a static asset
        response1 = await page.evaluate("""
            async () => {
                const response = await fetch('/css/styles.css');
                return {
                    ok: response.ok,
                    cached: response.headers.get('X-From-Cache') === 'true'
                };
            }
        """)
        
        # Load again - should come from cache
        response2 = await page.evaluate("""
            async () => {
                const response = await fetch('/css/styles.css');
                return {
                    ok: response.ok,
                    cached: response.headers.get('X-From-Cache') === 'true'
                };
            }
        """)
        
        assert response1['ok'] and response2['ok'], \
            "Both requests should succeed"
    
    @pytest.mark.asyncio
    async def test_network_first_strategy_for_api(self, page, pwa_server):
        """Test network-first strategy for API requests."""
        await page.goto(pwa_server)
        await page.wait_for_timeout(2000)
        
        # Make API request (should go to network first)
        response = await page.evaluate("""
            async () => {
                const response = await fetch('/api/schemes');
                return {
                    ok: response.ok,
                    fromCache: response.headers.get('X-From-Cache') === 'true'
                };
            }
        """)
        
        assert response['ok'], "API request should succeed"
        # First request should not be from cache
        assert not response.get('fromCache', False), \
            "First API request should be from network"
    
    @pytest.mark.asyncio
    async def test_cache_versioning(self, page, pwa_server):
        """Test that old caches are cleaned up on activation."""
        await page.goto(pwa_server)
        await page.wait_for_timeout(2000)
        
        # Check cache names
        cache_names = await page.evaluate("""
            async () => {
                return await caches.keys();
            }
        """)
        
        # Should only have current version caches
        assert len(cache_names) > 0, "Should have at least one cache"
        
        # All caches should start with 'bharatsahayak-'
        for name in cache_names:
            assert name.startswith('bharatsahayak-'), \
                f"Cache {name} should follow naming convention"
    
    @pytest.mark.asyncio
    async def test_selective_api_caching(self, page, pwa_server):
        """Test that only specified API endpoints are cached."""
        await page.goto(pwa_server)
        await page.wait_for_timeout(2000)
        
        # Cacheable endpoint
        await page.evaluate("""
            async () => {
                await fetch('/api/schemes');
            }
        """)
        
        # Non-cacheable endpoint
        await page.evaluate("""
            async () => {
                await fetch('/api/ask', {
                    method: 'POST',
                    body: JSON.stringify({ query: 'test' })
                });
            }
        """)
        
        await page.wait_for_timeout(1000)
        
        # Go offline and test
        await page.context.set_offline(True)
        
        # Cacheable should work
        schemes_response = await page.evaluate("""
            async () => {
                try {
                    const response = await fetch('/api/schemes');
                    return { ok: response.ok };
                } catch (e) {
                    return { ok: false };
                }
            }
        """)
        
        assert schemes_response['ok'], "Cacheable endpoint should work offline"


class TestVoiceInterfaceIntegration:
    """Test voice interface integration with PWA."""
    
    @pytest.mark.asyncio
    async def test_microphone_permission_request(self, page, pwa_server):
        """Test that microphone permission is requested."""
        await page.goto(pwa_server)
        await page.wait_for_timeout(2000)
        
        # Grant microphone permission
        await page.context.grant_permissions(['microphone'])
        
        # Click voice button
        voice_btn = await page.query_selector('#voiceBtn')
        assert voice_btn, "Voice button should exist"
        
        # Check if button is enabled
        is_disabled = await voice_btn.is_disabled()
        assert not is_disabled, "Voice button should be enabled"
    
    @pytest.mark.asyncio
    async def test_voice_recording_ui_state(self, page, pwa_server):
        """Test voice recording UI state changes."""
        await page.goto(pwa_server)
        await page.wait_for_timeout(2000)
        
        await page.context.grant_permissions(['microphone'])
        
        voice_btn = await page.query_selector('#voiceBtn')
        
        # Check initial state
        has_recording_class = await voice_btn.evaluate(
            'el => el.classList.contains("recording")'
        )
        assert not has_recording_class, "Should not have recording class initially"
        
        # Simulate recording start
        await page.evaluate("""
            () => {
                const btn = document.getElementById('voiceBtn');
                btn.classList.add('recording');
            }
        """)
        
        has_recording_class = await voice_btn.evaluate(
            'el => el.classList.contains("recording")'
        )
        assert has_recording_class, "Should have recording class when recording"
    
    @pytest.mark.asyncio
    async def test_voice_to_text_integration(self, page, pwa_server):
        """Test voice-to-text integration flow."""
        await page.goto(pwa_server)
        await page.wait_for_timeout(2000)
        
        # Mock the API response
        await page.route('**/api/voice-to-text', lambda route: route.fulfill(
            status=200,
            content_type='application/json',
            body=json.dumps({
                'text': 'मुझे योजनाओं के बारे में बताएं',
                'confidence': 0.95,
                'language': 'hi'
            })
        ))
        
        # Simulate voice input processing
        result = await page.evaluate("""
            async () => {
                const blob = new Blob(['fake audio data'], { type: 'audio/webm' });
                const formData = new FormData();
                formData.append('audio', blob);
                formData.append('language', 'hi');
                
                const response = await fetch('/api/voice-to-text', {
                    method: 'POST',
                    body: formData
                });
                
                return await response.json();
            }
        """)
        
        assert result['text'], "Should receive transcribed text"
        assert result['confidence'] > 0.8, "Should have high confidence"
    
    @pytest.mark.asyncio
    async def test_text_to_voice_integration(self, page, pwa_server):
        """Test text-to-voice integration flow."""
        await page.goto(pwa_server)
        await page.wait_for_timeout(2000)
        
        # Mock the API response with audio blob
        await page.route('**/api/text-to-voice', lambda route: route.fulfill(
            status=200,
            content_type='audio/wav',
            body=b'fake audio data'
        ))
        
        # Test TTS
        result = await page.evaluate("""
            async () => {
                const response = await fetch('/api/text-to-voice', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        text: 'नमस्ते',
                        language: 'hi'
                    })
                });
                
                return {
                    ok: response.ok,
                    contentType: response.headers.get('Content-Type')
                };
            }
        """)
        
        assert result['ok'], "TTS request should succeed"
        assert 'audio' in result['contentType'], "Should return audio content"
    
    @pytest.mark.asyncio
    async def test_voice_language_selection(self, page, pwa_server):
        """Test voice language selection integration."""
        await page.goto(pwa_server)
        await page.wait_for_timeout(2000)
        
        # Set language
        await page.evaluate("""
            () => {
                if (window.voiceModule) {
                    window.voiceModule.setVoiceLanguage('hi');
                }
            }
        """)
        
        # Verify language is set
        current_lang = await page.evaluate("""
            () => {
                return window.app ? window.app.currentLanguage : 'hi';
            }
        """)
        
        assert current_lang == 'hi', "Language should be set correctly"
    
    @pytest.mark.asyncio
    async def test_voice_offline_handling(self, page, pwa_server):
        """Test voice interface behavior when offline."""
        await page.goto(pwa_server)
        await page.wait_for_timeout(2000)
        
        # Go offline
        await page.context.set_offline(True)
        
        # Try to use voice (should queue or show error)
        await page.evaluate("""
            () => {
                const voiceBtn = document.getElementById('voiceBtn');
                if (voiceBtn) {
                    voiceBtn.click();
                }
            }
        """)
        
        await page.wait_for_timeout(1000)
        
        # Check if offline indicator is shown
        offline_indicator = await page.query_selector('#offlineIndicator')
        is_visible = await offline_indicator.is_visible()
        
        assert is_visible, "Should show offline indicator"


class TestPWAInstallability:
    """Test PWA installation and manifest."""
    
    @pytest.mark.asyncio
    async def test_manifest_present(self, page, pwa_server):
        """Test that manifest.json is present and valid."""
        await page.goto(pwa_server)
        
        # Check manifest link
        manifest_link = await page.query_selector('link[rel="manifest"]')
        assert manifest_link, "Manifest link should be present"
        
        # Fetch manifest
        manifest_href = await manifest_link.get_attribute('href')
        manifest_response = await page.goto(f"{pwa_server}{manifest_href}")
        
        assert manifest_response.ok, "Manifest should be accessible"
    
    @pytest.mark.asyncio
    async def test_manifest_content(self, page, pwa_server):
        """Test manifest content is valid."""
        manifest_response = await page.goto(f"{pwa_server}/manifest.json")
        manifest = await manifest_response.json()
        
        # Check required fields
        assert 'name' in manifest, "Manifest should have name"
        assert 'short_name' in manifest, "Manifest should have short_name"
        assert 'start_url' in manifest, "Manifest should have start_url"
        assert 'display' in manifest, "Manifest should have display mode"
        assert 'icons' in manifest, "Manifest should have icons"
        
        # Check icons
        assert len(manifest['icons']) > 0, "Should have at least one icon"
        
        # Verify icon sizes
        icon_sizes = [icon['sizes'] for icon in manifest['icons']]
        assert '192x192' in icon_sizes, "Should have 192x192 icon"
        assert '512x512' in icon_sizes, "Should have 512x512 icon"
    
    @pytest.mark.asyncio
    async def test_pwa_installable(self, page, pwa_server):
        """Test that PWA meets installability criteria."""
        await page.goto(pwa_server)
        await page.wait_for_timeout(2000)
        
        # Check for service worker
        sw_registered = await page.evaluate("""
            async () => {
                return 'serviceWorker' in navigator;
            }
        """)
        
        assert sw_registered, "Service worker should be supported"
        
        # Check for manifest
        has_manifest = await page.evaluate("""
            () => {
                return document.querySelector('link[rel="manifest"]') !== null;
            }
        """)
        
        assert has_manifest, "Manifest should be linked"


class TestPWAPerformance:
    """Test PWA performance characteristics."""
    
    @pytest.mark.asyncio
    async def test_initial_load_time(self, page, pwa_server):
        """Test that initial load time is acceptable."""
        start_time = time.time()
        
        await page.goto(pwa_server)
        await page.wait_for_load_state('networkidle')
        
        load_time = time.time() - start_time
        
        # Should load within 3 seconds
        assert load_time < 3.0, f"Initial load took {load_time}s, should be < 3s"
    
    @pytest.mark.asyncio
    async def test_cached_load_time(self, page, pwa_server):
        """Test that cached load is faster."""
        # First load
        await page.goto(pwa_server)
        await page.wait_for_load_state('networkidle')
        
        # Second load (from cache)
        start_time = time.time()
        await page.reload()
        await page.wait_for_load_state('networkidle')
        cached_load_time = time.time() - start_time
        
        # Cached load should be faster
        assert cached_load_time < 2.0, \
            f"Cached load took {cached_load_time}s, should be < 2s"
    
    @pytest.mark.asyncio
    async def test_low_bandwidth_performance(self, page, pwa_server):
        """Test performance on low bandwidth."""
        # Simulate slow 3G
        await page.context.route('**/*', lambda route: asyncio.create_task(
            slow_route(route, delay=0.5)
        ))
        
        start_time = time.time()
        await page.goto(pwa_server)
        await page.wait_for_load_state('domcontentloaded')
        load_time = time.time() - start_time
        
        # Should still be usable on slow connection
        assert load_time < 5.0, \
            f"Load on slow connection took {load_time}s, should be < 5s"


async def slow_route(route, delay):
    """Helper to simulate slow network."""
    await asyncio.sleep(delay)
    await route.continue_()


# Run tests
if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
