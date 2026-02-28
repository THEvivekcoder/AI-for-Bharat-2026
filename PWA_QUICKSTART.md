# BharatSahayak PWA Quick Start Guide

## Overview

The BharatSahayak Progressive Web App (PWA) provides a voice-first, multilingual interface for accessing government services, agricultural guidance, and more. This guide will help you get the PWA up and running quickly.

## Prerequisites

- Python 3.11+
- FastAPI backend running (see main QUICKSTART.md)
- Modern web browser (Chrome 90+, Firefox 88+, Safari 14+)
- HTTPS enabled (required for PWA features)

## Quick Start

### 1. Verify Backend is Running

```bash
# Start the backend if not already running
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Generate PWA Icons (First Time Only)

```bash
# Install Pillow if not already installed
pip install Pillow

# Create a simple icon (or use your logo)
python3 << 'EOF'
from PIL import Image, ImageDraw, ImageFont

# Create a simple icon with "BS" text
sizes = [72, 96, 128, 144, 152, 192, 384, 512]

for size in sizes:
    # Create image with gradient background
    img = Image.new('RGB', (size, size), color='#2563eb')
    draw = ImageDraw.Draw(img)
    
    # Add text
    font_size = size // 3
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
    except:
        font = ImageFont.load_default()
    
    text = "BS"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    position = ((size - text_width) // 2, (size - text_height) // 2)
    draw.text(position, text, fill='white', font=font)
    
    # Save
    img.save(f'frontend/icons/icon-{size}x{size}.png')
    print(f'Generated icon-{size}x{size}.png')

print('All icons generated!')
EOF
```

### 3. Configure Backend to Serve PWA

Add to your `app/main.py`:

```python
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

# Mount static files
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")
app.mount("/icons", StaticFiles(directory=FRONTEND_DIR / "icons"), name="icons")

@app.get("/manifest.json")
async def serve_manifest():
    return FileResponse(FRONTEND_DIR / "manifest.json")

@app.get("/sw.js")
async def serve_service_worker():
    return FileResponse(
        FRONTEND_DIR / "sw.js",
        media_type="application/javascript",
        headers={"Service-Worker-Allowed": "/", "Cache-Control": "no-cache"}
    )

@app.get("/{full_path:path}")
async def serve_pwa(full_path: str):
    if not full_path.startswith("api/"):
        return FileResponse(FRONTEND_DIR / "index.html")
```

### 4. Access the PWA

Open your browser and navigate to:
```
http://localhost:8000
```

For HTTPS (required for full PWA features):
```
https://localhost:8000
```

## Testing the PWA

### Test Voice Interface

1. Click the microphone button (large blue circle)
2. Allow microphone access when prompted
3. Speak your query in Hindi or English
4. The transcribed text will appear in the input box
5. Click send or wait for auto-send

### Test Chat Interface

1. Type a message in the text input
2. Click the send button or press Enter
3. View the response in the chat area
4. Responses can be played as audio

### Test Service Views

Click the navigation tabs at the top:
- **Chat**: Conversational interface
- **Schemes**: Browse government schemes
- **Farming**: Agricultural guidance
- **Skills**: Training and jobs
- **Health**: Health information

### Test Offline Mode

1. Open browser DevTools (F12)
2. Go to Network tab
3. Select "Offline" from throttling dropdown
4. Try using the app - cached content should work
5. Go back online - queued actions will sync

### Test PWA Installation

**On Desktop (Chrome/Edge):**
1. Look for install icon in address bar
2. Click "Install"
3. App opens in standalone window

**On Mobile (Android):**
1. Tap menu (⋮)
2. Select "Add to Home Screen"
3. Confirm installation
4. App appears on home screen

**On iOS (Safari):**
1. Tap share button
2. Select "Add to Home Screen"
3. Confirm
4. App appears on home screen

## Features Overview

### Voice Interface
- 🎤 Voice recording with visual feedback
- 🔊 Audio playback of responses
- 🌐 8 language support
- 🎯 Automatic language detection

### Chat Interface
- 💬 Real-time messaging
- 📝 Message history
- ⏱️ Timestamps
- 🔄 Loading indicators

### Offline Mode
- 📱 Works without internet
- 💾 Automatic caching
- 🔄 Background sync
- 📊 Sync status indicator

### Service Views
- 📋 Government schemes
- 🌾 Farmer advisory
- 🎓 Skills & jobs
- 🏥 Health information

## Troubleshooting

### Service Worker Not Registering

**Problem:** PWA features not working

**Solution:**
- Ensure HTTPS is enabled (required for service workers)
- Check browser console for errors
- Verify `sw.js` is accessible at `/sw.js`
- Clear browser cache and reload

### Voice Recording Not Working

**Problem:** Microphone button doesn't work

**Solution:**
- Check microphone permissions in browser settings
- Ensure HTTPS is enabled (required for getUserMedia)
- Try a different browser
- Check if microphone is working in other apps

### Icons Not Displaying

**Problem:** PWA icons are broken

**Solution:**
- Run the icon generation script above
- Verify icons exist in `frontend/icons/`
- Check file permissions
- Clear browser cache

### Offline Mode Not Working

**Problem:** App doesn't work offline

**Solution:**
- Verify service worker is registered (check DevTools > Application > Service Workers)
- Check cache storage (DevTools > Application > Cache Storage)
- Ensure you've used the app online first (to populate cache)
- Try unregistering and re-registering service worker

### API Requests Failing

**Problem:** "Network error" or "Failed to fetch"

**Solution:**
- Verify backend is running
- Check API endpoint URLs in `frontend/js/api.js`
- Check CORS configuration
- Look for errors in browser console and backend logs

## Development Tips

### Enable Debug Logging

Add to browser console:
```javascript
localStorage.setItem('debug', 'true');
location.reload();
```

### Clear All Caches

```javascript
// In browser console
caches.keys().then(keys => {
  keys.forEach(key => caches.delete(key));
  console.log('All caches cleared');
});
```

### Unregister Service Worker

```javascript
// In browser console
navigator.serviceWorker.getRegistrations().then(registrations => {
  registrations.forEach(reg => reg.unregister());
  console.log('Service workers unregistered');
});
```

### View Offline Queue

```javascript
// In browser console
JSON.parse(localStorage.getItem('offlineQueue'));
```

## Production Deployment

### 1. Generate Production Icons

Use your actual logo:
```bash
# Using ImageMagick
convert logo.png -resize 192x192 frontend/icons/icon-192x192.png
convert logo.png -resize 512x512 frontend/icons/icon-512x512.png
# ... repeat for all sizes
```

### 2. Update Manifest

Edit `frontend/manifest.json`:
```json
{
  "start_url": "https://bharatsahayak.gov.in/",
  "scope": "https://bharatsahayak.gov.in/"
}
```

### 3. Configure HTTPS

Ensure your server has valid SSL certificates:
```bash
# Using Let's Encrypt
sudo certbot --nginx -d bharatsahayak.gov.in
```

### 4. Enable Compression

Add to nginx config:
```nginx
gzip on;
gzip_types text/css application/javascript application/json;
gzip_min_length 1000;
```

### 5. Set Cache Headers

```nginx
location ~* \.(css|js|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

### 6. Deploy

```bash
# Build and deploy
git pull
systemctl restart bharatsahayak
```

## Monitoring

### Check PWA Status

1. Open DevTools (F12)
2. Go to Application tab
3. Check:
   - Manifest
   - Service Workers
   - Cache Storage
   - Local Storage

### Monitor Performance

Use Lighthouse:
1. Open DevTools
2. Go to Lighthouse tab
3. Select "Progressive Web App"
4. Click "Generate report"

Target scores:
- Performance: 90+
- Accessibility: 90+
- Best Practices: 90+
- SEO: 90+
- PWA: 100

## Next Steps

1. ✅ Test all features
2. ✅ Install PWA on mobile device
3. ✅ Test offline functionality
4. ✅ Verify voice interface works
5. ✅ Check all service views
6. ✅ Test on different browsers
7. ✅ Run Lighthouse audit
8. ✅ Deploy to production

## Support

For issues:
1. Check browser console for errors
2. Review service worker status
3. Test on different browsers
4. Check backend logs
5. Refer to `docs/pwa_implementation.md`

## Resources

- [PWA Documentation](docs/pwa_implementation.md)
- [Frontend README](frontend/README.md)
- [Integration Example](examples/pwa_integration_example.py)
- [Task Completion Summary](docs/task_21_completion_summary.md)

---

**Ready to use!** The PWA is now set up and ready for testing. Install it on your device and start exploring! 🚀
