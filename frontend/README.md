# BharatSahayak PWA Frontend

This is the Progressive Web App (PWA) frontend for BharatSahayak, a voice-enabled AI assistant for rural India.

## Features

- **Voice-First Interface**: Record voice queries and receive audio responses
- **Multilingual Support**: Hindi, English, Bengali, Telugu, Marathi, Tamil, Gujarati, Kannada
- **Offline Mode**: Core functionality works without internet connection
- **Service Workers**: Automatic caching and background sync
- **Responsive Design**: Works on devices with as little as 1GB RAM
- **Low Bandwidth**: Optimized for slow connections

## Structure

```
frontend/
├── index.html          # Main HTML file
├── manifest.json       # PWA manifest
├── sw.js              # Service worker
├── css/
│   └── styles.css     # Application styles
├── js/
│   ├── app.js         # Main application logic
│   ├── api.js         # API client
│   ├── voice.js       # Voice interface
│   ├── chat.js        # Chat interface
│   └── offline.js     # Offline mode management
└── icons/             # PWA icons (various sizes)
```

## Installation

### Development

1. Ensure the backend is running (see main README)

2. Serve the frontend using a static file server:

```bash
# Using Python
python -m http.server 8080 --directory frontend

# Or using Node.js http-server
npx http-server frontend -p 8080
```

3. Open http://localhost:8080 in your browser

### Production

The frontend should be served by the FastAPI backend as static files. Configure FastAPI to serve the frontend directory:

```python
from fastapi.staticfiles import StaticFiles

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
```

## PWA Installation

### On Mobile (Android/iOS)

1. Open the app in Chrome/Safari
2. Tap the menu button (⋮ or share icon)
3. Select "Add to Home Screen" or "Install App"
4. Follow the prompts

### On Desktop (Chrome/Edge)

1. Open the app in Chrome/Edge
2. Click the install icon in the address bar
3. Click "Install"

## Features by View

### Chat View
- Voice recording with visual feedback
- Text input with send button
- Message history with timestamps
- Loading states and error handling
- Audio playback of responses

### Schemes View
- Search government schemes
- Filter by category
- View detailed information
- Check eligibility

### Farmer View
- Crop recommendations
- Fertilizer guidance
- Market prices (mandi rates)
- Crop calendar

### Skills View
- Browse skill development programs
- Search government jobs
- Filter by qualifications
- View program details

### Health View
- Symptom checker
- Find nearby health facilities
- Health scheme information
- Emergency guidance

## Offline Functionality

The app caches:
- Static assets (HTML, CSS, JS)
- API responses for schemes, facilities, etc.
- User preferences and session data

When offline:
- Cached content is served
- User actions are queued
- Automatic sync when connection restored

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Opera 76+

## Performance

- First Contentful Paint: < 1.5s
- Time to Interactive: < 3s
- Lighthouse Score: 90+

## Accessibility

- ARIA labels on interactive elements
- Keyboard navigation support
- Screen reader compatible
- High contrast mode support

## Security

- HTTPS required for PWA features
- Content Security Policy headers
- No inline scripts
- Secure API communication

## Development

### Adding New Features

1. Create new module in `js/` directory
2. Import in `app.js`
3. Add UI elements in `index.html`
4. Style in `styles.css`

### Testing

Test on:
- Low-end Android devices (1GB RAM)
- Slow 3G connection
- Offline mode
- Different screen sizes

### Debugging

- Use Chrome DevTools Application tab for PWA features
- Check Service Worker status
- Inspect Cache Storage
- Monitor Network requests

## Localization

Language files are managed by the backend. The frontend:
- Detects user language preference
- Sends language code with API requests
- Displays translated content from backend

## Icons

Icons should be placed in `frontend/icons/` directory:
- icon-72x72.png
- icon-96x96.png
- icon-128x128.png
- icon-144x144.png
- icon-152x152.png
- icon-192x192.png
- icon-384x384.png
- icon-512x512.png

Generate icons from a single source using tools like:
- https://realfavicongenerator.net/
- https://www.pwabuilder.com/

## License

See main project LICENSE file.
