# BharatSahayak Integration Architecture

## Overview

This document describes how all BharatSahayak components are wired together to provide end-to-end functionality. The system follows a layered architecture with clear separation of concerns and well-defined integration points.

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Layer (PWA)                       │
│  - Voice Interface UI                                        │
│  - Chat Interface                                            │
│  - Service-specific UIs                                      │
│  - Offline Cache                                             │
└─────────────────────────────────────────────────────────────┘
                            ↓ HTTP/HTTPS
┌─────────────────────────────────────────────────────────────┐
│                    Middleware Layer                          │
│  - Rate Limiting                                             │
│  - Logging                                                   │
│  - Error Handling                                            │
│  - Impact Tracking (Automatic)                               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    API Layer                                 │
│  - Integrated Endpoints (End-to-End Flows)                   │
│  - Domain Service Endpoints                                  │
│  - Authentication Endpoints                                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              Integration Orchestrator                        │
│  - Coordinates all components                                │
│  - Manages end-to-end flows                                  │
│  - Handles cross-service interactions                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Service Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │Voice Interface│  │  RAG Engine  │  │Impact Tracker│      │
│  │  - STT       │  │  - LLM       │  │  - Analytics │      │
│  │  - TTS       │  │  - Vector DB │  │  - Metrics   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │Scheme Service│  │Farmer Service│  │Skills Service│      │
│  │  - Search    │  │  - Crop Adv. │  │  - Matching  │      │
│  │  - Eligibil. │  │  - Prices    │  │  - Jobs      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │Health Service│  │Language Proc.│  │Cache Manager │      │
│  │  - Symptoms  │  │  - Translate │  │  - Offline   │      │
│  │  - Facilities│  │  - Detect    │  │  - Sync      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Data Layer                                │
│  - PostgreSQL (Primary data)                                 │
│  - Redis (Cache & Sessions)                                  │
│  - FAISS (Vector embeddings)                                 │
│  - SQLite (Offline cache)                                    │
└─────────────────────────────────────────────────────────────┘
```

## Core Integration Points

### 1. Voice Interface ↔ RAG Engine

**Connection:** Integration Orchestrator

**Flow:**
1. User speaks query (audio input)
2. STT Engine converts audio to text
3. Text query sent to RAG Engine
4. RAG Engine processes query and generates response
5. TTS Engine converts response to audio
6. Audio response returned to user

**Implementation:**
- `IntegrationOrchestrator.process_voice_query()` coordinates the flow
- Voice engines initialized in orchestrator constructor
- RAG engine receives text queries from STT output
- TTS engine receives text responses from RAG output

**Code Location:**
- `app/services/integration_orchestrator.py` - Main coordination
- `app/services/voice_interface.py` - STT/TTS engines
- `app/services/rag_engine.py` - Query processing

**API Endpoint:**
```
POST /api/integrated/voice-query
- Input: Audio file (multipart/form-data)
- Output: JSON with text query, text answer, audio answer (base64), sources
```

### 2. RAG Engine ↔ Domain Services

**Connection:** Direct service calls from RAG Engine

**Flow:**
1. RAG Engine receives user query
2. Determines which domain service(s) to query
3. Calls appropriate service(s) for structured data
4. Combines service responses with vector search results
5. Generates comprehensive response

**Implementation:**
- RAG Engine can call any domain service directly
- Services return structured data (schemes, prices, jobs, etc.)
- RAG Engine formats data into natural language response
- Conversation context preserved across turns

**Code Location:**
- `app/services/rag_engine.py` - Query processing
- `app/services/scheme_repository.py` - Scheme data
- `app/services/crop_advisor.py` - Crop recommendations
- `app/services/skills_matcher.py` - Skills/jobs data
- `app/services/health_advisor.py` - Health guidance

**Example Integration:**
```python
# RAG Engine queries scheme service
schemes = scheme_repository.search_schemes(
    query="agriculture schemes",
    filters={"category": "agriculture"}
)

