# Impact Tracker Implementation

## Overview

The Impact Tracker service provides comprehensive analytics and social impact measurement for the BharatSahayak platform. It tracks user interactions, successful outcomes, and generates detailed reports to measure the platform's effectiveness in serving rural and semi-urban populations.

## Implementation Summary

### Components Implemented

1. **Impact Tracker Service** (`app/services/impact_tracker.py`)
   - `record_interaction()`: Records user interaction events
   - `record_outcome()`: Records successful outcome events
   - `get_metrics()`: Retrieves aggregated impact metrics with filters
   - `generate_report()`: Generates comprehensive impact reports

2. **API Endpoints** (`app/api/impact.py`)
   - `POST /api/impact/event/interaction`: Record interaction event
   - `POST /api/impact/event/outcome`: Record outcome event
   - `POST /api/impact/metrics`: Get aggregated metrics
   - `GET /api/impact/report/{report_type}`: Generate impact report

3. **Data Models** (from task 14.1)
   - `InteractionEvent`: Stores user interaction events
   - `OutcomeEvent`: Stores successful outcome events
   - Schemas for request/response validation

## Features

### 1. Interaction Event Recording

Tracks various user interactions:
- `query_submitted`: User submitted a query
- `scheme_accessed`: User viewed scheme details
- `job_discovered`: User found a job posting
- `facility_located`: User found a health facility
- `voice_interaction`: User used voice interface
- `language_used`: User interacted in specific language
- `crop_advice_requested`: Farmer requested crop advice
- `fertilizer_advice_requested`: Farmer requested fertilizer guidance
- `market_price_checked`: Farmer checked mandi prices
- `skill_program_viewed`: User viewed skill program
- `health_check_performed`: User performed health check

**Features:**
- Supports both authenticated and anonymous users
- Stores event metadata in JSONB format
- Automatic timestamp recording
- Language tracking for multilingual analytics

### 2. Outcome Event Recording

Tracks successful outcomes:
- `scheme_applied`: User applied for a scheme
- `job_applied`: User applied for a job
- `facility_visited`: User visited a health facility
- `skill_enrolled`: User enrolled in skill program
- `recommendation_followed`: User followed a recommendation
- `crop_planted`: Farmer planted recommended crop
- `fertilizer_purchased`: Farmer purchased recommended fertilizer

**Features:**
- Links outcomes to interactions for success rate calculation
- Flexible outcome data storage
- Supports impact measurement across all services

### 3. Metrics Aggregation

Provides comprehensive metrics:
- **users_served**: Total unique users
- **queries_resolved**: Total queries processed
- **schemes_accessed**: Number of scheme accesses
- **farmers_assisted**: Farmers who received advice
- **jobs_discovered**: Jobs found by users
- **health_checks_performed**: Health checks completed
- **languages_used**: Breakdown by language
- **events_by_type**: Count by event type
- **outcomes_by_type**: Count by outcome type
- **success_rate**: Ratio of outcomes to interactions

**Filtering Options:**
- Date range (start_date, end_date)
- Region (state, district)
- Language
- Event type
- Outcome type
- Service category (schemes, farmer, skills, health)

### 4. Report Generation

Generates comprehensive impact reports:
- **Daily**: Last 24 hours
- **Weekly**: Last 7 days
- **Monthly**: Last 30 days
- **Quarterly**: Last 90 days
- **Custom**: User-defined date range

**Report Contents:**
- Overall metrics
- Regional breakdown (by state)
- Language breakdown
- Service category breakdown
- Generated timestamp

## Database Schema

### Interactions Table
```sql
CREATE TABLE interactions (
    interaction_id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(user_id) ON DELETE SET NULL,
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB,
    language VARCHAR(10),
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_interactions_user_timestamp ON interactions(user_id, timestamp);
CREATE INDEX idx_interactions_event_type_timestamp ON interactions(event_type, timestamp);
```

### Outcomes Table
```sql
CREATE TABLE outcomes (
    outcome_id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(user_id) ON DELETE SET NULL,
    outcome_type VARCHAR(50) NOT NULL,
    outcome_data JSONB,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_outcomes_user_timestamp ON outcomes(user_id, timestamp);
CREATE INDEX idx_outcomes_outcome_type_timestamp ON outcomes(outcome_type, timestamp);
```

## API Usage Examples

### Record Interaction Event

