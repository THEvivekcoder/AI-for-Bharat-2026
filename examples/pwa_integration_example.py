"""
Example: Integrating the PWA Frontend with FastAPI Backend

This example shows how to serve the PWA frontend from the FastAPI backend
and configure proper routing for the Single Page Application.
"""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

# Initialize FastAPI app
app = FastAPI(
    title="BharatSahayak API",
    description="Voice-enabled AI assistant for rural India",
    version="1.0.0"
)

# Configure CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Path to frontend directory
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

# Mount static files (CSS, JS, icons, etc.)
app.mount(
    "/css",
    StaticFiles(directory=FRONTEND_DIR / "css"),
    name="css"
)
app.mount(
    "/js",
    StaticFiles(directory=FRONTEND_DIR / "js"),
    name="js"
)
app.mount(
    "/icons",
    StaticFiles(directory=FRONTEND_DIR / "icons"),
    name="icons"
)

# Serve manifest.json
@app.get("/manifest.json")
async def serve_manifest():
    return FileResponse(FRONTEND_DIR / "manifest.json")

# Serve service worker
@app.get("/sw.js")
async def serve_service_worker():
    return FileResponse(
        FRONTEND_DIR / "sw.js",
        media_type="application/javascript",
        headers={
            "Service-Worker-Allowed": "/",
            "Cache-Control": "no-cache"
        }
    )

# API routes (already implemented in previous tasks)
# These are just examples - actual routes are in app/api/

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "1.0.0"}

# ... other API routes ...

# Serve PWA for all non-API routes (SPA routing)
@app.get("/{full_path:path}")
async def serve_pwa(request: Request, full_path: str):
    """
    Serve the PWA for all routes that don't match API endpoints.
    This enables client-side routing in the SPA.
    """
    # Don't serve index.html for API routes
    if full_path.startswith("api/"):
        return {"error": "Not found"}, 404
    
    # Serve index.html for all other routes
    return FileResponse(FRONTEND_DIR / "index.html")


# Alternative: More explicit routing
class PWARouter:
    """
    Alternative approach with more explicit control over routing
    """
    
    def __init__(self, app: FastAPI, frontend_dir: Path):
        self.app = app
        self.frontend_dir = frontend_dir
        self.setup_routes()
    
    def setup_routes(self):
        """Setup all PWA routes"""
        
        # Static files
        self.app.mount(
            "/static",
            StaticFiles(directory=self.frontend_dir),
            name="static"
        )
        
        # Root route
        @self.app.get("/")
        async def root():
            return FileResponse(self.frontend_dir / "index.html")
        
        # PWA routes (client-side routing)
        pwa_routes = [
            "/chat",
            "/schemes",
            "/farmer",
            "/skills",
            "/health"
        ]
        
        for route in pwa_routes:
            @self.app.get(route)
            async def serve_view():
                return FileResponse(self.frontend_dir / "index.html")


# Production configuration example
def configure_production(app: FastAPI):
    """
    Additional configuration for production deployment
    """
    from fastapi.middleware.gzip import GZipMiddleware
    from fastapi.middleware.trustedhost import TrustedHostMiddleware
    
    # Enable compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Restrict hosts
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["bharatsahayak.gov.in", "*.bharatsahayak.gov.in"]
    )
    
    # Add security headers
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self' https://api.bharatsahayak.gov.in; "
            "media-src 'self' blob:; "
            "worker-src 'self';"
        )
        
        return response


# Cache control for static assets
@app.middleware("http")
async def add_cache_headers(request: Request, call_next):
    """Add appropriate cache headers for static assets"""
    response = await call_next(request)
    
    path = request.url.path
    
    # Long cache for static assets with hashes
    if any(path.startswith(prefix) for prefix in ["/css/", "/js/", "/icons/"]):
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    
    # No cache for service worker
    elif path == "/sw.js":
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    
    # Short cache for HTML
    elif path.endswith(".html") or path == "/":
        response.headers["Cache-Control"] = "no-cache, must-revalidate"
    
    return response


# Example: Testing the integration
if __name__ == "__main__":
    import uvicorn
    
    print("Starting BharatSahayak server...")
    print("PWA available at: http://localhost:8000")
    print("API docs at: http://localhost:8000/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )


# Docker deployment example
"""
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/
COPY frontend/ ./frontend/
COPY examples/pwa_integration_example.py ./main.py

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
"""

# Nginx reverse proxy example
"""
# nginx.conf
server {
    listen 80;
    server_name bharatsahayak.gov.in;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name bharatsahayak.gov.in;
    
    # SSL configuration
    ssl_certificate /etc/ssl/certs/bharatsahayak.crt;
    ssl_certificate_key /etc/ssl/private/bharatsahayak.key;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    
    # Proxy to FastAPI
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Cache static assets
    location ~* \.(css|js|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        proxy_pass http://localhost:8000;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # No cache for service worker
    location = /sw.js {
        proxy_pass http://localhost:8000;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }
}
"""

# Kubernetes deployment example
"""
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: bharatsahayak
spec:
  replicas: 3
  selector:
    matchLabels:
      app: bharatsahayak
  template:
    metadata:
      labels:
        app: bharatsahayak
    spec:
      containers:
      - name: bharatsahayak
        image: bharatsahayak:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: bharatsahayak-secrets
              key: database-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
---
apiVersion: v1
kind: Service
metadata:
  name: bharatsahayak-service
spec:
  selector:
    app: bharatsahayak
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
"""