# RAG Engine formats response
response = f"Found {len(schemes)} agriculture schemes: ..."
```

### 3. Domain Services ↔ Impact Tracker

**Connection:** Integration Orchestrator + Impact Tracking Middleware

**Flow:**
1. User interacts with domain service
2. Service processes request and returns response
3. Integration Orchestrator tracks interaction
4. Impact Tracker records event in database
5. Analytics aggregated for reporting

**Implementation:**
- **Automatic Tracking:** Middleware tracks all domain service requests
- **Manual Tracking:** Orchestrator tracks specific events with context
- **Outcome Tracking:** Orchestrator tracks successful outcomes

**Code Location:**
- `app/services/integration_orchestrator.py` - Manual tracking methods
- `app/middleware/impact_tracking.py` - Automatic tracking
- `app/services/impact_tracker.py` - Event recording

**Tracked Events:**
- Voice interactions
- Query submissions
- Scheme access
- Crop advice requests
- Job discoveries
- Health checks
- Facility locations

**Tracked Outcomes:**
- Scheme applications
- Job applications
- Skill enrollments
- Facility visits

### 4. All Endpoints ↔ Middleware

**Connection:** FastAPI middleware stack

**Flow:**
1. Request arrives at API endpoint
2. Rate Limiting Middleware checks limits
3. Logging Middleware logs request
4. Error Handling Middleware wraps execution
5. Impact Tracking Middleware records interaction
6. Endpoint processes request
7. Middleware processes response
8. Response returned to client

**Implementation:**
- Middleware applied to all requests automatically
- Order matters: Rate limiting → Logging → Error handling
- Impact tracking runs after successful responses
- Exception handlers catch and format errors

**Code Location:**
- `app/middleware/rate_limiter.py` - Rate limiting
- `app/middleware/logging.py` - Request logging
- `app/middleware/error_handling.py` - Error handling
- `app/middleware/impact_tracking.py` - Automatic tracking
- `app/main.py` - Middleware registration

## Integration Orchestrator

The Integration Orchestrator (`app/services/integration_orchestrator.py`) is the central component that coordinates all services.

### Responsibilities

1. **Voice Query Processing**
   - Coordinates STT → RAG → TTS flow
   - Manages conversation context
   - Tracks voice interactions

2. **Impact Tracking Coordination**
   - Provides tracking methods for all services
   - Ensures consistent event recording
   - Handles tracking failures gracefully

3. **Service Integration**
   - Initializes all required services
   - Manages service dependencies
   - Provides unified interface

### Key Methods

```python
# End-to-end voice query processing
async def process_voice_query(request: VoiceQueryRequest) -> VoiceQueryResponse

# Scheme tracking
def track_scheme_access(user_id, scheme_id, scheme_name, language)
def track_scheme_application(user_id, scheme_id, scheme_name)

# Farmer tracking
def track_crop_advice(user_id, crop_recommendations, language)
def track_fertilizer_advice(user_id, crop_name, language)
def track_market_price_check(user_id, crop_name, prices_found, language)

# Skills/Jobs tracking
def track_job_discovery(user_id, job_id, job_title, language)
def track_skill_program_view(user_id, program_id, program_name, language)
def track_skill_enrollment(user_id, program_id, program_name)

# Health tracking
def track_health_check(user_id, symptoms, urgency_level, language)
def track_facility_location(user_id, facility_type, facilities_found, language)
def track_facility_visit(user_id, facility_id, facility_name)
```

## Integrated API Endpoints

The integrated API (`app/api/integrated.py`) provides end-to-end endpoints that demonstrate full component integration.

### Available Endpoints

#### 1. Voice Query Processing
```
POST /api/integrated/voice-query
POST /api/integrated/voice-query/audio
```
Complete voice-to-voice flow with impact tracking.

#### 2. Scheme Tracking
```
POST /api/integrated/scheme/access
POST /api/integrated/scheme/apply
```
Track scheme interactions and applications.

#### 3. Job Tracking
```
POST /api/integrated/job/discover
```
Track job discoveries.

#### 4. Health Tracking
```
POST /api/integrated/health/check
```
Track health symptom checks.

## Middleware Integration

### 1. Rate Limiting Middleware

**Purpose:** Prevent abuse and ensure fair usage

**Configuration:**
```python
RATE_LIMITS = {
    "/api/voice": (100, 60),      # 100 requests per minute
    "/api/ask": (50, 60),          # 50 requests per minute
    "/api/schemes": (60, 60),      # 60 requests per minute
    "/api/auth": (5, 300),         # 5 requests per 5 minutes
}
```

**Features:**
- Per-user and per-IP limiting
- Burst capacity for short spikes
- Automatic cleanup of old entries
- Rate limit headers in responses

### 2. Logging Middleware

**Purpose:** Track all requests for debugging and monitoring

**Logged Information:**
- Request ID (UUID)
- Method and path
- Client IP
- Response status
- Processing time

**Headers Added:**
- `X-Request-ID`: Unique request identifier
- `X-Process-Time`: Processing time in seconds

### 3. Error Handling Middleware

**Purpose:** Provide consistent, multilingual error responses

**Features:**
- Catches all exceptions
- Translates errors to user's language
- Returns structured error responses
- Logs errors for debugging

**Error Response Format:**
```json
{
  "error_code": "DATA_NOT_FOUND",
  "message": "योजना नहीं मिली",
  "details": {"scheme_id": "123"},
  "suggestions": ["Search by category", "Try different keywords"]
}
```

### 4. Impact Tracking Middleware

**Purpose:** Automatically track domain service usage

**Tracked Endpoints:**
- `GET /api/schemes/{id}` → Scheme access
- `GET /api/jobs/{id}` → Job discovery
- `GET /api/skills/{id}` → Skill program view
- `POST /api/health/check` → Health check
- `POST /api/farmer/crop-advice` → Crop advice
- `GET /api/farmer/market-price` → Market price check

**Features:**
- Automatic tracking (no code changes needed)
- Extracts user ID from request state
- Detects language from headers
- Records only successful requests (2xx status)

## Data Flow Examples

### Example 1: Voice Query for Schemes

```
User speaks: "मुझे कृषि योजनाओं के बारे में बताएं"
                    ↓
        [Voice Interface - STT]
                    ↓
        Text: "Tell me about agriculture schemes"
                    ↓
        [RAG Engine - Query Processing]
                    ↓
        [Vector Store - Semantic Search]
                    ↓
        [Scheme Repository - Data Retrieval]
                    ↓
        [RAG Engine - Response Generation]
                    ↓
        Text: "Here are agriculture schemes: PM-KISAN, ..."
                    ↓
        [Voice Interface - TTS]
                    ↓
        Audio response in Hindi
                    ↓
        [Impact Tracker - Record Events]
        - Voice interaction
        - Query submission
        - Scheme access
