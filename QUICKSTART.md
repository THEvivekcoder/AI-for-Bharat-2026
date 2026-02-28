# Quick Start Guide

## Prerequisites

- Python 3.10+
- Docker and Docker Compose (for local development)

## Setup Steps

### 1. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
make install
```

### 2. Configure Environment

```bash
cp .env.example .env
```

The default `.env.example` is configured for local development with Docker.

### 3. Start Database Services

```bash
make db-up
```

This starts PostgreSQL and Redis using Docker Compose.

### 4. Initialize Database

```bash
make db-init
```

This creates all necessary database tables.

### 5. Validate Setup

```bash
make test
```

This runs validation tests to ensure everything is configured correctly.

### 6. Start Development Server

```bash
make dev
```

The API will be available at http://localhost:8000

### 7. Test the Health Endpoint

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

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Stopping Services

```bash
make db-down
```

## Troubleshooting

### Database Connection Error

Ensure PostgreSQL is running:
```bash
docker-compose ps
```

### Redis Connection Error

Ensure Redis is running:
```bash
docker-compose ps
```

### Port Already in Use

If port 8000 is already in use, modify the port in the `make dev` command or run:
```bash
uvicorn app.main:app --reload --port 8001
```