```bash
curl -X POST http://localhost:8000/api/impact/event/interaction \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "scheme_accessed",
    "event_data": {
      "scheme_id": "PM-KISAN",
      "state": "Maharashtra"
    },
    "language": "hi"
  }'
```

Response:
```json
{
  "success": true,
  "event_id": "5b963c26-97f2-4dde-9f04-edb2e3c3331b",
  "message": "Interaction event recorded successfully"
}
```

### Record Outcome Event

```bash
curl -X POST http://localhost:8000/api/impact/event/outcome \
  -H "Content-Type: application/json" \
  -d '{
    "outcome_type": "scheme_applied",
    "outcome_data": {
      "scheme_id": "PM-KISAN",
      "application_id": "APP123"
    }
  }'
```

### Get Metrics

```bash
curl -X POST http://localhost:8000/api/impact/metrics \
  -H "Content-Type: application/json" \
  -d '{
    "language": "hi",
    "service_category": "farmer"
  }'
```

Response:
```json
{
  "users_served": 150,
  "queries_resolved": 450,
  "schemes_accessed": 120,
  "farmers_assisted": 85,
  "jobs_discovered": 45,
  "health_checks_performed": 30,
  "languages_used": {
    "hi": 300,
    "mr": 100,
    "te": 50
  },
  "events_by_type": {
    "query_submitted": 200,
    "scheme_accessed": 120,
    "crop_advice_requested": 85
  },
  "outcomes_by_type": {
    "scheme_applied": 50,
    "crop_planted": 30
  },
  "success_rate": 0.1778,
  "period_start": "2026-01-28T15:48:37.506909",
  "period_end": "2026-02-27T15:48:37.506909"
}
```

### Generate Report

```bash
# Daily report
curl http://localhost:8000/api/impact/report/daily

# Weekly report
curl http://localhost:8000/api/impact/report/weekly

# Custom report
curl "http://localhost:8000/api/impact/report/custom?start_date=2026-01-01T00:00:00&end_date=2026-01-31T23:59:59"
```

## Testing

### Unit Tests
Run the service tests:
```bash
python scripts/test_impact_tracker.py
```

### API Tests
Start the server and run API tests:
```bash
# Terminal 1: Start server
uvicorn app.main:app --reload

# Terminal 2: Run API tests
python scripts/test_impact_api.py
```

## Privacy and Anonymization

The Impact Tracker implements privacy-by-design principles:

1. **Anonymous Tracking**: Users can be tracked anonymously (user_id is optional)
2. **Data Anonymization**: Personal information is not included in analytics queries
3. **Soft Deletes**: Foreign key uses SET NULL on user deletion to preserve analytics
4. **JSONB Storage**: Flexible event data storage without exposing PII in structured fields

## Performance Considerations

1. **Database Indexes**: Optimized indexes on user_id, event_type, and timestamp
2. **Efficient Aggregation**: Uses database-level aggregation for metrics
3. **Caching**: Consider implementing Redis caching for frequently accessed metrics
4. **Batch Processing**: For large-scale analytics, consider batch processing jobs

## Integration with Other Services

The Impact Tracker integrates with all BharatSahayak services:

1. **Scheme Service**: Tracks scheme accesses and applications
2. **Farmer Advisory**: Tracks crop advice, fertilizer guidance, and market price checks
3. **Skills Service**: Tracks skill program views and job discoveries
4. **Health Service**: Tracks health checks and facility lookups
5. **Voice Interface**: Tracks voice interactions and language usage
6. **RAG Engine**: Tracks query submissions and resolutions

## Future Enhancements

1. **Real-time Dashboards**: WebSocket-based live metrics
2. **Predictive Analytics**: ML models for impact prediction
3. **Geospatial Analysis**: Map-based visualization of regional impact
4. **A/B Testing**: Track effectiveness of different features
5. **User Journey Analysis**: Track complete user flows
6. **Export Functionality**: CSV/PDF report exports

## Requirements Validation

This implementation satisfies:
- **Requirement 9.1**: Records user interactions with all required fields
- **Requirement 9.2**: Aggregates data by region, language, and service category
- **Requirement 9.3**: Records successful outcomes and tracks metrics
- **Requirement 9.4**: Anonymizes personal information in analytics (via optional user_id and JSONB storage)

## Conclusion

The Impact Tracker service provides comprehensive analytics capabilities for measuring the social impact of BharatSahayak. It enables data-driven decision making, helps identify areas for improvement, and demonstrates the platform's effectiveness in serving rural and semi-urban populations.