```

### Example 2: Farmer Crop Advice

```
User: "What crops should I plant?"
                    ↓
        [API Endpoint - /api/farmer/crop-advice]
                    ↓
        [Crop Advisor - Analyze Conditions]
        - Soil type
        - Season
        - Location
        - Weather data
                    ↓
        [Crop Advisor - Generate Recommendations]
                    ↓
        Response: [Wheat, Rice, Sugarcane]
                    ↓
        [Impact Tracking Middleware - Automatic]
        - Record crop advice request
                    ↓
        [Integration Orchestrator - Manual]
        - Record with full context
```

### Example 3: Scheme Application Flow

```
User searches schemes
                    ↓
        [Scheme Repository - Search]
                    ↓
        [Eligibility Checker - Filter]
                    ↓
        Display eligible schemes
                    ↓
User clicks scheme
                    ↓
        [Impact Tracking Middleware]
        - Record scheme access
                    ↓
User applies for scheme
                    ↓
        [Integration Orchestrator]
        - Record scheme application (outcome)
                    ↓
        [Impact Tracker]
        - Store in database
        - Update analytics
```

## Testing Integration

### Verification Script

Run the integration verification:
```bash
python scripts/verify_integration_simple.py
```

This verifies:
- Component wiring
- End-to-end flow definitions
- Middleware integration
- API integration

### Integration Demo

Run the integration demo:
```bash
python examples/integration_demo.py
```

This demonstrates:
- Voice → RAG → Voice flow
- Scheme discovery flow
- Farmer advisory flow
- Health advisory flow
- Impact tracking
- Middleware integration

## Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/bharatsahayak

# Redis
REDIS_URL=redis://localhost:6379

# LLM
OPENAI_API_KEY=your_key_here
LLM_PROVIDER=openai
LLM_MODEL=gpt-3.5-turbo

# Voice
STT_MODEL=openai/whisper-large-v3
TTS_MODEL=coqui/tts

# Rate Limiting
RATE_LIMIT_ENABLED=true

# Impact Tracking
IMPACT_TRACKING_ENABLED=true
```

### Middleware Configuration

Middleware is configured in `app/main.py`:

```python
# Add middleware (order matters)
app.middleware("http")(rate_limiting_middleware)
app.middleware("http")(logging_middleware)
app.middleware("http")(error_handling_middleware)

# Setup impact tracking
setup_impact_tracking_middleware(app)

# Setup exception handlers
setup_exception_handlers(app)
```

## Deployment Considerations

### Production Checklist

- [ ] All middleware enabled
- [ ] Rate limits configured appropriately
- [ ] Error messages translated to all supported languages
- [ ] Impact tracking database optimized
- [ ] Logging configured for production
- [ ] TLS/HTTPS enabled
- [ ] CORS configured correctly
- [ ] Database connection pooling enabled
- [ ] Redis cache configured
- [ ] Vector store indexed and optimized

### Monitoring

Monitor these integration points:
- Voice processing latency (STT + TTS)
- RAG query response time
- Domain service response times
- Impact tracking write performance
- Middleware overhead
- Error rates by endpoint
- Rate limit violations

### Scaling

Scale these components independently:
- API servers (horizontal scaling)
- Database (read replicas)
- Redis (clustering)
- Vector store (sharding)
- Voice processing (GPU instances)

## Troubleshooting

### Common Issues

1. **Voice query fails**
   - Check STT/TTS model availability
   - Verify audio format compatibility
   - Check language support

2. **RAG responses are slow**
   - Optimize vector store index
   - Reduce top_k parameter
   - Cache frequent queries

3. **Impact tracking not recording**
   - Verify middleware is enabled
   - Check database connectivity
   - Review error logs

4. **Rate limiting too aggressive**
   - Adjust limits in configuration
   - Implement user-specific quotas
   - Add burst capacity

## Summary

All BharatSahayak components are successfully wired together:

✓ Voice Interface → RAG Engine: Connected via Integration Orchestrator
✓ RAG Engine → Domain Services: Direct service calls
✓ Domain Services → Impact Tracker: Automatic + manual tracking
✓ All Endpoints → Middleware: Automatic enhancement

The system provides:
- End-to-end voice-to-voice flows
- Automatic impact tracking
- Consistent error handling
- Rate limiting and security
- Complete request tracing

The integration is production-ready and fully testable.
