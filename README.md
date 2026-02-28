# BharatSahayak

Multilingual AI Public Assistant for Rural India

## Overview

BharatSahayak is a voice-first, multilingual AI assistant designed to democratize access to government services, agricultural guidance, skill development, and healthcare information for rural and semi-urban India.

## Setup

### Prerequisites

- Python 3.10+
- PostgreSQL 14+
- Redis 6+

### Installation

1. Clone the repository
2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Setup database:
   ```bash
   # Create database
   createdb bharatsahayak
   
   # Run migrations
   alembic upgrade head
   ```

### Running the Application

```bash
# Development mode
uvicorn app.main:app --reload

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
.
├── app/
│   ├── api/              # API endpoints
│   ├── models/           # Database models
│   ├── schemas/          # Pydantic schemas
│   ├── config.py         # Configuration
│   ├── database.py       # Database setup
│   ├── redis_client.py   # Redis client
│   ├── logging_config.py # Logging setup
│   ├── middleware.py     # Middleware
│   └── main.py           # FastAPI app
├── alembic/              # Database migrations
├── requirements.txt      # Dependencies
└── README.md
```

## Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "database": "healthy",
    "redis": "healthy"
  }
}
```
